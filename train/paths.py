"""하드코딩 절대경로 치환.

**``upstream/`` 을 수정하지 않습니다.** 치환한 사본을 ``.build/`` 에 만들어
거기서 실행합니다. ``.build/`` 는 ``.gitignore`` 대상입니다.

    from train import paths
    result = paths.build("BatteryLife/train_eval_scripts/CPTransformer.sh")
    print(result["path"])          # .build/BatteryLife/train_eval_scripts/CPTransformer.sh
    for row in result["changes"]:  # 무엇을 바꿨는지 전부 남습니다
        print(row)

치환은 **조용히** 일어나면 안 됩니다. 무엇을 바꿨는지 모르면 결과가 갈렸을
때 원인을 코드에서 찾게 됩니다. ``changes`` 를 반드시 로그에 남기십시오.

확인된 치환 대상
----------------

``upstream`` 커밋 9572e47 / febe174 기준으로 실제 위치를 확인했습니다.

======================================= ==========================================
원본                                     대체
======================================= ==========================================
``checkpoints=/data/hwx/BL_new``        ``CKPT_ROOT``
``root_path=/data/trf/.../dataset``     ``EXTRACT_DIR``
``processed_SOH_path=``                 ``HF_DIR/processed_SOH``
``cache_root=``                         ``CKPT_ROOT/cache``
``CUDA_VISIBLE_DEVICES=2,3``            ``CUDA_DEVICES``
``--num_processes N``                   ``NUM_PROCESSES``
``--num_workers 32``                    ``NUM_WORKERS``
``num_process=2``                       ``NUM_PROCESSES``
``batch_size=32``                       ``BATCH_SIZE``
======================================= ==========================================

추가로 ``NUM_PROCESSES=1`` 이면 ``--multi_gpu`` 를 제거합니다.
**단일 GPU 에서 실패하는 원인입니다.**

같은 하드코딩이 파이썬 쪽에도 있습니다 — ``aging_conditions.py:340``,
``dataset_overview_calculation.py:76``, ``view_monotonicity_results.py:16,19``.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from verify import REPO_ROOT, load_config, read_text, write_text

__all__ = ["BUILD_DIR", "build", "build_all", "RULES"]

BUILD_DIR = REPO_ROOT / ".build"
UPSTREAM = REPO_ROOT / "upstream"


def _rules(config: dict) -> list:
    """(정규식, 치환문자열, 설명). 위에서부터 순서대로 적용합니다."""
    ckpt = config.get("CKPT_ROOT", "").rstrip("/")
    extract = config.get("EXTRACT_DIR", "").rstrip("/")
    hf = config.get("HF_DIR", "").rstrip("/")
    devices = config.get("CUDA_DEVICES", "0")
    processes = config.get("NUM_PROCESSES", "1")
    workers = config.get("NUM_WORKERS", "4")
    batch = config.get("BATCH_SIZE", "8")

    return [
        # --- 셸 스크립트의 변수 대입 (줄 앞) ---
        (re.compile(r"^(\s*checkpoints=)\S+", re.M), rf"\g<1>{ckpt}", "checkpoints"),
        (re.compile(r"^(\s*root_path=)\S+", re.M), rf"\g<1>{extract}", "root_path"),
        (re.compile(r"^(\s*processed_SOH_path=)\S+", re.M),
         rf"\g<1>{hf}/processed_SOH", "processed_SOH_path"),
        (re.compile(r"^(\s*cache_root=)\S+", re.M), rf"\g<1>{ckpt}/cache", "cache_root"),
        (re.compile(r"^(\s*num_process=)\S+", re.M), rf"\g<1>{processes}", "num_process"),
        (re.compile(r"^(\s*batch_size=)\S+", re.M), rf"\g<1>{batch}", "batch_size"),
        (re.compile(r"^(\s*gpu_ids=)\S+", re.M), rf"\g<1>{devices}", "gpu_ids"),

        # --- 명령줄 인자 ---
        (re.compile(r"CUDA_VISIBLE_DEVICES=[0-9,]+"),
         f"CUDA_VISIBLE_DEVICES={devices}", "CUDA_VISIBLE_DEVICES"),
        (re.compile(r"--num_processes\s+\S+"),
         f"--num_processes {processes}", "--num_processes"),
        (re.compile(r"--num_workers\s+\d+"),
         f"--num_workers {workers}", "--num_workers"),
        (re.compile(r"--batch_size\s+\d+"),
         f"--batch_size {batch}", "--batch_size"),

        # --- 파이썬 쪽 하드코딩 절대경로 ---
        (re.compile(r"/data/trf/python_works/BatteryLife/dataset"),
         extract, "aging_conditions/dataset_overview 절대경로"),
        (re.compile(r"/data/trf/python_project/BatteryLife/dev/Issue 22"),
         f"{ckpt}/issue22", "view_monotonicity 출력 경로"),
        (re.compile(r"/data/hwx/BL_new"), ckpt, "체크포인트 절대경로"),
    ]


RULES = _rules  # 규칙을 보고 싶을 때 train.paths.RULES(config) 로 부릅니다


def _apply(text: str, config: dict) -> tuple:
    changes = []
    for pattern, replacement, label in _rules(config):
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        for match in matches:
            before = match.group(0)
            after = pattern.sub(replacement, before, count=1)
            if before != after:
                line = text.count("\n", 0, match.start()) + 1
                changes.append({"line": line, "rule": label,
                                "before": before.strip(), "after": after.strip()})
        text = pattern.sub(replacement, text)

    # NUM_PROCESSES=1 이면 --multi_gpu 를 뺍니다. 단일 GPU 에서 accelerate 가
    # 여기서 죽습니다. 남겨두면 원인을 엉뚱한 데서 찾게 됩니다.
    if str(config.get("NUM_PROCESSES", "1")).strip() == "1" and "--multi_gpu" in text:
        for match in re.finditer(r"--multi_gpu\s*", text):
            changes.append({
                "line": text.count("\n", 0, match.start()) + 1,
                "rule": "--multi_gpu 제거 (NUM_PROCESSES=1)",
                "before": "--multi_gpu", "after": "",
            })
        text = re.sub(r"--multi_gpu\s*", "", text)

    return text, changes


def build(relative_path: str, config: dict | None = None,
          build_dir=BUILD_DIR) -> dict:
    """``upstream/<relative_path>`` 을 치환해 ``.build/<relative_path>`` 에 씁니다.

    Parameters
    ----------
    relative_path
        ``upstream/`` 아래의 상대 경로. 예: ``BatteryLife/train_eval_scripts/CPTransformer.sh``

    Returns
    -------
    dict
        ``path`` (만들어진 사본), ``source`` (원본), ``changes`` (치환 목록)

    원본은 **읽기만** 합니다. 이 함수가 ``upstream/`` 아래에 쓰는 일은
    없습니다 — 아래 assert 가 그것을 보증합니다.
    """
    config = config if config is not None else load_config()
    source = UPSTREAM / relative_path
    if not source.exists():
        raise FileNotFoundError(f"원본이 없습니다: {source}")

    destination = Path(build_dir) / relative_path
    assert UPSTREAM not in destination.resolve().parents, (
        f"upstream/ 아래에 쓰려 하고 있습니다: {destination}"
    )

    text, changes = _apply(read_text(source), config)
    write_text(destination, text)
    return {"path": destination, "source": source, "changes": changes}


def build_all(relative_dir: str, pattern: str = "*.sh",
              config: dict | None = None, build_dir=BUILD_DIR) -> list:
    """디렉터리 하나를 통째로 치환합니다.

    스크립트가 서로를 부르는 경우가 있어 한 파일만 옮기면 깨집니다.
    ``.sh`` 가 아닌 파일은 그대로 복사합니다.
    """
    config = config if config is not None else load_config()
    source_dir = UPSTREAM / relative_dir
    if not source_dir.exists():
        raise FileNotFoundError(f"원본 디렉터리가 없습니다: {source_dir}")

    results = []
    for source in sorted(source_dir.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(UPSTREAM).as_posix()
        if source.match(pattern):
            results.append(build(relative, config, build_dir))
        else:
            destination = Path(build_dir) / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return results


def format_changes(result: dict) -> str:
    """치환 목록을 사람이 읽는 형태로. 로그에 그대로 남기십시오."""
    lines = [f"{result['source'].name}: 치환 {len(result['changes'])}건"]
    for change in result["changes"]:
        lines.append(f"  {change['line']:>4}  [{change['rule']}]")
        lines.append(f"        - {change['before']}")
        lines.append(f"        + {change['after'] or '(삭제)'}")
    if not result["changes"]:
        lines.append("  (바꾼 것이 없습니다. 이미 상대경로일 수 있습니다)")
    return "\n".join(lines)
