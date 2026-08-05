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

__all__ = ["BUILD_DIR", "build", "build_all", "build_variant", "absolutize",
           "RULES"]

BUILD_DIR = REPO_ROOT / ".build"
UPSTREAM = REPO_ROOT / "upstream"

# config.env 의 경로는 ``./data/...`` 처럼 상대입니다. 스크립트는 cwd 가
# ``upstream/BatteryLife`` 인 채로 실행되므로 상대경로를 그대로 넘기면
# 엉뚱한 곳을 봅니다. 반드시 절대 posix 경로로 바꿔서 넣습니다.
_PATH_KEYS = ("DATA_ROOT", "ZENODO_DIR", "EXTRACT_DIR", "HF_DIR", "CKPT_ROOT")


def absolutize(config: dict) -> dict:
    """경로 값들을 저장소 루트 기준 절대 posix 경로로 바꾼 사본을 돌려줍니다.

    Windows 라도 백슬래시를 쓰지 않습니다. 생성물이 bash 스크립트라
    ``D:\\...`` 의 백슬래시는 이스케이프로 먹힙니다.
    """
    out = dict(config)
    for key in _PATH_KEYS:
        value = out.get(key, "").strip()
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = REPO_ROOT / path
        out[key] = path.resolve().as_posix()
    return out


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


def _variant_rules(dataset, model, epochs, port, workers, hparams=None) -> list:
    """모델·데이터셋만 갈아끼웁니다. **학습 하이퍼파라미터는 건드리지 않습니다.**

    원본 스크립트는 모델마다 다르게 튜닝되어 있습니다. 학습률·층수·d_model 을
    임의로 맞추면 비교가 오염됩니다. 여기서 바꾸는 것은 넷뿐입니다.

    ``dataset``  비교 대상을 같은 데이터로 맞추기 위해 (§4-2)
    ``model``    ``model_name`` · ``--model_id`` · ``comment`` 를 한꺼번에
    ``epochs``   스모크 사본에서만 1 로
    ``port``     동시에 돌릴 때 accelerate 포트가 겹치지 않게
    """
    rules = []
    if dataset:
        # ``dataset=MIX_large # MIX_large`` — 뒤의 주석까지 지웁니다. 값만
        # 갈아끼우면 ``dataset=CALB # MIX_large`` 가 되어 읽는 사람을 속입니다.
        rules.append((re.compile(r"^(\s*dataset=)\S+[^\S\n]*(?:#[^\n]*)?", re.M),
                      rf"\g<1>{dataset}", "dataset"))
    if model:
        rules += [
            (re.compile(r"^(\s*model_name=)\S+", re.M), rf"\g<1>{model}", "model_name"),
            (re.compile(r"^(\s*comment=)'[^']*'", re.M), rf"\g<1>'{model}'", "comment"),
            (re.compile(r"--model_id\s+\S+"), f"--model_id {model}", "--model_id"),
        ]
    if epochs:
        rules.append((re.compile(r"^(\s*train_epochs=)\S+", re.M),
                      rf"\g<1>{epochs}", "train_epochs"))
    if port:
        rules.append((re.compile(r"^(\s*master_port=)\S+", re.M),
                      rf"\g<1>{port}", "master_port"))
    if workers is not None:
        # paths.py 의 기본 규칙은 ``--num_workers\s+\d+`` 를 잡습니다. 원본이
        # 8 · 32 로 리터럴이라 이미 걸리지만, 여기서 한 번 더 못박습니다.
        rules.append((re.compile(r"--num_workers\s+\S+"),
                      f"--num_workers {workers}", "--num_workers"))
    # ``hparams`` 는 **논문 문서**(assets/Selected_hyperparameters.md)가 지정한
    # 값을 셸 변수 대입에 덮어씁니다. 문서가 지정하지 않은 항목은 여기 들어오지
    # 않으므로 원본 셸 값이 그대로 남습니다 — 그것이 의도입니다.
    for key, value in (hparams or {}).items():
        rules.append((re.compile(rf"^(\s*{re.escape(key)}=)\S+", re.M),
                      rf"\g<1>{value}", f"{key} (문서값)"))
    return rules


# 상위 코드는 wandb.init 을 무조건 부릅니다 (run_main.py:224). 로그인하지
# 않은 기계에서는 여기서 멈춥니다. 지표는 stdout 에도 찍히고 collect.py 가
# 그것을 읽으므로 wandb 는 꺼도 됩니다.
_PREAMBLE = """\
# --- 이 파일은 생성물입니다. 고치려면 train/make_scripts.py 를 고치십시오. ---
# 원본: upstream/{source}
# {note}
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export PYTHONDONTWRITEBYTECODE=1   # upstream/ 에 __pycache__ 를 남기지 않습니다
export WANDB_MODE=disabled         # run_main.py:224 이 wandb.init 을 무조건 부릅니다
export OMP_NUM_THREADS=4

"""


def build_variant(relative_path: str, destination, *, dataset: str = "",
                  model: str = "", epochs: str = "", port: str = "",
                  note: str = "", config: dict | None = None,
                  hparams: dict | None = None,
                  header: str = "") -> dict:
    """``upstream/<relative_path>`` 을 치환 + 변형해 ``destination`` 에 씁니다.

    ``build()`` 와 달리 출력 경로를 직접 받습니다. 같은 원본에서 데이터셋만
    다른 사본을 여러 벌 만들어야 하기 때문입니다.
    """
    config = absolutize(config if config is not None else load_config())
    source = UPSTREAM / relative_path
    if not source.exists():
        raise FileNotFoundError(f"원본이 없습니다: {source}")

    destination = Path(destination)
    assert UPSTREAM not in destination.resolve().parents, (
        f"upstream/ 아래에 쓰려 하고 있습니다: {destination}"
    )

    text, changes = _apply(read_text(source), config)

    for pattern, replacement, label in _variant_rules(
            dataset, model, epochs, port, config.get("NUM_WORKERS"), hparams):
        for match in pattern.finditer(text):
            before = match.group(0)
            after = pattern.sub(replacement, before, count=1)
            if before != after:
                changes.append({"line": text.count("\n", 0, match.start()) + 1,
                                "rule": label, "before": before.strip(),
                                "after": after.strip()})
        text = pattern.sub(replacement, text)

    text = _PREAMBLE.format(source=relative_path, note=note or "(변형 없음)") + text
    if header:
        # 근거 표시는 파일을 여는 사람이 첫 화면에서 봐야 합니다. preamble 의
        # export 줄 앞에 끼워 넣습니다.
        text = text.replace("export PYTHONUTF8=1",
                            header.rstrip() + "\n\nexport PYTHONUTF8=1", 1)
    write_text(destination, text)
    return {"path": destination, "source": source, "changes": changes}


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
