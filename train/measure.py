#!/usr/bin/env python3
"""3에폭 사본을 돌려 **소요 시간과 메모리**를 잽니다 (지시 §E).

    python -m train.measure                       _timing36_*.sh 전부
    python -m train.measure <스크립트 이름 ...>    고른 것만

기록하는 것
-----------

전체 wall · 데이터 로딩 · 학습 에폭 평균 · **최대 VRAM** · 최대 RSS.

데이터 로딩 시간은 tqdm 이 마지막에 찍는 ``[MM:SS<00:00, ...]`` 을 train ·
vali · test 세 벌 더해서 씁니다. 에폭 시간은 ``Epoch: N cost time: X`` 입니다.

VRAM 한도
---------

**배치를 임의로 줄이지 않습니다.** OOM 이 나면 그 사실과 문서값·환산값을
적고 다음으로 넘어갑니다. 조건 변경은 사람이 정합니다.

GPU 메모리가 ``--vram-limit`` (기본 15000 MiB)를 넘으면 **그 자리에서
죽이고** 기록합니다. 16 GB 카드라 그 위는 스왑이 아니라 실패입니다.

산출물
------

``runs/<시각>_<이름>/`` 아래 ``log.txt`` · ``gpu.csv`` · ``measure.json``.
``experiments/results/`` 는 건드리지 않습니다 — 거기는 라벨 검증 산출물이고
LOCK 대상입니다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from train.launch import BATTERYLIFE, find_bash
from verify import REPO_ROOT, use_utf8_stdout, write_text

use_utf8_stdout()

BUILD_DIR = REPO_ROOT / ".build" / "batterylife"
RUNS_DIR = REPO_ROOT / "runs"

_EPOCH = re.compile(r"^Epoch:\s*(\d+)\s*cost time:\s*([\d.]+)", re.M)
# tqdm 이 완료 시 찍는 마지막 조각: ``100%|...| 60/60 [00:18<00:00,  3.33it/s]``
_TQDM_DONE = re.compile(r"100%\|[^|]*\|\s*(\d+)/\1\s*\[(\d+):(\d+)<00:00")


class GpuSampler(threading.Thread):
    """1초마다 nvidia-smi 로 GPU 메모리를 찍습니다.

    **GPU 전체 사용량**입니다. 이 기계에서 다른 것이 돌고 있으면 그만큼
    부풀려집니다 — 그래서 compute-app 별 값도 함께 남깁니다.
    """

    def __init__(self, csv_path: Path, interval: float = 1.0):
        super().__init__(daemon=True)
        self.csv_path = csv_path
        self.interval = interval
        self.stop_flag = threading.Event()
        self.peak_total = 0
        self.peak_process = 0
        self.samples = 0
        self.failed = ""

    def _query(self, args):
        done = subprocess.run(["nvidia-smi", *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
        return done.stdout if done.returncode == 0 else ""

    def run(self):
        rows = ["seconds,total_used_MiB,max_compute_app_MiB"]
        started = time.time()
        while not self.stop_flag.is_set():
            try:
                total = self._query(["--query-gpu=memory.used",
                                     "--format=csv,noheader,nounits"])
                apps = self._query(["--query-compute-apps=used_gpu_memory",
                                    "--format=csv,noheader,nounits"])
            except FileNotFoundError:
                self.failed = "nvidia-smi 를 찾지 못했습니다"
                return
            total_mib = max([int(v) for v in re.findall(r"\d+", total)] or [0])
            app_mib = max([int(v) for v in re.findall(r"\d+", apps)] or [0])
            self.peak_total = max(self.peak_total, total_mib)
            self.peak_process = max(self.peak_process, app_mib)
            self.samples += 1
            rows.append(f"{time.time() - started:.1f},{total_mib},{app_mib}")
            self.stop_flag.wait(self.interval)
        write_text(self.csv_path, "\n".join(rows) + "\n")


def _peak_rss(process) -> int:
    """프로세스 트리 전체의 최대 RSS(바이트). psutil 이 없으면 0."""
    try:
        import psutil
    except ImportError:
        return 0
    try:
        parent = psutil.Process(process.pid)
        total = parent.memory_info().rss
        for child in parent.children(recursive=True):
            try:
                total += child.memory_info().rss
            except psutil.Error:
                pass
        return total
    except psutil.Error:
        return 0


def parse_log(text: str) -> dict:
    epochs = [(int(n), float(s)) for n, s in _EPOCH.findall(text)]
    loads = [int(m) * 60 + int(s) for _, m, s in _TQDM_DONE.findall(text)]
    # tqdm 은 완료 줄을 **정확히 두 번** 찍습니다 (마지막 갱신 + 종료).
    # 값이 같다고 묶으면 서로 다른 split 이 우연히 같은 초일 때 하나가
    # 사라집니다. 짝수 번째만 씁니다.
    unique = loads[1::2]
    return {
        "epoch_seconds": [s for _, s in epochs],
        "epoch_mean_seconds": (sum(s for _, s in epochs) / len(epochs)
                               if epochs else None),
        "load_seconds_by_split": unique[:3],
        "load_seconds": sum(unique[:3]) if unique else None,
        "oom": bool(re.search(r"CUDA out of memory|OutOfMemoryError", text)),
        "traceback": bool(re.search(r"^Traceback", text, re.M)),
    }


def measure_one(script: Path, vram_limit: int, timeout: float) -> dict:
    bash = find_bash()
    if bash is None:
        return {"file": script.name, "ok": False, "why": "bash 를 찾지 못했습니다"}

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"{stamp}_{script.stem}"
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script, run_dir / script.name)
    log_path = run_dir / "log.txt"

    sampler = GpuSampler(run_dir / "gpu.csv")
    sampler.start()

    print(f"\n=== {script.name} ===", flush=True)
    print(f"  run 디렉터리: {run_dir}", flush=True)
    started = time.time()
    peak_rss = 0
    killed = ""
    with open(log_path, "w", encoding="utf-8", newline="\n") as log:
        process = subprocess.Popen(
            [bash, script.as_posix()], cwd=str(BATTERYLIFE),
            stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        while process.poll() is None:
            time.sleep(2.0)
            peak_rss = max(peak_rss, _peak_rss(process))
            if sampler.peak_total > vram_limit:
                killed = (f"VRAM {sampler.peak_total} MiB > 한도 {vram_limit} "
                          "MiB — 즉시 중단했습니다. **배치는 줄이지 않았습니다.**")
                process.kill()
                break
            if time.time() - started > timeout:
                killed = f"상한 {timeout:.0f}초를 넘겨 중단했습니다."
                process.kill()
                break
    wall = time.time() - started
    sampler.stop_flag.set()
    sampler.join(timeout=5)

    text = log_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_log(text)
    result = {
        "file": script.name,
        "run_dir": run_dir.name,
        "wall_seconds": round(wall, 1),
        "peak_vram_MiB_total": sampler.peak_total,
        "peak_vram_MiB_process": sampler.peak_process,
        "peak_rss_MiB": round(peak_rss / 1024 / 1024, 1) if peak_rss else None,
        "returncode": process.returncode,
        "killed": killed,
        **parsed,
    }
    result["ok"] = (not killed and process.returncode == 0
                    and len(parsed["epoch_seconds"]) >= 1)
    write_text(run_dir / "measure.json",
               json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"  wall {wall:.1f}초 · 로딩 {parsed['load_seconds']}초 · "
          f"에폭 평균 "
          f"{parsed['epoch_mean_seconds'] and round(parsed['epoch_mean_seconds'], 1)}초",
          flush=True)
    print(f"  최대 VRAM {sampler.peak_total} MiB (프로세스 "
          f"{sampler.peak_process} MiB) · 최대 RSS {result['peak_rss_MiB']} MiB",
          flush=True)
    if killed:
        print(f"  ** {killed}", flush=True)
    if parsed["oom"]:
        print("  ** CUDA OOM 이 로그에 있습니다. 배치는 줄이지 않았습니다 — "
              "사람이 정할 일입니다.", flush=True)
    if process.returncode not in (0, None) and not killed:
        print(f"  ** 종료 코드 {process.returncode}. 로그: {log_path}", flush=True)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="train/measure.py")
    parser.add_argument("scripts", nargs="*", help="비우면 _timing36_*.sh 전부")
    parser.add_argument("--vram-limit", type=int, default=15000,
                        help="MiB. 넘으면 즉시 중단 (기본 15000)")
    parser.add_argument("--timeout", type=float, default=3600.0,
                        help="한 개당 상한(초)")
    args = parser.parse_args(argv)

    if args.scripts:
        targets = [BUILD_DIR / name if not Path(name).is_absolute() else Path(name)
                   for name in args.scripts]
    else:
        targets = sorted(BUILD_DIR.glob("_timing36_*.sh"))
    if not targets:
        print("잴 것이 없습니다. python -m train.make_scripts 를 먼저 "
              "돌리십시오.", file=sys.stderr)
        return 1

    results = [measure_one(t, args.vram_limit, args.timeout) for t in targets]
    out = RUNS_DIR / "measure36.json"
    write_text(out, json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"\n요약: {out}")
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
