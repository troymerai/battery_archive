"""라벨 재현 실행과 사람이 읽을 보고서.

노트북 01 · 02 · 03 이 하는 일을 헤드리스로 냅니다. **계산 규칙을 여기서
만들지 않습니다.** SOH 와 라벨은 전부 ``verify/soh.py`` · ``verify/labels.py``
를 그대로 부르고, 이 파일은 pkl 을 한 번만 열어 두 변형을 함께 돌리고
표로 옮기는 일만 합니다.

pkl 을 한 번만 여는 이유
------------------------
재집계 · ``code`` 변형 · ``no_soc_span`` 변형이 각각 트리를 읽으면 8.6 GB 를
세 번 읽습니다. 한 번 열어 셋을 함께 계산합니다. 그 대가로 이 파일이
``labels.label_subset`` 대신 ``labels.label_cell`` 을 직접 부릅니다 — 규칙은
같고 파일 열기만 여기로 옮겨온 것입니다.

배포 라벨 키 이름이 pkl 파일명과 다르다
---------------------------------------
Tongji 만 배포 라벨 JSON 의 키가 ``-#`` 를 쓰고 pkl 파일명은 ``--`` 를 씁니다
(``Tongji1_CY25-05_1-#19.pkl`` 대 ``Tongji1_CY25-05_1--19.pkl``). 상위 코드도
같은 치환을 합니다 (``dataset_overview_calculation.py:9``). 이름 규칙이지
계산 규칙이 아니므로 대조 직전에 키만 맞춥니다. 몇 개가 이 치환을 탔는지
보고서에 적습니다 — 치환을 안 하면 Tongji 130셀이 전부 "우리만있음" 으로
나오고, 그 표는 발견이 아니라 버그입니다.
"""

from __future__ import annotations

import json
import math
import pickle
from pathlib import Path

from verify import REPO_ROOT, load_config, write_json, write_text
from verify import extras as ex
from verify import labels as lab
from verify import na_ion
from verify import recount as rc
from verify import soh as soh_mod
from verify import v2compare

__all__ = ["analyze", "run", "RESULTS", "PRIOR_CENSORED", "FOCUS_MICH_EXP",
           "FOCUS_MICH_EXP_CONTROL", "FOCUS_SNL_PREFIX"]

RESULTS = REPO_ROOT / "experiments" / "results"

# 직전 조사에서 보고된 중도절단 수. **기준값이 아니라 대조 대상입니다.**
# 이번 계산이 이것과 다르면 이번 계산이 틀렸다는 뜻이 아닙니다.
PRIOR_CENSORED = {
    "NA-ion": 21, "ZN-coin": 19, "Tongji": 22, "SNL": 9, "MICH_EXP": 6,
}
PRIOR_TOTAL = 77

FOCUS_MICH_EXP = [
    "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C",
    "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C",
    "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C",
    "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C",
    "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C",
    "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C",
]
# 대조군 — 전류·온도가 같고 SOC 구간만 0-100 인 셋
FOCUS_MICH_EXP_CONTROL = [
    "MICH_01R_pouch_NMC_25C_0-100_0.2-0.2C",
    "MICH_02C_pouch_NMC_-5C_0-100_0.2-0.2C",
    "MICH_03H_pouch_NMC_45C_0-100_0.2-0.2C",
]
FOCUS_SNL_PREFIX = "SNL_18650_NCA_25C_20-80_0.5-0.5C_"


# ---------------------------------------------------------------------------
# 배포 라벨 키 ↔ pkl 파일명
# ---------------------------------------------------------------------------

def normalize_label_keys(distributed: dict) -> tuple:
    """배포 라벨의 키를 pkl 파일명 쪽으로 맞춥니다. (dict, 치환된수)"""
    out, renamed = {}, 0
    for key, value in distributed.items():
        new = key.replace("-#", "--") if "-#" in key else key
        if new != key:
            renamed += 1
        out[new] = value
    return out, renamed


# ---------------------------------------------------------------------------
# 셀 하나
# ---------------------------------------------------------------------------

def _safe_soh(data: dict, file_name: str, index: int, *, use_soc_span: bool):
    """사이클 하나의 SOH. 계산할 수 없으면 None 입니다.

    CALB 는 상위 코드가 **외부 Excel 의 첫 사이클 용량** 을 공칭용량으로 쓰므로
    (Extract_life_labels.py:170) 여기 값과 기준이 다릅니다. 그래서 결과 행에
    ``soh_basis`` 를 붙여 pkl 메타 기준임을 남깁니다.
    """
    try:
        cycles = data["cycle_data"]
        nominal = soh_mod.nominal_capacity(file_name, data)
        span = soh_mod.soc_span_main(data) if use_soc_span else 1.0
        if not math.isfinite(nominal) or nominal == 0 or span == 0:
            return None
        return float(soh_mod.cycle_qd(cycles[index]) / nominal / span)
    except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
        return None


def _cell_rows(subset: str, file_name: str, data: dict) -> dict:
    """한 셀에 대해 세 변형을 함께 계산합니다.

    pkl 을 한 번만 열기 위해서입니다. ``discharge_denom`` 은 ISU_ILCC 밖에서는
    ``code`` 와 같은 값이 나와야 하고, 그것이 실제로 그런지도 이 자리에서
    확인됩니다 (``variants_identical`` 열).
    """
    route = lab.route_of(subset)
    out = {}
    for variant, use_span in (("code", True), ("no_soc_span", False),
                              ("discharge_denom", True)):
        result = lab.label_cell(subset, file_name, data, use_soc_span=use_span,
                                variant=variant)
        out[variant] = {
            "subset": lab.canonical(subset),
            "domain": lab.domain_of(subset),
            "cell": file_name,
            "route": route,
            "status": result["status"],
            "label": result["label"],
            "last_soh": result.get("last_soh"),
            "backend": result.get("backend", ""),
            "note": result.get("note", ""),
            "first_soh": _safe_soh(data, file_name, 0, use_soc_span=use_span),
            "last_soh_recomputed": _safe_soh(data, file_name, -1, use_soc_span=use_span),
            "soh_basis": "pkl 메타(외부 Excel 아님)" if route == lab.ROUTE_CALB else "pkl 메타",
        }
    return out


# ---------------------------------------------------------------------------
# 전체 실행 — pkl 을 한 번씩만 연다
# ---------------------------------------------------------------------------

def analyze(extract_dir, *, subsets=None, limit=None) -> dict:
    root = Path(extract_dir)
    if not root.exists():
        raise FileNotFoundError(
            f"EXTRACT_DIR 이 없습니다: {root}. config.env 를 확인하고 zip 을 푸십시오."
        )

    names = list(subsets) if subsets else rc.iter_subsets(root)
    names = [n for n in names if n not in rc.EXCLUDED_SUBSETS]
    excluded_present = [n for n in rc.iter_subsets(root) if n in rc.EXCLUDED_SUBSETS]

    labels_dir = root / "Life labels"
    metas, rows_code, rows_nospan, rows_dd = [], [], [], []
    extras_rows = []
    focus_raw = {}

    # 배포 라벨을 먼저 읽습니다. 셀 루프 안에서 extras 가 배포값을 함께 봐야
    # 하기 때문입니다 (논문식 라벨 대 배포 라벨 대조).
    dist_by_subset = {}
    for subset in names:
        try:
            distributed = lab.load_distributed_labels(labels_dir, subset)
        except FileNotFoundError:
            dist_by_subset[lab.canonical(subset)] = None
            continue
        normalized, renamed = normalize_label_keys(distributed)
        dist_by_subset[lab.canonical(subset)] = (normalized, renamed, len(distributed))

    for subset in names:
        paths = sorted((root / subset).glob("*.pkl"), key=lambda p: p.name)
        if limit is not None:
            paths = paths[:limit]
        pair_dist = dist_by_subset.get(lab.canonical(subset))
        dist_map = pair_dist[0] if pair_dist else {}
        for path in paths:
            with open(path, "rb") as f:
                data = pickle.load(f)

            meta = rc.cell_meta(path.name, data)
            meta["subset"] = lab.canonical(subset)
            metas.append(meta)

            pair = _cell_rows(subset, path.name, data)
            rows_code.append(pair["code"])
            rows_nospan.append(pair["no_soc_span"])
            rows_dd.append(pair["discharge_denom"])

            # CALB 도 넣습니다. 라벨은 재현불가지만 pkl 은 여기 있고,
            # cycle_number 집계(META-007)는 라벨과 무관하게 셀 수 있습니다.
            extras_rows.append(ex.cell_extras(
                lab.canonical(subset), path.name, data,
                rows={"code": pair["code"],
                      "nospan": pair["no_soc_span"],
                      "dd": pair["discharge_denom"]},
                theirs=dist_map.get(path.name),
            ))

            stem = path.stem
            if (stem in FOCUS_MICH_EXP or stem in FOCUS_MICH_EXP_CONTROL
                    or stem.startswith(FOCUS_SNL_PREFIX)):
                focus_raw[path.name] = {
                    "soc_interval_raw": repr(data.get("SOC_interval")),
                    "soc_span_main": _try(lambda: soh_mod.soc_span_main(data)),
                    "nominal_in_pkl": _try(lambda: float(data["nominal_capacity_in_Ah"])),
                    "nominal_used": _try(lambda: soh_mod.nominal_capacity(path.name, data)),
                    "cycles": len(data.get("cycle_data") or []),
                    # 곡선 최솟값. 상위 코드의 판정은 **마지막 사이클** 만 보므로
                    # (Extract_life_labels.py:121) 곡선이 0.8 아래로 내려갔다가
                    # 되살아난 셀은 폐기됩니다. 그 차이를 보이기 위한 값입니다.
                    "soh_min": _try(lambda: float(min(
                        soh_mod.soh_curve(data, path.name, use_soc_span=True)[1]))),
                    "soh_min_nospan": _try(lambda: float(min(
                        soh_mod.soh_curve(data, path.name, use_soc_span=False)[1]))),
                }

    # --- 배포 라벨과 대조 -------------------------------------------------
    compared_code, compared_nospan, compared_dd = [], [], []
    label_files, rename_counts, dist_only = {}, {}, {}
    for subset in names:
        name = lab.canonical(subset)
        subset_rows = [r for r in rows_code if r["subset"] == name]
        subset_rows_ns = [r for r in rows_nospan if r["subset"] == name]
        subset_rows_dd = [r for r in rows_dd if r["subset"] == name]
        pair_dist = dist_by_subset.get(name)
        if pair_dist is None:
            label_files[name] = None
            compared_code.extend(dict(r, theirs=None, match="배포라벨없음") for r in subset_rows)
            compared_nospan.extend(dict(r, theirs=None, match="배포라벨없음") for r in subset_rows_ns)
            compared_dd.extend(dict(r, theirs=None, match="배포라벨없음") for r in subset_rows_dd)
            continue

        normalized, renamed, raw_keys = pair_dist
        label_files[name] = {
            "file": lab.label_json_name(subset),
            "keys": raw_keys,
            "null_values": sum(1 for v in normalized.values() if v is None),
            "renamed_keys": renamed,
        }
        rename_counts[name] = renamed
        compared_code.extend(lab.compare(subset_rows, normalized))
        compared_nospan.extend(lab.compare(subset_rows_ns, normalized))
        compared_dd.extend(lab.compare(subset_rows_dd, normalized))

        have = {r["cell"] for r in subset_rows}
        extra = sorted(k for k in normalized if k not in have)
        if extra:
            dist_only[name] = extra

    return {
        "subsets": [lab.canonical(n) for n in names],
        "subsets_raw": names,
        "excluded_present": excluded_present,
        "metas": metas,
        "cells": compared_code,
        "cells_nospan": compared_nospan,
        "cells_discharge_denom": compared_dd,
        "extras": extras_rows,
        "label_files": label_files,
        "rename_counts": rename_counts,
        "dist_only": dist_only,
        "focus_raw": focus_raw,
        "extract_dir": root,
        "labels_dir": labels_dir,
    }


def _try(fn):
    try:
        return fn()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 롤업
# ---------------------------------------------------------------------------

def rollup_by(rows: list, field: str) -> list:
    """``labels.rollup`` 을 다른 축으로 재사용합니다. 세는 규칙은 그대로입니다."""
    return lab.rollup([dict(r, domain=r[field]) for r in rows])


def variant_diff(code_rows: list, nospan_rows: list) -> list:
    """두 변형을 셀 단위로 나란히 놓습니다."""
    index = {r["cell"]: r for r in nospan_rows}
    out = []
    for row in code_rows:
        other = index.get(row["cell"], {})
        out.append({
            "subset": row["subset"], "cell": row["cell"], "route": row["route"],
            "code_last_soh": row.get("last_soh"),
            "nospan_last_soh": other.get("last_soh"),
            "code_status": row.get("status"), "nospan_status": other.get("status"),
            "code_label": row.get("label"), "nospan_label": other.get("label"),
            "theirs": row.get("theirs"),
            "code_match": row.get("match"), "nospan_match": other.get("match"),
            "differs": (row.get("status") != other.get("status")
                        or row.get("label") != other.get("label")),
        })
    return out


# ---------------------------------------------------------------------------
# 마크다운 표
# ---------------------------------------------------------------------------

def _fmt(value, digits=4):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "예" if value else "아니오"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "비유한"
        return f"{value:.{digits}f}"
    return str(value)


def table(headers: list, rows: list) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(cell) for cell in row) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LABEL_REPORT.md
# ---------------------------------------------------------------------------

def _focus_rows(result: dict, cells: list, nospan_index: dict, *, snl: bool = False):
    by_name = {r["cell"]: r for r in result["cells"]}
    out = []
    for name in cells:
        key = name if name.endswith(".pkl") else name + ".pkl"
        row = by_name.get(key)
        raw = result["focus_raw"].get(key, {})
        other = nospan_index.get(key, {})
        if row is None:
            out.append([name, "(pkl 없음)"] + ["—"] * (14 if snl else 13))
            continue
        base = [
            name,
            raw.get("soc_interval_raw", "—"),
            raw.get("soc_span_main"),
        ]
        if snl:
            base.append(raw.get("nominal_in_pkl"))
            base.append(raw.get("nominal_used"))
        else:
            base.append(raw.get("nominal_used"))
        base += [
            raw.get("cycles"),
            row.get("first_soh"),
            row.get("last_soh_recomputed"),
            raw.get("soh_min"),
            row.get("status"),
            row.get("label"),
            "있음" if row.get("theirs") is not None else "없음",
            row.get("match"),
            other.get("status"),
            other.get("label"),
            raw.get("soh_min_nospan"),
        ]
        out.append(base)
    return out


def render(result: dict, *, stamp: str, variants: dict, recount_data: dict,
           computed: dict | None = None, na_map: dict | None = None) -> str:
    cells = result["cells"]
    nospan = result["cells_nospan"]
    nospan_index = {r["cell"]: r for r in nospan}

    domain_roll = lab.rollup(cells)
    subset_roll = rollup_by(cells, "subset")
    subset_roll_index = {r["domain"]: r for r in subset_roll}

    backends = sorted({r.get("backend", "") for r in cells if r.get("backend")})
    lines = []
    add = lines.append

    add("# LABEL_REPORT — 라벨 재현 결과")
    add("")
    add(f"실행: {stamp}   /   실행자: CC (헤드리스, `python run.py labels --recount`)")
    add("")
    add("이 파일은 **분석의 입력** 입니다. 판단과 해석은 사람이 합니다. 여기에는")
    add("계산한 것과 관찰한 것만 있습니다. 값이 배포물과 다른 것은 실패가 아니라")
    add("발견이며, 그 원인은 이 파일에 적지 않습니다.")
    add("")
    if result.get("partial"):
        add("> **부분 실행입니다.** `--subset` 또는 `--limit` 이 걸린 실행이라 아래 표는")
        add("> 배포 데이터 전체가 아닙니다. 산출물은 `experiments/results/scratch/` 에")
        add("> 쓰였고 LOCK 대상 파일을 덮어쓰지 않았습니다. 대조표로 쓰지 마십시오.")
        add("")
    add("## 0. 실행 조건")
    add("")
    add(table(["항목", "값"], [
        ["EXTRACT_DIR", Path(result["extract_dir"]).as_posix()],
        ["배포 라벨 폴더", Path(result["labels_dir"]).as_posix()],
        ["집계한 서브셋", f"{len(result['subsets'])}개 — " + ", ".join(result["subsets"])],
        ["셀 수 (pkl)", len(cells)],
        ["회귀 backend", ", ".join(backends) if backends else "(외삽 셀 없음)"],
        ["변형", "code (상위 코드 그대로) / no_soc_span (SOC span 나눗셈 제거) / "
                "discharge_denom (ISU_ILCC 분모만 방전 기준)"],
    ]))
    add("")
    add("`backend` 가 `numpy` 면 상위 코드의 `sklearn.LinearRegression` 대신 최소제곱으로")
    add("대체된 것이라 외삽 라벨의 끝자리가 다를 수 있습니다.")
    add("")
    add("### 절 차례")
    add("")
    add(table(["절", "내용", "지시문"], [
        ["1", "데이터셋 보고서 v2 수치 대조", "6-1"],
        ["2", "`ISU_ILCC` 240셀", "6-2"],
        ["3", "`RWTH` 48셀", "6-3"],
        ["4", "`UL_PUR` 10셀", "6-4"],
        ["5", "`XJTU` 23셀", "6-5"],
        ["6", "`cycle_number` 전 서브셋 집계", "6-6"],
        ["7", "곡선 무변화 셀", "6-7"],
        ["8", "`NA-ion` C-rate 편중", "6-8"],
        ["9", "도메인 · 서브셋 롤업", "(기존 1절)"],
        ["10", "불일치 셀", "(기존 2절)"],
        ["11", "`MICH_EXP` 6셀", "(기존 3절)"],
        ["12", "`SNL` 4셀", "(기존 4절)"],
        ["13", "`CALB` 재현불가", "(기존 5절)"],
        ["14", "재집계 요약", "(기존 6절)"],
        ["15", "SOC span 변형 비교", "(기존 7절)"],
        ["16", "확인 불가로 남은 것", "6-9 / (기존 8절)"],
        ["17", "산출 파일", "(기존 9절)"],
    ]))
    add("")
    add("절 번호가 직전 판(6서브셋 기준)에서 8 만큼 밀렸습니다. 기존 1~9 절이")
    add("9~17 절입니다.")
    add("")

    if computed is not None:
        add(v2compare.render_sections(result, computed, recount_data, na_map or {}))

    # --- 6-1 -------------------------------------------------------------
    add("---")
    add("")
    add("## 9. 도메인 롤업")
    add("")
    add(table(["도메인", "셀", "라벨보유", "중도절단", "외삽", "재현불가", "절단비"],
              [[r["domain"], r["cells"], r["labeled"], r["censored"],
                r["extrapolated"], r["unreproducible"], r["censored_ratio"]]
               for r in domain_roll]))
    add("")
    add("`중도절단` = 폐기(last SOH ≥ 0.825) + 외삽(0.8 < last SOH < 0.825).")
    add("`재현불가` = 외부 파일 미배포로 계산 경로 자체가 없는 셀 (CALB · Farasis).")
    add("")
    add("### 서브셋별")
    add("")
    add(table(["서브셋", "도메인", "셀", "라벨보유", "폐기", "외삽", "중도절단", "재현불가", "절단비"],
              [[r["domain"],
                next((c["domain"] for c in cells if c["subset"] == r["domain"]), "—"),
                r["cells"], r["labeled"], r["abandoned"], r["extrapolated"],
                r["censored"], r["unreproducible"], r["censored_ratio"]]
               for r in subset_roll]))
    add("")
    add("### 직전 조사와의 대조 — 77셀")
    add("")
    add("`중도절단` 을 무엇으로 세느냐에 따라 숫자가 갈립니다. 세 가지를 함께 냅니다.")
    add("")
    add("- **폐기+외삽** — `verify/labels.py` 의 `rollup` 정의 (last SOH > 0.8)")
    add("- **폐기만** — last SOH ≥ 0.825. 상위 코드가 `continue` 로 건너뛰어 라벨 JSON 에 키가 아예 안 생기는 셀")
    add("- **배포 라벨에 키 없음** — 배포된 JSON 에서 실제로 빠진 셀 수")
    add("")
    prior_rows = []
    total_cens = total_aband = total_absent = 0
    for subset, prior in PRIOR_CENSORED.items():
        bucket = subset_roll_index.get(subset, {})
        cens = bucket.get("censored", 0)
        aband = bucket.get("abandoned", 0)
        absent = sum(1 for r in cells if r["subset"] == subset and r.get("theirs") is None)
        total_cens += cens
        total_aband += aband
        total_absent += absent
        prior_rows.append([
            {"NA-ion": "Na-ion", "ZN-coin": "Zn-ion"}.get(subset, f"Li-ion ({subset})"),
            f"{prior}", cens, aband, absent,
            "일치" if prior in (cens, aband, absent) else "불일치",
        ])
    prior_rows.append(["**합계**", f"**{PRIOR_TOTAL}**", total_cens, total_aband,
                       total_absent,
                       "일치" if PRIOR_TOTAL in (total_cens, total_aband, total_absent)
                       else "불일치"])
    add(table(["도메인", "기존 보고 절단", "이번 폐기+외삽", "이번 폐기만",
               "배포 키 없음", "일치 여부"], prior_rows))
    add("")
    matched = [name for name, value in (("폐기+외삽", total_cens), ("폐기만", total_aband),
                                        ("배포 키 없음", total_absent))
               if value == PRIOR_TOTAL]
    if matched:
        add(f"합계 {PRIOR_TOTAL} 과 맞는 정의: **{' · '.join(matched)}**.")
    else:
        add(f"어느 정의로도 합계가 {PRIOR_TOTAL} 이 되지 않습니다.")
    add("")
    for subset, prior in PRIOR_CENSORED.items():
        bucket = subset_roll_index.get(subset, {})
        cens = bucket.get("censored", 0)
        aband = bucket.get("abandoned", 0)
        absent = sum(1 for r in cells if r["subset"] == subset and r.get("theirs") is None)
        if prior not in (cens, aband, absent):
            add(f"- `{subset}` — 기존 보고 {prior}, 이번 폐기+외삽 {cens} · 폐기만 {aband} · "
                f"배포 키 없음 {absent}. **어느 정의로도 맞지 않습니다.**")
    add("")
    add("어느 쪽이 옳은지는 이 파일이 말하지 않습니다. 셀 목록은 `nb03_cells.json` 의")
    add("`status` · `match` 로 거를 수 있습니다.")
    add("")
    add("### 배포 라벨 파일과 pkl 수")
    add("")
    add(table(["서브셋", "라벨 JSON", "키 수", "pkl 수", "차이", "null 값", "키이름 치환"],
              [[name,
                (info or {}).get("file", "(없음)"),
                (info or {}).get("keys", "—"),
                sum(1 for c in cells if c["subset"] == name),
                (sum(1 for c in cells if c["subset"] == name) - info["keys"]) if info else "—",
                (info or {}).get("null_values", "—"),
                (info or {}).get("renamed_keys", "—")]
               for name, info in sorted(result["label_files"].items())]))
    add("")
    add("`키이름 치환` 은 배포 라벨 키의 `-#` 를 pkl 파일명의 `--` 로 맞춘 개수입니다")
    add("(Tongji 만 해당). 치환하지 않으면 Tongji 전 셀이 대조 불가로 나옵니다.")
    add("")
    if result["dist_only"]:
        add("배포 라벨에는 있으나 보유 pkl 에 없는 키:")
        add("")
        for subset, keys in sorted(result["dist_only"].items()):
            add(f"- `{subset}` {len(keys)}개 — 예: {', '.join(keys[:3])}")
        add("")

    # --- 6-2 -------------------------------------------------------------
    mismatch = [r for r in cells if r.get("match") == "불일치"]
    add("---")
    add("")
    add("## 10. 불일치 셀")
    add("")
    add(table(["대조 결과", "셀 수"],
              sorted(((k, sum(1 for r in cells if r.get("match") == k))
                      for k in {r.get("match") for r in cells}),
                     key=lambda kv: (-kv[1], kv[0]))))
    add("")
    add("### 경로별 집계")
    add("")
    route_rows = []
    for route in (lab.ROUTE_MAIN, lab.ROUTE_XJTU, lab.ROUTE_CALB, lab.ROUTE_FARASIS):
        total = sum(1 for r in cells if r["route"] == route)
        if not total:
            continue
        bad = sum(1 for r in mismatch if r["route"] == route)
        route_rows.append([
            {lab.ROUTE_MAIN: "본경로", lab.ROUTE_XJTU: "XJTU보간",
             lab.ROUTE_CALB: "재현불가(CALB)", lab.ROUTE_FARASIS: "재현불가(Farasis)"}[route],
            total, bad, round(bad / total, 4) if total else None,
        ])
    add(table(["경로", "셀", "불일치", "비율"], route_rows))
    add("")
    add("### 서브셋별 대조 결과")
    add("")
    match_kinds = sorted({r.get("match", "?") for r in cells})
    add(table(["서브셋"] + match_kinds,
              [[subset] + [sum(1 for r in cells if r["subset"] == subset
                               and r.get("match") == kind) for kind in match_kinds]
               for subset in sorted({r["subset"] for r in cells})]))
    add("")
    add("### 차이값 분포 — `배포 − 재현`")
    add("")
    delta_tally = {}
    for row in mismatch:
        key = (row["subset"], row.get("delta"))
        delta_tally[key] = delta_tally.get(key, 0) + 1
    if delta_tally:
        add(table(["서브셋", "차이", "셀 수"],
                  [[subset, delta, count] for (subset, delta), count
                   in sorted(delta_tally.items(), key=lambda kv: (kv[0][0], str(kv[0][1])))]))
        add("")
        add("차이가 한 값에 몰리는지 흩어지는지가 핵심입니다. 위 표가 한 줄이면 전 셀이")
        add("같은 크기로 어긋난 것이고, 여러 줄이면 셀마다 다르게 어긋난 것입니다.")
        add("")
    only_ours = [r for r in cells if r.get("match") == "우리만있음"]
    if only_ours:
        add("### `우리만있음` — 재현은 됐는데 배포 라벨에 키가 없는 셀")
        add("")
        add(table(["서브셋", "셀", "재현 라벨", "상태", "마지막 SOH"],
                  [[r["subset"], r["cell"], r["label"], r["status"],
                    r.get("last_soh")] for r in only_ours]))
        add("")
        add("이 셀들은 last SOH 가 0.825 미만이라 상위 코드의 폐기 분기를 타지 않습니다.")
        add("그런데도 배포 JSON 에 키가 없습니다. 관찰된 사실만 적습니다.")
        add("")
    if mismatch:
        add(f"불일치 {len(mismatch)}셀:")
        add("")
        shown = mismatch[:80]
        add(table(["서브셋", "셀", "경로", "재현", "배포", "차이", "상태"],
                  [[r["subset"], r["cell"], r["route"], r["label"], r["theirs"],
                    r.get("delta"), r["status"]] for r in shown]))
        if len(mismatch) > len(shown):
            add("")
            add(f"위는 앞 {len(shown)}개입니다. 전체 {len(mismatch)}개는 `nb03_mismatch.json` 에 있습니다.")
    else:
        add("불일치 셀이 없습니다. 재현값과 배포값이 갈리는 셀은 나오지 않았습니다.")
    add("")

    # --- 6-3 -------------------------------------------------------------
    add("---")
    add("")
    add("## 11. `MICH_EXP` — `50-100` 6셀 [중점]")
    add("")
    headers = ["셀", "SOC_interval 실제값", "span", "nominal 사용값", "사이클",
               "첫 SOH", "마지막 SOH", "곡선 최소 SOH", "판정 상태", "재현 라벨",
               "배포 라벨", "대조", "nospan 상태", "nospan 라벨", "nospan 곡선 최소"]
    add(table(headers, _focus_rows(result, FOCUS_MICH_EXP, nospan_index)))
    add("")
    add("### 대조군 — 전류·온도 같고 SOC 구간만 `0-100`")
    add("")
    add(table(headers, _focus_rows(result, FOCUS_MICH_EXP_CONTROL, nospan_index)))
    add("")
    info = result["label_files"].get("MICH_EXP") or {}
    mich_cells = sorted(r["cell"] for r in cells if r["subset"] == "MICH_EXP")
    mich_missing = sorted(r["cell"] for r in cells
                          if r["subset"] == "MICH_EXP" and r.get("theirs") is None)
    focus_set = {n + ".pkl" for n in FOCUS_MICH_EXP}
    add(table(["항목", "값"], [
        ["pkl 수", len(mich_cells)],
        ["MICH_EXP_labels.json 키 수", info.get("keys", "—")],
        ["배포 라벨에 없는 셀 수", len(mich_missing)],
        ["빠진 셀이 위 6셀과 같은가", set(mich_missing) == focus_set],
    ]))
    add("")
    if set(mich_missing) != focus_set:
        add("빠진 셀 목록:")
        for name in mich_missing:
            add(f"- `{name}`")
        add("")
    flat = [name for name in FOCUS_MICH_EXP
            if (result["focus_raw"].get(name + ".pkl") or {}).get("soh_min") is not None
            and abs((result["focus_raw"][name + ".pkl"]["soh_min"])
                    - (next((r["first_soh"] for r in cells
                             if r["cell"] == name + ".pkl" and r["first_soh"] is not None), 0))) < 1e-3]
    add("관찰 — 위 6셀은 `첫 SOH` · `마지막 SOH` · `곡선 최소 SOH` 가 사실상 같습니다")
    add(f"({len(flat)}/6 셀에서 세 값의 차가 0.001 미만). 171~557 사이클을 도는 동안")
    add("기록된 방전용량이 거의 변하지 않습니다. `code` 변형에서는 이 값이 0.99 대라")
    add("폐기 임계 0.825 를 넘어 라벨이 만들어지지 않고, `no_soc_span` 변형에서는")
    add("정확히 그 절반인 0.50 아래라 **첫 사이클에서 바로 교차** 해 라벨이 1 이 됩니다.")
    add("어느 쪽도 수명 라벨로 쓸 수 있는 값이 아닙니다. 왜 곡선이 평평한지는 이 파일이")
    add("말하지 않습니다.")
    add("")

    # --- 6-4 -------------------------------------------------------------
    add("---")
    add("")
    add("## 12. `SNL` — `20-80` 4셀 [중점]")
    add("")
    add("이 4셀은 SOC span 나눗셈 대상이면서 동시에 `nominal_capacity` 가 상수 3.2 로")
    add("덮어쓰기되는 대상입니다 (`SNL_18650_NCA_25C_20-80` 접두사 일치,")
    add("`Extract_life_labels.py:111-114`). 두 보정이 같은 셀에 겹칩니다.")
    add("")
    snl_focus = sorted(r["cell"][:-4] for r in cells
                       if r["cell"].startswith(FOCUS_SNL_PREFIX))
    snl_headers = ["셀", "SOC_interval 실제값", "span", "nominal 원값(pkl)", "nominal 사용값",
                   "사이클", "첫 SOH", "마지막 SOH", "곡선 최소 SOH", "판정 상태", "재현 라벨",
                   "배포 라벨", "대조", "nospan 상태", "nospan 라벨", "nospan 곡선 최소"]
    add(table(snl_headers, _focus_rows(result, snl_focus, nospan_index, snl=True)))
    add("")
    snl_rows = [r for r in cells if r["subset"] == "SNL"]
    snl_cens = [r for r in snl_rows if "폐기" in r["status"] or "외삽" in r["status"]]
    snl_aband = [r for r in snl_rows if "폐기" in r["status"]]
    snl_absent = [r for r in snl_rows if r.get("theirs") is None]
    focus_nominals = {result["focus_raw"][r["cell"]]["nominal_in_pkl"]
                      for r in snl_rows if r["cell"].startswith(FOCUS_SNL_PREFIX)
                      and r["cell"] in result["focus_raw"]}
    add(table(["항목", "값"], [
        ["SNL 폐기(≥0.825) 셀 수", len(snl_aband)],
        ["SNL 폐기+외삽 셀 수", len(snl_cens)],
        ["SNL 배포 라벨에 키 없는 셀 수", len(snl_absent)],
        ["그중 `20-80_0.5-0.5C` 4셀", sum(1 for r in snl_cens
                                        if r["cell"].startswith(FOCUS_SNL_PREFIX))],
        ["4셀이 중도절단에 들어 있는가",
         f"{sum(1 for r in snl_cens if r['cell'].startswith(FOCUS_SNL_PREFIX))}/4"],
        ["4셀의 pkl 원 nominal 값", ", ".join(_fmt(v) for v in sorted(focus_nominals))],
        ["덮어쓰기 상수", "3.2"],
        ["덮어쓰기가 값을 바꾸는가", focus_nominals != {3.2}],
    ]))
    add("")
    add("`덮어쓰기가 값을 바꾸는가` 가 `아니오` 면, 이 4셀에서는 상수 3.2 와 pkl 원값이")
    add("같아 nominal 덮어쓰기가 결과에 영향을 주지 않는다는 뜻입니다. 그래도 두 보정이")
    add("겹치는 셀이라는 사실은 그대로입니다 — span 나눗셈은 여전히 걸립니다.")
    add("")
    if snl_cens:
        add("SNL 중도절단 셀 목록 (폐기 + 외삽):")
        add("")
        add(table(["셀", "상태", "마지막 SOH", "배포 라벨", "20-80 4셀"],
                  [[r["cell"], r["status"], r.get("last_soh"),
                    "있음" if r.get("theirs") is not None else "없음",
                    r["cell"].startswith(FOCUS_SNL_PREFIX)]
                   for r in sorted(snl_cens, key=lambda x: x["cell"])]))
        add("")

    # --- 6-5 -------------------------------------------------------------
    add("---")
    add("")
    add("## 13. `CALB` — 재현불가")
    add("")
    calb = [r for r in cells if r["subset"] == "CALB"]
    calb_info = result["label_files"].get("CALB") or {}
    statuses = sorted({r["status"] for r in calb})
    calb_names = {r["cell"] for r in calb}
    add(table(["항목", "값"], [
        ["CALB pkl 수", len(calb)],
        ["전부 재현불가(외부파일)인가", statuses == ["재현불가(외부파일)"]],
        ["나온 상태값", ", ".join(statuses) if statuses else "—"],
        ["배포 CALB_labels.json 키 수", calb_info.get("keys", "—")],
        ["`CALB_45_B254.pkl` 폴더에 있는가", "CALB_45_B254.pkl" in calb_names],
        ["`CALB_45_B254.pkl` 배포 라벨에 있는가",
         "CALB_45_B254.pkl" in (result["dist_only"].get("CALB") or [])],
        ["`CALB_25_T25-2.pkl` 폴더에 있는가", "CALB_25_T25-2.pkl" in calb_names],
        ["배포 라벨에만 있는 CALB 키",
         ", ".join(result["dist_only"].get("CALB") or []) or "없음"],
    ]))
    add("")
    add("CALB 는 상위 코드가 외부 요약 Excel(`汇总表`)의 용량 표를 읽어 λ=0.9 로 라벨을")
    add("만듭니다. 그 Excel 이 배포되지 않아 **계산 경로 자체가 없습니다.** 표에서")
    add("지우지 않고 `구조적불가` 로 남깁니다 — 지우면 \"확인했는데 문제없음\" 과")
    add("구별되지 않습니다.")
    add("")

    # --- 6-6 -------------------------------------------------------------
    add("---")
    add("")
    add("## 14. 재집계 요약")
    add("")
    add("전체는 `findings/recount.json` 에 있습니다. 여기에는 사람이 볼 부분만 옮깁니다.")
    add("")
    totals = recount_data["totals"]
    add(table(["항목", "값"], [
        ["서브셋", totals["subsets"]],
        ["셀", totals["cells"]],
        ["사이클 합", totals["cycles"]],
        ["form_factor 고유값", len(recount_data["form_factor"])],
        ["화학계 삼중조합 고유값", recount_data["chemistry_triplet"]["unique_count"]],
        ["nominal_capacity_in_Ah 고유값", recount_data["nominal_capacity_in_Ah"]["unique_count"]],
        ["SOC_interval 고유값", len(recount_data["soc_interval"])],
        ["charge_protocol 고유값", recount_data["charge_protocol"]["unique_count"]],
        ["charge_protocol multi 비율", recount_data["charge_protocol"]["multi_ratio"]],
        ["discharge_protocol 고유값", recount_data["discharge_protocol"]["unique_count"]],
        ["discharge_protocol multi 비율", recount_data["discharge_protocol"]["multi_ratio"]],
        ["온도 보유 셀 비율", recount_data["temperature_in_C"]["ratio"]],
    ]))
    add("")
    add("### `SOC_interval` 분포 — 값별 셀 수 전부")
    add("")
    subset_of = {m["cell"]: m["subset"] for m in result["metas"]}
    add(table(["SOC_interval", "셀 수", "서브셋"],
              [[key, bucket["cells"],
                ", ".join(sorted({subset_of.get(n, "?") for n in bucket["cell_names"]}))]
               for key, bucket in recount_data["soc_interval"].items()]))
    add("")
    add("`[0, 1]` 이 아닌 값이 SOC span 나눗셈의 대상입니다. 셀 이름은")
    add("`recount.json` 의 `soc_interval.<값>.cell_names` 에 전부 있습니다.")
    add("")
    add("### `form_factor`")
    add("")
    add(table(["값", "셀 수"], list(recount_data["form_factor"].items())))
    add("")
    add("### `nominal_capacity_in_Ah` 분포")
    add("")
    hist = list(recount_data["nominal_capacity_in_Ah"]["histogram"].items())
    add(table(["값", "셀 수"], hist[:25]))
    if len(hist) > 25:
        add("")
        add(f"위는 셀 수가 많은 순으로 앞 25개입니다. 고유값은 모두 {len(hist)}개이고 "
            f"{len(hist) - 25}개를 표에서 잘랐습니다 — 전체는 `recount.json` 의 "
            "`nominal_capacity_in_Ah.histogram` 에 있습니다.")
        tail_cells = sum(count for _, count in hist[25:])
        add(f"잘린 {len(hist) - 25}개 값이 덮는 셀은 {tail_cells}개입니다.")
    add("")
    add("고유값이 많은 이유 하나는 관찰됩니다 — ZN-coin 은 공칭용량이 상수가 아니라")
    add("**10번째 사이클의 방전용량** 이라 셀마다 값이 다릅니다 (`DAT-001`,")
    add("`preprocess_ZNion.py:52`). 그래서 소수 여섯째 자리까지 서로 다른 값이 줄줄이")
    add("나옵니다. 이것이 전부인지는 이 표가 말하지 않습니다.")
    add("")
    add("### 서브셋별 셀 수 · 사이클 수")
    add("")
    add(table(["서브셋", "셀", "사이클 합", "최소", "중앙", "최대"],
              [[name, info["cells"], info["cycles"]["sum"], info["cycles"]["min"],
                info["cycles"]["median"], info["cycles"]["max"]]
               for name, info in recount_data["by_subset"].items()]))
    add("")
    add("### 화학계 삼중조합 (cathode | anode | electrolyte)")
    add("")
    add(table(["조합", "셀 수"],
              list(recount_data["chemistry_triplet"]["values"].items())))
    add("")
    add("### 온도")
    add("")
    temp = recount_data["temperature_in_C"]
    add(table(["항목", "값"], [
        ["온도 보유 셀", f"{temp['cells_with_field']} / {temp['cells_total']}"],
        ["비율", temp["ratio"]],
        ["중앙값 종류 수", len(temp["values"])],
    ]))
    add("")
    add(table(["중앙 온도(°C)", "셀 수"], list(temp["values"].items())))
    add("")
    add("주의 — 온도는 셀 메타가 아니라 사이클마다의 시계열입니다. 필드가 있어도 값이")
    add("전부 `NaN` 인 서브셋과, 값이 전부 `0` 인 서브셋이 함께 있습니다. 전자는")
    add("`온도 보유` 에서 빠지고 후자는 `0` 으로 세어집니다. `0` 이 실측인지 자리표시인지는")
    add("데이터만으로 알 수 없습니다. 서브셋별 상황은 아래와 같습니다.")
    add("")
    temp_by_subset = {}
    for meta in result["metas"]:
        bucket = temp_by_subset.setdefault(meta["subset"], {"cells": 0, "with": 0, "values": set()})
        bucket["cells"] += 1
        if meta["has_temperature"]:
            bucket["with"] += 1
        if meta["temperature_median_C"] is not None:
            bucket["values"].add(meta["temperature_median_C"])
    add(table(["서브셋", "셀", "온도 보유", "중앙 온도 값"],
              [[name, info["cells"], info["with"],
                ", ".join(str(v) for v in sorted(info["values"])) or "—"]
               for name, info in sorted(temp_by_subset.items())]))
    add("")

    # --- 5-2 변형 비교 ----------------------------------------------------
    add("---")
    add("")
    add("## 15. SOC span 변형 비교 (`code` 대 `no_soc_span`)")
    add("")
    diff = variants["rows"]
    changed = [r for r in diff if r["differs"]]
    add(table(["항목", "값"], [
        ["셀 수", len(diff)],
        ["두 변형이 갈리는 셀", len(changed)],
        ["갈리는 서브셋", ", ".join(sorted({r["subset"] for r in changed})) or "—"],
    ]))
    add("")
    if changed:
        shown = changed[:80]
        add(table(["서브셋", "셀", "code last SOH", "code 상태", "code 라벨",
                   "nospan last SOH", "nospan 상태", "nospan 라벨", "배포 라벨"],
                  [[r["subset"], r["cell"], r["code_last_soh"], r["code_status"],
                    r["code_label"], r["nospan_last_soh"], r["nospan_status"],
                    r["nospan_label"], r["theirs"]] for r in shown]))
        if len(changed) > len(shown):
            add("")
            add(f"위는 앞 {len(shown)}개입니다. 전체는 `nb02_variants.json` 에 있습니다.")
    else:
        add("두 변형에서 라벨과 판정이 모두 같습니다.")
    add("")
    add("`no_soc_span` 이 옳다고 주장하는 표가 아닙니다. SOC span 나눗셈을 빼면")
    add("무엇이 갈리는지를 보이는 표입니다 (`LAB-005`).")
    add("")

    # --- 6-7 -------------------------------------------------------------
    add("---")
    add("")
    add("## 16. 확인 불가로 남은 것")
    add("")
    held = set(result["subsets"])
    all_v11 = {"CALB", "CALCE", "HNEI", "HUST", "ISU_ILCC", "MATR", "MICH",
               "MICH_EXP", "NA-ion", "RWTH", "SDU", "SNL", "Stanford",
               "Stanford_2", "Tongji", "UL_PUR", "XJTU", "ZN-coin"}
    missing = sorted(all_v11 - held)
    calb_cells = sum(1 for r in cells if r["subset"] == "CALB")
    add(table(["항목", "왜 확인 불가인가"], [
        ["CALB 라벨 재현",
         f"외부 요약 Excel(`汇总表-L148N58-循环.xlsx`) 미배포 — 구조적불가. "
         f"{calb_cells}셀. 상위 코드는 그 Excel 의 1사이클 용량을 공칭용량으로 쓰고 "
         f"λ=0.9 를 적용합니다 (`Extract_life_labels.py:167-222`)"],
        ["Farasis", "v11 배포 20개 파일에 Farasis 가 없습니다. 서브셋 자체가 부재이며 "
                    "라벨 단위도 사이클이 아니라 EFC 입니다 (`LAB-009`)"],
        ["`total_MICH` pkl 서브셋", "배포 zip 이 아닙니다 (`META-005`). "
                                  "`Life labels/total_MICH_labels.json` 은 배포되지만 "
                                  "pkl 서브셋은 없어 그 라벨과 대조할 pkl 이 없습니다"],
        ["논문 Table 1 서브셋별 셀 수", "이 저장소에 값이 들어와 있지 않아 9절의 "
                                  "`배포 라벨 보유` 열과 직접 대조하지 못했습니다"],
        ["v2 의 일부 수치 정의", "1절 표에서 `정의불명` 으로 표시한 항목들 — "
                            "무엇을 무엇으로 나눈 값인지가 넘어오지 않았습니다"],
        ["미보유 서브셋", ", ".join(missing) if missing
         else "없습니다. v11 배포 18개 pkl 서브셋을 전부 보유했습니다"],
    ]))
    add("")
    xjtu = result.get("xjtu_label_probe")
    if xjtu:
        add("### 배포 `XJTU_labels.json` 파일 자체")
        add("")
        add(table(["항목", "값"], [
            ["키 수", xjtu["keys"]],
            ["`NaN` 리터럴이 원문에 있는가", xjtu["has_nan_literal"]],
            ["비유한 값 개수", xjtu["nonfinite"]],
            ["null 값 개수", xjtu["nulls"]],
        ]))
        add("")
        add("XJTU pkl 을 보유했으므로 재계산 결과는 5절에 있습니다. 이 표는 배포 파일을")
        add("읽기만 한 것입니다 (`LAB-011`).")
        add("")

    add("---")
    add("")
    add("## 17. 산출 파일")
    add("")
    add(table(["파일", "내용"], [
        ["`experiments/results/nb03_cells.json`", "셀 전체 (배포 라벨 대조 포함)"],
        ["`experiments/results/nb03_rollup.json`", "도메인 롤업 + 서브셋 롤업"],
        ["`experiments/results/nb03_mismatch.json`", "불일치 셀"],
        ["`experiments/results/nb03_nolabel.json`", "라벨없음(비유한) 셀"],
        ["`experiments/results/nb03_cells_nospan.json`", "`no_soc_span` 변형 결과"],
        ["`experiments/results/nb03_cells_discharge_denom.json`", "`discharge_denom` 변형 결과"],
        ["`experiments/results/nb02_variants.json`", "변형 나란히 비교"],
        ["`experiments/results/nb04_extras.json`",
         "셀마다 추가로 잰 값 — `cycle_number` · 1사이클 용량 · 방전용량 낙폭 · 곡선 평탄도"],
        ["`experiments/results/nb04_cycle_numbers.json`", "`cycle_number` 서브셋 롤업"],
        ["`experiments/results/nb05_v2_compare.json`", "v2 대조표의 원자료"],
        ["`findings/recount.json`", "메타 재집계"],
        ["`findings/na_ion_crate.json`", "NA-ion 파일명 ↔ C-rate 매핑 (README 파싱)"],
        ["`experiments/results/prev_6subset/`", "직전 6서브셋 440셀 기준 산출물 (보존본)"],
    ]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def _probe_xjtu_labels(labels_dir) -> dict | None:
    """배포 XJTU 라벨 파일만 열어봅니다. pkl 이 없어도 됩니다."""
    path = Path(labels_dir) / "XJTU_labels.json"
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    obj = json.loads(raw)
    nonfinite = sum(1 for v in obj.values()
                    if isinstance(v, float) and not math.isfinite(v))
    return {
        "keys": len(obj),
        "has_nan_literal": "NaN" in raw,
        "nonfinite": nonfinite,
        "nulls": sum(1 for v in obj.values() if v is None),
    }


def run(*, variant: str = "code", do_recount: bool = False, stamp: str = "",
        subsets=None, limit=None, config=None) -> dict:
    """라벨 재현 전체를 돌리고 산출물을 씁니다."""
    config = config if config is not None else load_config()
    extract_dir = config.get("EXTRACT_DIR") or ""
    if not extract_dir:
        raise RuntimeError("config.env 에 EXTRACT_DIR 이 없습니다.")
    root = Path(extract_dir)
    if not root.is_absolute():
        root = (REPO_ROOT / root).resolve()

    # 부분 실행은 LOCK 대상 산출물을 덮어쓰지 않습니다.
    #
    # --subset 이나 --limit 을 준 실행의 결과는 전체 실행의 결과와 다른 것이
    # 당연한데, 파일 이름이 같으면 나중에 그 둘을 구별할 방법이 없습니다.
    # 훑어보기용 실행이 대조표 자리에 앉는 것을 막습니다.
    partial = bool(subsets) or limit is not None
    results_dir = (RESULTS / "scratch") if partial else RESULTS

    result = analyze(root, subsets=subsets, limit=limit)
    result["xjtu_label_probe"] = _probe_xjtu_labels(result["labels_dir"])
    result["partial"] = partial

    cells = result["cells"]
    nospan = result["cells_nospan"]
    dd = result["cells_discharge_denom"]
    diff = variant_diff(cells, nospan)
    diff_dd = variant_diff(cells, dd)
    changed_dd = [r for r in diff_dd if r["differs"]]
    variants = {
        "rows": diff,
        "changed": sum(1 for r in diff if r["differs"]),
        "discharge_denom_rows": changed_dd,
        "discharge_denom_changed": len(changed_dd),
        "discharge_denom_changed_subsets": sorted({r["subset"] for r in changed_dd}),
        "note": ("code 는 상위 코드 그대로, no_soc_span 은 SOC span 나눗셈만 뺀 변형, "
                 "discharge_denom 은 ISU_ILCC 분모만 min(Qd₁, nominal) 로 바꾼 변형입니다 "
                 "(LAB-005 · LAB-017). discharge_denom 이 ISU_ILCC 밖에서 무언가를 바꾸면 "
                 "discharge_denom_changed_subsets 에 그 서브셋이 나타납니다 — "
                 "나타나면 변형이 범위를 넘은 것입니다."),
    }

    written = []
    results_dir.mkdir(parents=True, exist_ok=True)
    written.append(write_json(results_dir / "nb03_cells.json", cells, normalized=True))
    written.append(write_json(results_dir / "nb03_rollup.json", {
        "by_domain": lab.rollup(cells),
        "by_subset": rollup_by(cells, "subset"),
    }, normalized=True))
    written.append(write_json(results_dir / "nb03_mismatch.json",
                              [r for r in cells if r.get("match") == "불일치"],
                              normalized=True))
    # 이 목록만 dict 로 씁니다. 비유한 라벨은 거의 전부 XJTU 경로에서 나오는데
    # XJTU 를 보유하지 않은 실행에서는 빈 배열이 나옵니다. 빈 배열만 남기면
    # "XJTU 를 확인했고 없었다" 로 읽힙니다. 무엇을 훑은 실행인지 함께 씁니다.
    nolabel = [r for r in cells if "라벨없음" in r.get("status", "")
               or "교차없음" in r.get("status", "")]
    written.append(write_json(results_dir / "nb03_nolabel.json", {
        "rows": nolabel,
        "scanned_subsets": result["subsets"],
        "xjtu_scanned": "XJTU" in result["subsets"],
        "note": ("비유한 라벨은 주로 XJTU 경로에서 나옵니다. xjtu_scanned 가 false 면 "
                 "rows 가 비어 있는 것은 XJTU 를 훑지 않았기 때문이지 확인해서 없는 것이 "
                 "아닙니다."),
    }, normalized=True))
    written.append(write_json(results_dir / "nb03_cells_nospan.json", nospan, normalized=True))
    written.append(write_json(results_dir / "nb03_cells_discharge_denom.json", dd,
                              normalized=True))
    written.append(write_json(results_dir / "nb02_variants.json", variants, normalized=True))
    written.append(write_json(results_dir / "nb04_extras.json", {
        "rows": result["extras"],
        "extrap_distance_definition": ex.EXTRAP_DISTANCE_DEF,
        "note": ("셀마다 추가로 잰 값입니다. 라벨 계산 규칙은 여기서 만들지 않습니다 — "
                 "verify/labels.py 가 낸 결과를 그대로 옮겨 담고, 그 밖의 값(cycle_number, "
                 "1사이클 용량, 방전용량 낙폭, 곡선 평탄도)만 여기서 잽니다."),
    }, normalized=True))
    written.append(write_json(results_dir / "nb04_cycle_numbers.json", {
        "by_subset": ex.cycle_number_rollup(result["extras"]),
        "note": ("논문 §2.2 는 라벨을 cycle number 로 정의하고 상위 코드의 첫 교차 분기는 "
                 "배열 인덱스 + 1 을 씁니다 (Extract_life_labels.py:153). paper_* 열이 "
                 "그 차이입니다."),
    }, normalized=True))

    # NA-ion C-rate 매핑 — pkl 메타에 없고 README 표에만 있습니다 (META-008).
    na_map = None
    readme = root / "READMEs" / "NA-ion_README.md"
    na_cells = [r["cell"] for r in cells if r["subset"] == "NA-ion"]
    if readme.exists() and na_cells:
        na_map = na_ion.build_mapping(readme, na_cells)
        target = (results_dir / "na_ion_crate.json") if partial \
            else (REPO_ROOT / "findings" / "na_ion_crate.json")
        written.append(write_json(target, na_map, normalized=True))

    recount_data = rc.recount(root, result["metas"],
                              subsets_present=result["subsets_raw"])
    if do_recount:
        # 부분 실행의 재집계는 findings/recount.json 을 덮어쓰지 않습니다.
        # 그 파일은 "배포 데이터를 이렇게 셌다" 를 뜻하고, 한 서브셋만 센
        # 결과가 그 자리에 앉으면 나머지가 0 인 것처럼 읽힙니다.
        target = (results_dir / "recount.json") if partial \
            else (REPO_ROOT / "findings" / "recount.json")
        written.append(write_json(target, recount_data, normalized=True))

    computed = v2compare.compute(result, recount_data)
    written.append(write_json(results_dir / "nb05_v2_compare.json", {
        "variants": {k: v for k, v in computed["variants"].items()},
        "variants_excl_ISU_ILCC": computed["variants_excl_isu"],
        "excl_ISU_ILCC_candidates": computed["excl_isu_candidates"],
        "extrap_median_by_subset_ours": computed["extrap_ours"]["median"],
        "ISU_ILCC": computed["isu"],
        "RWTH": computed["rwth"],
        "per_subset": computed["per_subset"],
        "extrap_median_by_subset": computed["extrap_median"],
        "censored_cycle_span": {k: list(v) for k, v in computed["censored_span"].items()},
        "counts": {
            "labeled_non_calb": len(computed["labeled_non_calb"]),
            "rule5_label_lt_100": len(computed["rule5_lt"]),
            "rule5_label_le_100": len(computed["rule5_le"]),
            "soc_span_not_one": len(computed["soc_affected"]),
            "first_soh_below_lambda_code_no_calb": len(computed["below_code"]),
            "first_soh_below_lambda_nospan_no_calb": len(computed["below_nospan"]),
            "first_soh_below_lambda_code_all": len(computed["below_code_all"]),
            "first_soh_below_lambda_nospan_all": len(computed["below_nospan_all"]),
            "only_ours": len(computed["only_ours"]),
            "only_ours_observed": len(computed["only_ours_observed"]),
            "curve_flat": len(computed["flat"]),
            "extrap_positive": len(computed["extrap_pos"]),
            "extrap_negative": len(computed["extrap_neg"]),
            "extrap_zero": len(computed["extrap_zero"]),
            "extrap_gt_5pct": len(computed["extrap_gt5"]),
            "extrap_gt_10pct": len(computed["extrap_gt10"]),
        },
        "cell_lists": {
            "ISU_ILCC_discharge_denom_mismatch": computed["isu_dd_mismatch"],
            "rule5_label_le_100": sorted(r["cell"] for r in computed["rule5_le"]),
            "rule5_label_lt_100": sorted(r["cell"] for r in computed["rule5_lt"]),
            "only_ours": sorted(r["cell"] for r in computed["only_ours"]),
            "only_ours_observed": sorted(r["cell"] for r in computed["only_ours_observed"]),
            "curve_flat": sorted(r["cell"] for r in computed["flat"]),
            "extrap_gt_10pct": sorted(r["cell"] for r in computed["extrap_gt10"]),
        },
        "note": ("v2 의 수치와 나란히 놓기 위한 집계입니다. 정의가 넘어오지 않은 항목은 "
                 "LABEL_REPORT.md 1절의 '이 표에서 쓴 정의' 에 이쪽 정의를 적어 두었습니다."),
    }, normalized=True))

    report_text = render(result, stamp=stamp, variants=variants,
                         recount_data=recount_data, computed=computed,
                         na_map=na_map)
    written.append(write_text(results_dir / "LABEL_REPORT.md", report_text))

    return {
        "result": result, "variants": variants, "recount": recount_data,
        "computed": computed, "na_map": na_map,
        "written": written, "variant": variant, "partial": partial,
        "results_dir": results_dir,
    }
