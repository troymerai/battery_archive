"""논문 Table 1 과 대조 — 배포 산출물의 어느 관문이 셀 수를 결정하는가.

배포된 BatteryMFormer 산출물 셋을 관문으로 놓고, 이번 생성 결과가 어디서
논문 수치와 갈리는지 셀 단위로 짚는다.

    관문 1  `generate_soh.py` 필터를 통과해 SOH 파일이 생겼는가
    관문 2  `name2agingConditionID.json` 에 이름이 있는가
            (`generate_split.py:36` — 없으면 분할에 들어가지 않는다)
            이 파일은 submodule HEAD 커밋 `febe174 update aging condition ID` 에서
            바뀌었다. **분할 JSON 과 논문 Table 1 은 그 직전 판을 쓴다.**
            그래서 두 판을 모두 관문으로 놓는다 (`gate2_head`, `gate2_pre_head`).
    관문 3  분할 JSON 에 이름이 있는가 (배포 실물)
    관문 4  로더의 `eol_cycle > early_cycle_threshold(=100)` 를 넘는가
            (`data_loader_soh_optimized.py:798`)

산출
-----
    analysis/out/table1_reconcile.json
    analysis/out/table1_gate_cells.csv        관문마다 걸린 셀
    analysis/out/removal_by_chemistry_subset.csv   화학×서브셋 제거율

실행
-----
    .venv-blife/Scripts/python.exe analysis/table1_reconcile.py
"""

import csv
import io
import json
import os
import pickle
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BMF = ROOT / 'upstream' / 'BatteryMFormer'
PROC = ROOT / 'data' / 'soh_v11' / 'processed_SOH'
OUT = ROOT / 'analysis' / 'out'

EARLY_CYCLE_THRESHOLD = 100

# generate_split.py:12 의 목록. Stanford(41) · MICH/MICH_EXP 개별 · SDU 는 없다.
SPLIT_DATASETS = ['CALB', 'NA-ion', 'ZN-coin', 'CALCE', 'HNEI', 'HUST', 'ISU_ILCC',
                  'MATR', 'RWTH', 'SNL', 'Stanford_2', 'Tongji', 'total_MICH',
                  'UL_PUR', 'XJTU']
LIION = ['CALCE', 'HNEI', 'HUST', 'ISU_ILCC', 'MATR', 'RWTH', 'SNL',
         'Stanford_2', 'Tongji', 'total_MICH', 'UL_PUR', 'XJTU']
DOMAIN = {'CALB': 'CALB', 'NA-ion': 'Na-ion', 'ZN-coin': 'Zn-ion'}
PAPER_TABLE1 = {'Li-ion': 963, 'CALB': 27, 'Na-ion': 31, 'Zn-ion': 95}


def _decode_first(s):
    """name2agingConditionID.json 은 같은 객체가 두 번 이어 붙어 있다. 앞 것을 쓴다."""
    dec = json.JSONDecoder()
    first, idx = dec.raw_decode(s)
    rest = s[idx:].strip()
    duplicated = False
    if rest:
        second, _ = dec.raw_decode(rest)
        duplicated = (second == first)
    return first, duplicated


def load_condition_map():
    s = io.open(BMF / 'name2agingConditionID.json', encoding='utf-8').read()
    return _decode_first(s)


def load_condition_map_pre_head():
    """HEAD 직전 판. 없으면 (None, 사유) 를 돌려준다."""
    import subprocess
    try:
        r = subprocess.run(['git', 'show', 'febe174^:name2agingConditionID.json'],
                           cwd=str(BMF), capture_output=True, encoding='utf-8')
    except OSError as exc:                                   # noqa: BLE001
        return None, f'git 실행 불가: {exc}'
    if r.returncode != 0:
        return None, f'git show 실패: {r.stderr.strip()[:120]}'
    first, _ = _decode_first(r.stdout)
    return first, None


def load_splits():
    sd = BMF / 'data_provider' / 'split_json'
    out = {}
    li = json.load(open(sd / 'pure_ood' / 'Liion_split_seed2021.json'))
    out['Li-ion'] = set(li['train'] + li['val'] + li['test'])
    zn = json.load(open(sd / 'pure_ood' / 'ZNcoin_split_seed2021.json'))
    out['Zn-ion'] = set(zn['train'] + zn['val'] + zn['test'])
    for dom, pat in (('CALB', 'CALB_loao_cond396_seed2021.json'),
                     ('Na-ion', 'NA-ion_loao_cond400_seed2021.json')):
        d = json.load(open(sd / 'loao' / pat))
        out[dom] = set(d['train'] + d['val'] + d['test'])
    return out


def read_chemistry():
    with open(OUT / 'dataset_cell_census.csv', encoding='utf-8') as f:
        lines = [ln for ln in f if not ln.startswith('#')]
    out = {}
    for r in csv.DictReader(lines):
        out[r['file']] = (r.get('cathode_normalized') or '').strip() or '미상'
    return out


def main():
    cond_map, dup = load_condition_map()
    cond_keys = set(cond_map)
    pre_map, pre_err = load_condition_map_pre_head()
    pre_keys = set(pre_map) if pre_map else set()
    splits = load_splits()
    chem = read_chemistry()

    rows = []
    for ds in SPLIT_DATASETS:
        p = PROC / ds
        if not p.is_dir():
            continue
        dom = DOMAIN.get(ds, 'Li-ion')
        for f in sorted(os.listdir(p)):
            if not f.endswith('.pkl'):
                continue
            n = len(pickle.load(open(p / f, 'rb'))['SOH'])
            rows.append({'domain': dom, 'dataset_dir': ds, 'cell': f,
                         'chemistry': chem.get(f, '미상'), 'traj_len': n,
                         'gate1_soh_generated': 1,
                         'gate2_in_condition_map': int(f in cond_keys),
                         'gate2_in_condition_map_pre_head': int(f in pre_keys),
                         'gate3_in_deployed_split': int(f in splits[dom]),
                         'gate4_len_gt_100': int(n > EARLY_CYCLE_THRESHOLD)})

    # 분할에는 있는데 이번 산출에 없는 셀
    have = {(r['domain'], r['cell']) for r in rows}
    for dom, cells in splits.items():
        for c in sorted(cells):
            if (dom, c) not in have:
                rows.append({'domain': dom, 'dataset_dir': '(없음)', 'cell': c,
                             'chemistry': chem.get(c, '미상'), 'traj_len': '',
                             'gate1_soh_generated': 0,
                             'gate2_in_condition_map': int(c in cond_keys),
                             'gate2_in_condition_map_pre_head': int(c in pre_keys),
                             'gate3_in_deployed_split': 1, 'gate4_len_gt_100': ''})

    with open(OUT / 'table1_gate_cells.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    summary = {'condition_map_file_duplicated_block': dup,
               'condition_map_keys': len(cond_keys),
               'condition_map_pre_head_keys': (len(pre_keys) if pre_map else None),
               'condition_map_pre_head_error': pre_err,
               'early_cycle_threshold': EARLY_CYCLE_THRESHOLD, 'domains': {}}
    for dom in ('Li-ion', 'CALB', 'Na-ion', 'Zn-ion'):
        dr = [r for r in rows if r['domain'] == dom]
        gen = [r for r in dr if r['gate1_soh_generated'] == 1]
        g2 = [r for r in gen if r['gate2_in_condition_map'] == 1]
        g2p = [r for r in gen if r['gate2_in_condition_map_pre_head'] == 1]
        g4 = [r for r in g2 if r['gate4_len_gt_100'] == 1]
        sp = splits[dom]
        sp_gen = [r for r in gen if r['gate3_in_deployed_split'] == 1]
        sp_g4 = [r for r in sp_gen if r['gate4_len_gt_100'] == 1]
        summary['domains'][dom] = {
            'paper_table1': PAPER_TABLE1[dom],
            'deployed_zip_cells': None,
            'gate1_generated': len(gen),
            'gate2_in_condition_map': len(g2),
            'gate2_in_condition_map_pre_head': len(g2p),
            'gate4_this_run_final': len(g4),
            'deployed_split_size': len(sp),
            'deployed_split_present_in_this_run': len(sp_gen),
            'deployed_split_and_len_gt100': len(sp_g4),
            'split_minus_unreachable_minus_le100': (
                len(sp) - len([r for r in dr if r['gate3_in_deployed_split'] == 1
                               and r['gate1_soh_generated'] == 0
                               and r['gate2_in_condition_map'] == 1])
                - len([r for r in sp_gen if r['gate4_len_gt_100'] == 0])),
            'in_split_but_not_generated': sorted(
                r['cell'] for r in dr if r['gate3_in_deployed_split'] == 1
                and r['gate1_soh_generated'] == 0),
            'generated_and_mapped_but_not_in_split': sorted(
                r['cell'] for r in g2 if r['gate3_in_deployed_split'] == 0),
        }

    json.dump(summary, open(OUT / 'table1_reconcile.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    # ---- 화학 × 서브셋 제거율 ----------------------------------------------
    cells_csv = OUT / 'filter_removal_cells.csv'
    if cells_csv.is_file():
        agg = defaultdict(lambda: {'input': 0, 'removed': 0})
        with open(cells_csv, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                a = agg[(r['chemistry'], r['subset'])]
                a['input'] += 1
                if r['outcome'] != 'KEPT':
                    a['removed'] += 1
        with open(OUT / 'removal_by_chemistry_subset.csv', 'w', newline='',
                  encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['cathode_normalized', 'subset', 'input', 'removed', 'removal_rate'])
            for (c, s), a in sorted(agg.items()):
                w.writerow([c, s, a['input'], a['removed'],
                            f'{a["removed"] / a["input"]:.4f}'])

    print(json.dumps({k: {kk: vv for kk, vv in v.items()
                          if not isinstance(vv, list)}
                      for k, v in summary['domains'].items()},
                     ensure_ascii=False, indent=2))
    for dom, v in summary['domains'].items():
        if v['in_split_but_not_generated']:
            print(f'{dom} 분할에는 있으나 이번 산출에 없음: {v["in_split_but_not_generated"]}')
        if v['generated_and_mapped_but_not_in_split']:
            print(f'{dom} 산출·매핑에는 있으나 분할에 없음: '
                  f'{v["generated_and_mapped_but_not_in_split"]}')


if __name__ == '__main__':
    main()
