"""라벨 재현.

상위 ``process_scripts/Extract_life_labels.py`` 의 계산 규칙을 옮깁니다.
**규칙을 바꾸지 않습니다.** 값이 배포 라벨과 다르면 그것은 발견이지
고칠 대상이 아닙니다.

라벨 생성 경로가 하나가 아니다
------------------------------

``cal_life_labels()`` 안에 조기 ``return`` 분기가 있어 서브셋마다 다른
경로를 탑니다. 하나의 규칙으로 뭉뚱그리면 **XJTU 와 Farasis 에서 전부
틀린 답이 나옵니다.**

======== ================================== ==============================
서브셋   경로                                재현
======== ================================== ==============================
XJTU     XJTU_tools.extract_xjtu_life_labels 가능 — 마지막 하강 구간 선형 보간
Farasis  Farasis_tools ...from_excel         **불가** — 외부 Excel, 단위가 EFC
CALB     Extract_life_labels.py 내부 분기     **불가** — 외부 Excel 요약표
그 외     cal_life_labels() 본 경로            가능 — SOH 가 λ 아래로 내려간 첫 사이클
======== ================================== ==============================

Farasis · CALB 는 ``재현불가(외부파일)`` 로 분류하고 대조 대상에서
제외하되, 결과 표에는 남겨 그 사실이 보이게 합니다. 지우면 "확인했는데
문제없음" 과 구별되지 않습니다.

XJTU 라벨에는 비유한값(NaN)이 정상적으로 섞입니다. 상위 코드가
``np.isfinite`` 로 유효 개수를 따로 세고 ``80% labels: {valid_count}`` 를
출력합니다. NaN 을 오류로 처리하지 말고 ``라벨없음(비유한)`` 으로 둡니다.

서브셋 개수를 이 파일에 박아두지 않습니다. 디스크에 있는 것을 셉니다.
인수인계 문서의 "나머지 13개" 는 2026-08-03 시점의 이해이며, 배포본에
실제로 몇 개가 있는지는 ``notebooks/01_pkl_structure.ipynb`` 가 셉니다.
"""

from __future__ import annotations

import math
import pickle
from pathlib import Path

import numpy as np

from verify import soh as soh_mod

__all__ = [
    "ROUTE_XJTU", "ROUTE_FARASIS", "ROUTE_CALB", "ROUTE_MAIN",
    "ABANDON_THRESHOLD", "EXTRAPOLATE_LOW", "REGRESS_CYCLE_NUM",
    "LAMBDA_DEFAULT", "LAMBDA_CALB", "LABEL_FILE_RENAME",
    "route_of", "domain_of", "lambda_of",
    "label_cell", "label_subset",
    "load_distributed_labels", "compare", "rollup",
]

# ---------------------------------------------------------------------------
# 확인된 상수 — 전부 Extract_life_labels.py 에서 옮겼습니다
# ---------------------------------------------------------------------------

ABANDON_THRESHOLD = 0.825   # last_cycle_soh >= 0.825 이면 셀을 버린다  (:124)
EXTRAPOLATE_LOW = 0.8       # 0.8 < soh < 0.825 이면 외삽              (:129)
REGRESS_CYCLE_NUM = 20      # 회귀 창 — 마지막 20 사이클                (:132, :203)
LAMBDA_DEFAULT = 0.80       # 기본 λ                                   (:144, :152)
LAMBDA_CALB = 0.90          # CALB 만 λ=0.9                            (:187, :217)

ROUTE_MAIN = "본경로"
ROUTE_XJTU = "XJTU"
ROUTE_FARASIS = "Farasis"
ROUTE_CALB = "CALB"

# 라벨 JSON 파일명 개명 규칙 (Extract_life_labels.py:230-241)
LABEL_FILE_RENAME = {
    "UL_PUR": "UL-PUR",
    "ZNcoin": "ZN-coin",
    "NAion": "NA-ion",
}

# 서브셋 이름 표기가 갈립니다. 상위 스크립트는 dataset_name 으로 ``NAion``,
# ``ZNcoin`` 을 쓰는데 배포 zip 은 ``NA-ion.zip``, ``ZN-coin.zip`` 입니다.
# 어느 쪽으로 불러도 같은 서브셋을 가리키게 합니다.
_ALIASES = {
    "NAion": "NA-ion", "NA_ion": "NA-ion", "NA-ion": "NA-ion",
    "ZNcoin": "ZN-coin", "ZN_coin": "ZN-coin", "ZN-coin": "ZN-coin",
    "UL_PUR": "UL_PUR", "UL-PUR": "UL_PUR",
}

# 4도메인 분할. **이 분할의 근거는 아직 확인되지 않았습니다** (META-006).
# 여기 적힌 것은 배포 파일 이름에서 읽어낸 추정이며, 논문 근거를 찾기
# 전까지는 "우리가 이렇게 묶었다" 이상의 뜻이 없습니다.
_DOMAIN = {
    "NA-ion": "Na-ion",
    "ZN-coin": "Zn-ion",
    "CALB": "CALB",
}


def canonical(subset: str) -> str:
    return _ALIASES.get(subset, subset)


def route_of(subset: str) -> str:
    """이 서브셋이 어느 경로를 타는가.

    ``verify/labels.py`` 는 계산 전에 **먼저 이것을 판정하고 분기합니다.**
    """
    name = canonical(subset)
    if name == "XJTU":
        return ROUTE_XJTU
    if name == "Farasis":
        return ROUTE_FARASIS
    if name == "CALB":
        return ROUTE_CALB
    return ROUTE_MAIN


def lambda_of(subset: str) -> float:
    return LAMBDA_CALB if canonical(subset) == "CALB" else LAMBDA_DEFAULT


def domain_of(subset: str) -> str:
    return _DOMAIN.get(canonical(subset), "Li-ion")


def label_json_name(subset: str) -> str:
    """배포 라벨 JSON 의 파일명."""
    name = canonical(subset)
    for src, dst in LABEL_FILE_RENAME.items():
        if name in (src, dst):
            return f"{dst}_labels.json"
    return f"{name}_labels.json"


# ---------------------------------------------------------------------------
# 역회귀 — fit(SOH, cycle_number)
# ---------------------------------------------------------------------------

def _fit_predict(soh_values, cycle_numbers, target: float):
    """SOH 를 설명변수로, 사이클 번호를 종속변수로 회귀한 뒤 target 에서 예측.

    상위 코드가 ``linear_regressor.fit(total_SOHs, total_cycle_numbers)`` 로
    **역회귀** 합니다 (Extract_life_labels.py:143). 통상적인 방향과 반대이며,
    그 이유는 코드에 적혀 있지 않습니다 (``LAB-003``).

    sklearn 이 있으면 상위와 같은 구현을 쓰고, 없으면 최소제곱으로 대체합니다.
    대체 시 부동소수점 끝자리가 다를 수 있어 반환값에 그 사실을 남깁니다.
    """
    x = np.asarray(soh_values, dtype=float).reshape(-1, 1)
    y = np.asarray(cycle_numbers, dtype=float)
    if len(x) != len(y):
        raise ValueError(f"길이 불일치: SOH {len(x)}개 대 사이클번호 {len(y)}개")

    try:
        from sklearn.linear_model import LinearRegression
    except ImportError:
        slope, intercept = np.polyfit(x.ravel(), y, 1)
        return float(slope * target + intercept), "numpy"

    regressor = LinearRegression()
    regressor.fit(x, y)
    value = regressor.predict(np.array([target]).reshape(-1, 1))[0]
    return float(value), "sklearn"


# ---------------------------------------------------------------------------
# 본 경로
# ---------------------------------------------------------------------------

def _label_main(file_name: str, data: dict, *, use_soc_span: bool = True) -> dict:
    """SOH 가 λ 아래로 내려간 첫 사이클 번호.

    원본: Extract_life_labels.py:106-165.
    """
    cycle_data = data["cycle_data"]
    nominal = soh_mod.nominal_capacity(file_name, data)
    span = soh_mod.soc_span_main(data) if use_soc_span else 1.0
    last_soh = soh_mod.cycle_qd(cycle_data[-1]) / nominal / span

    if last_soh >= ABANDON_THRESHOLD:
        # [0.825, inf) — 데이터셋에서 제외된다. 라벨이 만들어지지 않는다.
        return {"label": None, "status": "본경로:폐기(>=0.825)",
                "last_soh": float(last_soh), "backend": ""}

    if last_soh > EXTRAPOLATE_LOW:
        # (0.8, 0.825) — 마지막 20 사이클로 외삽
        n = len(cycle_data)
        numbers = np.array([i + 1 for i in range(n - REGRESS_CYCLE_NUM, n)], dtype=float)
        sohs = [soh_mod.cycle_qd(c) / nominal / span for c in cycle_data[-REGRESS_CYCLE_NUM:]]
        if len(sohs) != len(numbers):
            # 사이클이 20개 미만이면 상위 코드에서 길이가 어긋납니다.
            # range(n-20, n) 은 n<20 이어도 20개를 만들지만 cycle_data[-20:] 는
            # n개뿐입니다. 상위 코드는 여기서 예외로 죽습니다.
            return {"label": None,
                    "status": f"본경로:외삽불가(사이클 {len(sohs)}개 < 20)",
                    "last_soh": float(last_soh), "backend": ""}
        value, backend = _fit_predict(sohs, numbers, LAMBDA_DEFAULT)
        return {"label": int(value), "status": "본경로:외삽",
                "last_soh": float(last_soh), "backend": backend}

    # (-inf, 0.8] — 첫 교차. 사이클 번호가 아니라 **배열 인덱스 + 1** 입니다.
    for index, cycle in enumerate(cycle_data):
        value = soh_mod.cycle_qd(cycle) / nominal / span
        if value <= EXTRAPOLATE_LOW:
            return {"label": index + 1, "status": "본경로:첫교차",
                    "last_soh": float(last_soh), "backend": ""}

    # 상위 코드는 여기서 eol=None 을 그대로 저장합니다 (주석 처리된 대체
    # 경로가 남아 있습니다 — :157-162). JSON 에 null 로 들어갑니다.
    return {"label": None, "status": "본경로:교차없음(None 저장)",
            "last_soh": float(last_soh), "backend": ""}


# ---------------------------------------------------------------------------
# XJTU 경로
# ---------------------------------------------------------------------------

def _interpolate_last_descending(x_values, y_values, target_y: float) -> float:
    """마지막 하강 교차점을 선형 보간.

    원본: XJTU_tools.py:57-85 (``_linear_interpolate_last_descending_x_at_y``).
    교차가 여러 번이면 **가장 나중 것** 을 씁니다. 본 경로의 "첫 교차" 와
    정반대입니다 (``LAB-008``).
    """
    x = np.asarray(x_values, dtype=float)
    y = np.asarray(y_values, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    if len(x) == 0:
        return float("nan")

    order = np.argsort(x)
    x, y = x[order], y[order]

    crossings = []
    for i in range(1, len(x)):
        y0, y1 = y[i - 1], y[i]
        if y0 > target_y >= y1:
            x0, x1 = x[i - 1], x[i]
            if abs(y1 - y0) < 1e-12:
                crossings.append(float(x1))
            else:
                ratio = (target_y - y0) / (y1 - y0)
                crossings.append(float(x0 + ratio * (x1 - x0)))

    if crossings:
        return max(crossings)
    if y[0] <= target_y:
        return float(x[0])
    return float("nan")


def _extrapolate_from_tail(x_values, y_values, target_y: float,
                           regress_cycle_num: int = REGRESS_CYCLE_NUM):
    """꼬리 20 사이클 외삽.

    원본: XJTU_tools.py:88-108. 본 경로와 달리 사이클이 20개 미만이어도
    ``n = min(20, len(x))`` 로 잘라 쓰므로 길이가 어긋나지 않습니다.
    """
    x = np.asarray(x_values, dtype=float)
    y = np.asarray(y_values, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    if len(x) < 2:
        return float("nan"), ""

    order = np.argsort(x)
    x, y = x[order], y[order]
    n = min(regress_cycle_num, len(x))
    try:
        value, backend = _fit_predict(y[-n:], x[-n:], target_y)
        return float(int(value)), backend
    except Exception:
        return float("nan"), ""


def _label_xjtu(file_name: str, data: dict, *, use_soc_span: bool = True) -> dict:
    """XJTU 라벨. 원본: XJTU_tools.py:111-136."""
    numbers, values = soh_mod.soh_curve(
        data, file_name, use_soc_span=use_soc_span, xjtu_style=True
    )

    life = _interpolate_last_descending(numbers, values, LAMBDA_DEFAULT)
    status, backend = "XJTU:보간", ""

    if not np.isfinite(life):
        finite = values[np.isfinite(values)]
        last_soh = finite[-1] if len(finite) else float("nan")
        if np.isfinite(last_soh) and EXTRAPOLATE_LOW < last_soh < ABANDON_THRESHOLD:
            life, backend = _extrapolate_from_tail(numbers, values, LAMBDA_DEFAULT)
            status = "XJTU:꼬리외삽"
        else:
            status = "XJTU:라벨없음(비유한)"

    if not np.isfinite(life):
        # 상위 코드는 NaN 을 그대로 저장합니다 (cycle_life_label_to_int).
        # 오류가 아닙니다. json.dump 는 이것을 NaN 으로 씁니다.
        return {"label": None, "status": "XJTU:라벨없음(비유한)",
                "last_soh": None, "backend": backend}

    return {"label": int(math.ceil(float(life))), "status": status,
            "last_soh": None, "backend": backend}


# ---------------------------------------------------------------------------
# 셀 하나 / 서브셋 하나
# ---------------------------------------------------------------------------

def label_cell(subset: str, file_name: str, data: dict, *,
               use_soc_span: bool = True) -> dict:
    """셀 하나의 라벨을 재현합니다. 경로 판정이 먼저입니다."""
    route = route_of(subset)

    if route == ROUTE_FARASIS:
        return {"label": None, "status": "재현불가(외부파일)", "route": route,
                "last_soh": None, "backend": "",
                "note": "number_relationship.xlsx 미배포. 단위가 사이클이 아니라 EFC"}

    if route == ROUTE_CALB:
        return {"label": None, "status": "재현불가(외부파일)", "route": route,
                "last_soh": None, "backend": "",
                "note": "汇总表 요약 Excel 미배포. λ=0.9, CALB_45_B254 는 건너뜀"}

    if route == ROUTE_XJTU:
        result = _label_xjtu(file_name, data, use_soc_span=use_soc_span)
    else:
        result = _label_main(file_name, data, use_soc_span=use_soc_span)

    result["route"] = route
    result.setdefault("note", "")
    return result


def label_subset(subset: str, dataset_root, *, use_soc_span: bool = True,
                 limit: int | None = None) -> list:
    """서브셋 하나의 전 셀을 재현합니다.

    Parameters
    ----------
    dataset_root
        압축을 푼 곳. 그 아래에 서브셋 폴더가 있습니다 (``config.env`` 의
        ``EXTRACT_DIR``).
    limit
        앞에서 N개만. 훑어볼 때만 씁니다. 대조표에는 쓰지 마십시오.

    재현불가 경로(Farasis · CALB)는 pkl 을 읽지 않습니다. 읽어도 라벨을
    만들 수 없기 때문입니다. 대신 셀 목록만 남겨 표에서 보이게 합니다.
    """
    root = Path(dataset_root)
    directory = root / canonical(subset)
    if not directory.exists():
        directory = root / subset
    if not directory.exists():
        raise FileNotFoundError(f"서브셋 폴더가 없습니다: {root / canonical(subset)}")

    files = sorted(p.name for p in directory.iterdir() if p.suffix == ".pkl")
    if limit is not None:
        files = files[:limit]

    route = route_of(subset)
    rows = []
    for file_name in files:
        if route in (ROUTE_FARASIS, ROUTE_CALB):
            result = label_cell(subset, file_name, {}, use_soc_span=use_soc_span)
        else:
            with open(directory / file_name, "rb") as f:
                data = pickle.load(f)
            result = label_cell(subset, file_name, data, use_soc_span=use_soc_span)
        rows.append({
            "subset": canonical(subset),
            "domain": domain_of(subset),
            "cell": file_name,
            **result,
        })
    return rows


# ---------------------------------------------------------------------------
# 배포 라벨과의 대조
# ---------------------------------------------------------------------------

def load_distributed_labels(labels_dir, subset: str) -> dict:
    """배포된 ``<subset>_labels.json`` 을 읽습니다.

    폴더 이름에 공백이 있습니다 (``Life labels/``). pathlib 로 다룹니다.
    XJTU 라벨에는 ``NaN`` 이 들어 있을 수 있어 표준 ``json`` 이 float('nan')
    으로 읽습니다. 그것을 ``None`` 으로 바꿔 "라벨 없음" 과 같게 둡니다.
    """
    path = Path(labels_dir) / label_json_name(subset)
    if not path.exists():
        raise FileNotFoundError(f"배포 라벨이 없습니다: {path}")

    import json
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cleaned = {}
    for key, value in raw.items():
        if value is None:
            cleaned[key] = None
        elif isinstance(value, float) and not math.isfinite(value):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned


def compare(rows: list, distributed: dict) -> list:
    """재현값과 배포값을 셀 단위로 맞춥니다.

    ``match`` 열이 붙습니다.

    ============================ =========================================
    값                            뜻
    ============================ =========================================
    ``일치``                      두 값이 같다
    ``불일치``                    두 값이 다르다 — **발견입니다**
    ``우리만있음``                재현은 됐는데 배포 라벨에 없다
    ``배포만있음``                배포 라벨에는 있는데 재현이 안 된다
    ``양쪽없음``                  둘 다 없다 (폐기된 셀 등)
    ``대조제외(재현불가)``        Farasis · CALB
    ``대조제외(라벨없음)``        XJTU 의 정상적인 NaN
    ============================ =========================================
    """
    out = []
    for row in rows:
        row = dict(row)
        ours = row.get("label")
        theirs = distributed.get(row["cell"], "__absent__")
        row["theirs"] = None if theirs == "__absent__" else theirs

        if row["status"].startswith("재현불가"):
            row["match"] = "대조제외(재현불가)"
        elif row["status"] == "XJTU:라벨없음(비유한)":
            row["match"] = "대조제외(라벨없음)"
        elif theirs == "__absent__" and ours is None:
            row["match"] = "양쪽없음"
        elif theirs == "__absent__":
            row["match"] = "우리만있음"
        elif ours is None:
            row["match"] = "배포만있음"
        elif ours == theirs:
            row["match"] = "일치"
        else:
            row["match"] = "불일치"
            row["delta"] = theirs - ours if isinstance(theirs, (int, float)) else None
        out.append(row)
    return out


def rollup(rows: list) -> list:
    """도메인 롤업.

    총 셀 · 라벨 보유 · 중도절단 · 절단 비율.

    "중도절단" 은 ``last_cycle_soh`` 가 0.8 을 넘은 채로 끝난 셀입니다.
    폐기(>=0.825)와 외삽(0.8~0.825)이 여기 들어갑니다. 곧 EOL 에 도달하기
    전에 시험이 멈춘 셀입니다.
    """
    order, buckets = [], {}
    for row in rows:
        domain = row.get("domain", "?")
        if domain not in buckets:
            buckets[domain] = {
                "domain": domain, "cells": 0, "labeled": 0, "censored": 0,
                "abandoned": 0, "extrapolated": 0, "unreproducible": 0,
                "no_label": 0,
            }
            order.append(domain)
        bucket = buckets[domain]
        bucket["cells"] += 1
        status = row.get("status", "")
        if row.get("label") is not None:
            bucket["labeled"] += 1
        if status.startswith("재현불가"):
            bucket["unreproducible"] += 1
        if "폐기" in status:
            bucket["abandoned"] += 1
            bucket["censored"] += 1
        if "외삽" in status:
            bucket["extrapolated"] += 1
            bucket["censored"] += 1
        if "라벨없음" in status or "교차없음" in status:
            bucket["no_label"] += 1

    table = []
    for domain in order:
        bucket = buckets[domain]
        cells = bucket["cells"]
        bucket["censored_ratio"] = round(bucket["censored"] / cells, 4) if cells else None
        table.append(bucket)
    return table
