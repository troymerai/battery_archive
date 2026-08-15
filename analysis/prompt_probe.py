"""aging condition 프롬프트가 무엇으로 만들어지는지 실물로 확인한다.

BatteryMFormer 의 프롬프트는 pkl 을 읽지 않는다. `Prompts/Mapping_helper.py` 의
셀이름 -> 조건 ID 사전과 `Prompts/*_protocol_prompt.py` 의 하드코딩된 문자열이
전부다. 이 스크립트는 그 사실을 다음 넷으로 확인한다.

1. 서브셋마다 프롬프트 실물을 하나씩 뽑는다 (ZN-coin 포함)
2. 같은 셀의 pkl `cathode_material` / `anode_material` 을 나란히 찍어
   극 반전이 프롬프트로 전파되는지 본다
3. 배포된 `Qwen3_total.pkl` 의 셀 1,129개를 전부 매핑에 넣어
   매핑이 있는 셀과 없는 셀을 센다
4. 배포 데이터 1,382셀 전부를 매핑에 넣어 어느 셀이 프롬프트를 못 받는지 센다
5. 프롬프트 문장이 말하는 공칭용량과 pkl 의 `nominal_capacity_in_Ah` 를 대조한다

산출
-----
    analysis/out/prompt_samples.md          서브셋별 프롬프트 실물
    analysis/out/prompt_coverage.csv        셀 단위 매핑 성공/실패
    analysis/out/prompt_capacity_check.csv  프롬프트 공칭용량 대 pkl 공칭용량

실행
-----
    .venv-blife/Scripts/python.exe analysis/prompt_probe.py
"""

import csv
import io
import json
import pickle
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BMF = ROOT / 'upstream' / 'BatteryMFormer'
OUT = ROOT / 'analysis' / 'out'
CLEANED = ROOT / 'data' / 'extracted'

sys.path.insert(0, str(BMF))
from Prompts.Mapping_helper import Mapping_helper  # noqa: E402

# generate_aging_condition_embeddings.ipynb 의 cell 7 에 있는 배경 프롬프트.
# 프롬프트 전문은 bg_prompt + Mapping_helper.do_mapping() 이다.
BG_CALB = (
    "Task description: "
    "The end of life of a battery is the number of charge-discharge cycles until "
    "the battery's discharge capacity reaches 90% of its nominal capacity. "
    "The discharge capacity is calculated under the described operating condition. "
    "The state of the health (SOH) is computed by the ratio of the remaining capacity "
    "to the initial capacity. "
    "The target is the SOH degradation trajecotry until the end of life of the battery."
    "Please directly output the target of the battery based on the provided data. "
)
BG_OTHER = (
    "Task description: "
    "The end of life of a battery is the number of charge-discharge cycles until "
    "the battery's discharge capacity reaches 80% of its nominal capacity. "
    "The discharge capacity is calculated under the described operating condition. "
    "The state of the health (SOH) is computed by the ratio of the remaining capacity "
    "to the nominal capacity. "
    "The target is the SOH degradation trajecotry until the end of life of the battery."
    "Please directly output the target of the battery based on the provided data. "
)


def build_prompt(cell_name):
    """노트북 cell 7 과 같은 순서로 프롬프트 전문을 만든다."""
    bg = BG_CALB if 'CALB' in cell_name else BG_OTHER
    stem = cell_name.split('.pkl')[0]
    helper = Mapping_helper(prompt_type='PROTOCOL', cell_name=stem)
    return bg + helper.do_mapping()


def pkl_electrodes(subset, file_name):
    """같은 셀의 pkl 이 실제로 담고 있는 극 정보."""
    p = CLEANED / subset / file_name
    if not p.is_file():
        return None
    with open(p, 'rb') as f:
        d = pickle.load(f)
    return {
        'cathode_material': d.get('cathode_material'),
        'anode_material': d.get('anode_material'),
        'nominal_capacity_in_Ah': d.get('nominal_capacity_in_Ah'),
        'SOC_interval': d.get('SOC_interval'),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- 배포 프롬프트 임베딩의 셀 목록 -----------------------------------
    emb_path = BMF / 'data_provider' / 'prompt_embeddings' / 'Qwen3_total.pkl'
    with open(emb_path, 'rb') as f:
        deployed = sorted(pickle.load(f))

    # ---- 배포 데이터 1,382셀 -----------------------------------------------
    all_cells = []
    for sub in sorted(p.name for p in CLEANED.iterdir() if p.is_dir()):
        if sub in ('Life labels', 'READMEs', 'seen_unseen_labels', 'total_MICH'):
            continue
        for f in sorted((CLEANED / sub).glob('*.pkl')):
            all_cells.append((sub, f.name))

    deployed_set = set(deployed)
    rows = []
    for sub, fname in all_cells:
        try:
            build_prompt(fname)
            ok, err = 1, ''
        except Exception as exc:                       # noqa: BLE001
            ok, err = 0, f'{type(exc).__name__}: {exc}'[:160]
        rows.append({'subset': sub, 'file': fname,
                     'prompt_mapped': ok, 'error': err,
                     'in_deployed_embeddings': int(fname in deployed_set)})

    with open(OUT / 'prompt_coverage.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['subset', 'file', 'prompt_mapped',
                                          'error', 'in_deployed_embeddings'])
        w.writeheader()
        w.writerows(rows)

    # ---- 서브셋마다 프롬프트 실물 하나 -------------------------------------
    buf = io.StringIO()
    buf.write('# 프롬프트 실물 — 서브셋별 1개\n\n')
    buf.write('`bg_prompt`(노트북 cell 7) + `Mapping_helper.do_mapping()` 을 이어 붙인 전문입니다.\n')
    buf.write('pkl 의 `cathode_material` / `anode_material` 은 이 경로에 **들어가지 않습니다** — ')
    buf.write('아래 각 항의 "pkl 실제 값" 과 프롬프트 본문을 대조하십시오.\n\n')

    by_subset = {}
    for r in rows:
        by_subset.setdefault(r['subset'], []).append(r)

    for sub in sorted(by_subset):
        cand = [r for r in by_subset[sub] if r['prompt_mapped'] and r['in_deployed_embeddings']]
        if not cand:
            cand = [r for r in by_subset[sub] if r['prompt_mapped']]
        buf.write(f'## {sub}\n\n')
        if not cand:
            bad = by_subset[sub][0]
            buf.write(f'프롬프트를 만들 수 있는 셀이 없습니다. 예: `{bad["file"]}` → `{bad["error"]}`\n\n')
            continue
        pick = cand[0]
        el = pkl_electrodes(sub, pick['file'])
        buf.write(f'- 셀: `{pick["file"]}`\n')
        if el:
            buf.write(f'- pkl 실제 값: `cathode_material={el["cathode_material"]!r}`, '
                      f'`anode_material={el["anode_material"]!r}`, '
                      f'`nominal_capacity_in_Ah={el["nominal_capacity_in_Ah"]!r}`, '
                      f'`SOC_interval={el["SOC_interval"]!r}`\n')
        n_ok = sum(r['prompt_mapped'] for r in by_subset[sub])
        buf.write(f'- 이 서브셋 매핑 성공 {n_ok} / {len(by_subset[sub])}셀\n\n')
        buf.write('```text\n')
        buf.write(build_prompt(pick['file']).strip())
        buf.write('\n```\n\n')

    (OUT / 'prompt_samples.md').write_text(buf.getvalue(), encoding='utf-8')

    # ---- 프롬프트가 말하는 공칭용량 대 pkl 의 공칭용량 ---------------------
    cap_rows = []
    for sub, fname in all_cells:
        try:
            text = build_prompt(fname)
        except Exception:                                  # noqa: BLE001
            continue
        m = re.search(r'The nominal capacity is ([0-9.eE+-]+) Ah', text)
        if not m:
            continue
        el = pkl_electrodes(sub, fname)
        if not el or el['nominal_capacity_in_Ah'] is None:
            continue
        p_cap = float(m.group(1))
        d_cap = float(el['nominal_capacity_in_Ah'])
        rel = abs(p_cap - d_cap) / max(abs(d_cap), 1e-30)
        cap_rows.append({'subset': sub, 'file': fname,
                         'prompt_nominal_Ah': repr(p_cap), 'pkl_nominal_Ah': repr(d_cap),
                         'rel_diff': f'{rel:.6f}', 'match': int(rel < 1e-9)})
    with open(OUT / 'prompt_capacity_check.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['subset', 'file', 'prompt_nominal_Ah',
                                          'pkl_nominal_Ah', 'rel_diff', 'match'])
        w.writeheader()
        w.writerows(cap_rows)
    cap_by_sub = {}
    for r in cap_rows:
        a = cap_by_sub.setdefault(r['subset'], {'n': 0, 'match': 0, 'max_rel': 0.0})
        a['n'] += 1
        a['match'] += r['match']
        a['max_rel'] = max(a['max_rel'], float(r['rel_diff']))
    print('\n공칭용량 대조 (프롬프트 문장 대 pkl):')
    for k in sorted(cap_by_sub):
        a = cap_by_sub[k]
        print(f'  {k}: {a["match"]}/{a["n"]} 일치, 최대 상대차 {a["max_rel"]:.4f}')

    # ---- 요약 --------------------------------------------------------------
    n_ok = sum(r['prompt_mapped'] for r in rows)
    print(f'배포 데이터 {len(rows)}셀 중 프롬프트 매핑 성공 {n_ok}, 실패 {len(rows) - n_ok}')
    print(f'배포 임베딩 셀 수 {len(deployed)}')
    fail_by_sub = {}
    for r in rows:
        if not r['prompt_mapped']:
            fail_by_sub[r['subset']] = fail_by_sub.get(r['subset'], 0) + 1
    for k in sorted(fail_by_sub):
        print(f'  매핑 실패 {k}: {fail_by_sub[k]}')
    missing = sorted(set(deployed) - {r['file'] for r in rows})
    print(f'임베딩에는 있는데 data/extracted 에 없는 셀: {len(missing)}')
    for m in missing[:10]:
        print('   ', m)
    json.dump({'deployed_n': len(deployed), 'mapped_ok': n_ok, 'total': len(rows)},
              open(OUT / 'prompt_coverage_summary.json', 'w'), indent=2)


if __name__ == '__main__':
    main()
