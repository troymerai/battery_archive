"""데이터셋 보고서 v2 의 수치와 이번 재현값을 항목별로 나란히 놓습니다.

**여기에는 원인이 없습니다.** v2 가 낸 값과 이번에 계산한 값을 같은 줄에
놓고, 갈리면 갈린다고 적고, 어느 셀에서 갈리는지 목록으로 짚습니다.

정의가 지시문에 없는 항목
-------------------------
v2 의 수치 중 일부는 **무엇을 무엇으로 나눈 값인지가 넘어오지 않았습니다.**
그런 항목은 판정을 ``정의불명`` 으로 두고, 이쪽에서 쓴 정의를 표 아래에
그대로 적습니다. 정의를 맞춰 숫자를 맞추지 않습니다 — 그러면 대조가 아니라
끼워 맞추기입니다.

``규칙 5``
----------
지시문의 "하류 규칙 5" 가 이 저장소 문서에 정의되어 있지 않아, 상위 코드에서
같은 뜻을 갖는 자리를 찾아 그것으로 계산했습니다.

- ``Extract_life_labels.py:157-160`` — ``if eol < 100: continue`` 가 **주석
  처리된 채** 남아 있습니다 (``LAB-015`` 에 기록됨).
- ``data_provider/data_loader.py:488`` — ``eol <= self.early_cycle_threshold``
  이면 셀을 통째로 버립니다. ``early_cycle_threshold`` 의 기본값은 100
  (``run_main.py:74``) 이고 학습 스크립트 전부가 100 을 씁니다.

두 자리의 부등호가 다르므로 ``< 100`` 과 ``<= 100`` 을 **둘 다** 셉니다.
"""

from __future__ import annotations

import math

from verify import labels as lab
from verify import na_ion

__all__ = ["compute", "render_sections"]

# 상태 문자열 → 유형. verify/labels.py 가 만드는 값 그대로입니다.
TYPE_OBSERVED = "관측"
TYPE_EXTRAP = "외삽"
TYPE_CENSORED = "중도절단"
TYPE_OTHER = "그밖"

RULE5_THRESHOLD = 100


def type_of(status: str) -> str:
    if status in ("본경로:첫교차", "XJTU:보간"):
        return TYPE_OBSERVED
    if status in ("본경로:외삽", "XJTU:꼬리외삽"):
        return TYPE_EXTRAP
    if status.startswith("본경로:폐기"):
        return TYPE_CENSORED
    return TYPE_OTHER


# ---------------------------------------------------------------------------
# 작은 도구
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


def median(values):
    values = sorted(v for v in values if v is not None and math.isfinite(v))
    if not values:
        return None
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def _tally(pairs) -> str:
    """``{서브셋: 수}`` 를 ``A 3 · B 2`` 형태 한 줄로."""
    items = sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0]))
    return " · ".join(f"{k} {v}" for k, v in items) if items else "없음"


def _count_by(rows, field="subset") -> dict:
    out = {}
    for row in rows:
        out[row[field]] = out.get(row[field], 0) + 1
    return out


def _verdict(v2_value: str, ours: str) -> str:
    return "일치" if str(v2_value).strip() == str(ours).strip() else "불일치"


def _verdict_breakdown(expected_total: int, expected: dict,
                       actual_total: int, actual: dict) -> str:
    """``N — A 3 · B 2`` 꼴 항목의 판정.

    문자열로 비교하면 나열 **순서** 만 달라도 불일치로 나옵니다. 합계와
    서브셋별 값을 각각 봅니다.
    """
    if actual_total != expected_total:
        return "불일치"
    return "일치" if dict(actual) == dict(expected) else "불일치(내역)"


# ---------------------------------------------------------------------------
# 계산
# ---------------------------------------------------------------------------

def compute(result: dict, recount_data: dict) -> dict:
    cells = result["cells"]
    nospan = result["cells_nospan"]
    dd = result["cells_discharge_denom"]
    extras = result.get("extras") or []

    by_cell = {r["cell"]: r for r in cells}
    ns_by_cell = {r["cell"]: r for r in nospan}
    dd_by_cell = {r["cell"]: r for r in dd}
    ex_by_cell = {r["cell"]: r for r in extras}

    non_calb = [r for r in cells if r["subset"] != "CALB"]

    # --- 유형 분포 ---------------------------------------------------------
    types = {}
    for row in non_calb:
        types.setdefault(type_of(row["status"]), []).append(row)

    labeled_by_type = {
        key: sum(1 for r in rows if r.get("theirs") is not None)
        for key, rows in types.items()
    }

    labeled_non_calb = [r for r in non_calb if r.get("theirs") is not None]

    # --- 규칙 5 ------------------------------------------------------------
    rule5_lt = [r for r in labeled_non_calb
                if isinstance(r["theirs"], (int, float)) and r["theirs"] < RULE5_THRESHOLD]
    rule5_le = [r for r in labeled_non_calb
                if isinstance(r["theirs"], (int, float)) and r["theirs"] <= RULE5_THRESHOLD]

    # --- SOC 보정 대상 -----------------------------------------------------
    soc_affected = [r for r in extras
                    if r.get("soc_span") is not None and r["soc_span"] != 1.0]

    # --- 변형별 일치 -------------------------------------------------------
    def match_stats(rows, subset=None, exclude=None):
        chosen = [r for r in rows
                  if (subset is None or r["subset"] == subset)
                  and (exclude is None or r["subset"] not in exclude)]
        comparable = [r for r in chosen if r.get("match") in ("일치", "불일치")]
        hit = sum(1 for r in comparable if r["match"] == "일치")
        return {
            "cells": len(chosen),
            "comparable": len(comparable),
            "match": hit,
            "rate": round(hit / len(comparable), 4) if comparable else None,
        }

    variants = {
        "code": match_stats(cells),
        "no_soc_span": match_stats(nospan),
        "discharge_denom": match_stats(dd),
    }
    variants_excl_isu = {
        "code": match_stats(cells, exclude={"ISU_ILCC"}),
        "no_soc_span": match_stats(nospan, exclude={"ISU_ILCC"}),
        "discharge_denom": match_stats(dd, exclude={"ISU_ILCC"}),
    }

    # v2 의 "ISU_ILCC 제외 시 99.1% (809/816)" 은 분모 816 이 어느 집합인지가
    # 넘어오지 않았습니다. 재현 가능한 후보를 여러 개 내놓고 사람이 고르게
    # 합니다 — 816 이 나오게 정의를 짜맞추지 않습니다.
    def _rate(rows):
        comparable = [r for r in rows if r.get("match") in ("일치", "불일치")]
        hit = sum(1 for r in comparable if r["match"] == "일치")
        return {"match": hit, "comparable": len(comparable),
                "rate": round(hit / len(comparable), 4) if comparable else None}

    base = [r for r in cells if r["subset"] != "ISU_ILCC"]
    excl_isu_candidates = {
        "ISU_ILCC 제외, 전부": _rate(base),
        "ISU_ILCC 제외, 관측 유형만": _rate(
            [r for r in base if type_of(r["status"]) == TYPE_OBSERVED]),
        "ISU_ILCC 제외, 외삽 유형만": _rate(
            [r for r in base if type_of(r["status"]) == TYPE_EXTRAP]),
        "ISU_ILCC · Tongji 제외, 전부": _rate(
            [r for r in base if r["subset"] != "Tongji"]),
        "ISU_ILCC · Tongji 제외, 관측 유형만": _rate(
            [r for r in base if r["subset"] != "Tongji"
             and type_of(r["status"]) == TYPE_OBSERVED]),
        "ISU_ILCC · CALB 제외, 전부": _rate(
            [r for r in base if r["subset"] != "CALB"]),
    }

    isu = {
        "code": match_stats(cells, subset="ISU_ILCC"),
        "no_soc_span": match_stats(nospan, subset="ISU_ILCC"),
        "discharge_denom": match_stats(dd, subset="ISU_ILCC"),
    }
    isu_dd_mismatch = sorted(
        r["cell"] for r in dd
        if r["subset"] == "ISU_ILCC" and r.get("match") == "불일치")
    isu_dd_other = sorted(
        (r["cell"], r.get("match")) for r in dd
        if r["subset"] == "ISU_ILCC" and r.get("match") not in ("일치", "불일치"))

    rwth = {
        "code": match_stats(cells, subset="RWTH"),
        "no_soc_span": match_stats(nospan, subset="RWTH"),
    }

    # --- 1사이클 SOH < λ ---------------------------------------------------
    # CALB 를 넣고 빼는 두 가지를 함께 셉니다. CALB 는 λ 가 0.9 이고 상위
    # 코드가 pkl 이 아니라 외부 Excel 의 용량을 쓰므로, pkl 기준으로 잰 이 값이
    # 상위 코드의 판정과 같은 것이 아닙니다.
    def first_below(field, drop=()):
        out = []
        for row in extras:
            if row["subset"] in drop:
                continue
            value = row.get(field)
            if value is None:
                continue
            if value < lab.lambda_of(row["subset"]):
                out.append(row)
        return out

    below_code_all = first_below("soh_first_code")
    below_nospan_all = first_below("soh_first_nospan")
    below_code = first_below("soh_first_code", drop=("CALB",))
    below_nospan = first_below("soh_first_nospan", drop=("CALB",))
    below_code_set = {r["cell"] for r in below_code}
    only_nospan = [r for r in below_nospan if r["cell"] not in below_code_set]

    # --- 외삽 거리 ---------------------------------------------------------
    # 기준이 둘입니다 (verify/extras.py 참고). 갈리는 것은 Tongji 뿐입니다.
    def extrap_stats(field):
        rows = [r for r in extras if r.get(field) is not None]
        by_subset = {}
        for row in rows:
            by_subset.setdefault(row["subset"], []).append(row[field])
        return {
            "rows": rows,
            "median": {k: median(v) for k, v in sorted(by_subset.items())},
            "gt10": [r for r in rows if r[field] > 0.10],
            "gt5": [r for r in rows if r[field] > 0.05],
            "pos": [r for r in rows if r[field] > 0],
            "neg": [r for r in rows if r[field] < 0],
            "zero": [r for r in rows if r[field] == 0],
        }

    extrap_ours = extrap_stats("extrap_distance")
    extrap_theirs = extrap_stats("extrap_distance_theirs")
    extrap = extrap_theirs["rows"]
    extrap_median = extrap_theirs["median"]
    extrap_gt10 = extrap_theirs["gt10"]
    extrap_gt5 = extrap_theirs["gt5"]
    extrap_pos = extrap_theirs["pos"]
    extrap_neg = extrap_theirs["neg"]
    extrap_zero = extrap_theirs["zero"]

    # --- 중도절단 시점 -----------------------------------------------------
    censored_rows = [r for r in non_calb if type_of(r["status"]) == TYPE_CENSORED]
    censored_span = {}
    for row in censored_rows:
        info = ex_by_cell.get(row["cell"])
        if info is None:
            continue
        censored_span.setdefault(row["subset"], []).append(info["cycles"])
    censored_span = {k: (min(v), max(v), len(v))
                     for k, v in sorted(censored_span.items())}

    # --- 서브셋별 라벨 보유 · 외삽 비중 ------------------------------------
    per_subset = {}
    for row in cells:
        bucket = per_subset.setdefault(row["subset"], {
            "cells": 0, "labeled": 0, "extrap": 0, "observed": 0,
            "censored": 0, "other": 0, "match": 0, "mismatch": 0,
        })
        bucket["cells"] += 1
        if row.get("theirs") is not None:
            bucket["labeled"] += 1
        kind = type_of(row["status"])
        bucket[{TYPE_OBSERVED: "observed", TYPE_EXTRAP: "extrap",
                TYPE_CENSORED: "censored", TYPE_OTHER: "other"}[kind]] += 1
        if row.get("match") == "일치":
            bucket["match"] += 1
        elif row.get("match") == "불일치":
            bucket["mismatch"] += 1
    for bucket in per_subset.values():
        bucket["extrap_ratio"] = (round(bucket["extrap"] / bucket["cells"], 4)
                                  if bucket["cells"] else None)
        # v2 의 "외삽 비중" 은 전 셀이 아니라 **폐기를 뺀 셀** 을 분모로 씁니다
        # (10개 서브셋 전부에서 이 정의로 v2 값이 나옵니다).
        denominator = bucket["cells"] - bucket["censored"]
        bucket["extrap_ratio_noncensored"] = (
            round(bucket["extrap"] / denominator, 4) if denominator else None)

    # --- 규칙으로 설명 안 되는 셀 ------------------------------------------
    # 재현은 됐는데 배포 JSON 에 키가 없는 셀. 유형별로 갈라 둡니다 — v2 의
    # UL_PUR 5셀(153·155·173·268·295)은 이 서브셋의 `우리만있음` 8셀 중
    # **첫 교차로 라벨이 난 5셀** 과 정확히 같고, 나머지 3셀은 외삽입니다.
    # 어느 쪽이 v2 의 정의인지는 지시문에 없어 둘 다 냅니다.
    only_ours = [r for r in cells if r.get("match") == "우리만있음"]
    only_ours_observed = [r for r in only_ours if type_of(r["status"]) == TYPE_OBSERVED]

    # --- 곡선 평탄 ---------------------------------------------------------
    flat = [r for r in extras if r.get("curve_flat_code") is True]

    # --- SOC_interval 분포 -------------------------------------------------
    soc_hist = recount_data["soc_interval"]
    soc_buckets = {key: bucket["cells"] for key, bucket in soc_hist.items()}
    soc_unique_cells = sum(count for count in soc_buckets.values() if count == 1)

    return {
        "by_cell": by_cell, "ns_by_cell": ns_by_cell, "dd_by_cell": dd_by_cell,
        "ex_by_cell": ex_by_cell,
        "cells": cells, "nospan": nospan, "dd": dd, "extras": extras,
        "non_calb": non_calb,
        "types": types, "labeled_by_type": labeled_by_type,
        "labeled_non_calb": labeled_non_calb,
        "rule5_lt": rule5_lt, "rule5_le": rule5_le,
        "soc_affected": soc_affected,
        "variants": variants, "variants_excl_isu": variants_excl_isu,
        "excl_isu_candidates": excl_isu_candidates,
        "below_code_all": below_code_all, "below_nospan_all": below_nospan_all,
        "extrap_ours": extrap_ours, "extrap_theirs": extrap_theirs,
        "isu": isu, "isu_dd_mismatch": isu_dd_mismatch, "isu_dd_other": isu_dd_other,
        "rwth": rwth,
        "below_code": below_code, "below_nospan": below_nospan,
        "only_nospan": only_nospan,
        "extrap": extrap, "extrap_median": extrap_median,
        "extrap_gt10": extrap_gt10, "extrap_gt5": extrap_gt5,
        "extrap_pos": extrap_pos, "extrap_neg": extrap_neg, "extrap_zero": extrap_zero,
        "censored_span": censored_span,
        "per_subset": per_subset,
        "only_ours": only_ours, "only_ours_observed": only_ours_observed,
        "flat": flat,
        "soc_buckets": soc_buckets, "soc_unique_cells": soc_unique_cells,
    }


# ---------------------------------------------------------------------------
# 렌더
# ---------------------------------------------------------------------------

def render_sections(result: dict, computed: dict, recount_data: dict,
                    na_map: dict) -> str:
    c = computed
    lines = []
    add = lines.append

    _v2_table(add, c, recount_data)
    _isu(add, result, c)
    _rwth(add, result, c)
    _ul_pur(add, result, c)
    _xjtu(add, result, c)
    _cycle_numbers(add, result, c)
    _flat_curves(add, result, c)
    _na_ion(add, result, c, na_map)

    return "\n".join(lines)


# --- 1. v2 대조 -------------------------------------------------------------

def _v2_table(add, c, recount_data):
    types = c["types"]
    n_obs = len(types.get(TYPE_OBSERVED, []))
    n_ext = len(types.get(TYPE_EXTRAP, []))
    n_cen = len(types.get(TYPE_CENSORED, []))
    n_oth = len(types.get(TYPE_OTHER, []))
    lb = c["labeled_by_type"]

    soc_by_subset = _count_by(c["soc_affected"])
    rule5_by_subset = _count_by(c["rule5_lt"])
    only_by_subset = _count_by(c["only_ours"])
    diff_by_subset = _count_by(c["only_nospan"])

    ul_unexplained = sorted(
        r["label"] for r in c["only_ours_observed"]
        if r["subset"] == "UL_PUR" and r.get("label") is not None)
    ul_all = sorted(
        r["label"] for r in c["only_ours"]
        if r["subset"] == "UL_PUR" and r.get("label") is not None)

    soc = c["soc_buckets"]
    isu = c["isu"]

    rows = []

    def row(item, v2, ours, verdict=None):
        rows.append([item, v2, ours, verdict if verdict is not None
                     else _verdict(v2, ours)])

    row("유형 분포 (관측 / 외삽 / 중도절단)", "1,084 / 194 / 77",
        f"{n_obs:,} / {n_ext:,} / {n_cen:,}")
    row("위 셋에 안 드는 셀 (외삽불가·교차없음·비유한)", "(v2 미제공)", f"{n_oth:,}", "대조불가")
    row("라벨 있음 (관측 / 외삽 / 절단)", "1,054 / 191 / 0",
        f"{lb.get(TYPE_OBSERVED, 0):,} / {lb.get(TYPE_EXTRAP, 0):,} / {lb.get(TYPE_CENSORED, 0):,}")
    row("라벨 보유 셀 (CALB 제외)", "1,245", f"{len(c['labeled_non_calb']):,}")
    # v2 가 "약 1,209" 로 적어 문자열 비교가 성립하지 않습니다. 수로 봅니다.
    after_rule5 = len(c["labeled_non_calb"]) - len(c["rule5_le"])
    row("하류 규칙 5 적용 후 (배포 라벨 ≤ 100 제거)", "약 1,209", f"{after_rule5:,}",
        "일치" if after_rule5 == 1209 else "불일치")
    row("〃 (배포 라벨 < 100 제거)", "약 1,209",
        f"{len(c['labeled_non_calb']) - len(c['rule5_lt']):,}", "참고")
    row("SOC 보정 영향 셀 (span ≠ 1)",
        "239 (17.3%) — RWTH 48 · SNL 4 · MICH_EXP 6 · ISU_ILCC 181",
        f"{len(c['soc_affected'])} ({round(100*len(c['soc_affected'])/max(1,len(c['extras'])),1)}%) — {_tally(soc_by_subset)}",
        _verdict_breakdown(239, {"RWTH": 48, "SNL": 4, "MICH_EXP": 6, "ISU_ILCC": 181},
                           len(c["soc_affected"]), soc_by_subset))
    row("RWTH 보정 없음 → 보정", "0/48 → 48/48",
        f"{c['rwth']['no_soc_span']['match']}/{c['rwth']['no_soc_span']['comparable']}"
        f" → {c['rwth']['code']['match']}/{c['rwth']['code']['comparable']}")
    row("전체 일치율 3단계", "68.6% → 75.9% → 84.7%",
        " / ".join(f"{k} {_pct(v['rate'])}" for k, v in c["variants"].items()),
        "정의불명")
    row("ISU_ILCC 일치율 (코드 그대로)", "35.4%",
        f"{_pct(isu['code']['rate'])} ({isu['code']['match']}/{isu['code']['comparable']})",
        "일치" if isu["code"]["rate"] is not None
        and abs(isu["code"]["rate"] - 0.354) < 0.001 else "불일치")
    row("ISU_ILCC 제외 시 일치율", "99.1% (809/816)",
        f"{_pct(c['variants_excl_isu']['code']['rate'])} "
        f"({c['variants_excl_isu']['code']['match']}/{c['variants_excl_isu']['code']['comparable']})",
        "불일치(분모미상)")
    row("**ISU_ILCC 분모를 방전 기준으로**", "239/240",
        f"{isu['discharge_denom']['match']}/{isu['discharge_denom']['comparable']}")
    row("잔여 1셀", "ISU-ILCC_G14C4",
        ", ".join(n[:-4] for n in c["isu_dd_mismatch"]) or "없음")
    row("1사이클 SOH < λ (코드식 / 논문식) — CALB 제외", "7셀 / 218셀",
        f"{len(c['below_code'])}셀 / {len(c['below_nospan'])}셀")
    row("〃 — CALB 포함", "(v2 미제공)",
        f"{len(c['below_code_all'])}셀 / {len(c['below_nospan_all'])}셀", "참고")
    row("차이 셀 내역", "211 — ISU_ILCC 153 · RWTH 48 · MICH_EXP 6 · SNL 4",
        f"{len(c['only_nospan'])} — {_tally(diff_by_subset)}",
        _verdict_breakdown(211, {"ISU_ILCC": 153, "RWTH": 48, "MICH_EXP": 6, "SNL": 4},
                           len(c["only_nospan"]), diff_by_subset))
    row("SOC_interval 고유값", "184종", f"{len(soc)}종")
    row("SOC_interval `[0, 1]`", "1,143", f"{soc.get('[0, 1]', soc.get('[0.0, 1.0]', 0)):,}")
    row("SOC_interval `[0.2, 0.8]`", "52", f"{soc.get('[0.2, 0.8]', 0):,}")
    row("SOC_interval `[0.5, 1]`", "6", f"{soc.get('[0.5, 1]', soc.get('[0.5, 1.0]', 0)):,}")
    row("SOC_interval 그 값을 가진 셀이 하나뿐인 값", "181", f"{c['soc_unique_cells']:,}")
    rule5_le_by_subset = _count_by(c["rule5_le"])
    row("규칙 5 대상인데 라벨 잔존 (배포 라벨 ≤ 100)",
        "36 — ZN 22 · Tongji 9 · MICH_EXP 4 · ISU_ILCC 1",
        f"{len(c['rule5_le'])} — {_tally(rule5_le_by_subset)}",
        _verdict_breakdown(36, {"ZN-coin": 22, "Tongji": 9, "MICH_EXP": 4, "ISU_ILCC": 1},
                           len(c["rule5_le"]), rule5_le_by_subset))
    row("〃 (배포 라벨 < 100)", "(v2 미제공)",
        f"{len(c['rule5_lt'])} — {_tally(rule5_by_subset)}", "참고")
    observed_by_subset = _count_by(c["only_ours_observed"])
    row("규칙으로 설명 안 되는 셀 — 첫 교차만",
        "30 — NA-ion 9 · SDU 16 · UL_PUR 5",
        f"{len(c['only_ours_observed'])} — {_tally(observed_by_subset)}",
        _verdict_breakdown(30, {"NA-ion": 9, "SDU": 16, "UL_PUR": 5},
                           len(c["only_ours_observed"]), observed_by_subset))
    row("〃 — 외삽까지 포함", "(v2 미제공)",
        f"{len(c['only_ours'])} — {_tally(only_by_subset)}", "대조불가")
    row("UL_PUR 미설명 셀의 calc_life (첫 교차만)", "153 · 155 · 173 · 268 · 295",
        " · ".join(str(v) for v in ul_unexplained) or "없음",
        "일치" if ul_unexplained == [153, 155, 173, 268, 295] else "불일치")
    row("〃 (외삽까지 포함)", "(v2 미제공)",
        " · ".join(str(v) for v in ul_all) or "없음", "대조불가")
    gt10_by_subset = _count_by(c["extrap_gt10"])
    ours = c["extrap_ours"]
    row("외삽 거리 > 10% (배포 라벨 기준)", "11셀 (NA-ion 6 · Tongji 5)",
        f"{len(c['extrap_gt10'])}셀 ({_tally(gt10_by_subset)})",
        _verdict_breakdown(11, {"NA-ion": 6, "Tongji": 5},
                           len(c["extrap_gt10"]), gt10_by_subset))
    row("〃 (재현 라벨 기준)", "(v2 미제공)",
        f"{len(ours['gt10'])}셀 ({_tally(_count_by(ours['gt10']))})", "참고")
    row("외삽 거리 > 5% (배포 라벨 기준)", "15셀", f"{len(c['extrap_gt5'])}셀")
    row("〃 (재현 라벨 기준)", "(v2 미제공)", f"{len(ours['gt5'])}셀", "참고")
    row("외삽 거리 부호 분해 (양수 / 음수 / 0) — 배포 라벨 기준", "114 / 24 / 53",
        f"{len(c['extrap_pos'])} / {len(c['extrap_neg'])} / {len(c['extrap_zero'])}")
    row("〃 — 재현 라벨 기준", "(v2 미제공)",
        f"{len(ours['pos'])} / {len(ours['neg'])} / {len(ours['zero'])}", "참고")

    add("---")
    add("")
    add("## 1. 데이터셋 보고서 v2 수치 대조 [최우선]")
    add("")
    add("`v2` 열은 지시문으로 넘어온 값이고 `재현` 열은 이번 실행이 계산한 값입니다.")
    add("판정이 `정의불명` 인 줄은 v2 가 그 수를 **무엇으로 세었는지가 넘어오지")
    add("않아** 대조가 성립하지 않는 항목입니다. 정의를 맞춰 숫자를 맞추지")
    add("않았습니다.")
    add("")
    add(table(["항목", "v2", "재현", "판정"], rows))
    add("")
    scored = [r for r in rows if r[3] != "참고"]
    hit = sum(1 for r in scored if r[3] == "일치")
    miss = sum(1 for r in scored if str(r[3]).startswith("불일치"))
    unclear = len(scored) - hit - miss
    add(f"**대조 대상 {len(scored)}개 항목 중 일치 {hit} · 불일치 {miss} · "
        f"정의불명·대조불가 {unclear}.** (`참고` 로 표시한 {len(rows) - len(scored)}줄은")
    add("v2 값이 없어 대조 대상이 아니며, 정의를 바꾸면 수가 어떻게 달라지는지를")
    add("보이려고 나란히 둔 줄입니다.)")
    add("")
    add("### v2 의 정의를 되찾은 항목")
    add("")
    add("아래 다섯 항목은 처음 계산에서 v2 와 갈렸고, **v2 가 어느 집합을 세었는지를")
    add("찾아** 다시 계산하니 값이 맞았습니다. 숫자를 맞추려고 정의를 고른 것으로")
    add("읽힐 수 있는 자리이므로, 되찾은 정의와 처음 정의를 표에 **둘 다** 남깁니다.")
    add("")
    add(table(["항목", "처음 쓴 정의", "되찾은 정의", "근거"], [
        ["규칙 5", "배포 라벨 < 100", "배포 라벨 ≤ 100",
         "`data_loader.py:488` 의 `eol <= early_cycle_threshold`. 주석 처리된 "
         "`:157-160` 은 `<` 라 부등호가 갈립니다"],
        ["1사이클 SOH < λ", "1,382셀 전부", "CALB 27셀 제외",
         "CALB 는 상위 코드가 pkl 이 아니라 외부 Excel 의 용량을 쓰므로 pkl 기준 값이 "
         "상위 판정과 같은 것이 아닙니다"],
        ["외삽 거리", "재현 라벨 기준", "배포 라벨 기준",
         "두 기준이 갈리는 서브셋은 Tongji 하나뿐입니다 (`LAB-014` 의 +1). "
         "Tongji 중앙값이 0.1311 → 0.1357 로 v2 와 같아집니다"],
        ["외삽 거리 셀 집합", "외삽 194셀 전부", "배포 라벨이 있는 191셀",
         "빠지는 3셀은 UL_PUR 의 외삽 셀로, 배포 JSON 에 키가 없습니다"],
        ["외삽 비중", "외삽 / 전체 셀", "외삽 / (전체 셀 − 폐기)",
         "10개 서브셋 **전부** 에서 이 정의로 v2 값이 나옵니다"],
    ]))
    add("")
    add("되찾지 못한 것이 하나 남습니다 — `ISU_ILCC 제외 시 99.1% (809/816)` 의")
    add("분모 816 입니다. 아래 후보 어느 것도 816 이 되지 않습니다.")
    add("")
    add(table(["후보 집합", "일치", "대조가능", "일치율"],
              [[name, s["match"], s["comparable"], _pct(s["rate"])]
               for name, s in c["excl_isu_candidates"].items()]))
    add("")
    add("816 이 나오게 정의를 짜맞추지 않았습니다. 이 줄은 `불일치(분모미상)` 로")
    add("둡니다. 참고로 이번 실행의 불일치는 ISU_ILCC 155셀과 Tongji 104셀뿐이라,")
    add("그 둘을 빼면 남는 셀이 전부 일치합니다 — 즉 v2 의 99.1% 는 100% 도 89.6% 도")
    add("아닌 중간값이어서, 두 서브셋 중 하나만 뺀 집합으로도 설명되지 않습니다.")
    add("")

    add("### 이 표에서 쓴 정의")
    add("")
    add(table(["항목", "정의"], [
        ["유형 분류", "`관측` = 상태가 `본경로:첫교차` 또는 `XJTU:보간` / "
                    "`외삽` = `본경로:외삽` 또는 `XJTU:꼬리외삽` / "
                    "`중도절단` = `본경로:폐기(>=0.825)` / 그 밖은 `그밖`"],
        ["라벨 있음", "배포 라벨 JSON 에 그 셀의 키가 있고 값이 null·NaN 이 아님"],
        ["CALB 제외", "CALB 27셀은 외부 Excel 미배포로 계산 경로 자체가 없어 뺍니다"],
        ["규칙 5", "`Extract_life_labels.py:157-160` 의 주석 처리된 `if eol < 100: continue` 와 "
                 "`data_provider/data_loader.py:488` 의 `eol <= early_cycle_threshold`(기본 100). "
                 "부등호가 달라 둘 다 셉니다"],
        ["일치율", "분모는 `match` 가 `일치` 또는 `불일치` 인 셀 (배포 키가 없는 셀·재현불가 셀 제외)"],
        ["규칙으로 설명 안 되는 셀",
         "`match` 가 `우리만있음` — 상위 규칙대로면 라벨이 만들어져야 하는데 배포 JSON 에 "
         "키가 없는 셀. v2 의 UL_PUR 5셀이 이 서브셋 8셀 중 **첫 교차** 5셀과 정확히 "
         "같아, 유형을 첫 교차로 좁힌 줄과 외삽까지 넣은 줄을 둘 다 냅니다"],
        ["1사이클 SOH", "`코드식` = `Qd₁ / nominal / span`, `논문식` = `Qd₁ / nominal` (span 나눗셈 없음). "
                     "λ 는 CALB 만 0.9, 나머지 0.8"],
        ["외삽 거리", "`(라벨 − len(cycle_data)) / len(cycle_data)`. 음수면 외삽 라벨이 "
                   "이미 관측된 구간 안쪽을 가리킵니다. **v2 의 정의가 넘어오지 않아 "
                   "이쪽에서 정했고**, 10개 서브셋 중 9개에서 v2 중앙값과 소수 넷째 자리까지 "
                   "같아 정의가 맞다고 봤습니다. 남은 하나(Tongji)는 라벨을 배포값으로 "
                   "바꾸면 맞습니다"],
        ["외삽 비중", "`외삽 / (전체 셀 − 폐기)`"],
    ]))
    add("")

    add("### 외삽 거리 — 서브셋별 중앙값")
    add("")
    v2_extrap = {"SNL": -0.0079, "MATR": 0.0000, "SDU": 0.0041, "ZN-coin": 0.0240,
                 "HUST": 0.0287, "Tongji": 0.1357, "NA-ion": 0.2215}
    ours_median = c["extrap_ours"]["median"]
    rows = []
    for name in sorted(set(c["extrap_median"]) | set(ours_median) | set(v2_extrap)):
        mine = c["extrap_median"].get(name)
        alt = ours_median.get(name)
        theirs = v2_extrap.get(name)
        rows.append([name,
                     _fmt(theirs) if theirs is not None else "(v2 미제공)",
                     _fmt(mine), _fmt(alt),
                     sum(1 for r in c["extrap"] if r["subset"] == name),
                     "—" if (theirs is None or mine is None)
                     else ("일치" if abs(mine - theirs) < 5e-4 else "불일치")])
    add(table(["서브셋", "v2 중앙값", "재현 (배포 라벨 기준)", "재현 (재현 라벨 기준)",
               "외삽 셀", "판정"], rows))
    add("")
    add("두 기준이 갈리는 서브셋은 **Tongji 하나** 입니다. 다른 서브셋은 재현 라벨과")
    add("배포 라벨이 같아 두 열이 같습니다.")
    add("")

    add("### 중도절단 시점 분포 — 폐기(≥0.825) 셀의 사이클 수")
    add("")
    v2_span = {"Tongji": "30~199", "NA-ion": "120~246", "MICH_EXP": "171~557",
               "ZN-coin": "336~1,440", "SNL": "3,038~4,050"}
    rows = []
    for name in sorted(set(c["censored_span"]) | set(v2_span)):
        info = c["censored_span"].get(name)
        ours = f"{info[0]:,}~{info[1]:,}" if info else "없음"
        rows.append([name, v2_span.get(name, "(v2 미제공)"), ours,
                     info[2] if info else 0])
    add(table(["서브셋", "v2", "재현", "셀 수"], rows))
    add("")

    add("### 서브셋별 라벨 보유 · 외삽 비중")
    add("")
    v2_ratio = {"HUST": 1.0, "UL_PUR": 0.5, "MATR": 0.479, "NA-ion": 0.140,
                "SDU": 0.105, "MICH_EXP": 0.083, "Tongji": 0.074, "SNL": 0.058,
                "XJTU": 0.043, "ZN-coin": 0.025}
    rows = []
    for name in sorted(c["per_subset"]):
        bucket = c["per_subset"][name]
        theirs = v2_ratio.get(name)
        mine = bucket["extrap_ratio_noncensored"]
        rows.append([name, bucket["cells"], bucket["labeled"], bucket["observed"],
                     bucket["extrap"], bucket["censored"], bucket["other"],
                     _fmt(mine), _fmt(bucket["extrap_ratio"]),
                     _fmt(theirs) if theirs is not None else "—",
                     "—" if (theirs is None or mine is None)
                     else ("일치" if abs(mine - theirs) < 1e-3 else "불일치")])
    add(table(["서브셋", "셀", "배포 라벨 보유", "관측", "외삽", "폐기", "그밖",
               "외삽/(셀−폐기)", "외삽/셀", "v2 외삽 비중", "판정"], rows))
    add("")
    add("논문 Table 1 의 서브셋별 셀 수는 이 저장소에 값이 들어와 있지 않아")
    add("`배포 라벨 보유` 열과 직접 대조하지 못했습니다. v2 는 16개 중 13개가")
    add("일치하고 NA-ion +3 · ZN-coin +26 · UL_PUR −8 이라고 적습니다 — 그 셋의")
    add("재현값은 위 표에 있습니다.")
    add("")


def _pct(rate):
    return "—" if rate is None else f"{rate * 100:.1f}%"


# --- 2. ISU_ILCC -----------------------------------------------------------

def _isu(add, result, c):
    add("---")
    add("")
    add("## 2. `ISU_ILCC` 240셀 [중점]")
    add("")
    add("상위 전처리 `preprocess_ISU_ILCC.py` 의 `calculate_soc_start_and_end()` 는")
    add("충전 기준과 방전 기준을 **둘 다** 계산하지만 :164 가 충전 쪽만")
    add("`SOC_interval` 에 저장합니다. 그 결과 `Extract_life_labels.py:121` 의 분모")
    add("`nominal × span` 이 `min(Qc₁, 0.25)` 와 항등이 됩니다. `discharge_denom`")
    add("변형은 그 자리에 `min(Qd₁, nominal)` 을 넣습니다.")
    add("")
    add("> **이름 표기가 서브셋 안에서 갈립니다.** 배포 zip 의 폴더는 `ISU_ILCC/`(밑줄)")
    add("> 인데 셀 파일명은 `ISU-ILCC_G1C1.pkl`(붙임표)이고 배포 라벨 파일도")
    add("> `ISU-ILCC_labels.json`(붙임표)입니다. 상위 `Extract_life_labels.py:230-241`")
    add("> 의 개명 분기에는 ISU 항목이 없으므로, 상위는 `dataset_name` 을 `ISU-ILCC`")
    add("> 로 돌렸고 zip 을 묶을 때만 폴더를 `ISU_ILCC` 로 쓴 것입니다. 이름 규칙이지")
    add("> 계산 규칙이 아니라 대조 직전에 맞췄습니다 — 맞추지 않으면 240셀이 전부")
    add("> `배포라벨없음` 으로 나옵니다.")
    add("")
    add(table(["변형", "셀", "대조가능", "일치", "일치율"],
              [[name, s["cells"], s["comparable"], s["match"], _pct(s["rate"])]
               for name, s in c["isu"].items()]))
    add("")
    if c["isu_dd_other"]:
        add("대조가 성립하지 않은 셀: "
            + ", ".join(f"`{n[:-4]}` ({m})" for n, m in c["isu_dd_other"]))
        add("")

    # 두 변형이 갈리는 셀
    split = []
    for row in c["dd"]:
        if row["subset"] != "ISU_ILCC":
            continue
        code_row = c["by_cell"].get(row["cell"], {})
        if code_row.get("label") == row.get("label"):
            continue
        info = c["ex_by_cell"].get(row["cell"], {})
        split.append([
            row["cell"][:-4], info.get("qc1"), info.get("qd1"),
            info.get("qd1_over_qc1"), info.get("soc_interval_raw"),
            info.get("denom_code"), info.get("denom_discharge"),
            code_row.get("label"), row.get("label"), row.get("theirs"),
            code_row.get("match"), row.get("match"),
        ])
    add(f"### `code` 와 `discharge_denom` 의 라벨이 갈리는 셀 — {len(split)}개")
    add("")
    if split:
        shown = split[:80]
        add(table(["셀", "Qc₁", "Qd₁", "Qd₁/Qc₁", "SOC_interval", "코드 분모",
                   "방전 분모", "code 라벨", "dd 라벨", "배포", "code 대조", "dd 대조"],
                  shown))
        if len(split) > len(shown):
            add("")
            add(f"위는 앞 {len(shown)}개입니다. 전체는 `nb03_cells_discharge_denom.json` 과 "
                "`nb04_extras.json` 에 있습니다.")
    else:
        add("갈리는 셀이 없습니다.")
    add("")

    # 잔여 불일치
    add("### `discharge_denom` 에서도 남는 불일치")
    add("")
    if c["isu_dd_mismatch"]:
        rows = []
        for name in c["isu_dd_mismatch"]:
            row = c["dd_by_cell"].get(name, {})
            info = c["ex_by_cell"].get(name, {})
            rows.append([name[:-4], row.get("label"), row.get("theirs"),
                         row.get("delta"), row.get("status"),
                         info.get("qc1"), info.get("qd1"), info.get("cycles")])
        add(table(["셀", "재현", "배포", "차이", "상태", "Qc₁", "Qd₁", "사이클"], rows))
        add("")
        add("`ISU-ILCC_G14C4` 포함 여부: "
            + ("**예**" if any(n.startswith("ISU-ILCC_G14C4") for n in c["isu_dd_mismatch"])
               else "**아니오**"))
    else:
        add("없습니다 — 240셀 전부 일치했습니다.")
    add("")

    # SOC_interval 고유성
    isu_extras = [r for r in c["extras"] if r["subset"] == "ISU_ILCC"]
    values = {}
    for row in isu_extras:
        values[row["soc_interval_raw"]] = values.get(row["soc_interval_raw"], 0) + 1
    unique = sum(1 for count in values.values() if count == 1)
    add("### `SOC_interval` 고유성")
    add("")
    add(table(["항목", "값"], [
        ["ISU_ILCC 셀", len(isu_extras)],
        ["SOC_interval 고유값 종수", len(values)],
        ["그 값을 가진 셀이 하나뿐인 값", unique],
        ["가장 많은 셀이 공유하는 값", max(values.items(), key=lambda kv: kv[1])[0]
         if values else "—"],
        ["그 값을 가진 셀 수", max(values.values()) if values else "—"],
        ["v2 기대 (고유 SOC_interval 셀)", 181],
    ]))
    add("")


# --- 3. RWTH ---------------------------------------------------------------

def _rwth(add, result, c):
    add("---")
    add("")
    add("## 3. `RWTH` 48셀 [중점]")
    add("")
    add(table(["변형", "셀", "대조가능", "일치", "일치율"],
              [[name, s["cells"], s["comparable"], s["match"], _pct(s["rate"])]
               for name, s in c["rwth"].items()]))
    add("")
    rows = [r for r in c["extras"] if r["subset"] == "RWTH"]
    nominals = sorted({r["nominal_in_pkl"] for r in rows if r["nominal_in_pkl"] is not None})
    spans = sorted({r["soc_span"] for r in rows if r["soc_span"] is not None})
    intervals = sorted({r["soc_interval_raw"] for r in rows})
    add("### 공칭용량 — pkl 원값 대 하드코딩 1.85")
    add("")
    add(table(["항목", "값"], [
        ["RWTH 셀", len(rows)],
        ["pkl `nominal_capacity_in_Ah` 고유값", ", ".join(_fmt(v) for v in nominals) or "—"],
        ["`Extract_life_labels.py:111-112` 하드코딩", "1.85"],
        ["덮어쓰기가 값을 바꾸는가", set(nominals) != {1.85}],
        ["`SOC_interval` 고유값", ", ".join(intervals) or "—"],
        ["span 고유값", ", ".join(_fmt(v) for v in spans) or "—"],
        ["v2 가 적은 세 값", "부록 A.3 3 Ah / 저장소 문서 2.05 Ah / 코드 1.85"],
    ]))
    add("")
    add("`pkl 원값` 이 위 셋 중 어느 것과도 다르면 그 자체가 관찰입니다. 이 표는")
    add("어느 값이 옳은지 말하지 않습니다.")
    add("")
    add("### 48셀 전수")
    add("")
    body = []
    for row in sorted(rows, key=lambda r: r["cell"]):
        code_row = c["by_cell"].get(row["cell"], {})
        ns_row = c["ns_by_cell"].get(row["cell"], {})
        body.append([row["cell"][:-4], row["nominal_in_pkl"], row["nominal_used"],
                     row["soc_interval_raw"], row["soc_span"], row["cycles"],
                     row["soh_first_code"], row["soh_last_code"],
                     code_row.get("label"), ns_row.get("label"),
                     code_row.get("theirs"), code_row.get("match"),
                     ns_row.get("match")])
    add(table(["셀", "nominal(pkl)", "nominal(사용)", "SOC_interval", "span", "사이클",
               "첫 SOH", "마지막 SOH", "code 라벨", "nospan 라벨", "배포",
               "code 대조", "nospan 대조"], body))
    add("")


# --- 4. UL_PUR -------------------------------------------------------------

def _ul_pur(add, result, c):
    add("---")
    add("")
    add("## 4. `UL_PUR` 10셀 [중점]")
    add("")
    rows = [r for r in c["extras"] if r["subset"] == "UL_PUR"]
    body = []
    for row in sorted(rows, key=lambda r: r["cell"]):
        code_row = c["by_cell"].get(row["cell"], {})
        body.append([row["cell"][:-4], code_row.get("status"), code_row.get("label"),
                     code_row.get("theirs"), code_row.get("match"),
                     row["cycles"], row["qd_first"], row["qd_last"],
                     row["qd_max_drop"], row["qd_max_drop_at"],
                     row["soh_first_code"], row["soh_min_code"], row["soh_last_code"]])
    add(table(["셀", "상태", "재현 라벨", "배포 라벨", "대조", "사이클",
               "첫 Qd", "마지막 Qd", "최대 낙폭(Ah)", "낙폭 위치(사이클)",
               "첫 SOH", "최소 SOH", "마지막 SOH"], body))
    add("")
    with_label = [r for r in rows if (c["by_cell"].get(r["cell"], {}) or {}).get("theirs") is not None]
    without = [r for r in rows if (c["by_cell"].get(r["cell"], {}) or {}).get("theirs") is None]
    drops_with = [r["qd_max_drop"] for r in with_label if r["qd_max_drop"] is not None]
    drops_without = [r["qd_max_drop"] for r in without if r["qd_max_drop"] is not None]
    overlap = None
    if drops_with and drops_without:
        overlap = max(drops_with) >= min(drops_without)
    add(table(["항목", "값"], [
        ["배포 라벨 있는 셀", len(with_label)],
        ["배포 라벨 없는 셀", len(without)],
        ["라벨 있는 셀의 최대 낙폭 범위",
         f"{_fmt(min(drops_with))} ~ {_fmt(max(drops_with))}" if drops_with else "—"],
        ["라벨 없는 셀의 최대 낙폭 범위",
         f"{_fmt(min(drops_without))} ~ {_fmt(max(drops_without))}" if drops_without else "—"],
        ["두 무리가 겹치는가", overlap],
        ["v2 — 라벨 없는 8셀", "0.254~0.490 Ah 단일 사이클 급락 후 미회복"],
        ["v2 — 라벨 있는 2셀", "최대 낙폭 0.022 / 0.065 Ah"],
        ["라벨 없는 셀의 재현 라벨",
         " · ".join(str((c["by_cell"].get(r["cell"], {}) or {}).get("label"))
                    for r in sorted(without, key=lambda x: x["cell"]))],
    ]))
    add("")
    add("`두 무리가 겹치는가` 가 `아니오` 면 최대 낙폭만으로 두 무리가 갈립니다.")
    add("갈린다는 것이 원인을 뜻하지는 않습니다 — 이 표는 원인을 적지 않습니다.")
    add("")


# --- 5. XJTU ---------------------------------------------------------------

def _xjtu(add, result, c):
    add("---")
    add("")
    add("## 5. `XJTU` 23셀")
    add("")
    rows = [r for r in c["cells"] if r["subset"] == "XJTU"]
    routes = sorted({r["route"] for r in rows})
    statuses = {}
    for row in rows:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    probe = result.get("xjtu_label_probe") or {}
    add(table(["항목", "값"], [
        ["XJTU 셀", len(rows)],
        ["`route_of()` 판정", ", ".join(routes) or "—"],
        ["선형 보간 경로로 판정되는가", routes == [lab.ROUTE_XJTU]],
        ["상태값 분포", ", ".join(f"{k} {v}" for k, v in sorted(statuses.items()))],
        ["배포 `XJTU_labels.json` 키 수", probe.get("keys", "—")],
        ["원문에 `NaN` 리터럴이 있는가", probe.get("has_nan_literal", "—")],
        ["비유한 값 개수 (`LAB-011`)", probe.get("nonfinite", "—")],
        ["null 값 개수", probe.get("nulls", "—")],
    ]))
    add("")
    body = []
    for row in sorted(rows, key=lambda r: r["cell"]):
        info = c["ex_by_cell"].get(row["cell"], {})
        body.append([row["cell"][:-4], row["status"], row["label"], row["theirs"],
                     row.get("delta"), row["match"], info.get("cycles"),
                     info.get("soc_interval_raw"), info.get("nominal_in_pkl")])
    add(table(["셀", "상태", "재현", "배포", "차이", "대조", "사이클",
               "SOC_interval", "nominal(pkl)"], body))
    add("")


# --- 6. cycle_number -------------------------------------------------------

def _cycle_numbers(add, result, c):
    from verify import extras as ex

    add("---")
    add("")
    add("## 6. `cycle_number` 전 서브셋 집계 [중점]")
    add("")
    add("논문 §2.2 는 라벨을 \"SOH 가 80% 이하가 되는 **cycle number**\" 로 정의합니다.")
    add("상위 코드의 첫 교차 분기는 번호가 아니라 **배열 인덱스 + 1** 을 씁니다")
    add("(`Extract_life_labels.py:153`). 부록 A.1 이 RPT · formation 사이클 제거를")
    add("밝히므로 번호에 결번이 생기고, 그때 둘이 갈립니다.")
    add("")
    add("`논문식 라벨` = 첫 교차가 일어난 자리의 **실제 `cycle_number`**.")
    add("첫 교차 분기를 타지 않은 셀(외삽 · 폐기)에는 정의되지 않아 비웁니다.")
    add("")
    rollup = ex.cycle_number_rollup(c["extras"])
    add(table(["서브셋", "셀", "첫 번호 값별", "결번 있는 셀", "결번 판정가능",
               "논문식 ≠ 코드식", "논문식 ≠ 배포", "논문식 = 배포"],
              [[r["subset"], r["cells"],
                ", ".join(f"{k}:{v}" for k, v in r["first_values"].items()),
                r["non_contiguous"], r["contiguous_known"],
                r["paper_ne_code"], r["paper_ne_theirs"], r["paper_eq_theirs"]]
               for r in rollup]))
    add("")
    totals = {
        "cells": sum(r["cells"] for r in rollup),
        "non_contiguous": sum(r["non_contiguous"] for r in rollup),
        "paper_ne_code": sum(r["paper_ne_code"] for r in rollup),
        "paper_ne_theirs": sum(r["paper_ne_theirs"] for r in rollup),
        "paper_eq_theirs": sum(r["paper_eq_theirs"] for r in rollup),
    }
    add(table(["항목", "값"], [
        ["집계 셀", totals["cells"]],
        ["결번이 있는 셀", totals["non_contiguous"]],
        ["논문식 라벨이 코드식과 다른 셀", totals["paper_ne_code"]],
        ["논문식 라벨이 배포 라벨과 다른 셀", totals["paper_ne_theirs"]],
        ["논문식 라벨이 배포 라벨과 같은 셀", totals["paper_eq_theirs"]],
    ]))
    add("")

    # 결번이 있으면서 첫 번호가 1 인 서브셋
    add("### 결번이 있으면서 `cycle_number[0] = 1` 인 셀")
    add("")
    target = [r for r in c["extras"]
              if r.get("cycle_number_contiguous") is False
              and r.get("cycle_number_first") == 1]
    tally = _count_by(target)
    add(f"{len(target)}셀 — {_tally(tally)}")
    add("")
    split = [r for r in target if r.get("paper_vs_theirs") == "불일치"]
    add(f"그중 논문식 라벨이 배포 라벨과 갈리는 셀: {len(split)} — {_tally(_count_by(split))}")
    add("")

    add("### 교차 지점 — 실제 `cycle_number` · 재현 라벨(1+인덱스) · 배포 라벨")
    add("")
    rows = [r for r in c["extras"] if r.get("paper_label") is not None]
    disagree = [r for r in rows if r.get("paper_vs_theirs") == "불일치"
                or r.get("paper_minus_code")]
    shown = sorted(disagree, key=lambda r: (r["subset"], r["cell"]))[:120]
    if shown:
        add(table(["서브셋", "셀", "코드식(1+인덱스)", "실제 cycle_number", "배포",
                   "실제−코드식", "논문식 대 배포", "결번"],
                  [[r["subset"], r["cell"][:-4], r.get("label_code"),
                    r.get("paper_label"), r.get("theirs"),
                    r.get("paper_minus_code"), r.get("paper_vs_theirs"),
                    r.get("cycle_number_missing")] for r in shown]))
        if len(disagree) > len(shown):
            add("")
            add(f"위는 앞 {len(shown)}개입니다. 전체 {len(disagree)}개는 `nb04_extras.json` 에 있습니다.")
    else:
        add("코드식·논문식·배포가 갈리는 셀이 없습니다.")
    add("")


# --- 7. 곡선 평탄 ----------------------------------------------------------

def _flat_curves(add, result, c):
    add("---")
    add("")
    add("## 7. 곡선 무변화 셀 — 첫 SOH 와 곡선 최소 SOH 의 차 < 0.01")
    add("")
    flat = c["flat"]
    add(f"{len(flat)}셀 — {_tally(_count_by(flat))}")
    add("")
    shown = sorted(flat, key=lambda r: (r["subset"], r["cell"]))[:120]
    if shown:
        add(table(["서브셋", "셀", "사이클", "첫 SOH", "곡선 최소 SOH", "마지막 SOH",
                   "차", "상태", "재현 라벨", "배포 라벨"],
                  [[r["subset"], r["cell"][:-4], r["cycles"], r["soh_first_code"],
                    r["soh_min_code"], r["soh_last_code"],
                    (r["soh_first_code"] - r["soh_min_code"])
                    if (r["soh_first_code"] is not None and r["soh_min_code"] is not None) else None,
                    r.get("status_code"), r.get("label_code"), r.get("theirs")]
                   for r in shown]))
        if len(flat) > len(shown):
            add("")
            add(f"위는 앞 {len(shown)}개입니다. 전체는 `nb04_extras.json` 의 "
                "`curve_flat_code` 로 거를 수 있습니다.")
    else:
        add("해당 셀이 없습니다.")
    add("")
    add("MICH_EXP 6셀에서 관찰됐던 현상이 다른 서브셋에도 있는지를 보는 표입니다.")
    add("왜 곡선이 평평한지는 이 파일이 말하지 않습니다.")
    add("")


# --- 8. NA-ion C-rate ------------------------------------------------------

def _na_ion(add, result, c, na_map):
    add("---")
    add("")
    add("## 8. `NA-ion` C-rate 편중")
    add("")
    if not na_map or not na_map.get("mapping"):
        add("`READMEs/NA-ion_README.md` 를 파싱하지 못했습니다.")
        add("")
        return

    add("### 파싱 규칙 — 표의 어느 열을 무엇으로 읽었는가")
    add("")
    add(table(["항목", "값"], [[k, str(v)] for k, v in na_map["parse_rule"].items()]))
    add("")
    forms = na_map.get("name_form_counts") or {}
    add(table(["항목", "값"], [
        ["README 표 행 수", na_map["readme_rows"]],
        ["NA-ion pkl 셀", na_map["cells_total"]],
        ["매핑된 셀", na_map["cells_mapped"]],
        ["매핑 안 된 셀 (pkl 은 있는데 README 행 없음)", len(na_map["cells_unmapped"])],
        ["README 행만 있고 pkl 이 없는 것", len(na_map["readme_rows_without_cell"])],
        ["v2 가 적은 미매핑 셀 수", 5],
        ["파일명 형태 — 일반형", forms.get(na_ion.FORM_PLAIN, "—")],
        ["파일명 형태 — 타임스탬프형", forms.get(na_ion.FORM_TIMESTAMP, "—")],
    ]))
    add("")
    add("> **v2 와 갈립니다.** v2 는 \"5셀이 매핑되지 않았다\" 고 적고 그 이름을")
    add("> `2750-30_…` · `5000-25_…` 형태라고 밝힙니다. 이번 파싱에서는 **pkl 64셀이")
    add("> 전부 매핑됩니다.** 매핑되지 않는 5개는 셀이 아니라 **README 행** 입니다 —")
    add("> 표에는 있는데 배포 pkl 이 없는 행이고, 이름이 정확히 v2 가 적은 그 형태입니다.")
    add("> 즉 갈리는 것은 5 라는 수가 아니라 **어느 쪽에 5개가 남는가** 입니다.")
    add("")
    if na_map["cells_unmapped"]:
        add("매핑 안 된 셀: " + ", ".join(f"`{n}`" for n in na_map["cells_unmapped"]))
        add("")
    if na_map["readme_rows_without_cell"]:
        add(f"README 행만 있고 pkl 이 없는 행 {len(na_map['readme_rows_without_cell'])}개:")
        add("")
        for name in na_map["readme_rows_without_cell"]:
            add(f"- `{name}.xlsx`")
        add("")
    add("### 온도 열 — 본문 서술과의 어긋남 (`META-009`)")
    add("")
    add("README 본문은 \"There are 12 different charge/discharge protocols in this")
    add("dataset **at 25 degrees Celsius**\" 라고 적습니다. 표의 온도 열은 다음과")
    add("같습니다.")
    add("")
    add(table(["표의 온도(°C)", "행 수"],
              list(na_map["temperature_histogram"].items())))
    add("")

    # --- 구간별 라벨 유무 ---------------------------------------------------
    add("### C-rate 구간별 라벨 유무")
    add("")
    v2_bins = {
        "2.0~3.0C (저속)": (11, 3),
        "4.0~5.8C (중간)": (3, 25),
        "6.0C (고속)": (14, 3),
    }
    def bucketize(only_plain: bool):
        out = {}
        for cell, info in na_map["mapping"].items():
            if only_plain and info["name_form"] != na_ion.FORM_PLAIN:
                continue
            row = c["by_cell"].get(cell)
            if row is None:
                continue
            bucket = out.setdefault(info["bin"], {"none": [], "some": []})
            bucket["none" if row.get("theirs") is None else "some"].append(cell)
        return out

    buckets = bucketize(False)
    plain = bucketize(True)

    order = [name for name, _, _ in na_ion.CRATE_BINS]
    order += sorted(k for k in set(buckets) | set(plain) if k not in order)
    rows, tot = [], [0, 0, 0, 0, 0, 0]
    for name in order:
        b = buckets.get(name, {"none": [], "some": []})
        p = plain.get(name, {"none": [], "some": []})
        v2_none, v2_some = v2_bins.get(name, ("—", "—"))
        rows.append([name, v2_none, v2_some,
                     len(p["none"]), len(p["some"]),
                     len(b["none"]), len(b["some"])])
        if isinstance(v2_none, int):
            tot[0] += v2_none
            tot[1] += v2_some
        tot[2] += len(p["none"]); tot[3] += len(p["some"])
        tot[4] += len(b["none"]); tot[5] += len(b["some"])
    rows.append(["**합계**"] + [f"**{v}**" for v in tot])
    add(table(["C-rate 구간", "v2 라벨 없음", "v2 라벨 있음",
               "재현 없음 (일반형 59셀)", "재현 있음 (일반형 59셀)",
               "재현 없음 (64셀 전부)", "재현 있음 (64셀 전부)"], rows))
    add("")
    add("v2 의 합계 59셀은 **일반형 59셀** 과 같습니다. 타임스탬프형 5셀을 넣으면")
    add("저속 · 중간 구간과 `구간밖 3.9C` 가 늘어납니다 — v2 의 세 구간(2.0~3.0 ·")
    add("4.0~5.8 · 6.0)이 3.0C 초과 4.0C 미만을 덮지 않기 때문입니다.")
    add("")

    # --- 제외 사유 ----------------------------------------------------------
    add("### 라벨 없는 셀의 제외 사유 — 구간별")
    add("")
    add("v2 와 같은 집합(일반형 59셀)으로 먼저 내고, 타임스탬프형 5셀을 넣은 값을")
    add("괄호 안에 둡니다.")
    add("")

    def reasons_of(cells_without):
        out = {}
        for cell in cells_without:
            row = c["by_cell"].get(cell, {})
            label = row.get("label")
            if label is not None and label < RULE5_THRESHOLD:
                key = "규칙 5 대상 (재현 라벨 < 100)"
            elif type_of(row.get("status", "")) == TYPE_CENSORED:
                key = "중도절단 (폐기 ≥ 0.825)"
            else:
                key = f"그밖 ({row.get('status', '?')})"
            out[key] = out.get(key, 0) + 1
        return out

    body = []
    for name in order:
        p = plain.get(name, {"none": [], "some": []})
        b = buckets.get(name, {"none": [], "some": []})
        rp, rb = reasons_of(p["none"]), reasons_of(b["none"])
        merged = []
        for key in sorted(set(rp) | set(rb)):
            a, z = rp.get(key, 0), rb.get(key, 0)
            merged.append(f"{key} {a}" + ("" if a == z else f" ({z})"))
        body.append([name,
                     f"{len(p['none'])}" + ("" if len(p["none"]) == len(b["none"])
                                            else f" ({len(b['none'])})"),
                     " · ".join(merged) or "—"])
    add(table(["C-rate 구간", "라벨 없음 — 일반형 59셀 (64셀 전부)", "사유 분해"], body))
    add("")
    add("v2 는 저속 11셀이 `규칙 5` 8셀 + 중도절단 3셀, 6.0C 14셀이 전부 중도절단이라고")
    add("적습니다. 괄호 밖 값이 v2 와 같은 집합입니다.")
    add("")

    life1 = sorted(cell for cell, info in na_map["mapping"].items()
                   if (c["by_cell"].get(cell, {}) or {}).get("label") == 1)
    rule5_cells = sorted(
        (na_map["mapping"][cell]["c_rate"], cell)
        for cell in na_map["mapping"]
        if (c["by_cell"].get(cell, {}) or {}).get("label") is not None
        and c["by_cell"][cell]["label"] < RULE5_THRESHOLD
        and c["by_cell"][cell].get("theirs") is None)
    add("### 계산 수명 = 1 인 셀과 규칙 5 셀의 C-rate")
    add("")
    add(table(["항목", "값"], [
        ["계산 수명 = 1 인 셀", len(life1)],
        ["그 셀들의 C-rate",
         " · ".join(sorted({str(na_map["mapping"][n]["c_rate"]) + "C" for n in life1})) or "—"],
        ["v2 — 계산 수명 1 은 2C 에만", "2C"],
        ["규칙 5 셀 (라벨 없고 재현 라벨 < 100)", len(rule5_cells)],
        ["그 셀들의 C-rate 범위",
         (f"{min(r for r, _ in rule5_cells)}C ~ {max(r for r, _ in rule5_cells)}C"
          if rule5_cells else "—")],
        ["v2 — 나머지 규칙 5 셀은 2.5C~4.0C", "2.5C~4.0C"],
    ]))
    add("")
    if life1:
        add("계산 수명 = 1 인 셀 목록:")
        add("")
        add(table(["셀", "C-rate", "온도(°C)", "배포 라벨"],
                  [[n[:-4], na_map["mapping"][n]["c_rate"],
                    na_map["mapping"][n]["temperature_C"],
                    (c["by_cell"].get(n, {}) or {}).get("theirs")] for n in life1]))
        add("")
    if rule5_cells:
        add("규칙 5 셀 목록 (라벨 없고 재현 라벨 < 100):")
        add("")
        add(table(["셀", "C-rate", "재현 라벨", "상태"],
                  [[cell[:-4], rate, c["by_cell"][cell]["label"],
                    c["by_cell"][cell]["status"]] for rate, cell in rule5_cells]))
        add("")
