"""궤적의 어디까지가 측정이고 어디부터가 외삽인가 — 셀마다 경계를 찾는다.

`generate_soh.py` 는 외삽 여부를 기록하지 않는다. 산출 pkl 만 보면 마지막
몇 점이 측정값인지 알 수 없다. 그래서 원본 pkl 을 한 번 더 읽어
`generate_soh.py` 의 계산을 **외삽 직전까지** 그대로 되짚고, 그 지점의 길이를
`n_measured` 로 기록한다.

되짚기가 맞는지는 스스로 검증한다 — 되짚은 앞부분이 산출 pkl 의 같은 구간과
값이 같은지 셀마다 대조하고(`prefix_match`), 어긋난 셀은 사유와 함께 남긴다.

산출
-----
    analysis/out/traj_boundary.csv
        subset, cell, n_measured, n_total, n_extrapolated, branch,
        prefix_match, max_abs_diff, note

실행
-----
    .venv-blife/Scripts/python.exe analysis/soh_measured_boundary.py
"""

import csv
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLEANED = ROOT / 'data' / 'extracted'
SOH_DIR = ROOT / 'data' / 'soh_v11' / 'SOH'
OUT = ROOT / 'analysis' / 'out'

# generate_soh.py:36-40 의 목록을 그대로 옮긴 것. 값을 고치지 말 것.
EXCLUDED_CELLS = {
    'ISU-ILCC_G26C1.pkl', 'ISU-ILCC_G26C2.pkl', 'ISU-ILCC_G26C3.pkl', 'ISU-ILCC_G26C4.pkl',
    'ISU-ILCC_G11C1.pkl', 'ISU-ILCC_G11C2.pkl', 'ISU-ILCC_G11C3.pkl', 'ISU-ILCC_G11C4.pkl',
    'ISU-ILCC_G42C4.pkl', 'ISU-ILCC_G9C4.pkl', 'ISU-ILCC_G25C4.pkl', 'ISU-ILCC_G40C3.pkl',
}


def fix_spike_drops(raw_sohs, max_drop_per_cycle=0.04):
    """generate_soh.py:15-32 과 같은 계산."""
    if len(raw_sohs) <= 1:
        return list(raw_sohs)
    fixed = list(raw_sohs)
    for i in range(1, len(raw_sohs)):
        if raw_sohs[i - 1] - raw_sohs[i] > max_drop_per_cycle:
            fixed[i] = fixed[i - 1]
    return fixed


def measured_part(cell_path, cell_name):
    """외삽 직전까지의 (SOH, cycle_numbers, 분기) 를 돌려준다.

    generate_soh.py:56-129 를 그대로 따라간다. 외삽 블록(:130-184)은 밟지 않는다.
    """
    dataset_name = cell_name.split('_')[0]
    if dataset_name == 'MICH':
        dataset_name = 'total_MICH'
    filter_threshold = 0.925 if dataset_name == 'CALB' else 0.825
    eol_threshold = 0.9 if dataset_name == 'CALB' else 0.8

    with open(cell_path, 'rb') as f:
        data = pickle.load(f)

    nominal_capacity = data['nominal_capacity_in_Ah']
    nominal_capacity = 1.85 if 'RWTH' in cell_name else nominal_capacity
    discharge_depth = data['SOC_interval'][1] - data['SOC_interval'][0]

    raw_sohs, cycle_numbers = [], []
    for one_cycle_data in data['cycle_data']:
        qd = np.array(one_cycle_data['discharge_capacity_in_Ah'])
        soh = max(qd) / nominal_capacity / discharge_depth
        raw_sohs.append(soh)
        cycle_numbers.append(one_cycle_data['cycle_number'])
    del data

    if not raw_sohs:
        return None, None, 'EMPTY'

    if 'ZN-coin_441-1_20231227204855_08_4.' in cell_name:
        new = fix_spike_drops(raw_sohs[:-5], max_drop_per_cycle=0.03)
        new.extend(raw_sohs[-5:])
        raw_sohs = new
    else:
        raw_sohs = fix_spike_drops(raw_sohs, max_drop_per_cycle=0.03)

    if raw_sohs[-1] > filter_threshold:
        return None, None, 'FILTERED_TOO_HEALTHY'

    if raw_sohs[-1] <= eol_threshold:
        eol = 0
        for cn, soh in zip(cycle_numbers, raw_sohs):
            if soh <= eol_threshold:
                eol = cn
                break
        eol = int(eol)
        return raw_sohs[:eol], cycle_numbers[:eol], 'TRUNCATED_AT_EOL'

    return raw_sohs, cycle_numbers, 'EXTRAPOLATED_CANDIDATE'


def measured_part_calb():
    """CALB 는 pkl 이 아니라 엑셀에서 나온다. generate_CALB_soh.py 를 그대로 따라간다.

    반환: {셀이름.pkl: (측정 SOH 목록, 분기)}
    """
    import pandas as pd

    xlsx = ROOT / 'upstream' / 'BatteryMFormer' / 'process_scripts' / 'overall_CALB_cycling_data.xlsx'
    sheets = ['0℃循环', '25℃ 循环', '35℃ 循环', '45℃循环']
    out = {}
    for sheet in sheets:
        df = pd.read_excel(xlsx, sheet_name=sheet)
        cols = df.columns.tolist()
        if sheet == '0℃循环':
            start = [cols.index(i) for i in cols if i.startswith('A1')]
            names = ['CALB_0_' + i.replace('A', 'B') for i in cols if i.startswith('A1')]
        elif sheet == '25℃ 循环':
            start = [cols.index(i) for i in cols if i.startswith('T25')]
            names = ['CALB_25_' + i for i in cols if i.startswith('T25')]
        else:
            start = [cols.index(i) for i in cols if i.startswith('B')]
            pre = 'CALB_35_' if sheet == '35℃ 循环' else 'CALB_45_'
            names = [pre + i for i in cols if i.startswith('B')]

        for name, ci, di in zip(names, [i + 1 for i in start], [i + 4 for i in start]):
            cdf = pd.DataFrame({'cycle_number': df.iloc[:, ci].tolist(),
                                'time_in_s': df.iloc[:, ci + 1].values.tolist(),
                                'discharge_capacity_in_Ah': df.iloc[:, di].tolist()})
            cdf = cdf.dropna()
            if cdf.empty:
                continue
            nominal = cdf['discharge_capacity_in_Ah'].values.tolist()[0]
            soh = np.array(cdf['discharge_capacity_in_Ah']) / nominal
            mask = np.isnan(soh)
            raw = soh[~mask].tolist()
            cycles = np.arange(1, len(cdf) + 1)[~mask].tolist()
            if not raw:
                continue
            if raw[-1] > 0.925:
                out[name + '.pkl'] = (None, 'FILTERED_TOO_HEALTHY')
                continue
            if name == 'CALB_35_B229':
                raw = fix_spike_drops(raw, max_drop_per_cycle=0.03)
            if raw[-1] <= 0.9:
                eol = 0
                for cn, s in zip(cycles, raw):
                    if s <= 0.9:
                        eol = int(cn)
                        break
                out[name + '.pkl'] = (raw[:eol], 'TRUNCATED_AT_EOL')
            else:
                out[name + '.pkl'] = (raw, 'EXTRAPOLATED_CANDIDATE')
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    calb = measured_part_calb()
    subsets = sorted(p.name for p in SOH_DIR.iterdir() if p.is_dir())
    for sub in subsets:
        if sub == 'CALB':
            for gf in sorted((SOH_DIR / 'CALB').glob('*.pkl')):
                with open(gf, 'rb') as f:
                    gen_soh = np.asarray(pickle.load(f)['SOH'], dtype=float)
                meas, branch = calb.get(gf.name, (None, 'NO_EXCEL_RECORD'))
                if meas is None:
                    rows.append({'subset': 'CALB', 'cell': gf.name, 'n_measured': '',
                                 'n_total': len(gen_soh), 'n_extrapolated': '',
                                 'branch': branch, 'prefix_match': 0, 'max_abs_diff': '',
                                 'note': '엑셀 되짚기가 제외 판정'})
                    continue
                n = min(len(meas), len(gen_soh))
                mx = float(np.max(np.abs(np.asarray(meas[:n]) - gen_soh[:n]))) if n else float('nan')
                rows.append({
                    'subset': 'CALB', 'cell': gf.name, 'n_measured': len(meas),
                    'n_total': len(gen_soh), 'n_extrapolated': len(gen_soh) - len(meas),
                    'branch': 'EXTRAPOLATED' if len(gen_soh) > len(meas) else branch,
                    'prefix_match': int(mx < 1e-9), 'max_abs_diff': f'{mx:.3e}',
                    'note': '엑셀 경로(generate_CALB_soh.py)',
                })
            print(f'[CALB] {len(calb)}셀(엑셀 경로)', flush=True)
            continue
        src_dir = CLEANED / sub
        if not src_dir.is_dir():
            print(f'  원본 없음, 건너뜀: {sub}')
            continue
        gen_files = sorted((SOH_DIR / sub).glob('*.pkl'))
        print(f'[{sub}] {len(gen_files)}셀', flush=True)
        for gf in gen_files:
            cell = gf.name
            with open(gf, 'rb') as f:
                gen = pickle.load(f)
            gen_soh = np.asarray(gen['SOH'], dtype=float)

            src = src_dir / cell
            if not src.is_file():
                # CALB 는 엑셀 경로에서 나온다. 원본 pkl 과 셀 이름이 겹치지 않을 수 있다.
                rows.append({'subset': sub, 'cell': cell, 'n_measured': '',
                             'n_total': len(gen_soh), 'n_extrapolated': '',
                             'branch': 'NO_SOURCE_PKL', 'prefix_match': '',
                             'max_abs_diff': '', 'note': '원본 pkl 없음(엑셀 경로 산출로 추정)'})
                continue
            try:
                meas, _, branch = measured_part(src, cell)
            except Exception as exc:                            # noqa: BLE001
                rows.append({'subset': sub, 'cell': cell, 'n_measured': '',
                             'n_total': len(gen_soh), 'n_extrapolated': '',
                             'branch': 'ERROR', 'prefix_match': 0, 'max_abs_diff': '',
                             'note': f'{type(exc).__name__}: {exc}'[:160]})
                continue

            if meas is None:
                rows.append({'subset': sub, 'cell': cell, 'n_measured': '',
                             'n_total': len(gen_soh), 'n_extrapolated': '',
                             'branch': branch, 'prefix_match': 0, 'max_abs_diff': '',
                             'note': '되짚기는 제외 판정인데 산출물이 있다'})
                continue

            n_meas = min(len(meas), len(gen_soh))
            diff = np.abs(np.asarray(meas[:n_meas]) - gen_soh[:n_meas])
            mx = float(diff.max()) if n_meas else float('nan')
            rows.append({
                'subset': sub, 'cell': cell,
                'n_measured': len(meas), 'n_total': len(gen_soh),
                'n_extrapolated': len(gen_soh) - len(meas),
                'branch': 'EXTRAPOLATED' if len(gen_soh) > len(meas) else branch,
                'prefix_match': int(mx < 1e-9), 'max_abs_diff': f'{mx:.3e}',
                'note': '',
            })

    with open(OUT / 'traj_boundary.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['subset', 'cell', 'n_measured', 'n_total',
                                          'n_extrapolated', 'branch', 'prefix_match',
                                          'max_abs_diff', 'note'])
        w.writeheader()
        w.writerows(rows)

    ok = sum(1 for r in rows if r['prefix_match'] == 1)
    print(f'\n{len(rows)}셀 · 되짚기 일치 {ok} · 불일치 {len(rows) - ok}')
    bad = [r for r in rows if r['prefix_match'] != 1]
    for r in bad[:15]:
        print('  ', r['subset'], r['cell'], r['branch'], r['note'])
    if len(bad) > 15:
        print(f'   … 그 외 {len(bad) - 15}개는 CSV 참조')
    return 0


if __name__ == '__main__':
    sys.exit(main())
