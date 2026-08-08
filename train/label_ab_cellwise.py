"""채점표 효과를 **셀 단위로 분해**한다. 학습을 돌리지 않는다 — 추론만.

왜 20회면 되는가
----------------
`docs/reports/2026-08-08_label_ab_training.md` §1 이 AA≡AB · BA≡BB 를 보였고,
체크포인트 `model.safetensors` 가 **20/20 바이트 동일**함까지 확인했다.
그러니 예측은 학습 라벨에만 달렸고 시험 라벨과 무관하다.

따라서 **(학습라벨 × 모델 × 시드) = 2 × 2 × 5 = 20회** 추론하고, **같은
예측을 A 채점표와 B 채점표로 두 번 채점**하면 된다. 이러면 AA↔AB 비교에
학습 잡음이 **정확히 0** 이다 — 같은 숫자를 두 자로 재는 것이다.

표본이 같은가
-------------
같다. 규칙 5 통과 셀이 A·B 모두 140셀로 동일하고
(`label_ab_manifest` §1), 셀당 샘플 수는 `valid_cycle_number` 로 정해져
`eol` 과 무관하다 (`prep_ab` §1-1). 그래서 A 라벨로 지은 데이터셋의 샘플
배열을 그대로 두 채점표에 쓸 수 있다.

분해
----
샘플 하나에서 예측 `p`, A 라벨 `a`, B 라벨 `b` 일 때

    e_A = |p-a|/a          e_B = |p-b|/b
    Δ  = e_B - e_A
       = [ |p-a|/b - |p-a|/a ]  +  [ |p-b|/b - |p-a|/b ]
         ~~~~~~ 분모 항 ~~~~~~     ~~~~~~ 분자 항 ~~~~~~

분모 항은 **오차를 그대로 두고 나누는 수만 바꿨을 때**의 변화다. 분자 항은
**정답이 옮겨가 오차 자체가 달라진** 몫이다. 둘의 합이 정확히 Δ 다.

MAE 는 분모가 없으므로 `|p-b| - |p-a|` 만 본다.

    .venv-blife/Scripts/python.exe train/label_ab_cellwise.py
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BL = REPO / "upstream/BatteryLife"
CKPT = REPO / "data/checkpoints_label_ab"
RES = REPO / "experiments/results/label_ab"
OUT = REPO / "experiments/results/label_ab_cellwise.json"

MODELS = ["CPMLP", "CPTransformer"]
SEEDS = [42, 2021, 2024, 7, 1234]
# 학습 라벨 -> (그 체크포인트가 있는 조건, A채점 조건, B채점 조건)
TRAIN_SETS = {"A": ("AA", "AA", "AB"), "B": ("BA", "BA", "BB")}
LABEL_DIRS = {"A": REPO / "data/extracted/Life labels", "B": REPO / "data/labels_B"}
EXCLUDE = ["Tongji"]
CACHE_TAG = "liion"


def _stubs():
    try:
        import denseweight  # noqa: F401
    except ImportError:
        m = types.ModuleType("denseweight")

        class DW:
            def __init__(s, *a, **k): pass
            def fit(s, x): pass
            def __call__(s, x): return [1.0]
        m.DenseWeight = DW
        sys.modules["denseweight"] = m


def run_inference(model_name, seed, train_lab, device):
    """예측을 뽑는다. 라벨과 무관하다 — 입력 텐서와 가중치의 함수다."""
    import numpy as np
    import torch
    import joblib
    from safetensors.torch import load_file
    from data_provider.data_loader import Dataset_original, my_collate_fn_baseline
    from data_provider.data_split_recorder import split_recorder
    from data_provider import data_loader as dl
    from torch.utils.data import DataLoader
    from train.blife_patches import (apply_mix841, apply_exclude_prefixes,
                                     install_cell_recorder, install_tensor_cache)
    from train.infer_cell_preds import build_model

    cond = TRAIN_SETS[train_lab][0]
    ck = next(d for d in (CKPT / cond).iterdir() if f"_s{seed}-" in d.name
              and d.name.startswith(model_name + "_"))
    saved = json.loads((ck / "args.json").read_text(encoding="utf-8"))
    args_ns = argparse.Namespace(**saved)

    restore_841 = apply_mix841(split_recorder)
    apply_exclude_prefixes(split_recorder, EXCLUDE)
    undo = []
    r, cache_stats, _ = install_tensor_cache(dl, REPO / "data/tensor_cache", CACHE_TAG)
    if r:
        undo.append(r)
    r_rec, records = install_cell_recorder(dl)
    undo.append(r_rec)
    try:
        ds_args = argparse.Namespace(**{**saved, "dataset": "MIX_large"})
        ls = joblib.load(ck / "label_scaler")
        lcs = joblib.load(ck / "life_class_scaler")
        test_ds = Dataset_original(args=ds_args, flag="test",
                                   label_scaler=ls, life_class_scaler=lcs)
    finally:
        for u in reversed(undo):
            u()
        restore_841()

    loader = DataLoader(test_ds, batch_size=args_ns.batch_size, shuffle=False,
                        num_workers=0, drop_last=False,
                        collate_fn=my_collate_fn_baseline)
    model = build_model(args_ns)
    model.load_state_dict(load_file(str(ck / "model.safetensors")), strict=True)
    model.to(device).eval()

    std = float(np.sqrt(test_ds.label_scaler.var_[-1]))
    mean_v = float(test_ds.label_scaler.mean_[-1])
    preds, su = [], []
    with torch.no_grad():
        for cc, cm, _lab, _lc, _slc, _w, seen_unseen in loader:
            out = model(cc.float().to(device), cm.float().to(device))
            preds += (out * std + mean_v).detach().cpu().numpy().reshape(-1).tolist()
            su += seen_unseen.numpy().reshape(-1).tolist()

    cells = [{"file": f, "n": n} for f, n, e in records if n > 0]
    return np.array(preds), np.array(su, dtype=int), cells, cache_stats


def label_of(file_name, store):
    """`data_loader.py:417-431` 과 같은 조회 규칙."""
    p = file_name.split("_")[0]
    if p == "MICH":
        f, k = "total_MICH_labels.json", file_name
    elif p.startswith("Tongji"):
        f, k = "Tongji_labels.json", file_name.replace("--", "-#")
    else:
        f, k = f"{p}_labels.json", file_name
    t = store.get(f)
    return None if t is None else t.get(k)


def load_store(d: Path):
    out = {}
    for p in d.glob("*.json"):
        if p.name.startswith("_") or p.name == "ISU_ILCC_labels.json":
            continue
        out[p.name] = json.loads(p.read_text(encoding="utf-8"))
    return out


def main() -> int:
    import numpy as np
    import torch

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cpu", action="store_true")
    a = ap.parse_args()

    _stubs()
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(BL))
    os.chdir(BL)

    A = load_store(LABEL_DIRS["A"])
    B = load_store(LABEL_DIRS["B"])

    report = {"runs": {}, "cells": {}, "reconcile": []}
    per_cell_acc: dict = {}

    for train_lab in ["A", "B"]:
        cA, cB = TRAIN_SETS[train_lab][1], TRAIN_SETS[train_lab][2]
        for model_name in MODELS:
            # CPTransformer 는 GPU 커널 누산 순서 탓에 기록값과 어긋난다
            # (`cell_predictions` §3). CPU 로 돌려 기록과 맞춘다.
            device = "cpu" if (a.cpu or model_name == "CPTransformer"
                               or not torch.cuda.is_available()) else "cuda"
            for seed in SEEDS:
                preds, su, cells, cst = run_inference(model_name, seed, train_lab, device)
                N = len(preds)
                start = 0
                rows = []
                for c in cells:
                    n = c["n"]
                    sl = slice(start, start + n)
                    p = preds[sl]
                    la, lb = label_of(c["file"], A), label_of(c["file"], B)
                    eA = np.abs(p - la) / la
                    eB = np.abs(p - lb) / lb
                    den = np.abs(p - la) / lb - np.abs(p - la) / la   # 분모 항
                    num = np.abs(p - lb) / lb - np.abs(p - la) / lb   # 분자 항
                    rows.append({
                        "file": c["file"], "n": n, "a": la, "b": lb,
                        "changed": la != lb,
                        "seen_unseen": "seen" if int(su[sl][0]) == 1 else "unseen",
                        "mapeA": float(eA.mean()), "mapeB": float(eB.mean()),
                        "maeA": float(np.abs(p - la).mean()),
                        "maeB": float(np.abs(p - lb).mean()),
                        "den_term": float(den.mean()), "num_term": float(num.mean()),
                        "pred_mean": float(p.mean()),
                        "w": n / N,
                    })
                    start += n
                key = f"{model_name}_s{seed}_train{train_lab}"
                mapeA = sum(r["w"] * r["mapeA"] for r in rows)
                mapeB = sum(r["w"] * r["mapeB"] for r in rows)
                maeA = sum(r["w"] * r["maeA"] for r in rows)
                maeB = sum(r["w"] * r["maeB"] for r in rows)
                report["runs"][key] = {
                    "model": model_name, "seed": seed, "train_labels": train_lab,
                    "device": device, "n_samples": int(N), "n_cells": len(rows),
                    "cond_A": cA, "cond_B": cB,
                    "mape_A": mapeA, "mape_B": mapeB, "delta_mape": mapeB - mapeA,
                    "mae_A": maeA, "mae_B": maeB, "delta_mae": maeB - maeA,
                    "den_total": sum(r["w"] * r["den_term"] for r in rows),
                    "num_total": sum(r["w"] * r["num_term"] for r in rows),
                    "cache_hit": cst.get("hit"),
                }
                # 기록된 학습 지표와 대조
                for cond, got in ((cA, mapeA), (cB, mapeB)):
                    want = json.loads((RES / cond / f"{model_name}_s{seed}.json")
                                      .read_text(encoding="utf-8"))["final"]["test_mape"]
                    report["reconcile"].append(
                        {"cond": cond, "model": model_name, "seed": seed,
                         "recorded": want, "recomputed": got, "delta": got - want,
                         "ok": abs(got - want) <= 5e-5})
                # **시드별 셀 원자료를 남긴다.** 예전 판은 시드 평균만 남겨서
                # 집중도의 시드별 산포를 되짚을 수 없었다
                # (`docs/reports/2026-08-08_closing_checks.md` §1).
                report["runs"][key]["cells"] = rows
                for r in rows:
                    per_cell_acc.setdefault((train_lab, model_name, r["file"]), []).append(r)
                print(f"  {key:<34} dev={device:<4} 셀 {len(rows)} 샘플 {N}  "
                      f"MAPE A {mapeA:.4f} B {mapeB:.4f} Δ{mapeB-mapeA:+.4f}  "
                      f"MAE A {maeA:.1f} B {maeB:.1f} Δ{maeB-maeA:+.2f}")

    # 시드 평균 셀별 기여
    cellwise = {}
    for (train_lab, model_name, f), rs in per_cell_acc.items():
        cellwise.setdefault(f"{model_name}_train{train_lab}", []).append({
            "file": f, "a": rs[0]["a"], "b": rs[0]["b"], "changed": rs[0]["changed"],
            "seen_unseen": rs[0]["seen_unseen"], "w": rs[0]["w"], "n": rs[0]["n"],
            "contrib_mape": statistics.mean(r["w"] * (r["mapeB"] - r["mapeA"]) for r in rs),
            "contrib_mae": statistics.mean(r["w"] * (r["maeB"] - r["maeA"]) for r in rs),
            "den": statistics.mean(r["w"] * r["den_term"] for r in rs),
            "num": statistics.mean(r["w"] * r["num_term"] for r in rs),
            "mapeA": statistics.mean(r["mapeA"] for r in rs),
            "mapeB": statistics.mean(r["mapeB"] for r in rs),
        })
    report["cells"] = cellwise
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [r for r in report["reconcile"] if not r["ok"]]
    print(f"\n기록값 재현: {len(report['reconcile']) - len(bad)}/{len(report['reconcile'])} 통과")
    for r in bad:
        print(f"  불일치 {r['cond']}/{r['model']}/s{r['seed']}: "
              f"기록 {r['recorded']:.4f} 재계산 {r['recomputed']:.6f} Δ{r['delta']:+.2e}")
    print(f"기록: {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
