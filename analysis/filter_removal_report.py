"""필터 제거율 집계 — 서브셋별·정규화 화학별·필터 조건별.

`generate_soh.py` 가 셀을 버리는 조건 다섯 가지와, 그 뒤 로더가 거는
`eol_cycle <= early_cycle_threshold(=100)` 조건까지 한 표에 올린다
(`data_loader_soh_optimized.py:798`). 로더 조건은 궤적 생성 단계에서는
파일을 지우지 않지만, 학습·평가 모집단에서는 셀이 빠진다.

화학 정규화는 기존 census 의 `cathode_normalized` 열을 쓴다
(`analysis/out/dataset_cell_census.csv`, `analysis/dataset_metadata_survey.py` 산출).

산출
-----
    docs/reports/filter_removal_by_chemistry.csv
    analysis/out/filter_removal_by_subset.csv
    analysis/out/filter_removal_summary.json

실행
-----
    .venv-blife/Scripts/python.exe analysis/filter_removal_report.py
"""

import csv
import json
import pickle
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEANED = ROOT / 'data' / 'extracted'
SOH_ROOT = ROOT / 'data' / 'soh_v11'
SOH_DIR = SOH_ROOT / 'SOH'
OUT = ROOT / 'analysis' / 'out'
REPORTS = ROOT / 'docs' / 'reports'

EARLY_CYCLE_THRESHOLD = 100     # data_loader_soh_optimized.py:129
REASON_CLASSES = ['EXCLUDED_CELLS', 'EMPTY_CYCLE_DATA', 'FILTER_THRESHOLD',
                  'SLOPE_NON_NEGATIVE', 'SLOPE_BELOW_MIN', 'UNCLASSIFIED']

# 배포 zip 이 담은 서브셋 18개. total_MICH 는 MICH+MICH_EXP 의 병합본이라 뺀다.
DEPLOYED_SUBSETS = ['CALB', 'CALCE', 'HNEI', 'HUST', 'ISU_ILCC', 'MATR', 'MICH',
                    'MICH_EXP', 'NA-ion', 'RWTH', 'SDU', 'SNL', 'Stanford',
                    'Stanford_2', 'Tongji', 'UL_PUR', 'XJTU', 'ZN-coin']


def read_chemistry():
    p = OUT / 'dataset_cell_census.csv'
    with open(p, encoding='utf-8') as f:
        lines = [ln for ln in f if not ln.startswith('#')]
    out = {}
    for r in csv.DictReader(lines):
        out[(r['subset'], r['file'])] = (r.get('cathode_normalized') or '').strip() or '미상'
    return out


def read_skipped():
    p = SOH_ROOT / 'soh_skipped_cells.csv'
    out = {}
    with open(p, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[(r['subset'], r['cell'])] = r
    return out


def main():
    chem = read_chemistry()
    skipped = read_skipped()

    # 서브셋별 입력 셀
    inputs = {}
    for sub in DEPLOYED_SUBSETS:
        d = CLEANED / sub
        inputs[sub] = sorted(p.name for p in d.glob('*.pkl')) if d.is_dir() else []

    # 살아남은 셀과 궤적 길이
    survivors = {}
    for sub in DEPLOYED_SUBSETS:
        d = SOH_DIR / sub
        if not d.is_dir():
            survivors[sub] = {}
            continue
        lens = {}
        for f in d.glob('*.pkl'):
            with open(f, 'rb') as fh:
                lens[f.name] = len(pickle.load(fh)['SOH'])
        survivors[sub] = lens

    rows = []
    for sub in DEPLOYED_SUBSETS:
        for cell in inputs[sub]:
            rec = {'subset': sub, 'cell': cell,
                   'chemistry': chem.get((sub, cell), '미상')}
            sk = skipped.get((sub, cell))
            if sk:
                rec['outcome'] = 'REMOVED'
                rec['reason_class'] = sk['reason_class']
                rec['reason'] = sk['reason']
                rec['traj_len'] = ''
            elif cell in survivors[sub]:
                n = survivors[sub][cell]
                rec['outcome'] = 'KEPT'
                rec['reason_class'] = ''
                rec['reason'] = ''
                rec['traj_len'] = n
            else:
                rec['outcome'] = 'NO_OUTPUT_NO_REASON'
                rec['reason_class'] = 'UNACCOUNTED'
                rec['reason'] = '산출 파일도 없고 제외 사유 기록도 없음'
                rec['traj_len'] = ''
            rec['dropped_by_loader_le100'] = int(
                rec['outcome'] == 'KEPT' and rec['traj_len'] <= EARLY_CYCLE_THRESHOLD)
            rows.append(rec)

    def aggregate(keyfn):
        agg = defaultdict(lambda: {k: 0 for k in
                                   ['input', 'kept', 'kept_gt100', 'dropped_loader_le100',
                                    'removed_total'] + REASON_CLASSES + ['UNACCOUNTED']})
        for r in rows:
            k = keyfn(r)
            a = agg[k]
            a['input'] += 1
            if r['outcome'] == 'KEPT':
                a['kept'] += 1
                if r['dropped_by_loader_le100']:
                    a['dropped_loader_le100'] += 1
                else:
                    a['kept_gt100'] += 1
            else:
                a['removed_total'] += 1
                a[r['reason_class']] = a.get(r['reason_class'], 0) + 1
        return agg

    by_chem = aggregate(lambda r: r['chemistry'])
    by_sub = aggregate(lambda r: r['subset'])

    cols = (['key', 'input', 'removed_total'] + REASON_CLASSES + ['UNACCOUNTED']
            + ['kept', 'removal_rate', 'dropped_loader_le100', 'kept_gt100',
               'final_rate_after_loader'])

    def write(path, agg, keyname):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([keyname] + cols[1:])
            for k in sorted(agg):
                a = agg[k]
                rr = a['removed_total'] / a['input'] if a['input'] else 0.0
                fr = a['kept_gt100'] / a['input'] if a['input'] else 0.0
                w.writerow([k, a['input'], a['removed_total']]
                           + [a.get(c, 0) for c in REASON_CLASSES + ['UNACCOUNTED']]
                           + [a['kept'], f'{rr:.4f}', a['dropped_loader_le100'],
                              a['kept_gt100'], f'{fr:.4f}'])
            tot = {c: sum(agg[k].get(c, 0) for k in agg) for c in
                   ['input', 'kept', 'kept_gt100', 'dropped_loader_le100', 'removed_total']
                   + REASON_CLASSES + ['UNACCOUNTED']}
            rr = tot['removed_total'] / tot['input'] if tot['input'] else 0.0
            fr = tot['kept_gt100'] / tot['input'] if tot['input'] else 0.0
            w.writerow(['(합계)', tot['input'], tot['removed_total']]
                       + [tot.get(c, 0) for c in REASON_CLASSES + ['UNACCOUNTED']]
                       + [tot['kept'], f'{rr:.4f}', tot['dropped_loader_le100'],
                          tot['kept_gt100'], f'{fr:.4f}'])

    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    write(REPORTS / 'filter_removal_by_chemistry.csv', by_chem, 'cathode_normalized')
    write(OUT / 'filter_removal_by_subset.csv', by_sub, 'subset')

    with open(OUT / 'filter_removal_cells.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['subset', 'cell', 'chemistry', 'outcome',
                                          'reason_class', 'reason', 'traj_len',
                                          'dropped_by_loader_le100'])
        w.writeheader()
        w.writerows(rows)

    # 조건별 제거 수
    by_reason = defaultdict(int)
    for r in rows:
        if r['outcome'] != 'KEPT':
            by_reason[r['reason_class']] += 1
    summary = {
        'input_cells': len(rows),
        'kept_after_generate_soh': sum(1 for r in rows if r['outcome'] == 'KEPT'),
        'kept_after_loader_gt100': sum(1 for r in rows if r['outcome'] == 'KEPT'
                                       and not r['dropped_by_loader_le100']),
        'removed_by_reason': dict(sorted(by_reason.items())),
        'early_cycle_threshold': EARLY_CYCLE_THRESHOLD,
    }
    json.dump(summary, open(OUT / 'filter_removal_summary.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
