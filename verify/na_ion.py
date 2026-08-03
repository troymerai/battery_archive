"""NA-ion 셀별 C-rate 매핑 — README 표를 파싱합니다.

왜 README 인가
--------------
``.pkl`` 의 ``charge_protocol`` 은 NA-ion 64셀이 전부 같은 값이라 프로토콜을
구별하지 못합니다. 셀별 C-rate 는 ``READMEs/NA-ion_README.md`` 의 표에만
있습니다 (``META-008``).

파싱 규칙을 하드코딩하지 않습니다
---------------------------------
표의 열을 **머리글 이름으로** 찾습니다. 어느 열을 무엇으로 읽었는지는 반환
dict 의 ``columns`` 에 남고 보고서에 그대로 실립니다. 열 순서가 바뀌어도
읽히고, 머리글이 바뀌면 ``columns`` 가 비어 그 사실이 드러납니다.

파일명 대응
-----------
pkl 은 ``NA-ion_<이름>.pkl``, README 는 ``<이름>.xlsx`` 입니다. 양쪽에서
접두사 ``NA-ion_`` 과 확장자를 떼어 맞춥니다. 맞지 않는 것은 **양방향으로**
남깁니다 — pkl 만 있는 것과 README 행만 있는 것은 다른 사실입니다.
"""

from __future__ import annotations

import re
from pathlib import Path

from verify import read_text

__all__ = ["parse_readme_table", "build_mapping", "CRATE_BINS", "bin_of",
           "name_form", "FORM_TIMESTAMP", "FORM_PLAIN"]

# NA-ion 파일명은 두 가지 형태가 섞여 있습니다.
#
#   일반형      270040-1-1-64
#   타임스탬프형 2850-30_20250117105706_DefaultGroup_45_2
#
# 후자는 사이클러가 내보낸 이름이 그대로 남은 것으로 보이며, README 표에서
# 30°C 행이 나오는 것도 이 형태뿐입니다. 두 형태를 갈라 세면 v2 가 어느
# 집합을 세었는지가 드러납니다.
FORM_TIMESTAMP = "타임스탬프형"
FORM_PLAIN = "일반형"

_TIMESTAMP_RE = re.compile(r"^\d+-\d+_\d{8,}")


def name_form(stem: str) -> str:
    return FORM_TIMESTAMP if _TIMESTAMP_RE.match(stem) else FORM_PLAIN

# v2 §3.3 의 구간. **이 구간 나눔은 v2 의 것이며 데이터에서 유도한 것이
# 아닙니다.** 3.0C 초과 4.0C 미만과 5.8C 초과 6.0C 미만은 어느 구간에도
# 들어가지 않습니다 — 그 사실이 보이도록 그대로 둡니다.
CRATE_BINS = (
    ("2.0~3.0C (저속)", 2.0, 3.0),
    ("4.0~5.8C (중간)", 4.0, 5.8),
    ("6.0C (고속)", 6.0, 6.0),
)


def bin_of(rate):
    if rate is None:
        return "(C-rate 없음)"
    for name, low, high in CRATE_BINS:
        if low <= rate <= high:
            return name
    return f"(구간밖 {rate}C)"


def _split_row(line: str) -> list:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def parse_readme_table(path) -> dict:
    """README 안의 표 중 ``File_name`` 열을 가진 것을 찾아 파싱합니다."""
    lines = read_text(path).splitlines()
    header, rows = None, []
    i = 0
    while i < len(lines):
        if "|" not in lines[i]:
            i += 1
            continue
        cells = _split_row(lines[i])
        if i + 1 < len(lines) and "|" in lines[i + 1] and _is_separator(_split_row(lines[i + 1])):
            if any(c.lower().replace(" ", "") == "file_name" for c in cells):
                header = cells
                i += 2
                while i < len(lines) and "|" in lines[i]:
                    row = _split_row(lines[i])
                    if len(row) == len(header):
                        rows.append(row)
                    i += 1
                break
        i += 1

    if header is None:
        return {"columns": {}, "rows": [], "header": []}

    def find(*needles):
        for index, name in enumerate(header):
            flat = name.lower().replace(" ", "")
            if any(n in flat for n in needles):
                return index
        return None

    columns = {
        "file_name": find("file_name"),
        "current": find("current", "c-rate", "crate"),
        "temperature": find("temperature", "temp"),
        "nominal": find("nominal"),
    }

    parsed = []
    for row in rows:
        record = {"raw": row}
        for key, index in columns.items():
            record[key] = row[index] if index is not None else None
        record["c_rate"] = _parse_rate(record.get("current"))
        record["temperature_C"] = _parse_number(record.get("temperature"))
        record["stem"] = _strip_ext(record.get("file_name") or "")
        parsed.append(record)

    return {
        "columns": {k: (header[v] if v is not None else None)
                    for k, v in columns.items()},
        "column_index": columns,
        "header": header,
        "rows": parsed,
    }


def _strip_ext(name: str) -> str:
    for suffix in (".xlsx", ".xls", ".csv", ".pkl"):
        if name.lower().endswith(suffix):
            return name[: -len(suffix)]
    return name


def _parse_rate(text):
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*[Cc]\b", text)
    if not match:
        match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_number(text):
    if text is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(text))
    return float(match.group(0)) if match else None


def build_mapping(readme_path, cell_names, *, prefix: str = "NA-ion_") -> dict:
    """``findings/na_ion_crate.json`` 에 쓸 정규화 dict.

    ``cell_names`` 는 pkl 파일명 목록입니다 (``.pkl`` 포함).
    """
    table = parse_readme_table(readme_path)
    by_stem = {}
    duplicate_stems = []
    for row in table["rows"]:
        stem = row["stem"]
        if stem in by_stem:
            duplicate_stems.append(stem)
        by_stem[stem] = row

    mapping, unmapped_cells = {}, []
    for cell in sorted(cell_names):
        stem = _strip_ext(cell)
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
        row = by_stem.get(stem)
        if row is None:
            unmapped_cells.append(cell)
            continue
        mapping[cell] = {
            "readme_file_name": row["file_name"],
            "current_text": row["current"],
            "c_rate": row["c_rate"],
            "temperature_C": row["temperature_C"],
            "nominal_text": row["nominal"],
            "bin": bin_of(row["c_rate"]),
            "name_form": name_form(stem),
        }

    used = {_strip_ext(c)[len(prefix):] if _strip_ext(c).startswith(prefix)
            else _strip_ext(c) for c in cell_names}
    rows_without_cell = sorted(stem for stem in by_stem if stem not in used)

    temperatures = {}
    for row in table["rows"]:
        key = str(row["temperature_C"])
        temperatures[key] = temperatures.get(key, 0) + 1

    return {
        "source": Path(readme_path).name,
        "parse_rule": {
            "표 선택": "머리글에 File_name 이 있는 마크다운 표",
            "열 대응": table["columns"],
            "머리글 원문": table["header"],
            "C-rate 파싱": "Current 열에서 숫자+C 를 정규식으로 뽑아 float",
            "파일명 대응": f"pkl 이름에서 확장자와 접두사 {prefix!r} 를 떼고 README File_name 의 확장자를 뗀 것과 완전일치",
        },
        "readme_rows": len(table["rows"]),
        "duplicate_stems": sorted(set(duplicate_stems)),
        "cells_total": len(cell_names),
        "cells_mapped": len(mapping),
        "cells_unmapped": unmapped_cells,
        "readme_rows_without_cell": rows_without_cell,
        "temperature_histogram": dict(sorted(temperatures.items())),
        "name_form_counts": {
            form: sum(1 for v in mapping.values() if v["name_form"] == form)
            for form in (FORM_PLAIN, FORM_TIMESTAMP)
        },
        "mapping": dict(sorted(mapping.items())),
        "notes": [
            "C-rate 는 pkl 메타에 없습니다. 이 표가 유일한 출처입니다 (META-008).",
            "README 본문은 25도 단일이라고 적지만 표에는 30도 행이 섞여 있습니다 (META-009). temperature_histogram 을 보십시오.",
            "cells_unmapped 는 pkl 은 있는데 README 행이 없는 셀, readme_rows_without_cell 은 README 행은 있는데 pkl 이 없는 것입니다. 둘은 다른 사실입니다.",
        ],
    }
