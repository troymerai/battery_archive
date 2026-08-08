"""보고서용 그림 v2 — figures/report_v2/.

1차(figures/report/)를 덮어쓰지 않습니다. 입력은 오직 figures/report/data/*.csv 입니다.
원자료를 다시 읽지 않고, 학습도 추론도 하지 않습니다.

    C:/Users/taeyo/AppData/Local/Programs/Python/Python312/python.exe -m train.report_figures_v2

규칙
    그림 하나에 메시지 하나. 색 셋 이내. 캡션은 한 줄 40자 이내.
"""

from __future__ import annotations

import csv
import io
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "figures" / "report" / "data"
OUT = ROOT / "figures" / "report_v2"

# ── 색 ───────────────────────────────────────────────────────────────────
GREY = "#9AA0A6"   # 배경이 되는 데이터
NAVY = "#1F4E79"   # 이번 그림이 말하려는 것
WARN = "#D9534F"   # 문제가 있는 대상
TEAL = "#2E8B87"   # 두 번째 계열
INK = "#333333"    # 글자·축
FAINT = "#DDDDDD"  # 옅은 격자

_INSTALLED = {f.name for f in fm.fontManager.ttflist}
KOREAN = next(
    (n for n in ("Malgun Gothic", "NanumGothic", "Gulim", "Batang") if n in _INSTALLED),
    None,
)
if KOREAN:
    plt.rcParams["font.family"] = KOREAN
plt.rcParams.update({
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 200,
    "figure.dpi": 200,
    "axes.grid": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#BBBBBB",
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.labelsize": 9.5,
    "legend.fontsize": 9,
    "font.size": 9,
})

MM = 1.0 / 25.4
W = 160 * MM

CAPTIONS: list[tuple[str, str]] = []
CHECKS: list[str] = []


def L(ko: str, en: str) -> str:
    return ko if KOREAN else en


def rows(name: str) -> list[dict]:
    with (SRC / f"{name}.csv").open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def hgrid(ax) -> None:
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=FAINT, lw=0.7)


def save(fig, stem: str, caption: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    CAPTIONS.append((stem, caption))
    print(f"  {stem}.png / .pdf   캡션 {len(caption)}자: {caption}")


# ── 1 ────────────────────────────────────────────────────────────────────
def fig1() -> None:
    r = rows("fig1_subset_label_agreement")
    full = [x for x in r if x["agreement_pct_over_both"] and float(x["agreement_pct_over_both"]) >= 100]
    isu = next(x for x in r if x["subset"] == "ISU-ILCC")
    tj = next(x for x in r if x["subset"] == "Tongji")
    calb = next(x for x in r if x["subset"] == "CALB")
    n_full = sum(int(x["both"]) for x in full)

    bars = [
        (L(f"완전 일치 {len(full)}개 서브셋", f"{len(full)} subsets, all equal"),
         f"{n_full:,}" + L("셀", ""), 100.0, GREY, f"100%  ({n_full:,}/{n_full:,})"),
        ("ISU-ILCC", "240" + L("셀", ""), float(isu["agreement_pct_over_both"]), WARN,
         f"{float(isu['agreement_pct_over_both']):.1f}%  ({isu['equal']}/{isu['both']})"),
        ("Tongji", "108" + L("셀", ""), float(tj["agreement_pct_over_both"]), WARN,
         f"{float(tj['agreement_pct_over_both']):.1f}%  ({tj['equal']}/{tj['both']})"),
        ("CALB", "27" + L("셀", ""), None, None, L("배포 트리에서는 생성 불가",
                                                   "not generable from shipped tree")),
    ]

    fig, ax = plt.subplots(figsize=(W, 52 * MM))
    ys = [3, 2, 1, 0]
    for y, (name, n, pct, color, txt) in zip(ys, bars):
        if pct is None:
            ax.barh(y, 100, height=0.55, facecolor="none", edgecolor=GREY,
                    linewidth=1.0, linestyle=(0, (3, 2)))
            ax.text(2.5, y, txt, va="center", ha="left", fontsize=9, color=GREY)
        else:
            ax.barh(y, pct, height=0.55, color=color, edgecolor="none")
            ax.text(pct + 1.8, y, txt, va="center", ha="left", fontsize=9,
                    color=INK if color is GREY else WARN)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{n}\n{c}" for n, c, *_ in bars], fontsize=9)
    ax.set_ylim(-0.6, 3.6)
    ax.set_xlim(0, 132)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel(L("배포 라벨 A 와 재생성 라벨 B 의 일치율 (%)",
                    "agreement between label A and label B (%)"))
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=FAINT, lw=0.7)

    save(fig, "fig1_subset_agreement", L("라벨이 갈리는 서브셋은 둘뿐이다",
                                         "Only two subsets disagree"))
    CHECKS.append(f"fig1: 완전 일치 {len(full)}개 서브셋 = {n_full}셀 · "
                  f"ISU-ILCC {isu['equal']}/{isu['both']} · Tongji {tj['equal']}/{tj['both']} · "
                  f"CALB in_a={calb['in_a']} both={calb['both']}")


# ── 2 ────────────────────────────────────────────────────────────────────
def fig2() -> None:
    r = rows("fig2_isu_ilcc_a_vs_b")
    eq = [x for x in r if x["equal"] == "True"]
    df = [x for x in r if x["equal"] != "True"]

    fig, ax = plt.subplots(figsize=(W * 0.68, 78 * MM))
    lim = (12, 6000)
    ax.plot(lim, lim, color="#C9C9C9", lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.scatter([int(x["label_A"]) for x in eq], [int(x["label_B"]) for x in eq],
               s=9, color=GREY, alpha=0.55, linewidths=0, zorder=2,
               label=L(f"일치 {len(eq)}셀", f"equal ({len(eq)})"))
    ax.scatter([int(x["label_A"]) for x in df], [int(x["label_B"]) for x in df],
               s=13, color=WARN, alpha=0.75, linewidths=0, zorder=3,
               label=L(f"불일치 {len(df)}셀", f"differ ({len(df)})"))

    named = {"ISU-ILCC_G14C4.pkl": (8, -12), "ISU-ILCC_G13C1.pkl": (9, -4),
             "ISU-ILCC_G2C4.pkl": (9, 4), "ISU-ILCC_G34C2.pkl": (-8, -14)}
    for cell, off in named.items():
        x = next(v for v in r if v["cell"] == cell)
        ax.annotate(cell.replace("ISU-ILCC_", "").replace(".pkl", ""),
                    (int(x["label_A"]), int(x["label_B"])), textcoords="offset points",
                    xytext=off, fontsize=9, color=INK, zorder=5,
                    ha="right" if off[0] < 0 else "left")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_aspect("equal")
    ax.set_xlabel(L("배포 라벨 A (사이클)", "shipped label A (cycles)"))
    ax.set_ylabel(L("재생성 라벨 B (사이클)", "regenerated label B (cycles)"))
    ax.legend(loc="upper left", frameon=False, borderaxespad=0.2, handletextpad=0.3)

    save(fig, "fig2_isu_ilcc_a_vs_b", L("240셀 중 155셀이 어긋난다",
                                        "155 of 240 cells disagree"))
    CHECKS.append(f"fig2: 일치 {len(eq)} · 불일치 {len(df)} (합 {len(r)})")


# ── 3 ────────────────────────────────────────────────────────────────────
MODELS = ["CPMLP", "CPTransformer"]
SEEDS = [42, 2021, 2024, 7, 1234]


def fig3() -> None:
    from scipy import stats

    r = rows("fig3_conditions_by_seed")
    m = {(x["model"], int(x["seed"]), x["condition"]): float(x["test_mape"]) for x in r}
    assert len(m) == 40

    # (눈금 라벨, 뺄 조건, 더할 조건, 계열)
    comps = [
        (L("시험 A", "test A"), "AA", "BA", "train"),
        (L("시험 B", "test B"), "AB", "BB", "train"),
        (L("학습 A", "train A"), "AA", "AB", "score"),
        (L("학습 B", "train B"), "BA", "BB", "score"),
    ]
    groups = [(0, 1, GREY, L("학습 라벨 A→B", "swap training label")),
              (2, 3, NAVY, L("정답 라벨 A→B", "swap scoring label"))]
    jit = [-0.20, -0.10, 0.0, 0.10, 0.20]

    fig, axes = plt.subplots(1, 2, figsize=(W, 80 * MM), sharey=True)
    for ax, model in zip(axes, MODELS):
        hgrid(ax)
        ax.axhline(0, color="#888888", lw=0.9, zorder=2)
        for i, (lab, a, b, kind) in enumerate(comps):
            color = GREY if kind == "train" else NAVY
            d = [m[(model, s, b)] - m[(model, s, a)] for s in SEEDS]
            ax.scatter([i + j for j in jit], d, s=26, color=color, alpha=0.75,
                       linewidths=0, zorder=4)
            mean = sum(d) / len(d)
            ax.plot([i - 0.30, i + 0.30], [mean, mean], color=color, lw=3.0,
                    solid_capstyle="butt", zorder=5)
            t, p = stats.ttest_rel(
                [m[(model, s, b)] for s in SEEDS], [m[(model, s, a)] for s in SEEDS])
            ptxt = ("p<.0001" if p < 1e-4
                    else f"p={p:.4f}".replace("0.", ".") if p < 0.01
                    else f"p={p:.2f}".replace("0.", "."))
            ax.annotate(ptxt, (i, 1.0), xycoords=("data", "axes fraction"),
                        textcoords="offset points", xytext=(0, -10), ha="center",
                        fontsize=8, color=color)
            CHECKS.append(f"fig3: {model} {kind} {lab} Δ평균={mean:+.5f} p={p:.4g}")
        # 눈금 아래 묶음 표시 — 범례를 대신합니다.
        for lo, hi, color, name in groups:
            ax.plot([lo - 0.32, hi + 0.32], [-0.155, -0.155], color=color, lw=1.6,
                    transform=ax.get_xaxis_transform(), clip_on=False, zorder=6)
            ax.text((lo + hi) / 2, -0.235, name, transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=9, color=color, clip_on=False)
        ax.set_xlim(-0.6, 3.6)
        ax.set_xticks(range(4))
        ax.set_xticklabels([c[0] for c in comps], fontsize=9)
        ax.set_title(model, fontsize=10, pad=16, color=INK)
    axes[0].set_ylabel(L("Δ test MAPE", "Δ test MAPE"))
    axes[0].set_ylim(-0.037, 0.035)  # p 표기가 점과 겹치지 않도록 위쪽 여유

    save(fig, "fig3_delta_by_comparison",
         L("학습 라벨은 안 갈리고 정답 라벨만 갈린다", "Only the scoring label moves the metric"))


# ── 4 ────────────────────────────────────────────────────────────────────
def fig4() -> None:
    r = rows("fig4b_seed_cell_crosstab")
    a = rows("fig4a_cell_contributions")
    seeds = sorted({int(x["seed"]) for x in r}, key=lambda s: SEEDS.index(s))
    rs = {int(x["seed"]): float(x["seed_pearson_r"]) for x in r}

    fig, ax = plt.subplots(figsize=(W * 0.72, 72 * MM))
    hgrid(ax)
    alphas = [0.85, 0.70, 0.55, 0.42, 0.30]
    xs_all, ys_all = [], []
    for al, s in zip(alphas, seeds):
        sub = [x for x in r if int(x["seed"]) == s]
        xs = [float(x["rel_change_abs"]) * 100 for x in sub]
        ys = [float(x["abs_contrib_mape"]) * 1e3 for x in sub]
        xs_all += xs
        ys_all += ys
        ax.scatter(xs, ys, s=26, color=NAVY, alpha=al, linewidths=0, zorder=4,
                   label=f"seed {s}")

    n = len(xs_all)
    mx, my = sum(xs_all) / n, sum(ys_all) / n
    b = sum((p - mx) * (q - my) for p, q in zip(xs_all, ys_all)) / sum((p - mx) ** 2 for p in xs_all)
    a0 = my - b * mx
    lo, hi = 0, max(xs_all) * 1.06
    ax.plot([lo, hi], [a0 + b * lo, a0 + b * hi], color=INK, lw=1.1, ls=(0, (5, 3)), zorder=3)

    for i in range(3):
        c = a[i]
        cell = c["cell"]
        x = abs(float(c["rel_change"])) * 100
        y = abs(float(c["contrib_mape"])) * 1e3
        ax.annotate(cell.replace("ISU-ILCC_", "").replace(".pkl", ""), (x, y),
                    textcoords="offset points", xytext=(-7, 6), ha="right",
                    fontsize=9, color=INK, zorder=6)

    ax.set_xlabel(L("|상대 라벨 변화|  (%)", "|relative label change| (%)"))
    ax.set_ylabel(L("|셀 기여도|  (×0.001)", "|cell contribution| (x0.001)"))
    ax.set_xlim(-1, hi)
    ax.text(0.98, 0.96, f"r = {min(rs.values()):.3f} ~ {max(rs.values()):.3f}"
            + L("  (시드 5개)", "  (5 seeds)"),
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color=INK)
    ax.legend(loc="upper left", frameon=False, borderaxespad=0.2, handletextpad=0.2,
              labelspacing=0.25)

    save(fig, "fig4_change_vs_contribution",
         L("라벨이 많이 바뀐 셀이 많이 기여한다", "Cells whose label moved most contribute most"))
    CHECKS.append(f"fig4: 점 {n}개 · r {min(rs.values()):.3f}~{max(rs.values()):.3f}")


def fig4b() -> None:
    """(a) 를 원할 때만 쓰는 별도 그림. 본문에서 참조하지 않습니다."""
    a = rows("fig4a_cell_contributions")
    fig, ax = plt.subplots(figsize=(W * 0.72, 60 * MM))
    hgrid(ax)
    xs = range(len(a))
    vals = [float(x["contrib_mape"]) * 1e3 for x in a]
    ax.bar(xs, vals, width=0.72, color=[NAVY if v > 0 else GREY for v in vals],
           edgecolor="none")
    ax.axhline(0, color="#888888", lw=0.9)
    for i in range(3):
        ax.annotate(a[i]["cell"].replace("ISU-ILCC_", "").replace(".pkl", ""),
                    (i, vals[i]), textcoords="offset points", xytext=(0, 5),
                    ha="center", fontsize=9, color=INK, rotation=90)
    ax.set_ylim(-1.0, 4.4)
    ax.set_xticks([0, 4, 9, 14, 19, 26])
    ax.set_xticklabels(["1", "5", "10", "15", "20", "27"])
    ax.set_xlabel(L("셀 (|기여| 큰 순, 27셀)", "cells ranked by |contribution| (27)"))
    ax.set_ylabel(L("셀 기여도  (×0.001)", "cell contribution (x0.001)"))
    handles = [Patch(facecolor=NAVY, label=L("B 채점이 더 나쁨", "worse under B")),
               Patch(facecolor=GREY, label=L("B 채점이 더 좋음", "better under B"))]
    ax.legend(handles=handles, loc="upper right", frameon=False, borderaxespad=0.2)
    save(fig, "fig4b_cell_contributions",
         L("상위 3셀이 효과의 대부분을 만든다", "Three cells carry most of the effect"))


# ── 5 ────────────────────────────────────────────────────────────────────
def fig5() -> None:
    r = rows("fig5_effect_vs_model_gaps")
    models = [x for x in r if x["kind"] == "paper_table3"]
    gaps = [x for x in r if x["kind"] == "paper_adjacent_gap_pct"]
    eff_a = [float(x["value"]) for x in r if x["kind"] == "measured_effect_overall_pct"]
    eff_u = [float(x["value"]) for x in r if x["kind"] == "measured_effect_unseen_pct"]
    lo_a, hi_a, lo_u, hi_u = min(eff_a), max(eff_a), min(eff_u), max(eff_u)

    fig, ax = plt.subplots(figsize=(W, 76 * MM))
    hgrid(ax)
    xs = range(len(gaps))
    vals = [float(x["value"]) for x in gaps]
    ax.bar(xs, vals, width=0.52, color=GREY, edgecolor="none", zorder=3)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.18, f"{v:.1f}", ha="center", fontsize=9, color=INK, zorder=4)

    ax.axhspan(lo_a, hi_a, color=NAVY, alpha=0.20, zorder=2)
    ax.axhspan(lo_u, hi_u, color=WARN, alpha=0.20, zorder=2)
    ax.text(len(gaps) - 0.42, (lo_a + hi_a) / 2,
            L(f"전체 {lo_a:.1f}~{hi_a:.1f}%", f"overall {lo_a:.1f}-{hi_a:.1f}%"),
            ha="right", va="center", fontsize=9.5, color=NAVY, zorder=6)
    ax.text(len(gaps) - 0.42, (lo_u + hi_u) / 2,
            L(f"unseen {lo_u:.1f}~{hi_u:.1f}%", f"unseen {lo_u:.1f}-{hi_u:.1f}%"),
            ha="right", va="center", fontsize=9.5, color=WARN, zorder=6)

    ax.set_xticks(xs)
    ax.set_xticklabels([f"{i+1}→{i+2}" for i in xs])
    ax.set_xlim(-0.6, len(gaps) - 0.2)
    ax.set_ylim(0, 11.4)
    ax.set_ylabel(L("상대 격차 (%)", "relative gap (%)"))
    ax.set_xlabel(L("논문 Table 3 Li-ion 순위 인접쌍", "adjacent pairs in paper Table 3 (Li-ion)"))

    order = " · ".join(f"{i+1} {x['item']} {float(x['value']):.3f}"
                       for i, x in enumerate(models))
    fig.text(0.0, -0.13, order, fontsize=8.5, color=GREY)
    fig.text(0.0, -0.19, L("논문 값과 측정값은 실험 조건이 다름 — 상대 격차 축에서만 비교",
                           "Paper and measured values come from different setups; "
                           "compare only on the relative axis"),
             fontsize=8.5, color=INK)

    save(fig, "fig5_effect_vs_model_gaps",
         L("효과가 인접 모델 격차를 전부 넘는다", "The effect exceeds every adjacent gap"))
    CHECKS.append(f"fig5: 격차 {' · '.join(f'{v:.1f}%' for v in vals)} · "
                  f"전체 {lo_a:.1f}~{hi_a:.1f}% · unseen {lo_u:.1f}~{hi_u:.1f}%")


# ── 6 ────────────────────────────────────────────────────────────────────
def fig6() -> None:
    r = rows("fig6_guard_contrast")
    labels = {
        "XJTU": L("XJTU\n(규칙 있음)", "XJTU\n(rule)"),
        "other-12-subsets": L("나머지 12개\n(규칙 없음)", "other 12\n(no rule)"),
        "batch2_csv": L("batch2 .csv\n(가드 있음)", "batch2 .csv\n(guard)"),
        "batch1_xlsx": L("batch1 .xlsx\n(가드 없음)", "batch1 .xlsx\n(no guard)"),
    }
    order = ["XJTU", "other-12-subsets", "batch2_csv", "batch1_xlsx"]
    recs = {x["group"]: x for x in r}

    fig, ax = plt.subplots(figsize=(W * 0.82, 66 * MM))
    hgrid(ax)
    xs = [0, 1, 2.5, 3.5]
    for x, g in zip(xs, order):
        rec = recs[g]
        pct = float(rec["pct_labelled"])
        color = TEAL if rec["guard"] == "yes" else WARN
        ax.bar(x, pct, width=0.56, color=color, edgecolor="none", zorder=3)
        big = pct == 0
        ax.text(x, pct + (0.5 if big else 2.5),
                f"{rec['hits']}/{rec['den_labelled']}",
                ha="center", va="bottom", fontsize=12 if big else 10.5,
                color=color, fontweight="bold", zorder=4)
        if not big:
            ax.text(x, pct - 4.5, f"{pct:.1f}%", ha="center", va="top",
                    fontsize=9, color="white", zorder=5)
    ax.set_xticks(xs)
    ax.set_xticklabels([labels[g] for g in order], fontsize=9)
    ax.set_ylim(0, 116)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel(L("해당 셀의 비율 (%)", "share of affected cells (%)"))
    ax.text(0.5, -0.26, "Li-ion", transform=ax.get_xaxis_transform(), ha="center",
            fontsize=10, color=GREY)
    ax.text(3.0, -0.26, "Na-ion", transform=ax.get_xaxis_transform(), ha="center",
            fontsize=10, color=GREY)
    handles = [Patch(facecolor=TEAL, label=L("방어 규칙 있음", "guard present")),
               Patch(facecolor=WARN, label=L("방어 규칙 없음", "guard absent"))]
    ax.legend(handles=handles, loc="upper left", frameon=False, borderaxespad=0.3)

    save(fig, "fig6_guard_contrast", L("방어 규칙이 있는 범위는 0건이다",
                                       "Where a guard exists, nothing is affected"))
    CHECKS.append("fig6: " + " · ".join(
        f"{g} {recs[g]['hits']}/{recs[g]['den_labelled']}" for g in order))


# ── 7 ────────────────────────────────────────────────────────────────────
def fig7() -> None:
    r = rows("fig7_domain_sample_sizes")
    fig, ax = plt.subplots(figsize=(W * 0.86, 56 * MM))
    ys = list(range(len(r)))[::-1]
    for y, x in zip(ys, r):
        tot = int(x["total_cells"])
        te = int(x["test_cells"])
        small = te <= 5
        ax.barh(y, tot - 1, left=1, height=0.5,
                color=WARN if small else GREY, edgecolor="none", zorder=3)
        ax.text(tot * 1.13, y + 0.13, f"{tot:,}" + L("셀", ""), va="center",
                fontsize=9.5, color=INK)
        ax.text(tot * 1.13, y - 0.20, L(f"시험 {te}셀", f"test {te}"), va="center",
                fontsize=11 if small else 9, color=WARN if small else GREY,
                fontweight="bold" if small else "normal")
    ax.set_xscale("log")
    ax.set_xlim(1, 4200)
    ax.set_yticks(ys)
    ax.set_yticklabels([x["domain"] for x in r], fontsize=9.5)
    ax.set_ylim(-0.6, len(r) - 0.4)
    ax.set_xlabel(L("셀 수 (로그 눈금)", "cells (log scale)"))
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=FAINT, lw=0.7)

    save(fig, "fig7_domain_sample_sizes",
         L("CALB·Na-ion 은 시험 집합이 5셀이다", "CALB and Na-ion test on 5 cells"))
    CHECKS.append("fig7: " + " · ".join(
        f"{x['domain']} {x['total_cells']}셀 시험 {x['test_cells']}" for x in r))


# ── 8 ────────────────────────────────────────────────────────────────────
def fig8() -> None:
    r = rows("fig8_liion_label_distribution")
    vals = [int(x["life_label"]) for x in r]
    g40 = next(x for x in r if x["cell"] == "ISU-ILCC_G40C3.pkl")
    n_le = sum(1 for v in vals if v <= 100)

    fig, ax = plt.subplots(figsize=(W * 0.86, 60 * MM))
    hgrid(ax)
    # 경계 100 을 정확한 구간 경계로 넣습니다 — 걸치는 막대가 생기지 않게.
    edges = sorted({10 ** (i * math.log10(6000) / 40) for i in range(41)} | {100.0})
    counts, bins, patches = ax.hist(vals, bins=edges, color=GREY, edgecolor="white",
                                    linewidth=0.5, zorder=3)
    n_warn = 0
    for lo_e, hi_e, cnt, p in zip(bins[:-1], bins[1:], counts, patches):
        if hi_e <= 100.0:
            p.set_facecolor(WARN)
            n_warn += int(cnt)
    assert n_warn == n_le, (n_warn, n_le)
    ax.set_xscale("log")
    ax.set_xlim(0.8, 6000)
    ax.set_xlabel(L("배포 수명 라벨 (사이클, 로그 눈금)", "shipped life label (cycles, log)"))
    ax.set_ylabel(L("셀 수", "cells"))
    ymax = ax.get_ylim()[1]
    ax.axvline(100, color=INK, lw=1.0, ls=(0, (4, 3)), zorder=4)
    ax.text(112, ymax * 0.95, L("규칙 5 경계", "rule 5 cutoff"), fontsize=9, color=INK,
            va="top")
    ax.annotate(L(f"G40C3 · 라벨 {g40['life_label']}\n총 {int(g40['n_cycles']):,} 사이클",
                  f"G40C3, label {g40['life_label']}\n{int(g40['n_cycles']):,} cycles"),
                xy=(int(g40["life_label"]), 1.2), xytext=(1.35, ymax * 0.62),
                fontsize=9, color=WARN,
                arrowprops=dict(arrowstyle="->", lw=0.9, color=WARN))
    ax.set_title(L(f"n = {len(vals)}셀 · 최소 {min(vals)} · 최대 {max(vals):,} · "
                   f"경계 왼쪽 {n_le}셀",
                   f"n = {len(vals)}; min {min(vals)}, max {max(vals):,}; "
                   f"{n_le} left of cutoff"),
                 fontsize=9, loc="left", color=GREY, pad=6)

    save(fig, "fig8_liion_label_distribution",
         L("규칙 5 경계 왼쪽에 14셀이 남아 있다", "14 cells sit left of the rule-5 cutoff"))
    CHECKS.append(f"fig8: n={len(vals)} 최소 {min(vals)} 최대 {max(vals)} ≤100 {n_le}셀")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"한글 폰트: {KOREAN or '없음 — 영문 대체'}")
    print(f"입력: {SRC}")
    for fn in (fig1, fig2, fig3, fig4, fig4b, fig5, fig6, fig7, fig8):
        fn()
    print("\n── CSV 대조값 ──")
    for c in CHECKS:
        print(" ", c)
    over = [(s, c) for s, c in CAPTIONS if len(c) > 40]
    print("\n캡션 40자 초과:", over or "없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
