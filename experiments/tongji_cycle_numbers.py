"""Tongji `cycle_number` 전수 조사 — LAB-014 의 +1 어긋남을 좁히기 위한 것.

배경
----
라벨 재현에서 Tongji 배포 라벨이 있는 108셀 중 104셀이 정확히 +1 로 어긋나고
4셀만 일치합니다 (``findings/registry.yaml`` LAB-014). 기존 서술은 "전 130셀의
``cycle_data[0]['cycle_number']`` 가 2" 라고 적었는데, 그렇다면 108셀이 균일하게
어긋나야 합니다. 4셀이 예외인 이유를 좁히려고 130셀 전수를 집계합니다.

**관찰만 적습니다.** 원인을 추정해 기록하지 않습니다.

상위 코드의 첫교차 분기는 ``correct_cycle_index + 1`` — 즉 pkl 의
``cycle_number`` 가 아니라 **배열 인덱스** 입니다
(``Extract_life_labels.py:152-156``, ``verify/labels.py:198-203``). 그래서 두
번호를 나란히 놓습니다.

    py experiments/tongji_cycle_numbers.py

산출물
------
``experiments/results/tongji_cycle_numbers.json`` (정규화 JSON)
``experiments/results/TONGJI_REPORT.md``

``run.py labels`` 를 다시 돌리지 않습니다. 재현 라벨·배포 라벨은 기존
``experiments/results/nb03_cells.json`` 에서 읽어 옵니다.
"""

from __future__ import annotations

import collections
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verify import REPO_ROOT, read_json, use_utf8_stdout, write_json, write_text
from verify import labels as labels_mod
from verify import soh as soh_mod

EXTRACTED = REPO_ROOT / "data" / "extracted"
RESULTS = REPO_ROOT / "experiments" / "results"
LABELS_DIR = EXTRACTED / "Life labels"

LAMBDA = labels_mod.EXTRAPOLATE_LOW  # 0.8 — 상위 코드의 첫교차 임계
MISSING_CAP = 20                     # 표에 싣는 결번 최대 개수

# 대조 대상. 지시서가 지정한 4셀과 같은 프로토콜의 대조군 6셀.
FOCUS_MATCH = [
    "Tongji1_CY25-025_1--7.pkl",
    "Tongji1_CY25-1_1--1.pkl",
    "Tongji1_CY25-1_1--7.pkl",
    "Tongji1_CY25-1_1--9.pkl",
]
FOCUS_CONTROL = [
    "Tongji1_CY25-1_1--2.pkl",
    "Tongji1_CY25-1_1--3.pkl",
    "Tongji1_CY25-1_1--4.pkl",
    "Tongji1_CY25-1_1--5.pkl",
    "Tongji1_CY25-1_1--6.pkl",
    "Tongji1_CY25-1_1--8.pkl",
]


# ---------------------------------------------------------------------------
# 셀 하나
# ---------------------------------------------------------------------------

def _cycle_numbers(data: dict) -> list:
    """``cycle_number`` 목록. 정수로 못 바꾸면 None 을 넣습니다.

    ``verify/soh.py:139-141`` 은 못 바꿀 때 ``i + 1`` 로 대체하지만, 여기서는
    대체하지 않습니다 — 필드가 무엇인지 보는 것이 목적입니다.
    """
    out = []
    for cycle in data["cycle_data"]:
        try:
            out.append(int(cycle["cycle_number"]))
        except (KeyError, TypeError, ValueError):
            out.append(None)
    return out


def _soh_series(file_name: str, data: dict) -> list:
    """전 사이클 SOH. ``_label_main`` 과 같은 규칙입니다 (본 경로, span 나눗셈 포함)."""
    nominal = soh_mod.nominal_capacity(file_name, data)
    span = soh_mod.soc_span_main(data)
    return [soh_mod.cycle_qd(c) / nominal / span for c in data["cycle_data"]]


def inspect(path: Path) -> dict:
    with open(path, "rb") as f:
        data = pickle.load(f)

    numbers = _cycle_numbers(data)
    n = len(numbers)
    known = [v for v in numbers if v is not None]
    first = known[0] if known else None
    last = known[-1] if known else None

    # 결번 — 목록이 range(첫값, 첫값 + 개수) 와 같은가
    contiguous = None
    missing: list = []
    if first is not None and len(known) == n:
        expected = list(range(first, first + n))
        contiguous = numbers == expected
        if not contiguous:
            present = set(numbers)
            span_end = last if last is not None else first
            missing = [v for v in range(first, span_end + 1) if v not in present]

    strictly_increasing = all(
        a is not None and b is not None and b > a
        for a, b in zip(numbers, numbers[1:])
    ) if n > 1 else True

    # SOH 가 λ 아래로 처음 내려가는 지점. 상위 코드와 같이 `<=` 입니다.
    sohs = _soh_series(path.name, data)
    cross_index = None
    for i, value in enumerate(sohs):
        if value <= LAMBDA:
            cross_index = i
            break

    cross_number = numbers[cross_index] if cross_index is not None else None
    missing_before_cross = None
    if cross_index is not None and first is not None and cross_number is not None:
        # 첫값부터 교차 지점까지 사이에 빠진 번호 수
        missing_before_cross = (cross_number - first) - cross_index

    return {
        "cell": path.name,
        "n_cycles": n,
        "cycle_number_first": first,
        "cycle_number_last": last,
        "cycle_number_expected_last": (first + n - 1) if first is not None else None,
        "contiguous": contiguous,
        "n_missing": len(missing) if contiguous is not None else None,
        "missing": missing[:MISSING_CAP],
        "missing_truncated": len(missing) > MISSING_CAP,
        "strictly_increasing": strictly_increasing,
        "already_spent_cycles": data.get("already_spent_cycles"),
        "cross_index": cross_index,
        "cross_index_plus1": (cross_index + 1) if cross_index is not None else None,
        "cross_cycle_number": cross_number,
        "missing_before_cross": missing_before_cross,
        # 교차 지점의 SOH 와 그 직전 값. 교차가 아슬아슬한지 보려는 것입니다 —
        # 배포 라벨이 한 칸 뒤에서 교차했다면 이 두 값 중 하나가 0.8 에
        # 붙어 있어야 합니다.
        "soh_before_cross": (
            sohs[cross_index - 1] if cross_index is not None and cross_index > 0 else None
        ),
        "soh_at_cross": sohs[cross_index] if cross_index is not None else None,
        "first_soh": sohs[0] if sohs else None,
        "last_soh": sohs[-1] if sohs else None,
    }


# ---------------------------------------------------------------------------
# 집계
# ---------------------------------------------------------------------------

def load_nb03(subset: str) -> dict:
    """기존 라벨 산출에서 재현·배포 라벨을 읽습니다. 다시 계산하지 않습니다."""
    path = RESULTS / "nb03_cells.json"
    if not path.exists():
        raise FileNotFoundError(f"먼저 라벨 산출이 있어야 합니다: {path}")
    return {r["cell"]: r for r in read_json(path) if r.get("subset") == subset}


def first_numbers_of_subset(subset: str) -> dict:
    """서브셋의 ``cycle_number[0]`` 값별 셀 수."""
    counts: collections.Counter = collections.Counter()
    for path in sorted((EXTRACTED / subset).glob("*.pkl")):
        with open(path, "rb") as f:
            data = pickle.load(f)
        numbers = _cycle_numbers(data)
        counts[numbers[0] if numbers else None] += 1
    return {str(k): v for k, v in sorted(counts.items(), key=lambda kv: (kv[0] is None, kv[0]))}


def check_key_mapping(pkl_names: set) -> dict:
    """배포 라벨 키의 ``-#`` → pkl 파일명의 ``--`` 치환이 1:1 인지."""
    distributed = labels_mod.load_distributed_labels(LABELS_DIR, "Tongji")
    mapped: dict = {}
    collisions: list = []
    for key in distributed:
        new = key.replace("-#", "--") if "-#" in key else key
        if new in mapped:
            collisions.append({"pkl": new, "keys": [mapped[new], key]})
        mapped[new] = key

    no_pkl = sorted(k for k in mapped if k not in pkl_names)
    return {
        "distributed_keys": len(distributed),
        "renamed": sum(1 for k in distributed if "-#" in k),
        "unique_after_rename": len(mapped),
        "collisions": collisions,
        "mapped_to_missing_pkl": no_pkl,
        "one_to_one": len(distributed) == len(mapped) and not no_pkl,
    }


# ---------------------------------------------------------------------------
# 표
# ---------------------------------------------------------------------------

def _fmt(value) -> str:
    if value is None:
        return "—"
    if value is True:
        return "예"
    if value is False:
        return "아니오"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _row(r: dict, *, soh: bool = False) -> str:
    cols = [
        f"`{r['cell'].replace('.pkl', '')}`",
        _fmt(r["cycle_number_first"]),
        _fmt(r["cycle_number_last"]),
        _fmt(r["n_cycles"]),
        _fmt(r["contiguous"]),
        _fmt(r["n_missing"]),
        _fmt(r["cross_index"]),
        _fmt(r["cross_cycle_number"]),
        _fmt(r["missing_before_cross"]),
    ]
    if soh:
        cols += [_fmt(r["soh_before_cross"]), _fmt(r["soh_at_cross"])]
    cols += [
        _fmt(r["repro_label"]),
        _fmt(r["dist_label"]),
        _fmt(r["delta"]),
        r["match"] or "—",
    ]
    return "| " + " | ".join(cols) + " |"


_COLS = ["셀", "첫번호", "끝번호", "개수", "연속", "결번수", "교차인덱스",
         "교차번호", "교차전결번"]
_TAIL = ["재현", "배포", "차", "대조"]


def _header(*, soh: bool = False) -> str:
    cols = _COLS + (["SOH(교차전)", "SOH(교차)"] if soh else []) + _TAIL
    return ("| " + " | ".join(cols) + " |\n"
            + "|" + "---|" * len(cols))


_HEADER = _header()


def render(payload: dict) -> str:
    rows = payload["cells"]
    by_cell = {r["cell"]: r for r in rows}
    s = payload["summary"]
    lines: list = []
    add = lines.append

    add("# Tongji `cycle_number` 전수 조사")
    add("")
    add("`experiments/tongji_cycle_numbers.py` 가 만듭니다. "
        "원본 JSON 은 `experiments/results/tongji_cycle_numbers.json` 입니다.")
    add("")
    add("**관찰만 적습니다.** 원인 판정은 하지 않습니다.")
    add("")
    add(f"- 대상: `data/extracted/Tongji/` {s['n_cells']}셀 전수")
    add(f"- SOH·교차 규칙: 본 경로와 동일 (SOC span 나눗셈 포함, λ={LAMBDA}, `<=` 비교)")
    add("- 재현 라벨·배포 라벨: 기존 `nb03_cells.json` 에서 읽었습니다 (재계산 없음)")
    add("")

    add("## 1. `cycle_data[0]['cycle_number']` 값별 셀 수")
    add("")
    add("| 값 | 셀 수 |")
    add("|---|---|")
    for key, count in s["first_number_counts"].items():
        add(f"| {key} | {count} |")
    add("")

    add("## 2. 결번")
    add("")
    add("`cycle_number` 목록이 `range(첫값, 첫값+개수)` 와 같은지입니다.")
    add("")
    add("| 구분 | 셀 수 |")
    add("|---|---|")
    add(f"| 연속 (결번 없음) | {s['n_contiguous']} |")
    add(f"| 결번 있음 | {s['n_with_gaps']} |")
    add("")
    add(f"- 결번 수 분포: {s['missing_count_distribution']}")
    add(f"- 번호가 순증가하지 않는 셀: {s['n_not_increasing']}")
    add(f"- `already_spent_cycles` 값별 셀 수: {s['already_spent_counts']}")
    add("")

    add("## 3. 대조 4셀과 대조군 6셀")
    add("")
    add("지시서가 지정한 일치 4셀과, 같은 프로토콜의 +1 대조군 6셀입니다.")
    add("")
    add("`SOH(교차전)` · `SOH(교차)` 는 교차 직전·직후 값입니다. 배포 라벨이 한 "
        "칸 뒤에서 교차한 결과라면 이 값들이 λ 에 붙어 있어야 합니다.")
    add("")
    add("### 일치 4셀")
    add("")
    add(_header(soh=True))
    for name in FOCUS_MATCH:
        if name in by_cell:
            add(_row(by_cell[name], soh=True))
    add("")
    add("### 대조군 6셀 (`Tongji1_CY25-1_1--2` ~ `--8`, 전부 +1)")
    add("")
    add(_header(soh=True))
    for name in FOCUS_CONTROL:
        if name in by_cell:
            add(_row(by_cell[name], soh=True))
    add("")

    add("## 4. 결번 유무 × 대조 결과")
    add("")
    add("\"4셀은 결번이 없고 104셀은 결번이 있다\" 가 성립하는지 봅니다.")
    add("")
    add("| 대조 | 연속 (결번 없음) | 결번 있음 |")
    add("|---|---|---|")
    for name, block in s["contiguity_by_match"].items():
        add(f"| {name} | {block['contiguous']} | {block['with_gaps']} |")
    add("")

    add("## 5. 대조 결과별 교차 지점 요약")
    add("")
    add("| 대조 | 셀 수 | `교차번호 - 재현라벨` 값별 셀 수 | `교차전결번` 값별 셀 수 |")
    add("|---|---|---|---|")
    for name, block in s["by_match"].items():
        add(f"| {name} | {block['n']} | {block['number_minus_label']} | {block['missing_before_cross']} |")
    add("")

    add("## 6. 전 130셀")
    add("")
    add("`교차인덱스` 는 SOH 가 λ 아래로 처음 내려가는 **0-기준 배열 위치**, "
        "`교차번호` 는 그 지점의 `cycle_number` 입니다. "
        "상위 코드의 첫교차 라벨은 `교차인덱스 + 1` 입니다 "
        "(`Extract_life_labels.py:152-156`).")
    add("")
    add(_HEADER)
    for r in rows:
        add(_row(r))
    add("")

    gappy = [r for r in rows if r["n_missing"]]
    add("## 7. 결번 목록 (결번이 있는 셀)")
    add("")
    add(f"결번이 있는 셀 {len(gappy)}개. 셀당 최대 {MISSING_CAP}개까지 싣습니다.")
    add("")
    add("| 셀 | 결번수 | 빠진 번호 |")
    add("|---|---|---|")
    for r in gappy:
        shown = ", ".join(str(v) for v in r["missing"])
        if r["missing_truncated"]:
            shown += f", … (총 {r['n_missing']}개)"
        add(f"| `{r['cell'].replace('.pkl', '')}` | {r['n_missing']} | {shown or '—'} |")
    add("")

    add("## 8. 다른 서브셋의 `cycle_number[0]`")
    add("")
    add("| 서브셋 | 셀 수 | `cycle_number[0]` 값별 셀 수 |")
    add("|---|---|---|")
    for name, counts in payload["other_subsets"].items():
        total = sum(counts.values())
        detail = ", ".join(f"`{k}`: {v}" for k, v in counts.items())
        add(f"| {name} | {total} | {detail} |")
    add("")

    km = payload["key_mapping"]
    add("## 9. 배포 라벨 키 ↔ pkl 파일명")
    add("")
    add("배포 라벨 키는 `-#`, pkl 파일명은 `--` 입니다. 치환이 짝을 잘못 맞춘 "
        "사례가 있는지 봅니다.")
    add("")
    add("| 항목 | 값 |")
    add("|---|---|")
    add(f"| 배포 라벨 키 수 | {km['distributed_keys']} |")
    add(f"| `-#` 를 포함해 치환된 키 수 | {km['renamed']} |")
    add(f"| 치환 후 서로 다른 키 수 | {km['unique_after_rename']} |")
    add(f"| 치환 충돌 (두 키가 한 pkl 로) | {len(km['collisions'])} |")
    add(f"| 대응하는 pkl 이 없는 키 | {len(km['mapped_to_missing_pkl'])} |")
    add(f"| 1:1 대응 | {_fmt(km['one_to_one'])} |")
    add("")
    if km["collisions"]:
        add("충돌:")
        for c in km["collisions"]:
            add(f"- `{c['pkl']}` ← {c['keys']}")
        add("")
    if km["mapped_to_missing_pkl"]:
        add("대응 pkl 없음:")
        for name in km["mapped_to_missing_pkl"]:
            add(f"- `{name}`")
        add("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------

def main() -> int:
    use_utf8_stdout()

    nb03 = load_nb03("Tongji")
    paths = sorted((EXTRACTED / "Tongji").glob("*.pkl"))
    print(f"Tongji {len(paths)}셀 읽는 중 …")

    rows = []
    for path in paths:
        row = inspect(path)
        ref = nb03.get(path.name, {})
        row["repro_label"] = ref.get("label")
        row["dist_label"] = ref.get("theirs")
        row["delta"] = ref.get("delta")
        row["match"] = ref.get("match")
        row["status"] = ref.get("status")
        # 교차 지점의 cycle_number 와 재현 라벨의 차 — 두 번호 체계의 간격
        if row["cross_cycle_number"] is not None and isinstance(row["repro_label"], int):
            row["number_minus_label"] = row["cross_cycle_number"] - row["repro_label"]
        else:
            row["number_minus_label"] = None
        rows.append(row)

    first_counts: collections.Counter = collections.Counter(
        r["cycle_number_first"] for r in rows
    )
    by_match: dict = {}
    for name in ("일치", "불일치", "양쪽없음"):
        group = [r for r in rows if r["match"] == name]
        if not group:
            continue
        by_match[name] = {
            "n": len(group),
            "number_minus_label": {
                str(k): v for k, v in sorted(
                    collections.Counter(r["number_minus_label"] for r in group).items(),
                    key=lambda kv: (kv[0] is None, kv[0]),
                )
            },
            "missing_before_cross": {
                str(k): v for k, v in sorted(
                    collections.Counter(r["missing_before_cross"] for r in group).items(),
                    key=lambda kv: (kv[0] is None, kv[0]),
                )
            },
        }

    contiguity_by_match: dict = {}
    for name in ("일치", "불일치", "양쪽없음"):
        group = [r for r in rows if r["match"] == name]
        if not group:
            continue
        contiguity_by_match[name] = {
            "contiguous": sum(1 for r in group if r["contiguous"] is True),
            "with_gaps": sum(1 for r in group if r["contiguous"] is False),
        }

    summary = {
        "n_cells": len(rows),
        "first_number_counts": {
            str(k): v for k, v in sorted(first_counts.items(),
                                         key=lambda kv: (kv[0] is None, kv[0]))
        },
        "n_contiguous": sum(1 for r in rows if r["contiguous"] is True),
        "n_with_gaps": sum(1 for r in rows if r["contiguous"] is False),
        "n_not_increasing": sum(1 for r in rows if not r["strictly_increasing"]),
        "already_spent_counts": {
            str(k): v for k, v in sorted(
                collections.Counter(r["already_spent_cycles"] for r in rows).items(),
                key=lambda kv: (kv[0] is None, kv[0]),
            )
        },
        "missing_count_distribution": {
            str(k): v for k, v in sorted(
                collections.Counter(r["n_missing"] for r in rows).items(),
                key=lambda kv: (kv[0] is None, kv[0]),
            )
        },
        "by_match": by_match,
        "contiguity_by_match": contiguity_by_match,
        "lambda": LAMBDA,
    }

    other = {}
    for subset in ("CALB", "MICH_EXP", "NA-ion", "SNL", "ZN-coin"):
        if (EXTRACTED / subset).is_dir():
            print(f"{subset} 읽는 중 …")
            other[subset] = first_numbers_of_subset(subset)
    other["Tongji"] = summary["first_number_counts"]

    payload = {
        "generated_by": "experiments/tongji_cycle_numbers.py",
        "source": "data/extracted/Tongji/*.pkl + experiments/results/nb03_cells.json",
        "lambda": LAMBDA,
        "missing_cap": MISSING_CAP,
        "summary": summary,
        "other_subsets": other,
        "key_mapping": check_key_mapping({p.name for p in paths}),
        "cells": rows,
    }

    write_json(RESULTS / "tongji_cycle_numbers.json", payload, normalized=True)
    write_text(RESULTS / "TONGJI_REPORT.md", render(payload))

    print(f"\ncycle_number[0] 분포: {summary['first_number_counts']}")
    print(f"연속 {summary['n_contiguous']} / 결번 {summary['n_with_gaps']}")
    for name, block in by_match.items():
        print(f"  {name}: n={block['n']} 교차번호-재현라벨={block['number_minus_label']}")
    print(f"키 1:1 대응: {payload['key_mapping']['one_to_one']}")
    print("\n→ experiments/results/tongji_cycle_numbers.json")
    print("→ experiments/results/TONGJI_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
