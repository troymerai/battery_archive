"""
Dummy 보다 한 칸 강한 무학습 baseline: **aging condition(프로토콜) 별 train 평균**.

Dummy 는 도메인/데이터셋 평균 하나만 쓴다. 여기서는 test 셀이 속한 aging
condition 의 train 평균을 예측으로 쓰고, 그 condition 이 train 에 없으면
데이터셋 train 평균으로 되돌아간다(Dummy 와 동일).

이 baseline 이 보고된 최고 MAPE 에 근접하면, 그 도메인의 벤치마크는 곡선에서
무언가를 배우는 능력이 아니라 '조건 → 수명' 조회표를 재는 것에 가깝다.

사용법:
    .venv-blife/Scripts/python.exe analysis/condition_mean_baseline.py
출력:
    analysis/out/condition_mean_baseline.json
"""
import json
import os

import numpy as np
from sklearn.metrics import mean_absolute_percentage_error

from domain_discriminability import (SEEDS, collect, domain_groups, load_labels,
                                     load_splits)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COND_JSON = os.path.join(ROOT, "upstream", "BatteryLife", "name2agingConditionID.json")
OUT = os.path.join(ROOT, "analysis", "out", "condition_mean_baseline.json")

RNG = np.random.default_rng(1)
N_BOOT = 1000


def main():
    splits, labels = load_splits(), load_labels()
    cond = json.load(open(COND_JSON, encoding="utf-8"))
    res = {}

    for domain in ["Li-ion", "Zn-ion", "Na-ion", "CALB"]:
        res[domain] = {}
        for seed in SEEDS:
            rows, gmean = collect(domain, seed, splits, labels)

            # condition -> train 라벨
            per_cond = {}
            for gkey, name, y in rows["train"]:
                c = cond.get(name)
                if c is None:
                    continue
                per_cond.setdefault(c, []).append(y)
            cmean = {c: float(np.mean(v)) for c, v in per_cond.items()}

            yte, pred, hit = [], [], 0
            for gkey, name, y in rows["test"]:
                c = cond.get(name)
                if c is not None and c in cmean:
                    pred.append(cmean[c])
                    hit += 1
                else:
                    pred.append(gmean[gkey])      # Dummy 로 폴백
                yte.append(y)

            m = float(mean_absolute_percentage_error(np.asarray(yte), np.asarray(pred))) if yte else None
            ci = None
            if yte:
                ya, pa = np.asarray(yte, float), np.asarray(pred, float)
                b = np.array([np.mean(np.abs(ya[i] - pa[i]) / np.abs(ya[i]))
                              for i in (RNG.integers(0, ya.size, ya.size) for _ in range(N_BOOT))])
                ci = [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]

            res[domain][str(seed)] = {
                "n_test": len(yte),
                "n_test_with_seen_condition": hit,
                "n_train_conditions": len(cmean),
                "condition_mean_test_mape": m,
                "ci95": ci,
            }

    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
    print("written", OUT)
    for d, v in res.items():
        ms = [v[str(s)]["condition_mean_test_mape"] for s in SEEDS]
        hits = [f"{v[str(s)]['n_test_with_seen_condition']}/{v[str(s)]['n_test']}" for s in SEEDS]
        print(f"{d:8s} cond-mean MAPE {np.mean(ms):.3f} ±{np.std(ms, ddof=1):.3f}  "
              f"per-seed {[round(x, 3) for x in ms]}  seen-cond {hits}")


if __name__ == "__main__":
    main()
