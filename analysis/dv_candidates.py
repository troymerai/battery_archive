"""종속변수 후보 정량화 — knee 3종 × 곡률 3종 × 궤적 2판.

**이 스크립트는 어느 정의가 낫다고 판단하지 않는다.** 후보마다 값을 내고,
정의끼리 얼마나 갈리는지를 순위상관과 값차이로 잰다. 고르는 것은 사람 몫이다.

궤적 2판
---------
    observed   `data/soh_v11/SOH/` 의 Step 1 산출을 측정 구간까지 자른 것.
               외삽 꼬리 없음, PCHIP 평활 없음
    processed  `data/soh_v11/processed_SOH/` 의 Step 2·3·5 산출 전체.
               외삽 꼬리 있음, PCHIP 평활 있음

경계(`n_measured`)는 `analysis/soh_measured_boundary.py` 가 만든
`analysis/out/traj_boundary.csv` 에서 읽는다.

두 판의 차이에는 **꼬리와 평활 두 가지가 함께 들어 있다.** 어느 쪽이 얼마나
기여했는지 나누어 보려면 셀마다 함께 남기는 `n_extrapolated` ·
`extrap_frac` · `pchip_changed` · `pchip_max_abs_diff` 를 보십시오.

산출
-----
    docs/reports/dv_candidates.csv          셀 단위 전체 지표
    docs/reports/dv_disagreement_cells.csv  정의가 크게 갈리는 셀
    analysis/out/dv_correlations.json       순위상관 행렬(전체·화학별)
    analysis/out/dv_failures.csv            지표별 산출 실패 셀

실행
-----
    .venv-blife/Scripts/python.exe analysis/dv_candidates.py
"""

import csv
import json
import pickle
from pathlib import Path

import numpy as np
from scipy.signal import savgol_filter
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
SOH_DIR = ROOT / 'data' / 'soh_v11' / 'SOH'
PROC_DIR = ROOT / 'data' / 'soh_v11' / 'processed_SOH'
OUT = ROOT / 'analysis' / 'out'
REPORTS = ROOT / 'docs' / 'reports'

MIN_POINTS = 15          # 이보다 짧으면 어떤 지표도 내지 않는다
EDGE_FRAC = 0.05         # 곡률 최댓점에서 양 끝 5% 를 제외한다
TANGENT_FRAC = 0.25      # 접선 교차에 쓰는 앞·뒤 구간 비율
GRID_MIN, GRID_MAX = 0.10, 0.90   # 이중선형 절점 탐색 범위
GRID_N = 200

KNEE_METHODS = ['curvature_max', 'bilinear', 'tangent_cross']
CURV_METHODS = ['quad_coef', 'resid_signmean', 'slope_ratio']
AXES = ['cycle', 'lifefrac']
VERSIONS = ['observed', 'processed']


# --------------------------------------------------------------------------
# knee 후보 3종
# --------------------------------------------------------------------------
def knee_curvature_max(x, y):
    """정규화한 (t, s) 평면에서 곡률 |s''|/(1+s'^2)^1.5 이 최대인 지점."""
    n = len(x)
    if n < MIN_POINTS:
        return None, 'TOO_SHORT'
    span = y.max() - y.min()
    if span <= 0:
        return None, 'FLAT'
    t = (x - x[0]) / (x[-1] - x[0])
    s = (y - y.min()) / span
    win = min(n if n % 2 else n - 1, max(5, (n // 20) * 2 + 1))
    if win >= n:
        win = n - 1 if (n - 1) % 2 else n - 2
    if win < 5:
        return None, 'TOO_SHORT'
    try:
        s_sm = savgol_filter(s, win, 3)
    except Exception:                                     # noqa: BLE001
        return None, 'SAVGOL_FAILED'
    d1 = np.gradient(s_sm, t)
    d2 = np.gradient(d1, t)
    kappa = np.abs(d2) / np.power(1.0 + d1 ** 2, 1.5)
    lo = max(1, int(np.floor(EDGE_FRAC * n)))
    hi = min(n - 1, int(np.ceil((1 - EDGE_FRAC) * n)))
    if hi - lo < 3:
        return None, 'EDGE_EXCLUSION_EMPTY'
    j = lo + int(np.argmax(kappa[lo:hi]))
    return float(x[j]), None


def knee_bilinear(x, y):
    """연속 조각선형(hinge) 적합의 절점. 격자 탐색으로 SSE 최소점을 찾는다."""
    n = len(x)
    if n < MIN_POINTS:
        return None, 'TOO_SHORT'
    t = (x - x[0]) / (x[-1] - x[0])
    cands = np.linspace(GRID_MIN, GRID_MAX, GRID_N)
    best_sse, best_tb, best_b2 = np.inf, None, None
    for tb in cands:
        design = np.column_stack([np.ones(n), t, np.maximum(t - tb, 0.0)])
        try:
            beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        except np.linalg.LinAlgError:
            continue
        sse = float(np.sum((y - design @ beta) ** 2))
        if sse < best_sse:
            best_sse, best_tb, best_b2 = sse, tb, float(beta[2])
    if best_tb is None:
        return None, 'NO_FIT'
    if best_tb <= cands[0] + 1e-12 or best_tb >= cands[-1] - 1e-12:
        return None, 'BREAKPOINT_AT_GRID_EDGE'
    if abs(best_b2) < 1e-9:
        return None, 'NO_SLOPE_CHANGE'
    return float(x[0] + best_tb * (x[-1] - x[0])), None


def knee_tangent_cross(x, y):
    """앞 25% 구간과 뒤 25% 구간에 맞춘 두 직선의 교점."""
    n = len(x)
    if n < MIN_POINTS:
        return None, 'TOO_SHORT'
    k = max(3, int(round(TANGENT_FRAC * n)))
    if 2 * k > n:
        return None, 'SEGMENTS_OVERLAP'
    a1, b1 = np.polyfit(x[:k], y[:k], 1)
    a2, b2 = np.polyfit(x[-k:], y[-k:], 1)
    denom = a1 - a2
    scale = max(abs(a1), abs(a2), 1e-30)
    if abs(denom) < 1e-6 * scale:
        return None, 'TANGENTS_PARALLEL'
    xc = (b2 - b1) / denom
    if not np.isfinite(xc) or xc < x[0] or xc > x[-1]:
        return None, 'INTERSECTION_OUT_OF_RANGE'
    return float(xc), None


# --------------------------------------------------------------------------
# 곡률 후보 3종
# --------------------------------------------------------------------------
def curv_quad_coef(u, y):
    """2차 다항 적합의 이차항 계수."""
    if len(u) < MIN_POINTS:
        return None, 'TOO_SHORT'
    try:
        c = np.polyfit(u, y, 2)
    except Exception:                                     # noqa: BLE001
        return None, 'POLYFIT_FAILED'
    return float(c[0]), None


def curv_resid_signmean(u, y):
    """직선 적합 잔차 부호의 평균. 양수면 잔차가 대체로 직선 위쪽."""
    if len(u) < MIN_POINTS:
        return None, 'TOO_SHORT'
    a, b = np.polyfit(u, y, 1)
    r = y - (a * u + b)
    sg = np.sign(r)
    if np.all(sg == 0):
        return None, 'EXACTLY_LINEAR'
    return float(np.mean(sg)), None


def curv_slope_ratio(u, y):
    """전반부 회귀기울기 / 후반부 회귀기울기."""
    n = len(u)
    if n < MIN_POINTS:
        return None, 'TOO_SHORT'
    m = n // 2
    if m < 3 or n - m < 3:
        return None, 'HALF_TOO_SHORT'
    s1 = np.polyfit(u[:m], y[:m], 1)[0]
    s2 = np.polyfit(u[m:], y[m:], 1)[0]
    if abs(s2) < 1e-12:
        return None, 'SECOND_HALF_SLOPE_ZERO'
    return float(s1 / s2), None


# --------------------------------------------------------------------------
def load_traj(path):
    with open(path, 'rb') as f:
        d = pickle.load(f)
    y = np.asarray(d['SOH'], dtype=float)
    x = np.asarray(d['cycle_numbers'], dtype=float)
    if len(x) != len(y):
        m = min(len(x), len(y))
        x, y = x[:m], y[:m]
    return x, y


def measure(x, y):
    """한 궤적에 대해 knee 3종 · 곡률 3종 × 축 2종을 낸다."""
    vals, fails = {}, {}
    eol = float(x[-1]) if len(x) else float('nan')
    for name, fn in zip(KNEE_METHODS, (knee_curvature_max, knee_bilinear, knee_tangent_cross)):
        v, err = fn(x, y)
        vals[f'knee_{name}_cycle'] = v
        vals[f'knee_{name}_lifefrac'] = (v / eol) if (v is not None and eol > 0) else None
        if err:
            fails[f'knee_{name}'] = err
    axis_u = {'cycle': x, 'lifefrac': (x / eol) if eol > 0 else x}
    for ax in AXES:
        u = axis_u[ax]
        for name, fn in zip(CURV_METHODS, (curv_quad_coef, curv_resid_signmean, curv_slope_ratio)):
            v, err = fn(u, y)
            vals[f'curv_{name}_{ax}'] = v
            if err:
                fails[f'curv_{name}_{ax}'] = err
    vals['eol_cycle'] = eol
    vals['n_points'] = len(x)
    vals['soh_first'] = float(y[0]) if len(y) else None
    vals['soh_last'] = float(y[-1]) if len(y) else None
    vals['fade_rate_per_cycle'] = (
        float((y[0] - y[-1]) / (x[-1] - x[0])) if len(x) > 1 and x[-1] != x[0] else None
    )
    return vals, fails


def read_boundary():
    p = OUT / 'traj_boundary.csv'
    if not p.is_file():
        raise SystemExit(f'{p} 가 없습니다. analysis/soh_measured_boundary.py 를 먼저 돌리십시오.')
    out = {}
    with open(p, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[(r['subset'], r['cell'])] = r
    return out


def read_chemistry():
    p = OUT / 'dataset_cell_census.csv'
    out = {}
    with open(p, encoding='utf-8') as f:
        lines = [ln for ln in f if not ln.startswith('#')]
    for r in csv.DictReader(lines):
        out[(r['subset'], r['file'])] = r.get('cathode_normalized') or '미상'
    return out


def spearman_matrix(rows, keys):
    """keys 끼리의 Spearman 순위상관 행렬. 쌍마다 둘 다 유한한 셀만 쓴다."""
    mat = {}
    for a in keys:
        mat[a] = {}
        for b in keys:
            va = np.array([r.get(a) if r.get(a) is not None else np.nan for r in rows], dtype=float)
            vb = np.array([r.get(b) if r.get(b) is not None else np.nan for r in rows], dtype=float)
            ok = np.isfinite(va) & np.isfinite(vb)
            if ok.sum() < 5:
                mat[a][b] = {'rho': None, 'n': int(ok.sum())}
                continue
            rho = spearmanr(va[ok], vb[ok]).statistic
            mat[a][b] = {'rho': (None if not np.isfinite(rho) else round(float(rho), 4)),
                         'n': int(ok.sum())}
    return mat


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    boundary = read_boundary()
    chem = read_chemistry()

    rows, failures = [], []
    subsets = sorted(p.name for p in PROC_DIR.iterdir() if p.is_dir())
    for sub in subsets:
        if sub in ('MICH', 'MICH_EXP'):
            # total_MICH 가 이 둘의 병합본이다. 셀이 두 번 세어지지 않도록 여기서 뺀다.
            continue
        for pf in sorted((PROC_DIR / sub).glob('*.pkl')):
            cell = pf.name
            row = {'subset': sub, 'cell': cell,
                   'chemistry': chem.get((sub, cell))
                   or chem.get(('MICH', cell)) or chem.get(('MICH_EXP', cell))
                   or chem.get(('Stanford_2', cell)) or '미상'}

            bx = boundary.get((sub, cell)) or boundary.get(('MICH', cell)) \
                or boundary.get(('MICH_EXP', cell))
            n_meas = int(bx['n_measured']) if bx and bx['n_measured'] else None
            row['n_measured'] = n_meas if n_meas is not None else ''
            row['boundary_branch'] = bx['branch'] if bx else 'NO_BOUNDARY_RECORD'
            row['boundary_prefix_match'] = bx['prefix_match'] if bx else ''

            xp, yp = load_traj(pf)
            row['n_total'] = len(xp)
            row['n_extrapolated'] = (len(xp) - n_meas) if n_meas is not None else ''
            row['extrap_frac'] = (round((len(xp) - n_meas) / len(xp), 6)
                                  if n_meas is not None and len(xp) else '')

            # Step 1 산출과 대조해 PCHIP 평활이 값을 바꿨는지 본다
            raw_path = SOH_DIR / sub / cell
            if raw_path.is_file():
                xr, yr = load_traj(raw_path)
                m = min(len(yr), len(yp))
                dmax = float(np.max(np.abs(yr[:m] - yp[:m]))) if m else float('nan')
                row['pchip_changed'] = int(dmax > 1e-9) if np.isfinite(dmax) else ''
                row['pchip_max_abs_diff'] = f'{dmax:.3e}' if np.isfinite(dmax) else ''
            else:
                xr, yr = xp, yp
                row['pchip_changed'] = ''
                row['pchip_max_abs_diff'] = ''

            for version in VERSIONS:
                if version == 'processed':
                    x, y = xp, yp
                else:
                    if n_meas is None or n_meas < 2:
                        for k in ([f'knee_{m_}_cycle' for m_ in KNEE_METHODS]
                                  + [f'knee_{m_}_lifefrac' for m_ in KNEE_METHODS]
                                  + [f'curv_{m_}_{a}' for m_ in CURV_METHODS for a in AXES]
                                  + ['eol_cycle', 'n_points', 'soh_first', 'soh_last',
                                     'fade_rate_per_cycle']):
                            row[f'{version}__{k}'] = ''
                        failures.append({'subset': sub, 'cell': cell, 'version': version,
                                         'metric': '(all)', 'reason': 'NO_MEASURED_BOUNDARY'})
                        continue
                    x, y = xr[:n_meas], yr[:n_meas]
                vals, fails = measure(x, y)
                for k, v in vals.items():
                    row[f'{version}__{k}'] = '' if v is None else v
                for k, err in fails.items():
                    failures.append({'subset': sub, 'cell': cell, 'version': version,
                                     'metric': k, 'reason': err})
            rows.append(row)
        print(f'[{sub}] {sum(1 for r in rows if r["subset"] == sub)}셀', flush=True)

    fieldnames = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with open(REPORTS / 'dv_candidates.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fieldnames})

    with open(OUT / 'dv_failures.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['subset', 'cell', 'version', 'metric', 'reason'])
        w.writeheader()
        w.writerows(failures)

    # ---------------- 정의 간 차이 ------------------------------------------
    def num(rs, key):
        return [(r.get(key) if isinstance(r.get(key), float) else
                 (float(r[key]) if r.get(key) not in ('', None) else None)) for r in rs]

    numeric_rows = []
    for r in rows:
        nr = dict(r)
        for k, v in r.items():
            if '__' in k and v not in ('', None):
                try:
                    nr[k] = float(v)
                except (TypeError, ValueError):
                    nr[k] = None
            elif '__' in k:
                nr[k] = None
        numeric_rows.append(nr)

    corr = {'knee': {}, 'curvature': {}, 'version_cross': {}, 'by_chemistry': {}}
    for version in VERSIONS:
        corr['knee'][version] = spearman_matrix(
            numeric_rows, [f'{version}__knee_{m_}_cycle' for m_ in KNEE_METHODS])
        corr['curvature'][version] = spearman_matrix(
            numeric_rows,
            [f'{version}__curv_{m_}_{a}' for m_ in CURV_METHODS for a in AXES])

    cross_keys = ([f'knee_{m_}_cycle' for m_ in KNEE_METHODS]
                  + [f'knee_{m_}_lifefrac' for m_ in KNEE_METHODS]
                  + [f'curv_{m_}_{a}' for m_ in CURV_METHODS for a in AXES]
                  + ['eol_cycle', 'fade_rate_per_cycle'])
    for k in cross_keys:
        m = spearman_matrix(numeric_rows, [f'observed__{k}', f'processed__{k}'])
        a, b = f'observed__{k}', f'processed__{k}'
        va = np.array([r.get(a) if r.get(a) is not None else np.nan for r in numeric_rows])
        vb = np.array([r.get(b) if r.get(b) is not None else np.nan for r in numeric_rows])
        ok = np.isfinite(va) & np.isfinite(vb)
        d = vb[ok] - va[ok]
        rel = np.abs(d) / np.maximum(np.abs(va[ok]), 1e-12)
        corr['version_cross'][k] = {
            'spearman_rho': m[a][b]['rho'], 'n': int(ok.sum()),
            'diff_median': (round(float(np.median(d)), 6) if ok.sum() else None),
            'diff_p05': (round(float(np.percentile(d, 5)), 6) if ok.sum() else None),
            'diff_p95': (round(float(np.percentile(d, 95)), 6) if ok.sum() else None),
            'reldiff_median': (round(float(np.median(rel)), 6) if ok.sum() else None),
            'reldiff_p95': (round(float(np.percentile(rel, 95)), 6) if ok.sum() else None),
        }

    chems = sorted({r['chemistry'] for r in numeric_rows})
    for c in chems:
        sub_rows = [r for r in numeric_rows if r['chemistry'] == c]
        entry = {'n_cells': len(sub_rows), 'knee': {}, 'curvature': {}, 'version_cross': {}}
        entry['knee']['processed'] = spearman_matrix(
            sub_rows, [f'processed__knee_{m_}_cycle' for m_ in KNEE_METHODS])
        entry['curvature']['processed'] = spearman_matrix(
            sub_rows, [f'processed__curv_{m_}_{a}' for m_ in CURV_METHODS for a in AXES])
        for k in cross_keys:
            a, b = f'observed__{k}', f'processed__{k}'
            m = spearman_matrix(sub_rows, [a, b])
            va = np.array([r.get(a) if r.get(a) is not None else np.nan for r in sub_rows])
            vb = np.array([r.get(b) if r.get(b) is not None else np.nan for r in sub_rows])
            ok = np.isfinite(va) & np.isfinite(vb)
            entry['version_cross'][k] = {
                'spearman_rho': m[a][b]['rho'], 'n': int(ok.sum()),
                'reldiff_median': (round(float(np.median(
                    np.abs(vb[ok] - va[ok]) / np.maximum(np.abs(va[ok]), 1e-12))), 6)
                    if ok.sum() else None),
            }
        ef = [r['extrap_frac'] for r in rows
              if r['chemistry'] == c and r['extrap_frac'] not in ('', None)]
        ef = [float(v) for v in ef]
        entry['extrap_frac_median'] = round(float(np.median(ef)), 6) if ef else None
        entry['extrap_frac_mean'] = round(float(np.mean(ef)), 6) if ef else None
        entry['share_with_extrapolation'] = (
            round(float(np.mean([v > 0 for v in ef])), 4) if ef else None)
        corr['by_chemistry'][c] = entry

    # ---------------- 불일치가 큰 셀 ----------------------------------------
    # (dv_correlations.json 은 아래에서 문턱별 개수까지 채운 뒤 한 번에 쓴다)
    def rank_of(key):
        v = np.array([r.get(key) if r.get(key) is not None else np.nan for r in numeric_rows])
        rk = np.full(len(v), np.nan)
        ok = np.isfinite(v)
        if ok.sum() > 1:
            order = np.argsort(np.argsort(v[ok]))
            rk[ok] = order / (ok.sum() - 1)
        return rk

    knee_ranks = np.vstack([rank_of(f'processed__knee_{m_}_lifefrac') for m_ in KNEE_METHODS])
    curv_ranks = np.vstack([rank_of(f'processed__curv_{m_}_lifefrac') for m_ in CURV_METHODS])
    knee_spread = np.nanmax(knee_ranks, axis=0) - np.nanmin(knee_ranks, axis=0)
    curv_spread = np.nanmax(curv_ranks, axis=0) - np.nanmin(curv_ranks, axis=0)

    vk = np.array([r.get('observed__knee_bilinear_lifefrac') or np.nan for r in numeric_rows])
    pk = np.array([r.get('processed__knee_bilinear_lifefrac') or np.nan for r in numeric_rows])
    version_gap = np.abs(pk - vk)

    # 문턱을 바꾸면 목록 크기가 얼마나 달라지는지 함께 남긴다 — 문턱 자체가 자의적이므로
    thresholds = {}
    for t in (0.3, 0.5, 0.7, 0.9):
        thresholds[f'knee_rank_spread>={t}'] = int(np.nansum(knee_spread >= t))
        thresholds[f'curv_rank_spread>={t}'] = int(np.nansum(curv_spread >= t))
    for t in (0.02, 0.05, 0.10, 0.20):
        thresholds[f'obs_vs_proc_kneefrac>={t}'] = int(np.nansum(version_gap >= t))
    corr['disagreement_counts_by_threshold'] = thresholds
    corr['cells_where_versions_differ'] = int(sum(
        1 for r in rows
        if (r['extrap_frac'] not in ('', None) and float(r['extrap_frac']) > 0)
        or r['pchip_changed'] == 1))
    json.dump(corr, open(OUT / 'dv_correlations.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    KNEE_T, CURV_T, VER_T = 0.7, 0.7, 0.05
    dis = []
    for i, r in enumerate(rows):
        ks = knee_spread[i] if i < len(knee_spread) else np.nan
        cs = curv_spread[i] if i < len(curv_spread) else np.nan
        vg = version_gap[i] if i < len(version_gap) else np.nan
        flags = []
        if np.isfinite(ks) and ks >= KNEE_T:
            flags.append(f'knee_rank_spread>={KNEE_T}')
        if np.isfinite(cs) and cs >= CURV_T:
            flags.append(f'curv_rank_spread>={CURV_T}')
        if np.isfinite(vg) and vg >= VER_T:
            flags.append(f'observed_vs_processed_kneefrac>={VER_T}')
        if not flags:
            continue
        dis.append({
            'subset': r['subset'], 'cell': r['cell'], 'chemistry': r['chemistry'],
            'flags': ';'.join(flags),
            'severity': round(float(np.nanmax([ks if np.isfinite(ks) else 0,
                                               cs if np.isfinite(cs) else 0])), 4),
            'knee_rank_spread': '' if not np.isfinite(ks) else round(float(ks), 4),
            'curv_rank_spread': '' if not np.isfinite(cs) else round(float(cs), 4),
            'knee_lifefrac_gap_obs_vs_proc': '' if not np.isfinite(vg) else round(float(vg), 4),
            'n_total': r['n_total'], 'n_measured': r['n_measured'],
            'n_extrapolated': r['n_extrapolated'], 'extrap_frac': r['extrap_frac'],
            'pchip_changed': r['pchip_changed'],
            'eol_cycle': r.get('processed__eol_cycle', ''),
            'soh_first': r.get('processed__soh_first', ''),
            'soh_last': r.get('processed__soh_last', ''),
            'knee_curvature_max_lifefrac': r.get('processed__knee_curvature_max_lifefrac', ''),
            'knee_bilinear_lifefrac': r.get('processed__knee_bilinear_lifefrac', ''),
            'knee_tangent_cross_lifefrac': r.get('processed__knee_tangent_cross_lifefrac', ''),
        })
    dis.sort(key=lambda d: -d['severity'])
    with open(REPORTS / 'dv_disagreement_cells.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(dis[0].keys()) if dis else ['subset', 'cell'])
        w.writeheader()
        w.writerows(dis)

    print(f'\n셀 {len(rows)} · 지표 실패 기록 {len(failures)} · 불일치 셀 {len(dis)}')
    print(f'  {REPORTS / "dv_candidates.csv"}')
    print(f'  {REPORTS / "dv_disagreement_cells.csv"}')
    print(f'  {OUT / "dv_correlations.json"}')


if __name__ == '__main__':
    main()
