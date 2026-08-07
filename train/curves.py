"""runs/ 의 학습 로그에서 에폭별 지표를 뽑아 정규화 JSON 으로 저장합니다.

학습하지 않습니다. 이미 있는 로그만 읽습니다.
로그에 없는 값은 만들지 않습니다 — 없으면 null 입니다.

    python -m train.curves

출력: experiments/results/curves/<model>_<domain>_s<seed>[__<tag>].json
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # 콘솔이 cp949 여도 한글이 깨지지 않게
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs" / "2026-08-04"
OUT = ROOT / "experiments" / "results" / "curves"

# ── 로그에서 실제로 확인한 형식 ──────────────────────────────────────────
# Epoch: 13 | Train Loss: 0.01120| Train cl loss: 0.00000| Train lc loss: 0.00000
#  | Train RMSE: 56.3487304 | Train MAPE: 0.1122775 | Vali RMSE: 181.4223160
#  | Vali MAE: 119.6483721| Vali MAPE: 0.1825967| Test RMSE: 204.4183486
#  | Test MAE: 121.3789885 | Test MAPE: 0.1409135
NUM = r"([-+0-9.eE]+)"
RE_EPOCH = re.compile(
    r"Epoch:\s*(\d+)\s*\|\s*Train Loss:\s*" + NUM +
    r"\s*\|\s*Train cl loss:\s*" + NUM +
    r"\s*\|\s*Train lc loss:\s*" + NUM +
    r"\s*\|\s*Train RMSE:\s*" + NUM +
    r"\s*\|\s*Train MAPE:\s*" + NUM +
    r"\s*\|\s*Vali RMSE:\s*" + NUM +
    r"\s*\|\s*Vali MAE:\s*" + NUM +
    r"\s*\|\s*Vali MAPE:\s*" + NUM +
    r"\s*\|\s*Test RMSE:\s*" + NUM +
    r"\s*\|\s*Test MAE:\s*" + NUM +
    r"\s*\|\s*Test MAPE:\s*" + NUM
)
RE_COUNTER = re.compile(r"EarlyStopping counter:\s*(\d+)\s*out of\s*(\d+)")
RE_BEST = re.compile(
    r"Best model performance:\s*Test MAE:\s*" + NUM +
    r"\s*\|\s*Test RMSE:\s*" + NUM +
    r"\s*\|\s*Test MAPE:\s*" + NUM +
    r"\s*\|\s*Test 15%-accuracy:\s*" + NUM +
    r"\s*\|\s*Test 10%-accuracy:\s*" + NUM +
    r"\s*\|\s*Val MAE:\s*" + NUM +
    r"\s*\|\s*Val RMSE:\s*" + NUM +
    r"\s*\|\s*Val MAPE:\s*" + NUM +
    r"\s*\|\s*Val 15%-accuracy:\s*" + NUM +
    r"\s*\|\s*Val 10%-accuracy:\s*" + NUM
)
RE_SEEN_MAPE = re.compile(
    r"Test Seen MAPE:\s*" + NUM + r"\s*\|\s*Test Unseen MAPE:\s*" + NUM)
RE_SEEN_ACC15 = re.compile(
    r"Test Seen 15%-accuracy:\s*" + NUM + r"\s*\|\s*Test Unseen 15%-accuracy:\s*" + NUM)
RE_SEEN_ACC10 = re.compile(
    r"Test Seen 10%-accuracy:\s*" + NUM + r"\s*\|\s*Test Unseen 10%-accuracy:\s*" + NUM)
RE_CFG = re.compile(r"\{'task_name':.*?'alpha2':\s*[-+0-9.eE]+\}")
RE_HDR = re.compile(r"=====\s*([^=\n]+?)\s*=====")
RE_LOADED = re.compile(r"Loading (training|vali|test) samples")

# dataset 이름은 <도메인><seed> 규칙입니다 (docs/RUN.md §8-5).
DOMAIN_OF = {"CALB": "CALB", "NAion": "Na-ion", "ZN-coin": "Zn-ion",
             "MIX_large_841": "Li-ion"}

# 시험 셀 수 — docs/PLAN.md §3-0 실측표
TEST_CELLS = {"CALB": 5, "Na-ion": 5, "Zn-ion": 20, "Li-ion": 162}

# 어떤 로그가 어느 묶음인지. (경로, 묶음, 태그)
#   main       — Table 3 대조표(보고서 부록 B)를 만든 36회 정규 실행
#   diagnostic — Zn-ion 학습률/배치/patience 진단 · Li-ion 재실행
#   superseded — 옛 셸 파라미터 기준. 그림에 쓰지 않습니다.
#
# Zn-ion 만 정본이 `zn_lr9.log`(lr 5e-5) 입니다. 문서 지정 학습률
# (CPMLP 5e-4 · CPTransformer 1e-3)로는 학습되지 않아 다른 세 도메인과 같은
# 5e-5 로 낮춰 9회를 다시 돌렸고 그쪽이 표에 들어갔습니다. runs/README.md 참고.
# 파일명 접미사는 `tag` 와 같습니다 — 정본 여부는 파일명이 아니라 `group` 입니다.
SOURCES: list[tuple[str, str, str | None]] = [
    ("20260804-152940_*_CALB_s*.log", "main", None),
    ("20260804-153653_*_Na-ion_s*.log", "main", None),
    ("20260804-154322_*_Zn-ion_s*.log", "diagnostic", None),
    ("run_liion.log", "main", None),
    ("run_liion_rest.log", "diagnostic", "rerun"),
    ("zn_lr9.log", "main", "lr5e-05"),
    ("zn_x1_lr.log", "diagnostic", "x1_lr"),
    ("zn_x2_batch.log", "diagnostic", "x2_batch"),
    ("zn_x3_patience.log", "diagnostic", "x3_patience"),
    ("zn_diagnose.log", "diagnostic", "diagnose"),
    ("timing_*.log", "superseded", "timing"),
    ("smoke_*.log", "superseded", "smoke"),
    ("test_liion.log", "superseded", "test"),
    ("test_halfbatch.log", "superseded", "test"),
]


def read_text(path: Path) -> str:
    """UTF-16LE(PowerShell) 과 UTF-8(bash) 를 모두 읽습니다."""
    raw = path.read_bytes()
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16-le", "replace")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw.decode("utf-8-sig", "replace")
    return raw.decode("utf-8", "replace")


def split_runs(text: str) -> list[tuple[str | None, str]]:
    """한 파일에 여러 실행이 이어 붙은 로그를 실행 단위로 자릅니다."""
    starts = [m.start() for m in RE_CFG.finditer(text)]
    if not starts:
        return []
    out = []
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        # 설정 dict 앞에 붙은 '===== 이름 =====' 머리글을 찾아 붙입니다.
        head = text[starts[i - 1] if i else 0:s]
        hdrs = RE_HDR.findall(head)
        name = hdrs[-1].strip() if hdrs else None
        out.append((name, text[s:end]))
    return out


def parse_run(block: str) -> dict:
    cfg = ast.literal_eval(RE_CFG.search(block).group(0))

    # 에폭별 지표 — 순서대로 읽으면서 조기 종료 카운터를 함께 봅니다.
    epochs, improved, cur = [], [], None
    for line in block.splitlines():
        m = RE_EPOCH.search(line)
        if m:
            g = m.groups()
            cur = {
                "epoch": int(g[0]),
                "train_loss": float(g[1]),
                "train_cl_loss": float(g[2]),
                "train_lc_loss": float(g[3]),
                "train_rmse": float(g[4]),
                "train_mape": float(g[5]),
                "vali_rmse": float(g[6]),
                "vali_mae": float(g[7]),
                "vali_mape": float(g[8]),
                "test_rmse": float(g[9]),
                "test_mae": float(g[10]),
                "test_mape": float(g[11]),
                # 에폭별 15%-Acc · Seen/Unseen 은 로그에 없습니다.
                "vali_acc15": None,
                "test_acc15": None,
                "test_seen_mape": None,
                "test_unseen_mape": None,
            }
            epochs.append(cur)
            improved.append(True)
            continue
        if cur is not None and RE_COUNTER.search(line):
            improved[-1] = False

    # 최적 검증 에폭 = 조기 종료 카운터가 뒤따르지 않은 마지막 에폭.
    # (least_epochs 구간은 카운터가 0 으로 찍히므로 '개선 아님'으로 셉니다.)
    best_epoch = None
    for e, ok in zip(epochs, improved):
        if ok:
            best_epoch = e["epoch"]

    mb = RE_BEST.search(block)
    best = None
    if mb:
        g = mb.groups()
        best = {
            "test_mae": float(g[0]), "test_rmse": float(g[1]),
            "test_mape": float(g[2]), "test_acc15": float(g[3]),
            "test_acc10": float(g[4]), "vali_mae": float(g[5]),
            "vali_rmse": float(g[6]), "vali_mape": float(g[7]),
            "vali_acc15": float(g[8]), "vali_acc10": float(g[9]),
        }
    for rx, keys in ((RE_SEEN_MAPE, ("test_seen_mape", "test_unseen_mape")),
                     (RE_SEEN_ACC15, ("test_seen_acc15", "test_unseen_acc15")),
                     (RE_SEEN_ACC10, ("test_seen_acc10", "test_unseen_acc10"))):
        m = rx.search(block)
        if m and best is not None:
            best[keys[0]], best[keys[1]] = float(m.group(1)), float(m.group(2))

    # 교차 검증 — 최적 에폭의 Test MAPE 가 최종 보고값과 같아야 합니다.
    best_epoch_agrees = None
    if best is not None and best_epoch is not None:
        row = next(e for e in epochs if e["epoch"] == best_epoch)
        best_epoch_agrees = abs(row["test_mape"] - best["test_mape"]) < 5e-5

    ds = cfg["dataset"]
    domain = next((v for k, v in DOMAIN_OF.items() if ds.startswith(k)), None)

    return {
        "model": cfg["model"],
        "domain": domain,
        "dataset": ds,
        "seed": cfg["seed"],
        "conditions": {
            "data_build": "Dataset_original",
            "learning_rate": cfg["learning_rate"],
            "batch_size": cfg["batch_size"],
            "patience": cfg["patience"],
            "train_epochs": cfg["train_epochs"],
            "least_epochs": cfg["least_epochs"],
            "d_model": cfg["d_model"],
            "d_ff": cfg["d_ff"],
            "e_layers": cfg["e_layers"],
            "d_layers": cfg["d_layers"],
            "dropout": cfg["dropout"],
            "lradj": cfg["lradj"],
            "loss": cfg["loss"],
            "seq_len": cfg["seq_len"],
            "charge_discharge_length": cfg["charge_discharge_length"],
        },
        "test_cells": TEST_CELLS.get(domain),
        "last_epoch": epochs[-1]["epoch"] if epochs else None,
        "best_val_epoch": best_epoch,
        "best_epoch_agrees_with_final": best_epoch_agrees,
        "early_stopped": "Early stopping" in block,
        "n_epochs": len(epochs),
        "final": best,
        "epochs": epochs,
        "args": cfg,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written, failed, seen = [], [], {}

    for pattern, group, tag in SOURCES:
        for path in sorted(RUNS.glob(pattern)):
            text = read_text(path)
            blocks = split_runs(text)
            if not blocks:
                failed.append((str(path.relative_to(ROOT)), "설정 dict 가 없습니다 — 학습이 시작되지 않은 로그"))
                continue
            for name, block in blocks:
                try:
                    rec = parse_run(block)
                except Exception as exc:  # noqa: BLE001
                    failed.append((f"{path.name}:{name or '?'}", f"{type(exc).__name__}: {exc}"))
                    continue
                if not rec["epochs"]:
                    failed.append((f"{path.name}:{name or '?'}", "에폭 지표 줄이 없습니다 — 중단된 실행"))
                    continue
                rec["group"] = group
                rec["tag"] = tag
                rec["source_log"] = str(path.relative_to(ROOT)).replace("\\", "/")
                rec["source_header"] = name

                stem = f"{rec['model']}_{rec['domain']}_s{rec['seed']}"
                if tag:
                    stem += f"__{tag}"
                if stem in seen:  # 같은 파일 안 중복 실행
                    stem += f"__dup{seen[stem]}"
                seen[stem] = seen.get(stem, 0) + 1
                fp = OUT / f"{stem}.json"
                fp.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
                written.append((stem, group, rec["n_epochs"], rec["best_val_epoch"],
                                rec["best_epoch_agrees_with_final"]))

    print(f"저장 {len(written)}건 -> {OUT.relative_to(ROOT)}")
    for stem, group, n, be, ok in written:
        flag = "" if ok else "  << 최적에폭 대조 불일치" if ok is False else "  << 대조 불가"
        print(f"  [{group:<10}] {stem:<44} epochs={n:<3} best={be}{flag}")
    print(f"\n파싱 실패 {len(failed)}건")
    for f, why in failed:
        print(f"  {f}: {why}")


if __name__ == "__main__":
    main()
