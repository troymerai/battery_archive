#!/usr/bin/env python3
"""백그라운드 학습 실행.

    python train/launch.py BatteryLife/train_eval_scripts/CPTransformer.sh
    python train/launch.py ... --dry-run     명령만 보고 실행하지 않음

하는 일 넷:

1. ``train/paths.py`` 로 치환한 사본을 ``.build/`` 에 만든다
2. ``runs/<시각>_<이름>/`` 을 만들고 치환 목록 · 설정 · 하드웨어를 남긴다
3. Git Bash 로 백그라운드 실행하고 stdout·stderr 를 ``log.txt`` 에 쌓는다
4. pid 를 남긴다

**Windows 에서는 Git Bash 가 필요합니다.** 상위 학습 스크립트가 bash
파일이라 바꿀 수 없습니다. 라벨 검증 경로는 bash 없이 돌아가므로 첫 태그
범위에서는 필요하지 않습니다.

실행 전에 ``runs/<...>/changes.txt`` 를 반드시 읽으십시오. 무엇을 바꿔서
돌렸는지 모르면 결과가 갈렸을 때 원인을 코드에서 찾게 됩니다.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from train import paths as paths_mod
from verify import REPO_ROOT, load_config, use_utf8_stdout, write_text

use_utf8_stdout()

RUNS_DIR = REPO_ROOT / "runs"

# Git for Windows 의 흔한 설치 위치. PATH 에 없을 때 여기서 찾습니다.
_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
)


def find_bash() -> str | None:
    found = shutil.which("bash")
    if found:
        return found
    for candidate in _BASH_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def prepare(relative_path: str, config: dict | None = None) -> dict:
    """치환 사본을 만들고 run 디렉터리를 꾸립니다. 실행은 하지 않습니다."""
    config = config if config is not None else load_config()

    script_dir = str(Path(relative_path).parent).replace("\\", "/")
    results = paths_mod.build_all(script_dir, "*.sh", config)

    target = paths_mod.BUILD_DIR / relative_path
    if not target.exists():
        raise FileNotFoundError(f"치환 사본이 없습니다: {target}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"{stamp}_{Path(relative_path).stem}"
    run_dir.mkdir(parents=True, exist_ok=True)

    changed = [r for r in results if r["changes"]]
    write_text(
        run_dir / "changes.txt",
        "\n\n".join(paths_mod.format_changes(r) for r in changed)
        or "치환된 파일이 없습니다.\n",
    )
    write_text(
        run_dir / "config.txt",
        "\n".join(f"{key}={value}" for key, value in sorted(config.items())) + "\n",
    )

    hardware = REPO_ROOT / "manifests" / "hardware.txt"
    write_text(
        run_dir / "README.txt",
        "이 실행에 쓰인 것\n"
        f"  원본 : upstream/{relative_path}\n"
        f"  사본 : {target.relative_to(REPO_ROOT).as_posix()}\n"
        f"  치환 : changes.txt ({sum(len(r['changes']) for r in results)}건)\n"
        f"  설정 : config.txt\n"
        f"  로그 : log.txt\n\n"
        "지표는 log.txt 의 'Best model performance:' 줄에 있습니다.\n"
        "  python train/collect.py " + run_dir.name + "\n\n"
        f"하드웨어를 {hardware.relative_to(REPO_ROOT).as_posix()} 에 기록하십시오.\n"
        "LOCK 의 interval 항목은 그 기록 없이는 뜻이 없습니다.\n",
    )
    return {"run_dir": run_dir, "script": target, "results": results}


def launch(relative_path: str, config: dict | None = None,
           dry_run: bool = False) -> int:
    prepared = prepare(relative_path, config)
    run_dir, script = prepared["run_dir"], prepared["script"]

    bash = find_bash()
    if bash is None:
        print(
            "bash 를 찾지 못했습니다.\n"
            "Windows 에서는 Git for Windows 를 설치하십시오 "
            "(https://git-scm.com/download/win).\n"
            "상위 학습 스크립트가 bash 파일이라 이것만은 우회되지 않습니다.\n"
            "라벨 검증에는 bash 가 필요 없습니다.",
            file=sys.stderr,
        )
        return 1

    command = [bash, str(script)]
    print(f"run 디렉터리: {run_dir}")
    print(f"명령: {' '.join(command)}")
    print(f"작업 디렉터리: {script.parent}")

    if dry_run:
        print("\n(--dry-run: 실행하지 않았습니다)")
        print(f"치환 목록: {(run_dir / 'changes.txt')}")
        return 0

    log_path = run_dir / "log.txt"
    with open(log_path, "w", encoding="utf-8", newline="\n") as log:
        process = subprocess.Popen(
            command,
            cwd=str(script.parent),
            stdout=log,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )

    write_text(run_dir / "pid.txt", f"{process.pid}\n")
    print(f"\npid {process.pid} 로 실행했습니다. 로그: {log_path}")
    print("먼저 changes.txt 를 읽으십시오. 무엇을 바꿔 돌렸는지가 거기 있습니다.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="train/launch.py",
        description="치환 사본을 만들어 백그라운드로 학습을 돌립니다",
    )
    parser.add_argument("script", help="upstream/ 아래 상대 경로 (.sh)")
    parser.add_argument("--dry-run", action="store_true",
                        help="치환만 하고 실행하지 않음")
    args = parser.parse_args(argv)
    return launch(args.script, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
