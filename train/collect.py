#!/usr/bin/env python3
"""체크포인트 · 로그 → 지표 JSON.

    python train/collect.py <run 디렉터리 이름 또는 경로>
    python train/collect.py --all

상위 코드는 지표를 파일로 저장하지 않습니다. wandb 로 보내고 stdout 에
찍을 뿐입니다 (``run_main.py:427-430``). 그래서 여기서는 **로그를 파싱**
합니다. 형식은 이렇습니다.

    Best model performance: Test MAE: 0.1234 | Test RMSE: ... | Test MAPE: ...
      | Test 15%-accuracy: ... | Test 10%-accuracy: ... | Val MAE: ...
    Best model performance: Test Seen MAPE: ... | Test Unseen MAPE: ...
    Best model performance: Test Seen 15%-accuracy: ... | Test Unseen 15%-accuracy: ...
    Best model performance: Test Seen 10%-accuracy: ... | Test Unseen 10%-accuracy: ...

설정은 체크포인트 폴더의 ``args.json`` 에 있습니다 (``run_main.py:222``).

주의 — alpha 인자의 도움말이 값과 어긋나 있습니다
--------------------------------------------------

``run_main.py:125-126`` 에서

    --alpha1  default 0.15   help='the 10 percent alpha for alpha-accuracy'
    --alpha2  default 0.1    help='the 15 percent alpha for alpha-accuracy'

도움말 문구가 서로 바뀌어 있습니다. 값과 출력 라벨은 맞습니다 —
``alpha_acc1`` (=0.15) 이 ``15%-accuracy`` 로 찍힙니다. **도움말만 보고
따라가면 15%-Acc 와 10%-Acc 를 뒤집어 읽게 됩니다.**

MAPE 는 비율입니다 (``utils/metrics.py:26`` — ``mean(|(pred-true)/true|)``).
백분율이 아닙니다. 논문 표와 비교할 때 100 을 곱해야 하는지 확인하십시오.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from verify import REPO_ROOT, read_json, read_text, use_utf8_stdout, write_json

use_utf8_stdout()

RUNS_DIR = REPO_ROOT / "runs"
RESULTS_DIR = REPO_ROOT / "experiments" / "results"

_BEST_LINE = re.compile(r"^Best model performance:\s*(.+)$", re.M)
# 키에 **숫자가 들어갑니다** — ``Test 15%-accuracy`` · ``Test 10%-accuracy``.
# 문자 클래스에서 0-9 를 빼면 네 개의 accuracy 지표가 전부 ``%-accuracy``
# 하나로 뭉쳐 마지막 값만 남습니다. 실제로 그렇게 새고 있었습니다.
_PAIR = re.compile(r"([A-Za-z0-9%\- ]+?):\s*([-+0-9.eE]+)")


def parse_log(text: str) -> dict:
    """``Best model performance:`` 줄에서 지표를 뽑습니다.

    여러 번 찍혀 있으면 **마지막 것** 을 씁니다. 재시작한 실행에서 앞의
    것은 중간 결과입니다.
    """
    metrics: dict = {}
    for match in _BEST_LINE.finditer(text):
        for key, value in _PAIR.findall(match.group(1)):
            key = key.strip().replace(" ", "_")
            if not key:
                continue
            try:
                metrics[key] = float(value)
            except ValueError:
                continue
    return metrics


def collect(run_dir) -> dict:
    """run 디렉터리 하나에서 지표를 모읍니다."""
    run_dir = Path(run_dir)
    if not run_dir.is_absolute() and not run_dir.exists():
        run_dir = RUNS_DIR / run_dir
    if not run_dir.exists():
        raise FileNotFoundError(f"run 디렉터리가 없습니다: {run_dir}")

    log_path = run_dir / "log.txt"
    record = {
        "run": run_dir.name,
        "log_found": log_path.exists(),
        "metrics": {},
        "args": None,
        "changes_count": None,
        "incomplete": True,
        "note": "",
    }

    if log_path.exists():
        text = read_text(log_path)
        record["metrics"] = parse_log(text)
        record["incomplete"] = not record["metrics"]
        if record["incomplete"]:
            tail = [line for line in text.splitlines() if line.strip()][-3:]
            record["note"] = (
                "'Best model performance:' 줄이 없습니다. 아직 도는 중이거나 죽었습니다. "
                "로그 끝: " + " / ".join(tail)
            )

    changes = run_dir / "changes.txt"
    if changes.exists():
        record["changes_count"] = read_text(changes).count("[")

    # 체크포인트 폴더의 args.json. 여러 개면 가장 최근 것.
    candidates = sorted(run_dir.rglob("args.json"))
    if not candidates:
        config_path = run_dir / "config.txt"
        if config_path.exists():
            record["note"] += (
                "  args.json 을 찾지 못했습니다. CKPT_ROOT 아래를 보십시오 "
                "(config.txt 참조)."
            )
    else:
        record["args"] = read_json(candidates[-1])

    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="train/collect.py",
        description="학습 로그에서 지표를 뽑아 JSON 으로 남깁니다",
    )
    parser.add_argument("run", nargs="?", help="run 디렉터리 이름 또는 경로")
    parser.add_argument("--all", action="store_true", help="runs/ 전부")
    parser.add_argument("--out", default="", help="출력 JSON 경로")
    args = parser.parse_args(argv)

    if args.all:
        if not RUNS_DIR.exists():
            print("runs/ 가 없습니다. 아직 아무것도 돌리지 않았습니다.")
            return 0
        records = [collect(path) for path in sorted(RUNS_DIR.iterdir()) if path.is_dir()]
    elif args.run:
        records = [collect(args.run)]
    else:
        parser.print_help()
        return 0

    for record in records:
        print(f"\n[{record['run']}]")
        if record["metrics"]:
            width = max(len(key) for key in record["metrics"])
            for key, value in record["metrics"].items():
                print(f"  {key.ljust(width)}  {value}")
        else:
            print(f"  지표 없음 — {record['note'] or '로그가 없습니다'}")

    destination = Path(args.out) if args.out else RESULTS_DIR / "train_metrics.json"
    write_json(destination, records, normalized=True)
    print(f"\n기록: {destination}")
    print(
        "\nMAPE 는 비율입니다 (백분율 아님). 15%-Acc 는 alpha_acc1 입니다 — "
        "run_main.py 의 도움말 문구가 값과 어긋나 있으니 그것을 따라가지 마십시오."
    )
    print("LOCK 의 interval 항목에 넣기 전에 manifests/hardware.txt 를 채우십시오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
