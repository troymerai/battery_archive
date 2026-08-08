"""A/B 본 실험 — **한 조합**을 돌린다. 반복은 `train/run_label_ab.ps1` 이 한다.

네 조건
-------
`AA` · `AB` · `BA` · `BB` — 앞 글자가 **학습** 라벨, 뒷 글자가 **시험** 라벨.

| 조건 | train | val | test |
|---|---|---|---|
| AA | A | A | A |
| AB | A | **A** | B |
| BA | B | **B** | A |
| BB | B | B | B |

**val 은 train 을 따릅니다.** 검증 집합은 조기종료와 최적 모델 선택에 쓰이므로
학습 절차의 일부다. 시험 라벨을 val 에 주면 시험 정답이 모델 선택에 새어 든다.

체크포인트를 조건별로 가르는 이유
---------------------------------
네 조건은 모델·하이퍼파라미터·시드가 같아 상위 `setting` 문자열이
**완전히 같다** (`run_main.py:141-151`). 그런데 상위는 실행을 시작할 때 그
폴더를 **지운다** (`:213-215`). 한 루트에 몰면 뒤 조건이 앞 조건을 지운다.
그래서 `data/checkpoints_label_ab/<조건>/` 로 가른다.

**기존 `data/checkpoints/`(684 MB)는 건드리지 않는다** — 루트 자체가 다르다.

    py -3.12 train/run_label_ab_one.py --condition AB --model CPMLP --seed 42 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / ".build/batterylife/run_main_nodeepspeed.py"
CURVES = REPO / "experiments/results/curves"
OUT_ROOT = REPO / "experiments/results/label_ab"
CKPT_ROOT = REPO / "data/checkpoints_label_ab"
LOG_ROOT = REPO / "runs/label_ab"

CONDITIONS = {"AA": ("A", "A"), "AB": ("A", "B"), "BA": ("B", "A"), "BB": ("B", "B")}
MODELS = ["CPMLP", "CPTransformer"]
SEEDS = [42, 2021, 2024, 7, 1234]
DOMAIN = "Li-ion"
EXCLUDE_PREFIX = "Tongji"
CACHE_TAG = "liion"
ARGS_SEED = 2021          # Li-ion 은 3 시드가 같은 하이퍼파라미터를 쓴다
TIMEOUT_S = {"CPMLP": 24 * 60, "CPTransformer": 61 * 60}

BEST = re.compile(
    r"Best model performance: Test MAE: ([\d.]+) \| Test RMSE: ([\d.]+) \| "
    r"Test MAPE: ([\d.]+) \| Test 15%-accuracy: ([\d.]+) \| Test 10%-accuracy: ([\d.]+) \| "
    r"Val MAE: ([\d.]+) \| Val RMSE: ([\d.]+) \| Val MAPE: ([\d.]+) \| "
    r"Val 15%-accuracy: ([\d.]+) \| Val 10%-accuracy: ([\d.]+)")
SEEN = re.compile(r"Test Seen MAPE: ([\d.]+) \| Test Unseen MAPE: ([-\d.]+)")
EPOCH = re.compile(r"^Epoch: (\d+) \| Train Loss: ([\d.]+)", re.M)


def result_path(cond: str, model: str, seed: int) -> Path:
    return OUT_ROOT / cond / f"{model}_s{seed}.json"


def find_args(model: str) -> dict:
    for p in sorted(CURVES.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if (d.get("group") == "main" and d["model"] == model
                and d["domain"] == DOMAIN and d["seed"] == ARGS_SEED):
            return d["args"]
    raise SystemExit(f"curves 에서 {model}/{DOMAIN}/s{ARGS_SEED} 를 못 찾았습니다.")


def build(cond: str, model: str, seed: int, port: int):
    a = find_args(model)
    train_lab, test_lab = CONDITIONS[cond]
    ckpt = CKPT_ROOT / cond
    env = {
        "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1", "WANDB_MODE": "disabled",
        "OMP_NUM_THREADS": "4", "CUDA_VISIBLE_DEVICES": "0",
        "BLIFE_TENSOR_CACHE": CACHE_TAG,
        "BLIFE_EXCLUDE_PREFIX": EXCLUDE_PREFIX,
        # val 은 train 을 따른다 — 진입점이 기본으로 그렇게 채우지만 여기서도
        # 명시해 로그만 보고도 조건을 읽을 수 있게 한다.
        "BLIFE_LABELS": f"train={train_lab},val={train_lab},test={test_lab}",
    }
    cmd = [
        "accelerate", "launch", "--num_processes", "1",
        "--main_process_port", str(port), str(ENTRY),
        "--task_name", a["task_name"], "--data", a["data"], "--is_training", "1",
        "--root_path", a["root_path"], "--model_id", a["model_id"],
        "--model", a["model"], "--features", a["features"],
        "--seq_len", str(a["seq_len"]), "--label_len", str(a["label_len"]),
        "--factor", str(a["factor"]), "--enc_in", str(a["enc_in"]),
        "--dec_in", str(a["dec_in"]), "--c_out", str(a["c_out"]),
        "--des", a["des"], "--itr", "1", "--seed", str(seed),
        "--d_model", str(a["d_model"]), "--d_ff", str(a["d_ff"]),
        "--batch_size", str(a["batch_size"]),
        "--learning_rate", str(a["learning_rate"]),
        "--train_epochs", str(a["train_epochs"]),
        "--least_epochs", str(a["least_epochs"]),
        "--model_comment", a["model_comment"],
        "--accumulation_steps", str(a["accumulation_steps"]),
        "--charge_discharge_length", str(a["charge_discharge_length"]),
        "--dataset", a["dataset"], "--num_workers", "0",
        "--e_layers", str(a["e_layers"]), "--lstm_layers", str(a["lstm_layers"]),
        "--d_layers", str(a["d_layers"]), "--patience", str(a["patience"]),
        "--n_heads", str(a["n_heads"]),
        "--early_cycle_threshold", str(a["early_cycle_threshold"]),
        "--dropout", str(a["dropout"]), "--lradj", a["lradj"], "--loss", a["loss"],
        "--checkpoints", str(ckpt.as_posix()),
    ]
    return cmd, env, a


def parse_log(text: str) -> dict:
    out: dict = {"epochs": []}
    m = BEST.search(text)
    if m:
        f = [float(x) for x in m.groups()]
        out["final"] = {
            "test_mae": f[0], "test_rmse": f[1], "test_mape": f[2],
            "test_acc15": f[3], "test_acc10": f[4],
            "vali_mae": f[5], "vali_rmse": f[6], "vali_mape": f[7],
            "vali_acc15": f[8], "vali_acc10": f[9],
        }
    s = SEEN.search(text)
    if s:
        out.setdefault("final", {})["test_seen_mape"] = float(s.group(1))
        out["final"]["test_unseen_mape"] = float(s.group(2))
    for e in EPOCH.finditer(text):
        out["epochs"].append({"epoch": int(e.group(1)), "train_loss": float(e.group(2))})
    out["n_epochs"] = len(out["epochs"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--port", type=int, default=29000)
    ap.add_argument("--timeout", type=int, default=None, help="초. 기본은 모델별 값")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cmd, env_add, src = build(a.condition, a.model, a.seed, a.port)
    res = result_path(a.condition, a.model, a.seed)
    timeout = a.timeout if a.timeout is not None else TIMEOUT_S[a.model]

    if a.dry_run:
        print(json.dumps({
            "condition": a.condition, "model": a.model, "seed": a.seed,
            "labels": env_add["BLIFE_LABELS"],
            "checkpoints": str((CKPT_ROOT / a.condition).relative_to(REPO)),
            "result": str(res.relative_to(REPO)),
            "timeout_s": timeout, "port": a.port,
            "env": {k: v for k, v in env_add.items() if k.startswith("BLIFE")},
            "cmd": " ".join(cmd),
        }, ensure_ascii=False))
        return 0

    res.parent.mkdir(parents=True, exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    (CKPT_ROOT / a.condition).mkdir(parents=True, exist_ok=True)
    log = LOG_ROOT / f"{a.condition}_{a.model}_s{a.seed}.log"

    env = dict(os.environ)
    env.update(env_add)

    t0 = time.perf_counter()
    timed_out = False
    try:
        proc = subprocess.run(cmd, cwd=REPO / "upstream/BatteryLife", env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
        rc, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = -9
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\n\n*** 타임아웃 {timeout}s 초과로 죽였습니다 ***"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
    elapsed = time.perf_counter() - t0

    log.write_text(
        f"# {a.condition} / {a.model} / seed {a.seed}\n"
        f"# labels={env_add['BLIFE_LABELS']}\n"
        f"# checkpoints={CKPT_ROOT / a.condition}\n"
        f"# rc={rc} timed_out={timed_out} elapsed={elapsed:.1f}s timeout={timeout}s\n"
        f"# cmd: {' '.join(cmd)}\n"
        "\n===== STDOUT =====\n" + stdout + "\n===== STDERR =====\n" + stderr,
        encoding="utf-8")

    parsed = parse_log(stdout)
    ok = (rc == 0 and "final" in parsed)
    if ok:
        res.write_text(json.dumps({
            "condition": a.condition, "train_labels": CONDITIONS[a.condition][0],
            "test_labels": CONDITIONS[a.condition][1],
            "model": a.model, "domain": DOMAIN, "seed": a.seed,
            "exclude_prefix": EXCLUDE_PREFIX, "tensor_cache": CACHE_TAG,
            "elapsed_s": round(elapsed, 1),
            "checkpoints": str((CKPT_ROOT / a.condition).relative_to(REPO)),
            "log": str(log.relative_to(REPO)),
            "args": src, **parsed,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK   {a.condition}/{a.model}/s{a.seed}  {elapsed:.0f}s  "
              f"MAPE {parsed['final']['test_mape']:.4f}  epochs {parsed['n_epochs']}")
        return 0

    fail = OUT_ROOT / "_failures"
    fail.mkdir(parents=True, exist_ok=True)
    (fail / f"{a.condition}_{a.model}_s{a.seed}.txt").write_text(
        f"rc={rc} timed_out={timed_out} elapsed={elapsed:.1f}s\n"
        f"cmd: {' '.join(cmd)}\n"
        f"log: {log}\n\n===== STDERR =====\n{stderr}\n", encoding="utf-8")
    print(f"FAIL {a.condition}/{a.model}/s{a.seed}  rc={rc} "
          f"{'(타임아웃)' if timed_out else ''}  {elapsed:.0f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
