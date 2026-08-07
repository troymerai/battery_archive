"""LOCK.md 판정 — digest 와 interval.

``LOCK.md`` 의 표를 읽어 항목마다 다시 계산하고 기준값과 맞춰봅니다.

불일치가 나오면 **어느 층인지** 를 먼저 말합니다. 층을 모르면 원인을 찾을
수 없습니다.

======== ==========================================================
층        어긋났을 때의 뜻
======== ==========================================================
코드      상위 저장소나 verify/ 가 달라졌다
데이터    받은 zip 이 다르다. 판본(v11/v12) 확인
환경      패키지 버전이 다르다
결과      위 셋이 맞는데 결과가 다르다 → **비결정성 의심**
======== ==========================================================

``interval`` 항목은 하드웨어에 따라 다릅니다. 기준값 옆의 구간과 비교하고,
어느 기계에서 잰 것인지는 ``manifests/hardware.txt`` 를 보십시오.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from verify import (
    BATTERYLIFE, BATTERYML, BATTERYMFORMER, FINDINGS, MANIFESTS, REPO_ROOT,
    load_config, md5_file, read_json, read_text, sha256_file, sha256_text,
    json_digest, tree_digest, write_text,
)

__all__ = ["LOCK_PATH", "check", "init", "format_report", "LAYER_CODE",
           "LAYER_DATA", "LAYER_ENV", "LAYER_RESULT"]

LOCK_PATH = REPO_ROOT / "LOCK.md"

LAYER_CODE = "코드"
LAYER_DATA = "데이터"
LAYER_ENV = "환경"
LAYER_RESULT = "결과"

UNSET = "(미정)"

# 결과 산출물이 놓이는 곳. 노트북이 여기에 정규화 JSON 으로 씁니다.
RESULTS = REPO_ROOT / "experiments" / "results"

# 항목 이름 → (층, 계산 방법). 계산 방법이 None 이면 사람이 재는 값입니다.
_ITEMS = {
    "upstream/BatteryML tree": (LAYER_CODE, "tree", BATTERYML),
    "upstream/BatteryLife tree": (LAYER_CODE, "tree", BATTERYLIFE),
    "upstream/BatteryMFormer commit": (LAYER_CODE, "submodule", BATTERYMFORMER),
    "verify/ tree": (LAYER_CODE, "tree", REPO_ROOT / "verify"),
    "env repro": (LAYER_ENV, "envfile", MANIFESTS / "env_lock" / "repro.txt"),
    "env blife": (LAYER_ENV, "envfile", MANIFESTS / "env_lock" / "blife.txt"),
    "nb01 재집계 recount.json": (LAYER_RESULT, "json", FINDINGS / "recount.json"),
    "nb03 셀 단위 대조표": (LAYER_RESULT, "json", RESULTS / "nb03_cells.json"),
    "nb03 도메인 롤업 표": (LAYER_RESULT, "json", RESULTS / "nb03_rollup.json"),
    "nb03 불일치 셀 목록": (LAYER_RESULT, "json", RESULTS / "nb03_mismatch.json"),
    "nb03 라벨없음(비유한) 셀 목록": (LAYER_RESULT, "json", RESULTS / "nb03_nolabel.json"),
    # v11 전수(1,382셀) 확장에서 늘어난 산출물. 계산 방법은 위와 같은 "json"
    # 입니다 — 정규화 JSON 을 읽어 sha256 을 냅니다. 판정 규칙은 건드리지
    # 않았고, **어느 파일을 볼지** 만 늘렸습니다.
    #
    # 이름은 LOCK.md 표의 항목 이름과 **글자 그대로 같아야 합니다.** 여기가
    # 이름 → 경로 대응표이고, 표에 있는데 여기 없는 이름은 compute() 가
    # "(모르는 항목)" 을 돌려주어 lock-init 이 채우지 못하고 (미정) 으로
    # 남습니다.
    "nb02 변형 비교": (LAYER_RESULT, "json", RESULTS / "nb02_variants.json"),
    "nb03 no_soc_span 변형": (LAYER_RESULT, "json", RESULTS / "nb03_cells_nospan.json"),
    "nb03 discharge_denom 변형": (LAYER_RESULT, "json",
                                RESULTS / "nb03_cells_discharge_denom.json"),
    "nb04 cycle_number 롤업": (LAYER_RESULT, "json", RESULTS / "nb04_cycle_numbers.json"),
    "nb04 셀별 추가 측정": (LAYER_RESULT, "json", RESULTS / "nb04_extras.json"),
    "nb05 v2 대조표 원자료": (LAYER_RESULT, "json", RESULTS / "nb05_v2_compare.json"),
    "findings/na_ion_crate.json": (LAYER_RESULT, "json", FINDINGS / "na_ion_crate.json"),
    "findings/registry.yaml": (LAYER_CODE, "file", FINDINGS / "registry.yaml"),
    "findings/anchors.yaml": (LAYER_CODE, "file", FINDINGS / "anchors.yaml"),
}

_ROW = re.compile(r"^\|(?P<item>[^|]+)\|(?P<kind>[^|]+)\|(?P<expected>[^|]*)\|(?P<note>[^|]*)\|\s*$")


# ---------------------------------------------------------------------------
# LOCK.md 읽기
# ---------------------------------------------------------------------------

def parse(lock_path=LOCK_PATH) -> list:
    """표에서 항목 행만 뽑습니다. 표 밖의 글은 건드리지 않습니다."""
    rows = []
    for number, line in enumerate(read_text(lock_path).splitlines(), 1):
        match = _ROW.match(line.strip())
        if not match:
            continue
        item = match.group("item").strip()
        kind = match.group("kind").strip()
        if kind not in ("digest", "interval") or item in ("항목", ""):
            continue
        rows.append({
            "line": number,
            "item": item,
            "kind": kind,
            "expected": match.group("expected").strip(),
            "note": match.group("note").strip(),
        })
    return rows


# ---------------------------------------------------------------------------
# 다시 계산
# ---------------------------------------------------------------------------

def _submodule_head(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "(대상없음)"


def _pip_freeze_digest(path: Path) -> str:
    """저장된 pip freeze 파일의 해시.

    파일이 없거나 **패키지 줄이 하나도 없으면** 대상없음입니다.
    빈 목록도 해시는 나옵니다. 그 해시를 기준값으로 박으면 "아무것도 설치되지
    않은 환경" 이 정상 환경인 것처럼 잠깁니다. 빈 것은 빈 것으로 둡니다.
    """
    if not path.exists():
        return "(대상없음)"
    lines = sorted(
        line.strip() for line in read_text(path).splitlines()
        if line.strip() and not line.startswith("#")
    )
    if not lines:
        return "(대상없음)"
    return sha256_text("\n".join(lines))


def current_pip_freeze() -> str:
    """지금 인터프리터의 pip freeze. 빈 결과면 빈 문자열입니다.

    pip 이 없는 인터프리터(일부 배포판)에서는 아무것도 나오지 않습니다.
    그 경우 파일을 만들지 않습니다 — 빈 파일이 있으면 "쟀는데 비어 있다" 로
    읽히고, 그것은 사실이 아닙니다.
    """
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True, text=True, encoding="utf-8", timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    lines = sorted(line.strip() for line in out.stdout.splitlines() if line.strip())
    return "\n".join(lines) + "\n" if lines else ""


def _zip_md5(item: str, config: dict) -> str:
    """``<이름>.zip`` 행. ZENODO_DIR 아래에서 찾습니다."""
    root = config.get("ZENODO_DIR") or config.get("DATA_ROOT") or ""
    if not root:
        return "(대상없음)"
    candidate = Path(root) / item
    if not candidate.exists():
        return "(대상없음)"
    return md5_file(candidate)


def compute(item: str, config: dict | None = None) -> tuple:
    """(층, 실제값). 계산할 수 없으면 실제값이 ``(대상없음)`` 입니다."""
    config = config if config is not None else load_config()

    if item.endswith(".zip"):
        return LAYER_DATA, _zip_md5(item, config)

    spec = _ITEMS.get(item)
    if spec is None:
        return LAYER_RESULT, "(모르는 항목)"

    layer, how, target = spec
    if how == "tree":
        return layer, tree_digest(target)
    if how == "submodule":
        if not target.exists() or not any(target.iterdir()):
            return layer, "(대상없음)"
        return layer, _submodule_head(target)
    if how == "envfile":
        return layer, _pip_freeze_digest(target)
    if how == "file":
        return layer, sha256_file(target) if target.exists() else "(대상없음)"
    if how == "json":
        if not target.exists():
            return layer, "(대상없음)"
        return layer, json_digest(read_json(target))
    return layer, "(대상없음)"


def stale(items, lock_path=LOCK_PATH, config: dict | None = None) -> list:
    """지정한 항목만 재어 **LOCK 기준값이 낡았는지** 봅니다.

    ``check()`` 는 전 항목을 재는데 데이터 층에서 zip 20개(29 GB)를 md5 하므로
    분 단위가 걸립니다. 자주 바뀌는 파일 한둘을 확인하려고 그것을 부를 수는
    없어서, 필요한 항목만 재는 얇은 함수를 따로 둡니다.

    **고치지 않습니다. 알리기만 합니다.** 기준값을 자동으로 덮어쓰면
    ``init()`` 이 값 있는 행을 건드리지 않는 설계가 무의미해집니다 — 그 설계의
    이유는 ``init()`` 의 docstring 에 있습니다.

    돌려주는 것은 어긋난 항목의 ``{item, expected, actual}`` 목록입니다.
    LOCK 표에 없는 이름과 계산되지 않는 항목(``(...)``)은 건너뜁니다.
    """
    config = config if config is not None else load_config()
    wanted = set(items)
    result = []
    for row in parse(lock_path):
        if row["item"] not in wanted or row["kind"] != "digest":
            continue
        _, actual = compute(row["item"], config)
        if actual.startswith("(") or row["expected"] == UNSET:
            continue
        if actual != row["expected"]:
            result.append({
                "item": row["item"],
                "expected": row["expected"],
                "actual": actual,
                "line": row["line"],
            })
    return result


# ---------------------------------------------------------------------------
# 판정
# ---------------------------------------------------------------------------

def check(lock_path=LOCK_PATH, config: dict | None = None) -> dict:
    """전 항목을 대조합니다."""
    config = config if config is not None else load_config()
    rows = []
    for row in parse(lock_path):
        row = dict(row)
        layer, actual = compute(row["item"], config)
        row["layer"] = layer
        row["actual"] = actual

        if row["kind"] == "interval":
            row["verdict"] = "구간(사람 판정)" if row["expected"] != UNSET else "미정"
        elif row["expected"] == UNSET:
            row["verdict"] = "미정"
        elif actual.startswith("("):
            row["verdict"] = "대상없음"
        elif actual == row["expected"]:
            row["verdict"] = "일치"
        else:
            row["verdict"] = "불일치"
        rows.append(row)

    broken = {row["layer"] for row in rows if row["verdict"] == "불일치"}
    diagnosis = _diagnose(broken, rows)
    return {"rows": rows, "broken_layers": sorted(broken), "diagnosis": diagnosis}


def _diagnose(broken: set, rows: list) -> str:
    if not broken:
        checked = sum(1 for row in rows if row["verdict"] == "일치")
        undecided = sum(1 for row in rows if row["verdict"] == "미정")
        missing = sum(1 for row in rows if row["verdict"] == "대상없음")
        parts = [f"불일치 없음 (일치 {checked})"]
        if undecided:
            parts.append(f"미정 {undecided} — `python run.py lock-init` 으로 채웁니다")
        if missing:
            parts.append(f"대상없음 {missing} — 데이터나 산출물이 아직 없습니다")
        return ". ".join(parts)

    lines = [f"어긋난 층: {', '.join(sorted(broken))}"]
    if broken == {LAYER_RESULT}:
        lines.append(
            "코드 · 데이터 · 환경은 맞는데 결과만 다릅니다. "
            "비결정성 의심 — 시드 · 정렬 · 부동소수점 누적 순서를 확인하십시오."
        )
        lines.append(
            "이것 자체가 보고할 만한 발견입니다. 이 출력을 그대로 붙여 공유하십시오."
        )
    else:
        hint = {
            LAYER_CODE: "상위 저장소나 verify/ 가 달라졌습니다. 커밋을 확인하십시오 "
                        "(manifests/upstream_commits.txt).",
            LAYER_DATA: "받은 zip 이 다릅니다. 판본(v11/v12)을 확인하십시오 "
                        "(manifests/data_md5.txt).",
            LAYER_ENV: "패키지 버전이 다릅니다. manifests/env_lock/ 을 확인하십시오.",
            LAYER_RESULT: "결과 산출물이 다릅니다. 위 층부터 먼저 맞추십시오.",
        }
        for layer in sorted(broken):
            lines.append(f"- {layer}: {hint[layer]}")
        if LAYER_RESULT in broken and len(broken) > 1:
            lines.append(
                "위층이 어긋난 상태에서 결과가 다른 것은 당연합니다. "
                "위층부터 맞춘 뒤 다시 보십시오."
            )
    return "\n".join(lines)


def format_report(result: dict) -> str:
    rows = result["rows"]
    if not rows:
        return "LOCK.md 에 항목이 없습니다."

    mark = {"일치": "  ok  ", "불일치": " FAIL ", "미정": " 미정 ",
            "대상없음": " skip ", "구간(사람 판정)": " 구간 "}
    width = max(len(row["item"]) for row in rows)
    lines = []
    for row in rows:
        label = mark.get(row["verdict"], "  ??  ")
        lines.append(
            f"[{label}] {row['item'].ljust(width)}  {row['layer']}/{row['kind']}"
        )
        if row["verdict"] == "불일치":
            lines.append(f"{' ' * (width + 11)}기준 {row['expected']}")
            lines.append(f"{' ' * (width + 11)}실제 {row['actual']}")
        elif row["verdict"] == "구간(사람 판정)":
            lines.append(f"{' ' * (width + 11)}기준 {row['expected']}  ({row['note']})")

    lines.append("")
    lines.append(result["diagnosis"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# lock-init
# ---------------------------------------------------------------------------

def init(lock_path=LOCK_PATH, config: dict | None = None, *,
         stamp: str = "", author: str = "") -> dict:
    """``(미정)`` 을 지금 계산되는 값으로 채웁니다.

    이미 값이 들어 있는 행은 **건드리지 않습니다.** 기준값을 덮어쓰면
    "모두가 같은 것을 본다" 가 무너집니다. 값을 바꿔야 한다면 새 태그를
    찍으십시오.

    계산되지 않는 항목(데이터 미다운로드, 노트북 미실행)은 ``(미정)`` 인 채로
    남습니다. 그 상태로 태그를 찍지 마십시오.
    """
    config = config if config is not None else load_config()

    env_path = MANIFESTS / "env_lock" / "repro.txt"
    freeze = current_pip_freeze()
    if freeze:
        write_text(env_path, freeze)
    else:
        env_path = None  # pip 이 없거나 빈 결과. 파일을 만들지 않습니다.

    filled, skipped = [], []
    out_lines = []
    for line in read_text(lock_path).splitlines():
        match = _ROW.match(line.strip())
        if not match or match.group("kind").strip() not in ("digest", "interval"):
            out_lines.append(line)
            continue

        item = match.group("item").strip()
        expected = match.group("expected").strip()
        if expected != UNSET:
            out_lines.append(line)
            continue
        if match.group("kind").strip() == "interval":
            skipped.append((item, "interval 은 사람이 잽니다"))
            out_lines.append(line)
            continue

        _, actual = compute(item, config)
        if actual.startswith("("):
            skipped.append((item, actual))
            out_lines.append(line)
            continue

        out_lines.append(line.replace(UNSET, actual, 1))
        filled.append((item, actual))

    text = "\n".join(out_lines) + "\n"
    if stamp:
        text = text.replace("생성: (미정)", f"생성: {stamp}", 1)
    if author:
        text = text.replace("생성자: (미정)", f"생성자: {author}", 1)
    write_text(lock_path, text)

    return {
        "filled": filled,
        "skipped": skipped,
        "env_lock": env_path or "(pip freeze 가 비어 기록하지 않았습니다)",
    }
