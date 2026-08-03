"""registry.yaml → findings/PAPER_CODE_MAP.md · docs/OPEN_QUESTIONS.md.

``verdict`` 는 **사람이 쓰지 않습니다.** 슬롯에서 유도합니다. 사람이 쓰면
슬롯과 결론이 어긋나도 아무도 모릅니다. 여기서 유도하면 슬롯을 고치는 것
말고는 결론을 바꿀 방법이 없습니다.

유도 규칙 (``findings/SCHEMA.md`` 와 같습니다):

=================== =============== ==========================================
paper 슬롯           code 슬롯        판정
=================== =============== ==========================================
미조사               확인             **미정** — "코드 전용" 이라 말할 수 없음
부재확인             확인             코드 전용
조사했으나불명       확인             **근거불명** — 값은 있으나 출처를 못 댐
확인                 확인 · 값 같음    일치
확인                 확인 · 값 다름    불일치
확인                 부재확인          논문 전용 (미구현)
아무거나             구조적불가        **확인불가** — 종결 상태
=================== =============== ==========================================

``확인불가`` 는 실패가 아니라 **종결된 판정** 입니다. 미해결 목록에 쌓아두지
않고 별도 절에 둡니다. 외부 자료 미배포처럼 확인 경로 자체가 없는 항목을
계속 미해결로 두면, 언젠가 누군가 그럴듯한 설명을 지어 붙이게 됩니다.
"""

from __future__ import annotations

from pathlib import Path

from verify import FINDINGS, REPO_ROOT, load_yaml, write_text

__all__ = [
    "REGISTRY_PATH", "MAP_PATH", "OPEN_PATH",
    "STATUSES", "SLOTS", "derive_verdict", "validate", "render_all",
]

REGISTRY_PATH = FINDINGS / "registry.yaml"
MAP_PATH = FINDINGS / "PAPER_CODE_MAP.md"
OPEN_PATH = REPO_ROOT / "docs" / "OPEN_QUESTIONS.md"

UNSEARCHED = "미조사"
FOUND = "확인"
ABSENT = "부재확인"
UNCLEAR = "조사했으나불명"
IMPOSSIBLE = "구조적불가"

STATUSES = (UNSEARCHED, FOUND, ABSENT, UNCLEAR, IMPOSSIBLE)
SLOTS = ("paper", "upstream_doc", "code")

V_UNDECIDED = "미정"
V_CODE_ONLY = "코드전용"
V_NO_BASIS = "근거불명"
V_MATCH = "일치"
V_MISMATCH = "불일치"
V_PAPER_ONLY = "논문전용(미구현)"
V_UNVERIFIABLE = "확인불가"

# 미해결로 남는 판정. 확인불가는 여기 들어가지 않습니다 — 종결이므로.
OPEN_VERDICTS = (V_UNDECIDED, V_NO_BASIS, V_MISMATCH, V_PAPER_ONLY)


def _slot(record: dict, name: str) -> dict:
    slot = record.get(name) or {}
    return slot if isinstance(slot, dict) else {}


def _status(record: dict, name: str) -> str:
    return (_slot(record, name).get("status") or UNSEARCHED).strip()


def _value(record: dict, name: str):
    """빈 문자열은 값이 없는 것으로 봅니다.

    ``확인`` 이면서 ``value`` 가 비어 있는 상태가 실제로 있습니다 — 논문에
    서술이 있다는 것까지는 확인했으나 값이나 위치를 확정하지 못한 경우입니다.
    그것을 값이 같다/다르다로 판정하면 안 됩니다. **판정 보류** 여야 합니다.
    """
    value = _slot(record, name).get("value")
    if value is None:
        return None
    return value if str(value).strip() else None


def derive_verdict(record: dict) -> tuple:
    """(판정, 사유) 를 돌려줍니다. paper × code 로만 유도합니다.

    ``upstream_doc`` 은 보조 근거입니다. 상위 저장소 README 는 논문도 코드도
    아니어서, 여기 있는 서술이 논문 근거를 대신할 수 없습니다. 표에는 보이되
    판정에는 넣지 않습니다.
    """
    paper = _status(record, "paper")
    code = _status(record, "code")

    if IMPOSSIBLE in (paper, code):
        which = "code" if code == IMPOSSIBLE else "paper"
        return V_UNVERIFIABLE, f"{which} 슬롯이 구조적불가 — 확인 경로 자체가 없음"

    if code == FOUND:
        if paper == UNSEARCHED:
            return V_UNDECIDED, "논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다"
        if paper == ABSENT:
            return V_CODE_ONLY, "논문에서 찾아봤고 없었습니다"
        if paper == UNCLEAR:
            return V_NO_BASIS, "찾아봤으나 근거를 못 댔습니다. 값은 코드에 있습니다"
        if paper == FOUND:
            paper_value, code_value = _value(record, "paper"), _value(record, "code")
            if paper_value is None or code_value is None:
                return V_UNDECIDED, "양쪽 확인이나 value 가 비어 비교할 수 없습니다"
            if str(paper_value).strip() == str(code_value).strip():
                return V_MATCH, "양쪽 값이 같습니다"
            return V_MISMATCH, f"논문 {paper_value!r} 대 코드 {code_value!r}"

    if code == ABSENT:
        if paper == FOUND:
            return V_PAPER_ONLY, "논문에 있으나 코드에서 찾아봤고 없었습니다"
        if paper == ABSENT:
            return V_UNDECIDED, "양쪽 다 없습니다. 레코드 자체가 필요한지 다시 보십시오"

    if code == UNCLEAR:
        return V_NO_BASIS, "코드에서 찾아봤으나 근거를 못 댔습니다"

    return V_UNDECIDED, "code 슬롯이 미조사입니다"


def validate(record: dict) -> list:
    """기록 요건 위반을 찾습니다. 판정보다 이쪽이 먼저입니다."""
    problems = []
    record_id = record.get("id", "(id 없음)")

    if not record.get("question"):
        problems.append(f"{record_id}: question 이 비었습니다")

    if "verdict" in record:
        problems.append(
            f"{record_id}: verdict 를 손으로 적었습니다. 지우십시오 — render.py 가 유도합니다"
        )

    for name in SLOTS:
        if name not in record:
            problems.append(f"{record_id}: {name} 슬롯이 없습니다")
            continue
        slot = _slot(record, name)
        status = (slot.get("status") or "").strip()
        if status not in STATUSES:
            problems.append(f"{record_id}.{name}: 모르는 status {status!r}")
            continue
        if status == FOUND and not slot.get("locus"):
            problems.append(f"{record_id}.{name}: 확인인데 locus 가 없습니다 (§·쪽·파일:행)")
        if status in (ABSENT, UNCLEAR) and not slot.get("searched"):
            problems.append(
                f"{record_id}.{name}: {status} 인데 searched 가 없습니다 — 어디를 봤는지 적으십시오"
            )
        if status == IMPOSSIBLE and not (slot.get("note") or slot.get("searched")):
            problems.append(f"{record_id}.{name}: 구조적불가인데 왜 불가한지가 없습니다")
    return problems


def _cell(text) -> str:
    """표 칸. 파이프와 줄바꿈을 죽입니다."""
    if text is None:
        return "—"
    if isinstance(text, (list, tuple)):
        text = "; ".join(str(item) for item in text)
    return str(text).replace("|", "\\|").replace("\n", " ").strip() or "—"


def _slot_cell(record: dict, name: str) -> str:
    slot = _slot(record, name)
    status = _status(record, name)
    locus = slot.get("locus")
    if status == FOUND and locus:
        return f"{status} · `{_cell(locus)}`"
    return status


def render_map(document: dict) -> str:
    records = sorted(document.get("records") or [], key=lambda r: str(r.get("id", "")))

    lines = [
        "<!-- 자동 생성물입니다. 손으로 고치지 마십시오. -->",
        "<!-- 원본은 findings/registry.yaml 이고, 이 파일은 -->",
        "<!--   python run.py claims -->",
        "<!-- 로 다시 만들어집니다. 여기서 고친 것은 다음 실행에 지워집니다. -->",
        "",
        "# PAPER ↔ CODE MAP",
        "",
        f"레코드 {len(records)}개. `findings/registry.yaml` 에서 생성했습니다.",
        "",
        "판정은 슬롯에서 유도한 것입니다. 판정을 바꾸려면 슬롯을 고치십시오.",
        "유도 규칙은 `findings/SCHEMA.md` 에 있습니다.",
        "",
    ]

    counts = {}
    rows = []
    for record in records:
        verdict, reason = derive_verdict(record)
        counts[verdict] = counts.get(verdict, 0) + 1
        rows.append((record, verdict, reason))

    lines.append("## 판정 분포")
    lines.append("")
    lines.append("| 판정 | 개수 | 뜻 |")
    lines.append("|---|---|---|")
    meanings = {
        V_MATCH: "논문과 코드가 같다",
        V_MISMATCH: "논문과 코드가 다르다 — 발견",
        V_CODE_ONLY: "논문에서 찾아봤고 없었다",
        V_PAPER_ONLY: "논문에 있으나 코드에 없다",
        V_NO_BASIS: "값은 있으나 출처를 못 댔다",
        V_UNDECIDED: "아직 판정할 수 없다 (대개 논문 미조사)",
        V_UNVERIFIABLE: "확인 경로 자체가 없다 — 종결",
    }
    for verdict in (V_MATCH, V_MISMATCH, V_CODE_ONLY, V_PAPER_ONLY,
                    V_NO_BASIS, V_UNDECIDED, V_UNVERIFIABLE):
        if counts.get(verdict):
            lines.append(f"| {verdict} | {counts[verdict]} | {meanings[verdict]} |")
    lines.append("")

    lines.append("## 레코드")
    lines.append("")
    lines.append("| id | 질문 | paper | upstream_doc | code | 판정 |")
    lines.append("|---|---|---|---|---|---|")
    for record, verdict, _ in rows:
        lines.append(
            f"| `{_cell(record.get('id'))}` | {_cell(record.get('question'))} "
            f"| {_slot_cell(record, 'paper')} | {_slot_cell(record, 'upstream_doc')} "
            f"| {_slot_cell(record, 'code')} | **{verdict}** |"
        )
    lines.append("")

    lines.append("## 레코드 상세")
    lines.append("")
    for record, verdict, reason in rows:
        lines.append(f"### `{record.get('id')}` — {_cell(record.get('question'))}")
        lines.append("")
        lines.append(f"**판정: {verdict}** — {reason}")
        lines.append("")
        for name in SLOTS:
            slot = _slot(record, name)
            lines.append(f"- **{name}** — {_status(record, name)}")
            for key in ("locus", "value", "searched", "checked_by", "note"):
                if slot.get(key) not in (None, "", []):
                    lines.append(f"    - {key}: {_cell(slot.get(key))}")
        if record.get("note"):
            lines.append(f"- **note** — {_cell(record.get('note'))}")
        if record.get("anchors"):
            lines.append(f"- **anchors** — {_cell(record.get('anchors'))}")
        lines.append("")

    return "\n".join(lines) + "\n"


def render_open_questions(document: dict) -> str:
    records = sorted(document.get("records") or [], key=lambda r: str(r.get("id", "")))
    open_rows, closed_rows = [], []
    for record in records:
        verdict, reason = derive_verdict(record)
        if verdict == V_UNVERIFIABLE:
            closed_rows.append((record, verdict, reason))
        elif verdict in OPEN_VERDICTS:
            open_rows.append((record, verdict, reason))

    lines = [
        "<!-- 자동 생성물입니다. 손으로 고치지 마십시오. -->",
        "<!-- python run.py claims 로 다시 만들어집니다. -->",
        "",
        "# OPEN QUESTIONS",
        "",
        "## 미해결",
        "",
    ]
    if open_rows:
        lines.append("| id | 질문 | 판정 | 다음에 할 일 |")
        lines.append("|---|---|---|---|")
        for record, verdict, reason in open_rows:
            todo = {
                V_UNDECIDED: "논문 슬롯을 채운다 (부록까지)",
                V_NO_BASIS: "근거를 더 찾거나, 못 찾았다는 사실을 그대로 둔다",
                V_MISMATCH: "어느 셀이 어떻게 다른지 짚는다",
                V_PAPER_ONLY: "코드에 정말 없는지 한 번 더 본다",
            }.get(verdict, "")
            lines.append(
                f"| `{_cell(record.get('id'))}` | {_cell(record.get('question'))} "
                f"| {verdict} | {todo} |"
            )
    else:
        lines.append("없습니다.")
    lines.append("")

    lines.extend([
        "## 확인불가 — 종결",
        "",
        "**미해결이 아닙니다.** 확인 경로 자체가 없어 종결된 항목입니다.",
        "여기 있는 것을 미해결로 되돌리지 마십시오. 원인 불명이 `설명됨` 으로",
        "둔갑하지 않는 것이 이 저장소의 존재 이유입니다.",
        "",
    ])
    if closed_rows:
        lines.append("| id | 질문 | 왜 불가한가 |")
        lines.append("|---|---|---|")
        for record, _, reason in closed_rows:
            why = ""
            for name in SLOTS:
                slot = _slot(record, name)
                if (slot.get("status") or "").strip() == IMPOSSIBLE:
                    why = slot.get("note") or slot.get("searched") or reason
                    break
            lines.append(
                f"| `{_cell(record.get('id'))}` | {_cell(record.get('question'))} | {_cell(why)} |"
            )
    else:
        lines.append("없습니다.")
    lines.append("")

    return "\n".join(lines) + "\n"


def render_all(registry_path=REGISTRY_PATH, *, write: bool = True):
    """registry 를 읽어 검증하고 두 문서를 다시 만듭니다."""
    document = load_yaml(registry_path) or {}
    records = document.get("records") or []

    problems = []
    seen = set()
    for record in records:
        record_id = record.get("id")
        if record_id in seen:
            problems.append(f"{record_id}: id 가 중복입니다")
        seen.add(record_id)
        problems.extend(validate(record))

    map_text = render_map(document)
    open_text = render_open_questions(document)
    if write:
        write_text(MAP_PATH, map_text)
        write_text(OPEN_PATH, open_text)

    return {
        "records": len(records),
        "problems": problems,
        "map_path": Path(MAP_PATH),
        "open_path": Path(OPEN_PATH),
    }
