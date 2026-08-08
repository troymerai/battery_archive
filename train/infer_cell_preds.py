"""체크포인트로 **추론만** 돌려 셀별 예측값을 뽑는다.

왜 필요한가
-----------
상위 저장소는 셀별 예측을 남기지 않는다. `utils/tools.py:240-249` 가
`total_preds` 로 지표만 내고 버리고, 셀 식별자는 배치에 실리지도 않는다
(`data_loader.py:647-659` · `:69-80`). 그래서 "셀 균등 평균" 같은 질문에
답하려면 예측값을 다시 만들어야 한다.

**재학습은 필요 없다.** 셀 경계가 결정적으로 복원되기 때문이다.

* 시험 로더가 `shuffle=False` · `drop_last=False` (`data_factory.py:93-121`)
* `read_data` 가 `self.files` 순서대로 셀마다 샘플을 **연속으로** 이어 붙인다
  (`data_loader.py:334-371`)

따라서 셀 `k` 의 샘플은 구간 `[Σ_{i<k} n_i, Σ_{i≤k} n_i)` 이고, `n_i` 는
`experiments/results/cell_sample_counts.json` 에 이미 있다.

**이 복원을 믿고 쓰지 않는다 — 매번 검증한다.** `seen_unseen_id` 와
`dataset_id` 는 셀 단위로 붙으므로(`data_loader.py:357, :360-369`), 복원한
경계 안에서 이 두 값이 **상수가 아니면 경계가 틀린 것이다.** 값싸고 확실한
검사라 조합마다 돌린다.

학습을 돌리지 않는다 — `model.eval()` · `torch.no_grad()` 이고 옵티마이저를
만들지 않는다. 체크포인트는 **읽기만** 한다.

사용
----
    .venv-blife/Scripts/python.exe train/infer_cell_preds.py --all
    .venv-blife/Scripts/python.exe train/infer_cell_preds.py --model CPMLP --domain CALB --seed 2024
    ... --no-cache        입력 텐서 캐시를 끄고 돈다 (캐시 동등성 확인용)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BL = REPO / "upstream/BatteryLife"
CKPT_ROOT = REPO / "data/checkpoints"
CURVES = REPO / "experiments/results/curves"
COUNTS = REPO / "experiments/results/cell_sample_counts.json"
OUT_DIR = REPO / "experiments/results/cell_preds"
CACHE_DIR = REPO / "data/tensor_cache"

sys.path.insert(0, str(REPO))
# 캐시·분할·라벨 패치는 **학습 진입점과 같은 코드**를 쓴다.
# 예전에는 여기와 train/templates/entrypoint.py 에 복제돼 있었다
# (`docs/reports/2026-08-07_cell_predictions.md` §10-1).
from train.blife_patches import (CACHE_TAG, MIX_841_EXCLUDED,  # noqa: E402
                                 LabelMissing,
                                 apply_mix841, install_cell_recorder,
                                 install_label_source, install_tensor_cache,
                                 make_eol_lookup)

# 라벨 원본 — A 는 배포판, B 는 공개 코드 재생성분
LABEL_SOURCES = {
    "A": REPO / "data/extracted/Life labels",
    "B": REPO / "data/labels_B",
}


def _install_stubs() -> None:
    try:
        import denseweight  # noqa: F401
    except ImportError:
        mod = types.ModuleType("denseweight")

        class DenseWeight:
            def __init__(self, *a, **k): pass
            def fit(self, x): pass
            def __call__(self, x): return [1.0]

        mod.DenseWeight = DenseWeight
        sys.modules["denseweight"] = mod


def setting_name(a: dict) -> str:
    """run_main.py:141-151 의 setting 문자열 + '-' + model_comment."""
    s = ("{}_sl{}_lr{}_dm{}_nh{}_el{}_dl{}_df{}_lradj{}_dataset{}_loss{}"
         "_wd{}_wl{}_bs{}_s{}").format(
        a["model"], a["seq_len"], a["learning_rate"], a["d_model"], a["n_heads"],
        a["e_layers"], a["d_layers"], a["d_ff"], a["lradj"], a["dataset"],
        a["loss"], a["wd"], a["weighted_loss"], a["batch_size"], a["seed"])
    return s + "-" + a["model_comment"]


def load_combos() -> list[dict]:
    """`group == "main"` 인 36건을 curves JSON 에서 읽는다."""
    out = []
    for p in sorted(glob.glob(str(CURVES / "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("group") != "main":
            continue
        out.append({
            "model": d["model"], "domain": d["domain"], "seed": d["seed"],
            "args": d["args"], "final": d["final"], "curve_json": Path(p).name,
            "ckpt": setting_name(d["args"]),
        })
    return out


def build_model(args_ns):
    """run_main.py:154-196 의 분기 중 이 저장소가 쓰는 3종만."""
    from models import CPMLP, CPTransformer, MLP

    table = {"CPMLP": CPMLP, "CPTransformer": CPTransformer, "MLP": MLP}
    mod = table.get(args_ns.model)
    if mod is None:
        raise SystemExit(f"이 하네스는 {sorted(table)} 만 다룹니다: {args_ns.model}")
    return mod.Model(args_ns).float()


def metrics_from(preds, refs, alpha1=0.15, alpha2=0.10):
    """utils/tools.py:243-259 와 같은 정의."""
    import numpy as np
    from sklearn.metrics import (mean_absolute_error,
                                 mean_absolute_percentage_error,
                                 root_mean_squared_error)
    rel = np.abs(preds - refs) / refs
    return {
        "mape": float(mean_absolute_percentage_error(refs, preds)),
        "mae": float(mean_absolute_error(refs, preds)),
        "rmse": float(root_mean_squared_error(refs, preds)),
        "acc15": float((rel <= alpha1).sum() / len(refs) * 100),
        "acc10": float((rel <= alpha2).sum() / len(refs) * 100),
    }


def run_one(combo: dict, use_cache: bool, device: str, label_set: str = "A") -> dict:
    import numpy as np
    import torch
    import joblib
    from safetensors.torch import load_file
    from data_provider.data_loader import Dataset_original, my_collate_fn_baseline
    from data_provider.data_split_recorder import split_recorder
    from data_provider import data_loader as dl
    from torch.utils.data import DataLoader

    ck_dir = CKPT_ROOT / combo["ckpt"]
    saved = json.loads((ck_dir / "args.json").read_text(encoding="utf-8"))
    args_ns = argparse.Namespace(**saved)

    # 상위 elif 사슬에 MIX_large_841 가지가 없다. `.build` 진입점과 같은 방식으로
    # 데이터셋 객체에만 MIX_large 로 보이게 한다.
    ds_name = args_ns.dataset
    restore_841 = None
    if ds_name == "MIX_large_841":
        restore_841 = apply_mix841(split_recorder)
        ds_name = "MIX_large"

    undo = []
    cache_stats = {"hit": 0, "miss": 0, "off": True}
    label_stats = {"found": 0, "missing": 0, "no_file": 0}

    # 라벨을 갈아 끼울 때는 **캐시에도 알려야 한다.** 캐시 색인이 만들 때의
    # eol 을 담고 있어서, 그냥 두면 read_cell_df 가 통째로 대체되며 라벨 교체가
    # 조용히 무시된다 (blife_patches.install_tensor_cache 주석).
    eol_lookup = None
    if label_set != "A":
        eol_lookup, label_stats = make_eol_lookup(LABEL_SOURCES[label_set])

    if use_cache:
        r, cache_stats, _desc = install_tensor_cache(
            dl, CACHE_DIR, CACHE_TAG[combo["domain"]], eol_lookup=eol_lookup)
        if r is not None:
            undo.append(r)
    if label_set != "A":
        # 캐시에 없는 셀은 원래 경로로 가므로 조회부도 함께 갈아 끼운다.
        # (캐시가 켜져 있어도 필요하다 — 적중하지 않은 셀이 A 라벨을 쓰면 안 된다.)
        r, _ = install_label_source(dl, LABEL_SOURCES[label_set])
        undo.append(r)
    # 셀 경계는 미리 계산한 표에서 읽지 않고 **그 자리에서 관측한다.**
    # 라벨이 바뀌면 경계도 바뀌므로 A 기준 표를 믿으면 틀린다.
    r_rec, cell_records = install_cell_recorder(dl)
    undo.append(r_rec)
    try:
        ds_args = argparse.Namespace(**{**saved, "dataset": ds_name})
        label_scaler = joblib.load(ck_dir / "label_scaler")
        life_class_scaler = joblib.load(ck_dir / "life_class_scaler")
        test_ds = Dataset_original(args=ds_args, flag="test",
                                   label_scaler=label_scaler,
                                   life_class_scaler=life_class_scaler)
    finally:
        for r in reversed(undo):
            r()
        if restore_841 is not None:
            restore_841()

    test_loader = DataLoader(test_ds, batch_size=args_ns.batch_size, shuffle=False,
                             num_workers=0, drop_last=False,
                             collate_fn=my_collate_fn_baseline)

    model = build_model(args_ns)
    state = load_file(str(ck_dir / "model.safetensors"))
    model.load_state_dict(state, strict=True)   # strict — 키가 하나라도 어긋나면 여기서 멈춘다
    model.to(device).eval()

    std = float(np.sqrt(test_ds.label_scaler.var_[-1]))
    mean_value = float(test_ds.label_scaler.mean_[-1])

    preds, refs, su_ids, ds_ids = [], [], [], []
    with torch.no_grad():
        for cycle_curve_data, curve_attn_mask, labels, _lc, _slc, _w, seen_unseen in test_loader:
            cycle_curve_data = cycle_curve_data.float().to(device)
            curve_attn_mask = curve_attn_mask.float().to(device)
            labels = labels.float().to(device)
            outputs = model(cycle_curve_data, curve_attn_mask)
            preds += (outputs * std + mean_value).detach().cpu().numpy().reshape(-1).tolist()
            refs += (labels * std + mean_value).detach().cpu().numpy().reshape(-1).tolist()
            su_ids += seen_unseen.numpy().reshape(-1).tolist()
    preds = np.array(preds)
    refs = np.array(refs)
    su_ids = np.array(su_ids, dtype=int)
    ds_ids = np.array(test_ds.total_dataset_ids, dtype=int)

    observed = [{"file": f, "n_samples": n, "eol": eol}
                for f, n, eol in cell_records if n > 0]
    dropped = [{"file": f, "eol": eol} for f, n, eol in cell_records if n == 0]
    return {"preds": preds, "refs": refs, "su_ids": su_ids, "ds_ids": ds_ids,
            "cache_stats": cache_stats, "label_stats": label_stats,
            "labels": label_set, "n_test_cells_listed": len(test_ds.files),
            "observed_cells": observed, "dropped_cells": dropped}


def reconstruct_cells(combo, res, counts):
    """셀 경계를 복원하고 **그 자리에서 검증한다.**

    경계는 `install_cell_recorder` 가 관측한 것을 쓴다. `counts`
    (`cell_sample_counts.json`, A 라벨 기준) 는 **대조용으로만** 쓴다 —
    라벨 B 에서는 당연히 다를 수 있고, 다르다는 사실 자체가 기록거리다.
    """
    import numpy as np

    cells = res["observed_cells"]
    expect_total = sum(c["n_samples"] for c in cells)

    problems = []
    n_got = len(res["preds"])
    if n_got != expect_total:
        problems.append(f"샘플 수 불일치: 로더 {n_got} · 관측 경계 합 {expect_total}")
        return None, problems

    # A 라벨일 때만 미리 계산한 표와 대조한다 (교차 검증).
    if res["labels"] == "A":
        entry = counts["per_domain"][combo["domain"]][str(combo["seed"])]
        want = {c["file"]: c["n_samples"] for c in entry["cells"]}
        got = {c["file"]: c["n_samples"] for c in cells}
        if want != got:
            only_w = sorted(set(want) - set(got))
            only_g = sorted(set(got) - set(want))
            diff = [f for f in set(want) & set(got) if want[f] != got[f]]
            problems.append(f"cell_sample_counts.json 과 불일치 — "
                            f"표에만 {len(only_w)} · 관측에만 {len(only_g)} · 개수다름 {len(diff)}")

    out, start = [], 0
    for c in cells:
        n = c["n_samples"]
        sl = slice(start, start + n)
        su = res["su_ids"][sl]
        di = res["ds_ids"][sl]
        # 셀 안에서 상수여야 한다 — 아니면 경계가 틀렸다
        if len(np.unique(su)) != 1:
            problems.append(f"{c['file']}: seen_unseen 이 셀 안에서 갈림 {np.unique(su).tolist()}")
        if len(np.unique(di)) != 1:
            problems.append(f"{c['file']}: dataset_id 가 셀 안에서 갈림 {np.unique(di).tolist()}")
        p, r = res["preds"][sl], res["refs"][sl]
        rel = np.abs(p - r) / r
        out.append({
            "file": c["file"], "n_samples": n,
            "eol": c["eol"],
            "seen_unseen": ("seen" if int(su[0]) == 1 else "unseen") if len(su) else None,
            "seen_unseen_id": int(su[0]) if len(su) else None,
            "dataset_id": int(di[0]) if len(di) else None,
            "start": start, "stop": start + n,
            "ref": float(r[0]),
            "ref_constant": bool(np.all(r == r[0])),
            "mape": float(rel.mean()),
            "acc15": float((rel <= 0.15).mean() * 100),
            "acc10": float((rel <= 0.10).mean() * 100),
            "pred_mean": float(p.mean()), "pred_min": float(p.min()),
            "pred_max": float(p.max()),
        })
        start += n

    if start != n_got:
        problems.append(f"경계 합 {start} != 샘플 수 {n_got}")
    return out, problems


def aggregate(cell_rows):
    """셀 균등 지표. 셀별 값을 셀 간 균등 평균."""
    import numpy as np
    m = np.array([c["mape"] for c in cell_rows])
    a15 = np.array([c["acc15"] for c in cell_rows])
    a10 = np.array([c["acc10"] for c in cell_rows])
    seen = [c for c in cell_rows if c["seen_unseen"] == "seen"]
    unseen = [c for c in cell_rows if c["seen_unseen"] == "unseen"]
    out = {
        "cell_uniform_mape": float(m.mean()),
        "cell_uniform_acc15": float(a15.mean()),
        "cell_uniform_acc10": float(a10.mean()),
        "n_cells": len(cell_rows),
    }
    for name, grp in (("seen", seen), ("unseen", unseen)):
        if grp:
            out[f"cell_uniform_{name}_mape"] = float(np.mean([c["mape"] for c in grp]))
            out[f"cell_uniform_{name}_acc15"] = float(np.mean([c["acc15"] for c in grp]))
            out[f"n_{name}_cells"] = len(grp)
    return out


def main() -> int:
    import numpy as np
    import torch

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--model")
    ap.add_argument("--domain")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--no-cache", action="store_true", help="입력 텐서 캐시를 끈다")
    ap.add_argument("--cpu", action="store_true", help="CUDA 가 있어도 CPU 로 돈다")
    ap.add_argument("--labels", default="A", choices=sorted(LABEL_SOURCES),
                    help="A=배포 라벨 · B=공개 코드 재생성 라벨")
    ap.add_argument("--tol", type=float, default=1e-6,
                    help="기존 지표와의 허용 오차 (절대)")
    ap.add_argument("--out-tag", default="", help="산출물 파일 이름에 붙일 꼬리표")
    a = ap.parse_args()

    _install_stubs()
    sys.path.insert(0, str(BL))
    os.chdir(BL)

    device = "cpu" if a.cpu else ("cuda" if torch.cuda.is_available() else "cpu")
    counts = json.loads(COUNTS.read_text(encoding="utf-8"))
    combos = load_combos()
    if not a.all:
        combos = [c for c in combos
                  if (not a.model or c["model"] == a.model)
                  and (not a.domain or c["domain"] == a.domain)
                  and (a.seed is None or c["seed"] == a.seed)]
    if not combos:
        print("고른 조합이 없습니다.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 라벨 조건이 A 가 아니면 산출물 이름에 반드시 남긴다 — 두 조건이 같은
    # 파일을 덮어쓰면 A/B 실험이 조용히 무너진다.
    tag = a.out_tag if a.labels == "A" else f"_{a.labels}{a.out_tag}"
    print(f"조합 {len(combos)}개 · device={device} · "
          f"텐서캐시={'끔' if a.no_cache else '켬'} · 라벨={a.labels} "
          f"({LABEL_SOURCES[a.labels].relative_to(REPO)})\n")

    summary, all_problems, mismatches, blocked = {}, [], [], []
    for i, combo in enumerate(combos, 1):
        key = f"{combo['model']}_{combo['domain']}_s{combo['seed']}"
        try:
            res = run_one(combo, use_cache=not a.no_cache, device=device,
                          label_set=a.labels)
        except LabelMissing as exc:
            # 라벨 원본에 그 셀이 없다. 건너뛰면 표본이 바뀌므로 조합 전체를 버린다.
            print(f"[{i}/{len(combos)}] {key:<34} **라벨없음으로 중단**")
            for line in str(exc).splitlines():
                print(f"          {line}")
            blocked.append((key, exc.file_name))
            continue
        cell_rows, problems = reconstruct_cells(combo, res, counts)
        if problems:
            all_problems.append((key, problems))
        if cell_rows is None:
            print(f"[{i}/{len(combos)}] {key:<34} 경계 복원 실패 — 건너뜀")
            continue

        sw = metrics_from(res["preds"], res["refs"])
        cu = aggregate(cell_rows)
        want = combo["final"]
        d_mape = sw["mape"] - want["test_mape"]
        d_acc = sw["acc15"] - want["test_acc15"]
        # curves JSON 은 소수 4자리(mape)·4자리(acc)로 반올림돼 있다.
        # **라벨 B 는 기존 36회와 다른 정답을 쓰므로 대조 자체가 성립하지 않는다.**
        ok = (abs(d_mape) <= 5e-5 + a.tol and abs(d_acc) <= 5e-3 + a.tol
              if a.labels == "A" else None)
        if ok is False:
            mismatches.append((key, want["test_mape"], sw["mape"], want["test_acc15"], sw["acc15"]))

        verdict = {True: "OK", False: "**불일치**", None: "대조없음(B)"}[ok]
        print(f"[{i}/{len(combos)}] {key:<34} "
              f"MAPE {sw['mape']:.4f} (기존 {want['test_mape']:.4f}, Δ{d_mape:+.2e}) "
              f"Acc15 {sw['acc15']:.2f} (기존 {want['test_acc15']:.2f}, Δ{d_acc:+.2e}) "
              f"{verdict} "
              f"| 셀균등 MAPE {cu['cell_uniform_mape']:.4f} "
              f"| 셀 {len(cell_rows)} 버림 {len(res['dropped_cells'])} "
              f"| 캐시 적중 {res['cache_stats']['hit']}"
              + (f" | 라벨 {res['label_stats']}" if a.labels != "A" else "")
              + (f" · 문제 {len(problems)}" if problems else ""))

        np.savez_compressed(
            OUT_DIR / f"{key}{tag}.npz",
            preds=res["preds"], refs=res["refs"],
            seen_unseen_id=res["su_ids"], dataset_id=res["ds_ids"],
            cell_start=np.array([c["start"] for c in cell_rows]),
            cell_stop=np.array([c["stop"] for c in cell_rows]),
            cell_files=np.array([c["file"] for c in cell_rows]),
        )
        summary[key] = {
            "model": combo["model"], "domain": combo["domain"], "seed": combo["seed"],
            "checkpoint": combo["ckpt"], "curve_json": combo["curve_json"],
            "device": device, "tensor_cache": not a.no_cache,
            "labels": a.labels,
            "label_source": str(LABEL_SOURCES[a.labels].relative_to(REPO)),
            "label_lookup_stats": res["label_stats"],
            "n_cells": len(cell_rows),
            "dropped_cells": res["dropped_cells"],
            "n_samples": int(len(res["preds"])),
            "sample_weighted": sw,
            "reported": {"test_mape": want["test_mape"], "test_acc15": want["test_acc15"],
                         "test_mae": want["test_mae"], "test_rmse": want["test_rmse"],
                         "test_seen_mape": want.get("test_seen_mape"),
                         "test_unseen_mape": want.get("test_unseen_mape")},
            "delta": {"mape": d_mape, "acc15": d_acc},
            "reconciles": (None if ok is None else bool(ok)),
            "cell_uniform": cu,
            "boundary_problems": problems,
            "cells": cell_rows,
        }

    out_json = REPO / f"experiments/results/cell_metrics{tag}.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
    print(f"\n기록: {out_json.relative_to(REPO)}")
    print(f"      {OUT_DIR.relative_to(REPO)}/*.npz  ({len(summary)}건)")

    print(f"\n경계 검증: 문제 있는 조합 {len(all_problems)} / {len(summary)}")
    for key, ps in all_problems:
        for p in ps:
            print(f"  {key}: {p}")
    if blocked:
        print(f"\n라벨없음으로 돌지 못한 조합 {len(blocked)}:")
        for key, cell in blocked:
            print(f"  {key}  (처음 걸린 셀: {cell})")
    print(f"정합성 검증: 재현 실패 {len(mismatches)} / {len(summary)}")
    for key, wm, gm, wa, ga in mismatches:
        print(f"  {key}: MAPE 기존 {wm:.4f} 재계산 {gm:.6f} · Acc15 기존 {wa:.2f} 재계산 {ga:.4f}")

    return 0 if not all_problems and not mismatches and not blocked else 2


if __name__ == "__main__":
    sys.exit(main())
