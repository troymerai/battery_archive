"""배포 데이터 재집계 — 노트북 01 이 하는 일의 헤드리스 판.

**세는 것만 합니다.** 논문 숫자와 맞추거나 해석하는 것은 사람의 일입니다.
여기서는 pkl 이 실제로 무엇을 담고 있는지만 셉니다.

서브셋 개수를 이 파일에 박아두지 않습니다. ``EXTRACT_DIR`` 아래에 있는
것을 셉니다. 보유하지 않은 서브셋은 집계에 나타나지 않으며, 그 사실이
``subsets_present`` 에 남습니다.

집계에서 빼는 것
----------------
``total_MICH`` 는 배포 zip 이 아닙니다 (Zenodo v11 의 20개 파일에 없습니다).
``Life labels/`` 에 ``total_MICH_labels.json`` 이 있고 로컬 작업 폴더에
``total_MICH/`` 사본이 돌아다니지만, pkl 서브셋으로 세면 MICH 와 MICH_EXP
셀이 이중으로 계산됩니다 (``META-005``). 따라서 pkl 트리에 들어 있어도
집계 대상에서 제외하고, 제외했다는 사실을 ``excluded`` 에 남깁니다.

시각 정보를 넣지 않는다
-----------------------
``generated`` 를 null 로 둡니다. 이 파일은 ``LOCK.md`` 의 해시 대상이고,
해시가 시계에 따라 달라지면 "모두가 같은 것을 본다" 가 성립하지 않습니다.
같은 데이터 · 같은 코드면 언제 돌려도 같은 바이트여야 합니다. 언제 돌렸는지는
``CC_REPORT.md`` 와 ``experiments/results/LABEL_REPORT.md`` 에 적습니다.
"""

from __future__ import annotations

import math
import pickle
from pathlib import Path

__all__ = [
    "EXCLUDED_SUBSETS", "NON_PKL_DIRS",
    "cell_meta", "protocol_value", "recount", "iter_subsets",
]

# pkl 서브셋으로 세지 않는 디렉터리.
EXCLUDED_SUBSETS = ("total_MICH",)
NON_PKL_DIRS = ("Life labels", "READMEs")


def iter_subsets(dataset_root) -> list:
    """``EXTRACT_DIR`` 아래에서 pkl 을 가진 서브셋 폴더 이름을 정렬해 돌려줍니다."""
    root = Path(dataset_root)
    if not root.exists():
        return []
    out = []
    for path in sorted(root.iterdir(), key=lambda p: p.name):
        if not path.is_dir() or path.name in NON_PKL_DIRS:
            continue
        if any(path.glob("*.pkl")):
            out.append(path.name)
    return out


# ---------------------------------------------------------------------------
# 값 정규화 — 세기 위해 문자열로 만든다
# ---------------------------------------------------------------------------

def _scalar(value) -> str:
    """값을 세기 위한 문자열.

    ``float(value)`` 로 한 번 내리는 것이 중요합니다. pkl 안의 수는 파이썬
    float 과 ``numpy.float64`` 가 섞여 있고, numpy 2.x 의 ``repr`` 은
    ``np.float64(0.000384)`` 를 냅니다. 그대로 세면 같은 값이 표기 두 가지로
    갈립니다. 정수도 float 으로 내려 ``3`` 과 ``3.0`` 이 갈라지지 않게 합니다.
    """
    if value is None:
        return "(None)"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            return "(비유한)"
        return repr(round(number, 6))
    return str(value)


def protocol_value(protocol) -> str:
    """충·방전 프로토콜 한 셀의 값.

    상위 데이터에서 프로토콜은 dict 의 **리스트** 입니다. 단(stage)이 하나면
    그 단의 non-null 필드를 정렬해 문자열로 만들고, 둘 이상이면 ``multi``
    입니다. ``multi`` 로 뭉뚱그려지는 셀이 몇 %인지가 ``META-004`` 의 쟁점이라
    비율을 따로 셉니다 — 프로토콜 421종을 데이터만으로 구별할 수 있는지가
    거기 달려 있습니다.
    """
    if protocol is None:
        return "(None)"
    if not isinstance(protocol, (list, tuple)):
        return _scalar(protocol)
    if len(protocol) == 0:
        return "(빈리스트)"
    if len(protocol) > 1:
        return "multi"

    stage = protocol[0]
    if not isinstance(stage, dict):
        return _scalar(stage)
    parts = [f"{k}={_scalar(v)}" for k, v in sorted(stage.items()) if v is not None]
    return "{" + ",".join(parts) + "}" if parts else "(전부None)"


def _soc_key(interval) -> str:
    if interval is None:
        return "(None)"
    if isinstance(interval, (list, tuple)):
        return "[" + ", ".join(_scalar(v) for v in interval) + "]"
    return _scalar(interval)


def _has_temperature(cycle_data) -> bool:
    """온도 보유 여부.

    상위 pkl 은 온도를 셀 메타가 아니라 **사이클마다의 시계열** 로 담습니다.
    필드가 있어도 값이 전부 None · NaN 인 셀이 있어, 유한한 값이 하나라도
    있는 셀만 보유로 셉니다.
    """
    for cycle in cycle_data:
        values = cycle.get("temperature_in_C")
        if values is None:
            continue
        if isinstance(values, (int, float)):
            if math.isfinite(float(values)):
                return True
            continue
        for value in values:
            try:
                if value is not None and math.isfinite(float(value)):
                    return True
            except (TypeError, ValueError):
                continue
    return False


def _median_temperature(cycle_data):
    """셀의 대표 온도 — 첫 사이클 유한값의 중앙값을 반올림한 정수.

    운전온도 종류 수(``META-003``)를 세기 위한 것입니다. 시험 온도 설정값이
    아니라 **측정값의 중앙값** 이므로 설정 온도와 다를 수 있습니다.
    """
    for cycle in cycle_data:
        values = cycle.get("temperature_in_C")
        if values is None or isinstance(values, (int, float)):
            continue
        finite = []
        for value in values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                finite.append(number)
        if finite:
            finite.sort()
            middle = len(finite) // 2
            if len(finite) % 2:
                return int(round(finite[middle]))
            return int(round((finite[middle - 1] + finite[middle]) / 2))
    return None


# ---------------------------------------------------------------------------
# 셀 하나의 메타
# ---------------------------------------------------------------------------

def cell_meta(file_name: str, data: dict) -> dict:
    """재집계에 쓰는 셀 하나의 메타. pkl 에 있는 것만 읽습니다."""
    cycle_data = data.get("cycle_data") or []
    return {
        "cell": file_name,
        "cycles": len(cycle_data),
        "form_factor": _scalar(data.get("form_factor")),
        "cathode_material": _scalar(data.get("cathode_material")),
        "anode_material": _scalar(data.get("anode_material")),
        "electrolyte_material": _scalar(data.get("electrolyte_material")),
        "nominal_capacity_in_Ah": _scalar(data.get("nominal_capacity_in_Ah")),
        "soc_interval": _soc_key(data.get("SOC_interval")),
        "charge_protocol": protocol_value(data.get("charge_protocol")),
        "discharge_protocol": protocol_value(data.get("discharge_protocol")),
        "has_temperature": _has_temperature(cycle_data),
        "temperature_median_C": _median_temperature(cycle_data),
        "missing_fields": sorted(
            key for key in (
                "form_factor", "cathode_material", "anode_material",
                "electrolyte_material", "nominal_capacity_in_Ah", "SOC_interval",
                "charge_protocol", "discharge_protocol",
            ) if data.get(key) is None
        ),
    }


# ---------------------------------------------------------------------------
# 집계
# ---------------------------------------------------------------------------

def _tally(rows: list, field: str) -> dict:
    out: dict = {}
    for row in rows:
        out[row[field]] = out.get(row[field], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def _quantiles(numbers: list) -> dict:
    if not numbers:
        return {"n": 0, "min": None, "median": None, "max": None, "sum": 0}
    values = sorted(numbers)
    middle = len(values) // 2
    median = (values[middle] if len(values) % 2
              else (values[middle - 1] + values[middle]) / 2)
    return {
        "n": len(values), "min": values[0], "median": median,
        "max": values[-1], "sum": sum(values),
    }


def summarize(metas: list) -> dict:
    """셀 메타 목록 → 정규화 집계 dict. pkl 을 다시 읽지 않습니다."""
    triplets = {}
    for row in metas:
        key = " | ".join((row["cathode_material"], row["anode_material"],
                          row["electrolyte_material"]))
        triplets[key] = triplets.get(key, 0) + 1

    soc: dict = {}
    for row in metas:
        bucket = soc.setdefault(row["soc_interval"], {"cells": 0, "cell_names": []})
        bucket["cells"] += 1
        bucket["cell_names"].append(row["cell"])
    for bucket in soc.values():
        bucket["cell_names"].sort()
    soc = dict(sorted(soc.items(), key=lambda kv: (-kv[1]["cells"], kv[0])))

    by_subset: dict = {}
    for row in metas:
        bucket = by_subset.setdefault(row["subset"], {"cells": 0, "cycle_counts": []})
        bucket["cells"] += 1
        bucket["cycle_counts"].append(row["cycles"])
    by_subset = {
        name: {"cells": bucket["cells"], "cycles": _quantiles(bucket["cycle_counts"])}
        for name, bucket in sorted(by_subset.items())
    }

    charge = _tally(metas, "charge_protocol")
    discharge = _tally(metas, "discharge_protocol")
    total = len(metas)

    missing: dict = {}
    for row in metas:
        for field in row["missing_fields"]:
            missing[field] = missing.get(field, 0) + 1

    with_temp = sum(1 for row in metas if row["has_temperature"])
    temp_values: dict = {}
    for row in metas:
        if row["temperature_median_C"] is None:
            continue
        key = str(row["temperature_median_C"])
        temp_values[key] = temp_values.get(key, 0) + 1

    return {
        "totals": {
            "subsets": len(by_subset),
            "cells": total,
            "cycles": sum(row["cycles"] for row in metas),
        },
        "by_subset": by_subset,
        "form_factor": _tally(metas, "form_factor"),
        "chemistry_triplet": {
            "unique_count": len(triplets),
            "values": dict(sorted(triplets.items(), key=lambda kv: (-kv[1], kv[0]))),
        },
        "nominal_capacity_in_Ah": {
            "unique_count": len(set(row["nominal_capacity_in_Ah"] for row in metas)),
            "histogram": _tally(metas, "nominal_capacity_in_Ah"),
        },
        "soc_interval": soc,
        "charge_protocol": {
            "unique_count": len(charge),
            "multi_ratio": round(charge.get("multi", 0) / total, 4) if total else None,
            "values": charge,
        },
        "discharge_protocol": {
            "unique_count": len(discharge),
            "multi_ratio": round(discharge.get("multi", 0) / total, 4) if total else None,
            "values": discharge,
        },
        "temperature_in_C": {
            "cells_with_field": with_temp,
            "cells_total": total,
            "ratio": round(with_temp / total, 4) if total else None,
            "values": dict(sorted(temp_values.items(), key=lambda kv: (-kv[1], kv[0]))),
        },
        "missing_fields": dict(sorted(missing.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def recount(dataset_root, metas: list, *, subsets_present: list) -> dict:
    """``findings/recount.json`` 에 쓸 정규화 dict."""
    result = summarize(metas)
    result["status"] = "집계완료"
    result["generated"] = None
    result["dataset_root"] = Path(dataset_root).as_posix()
    result["subsets_present"] = sorted(subsets_present)
    result["excluded"] = list(EXCLUDED_SUBSETS)
    result["notes"] = [
        "보유한 서브셋만 셉니다. 미보유 서브셋은 subsets_present 에 없으며, 여기 없는 것을 0 으로 읽지 마십시오.",
        "generated 를 null 로 둡니다. 이 파일은 LOCK 의 해시 대상이라 시계에 따라 바이트가 달라지면 안 됩니다. 실행 시각은 CC_REPORT.md 에 있습니다.",
        "total_MICH 는 배포 zip 이 아니라 로컬 산출물이므로 제외했습니다 (META-005). 다만 Life labels/ 에는 total_MICH_labels.json 이 실제로 배포되어 있습니다.",
        "temperature_in_C 는 셀 메타가 아니라 사이클마다의 시계열입니다. 유한한 값이 하나라도 있는 셀만 보유로 셉니다.",
        "temperature_median_C 는 측정값의 중앙값이지 시험 설정 온도가 아닙니다.",
        "protocol 값이 multi 인 셀은 단이 둘 이상이라 데이터만으로 종류를 구별할 수 없습니다 (META-004).",
    ]
    return result


def load_metas(dataset_root, subsets=None) -> tuple:
    """pkl 을 읽어 셀 메타 목록을 만듭니다. (metas, subsets_present)

    이 함수는 pkl 을 한 번씩만 엽니다. 라벨 재현과 함께 돌릴 때는
    ``verify/report.py`` 가 자기 루프 안에서 ``cell_meta`` 를 부르므로
    이 함수를 쓰지 않습니다 — 두 번 읽지 않기 위해서입니다.
    """
    root = Path(dataset_root)
    names = list(subsets) if subsets else iter_subsets(root)
    names = [n for n in names if n not in EXCLUDED_SUBSETS]
    metas = []
    for subset in names:
        for path in sorted((root / subset).glob("*.pkl"), key=lambda p: p.name):
            with open(path, "rb") as f:
                data = pickle.load(f)
            row = cell_meta(path.name, data)
            row["subset"] = subset
            metas.append(row)
    return metas, names
