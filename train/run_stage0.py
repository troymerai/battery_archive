"""A/B 학습 0단계 예행 — **짧은 학습만** 돌린다. 본 실험이 아니다.

왜 0단계가 있는가
-----------------
추론 하네스에서 `--labels B` 가 **아무 효과 없이 조용히 무시된 적이 있다**
(`docs/reports/2026-08-07_label_ab_manifest.md` §5-2). 텐서 캐시 색인이
`eol` 을 함께 담고 있어서 `read_cell_df` 가 통째로 대체됐기 때문이다.
학습 진입점에도 같은 함정이 있었다. 그대로 80회를 돌리면 **네 조건이 전부
같은 라벨로 돌면서 "차이 없음"** 이 나온다.

그래서 본 실험 전에 두 가지를 확인한다.

* **음성 대조** — A 와 B 의 라벨이 실제로 다른 표본에서 손실이 갈리는가
* **양성 대조** — 라벨이 같은 표본에서 결과가 같은가 (라벨 말고 딴 게
  바뀌지 않았는가)

안전장치
--------
* `--checkpoints` 를 **`data/checkpoints_stage0/`** 로 돌린다. 상위
  `run_main.py:213-215` 가 시작할 때 체크포인트 폴더를 **지우기** 때문에,
  기존 36회분(684 MB)을 건드리지 않으려면 반드시 갈라야 한다
* 에폭을 짧게 준다. 본 실험이 아니다

사용
----
    py -3.12 train/run_stage0.py --labels A --tag neg_A
    py -3.12 train/run_stage0.py --labels B --tag neg_B
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CKPT_SRC = REPO / "data/checkpoints"
CKPT_STAGE0 = REPO / "data/checkpoints_stage0"
ENTRY = REPO / ".build/batterylife/run_main_nodeepspeed.py"
LOGS = REPO / "runs/stage0"
CURVES = REPO / "experiments/results/curves"

CACHE_TAG = {"Li-ion": "liion", "Zn-ion": "znion", "Na-ion": "naion", "CALB": "calb"}


def find_args(model: str, domain: str, seed: int) -> dict:
    """기존 36회의 args 를 그대로 가져온다 — 조건을 새로 만들지 않는다."""
    for p in sorted(CURVES.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if (d.get("group") == "main" and d["model"] == model
                and d["domain"] == domain and d["seed"] == seed):
            return d["args"]
    raise SystemExit(f"curves 에서 {model}/{domain}/s{seed} (group=main) 를 못 찾았습니다.")


def build_cmd(a: dict, epochs: int, seed: int, port: int) -> list[str]:
    return [
        "accelerate", "launch", "--num_processes", "1",
        "--main_process_port", str(port), str(ENTRY),
        "--task_name", a["task_name"],
        "--data", a["data"],
        "--is_training", "1",
        "--root_path", a["root_path"],
        "--model_id", a["model_id"],
        "--model", a["model"],
        "--features", a["features"],
        "--seq_len", str(a["seq_len"]),
        "--label_len", str(a["label_len"]),
        "--factor", str(a["factor"]),
        "--enc_in", str(a["enc_in"]),
        "--dec_in", str(a["dec_in"]),
        "--c_out", str(a["c_out"]),
        "--des", a["des"],
        "--itr", "1",
        "--seed", str(seed),
        "--d_model", str(a["d_model"]),
        "--d_ff", str(a["d_ff"]),
        "--batch_size", str(a["batch_size"]),
        "--learning_rate", str(a["learning_rate"]),
        "--train_epochs", str(epochs),
        "--least_epochs", str(min(a["least_epochs"], epochs)),
        "--model_comment", a["model_comment"],
        "--accumulation_steps", str(a["accumulation_steps"]),
        "--charge_discharge_length", str(a["charge_discharge_length"]),
        "--dataset", a["dataset"],
        "--num_workers", "0",
        "--e_layers", str(a["e_layers"]),
        "--lstm_layers", str(a["lstm_layers"]),
        "--d_layers", str(a["d_layers"]),
        "--patience", str(a["patience"]),
        "--n_heads", str(a["n_heads"]),
        "--early_cycle_threshold", str(a["early_cycle_threshold"]),
        "--dropout", str(a["dropout"]),
        "--lradj", a["lradj"],
        "--loss", a["loss"],
        "--checkpoints", str(CKPT_STAGE0.as_posix()),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="CPMLP")
    ap.add_argument("--domain", default="Li-ion")
    ap.add_argument("--seed", type=int, default=2021)
    ap.add_argument("--args-seed", type=int, default=None,
                    help="args 를 가져올 조합의 seed (신규 시드 검증용)")
    ap.add_argument("--labels", default="A", help="A · B · 또는 디렉터리 경로")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--exclude-prefix", default="Tongji",
                    help="비우면 제외 없음")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--port", type=int, default=28100)
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()

    src = find_args(a.model, a.domain, a.args_seed if a.args_seed is not None else a.seed)
    LOGS.mkdir(parents=True, exist_ok=True)
    CKPT_STAGE0.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["WANDB_MODE"] = "disabled"
    env["OMP_NUM_THREADS"] = "4"
    env["CUDA_VISIBLE_DEVICES"] = "0"
    if not a.no_cache:
        env["BLIFE_TENSOR_CACHE"] = CACHE_TAG[a.domain]
    else:
        env.pop("BLIFE_TENSOR_CACHE", None)
    if a.labels and a.labels != "A":
        env["BLIFE_LABELS"] = a.labels
    else:
        env.pop("BLIFE_LABELS", None)
    if a.exclude_prefix:
        env["BLIFE_EXCLUDE_PREFIX"] = a.exclude_prefix
    else:
        env.pop("BLIFE_EXCLUDE_PREFIX", None)

    cmd = build_cmd(src, a.epochs, a.seed, a.port)
    log = LOGS / f"{a.tag}.log"
    print(f"[stage0] {a.tag}  {a.model}/{a.domain}/s{a.seed}  라벨={a.labels} "
          f"에폭={a.epochs} 제외={a.exclude_prefix or '없음'} "
          f"캐시={'끔' if a.no_cache else CACHE_TAG[a.domain]}")
    print(f"         체크포인트 -> {CKPT_STAGE0.relative_to(REPO)}  (기존 36회분과 분리)")

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=REPO / "upstream/BatteryLife", env=env,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    elapsed = time.perf_counter() - t0

    log.write_text(
        f"# stage0 tag={a.tag}\n"
        f"# {a.model}/{a.domain}/seed {a.seed}  labels={a.labels} epochs={a.epochs}\n"
        f"# BLIFE_TENSOR_CACHE={env.get('BLIFE_TENSOR_CACHE')} "
        f"BLIFE_LABELS={env.get('BLIFE_LABELS')} "
        f"BLIFE_EXCLUDE_PREFIX={env.get('BLIFE_EXCLUDE_PREFIX')}\n"
        f"# 종료코드 {proc.returncode}  경과 {elapsed:.1f}s\n"
        f"# cmd: {' '.join(cmd)}\n"
        "\n===== STDOUT =====\n" + proc.stdout
        + "\n===== STDERR =====\n" + proc.stderr, encoding="utf-8")

    print(f"         종료코드 {proc.returncode}  경과 {elapsed:.1f}s  -> {log.relative_to(REPO)}")
    if proc.returncode != 0:
        tail = [l for l in proc.stderr.strip().splitlines() if l.strip()][-6:]
        for l in tail:
            print(f"         {l[:150]}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
