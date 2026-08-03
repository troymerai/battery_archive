"""verify — 라벨·앵커·잠금 검증 하니스.

여기 있는 함수는 **얇게** 유지합니다. 로직이 함수 안에 숨으면 노트북이 다시
하네스가 되고, 조원은 자기 손으로 확인하지 않게 됩니다. 계산의 뼈대는
노트북에 남기고, 이 패키지는 반복되는 잡일(인코딩, 정규화, 해시)만 맡습니다.

원칙 세 가지:

1. 모든 파일 입출력에 ``encoding="utf-8"`` 을 명시합니다. 한국어 Windows 의
   Python 기본 인코딩은 cp949 이고, 이 저장소는 문서가 한국어이며 상위
   코드가 중국어 컬럼명(``循环序号``)을 읽습니다.
2. 경로는 ``pathlib`` 로만 다룹니다. 데이터 폴더 이름에 공백이 있습니다
   (``Life labels/``).
3. 해시 계산 전에 정규화합니다. ``\\r`` 제거 → UTF-8 → sha256.
   표 형태 결과는 렌더링된 마크다운이 아니라 **정규화된 JSON** 을 해싱합니다.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

__all__ = [
    "use_utf8_stdout",
    "REPO_ROOT",
    "UPSTREAM",
    "BATTERYLIFE",
    "BATTERYML",
    "BATTERYMFORMER",
    "FINDINGS",
    "MANIFESTS",
    "read_text",
    "write_text",
    "read_json",
    "write_json",
    "norm_text",
    "sha256_text",
    "sha256_bytes",
    "sha256_file",
    "md5_file",
    "json_digest",
    "tree_digest",
    "load_config",
    "load_yaml",
    "short",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = REPO_ROOT / "upstream"
BATTERYML = UPSTREAM / "BatteryML"
BATTERYLIFE = UPSTREAM / "BatteryLife"
BATTERYMFORMER = UPSTREAM / "BatteryMFormer"
FINDINGS = REPO_ROOT / "findings"
MANIFESTS = REPO_ROOT / "manifests"

# 트리 해시에서 제외할 것. 계산 결과가 기계마다 달라지는 것들.
_TREE_EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".ipynb_checkpoints",
    ".pytest_cache",
    ".mypy_cache",
}
_TREE_EXCLUDE_SUFFIX = {".pyc", ".pyo"}


# ---------------------------------------------------------------------------
# 표준 출력
# ---------------------------------------------------------------------------

def use_utf8_stdout() -> None:
    """stdout · stderr 를 UTF-8 로 고정합니다.

    한국어 Windows 콘솔의 기본 인코딩이 **cp949** 라, 이 저장소의 한국어
    출력에 섞인 문자 하나(``—`` 같은)로 ``UnicodeEncodeError`` 가 나며
    죽습니다. 파일 입출력만 챙겨서는 부족합니다.

    README 가 ``setx PYTHONIOENCODING utf-8`` 을 안내하지만, 그 설정에
    **기대지 않습니다.** 조원이 그 절을 건너뛰어도 도구는 돌아가야 합니다.
    """
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


# ---------------------------------------------------------------------------
# 파일 입출력 — encoding 을 하나도 빠뜨리지 않는다
# ---------------------------------------------------------------------------

def read_text(path) -> str:
    """UTF-8 로 읽습니다. 기본 인코딩(cp949)에 맡기지 않습니다."""
    return Path(path).read_text(encoding="utf-8")


def write_text(path, text: str) -> Path:
    """UTF-8 · LF 로 씁니다. Windows 에서도 CRLF 로 바뀌지 않게 newline="\\n"."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return p


def read_json(path):
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj, *, normalized: bool = False) -> Path:
    """JSON 을 씁니다.

    ``normalized=True`` 면 해시 대상과 **같은 바이트** 로 씁니다.
    LOCK 에 걸리는 산출물(recount.json 등)은 반드시 이쪽을 씁니다.
    """
    if normalized:
        text = _canonical_json(obj)
    else:
        text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return write_text(path, text)


# ---------------------------------------------------------------------------
# 정규화와 해시
# ---------------------------------------------------------------------------

def norm_text(text: str) -> str:
    r"""``\r`` 을 제거합니다. OS 간 줄바꿈 차이로 해시가 어긋나지 않게."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def sha256_text(text: str) -> str:
    """정규화 → UTF-8 → sha256."""
    return hashlib.sha256(norm_text(text).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    """텍스트면 정규화 후, 아니면 원본 바이트로 sha256."""
    raw = Path(path).read_bytes()
    try:
        return sha256_text(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return sha256_bytes(raw)


def md5_file(path, chunk: int = 1 << 20) -> str:
    """파일 md5. Zenodo 가 md5 로 공개하므로 데이터 대조는 md5 를 씁니다."""
    h = hashlib.md5()
    with open(Path(path), "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def json_digest(obj) -> str:
    """표 형태 결과의 해시.

    렌더링된 마크다운을 해싱하면 공백 하나로 어긋납니다. 정규화된 JSON 을
    해싱합니다.
    """
    return hashlib.sha256(_canonical_json(obj).encode("utf-8")).hexdigest()


def tree_digest(root) -> str:
    """디렉터리 전체의 sha256.

    상대 경로를 정렬해 순서를 고정하고, 파일마다 ``<posix경로>\\0<파일해시>\\n``
    을 이어붙여 해싱합니다. 경로는 POSIX 형식으로 통일해 Windows 의 ``\\`` 가
    섞이지 않게 합니다.
    """
    root = Path(root)
    if not root.exists():
        return "(없음)"

    entries = []
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in _TREE_EXCLUDE_DIRS for part in rel_parts[:-1]):
            continue
        if path.suffix in _TREE_EXCLUDE_SUFFIX:
            continue
        rel = path.relative_to(root).as_posix()
        entries.append(f"{rel}\0{sha256_file(path)}\n")

    return hashlib.sha256("".join(entries).encode("utf-8")).hexdigest()


def short(digest: str, n: int = 12) -> str:
    """해시를 표에 넣을 때만 줄입니다. 대조는 항상 전체 길이로 합니다."""
    if not digest or digest.startswith("("):
        return digest
    return digest[:n]


# ---------------------------------------------------------------------------
# config.env
# ---------------------------------------------------------------------------

def load_config(path=None) -> dict:
    """``config.env`` 를 읽습니다.

    없으면 ``config.env.example`` 을 읽고, 그것도 없으면 빈 dict 입니다.
    값에 따옴표를 붙이지 않습니다 — 경로에 공백이 있어도 줄 전체가 값입니다.
    환경변수가 있으면 파일 값을 덮어씁니다.
    """
    if path is None:
        path = REPO_ROOT / "config.env"
        if not path.exists():
            path = REPO_ROOT / "config.env.example"
    path = Path(path)

    cfg: dict = {}
    if path.exists():
        for line in read_text(path).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()

    for key in list(cfg):
        if os.environ.get(key):
            cfg[key] = os.environ[key]
    return cfg


# ---------------------------------------------------------------------------
# YAML
# ---------------------------------------------------------------------------

def load_yaml(path):
    """PyYAML 이 있으면 그것을, 없으면 내장 축소 파서를 씁니다.

    조원은 clone 만 합니다. 아무것도 설치하지 않은 상태에서도
    ``python run.py claims`` 가 돌아가야 합니다.
    """
    text = read_text(path)
    try:
        import yaml  # type: ignore
    except ImportError:
        from verify._minyaml import loads
        return loads(text)
    return yaml.safe_load(text)
