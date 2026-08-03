"""PyYAML 이 없을 때 쓰는 축소 YAML 파서.

조원은 clone 만 합니다. 아무것도 설치하지 않은 bare Python 에서도
``python run.py claims`` 와 ``python run.py anchors`` 가 돌아가야 하므로
표준 라이브러리만으로 읽습니다.

**이 저장소가 직접 쓴 YAML 만 읽을 수 있습니다.** 지원 범위:

* 들여쓰기 기반 매핑과 시퀀스 (중첩 포함)
* ``"..."`` · ``'...'`` 인용 스칼라, 평문 스칼라
* ``true`` / ``false`` / ``null`` / ``~`` / 정수 / 실수
* ``[]`` · ``{}`` 와 단순 flow 시퀀스 ``[a, b]``
* ``#`` 주석 (인용 부호 안은 주석으로 보지 않음)

지원하지 않는 것: 블록 스칼라(``|``, ``>``), 앵커(``&``/``*``), 태그,
여러 문서(``---``), 복합 키. 이 저장소의 YAML 은 이것들을 쓰지 않습니다.
쓰게 되면 여기서 명시적으로 실패합니다 — 조용히 틀리지 않습니다.

PyYAML 이 설치되어 있으면 그쪽이 우선입니다 (``verify.load_yaml``).
"""

from __future__ import annotations

__all__ = ["loads", "MiniYAMLError"]


class MiniYAMLError(ValueError):
    """축소 파서가 다룰 수 없는 문법을 만났을 때."""


_UNSUPPORTED_PREFIX = ("|", ">", "&", "*", "!", "?")


def loads(text: str):
    """YAML 문자열을 파이썬 객체로."""
    lines = _tokenize(text)
    if not lines:
        return None
    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise MiniYAMLError(
            f"{lines[index][2]}행에서 멈췄습니다: {lines[index][1]!r} "
            "(들여쓰기가 어긋났을 수 있습니다)"
        )
    return value


# ---------------------------------------------------------------------------
# 토큰화
# ---------------------------------------------------------------------------

def _tokenize(text: str):
    """[들여쓰기, 내용, 원본행번호] 목록. 빈 줄과 주석 줄은 버립니다."""
    out = []
    for lineno, raw in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise MiniYAMLError(f"{lineno}행: 들여쓰기에 탭이 있습니다")
        stripped = _strip_comment(raw).rstrip()
        if not stripped.strip():
            continue
        if stripped.strip() in ("---", "..."):
            raise MiniYAMLError(f"{lineno}행: 여러 문서(---)는 지원하지 않습니다")
        indent = len(stripped) - len(stripped.lstrip())
        out.append([indent, stripped.strip(), lineno])
    return out


def _strip_comment(line: str) -> str:
    """인용 부호 밖의 ``#`` 부터 잘라냅니다."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


# ---------------------------------------------------------------------------
# 파싱
# ---------------------------------------------------------------------------

def _parse_block(lines, index, indent):
    if index >= len(lines):
        return None, index
    text = lines[index][1]
    if text == "-" or text.startswith("- "):
        return _parse_seq(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_seq(lines, index, indent):
    items = []
    while index < len(lines):
        cur_indent, text, lineno = lines[index]
        if cur_indent != indent:
            break
        if not (text == "-" or text.startswith("- ")):
            break

        if text == "-":
            # 값이 다음 줄부터 시작하는 형태
            index += 1
            if index < len(lines) and lines[index][0] > indent:
                value, index = _parse_block(lines, index, lines[index][0])
            else:
                value = None
            items.append(value)
            continue

        # "- " 뒤의 내용을 그 내용이 실제로 시작하는 열에 놓인 한 줄로 바꿔
        # 읽습니다. 뒤따르는 같은 열의 줄들이 자연스럽게 같은 매핑에 붙습니다.
        content = text[1:].lstrip()
        offset = cur_indent + (len(text) - len(content))
        lines[index] = [offset, content, lineno]
        value, index = _parse_block(lines, index, offset)
        items.append(value)
    return items, index


def _parse_map(lines, index, indent):
    mapping = {}
    while index < len(lines):
        cur_indent, text, lineno = lines[index]
        if cur_indent != indent:
            break
        if text.startswith("- "):
            break

        key, sep, rest = _split_key(text)
        if not sep:
            raise MiniYAMLError(f"{lineno}행: 콜론이 없습니다 — {text!r}")
        key = _scalar(key, lineno)
        rest = rest.strip()
        index += 1

        if rest:
            if rest[0] in _UNSUPPORTED_PREFIX and rest not in ("*", "!"):
                raise MiniYAMLError(
                    f"{lineno}행: 지원하지 않는 문법입니다 — {rest[0]!r} "
                    "(블록 스칼라·앵커·태그는 쓰지 않습니다)"
                )
            mapping[key] = _scalar(rest, lineno)
            continue

        if index < len(lines) and lines[index][0] > indent:
            mapping[key], index = _parse_block(lines, index, lines[index][0])
        elif index < len(lines) and lines[index][0] == indent and (
            lines[index][1] == "-" or lines[index][1].startswith("- ")
        ):
            # 같은 열에 놓인 시퀀스도 이 키의 값입니다 (YAML 이 허용하는 형태).
            mapping[key], index = _parse_seq(lines, index, indent)
        else:
            mapping[key] = None
    return mapping, index


def _split_key(text: str):
    """인용 부호 밖의 첫 ``:`` 에서 자릅니다.

    ``line: "10:30"`` 처럼 값 안에 콜론이 있어도 키를 잘못 자르지 않습니다.
    """
    quote = None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == ":" and (i + 1 == len(text) or text[i + 1] in " \t"):
            return text[:i], ":", text[i + 1:]
    return text, "", ""


def _scalar(token: str, lineno: int):
    token = token.strip()
    if not token:
        return None

    if token[0] == '"' and token.endswith('"') and len(token) >= 2:
        return _unescape(token[1:-1])
    if token[0] == "'" and token.endswith("'") and len(token) >= 2:
        return token[1:-1].replace("''", "'")

    if token == "[]":
        return []
    if token == "{}":
        return {}
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part, lineno) for part in _split_flow(inner)]
    if token.startswith("{"):
        raise MiniYAMLError(f"{lineno}행: flow 매핑은 지원하지 않습니다 — {token!r}")

    low = token.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False

    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return token


def _split_flow(inner: str):
    parts, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _unescape(text: str) -> str:
    out, i = [], 0
    table = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt in table:
                out.append(table[nxt])
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)
