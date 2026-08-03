"""SOH 계산과 그 변형.

상위 코드의 계산 규칙을 옮긴 것입니다. **규칙을 바꾸지 않습니다.**
원본은 ``upstream/BatteryLife/process_scripts/Extract_life_labels.py`` 와
``.../Extract_life_labels_tools/XJTU_tools.py`` 입니다.

변형이 하나 있습니다 — **SOC span 나눗셈을 끌 수 있습니다.**
이 항의 타당성이 미해결이라(``LAB-005``) 두 결과를 나란히 봐야 합니다.
끄는 것이 옳다고 주장하는 것이 아닙니다. 갈리는지 보려는 것입니다.

    soh_curve(data, use_soc_span=True)    상위 코드와 같음
    soh_curve(data, use_soc_span=False)   나눗셈을 뺀 변형
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "nominal_capacity",
    "soc_span_main",
    "soc_span_xjtu",
    "cycle_qd",
    "soh_curve",
    "last_cycle_soh",
    "NOMINAL_OVERRIDES",
]

# 상위 코드가 파일명 접두사로 nominal 을 덮어쓰는 두 건.
# Extract_life_labels.py:111-114. 근거는 코드에만 있고 논문 조사 전입니다
# (findings/registry.yaml LAB-006).
NOMINAL_OVERRIDES = (
    ("RWTH", 1.85),
    ("SNL_18650_NCA_25C_20-80", 3.2),
)


def nominal_capacity(file_name: str, data: dict) -> float:
    """공칭용량. 파일명 접두사에 따른 덮어쓰기를 포함합니다.

    원본: Extract_life_labels.py:111-116
    """
    for prefix, value in NOMINAL_OVERRIDES:
        if file_name.startswith(prefix):
            return float(value)
    return float(data["nominal_capacity_in_Ah"])


def soc_span_main(data: dict) -> float:
    """본 경로의 SOC span.

    원본: Extract_life_labels.py:117-120

        SOC_interval = SOC_interval[1] - SOC_interval[0]
        if SOC_interval == 0:
            SOC_interval = 1

    **부호를 취하지 않습니다.** interval 이 역순으로 저장된 셀이 있으면
    음수가 되고 SOH 부호가 뒤집힙니다. XJTU 경로는 ``abs()`` 를 씁니다
    (아래). 이 차이 자체가 관찰 대상입니다.
    """
    interval = data["SOC_interval"]
    span = interval[1] - interval[0]
    if span == 0:
        span = 1  # fully charge and discharge
    return float(span)


def soc_span_xjtu(data: dict) -> float:
    """XJTU 경로의 SOC span.

    원본: Extract_life_labels_tools/XJTU_tools.py:9-14

    본 경로와 달리 ``abs()`` 를 취하고, 비유한값이거나 1e-12 이하면 1.0 을
    씁니다. 본 경로는 정확히 0 일 때만 1 로 바꿉니다.
    """
    interval = data["SOC_interval"]
    span = abs(float(interval[1]) - float(interval[0]))
    if np.isfinite(span) and span > 1e-12:
        return span
    return 1.0


def cycle_qd(cycle: dict, *, xjtu_style: bool = False) -> float:
    """한 사이클의 방전용량.

    본 경로는 ``max(discharge_capacity_in_Ah)`` 하나뿐입니다
    (Extract_life_labels.py:121, 136, 150).

    XJTU 경로는 전류가 음수인 구간만 골라 ``nanmax`` 를 취합니다
    (XJTU_tools.py:17-33). 고를 수 있는 점이 없으면 유한한 전체에서 취합니다.
    """
    discharge = np.asarray(cycle["discharge_capacity_in_Ah"], dtype=float)
    if not xjtu_style:
        return float(np.max(discharge))

    current = np.asarray(cycle["current_in_A"], dtype=float)
    n = min(len(current), len(discharge))
    if n == 0:
        return float("nan")
    current, discharge = current[:n], discharge[:n]
    mask = np.isfinite(current) & np.isfinite(discharge)
    if not np.any(mask):
        return float("nan")
    discharge_mask = mask & (current < 0)
    values = discharge[discharge_mask] if np.any(discharge_mask) else discharge[mask]
    return float(np.nanmax(values))


def soh_curve(data, file_name: str = "", *, use_soc_span: bool = True,
              xjtu_style: bool = False):
    """전 사이클의 (사이클번호, SOH) 곡선.

    Parameters
    ----------
    use_soc_span
        ``False`` 면 SOC span 나눗셈을 뺍니다 (``LAB-005`` 변형).
    xjtu_style
        ``True`` 면 XJTU 경로의 span·Qd 규칙을 씁니다.

    Returns
    -------
    (cycle_numbers, soh_values) : 둘 다 float 배열

    사이클 번호는 pkl 의 ``cycle_number`` 필드를 씁니다. 정수로 바꿀 수
    없으면 ``i + 1`` 로 대체합니다 (XJTU_tools.py:40-44).

    **본 경로의 상위 코드는 사이클 번호를 이렇게 쓰지 않습니다.** 첫 교차
    분기는 ``correct_cycle_index + 1`` (배열 인덱스), 외삽 분기는
    ``range(len-20, len)`` 기반 번호를 씁니다. 그 차이는 labels.py 가
    경로별로 재현합니다. 여기서는 곡선을 보기 위한 번호입니다.
    """
    nominal = nominal_capacity(file_name, data)
    span = (soc_span_xjtu(data) if xjtu_style else soc_span_main(data)) if use_soc_span else 1.0

    numbers, values = [], []
    for i, cycle in enumerate(data["cycle_data"]):
        try:
            number = int(cycle["cycle_number"])
        except (KeyError, TypeError, ValueError):
            number = i + 1
        qd = cycle_qd(cycle, xjtu_style=xjtu_style)
        if not np.isfinite(nominal) or nominal <= 0:
            soh = float("nan")
        else:
            soh = qd / nominal / span
        numbers.append(float(number))
        values.append(float(soh))
    return np.asarray(numbers, dtype=float), np.asarray(values, dtype=float)


def last_cycle_soh(data, file_name: str = "", *, use_soc_span: bool = True) -> float:
    """마지막 사이클의 SOH. 폐기 임계(0.825) 판정에 쓰이는 값입니다.

    원본: Extract_life_labels.py:110, 121 — ``cycle_data[-1]`` 하나만 봅니다.
    곡선의 최솟값이 아니라 **마지막 사이클** 이라는 점이 중요합니다.
    용량이 되살아난 셀은 곡선이 0.8 아래로 내려갔더라도 여기서 폐기됩니다.
    """
    nominal = nominal_capacity(file_name, data)
    span = soc_span_main(data) if use_soc_span else 1.0
    qd = cycle_qd(data["cycle_data"][-1])
    return float(qd / nominal / span)
