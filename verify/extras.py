"""전수 확장에서 추가로 재는 값들.

``verify/labels.py`` 의 계산 규칙에 손대지 않고, **같은 pkl 을 여는 김에**
따로 재는 것만 모읍니다. 여기에는 판정이 없습니다 — 세고 재기만 합니다.

여기서 재는 것

``cycle_number`` 집계
    논문 §2.2 는 라벨을 "SOH 가 80% 이하가 되는 **cycle number**" 로 정의하고,
    부록 A.1 은 RPT · formation 사이클을 제거했다고 밝힙니다. 제거하면 번호에
    결번이 생깁니다. 반면 상위 코드의 첫 교차 분기는 번호가 아니라 **배열
    인덱스 + 1** 을 씁니다 (``Extract_life_labels.py:153``). 둘이 갈리는 셀이
    몇 개인지가 ``LAB-014`` · ``LAB-016`` · ``META-007`` 의 관찰 대상입니다.

``discharge_denom`` 대조에 쓰는 1사이클 용량
    ``Qc₁`` · ``Qd₁`` 과 두 값의 비. ISU_ILCC 분모가 충전 기준인지 방전 기준인지
    (``LAB-017``) 를 셀 단위로 보이기 위한 값입니다.

사이클 간 방전용량 낙폭
    UL_PUR 8셀이 단일 사이클에서 급락하는지 (LABEL_REPORT.md 4절) 를 재는 값입니다.
    전 셀에서 잽니다 — UL_PUR 만 재면 두 무리가 겹치는지 알 수 없습니다.

곡선 평탄도
    첫 SOH 와 곡선 최소 SOH 의 차. MICH_EXP 6셀에서 관찰된 현상이 다른
    서브셋에도 있는지 (``LAB-012``) 를 훑는 값입니다.

외삽 거리
    외삽 라벨이 마지막 관측 사이클에서 얼마나 떨어져 있는가.
    **정의를 여기에 적어 둡니다** — ``(라벨 − 관측 사이클 수) / 관측 사이클 수``
    입니다. 음수면 외삽 라벨이 이미 관측된 구간 안쪽을 가리킵니다.
"""

from __future__ import annotations

import math

import numpy as np

from verify import soh as soh_mod

__all__ = ["cell_extras", "cycle_number_rollup", "EXTRAP_DISTANCE_DEF"]

EXTRAP_DISTANCE_DEF = (
    "(라벨 − len(cycle_data)) / len(cycle_data). "
    "extrap_distance 는 재현 라벨 기준, extrap_distance_theirs 는 배포 라벨 기준."
)


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _cycle_numbers(cycle_data) -> list:
    """``cycle_number`` 를 정수 목록으로. 정수로 못 바꾸면 ``None`` 을 둡니다."""
    return [_int_or_none((cycle or {}).get("cycle_number")) for cycle in cycle_data]


def _qd_series(cycle_data) -> list:
    out = []
    for cycle in cycle_data:
        try:
            out.append(float(np.max(np.asarray(
                cycle["discharge_capacity_in_Ah"], dtype=float))))
        except (KeyError, TypeError, ValueError):
            out.append(float("nan"))
    return out


def cell_extras(subset: str, file_name: str, data: dict, *,
                rows: dict, theirs) -> dict:
    """셀 하나에서 추가로 재는 값 전부.

    Parameters
    ----------
    rows
        ``{변형이름: 결과행}``. 이미 계산된 라벨 행을 다시 계산하지 않고 씁니다.
    theirs
        배포 라벨 값 (없으면 ``None``).
    """
    cycle_data = data.get("cycle_data") or []
    n = len(cycle_data)
    numbers = _cycle_numbers(cycle_data)
    known = [v for v in numbers if v is not None]

    contiguous = None
    missing_count = None
    if len(known) == n and n > 0:
        contiguous = known == list(range(known[0], known[0] + n))
        strictly_up = all(b > a for a, b in zip(known, known[1:]))
        if strictly_up:
            missing_count = (known[-1] - known[0] + 1) - n

    qd = _qd_series(cycle_data)
    finite_qd = [v for v in qd if math.isfinite(v)]
    drops = [a - b for a, b in zip(qd, qd[1:])
             if math.isfinite(a) and math.isfinite(b)]

    first_index = soh_mod.first_cycle_index(data) if n else None
    qc1 = qd1 = None
    if n:
        try:
            qc1 = _float_or_none(soh_mod.cycle_qc(cycle_data[first_index]))
        except (KeyError, TypeError, ValueError):
            qc1 = None
        qd1 = _float_or_none(soh_mod.cycle_qd(cycle_data[first_index]))

    out = {
        "subset": subset,
        "cell": file_name,
        "cycles": n,
        # --- cycle_number -------------------------------------------------
        "cycle_number_first": numbers[0] if numbers else None,
        "cycle_number_last": numbers[-1] if numbers else None,
        "cycle_number_all_int": len(known) == n,
        "cycle_number_contiguous": contiguous,
        "cycle_number_missing": missing_count,
        # --- 1사이클 용량 --------------------------------------------------
        "first_cycle_index": first_index,
        "first_cycle_number": numbers[first_index] if n else None,
        "qc1": qc1,
        "qd1": qd1,
        "qd1_over_qc1": (qd1 / qc1) if (qc1 and qd1 is not None and qc1 != 0) else None,
        # --- 분모 ----------------------------------------------------------
        "nominal_in_pkl": _float_or_none(data.get("nominal_capacity_in_Ah")),
        "nominal_used": _float_or_none(soh_mod.nominal_capacity(file_name, data)),
        "soc_interval_raw": repr(data.get("SOC_interval")),
        "soc_span": _float_or_none(soh_mod.soc_span_main(data)),
        "denom_code": _float_or_none(soh_mod.code_denominator(file_name, data)),
        "denom_discharge": _float_or_none(
            soh_mod.discharge_denominator(file_name, data)),
        # --- 방전용량 낙폭 --------------------------------------------------
        "qd_first": finite_qd[0] if finite_qd else None,
        "qd_last": finite_qd[-1] if finite_qd else None,
        "qd_max_drop": max(drops) if drops else None,
        "qd_max_drop_at": (drops.index(max(drops)) + 1) if drops else None,
        "theirs": theirs,
    }

    # --- 변형별 SOH 곡선 ---------------------------------------------------
    for variant, use_span in (("code", True), ("nospan", False)):
        try:
            _, values = soh_mod.soh_curve(data, file_name, use_soc_span=use_span)
            finite = values[np.isfinite(values)]
            first = _float_or_none(values[0]) if len(values) else None
            out[f"soh_first_{variant}"] = first
            out[f"soh_min_{variant}"] = _float_or_none(finite.min()) if len(finite) else None
            out[f"soh_last_{variant}"] = _float_or_none(values[-1]) if len(values) else None
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            out[f"soh_first_{variant}"] = None
            out[f"soh_min_{variant}"] = None
            out[f"soh_last_{variant}"] = None

    flat = None
    if out["soh_first_code"] is not None and out["soh_min_code"] is not None:
        flat = abs(out["soh_first_code"] - out["soh_min_code"]) < 0.01
    out["curve_flat_code"] = flat

    # --- 라벨 세 가지와 논문식 라벨 ----------------------------------------
    for variant, row in rows.items():
        out[f"label_{variant}"] = row.get("label")
        out[f"status_{variant}"] = row.get("status")

    code_row = rows.get("code", {})
    label = code_row.get("label")
    status = code_row.get("status") or ""

    paper_label = None
    if "첫교차" in status and label is not None and 1 <= label <= n:
        # 상위 코드의 라벨은 배열 인덱스 + 1 입니다. 논문 §2.2 의 정의대로라면
        # 같은 자리의 cycle_number 를 써야 합니다. 그 두 값을 나란히 둡니다.
        paper_label = numbers[label - 1]
    out["paper_label"] = paper_label
    out["paper_minus_code"] = (paper_label - label) if (
        paper_label is not None and label is not None) else None
    out["paper_vs_theirs"] = None
    if paper_label is not None and isinstance(theirs, (int, float)):
        out["paper_vs_theirs"] = "일치" if paper_label == theirs else "불일치"

    # 외삽 거리를 **두 기준으로** 잽니다.
    #
    #   재현 기준  (라벨 − N) / N,  라벨 = 이번 재현값
    #   배포 기준  (라벨 − N) / N,  라벨 = 배포 JSON 값
    #
    # 두 기준이 갈리는 것은 Tongji 뿐입니다 — 다른 서브셋은 재현값과 배포값이
    # 같아서 같은 수가 나옵니다. Tongji 만 배포 라벨이 재현값보다 정확히 1 크기
    # 때문입니다 (``LAB-014``). 배포 라벨이 없는 셀은 배포 기준에서 빠집니다.
    distance = None
    distance_theirs = None
    if "외삽" in status and n:
        if label is not None:
            distance = (label - n) / n
        if isinstance(theirs, (int, float)):
            distance_theirs = (theirs - n) / n
    out["extrap_distance"] = distance
    out["extrap_distance_theirs"] = distance_theirs

    return out


def cycle_number_rollup(rows: list) -> list:
    """서브셋별 ``cycle_number`` 집계."""
    buckets: dict = {}
    for row in rows:
        bucket = buckets.setdefault(row["subset"], {
            "subset": row["subset"], "cells": 0, "first_values": {},
            "non_contiguous": 0, "contiguous_known": 0,
            "paper_ne_theirs": 0, "paper_eq_theirs": 0,
            "paper_ne_code": 0,
        })
        bucket["cells"] += 1
        key = str(row.get("cycle_number_first"))
        bucket["first_values"][key] = bucket["first_values"].get(key, 0) + 1
        if row.get("cycle_number_contiguous") is False:
            bucket["non_contiguous"] += 1
        if row.get("cycle_number_contiguous") is not None:
            bucket["contiguous_known"] += 1
        if row.get("paper_vs_theirs") == "불일치":
            bucket["paper_ne_theirs"] += 1
        elif row.get("paper_vs_theirs") == "일치":
            bucket["paper_eq_theirs"] += 1
        if row.get("paper_minus_code"):
            bucket["paper_ne_code"] += 1

    out = []
    for name in sorted(buckets):
        bucket = buckets[name]
        bucket["first_values"] = dict(sorted(
            bucket["first_values"].items(), key=lambda kv: (-kv[1], kv[0])))
        out.append(bucket)
    return out
