"""A/B 라벨 교체 40회 결과 분석. **학습을 다시 돌리지 않는다.**

조건 이름은 앞 글자가 **학습** 라벨, 뒷 글자가 **시험** 라벨이다.
`val` 은 `train` 을 따른다 (`docs/reports/2026-08-07_ab_runner.md` §2).

무엇을 보는가
-------------
1. **AA vs AB · BA vs BB 의 학습 곡선이 같은가.** val 을 train 에 붙였으므로
   학습 라벨·검증 라벨·시드가 같고 **원리상 같은 모델**이어야 한다. 시험
   라벨은 학습에 쓰이지 않는다. 다르면 시험 라벨을 읽는 일이 학습 난수를
   건드린다는 뜻이고, 그 자체가 발견이다.
2. **AA vs BA** (둘 다 시험 A) · **AB vs BB** (둘 다 시험 B) — 시험 집합이
   같아 MAPE 를 직접 비교할 수 있다. 학습 라벨만 다르다. **핵심 비교다.**
3. **AA vs BB** — 시험 라벨이 서로 달라 **MAPE 를 직접 비교할 수 없다.**
   분모가 다른 값이다.

    py -3.12 train/analyze_label_ab.py
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "experiments/results/label_ab"
LOGS = REPO / "runs/label_ab"
OUT = REPO / "experiments/results/label_ab_analysis.json"

CONDITIONS = ["AA", "AB", "BA", "BB"]
MODELS = ["CPMLP", "CPTransformer"]
SEEDS = [42, 2021, 2024, 7, 1234]

# 학습·검증 곡선. **Test 는 일부러 뺀다** — 시험 라벨이 조건마다 달라
# 당연히 갈리고, 여기서 보려는 것은 "학습이 같았는가" 이다.
EPOCH_RE = re.compile(
    r"^Epoch: (\d+) \| Train Loss: ([\d.]+)\| Train cl loss: [\d.]+\| "
    r"Train lc loss: [\d.]+ \| Train RMSE: ([\d.]+) \| Train MAPE: ([\d.]+) \| "
    r"Vali RMSE: ([\d.]+)\| Vali MAE: ([\d.]+)\| Vali MAPE: ([\d.]+)\| "
    r"Test RMSE: ([\d.]+)\| Test MAE: ([\d.]+) \| Test MAPE: ([\d.]+)", re.M)


def load_results():
    out = {}
    for cond in CONDITIONS:
        for model in MODELS:
            for seed in SEEDS:
                p = RES / cond / f"{model}_s{seed}.json"
                if p.exists():
                    out[(cond, model, seed)] = json.loads(p.read_text(encoding="utf-8"))
    return out


def load_curve(cond, model, seed):
    """로그에서 에폭별 학습·검증·시험 지표를 뽑는다."""
    p = LOGS / f"{cond}_{model}_s{seed}.log"
    if not p.exists():
        return None
    rows = []
    for m in EPOCH_RE.finditer(p.read_text(encoding="utf-8", errors="replace")):
        g = m.groups()
        rows.append({
            "epoch": int(g[0]), "train_loss": float(g[1]),
            "train_rmse": float(g[2]), "train_mape": float(g[3]),
            "vali_rmse": float(g[4]), "vali_mae": float(g[5]), "vali_mape": float(g[6]),
            "test_rmse": float(g[7]), "test_mae": float(g[8]), "test_mape": float(g[9]),
        })
    return rows


TRAIN_KEYS = ["train_loss", "train_rmse", "train_mape",
              "vali_rmse", "vali_mae", "vali_mape"]


def compare_curves(a, b):
    """두 곡선의 학습·검증 부분이 같은가. 시험 부분은 따로 센다."""
    if a is None or b is None:
        return {"comparable": False, "reason": "로그 없음"}
    out = {"comparable": True, "n_epochs": (len(a), len(b)),
           "same_length": len(a) == len(b)}
    n = min(len(a), len(b))
    worst = {}
    for k in TRAIN_KEYS:
        d = max((abs(a[i][k] - b[i][k]) for i in range(n)), default=0.0)
        worst[k] = d
    out["train_val_maxdiff"] = worst
    out["train_val_identical"] = out["same_length"] and all(v == 0.0 for v in worst.values())
    out["test_mape_maxdiff"] = max(
        (abs(a[i]["test_mape"] - b[i]["test_mape"]) for i in range(n)), default=0.0)
    return out


def mean_sd(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None, 0
    return (statistics.mean(xs),
            statistics.stdev(xs) if len(xs) > 1 else 0.0,
            len(xs))


def main() -> int:
    res = load_results()
    have = sorted(res)
    missing = [(c, m, s) for c in CONDITIONS for m in MODELS for s in SEEDS
               if (c, m, s) not in res]

    print(f"결과 {len(have)}/40   미완료 {len(missing)}")
    if missing:
        for x in missing:
            print(f"  미완료: {x}")
    print()

    report = {"n_results": len(have), "missing": [list(x) for x in missing]}

    # ---------- 1. AA vs AB · BA vs BB 곡선 동일성 -------------------
    print("=" * 78)
    print("1. 학습 곡선 동일성 — AA vs AB, BA vs BB (원리상 같은 모델이어야 함)")
    print("=" * 78)
    pairs = [("AA", "AB"), ("BA", "BB")]
    curve_rows = []
    for c1, c2 in pairs:
        for model in MODELS:
            for seed in SEEDS:
                if (c1, model, seed) not in res or (c2, model, seed) not in res:
                    continue
                cmp = compare_curves(load_curve(c1, model, seed),
                                     load_curve(c2, model, seed))
                curve_rows.append({"pair": f"{c1}/{c2}", "model": model,
                                   "seed": seed, **cmp})
                w = cmp.get("train_val_maxdiff", {})
                mx = max(w.values()) if w else None
                print(f"  {c1}/{c2}  {model:<14} s{seed:<5} "
                      f"에폭 {cmp.get('n_epochs')}  "
                      f"학습·검증 {'동일' if cmp.get('train_val_identical') else '**다름**'}"
                      + (f" (최대차 {mx:.3e})" if mx else "")
                      + f"  시험MAPE 최대차 {cmp.get('test_mape_maxdiff', 0):.4f}")
    report["curve_identity"] = curve_rows
    n_same = sum(1 for r in curve_rows if r.get("train_val_identical"))
    print(f"\n  => 학습·검증 곡선이 동일한 쌍: {n_same}/{len(curve_rows)}")

    # ---------- 최종 지표 표 -----------------------------------------
    print()
    print("=" * 78)
    print("2. 조건별 최종 지표 (시드 5개)")
    print("=" * 78)
    summary = {}
    for model in MODELS:
        for cond in CONDITIONS:
            mapes = [res[(cond, model, s)]["final"]["test_mape"]
                     for s in SEEDS if (cond, model, s) in res]
            accs = [res[(cond, model, s)]["final"]["test_acc15"]
                    for s in SEEDS if (cond, model, s) in res]
            m1, s1, n = mean_sd(mapes)
            m2, s2, _ = mean_sd(accs)
            summary[f"{model}_{cond}"] = {
                "mape_mean": m1, "mape_sd": s1, "acc15_mean": m2, "acc15_sd": s2,
                "n": n, "mapes": mapes, "accs": accs,
                "test_labels": cond[1], "train_labels": cond[0]}
            print(f"  {model:<14} {cond}  (train {cond[0]} / test {cond[1]})  "
                  f"MAPE {m1:.4f} ± {s1:.4f}   15%-Acc {m2:.2f} ± {s2:.2f}   n={n}")
    report["summary"] = summary

    # ---------- 2. 핵심 비교 -----------------------------------------
    print()
    print("=" * 78)
    print("3. 핵심 비교 — 시험 집합이 같은 쌍만")
    print("=" * 78)
    core = []
    for c1, c2, testlab in [("AA", "BA", "A"), ("AB", "BB", "B")]:
        for model in MODELS:
            per_seed = []
            for s in SEEDS:
                if (c1, model, s) in res and (c2, model, s) in res:
                    a = res[(c1, model, s)]["final"]["test_mape"]
                    b = res[(c2, model, s)]["final"]["test_mape"]
                    per_seed.append({"seed": s, c1: a, c2: b, "delta": b - a,
                                     "rel": (b - a) / a if a else None})
            if not per_seed:
                continue
            d = [x["delta"] for x in per_seed]
            md, sd, n = mean_sd(d)
            a_m, _, _ = mean_sd([x[c1] for x in per_seed])
            b_m, _, _ = mean_sd([x[c2] for x in per_seed])
            worse = sum(1 for x in per_seed if x["delta"] > 0)
            core.append({"pair": f"{c1} vs {c2}", "test_labels": testlab,
                         "model": model, "per_seed": per_seed,
                         "mean_delta": md, "sd_delta": sd,
                         "mean_a": a_m, "mean_b": b_m,
                         "n_seeds_b_worse": worse, "n": n})
            print(f"  [시험 {testlab}] {c1} vs {c2}  {model:<14} "
                  f"{c1} {a_m:.4f} -> {c2} {b_m:.4f}   Δ {md:+.4f} ± {sd:.4f}   "
                  f"({worse}/{n} 시드에서 {c2} 가 더 나쁨)")
            for x in per_seed:
                print(f"        s{x['seed']:<5} {x[c1]:.4f} -> {x[c2]:.4f}  "
                      f"Δ {x['delta']:+.4f} ({x['rel']*100:+.1f}%)")
    report["core_comparisons"] = core

    # ---------- 3. 비교 불가 -----------------------------------------
    print()
    print("=" * 78)
    print("4. AA vs BB — 시험 라벨이 달라 직접 비교 불가")
    print("=" * 78)
    incomp = []
    for model in MODELS:
        aa, _, _ = mean_sd([res[("AA", model, s)]["final"]["test_mape"]
                            for s in SEEDS if ("AA", model, s) in res])
        bb, _, _ = mean_sd([res[("BB", model, s)]["final"]["test_mape"]
                            for s in SEEDS if ("BB", model, s) in res])
        incomp.append({"model": model, "AA_mape": aa, "BB_mape": bb,
                       "note": "분모가 다른 정답이라 이 두 수는 같은 양이 아니다"})
        print(f"  {model:<14} AA {aa:.4f} (시험 A) · BB {bb:.4f} (시험 B) "
              f"— 두 수는 **같은 양이 아니다**")
    report["incomparable"] = incomp

    # ---------- 소요 시간 --------------------------------------------
    el = {}
    for (cond, model, seed), r in res.items():
        el.setdefault(model, []).append(r.get("elapsed_s", 0))
    report["elapsed"] = {m: {"mean_s": statistics.mean(v), "total_h": sum(v) / 3600,
                             "n": len(v)} for m, v in el.items()}
    print()
    for m, v in report["elapsed"].items():
        print(f"  {m:<14} 평균 {v['mean_s']/60:.1f}분 · 합계 {v['total_h']:.2f}시간 (n={v['n']})")

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n기록: {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
