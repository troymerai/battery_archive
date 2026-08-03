"""코드 앵커 재검증.

``findings/anchors.yaml`` 에 등록한 위치가 아직 유효한지 확인합니다.

**행 번호는 상위 갱신 시 썩습니다.** 그래서 행 번호로 찾지 않고
``findings/snippets/<id>.txt`` 의 원문으로 재탐색합니다. 행 번호는 결과일 뿐
기준이 아닙니다.

판정 넷:

======== ==================================================================
유효      원문이 그대로 있고 행 번호도 같다
행이동    원문은 그대로인데 행 번호가 달라졌다 — anchors.yaml 의 line 을 고친다
내용변경  원문이 사라졌으나 비슷한 줄이 있다 — 상위가 그 부분을 고쳤다
소실      비슷한 줄조차 없다 — 앵커가 가리키던 것이 없어졌다
======== ==================================================================

`행이동` 은 문제가 아닙니다. `내용변경` 과 `소실` 은 **그 앵커에 걸린
findings 레코드를 다시 봐야 한다는 뜻** 입니다. 근거가 움직였는데 판정이
그대로면 그 판정은 더 이상 근거가 없습니다.
"""

from __future__ import annotations

from pathlib import Path

from verify import FINDINGS, REPO_ROOT, load_yaml, norm_text, read_text, sha256_text

__all__ = ["ANCHORS_PATH", "SNIPPET_DIR", "check", "format_report"]

ANCHORS_PATH = FINDINGS / "anchors.yaml"
SNIPPET_DIR = FINDINGS / "snippets"

STATUS_OK = "유효"
STATUS_MOVED = "행이동"
STATUS_CHANGED = "내용변경"
STATUS_LOST = "소실"

_REPO_DIRS = {
    "BatteryML": REPO_ROOT / "upstream" / "BatteryML",
    "BatteryLife": REPO_ROOT / "upstream" / "BatteryLife",
    "BatteryMFormer": REPO_ROOT / "upstream" / "BatteryMFormer",
}


def _find_line(haystack: str, needle: str) -> int | None:
    """``needle`` 이 시작하는 1-기준 행 번호. 없으면 None."""
    position = haystack.find(needle)
    if position < 0:
        return None
    return haystack.count("\n", 0, position) + 1


def _first_code_line(snippet: str) -> str:
    for line in snippet.splitlines():
        if line.strip():
            return line.strip()
    return ""


def check(anchors_path=ANCHORS_PATH) -> list:
    """앵커를 하나씩 재탐색합니다. 결과 행의 목록을 돌려줍니다."""
    document = load_yaml(anchors_path) or {}
    anchors = document.get("anchors") or []

    rows = []
    for anchor in anchors:
        anchor_id = anchor.get("id", "(id 없음)")
        row = {
            "id": anchor_id,
            "repo": anchor.get("repo", ""),
            "path": anchor.get("path", ""),
            "line_recorded": anchor.get("line"),
            "line_found": None,
            "status": STATUS_LOST,
            "detail": "",
        }

        repo_dir = _REPO_DIRS.get(row["repo"])
        if repo_dir is None:
            row["detail"] = f"모르는 저장소: {row['repo']!r}"
            rows.append(row)
            continue

        target = repo_dir / str(row["path"])
        if not target.exists():
            row["detail"] = f"파일이 없습니다: {target.relative_to(REPO_ROOT).as_posix()}"
            if row["repo"] == "BatteryMFormer" and not any(repo_dir.iterdir() if repo_dir.exists() else []):
                row["detail"] += "  (submodule 미초기화? `git submodule update --init`)"
            rows.append(row)
            continue

        snippet_file = SNIPPET_DIR / (anchor.get("snippet_file") or f"{anchor_id}.txt")
        if not snippet_file.exists():
            row["detail"] = f"스니펫이 없습니다: {snippet_file.name}"
            rows.append(row)
            continue

        snippet = norm_text(read_text(snippet_file))
        recorded_sha = anchor.get("sha256") or ""
        actual_sha = sha256_text(snippet)
        if recorded_sha and recorded_sha != actual_sha:
            row["detail"] = (
                "스니펫 파일이 등록된 sha256 과 다릅니다. "
                "누군가 스니펫을 고쳤습니다 — 상위가 아니라 이쪽 문제입니다. "
                f"등록 {recorded_sha[:12]} / 실제 {actual_sha[:12]}"
            )
            rows.append(row)
            continue

        source = norm_text(read_text(target))
        found = _find_line(source, snippet.rstrip("\n"))
        if found is not None:
            row["line_found"] = found
            if row["line_recorded"] in (None, found):
                row["status"] = STATUS_OK
            else:
                row["status"] = STATUS_MOVED
                row["detail"] = (
                    f"{row['line_recorded']}행 → {found}행. "
                    "anchors.yaml 의 line 을 고치십시오. 판정은 그대로입니다."
                )
            rows.append(row)
            continue

        needle = _first_code_line(snippet)
        candidates = [
            index + 1
            for index, line in enumerate(source.splitlines())
            if needle and needle in line
        ]
        if candidates:
            row["status"] = STATUS_CHANGED
            row["line_found"] = candidates[0]
            row["detail"] = (
                f"원문이 그대로는 없습니다. 첫 줄과 비슷한 곳: {candidates}행. "
                "이 앵커에 걸린 findings 레코드를 다시 보십시오."
            )
        else:
            row["status"] = STATUS_LOST
            row["detail"] = (
                "비슷한 줄조차 없습니다. 상위가 이 부분을 들어냈을 수 있습니다. "
                "이 앵커에 걸린 findings 레코드를 다시 보십시오."
            )
        rows.append(row)

    return rows


def format_report(rows: list) -> str:
    """사람이 읽는 표."""
    if not rows:
        return "등록된 앵커가 없습니다."

    lines = []
    width = max(len(str(row["id"])) for row in rows)
    for row in rows:
        mark = {
            STATUS_OK: "  ok  ",
            STATUS_MOVED: " move ",
            STATUS_CHANGED: "CHANGE",
            STATUS_LOST: " LOST ",
        }.get(row["status"], "  ??  ")
        where = f"{row['path']}:{row['line_found'] or row['line_recorded'] or '?'}"
        lines.append(f"[{mark}] {str(row['id']).ljust(width)}  {where}")
        if row["detail"]:
            lines.append(f"{' ' * (width + 11)}{row['detail']}")

    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    summary = " / ".join(f"{key} {value}" for key, value in sorted(counts.items()))
    lines.append("")
    lines.append(f"앵커 {len(rows)}개 — {summary}")
    if counts.get(STATUS_CHANGED) or counts.get(STATUS_LOST):
        lines.append(
            "내용변경·소실이 있습니다. findings/registry.yaml 에서 이 앵커를 "
            "인용한 레코드의 code 슬롯을 다시 확인하십시오."
        )
    return "\n".join(lines)
