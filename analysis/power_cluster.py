"""검정력 계산 — 클러스터 구조를 재고, 증분 R² 0.05 를 잡을 수 있는지 판정한다.

**통계 방법을 고르지 않는다.** 급내상관·설계효과·유효표본을 재고, 그 수치로
80% 검정력이 나오는지 판정하고, 안 나오면 탐지 가능한 최소 증분 R² 를 역산한다.
대안 방법은 이 데이터 구조에서 무엇이 성립하고 무엇이 성립하지 않는지만 적는다.

산출
-----
    analysis/out/power_analysis.json    모든 수치
    docs/reports/power_analysis.md      사람이 읽는 표

실행
-----
    .venv-blife/Scripts/python.exe analysis/power_cluster.py
"""

import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import f as f_dist
from scipy.stats import ncf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis' / 'out'
REPORTS = ROOT / 'docs' / 'reports'
DV_CSV = REPORTS / 'dv_candidates.csv'

ALPHA = 0.05
TARGET_POWER = 0.80
DELTA_R2 = 0.05                 # 설계안의 중단 기준
R2_FULL_GRID = [0.3, 0.5, 0.7]
N_PREDICTORS = 13               # 설계안이 말한 예측변수 수
U_GRID = [1, 3, 13]             # 검정 대상 블록의 예측변수 수

# 클러스터로 쓰는 서브셋 — `generate_split.py:12` 의 15개.
# `Stanford/` 는 로더가 모든 `Stanford*` 를 `Stanford_2` 로 보내므로(
# `data_loader_soh_optimized.py:777-778`) 배포 모집단에 들어가지 않고,
# 그 41셀 중 38개는 `Stanford_2` 와 바이트 동일한 중복이다
# (`docs/reports/2026-08-13_dataset_metadata_survey_fix.md` §3).
# `SDU` 는 BatteryMFormer 처리 경로 자체가 없다.
CLUSTER_SUBSETS = ['CALB', 'NA-ion', 'ZN-coin', 'CALCE', 'HNEI', 'HUST', 'ISU_ILCC',
                   'MATR', 'RWTH', 'SNL', 'Stanford_2', 'Tongji', 'total_MICH',
                   'UL_PUR', 'XJTU']

# 종속변수 — 설계안이 든 넷. processed 판을 쓴다.
DVS = {
    'curvature_quad_lifefrac': 'processed__curv_quad_coef_lifefrac',
    'fade_rate_per_cycle': 'processed__fade_rate_per_cycle',
    'knee_position_lifefrac': 'processed__knee_bilinear_lifefrac',
    'eol_cycle': 'processed__eol_cycle',
}


def icc_oneway(groups):
    """일원 변량효과 ANOVA 로 급내상관을 낸다. 불균형 설계를 다룬다.

    groups: {클러스터: [값, ...]}
    반환: ICC, MSB, MSW, m0(보정 평균 클러스터 크기), k, N
    """
    groups = {g: np.asarray(v, dtype=float) for g, v in groups.items()}
    groups = {g: v[np.isfinite(v)] for g, v in groups.items()}
    groups = {g: v for g, v in groups.items() if len(v) >= 1}
    k = len(groups)
    sizes = np.array([len(v) for v in groups.values()], dtype=float)
    N = float(sizes.sum())
    if k < 2 or N <= k:
        return None
    grand = float(np.concatenate(list(groups.values())).mean())
    ssb = float(sum(len(v) * (v.mean() - grand) ** 2 for v in groups.values()))
    ssw = float(sum(((v - v.mean()) ** 2).sum() for v in groups.values()))
    msb = ssb / (k - 1)
    msw = ssw / (N - k)
    m0 = (N - (sizes ** 2).sum() / N) / (k - 1)
    denom = msb + (m0 - 1) * msw
    icc = (msb - msw) / denom if denom > 0 else float('nan')
    return {'icc': float(icc), 'icc_clipped': float(max(icc, 0.0)),
            'MSB': msb, 'MSW': msw, 'm0': float(m0), 'k': int(k), 'N': int(N),
            'mean_cluster_size': float(N / k),
            'cluster_sizes': {g: int(len(v)) for g, v in sorted(groups.items())}}


def power_f(u, v, f2, alpha=ALPHA):
    """증분 F 검정의 검정력. 비중심모수 lambda = f^2 * (u+v+1)."""
    if v <= 0:
        return float('nan')
    lam = f2 * (u + v + 1)
    fc = f_dist.ppf(1 - alpha, u, v)
    return float(1.0 - ncf.cdf(fc, u, v, lam))


def min_detectable_delta_r2(u, n_eff, r2_full, alpha=ALPHA, target=TARGET_POWER):
    """80% 검정력을 주는 최소 증분 R² 를 이분법으로 역산한다."""
    v = n_eff - u - 1 if u >= N_PREDICTORS else n_eff - N_PREDICTORS - 1
    if v <= 1:
        return None, v
    lo, hi = 1e-6, 0.95 * (1 - 1e-9)
    if power_f(u, v, hi / max(1 - r2_full, 1e-9)) < target:
        return None, v
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f2 = mid / max(1 - r2_full, 1e-9)
        if power_f(u, v, f2) < target:
            lo = mid
        else:
            hi = mid
    return float(hi), v


def read_rows():
    if not DV_CSV.is_file():
        raise SystemExit(f'{DV_CSV} 가 없습니다. analysis/dv_candidates.py 를 먼저 돌리십시오.')
    with open(DV_CSV, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r['subset'] in CLUSTER_SUBSETS]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = read_rows()

    result = {'alpha': ALPHA, 'target_power': TARGET_POWER,
              'delta_r2_stop_rule': DELTA_R2, 'n_predictors_design': N_PREDICTORS,
              'dv': {}}

    for label, col in DVS.items():
        groups = {}
        for r in rows:
            v = r.get(col, '')
            if v in ('', None):
                continue
            try:
                fv = float(v)
            except ValueError:
                continue
            if not np.isfinite(fv):
                continue
            groups.setdefault(r['subset'], []).append(fv)
        st = icc_oneway(groups)
        if st is None:
            result['dv'][label] = {'error': 'CLUSTERS_INSUFFICIENT'}
            continue

        rho = st['icc_clipped']
        mbar = st['mean_cluster_size']
        deff_mean = 1.0 + (mbar - 1.0) * rho          # 설계안이 쓴 정의
        deff_m0 = 1.0 + (st['m0'] - 1.0) * rho        # 불균형 보정 크기를 쓴 것
        n_eff_mean = st['N'] / deff_mean
        n_eff_m0 = st['N'] / deff_m0

        entry = {**st, 'design_effect_mean_size': deff_mean,
                 'design_effect_m0': deff_m0,
                 'n_eff_mean_size': n_eff_mean, 'n_eff_m0': n_eff_m0,
                 'power': {}, 'min_detectable_delta_r2': {}}

        for n_eff_label, n_eff in (('n_eff_mean_size', n_eff_mean), ('n_eff_m0', n_eff_m0),
                                   ('n_raw', float(st['N']))):
            entry['power'][n_eff_label] = {}
            entry['min_detectable_delta_r2'][n_eff_label] = {}
            for r2f in R2_FULL_GRID:
                f2 = DELTA_R2 / (1.0 - r2f)
                per_u = {}
                per_u_min = {}
                for u in U_GRID:
                    v = n_eff - N_PREDICTORS - 1 if u < N_PREDICTORS else n_eff - u - 1
                    per_u[f'u={u}'] = {
                        'df_denom': round(float(v), 2),
                        'f2': round(float(f2), 5),
                        'power': (round(power_f(u, v, f2), 4) if v > 1 else None),
                    }
                    md, vv = min_detectable_delta_r2(u, n_eff, r2f)
                    per_u_min[f'u={u}'] = (round(md, 4) if md is not None else None)
                entry['power'][n_eff_label][f'R2_full={r2f}'] = per_u
                entry['min_detectable_delta_r2'][n_eff_label][f'R2_full={r2f}'] = per_u_min
        result['dv'][label] = entry

    json.dump(result, open(OUT / 'power_analysis.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    # ---------------- 사람이 읽는 표 -----------------------------------------
    L = []
    L.append('# 검정력 계산 — 1a 단계가 실행 가능한가\n')
    L.append('`analysis/power_cluster.py` 가 만든 표입니다. 원자료는 '
             '`analysis/out/power_analysis.json` 입니다.\n')
    L.append(f'- 유의수준 {ALPHA}, 목표 검정력 {TARGET_POWER}\n'
             f'- 설계안의 중단 기준 증분 R² = {DELTA_R2}\n'
             f'- Cohen f² = ΔR² / (1 − R²_full)\n'
             f'- 비중심모수 λ = f² · (u + v + 1)\n'
             f'- 설계안의 예측변수 수 {N_PREDICTORS}개. 검정 대상 블록 크기 u 는 '
             f'{U_GRID} 세 가지로 나눠 냅니다\n')

    L.append('\n## 1. 클러스터 구조와 급내상관\n')
    L.append('| 종속변수 | 클러스터 k | 셀 N | 평균 크기 m̄ | 보정 크기 m₀ | ICC ρ | '
             '설계효과 1+(m̄−1)ρ | 유효표본 N/deff |')
    L.append('|---|---:|---:|---:|---:|---:|---:|---:|')
    for label, e in result['dv'].items():
        if 'error' in e:
            L.append(f'| {label} | — | — | — | — | — | — | 산출 불가 ({e["error"]}) |')
            continue
        L.append(f'| {label} | {e["k"]} | {e["N"]} | {e["mean_cluster_size"]:.1f} | '
                 f'{e["m0"]:.1f} | {e["icc"]:.4f} | {e["design_effect_mean_size"]:.1f} | '
                 f'{e["n_eff_mean_size"]:.1f} |')
    L.append('\n설계효과를 보정 크기 m₀ 로 계산하면 유효표본은 다음과 같습니다 — '
             '클러스터 크기가 13~240 으로 갈려 두 정의의 값이 벌어집니다.\n')
    L.append('| 종속변수 | 1+(m₀−1)ρ | 유효표본(m₀ 기준) |')
    L.append('|---|---:|---:|')
    for label, e in result['dv'].items():
        if 'error' in e:
            continue
        L.append(f'| {label} | {e["design_effect_m0"]:.1f} | {e["n_eff_m0"]:.1f} |')

    L.append('\n## 2. 증분 R² 0.05 의 검정력\n')
    for label, e in result['dv'].items():
        if 'error' in e:
            continue
        L.append(f'\n### {label}\n')
        L.append('| 표본 기준 | R²_full | f² | u=1 | u=3 | u=13 |')
        L.append('|---|---:|---:|---:|---:|---:|')
        for nl in ('n_raw', 'n_eff_mean_size', 'n_eff_m0'):
            for r2f in R2_FULL_GRID:
                d = e['power'][nl][f'R2_full={r2f}']
                def fmt(u):
                    p = d[f'u={u}']['power']
                    return '—' if p is None else f'{p:.3f}'
                L.append(f'| {nl} | {r2f} | {d["u=1"]["f2"]:.4f} | '
                         f'{fmt(1)} | {fmt(3)} | {fmt(13)} |')

    L.append('\n## 3. 80% 검정력으로 탐지 가능한 최소 증분 R²\n')
    for label, e in result['dv'].items():
        if 'error' in e:
            continue
        L.append(f'\n### {label}\n')
        L.append('| 표본 기준 | R²_full | u=1 | u=3 | u=13 |')
        L.append('|---|---:|---:|---:|---:|')
        for nl in ('n_raw', 'n_eff_mean_size', 'n_eff_m0'):
            for r2f in R2_FULL_GRID:
                d = e['min_detectable_delta_r2'][nl][f'R2_full={r2f}']
                def fmt2(u):
                    v = d[f'u={u}']
                    return '탐지 불가' if v is None else f'{v:.3f}'
                L.append(f'| {nl} | {r2f} | {fmt2(1)} | {fmt2(3)} | {fmt2(13)} |')

    (REPORTS / 'power_analysis.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(f'{OUT / "power_analysis.json"}')
    print(f'{REPORTS / "power_analysis.md"}')


if __name__ == '__main__':
    main()
