"""
T3 최종 표 — 도메인별 판별력.

모델이 실제로 평가받는 모집단에 맞춘다.
data_loader.py:488 `if df is None or eol <= self.early_cycle_threshold: return`
때문에 **라벨 <= 100 인 셀은 학습·평가에서 통째로 빠진다** (기본값 100).
셀마다 표본 수가 96개로 같으므로 표본 단위 MAPE = 셀 단위 MAPE 이고,
따라서 이 모집단의 셀 단위 Dummy MAPE 가 보고된 모델 MAPE 의 올바른 비교군이다.

같이 내는 값:
  - Dummy(repo)      : Dummy.py 그대로 (라벨 필터 없음). 논문 Dummy 행과 대응.
  - Dummy(eval)      : eol>100 모집단. 모델 행과 대응.
  - CondMean(eval)   : aging condition 별 train 평균 (무학습 상한 baseline).

사용법:
    .venv-blife/Scripts/python.exe analysis/discriminability_table.py
출력:
    analysis/out/discriminability.json
    analysis/out/discriminability.md
"""
import json
import os
from collections import defaultdict

import numpy as np
from sklearn.metrics import mean_absolute_percentage_error as MAPE

from domain_discriminability import SEEDS, collect, load_labels, load_splits

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTJ = os.path.join(ROOT, "analysis", "out", "discriminability.json")
OUTM = os.path.join(ROOT, "analysis", "out", "discriminability.md")
COND = os.path.join(ROOT, "upstream", "BatteryLife", "name2agingConditionID.json")
REPORTED = os.path.join(ROOT, "analysis", "out", "reported_table.json")

EOL_MIN = 100          # early_cycle_threshold 기본값
N_BOOT = 1000
RNG = np.random.default_rng(20260806)
DOMAINS = ["Li-ion", "Zn-ion", "Na-ion", "CALB"]


def boot_ci(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    b = np.empty(N_BOOT)
    for i in range(N_BOOT):
        idx = RNG.integers(0, y.size, y.size)
        b[i] = np.mean(np.abs(y[idx] - p[idx]) / np.abs(y[idx]))
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main():
    splits, labels = load_splits(), load_labels()
    cond = json.load(open(COND, encoding="utf-8"))
    rep = json.load(open(REPORTED, encoding="utf-8"))["by_domain"]
    res = {}

    for dom in DOMAINS:
        per_seed = []
        for s in SEEDS:
            rows, gmean_all = collect(dom, s, splits, labels)
            tr = [r for r in rows["train"] if r[2] > EOL_MIN]
            te = [r for r in rows["test"] if r[2] > EOL_MIN]

            g = defaultdict(list)
            for k, _, y in tr:
                g[k].append(y)
            gmean = {k: float(np.mean(v)) for k, v in g.items()}

            c = defaultdict(list)
            for _, n, y in tr:
                if n in cond:
                    c[cond[n]].append(y)
            cmean = {k: float(np.mean(v)) for k, v in c.items()}

            yt = [y for _, _, y in te]
            p_dummy = [gmean[k] for k, _, _ in te]
            p_cond = [cmean.get(cond.get(n), gmean[k]) for k, n, _ in te]
            seen = sum(1 for _, n, _ in te if cond.get(n) in cmean)

            lo, hi = boot_ci(yt, p_dummy)
            ya = np.asarray(yt, float)
            per_seed.append({
                "seed": s,
                "n_test_all": len(rows["test"]), "n_test_eval": len(te),
                "n_train_eval": len(tr),
                "dummy_repo": float(MAPE([y for _, _, y in rows["test"]],
                                         [gmean_all[k] for k, _, _ in rows["test"]])),
                "dummy_eval": float(MAPE(yt, p_dummy)),
                "dummy_eval_ci95": [lo, hi], "dummy_eval_ci_width": hi - lo,
                "condmean_eval": float(MAPE(yt, p_cond)),
                "n_test_seen_condition": seen,
                "test_cv": float(ya.std(ddof=1) / ya.mean()),
            })

        def agg(k):
            v = np.array([p[k] for p in per_seed], float)
            return float(v.mean()), float(v.std(ddof=1))

        r = rep[dom]
        d_mean, d_std = agg("dummy_eval")
        c_mean, c_std = agg("condmean_eval")
        ciw, _ = agg("dummy_eval_ci_width")
        res[dom] = {
            "per_seed": per_seed,
            "n_cells_total": per_seed[0]["n_train_eval"] + per_seed[0]["n_test_eval"],
            "dummy_repo": agg("dummy_repo"),
            "dummy_eval": [d_mean, d_std],
            "condmean_eval": [c_mean, c_std],
            "test_cv": agg("test_cv"),
            "dummy_ci_width_mean": ciw,
            "reported_dummy": r["dummy_reported"],
            "reported_best": r["best_mape"], "reported_best_model": r["best_model"],
            "reported_gap_1st_2nd": r["gap_best_to_second"],
            "reported_model_spread": r["model_mape_min_max_spread"],
            "ratio_best_over_dummy": round(r["best_mape"] / d_mean, 3),
            "ratio_best_over_condmean": round(r["best_mape"] / c_mean, 3),
            "ci_width_over_model_spread": round(ciw / r["model_mape_min_max_spread"], 2),
        }

    json.dump(res, open(OUTJ, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    lines = ["| 도메인 | 셀 | test 셀 | test CV | Dummy(eval) | Dummy 95% CI | CondMean | 보고 최고 | best/Dummy | best/CondMean | CI폭/모델폭 |",
             "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|"]
    for d in DOMAINS:
        v = res[d]
        p = v["per_seed"]
        ci = f"[{np.mean([x['dummy_eval_ci95'][0] for x in p]):.3f}, {np.mean([x['dummy_eval_ci95'][1] for x in p]):.3f}]"
        lines.append(
            f"| {d} | {v['n_cells_total']} | {p[0]['n_test_eval']} | {v['test_cv'][0]:.3f} | "
            f"{v['dummy_eval'][0]:.3f}±{v['dummy_eval'][1]:.3f} | {ci} | "
            f"{v['condmean_eval'][0]:.3f}±{v['condmean_eval'][1]:.3f} | {v['reported_best']:.3f} | "
            f"{v['ratio_best_over_dummy']:.3f} | {v['ratio_best_over_condmean']:.3f} | "
            f"{v['ci_width_over_model_spread']:.2f} |")
    open(OUTM, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
