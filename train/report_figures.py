"""종합 진척 보고서용 그림 8종을 만듭니다 (figures/report/).

기존 산출물만 재집계합니다. 학습도 추론도 하지 않습니다.
없는 값은 추정하지 않습니다 — 원자료에 없으면 그 그림을 만들지 않습니다.

    C:/Users/taeyo/AppData/Local/Programs/Python/Python312/python.exe -m train.report_figures

출력
    figures/report/figN_*.png   300 dpi
    figures/report/figN_*.pdf   벡터
    figures/report/data/figN_*.csv   그림에 쓴 수치 전부

기존 figures/ 6종(train/figures.py 산출물)은 건드리지 않습니다.
"""

from __future__ import annotations

import csv
import json
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
RESULTS = ROOT / "experiments" / "results"
ANALYSIS = ROOT / "analysis"
EXTRACT = ROOT / "data" / "extracted"
OUT = ROOT / "figures" / "report"
DATA = OUT / "data"

# ── 스타일 ───────────────────────────────────────────────────────────────
# 흑백 인쇄 대비: 색만으로 구분하지 않고 명암·해칭·모양을 함께 씁니다.
_INSTALLED = {f.name for f in fm.fontManager.ttflist}
KOREAN = next(
    (n for n in ("Malgun Gothic", "NanumGothic", "Gulim", "Batang") if n in _INSTALLED),
    None,
)
if KOREAN:
    plt.rcParams["font.family"] = KOREAN
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["figure.dpi"] = 300
plt.rcParams["axes.grid"] = False
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["font.size"] = 7.5
plt.rcParams["axes.titlesize"] = 8.5
plt.rcParams["legend.fontsize"] = 7.0
plt.rcParams["xtick.labelsize"] = 7.0
plt.rcParams["ytick.labelsize"] = 7.0

MM = 1.0 / 25.4
W160 = 160 * MM  # 본문 폭 상한

# 명암 4단계 (흑백 안전)
G0, G1, G2, G3 = "#f2f2f2", "#c8c8c8", "#7a7a7a", "#242424"

NOTES: list[str] = []
CHECKS: list[str] = []


def L(ko: str, en: str) -> str:
    """한글 폰트가 없으면 영문으로 대체합니다."""
    return ko if KOREAN else en


def jload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cload(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def save(fig, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  wrote {stem}.png / .pdf")


def write_csv(stem: str, header: list[str], rows: list[list]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / f"{stem}.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote data/{stem}.csv  ({len(rows)} rows)")


def pearson(xs, ys) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy)


# ── 그림 1 — 서브셋별 라벨 재현율 ────────────────────────────────────────
def fig1() -> None:
    man = jload(RESULTS / "label_ab_manifest.json")
    subs = man["subsets"]

    rows = []
    for name, s in subs.items():
        both, eq = s["both"], s["equal"]
        pct = None if both == 0 else 100.0 * eq / both
        rows.append(
            dict(
                subset=name,
                both=both,
                equal=eq,
                differ=s["differ"],
                in_a=s["in_a"],
                in_b=s["in_b"],
                only_a=s["only_a"],
                only_b=s["only_b"],
                pct=pct,
            )
        )

    calb = next(r for r in rows if r["subset"] == "CALB")
    # CALB 는 배포 트리에 입력 파일이 없어 B 생성 자체가 막혔습니다(both=0).
    # 나중에 MFormer 엑셀을 얹어 27/27 일치했습니다 (calb_excel 보고서 §2-3).
    calb["pct"] = 100.0
    calb["note"] = "MFormer 엑셀로 27/27 (배포 트리에서는 생성 불가)"
    for r in rows:
        r.setdefault("note", "")

    others = [r for r in rows if r["subset"] != "CALB"]
    others.sort(key=lambda r: (r["pct"], r["both"]))
    ordered = [calb] + others  # CALB 를 맨 아래(성격이 다름)

    fig, ax = plt.subplots(figsize=(W160, 92 * MM))
    ys = list(range(len(ordered)))
    for y, r in zip(ys, ordered):
        if r["subset"] == "CALB":
            ax.barh(y, r["pct"], color="white", edgecolor=G3, hatch="///", height=0.68, linewidth=0.8)
        elif r["pct"] >= 100.0:
            ax.barh(y, r["pct"], color=G1, edgecolor=G2, height=0.68, linewidth=0.5)
        else:
            ax.barh(y, r["pct"], color=G3, edgecolor=G3, height=0.68, linewidth=0.5)

    labels = []
    for r in ordered:
        n = r["both"] if r["subset"] != "CALB" else r["in_a"]
        labels.append(f"{r['subset']} ({n}{L('셀', ' cells')})")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.7, len(ordered) - 0.3)

    for y, r in zip(ys, ordered):
        if r["subset"] == "CALB":
            txt = "27/27 *"
        else:
            txt = f"{r['pct']:.1f}%  ({r['equal']}/{r['both']})"
        ax.text(r["pct"] + 1.5, y, txt, va="center", ha="left", fontsize=6.8)

    # CALB 는 성격이 다릅니다 — 가로선으로 갈라 둡니다.
    ax.axhline(0.5, color=G2, lw=0.6, ls=(0, (3, 2)))

    ax.set_xlim(0, 135)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel(L("배포 라벨 A 와 재생성 라벨 B 의 일치율 (%)",
                    "agreement between shipped label A and regenerated label B (%)"))
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    handles = [
        Patch(facecolor=G1, edgecolor=G2, label=L("전부 일치 (16개 서브셋)", "all equal (16 subsets)")),
        Patch(facecolor=G3, edgecolor=G3, label=L("일부 불일치 (2개 서브셋)", "some differ (2 subsets)")),
        Patch(facecolor="white", edgecolor=G3, hatch="///",
              label=L("* 배포 트리에서는 B 생성 불가 → 별도 경로로 27/27",
                      "* B not generable from shipped tree -> 27/27 via separate path")),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.075))
    ax.set_title(L("분모 = 양쪽에 모두 있는 셀. NA-ion·SDU·UL-PUR 은 B 에만 있는 셀이 각각 9·16·8 개 더 있습니다.",
                   "denominator = cells present in both. NA-ion/SDU/UL-PUR have 9/16/8 extra cells in B."),
                 fontsize=6.5, loc="left", color=G2, pad=6)

    save(fig, "fig1_subset_label_agreement")
    write_csv(
        "fig1_subset_label_agreement",
        ["subset", "in_a", "in_b", "both", "equal", "differ", "only_a", "only_b",
         "agreement_pct_over_both", "note"],
        [[r["subset"], r["in_a"], r["in_b"], r["both"], r["equal"], r["differ"],
          r["only_a"], r["only_b"],
          "" if r["subset"] == "CALB" else round(r["pct"], 4), r["note"]] for r in ordered],
    )
    CHECKS.append(f"fig1: 100% 서브셋 {sum(1 for r in others if r['pct'] >= 100)}개, "
                  f"불일치 {sum(1 for r in others if r['pct'] < 100)}개, CALB 별도 1개")


# ── 그림 2 — ISU-ILCC 240셀, A 대 B ──────────────────────────────────────
def fig2() -> None:
    man = jload(RESULTS / "label_ab_manifest.json")
    pairs = [v for k, v in man["pairs"].items() if v["subset"] == "ISU-ILCC"]
    assert len(pairs) == 240, len(pairs)

    cw = jload(RESULTS / "label_ab_cellwise.json")
    test27 = {c["file"] for c in cw["cells"]["CPMLP_trainA"] if c["changed"]}
    assert len(test27) == 27, len(test27)

    eq = [p for p in pairs if p["equal"]]
    df = [p for p in pairs if not p["equal"]]
    rel_all = sorted(p["rel_diff"] for p in pairs)
    rel_dif = sorted(p["rel_diff"] for p in df)
    rel_27 = sorted(abs(p["b"] - p["a"]) / p["a"] for p in pairs if p["cell"] in test27)

    def med(v):
        n = len(v)
        return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])

    m_all, mx_all = med(rel_all), max(rel_all)
    m_dif = med(rel_dif)  # 매니페스트 rel_diff_median 은 이 모집단(불일치 셀)입니다
    m_27, mx_27, mean_27 = med(rel_27), max(rel_27), sum(rel_27) / len(rel_27)
    cell_max = max(pairs, key=lambda p: p["rel_diff"])["cell"]

    fig = plt.figure(figsize=(W160, 84 * MM))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.30)
    ax = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    lim = (12, 6000)
    ax.plot(lim, lim, color=G2, lw=0.7, zorder=1)
    ax.scatter([p["a"] for p in eq], [p["b"] for p in eq], s=13, marker="o",
               facecolors="none", edgecolors=G2, linewidths=0.6, zorder=2,
               label=L(f"일치 {len(eq)}셀", f"equal ({len(eq)})"))
    ax.scatter([p["a"] for p in df], [p["b"] for p in df], s=15, marker="x",
               color=G3, linewidths=0.8, zorder=3,
               label=L(f"불일치 {len(df)}셀", f"differ ({len(df)})"))

    top3 = ["ISU-ILCC_G14C4.pkl", "ISU-ILCC_G13C1.pkl", "ISU-ILCC_G2C4.pkl"]
    offs = {"ISU-ILCC_G14C4.pkl": (-2, -14), "ISU-ILCC_G13C1.pkl": (7, -11),
            "ISU-ILCC_G2C4.pkl": (7, 7)}
    for name in top3:
        p = next(x for x in pairs if x["cell"] == name)
        ax.scatter([p["a"]], [p["b"]], s=44, marker="s", facecolors="none",
                   edgecolors=G3, linewidths=1.1, zorder=4)
        ax.annotate(name.replace("ISU-ILCC_", "").replace(".pkl", ""),
                    (p["a"], p["b"]), textcoords="offset points",
                    xytext=offs[name], fontsize=6.8, zorder=5)
    pmax = max(pairs, key=lambda x: x["rel_diff"])
    ax.annotate(pmax["cell"].replace("ISU-ILCC_", "").replace(".pkl", ""),
                (pmax["a"], pmax["b"]), textcoords="offset points", xytext=(-30, -12),
                fontsize=6.6, color=G2, zorder=5)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_aspect("equal")
    ax.set_xlabel(L("배포 라벨 A (사이클)", "shipped label A (cycles)"))
    ax.set_ylabel(L("공개 코드 재생성 라벨 B (사이클)", "regenerated label B (cycles)"))
    ax.legend(loc="upper left", frameon=False, borderaxespad=0.2)

    bins = [0.0, 1e-12, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15, 0.25, 0.50, 1.0]
    ax2.hist([r * 100 for r in rel_all], bins=[b * 100 for b in bins],
             color=G1, edgecolor=G2, linewidth=0.5,
             label=L("ISU-ILCC 240셀", "ISU-ILCC, 240 cells"))
    ax2.hist([r * 100 for r in rel_27], bins=[b * 100 for b in bins],
             color="white", edgecolor=G3, linewidth=0.8, hatch="////",
             label=L("그중 시험 집합 27셀", "of which 27 test cells"))
    ax2.set_xscale("symlog", linthresh=0.5, linscale=0.35)
    ax2.set_xticks([0, 1, 10, 100])
    ax2.set_xticklabels(["0", "1", "10", "100"])
    ax2.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax2.set_xlabel(L("상대차  |B-A| / A  (%)", "relative diff |B-A|/A (%)"))
    ax2.set_ylabel(L("셀 수", "cells"))
    ax2.legend(loc="upper right", frameon=False, borderaxespad=0.2)
    ax2.set_title(
        L(f"240셀 중앙 {m_all*100:.2f}%\n"
          f"불일치 155셀 중앙 {m_dif*100:.2f}% · 최대 {mx_all*100:.2f}%\n"
          f"시험 27셀 평균 {mean_27*100:.2f}% · 중앙 {m_27*100:.2f}% · 최대 {mx_27*100:.2f}%",
          f"240 cells median {m_all*100:.2f}%\n"
          f"155 differing median {m_dif*100:.2f}%, max {mx_all*100:.2f}%\n"
          f"27 test cells mean {mean_27*100:.2f}%, median {m_27*100:.2f}%, max {mx_27*100:.2f}%"),
        fontsize=6.4, loc="left", color=G3, pad=5)

    save(fig, "fig2_isu_ilcc_a_vs_b")
    write_csv(
        "fig2_isu_ilcc_a_vs_b",
        ["cell", "label_A", "label_B", "equal", "abs_diff", "rel_diff",
         "in_test140", "a_pass_rule5", "b_pass_rule5"],
        [[p["cell"], p["a"], p["b"], p["equal"], p["abs_diff"], p["rel_diff"],
          p["cell"] in test27, p["a_pass_rule5"], p["b_pass_rule5"]]
         for p in sorted(pairs, key=lambda x: -x["rel_diff"])],
    )
    CHECKS.append(f"fig2: 240셀 일치 {len(eq)} · 불일치 {len(df)} / "
                  f"240셀 중앙 {m_all*100:.2f}% · 불일치 155셀 중앙 {m_dif*100:.2f}% · "
                  f"최대 {mx_all*100:.2f}% / "
                  f"27셀 평균 {mean_27*100:.2f}% 중앙 {m_27*100:.2f}% 최대 {mx_27*100:.2f}%")


# ── 그림 3 — 조건 4개 × 시드 5개 ─────────────────────────────────────────
SEEDS = [42, 2021, 2024, 7, 1234]
CONDS = ["AA", "BA", "AB", "BB"]  # 시험 라벨로 묶습니다: (A,A)(B,A) | (A,B)(B,B)
MODELS = ["CPMLP", "CPTransformer"]


def _load_ab_runs() -> dict:
    out = {}
    for cond in ("AA", "AB", "BA", "BB"):
        for model in MODELS:
            for seed in SEEDS:
                p = RESULTS / "label_ab" / cond / f"{model}_s{seed}.json"
                d = jload(p)
                assert d["condition"] == cond and d["model"] == model and d["seed"] == seed
                out[(cond, model, seed)] = d["final"]
    assert len(out) == 40, len(out)
    return out


def fig3() -> None:
    runs = _load_ab_runs()

    fig, axes = plt.subplots(1, 2, figsize=(W160, 78 * MM), sharey=True)
    marks = ["o", "s", "^", "D", "v"]

    for ax, model in zip(axes, MODELS):
        ax.axvspan(-0.5, 1.5, color=G0, zorder=0)
        ax.axvspan(1.5, 3.5, color="#e2e2e2", zorder=0)
        for i, seed in enumerate(SEEDS):
            ys = [runs[(c, model, seed)]["test_mape"] for c in CONDS]
            # 실선: 시험 라벨이 같은 짝 (직접 비교 가능 — 학습 라벨 효과)
            ax.plot([0, 1], ys[0:2], color=G2, lw=0.6, zorder=2)
            ax.plot([2, 3], ys[2:4], color=G2, lw=0.6, zorder=2)
            # 파선: 같은 모델·다른 정답 (채점표 효과)
            ax.plot([0, 2], [ys[0], ys[2]], color=G2, lw=0.5, ls=(0, (2, 2)), zorder=1)
            ax.plot([1, 3], [ys[1], ys[3]], color=G2, lw=0.5, ls=(0, (2, 2)), zorder=1)
            ax.scatter(range(4), ys, s=20, marker=marks[i], facecolors="white",
                       edgecolors=G3, linewidths=0.8, zorder=4, label=f"seed {seed}")
        means = [sum(runs[(c, model, s)]["test_mape"] for s in SEEDS) / 5 for c in CONDS]
        for x, m in zip(range(4), means):
            ax.plot([x - 0.28, x + 0.28], [m, m], color=G3, lw=1.8, zorder=6,
                    solid_capstyle="butt")
        # 시드 평균은 눈금 아래 한 줄로 적습니다 (점과 겹치지 않게).
        for x, m in zip(range(4), means):
            ax.annotate(f"{m:.4f}", (x, 0), xycoords=("data", "axes fraction"),
                        textcoords="offset points", xytext=(0, -22), ha="center",
                        fontsize=6.4, color=G3)

        ax.set_xlim(-0.5, 3.5)
        ax.set_xticks(range(4))
        ax.set_xticklabels(CONDS)
        ax.set_title(model, pad=4)
        ax.set_xlabel(L("조건 (학습 라벨, 시험 라벨) · 아래 줄은 시드 평균",
                        "condition (train label, test label); lower row = seed mean"),
                      labelpad=16)

    axes[0].set_ylabel(L("test MAPE", "test MAPE"))
    axes[0].text(0.5, 0.985, L("시험 = A", "test = A"), transform=axes[0].get_xaxis_transform(),
                 ha="center", va="top", fontsize=6.8, color=G2)
    axes[0].text(2.5, 0.985, L("시험 = B", "test = B"), transform=axes[0].get_xaxis_transform(),
                 ha="center", va="top", fontsize=6.8, color=G2)
    axes[1].text(0.5, 0.985, L("시험 = A", "test = A"), transform=axes[1].get_xaxis_transform(),
                 ha="center", va="top", fontsize=6.8, color=G2)
    axes[1].text(2.5, 0.985, L("시험 = B", "test = B"), transform=axes[1].get_xaxis_transform(),
                 ha="center", va="top", fontsize=6.8, color=G2)

    handles = [Line2D([], [], marker=m, ls="", mfc="white", mec=G3, mew=0.8, ms=4.5,
                      label=f"seed {s}") for m, s in zip(marks, SEEDS)]
    handles += [
        Line2D([], [], color=G2, lw=0.8, label=L("시험 라벨 동일 (직접 비교 가능)",
                                                 "same test label (comparable)")),
        Line2D([], [], color=G2, lw=0.8, ls=(0, (2, 2)),
               label=L("같은 모델·다른 정답 (음영 경계를 넘음)",
                       "same model, different ground truth")),
        Line2D([], [], color=G3, lw=1.8, label=L("시드 평균", "seed mean")),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, -0.20))
    fig.text(0.0, -0.26, L("음영이 다른 두 구역은 서로 다른 정답에 대한 정확도입니다. "
                           "구역을 가로지르는 값끼리는 같은 양이 아닙니다.",
                           "The two shaded zones score against different ground truth; "
                           "values across zones are not the same quantity."),
             fontsize=6.4, color=G2)

    save(fig, "fig3_conditions_by_seed")
    write_csv(
        "fig3_conditions_by_seed",
        ["model", "seed", "condition", "train_labels", "test_labels",
         "test_mape", "test_acc15", "test_seen_mape", "test_unseen_mape"],
        [[model, seed, cond, cond[0], cond[1],
          runs[(cond, model, seed)]["test_mape"], runs[(cond, model, seed)]["test_acc15"],
          runs[(cond, model, seed)]["test_seen_mape"], runs[(cond, model, seed)]["test_unseen_mape"]]
         for model in MODELS for seed in SEEDS for cond in ("AA", "AB", "BA", "BB")],
    )
    for model in MODELS:
        for c in ("AA", "AB", "BA", "BB"):
            m = sum(runs[(c, model, s)]["test_mape"] for s in SEEDS) / 5
            CHECKS.append(f"fig3: {model} {c} 시드평균 MAPE = {m:.5f}")


# ── 그림 4 — 효과가 어디서 오는가 ────────────────────────────────────────
def fig4() -> None:
    cw = jload(RESULTS / "label_ab_cellwise.json")
    agg = [c for c in cw["cells"]["CPMLP_trainA"] if c["changed"]]
    agg.sort(key=lambda c: -abs(c["contrib_mape"]))
    assert len(agg) == 27

    total_abs = sum(abs(c["contrib_mape"]) for c in agg)
    cum = []
    acc = 0.0
    for c in agg:
        acc += abs(c["contrib_mape"])
        cum.append(100.0 * acc / total_abs)

    # (b) 시드별 원자료 — CPMLP · train A
    per_seed = {}
    for seed in SEEDS:
        run = cw["runs"][f"CPMLP_s{seed}_trainA"]
        rows = {}
        for c in run["cells"]:
            if not c["changed"]:
                continue
            rows[c["file"]] = dict(
                rel=abs(c["b"] - c["a"]) / c["a"],
                contrib=c["w"] * (c["mapeB"] - c["mapeA"]),
            )
        assert len(rows) == 27, (seed, len(rows))
        per_seed[seed] = rows

    rs = {}
    for seed in SEEDS:
        xs = [per_seed[seed][c["file"]]["rel"] for c in agg]
        ys = [abs(per_seed[seed][c["file"]]["contrib"]) for c in agg]
        rs[seed] = pearson(xs, ys)

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(W160, 76 * MM),
                                   gridspec_kw=dict(width_ratios=[1.30, 1.0], wspace=0.62))

    # (a)
    xs = range(27)
    pos = [c["contrib_mape"] * 1e3 if c["contrib_mape"] > 0 else 0 for c in agg]
    neg = [c["contrib_mape"] * 1e3 if c["contrib_mape"] < 0 else 0 for c in agg]
    axa.bar(xs, pos, color=G2, edgecolor=G3, linewidth=0.4, width=0.75,
            label=L("B 채점이 더 나쁨 (+)", "worse under B (+)"))
    axa.bar(xs, neg, color="white", edgecolor=G3, linewidth=0.6, width=0.75, hatch="////",
            label=L("B 채점이 더 좋음 (-)", "better under B (-)"))
    axa.axhline(0, color=G3, lw=0.6)
    axa.set_ylabel(L("셀 기여도  (×0.001) (ΔMAPE)", "cell contribution x1e-3 (dMAPE)"))
    axa.set_xlabel(L("셀 (|기여| 큰 순, 27셀)", "cells, ranked by |contribution| (27)"))
    axa.set_xticks([0, 4, 9, 14, 19, 26])
    axa.set_xticklabels(["1", "5", "10", "15", "20", "27"])
    axa.set_ylim(-1.05, 3.55)
    for i in range(3):
        axa.annotate(agg[i]["file"].replace("ISU-ILCC_", "").replace(".pkl", ""),
                     (i, agg[i]["contrib_mape"] * 1e3), textcoords="offset points",
                     xytext=(-1, 5), fontsize=6.4, rotation=90, ha="center")
    axc = axa.twinx()
    axc.plot(xs, cum, color=G3, lw=1.0, ls=(0, (4, 1.6)), marker="", zorder=5)
    axc.set_ylim(0, 105)
    axc.set_ylabel(L("절대 기여 누적 비중 (%)", "cumulative share of |contribution| (%)"))
    axc.spines["right"].set_visible(True)
    axc.spines["top"].set_visible(False)
    for i, lab in ((0, None), (2, f"{cum[2]:.0f}%"), (4, f"{cum[4]:.0f}%"), (9, f"{cum[9]:.0f}%")):
        if lab:
            axc.annotate(lab, (i, cum[i]), textcoords="offset points", xytext=(3, -8),
                         fontsize=6.6, color=G3)
    h1, l1 = axa.get_legend_handles_labels()
    h1.append(Line2D([], [], color=G3, lw=1.0, ls=(0, (4, 1.6)),
                     label=L("절대 기여 누적 (오른쪽 축)", "cumulative |contrib| (right axis)")))
    axa.legend(handles=h1, loc="lower right", frameon=False, borderaxespad=0.2,
               handlelength=1.6, handletextpad=0.4)
    axa.set_title("(a)", loc="left", fontsize=8, pad=3)

    # (b)
    marks = ["o", "s", "^", "D", "v"]
    for m, seed in zip(marks, SEEDS):
        xs2 = [per_seed[seed][c["file"]]["rel"] * 100 for c in agg]
        ys2 = [abs(per_seed[seed][c["file"]]["contrib"]) * 1e3 for c in agg]
        axb.scatter(xs2, ys2, s=15, marker=m, facecolors="none", edgecolors=G3,
                    linewidths=0.6, label=f"seed {seed}  r={rs[seed]:.3f}")
    axb.set_xlabel(L("|상대 라벨 변화|  |B-A|/A  (%)", "|relative label change| (%)"))
    axb.set_ylabel(L("|셀 기여도|  (×0.001)", "|cell contribution| x1e-3"))
    axb.legend(loc="upper left", frameon=False, borderaxespad=0.2, handletextpad=0.3)
    axb.set_title("(b)", loc="left", fontsize=8, pad=3)

    save(fig, "fig4_effect_concentration")
    write_csv(
        "fig4a_cell_contributions",
        ["rank", "cell", "label_A", "label_B", "rel_change", "seen_unseen",
         "mape_A", "mape_B", "weight", "contrib_mape", "cum_abs_share_pct"],
        [[i + 1, c["file"], c["a"], c["b"], (c["b"] - c["a"]) / c["a"], c["seen_unseen"],
          c["mapeA"], c["mapeB"], c["w"], c["contrib_mape"], round(cum[i], 4)]
         for i, c in enumerate(agg)],
    )
    write_csv(
        "fig4b_seed_cell_crosstab",
        ["seed", "cell", "rel_change_abs", "contrib_mape", "abs_contrib_mape", "seed_pearson_r"],
        [[seed, c["file"], per_seed[seed][c["file"]]["rel"],
          per_seed[seed][c["file"]]["contrib"], abs(per_seed[seed][c["file"]]["contrib"]),
          round(rs[seed], 6)]
         for seed in SEEDS for c in agg],
    )
    CHECKS.append("fig4: CPMLP·trainA 절대기여 누적 상위1 {:.1f}% · 상위3 {:.1f}% · "
                  "상위5 {:.1f}% · 상위10 {:.1f}%".format(cum[0], cum[2], cum[4], cum[9]))
    CHECKS.append("fig4: 시드별 r = " + " · ".join(f"{s}:{rs[s]:.3f}" for s in SEEDS))
    CHECKS.append(f"fig4: 27셀 기여 합 = {sum(c['contrib_mape'] for c in agg):+.5f}")


# ── 그림 5 — 효과 크기와 모델 간 격차 ────────────────────────────────────
# BatteryLife (KDD'25) Table 3, Li-ion MAPE. 논문 PDF 본문에서 그대로 옮겼습니다.
TABLE3 = [
    ("CPMLP", 0.179, 0.003),
    ("CPTransformer", 0.184, 0.003),
    ("CPGRU", 0.189, 0.008),
    ("CPBiGRU", 0.190, 0.001),
    ("CPBiLSTM", 0.191, 0.007),
    ("CPLSTM", 0.196, 0.006),
]


def fig5() -> None:
    ana = jload(RESULTS / "label_ab_analysis.json")
    s = ana["summary"]

    # 채점표 효과 = 같은 모델, 정답만 A→B (§2-3)
    eff_all = []
    for model in MODELS:
        for a, b in (("AA", "AB"), ("BA", "BB")):
            ma, mb = s[f"{model}_{a}"]["mape_mean"], s[f"{model}_{b}"]["mape_mean"]
            eff_all.append((f"{model} {a}→{b}", 100.0 * (mb - ma) / ma))

    # unseen 은 학습 보고서 §2-4 표 (같은 40회에서 갈라 낸 값)
    runs = _load_ab_runs()
    eff_unseen = []
    for model in MODELS:
        for a, b in (("AA", "AB"), ("BA", "BB")):
            ua = sum(runs[(a, model, sd)]["test_unseen_mape"] for sd in SEEDS) / 5
            ub = sum(runs[(b, model, sd)]["test_unseen_mape"] for sd in SEEDS) / 5
            eff_unseen.append((f"{model} {a}→{b}", 100.0 * (ub - ua) / ua))

    lo_a, hi_a = min(v for _, v in eff_all), max(v for _, v in eff_all)
    lo_u, hi_u = min(v for _, v in eff_unseen), max(v for _, v in eff_unseen)

    gaps = []
    for (n1, m1, _), (n2, m2, _) in zip(TABLE3, TABLE3[1:]):
        gaps.append((f"{n1}→{n2}", 100.0 * (m2 - m1) / m1))

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(W160, 72 * MM),
                                   gridspec_kw=dict(width_ratios=[1.0, 1.12], wspace=0.52))

    # 왼쪽 — 논문 Table 3 상위 6모델
    ys = list(range(len(TABLE3)))[::-1]
    for y, (name, mape, sd) in zip(ys, TABLE3):
        axl.errorbar([mape], [y], xerr=[sd], fmt="o", ms=4.2, color=G3,
                     ecolor=G2, elinewidth=0.9, capsize=2.2, mfc="white", mew=0.9)
    axl.set_yticks(ys)
    axl.set_yticklabels([n for n, _, _ in TABLE3])
    axl.set_ylim(-0.6, len(TABLE3) - 0.4)
    axl.set_xlabel(L("논문 Table 3 · Li-ion MAPE", "paper Table 3, Li-ion MAPE"))
    axl.set_xlim(0.172, 0.206)
    axl.spines["left"].set_visible(False)
    axl.tick_params(axis="y", length=0)
    for i, (label, g) in enumerate(gaps):
        y = (ys[i] + ys[i + 1]) / 2.0
        axl.annotate(f"{g:.1f}%", (0.2035, y), fontsize=6.6, ha="right", va="center", color=G3)
        axl.annotate("", xy=(0.2045, ys[i]), xytext=(0.2045, ys[i + 1]),
                     arrowprops=dict(arrowstyle="<->", lw=0.6, color=G2))
    axl.set_title(L("(a) 논문이 보고한 상위 6모델", "(a) top-6 models as reported"),
                  loc="left", fontsize=8, pad=3)

    # 오른쪽 — 상대 격차(%) 축에서 비교
    n = len(gaps)
    axr.axhspan(lo_a, hi_a, color=G1, zorder=0)
    axr.axhspan(lo_u, hi_u, facecolor="white", edgecolor=G3,
                hatch="\\\\\\", linewidth=0.7, zorder=1)
    axr.scatter(range(n), [g for _, g in gaps], s=30, marker="D", facecolors="white",
                edgecolors=G3, linewidths=1.0, zorder=4)
    for i, (_, g) in enumerate(gaps):
        axr.annotate(f"{g:.1f}", (i, g), textcoords="offset points", xytext=(0, 7),
                     ha="center", fontsize=6.4, color=G3, zorder=5)
    short = ["MLP→Trans", "Trans→GRU", "GRU→BiGRU", "BiGRU→BiLSTM", "BiLSTM→LSTM"]
    axr.set_xlim(-0.7, n - 0.3)
    axr.set_xticks(range(n))
    axr.set_xticklabels(short, rotation=32, ha="right", fontsize=6.3)
    axr.set_ylim(0, 11.5)
    axr.set_ylabel(L("상대 격차 (%)", "relative gap (%)"))
    bbox = dict(facecolor="white", edgecolor="none", pad=1.0)
    axr.text(-0.6, (lo_a + hi_a) / 2,
             L(f"전체 {lo_a:.1f}~{hi_a:.1f}%", f"overall {lo_a:.1f}-{hi_a:.1f}%"),
             ha="left", va="center", fontsize=6.8, color=G3, zorder=6, bbox=bbox)
    axr.text(-0.6, (lo_u + hi_u) / 2,
             L(f"unseen {lo_u:.1f}~{hi_u:.1f}%", f"unseen {lo_u:.1f}-{hi_u:.1f}%"),
             ha="left", va="center", fontsize=6.8, color=G3, zorder=6, bbox=bbox)
    handles = [
        Line2D([], [], marker="D", ls="", mfc="white", mec=G3, mew=1.0, ms=4.4,
               label=L("논문 인접 모델 격차", "adjacent gap, paper")),
        Patch(facecolor=G1, edgecolor="none", label=L("측정한 채점표 효과 (전체)",
                                                      "measured scoring effect (overall)")),
        Patch(facecolor="white", edgecolor=G3, hatch="\\\\\\",
              label=L("측정한 채점표 효과 (unseen)", "measured scoring effect (unseen)")),
    ]
    axr.legend(handles=handles, loc="upper center", frameon=True, framealpha=1.0,
               edgecolor="none", borderaxespad=0.15, fontsize=6.4, handlelength=1.4)
    axr.set_title(L("(b) 상대 격차 축에서의 비교", "(b) compared on a relative-gap axis"),
                  loc="left", fontsize=8, pad=3)

    fig.text(0.0, -0.10,
             L("단서: (a) 는 논문이 보고한 값이고 (b) 의 띠는 이 저장소의 40회 실행에서 잰 값입니다. "
               "하드웨어·하이퍼파라미터·시드 수가 다르므로 절대 MAPE 를 겹쳐 읽지 마십시오. "
               "비교는 상대 격차(%) 축에서만 성립합니다.",
               "Caveat: (a) is as reported in the paper; (b) bands are measured in this repo. "
               "Hardware, hyperparameters and seed counts differ - compare only on the relative axis."),
             fontsize=6.4, color=G2, wrap=True)

    save(fig, "fig5_effect_vs_model_gaps")
    rows = [["paper_table3", n, "", mape, sd] for n, mape, sd in TABLE3]
    rows += [["paper_adjacent_gap_pct", lab, "", g, ""] for lab, g in gaps]
    rows += [["measured_effect_overall_pct", lab, "test MAPE", g, ""] for lab, g in eff_all]
    rows += [["measured_effect_unseen_pct", lab, "test unseen MAPE", g, ""] for lab, g in eff_unseen]
    write_csv("fig5_effect_vs_model_gaps", ["kind", "item", "metric", "value", "sd"], rows)
    CHECKS.append("fig5: 논문 인접 격차 = " + " · ".join(f"{g:.1f}%" for _, g in gaps))
    CHECKS.append(f"fig5: 측정 효과 전체 {lo_a:.1f}~{hi_a:.1f}% · unseen {lo_u:.1f}~{hi_u:.1f}%")


# ── 그림 6 — 방어 유무 대조 ──────────────────────────────────────────────
def fig6() -> None:
    rows = cload(ANALYSIS / "li_ion_label_vs_soh.csv")
    tc = cload(ANALYSIS / "li_ion_temporary_crossing.csv")
    assert len(rows) == 839 and len(tc) == 107

    xj = [r for r in rows if r["subset"] == "XJTU"]
    nx = [r for r in rows if r["subset"] != "XJTU"]
    xj_repro = [r for r in xj if r["repro_denom"] in ("repo", "dis1")]
    nx_repro = [r for r in nx if r["repro_denom"] in ("repo", "dis1")]
    xj_test = [r for r in xj_repro if (fnum(r["n_cycles_after"]) or 0) >= 5]
    nx_test = [r for r in nx_repro if (fnum(r["n_cycles_after"]) or 0) >= 5]
    n_xj_hit = sum(1 for r in tc if r["subset"] == "XJTU")
    n_nx_hit = len(tc) - n_xj_hit
    assert n_xj_hit == 0

    na = cload(ANALYSIS / "na_ion_cell_summary.csv")
    b1 = [r for r in na if r["family"] == "batch1_xlsx"]
    b2 = [r for r in na if r["family"] == "batch2_csv"]
    assert len(b1) == 5 and len(b2) == 59
    # 유형 I(마지막 사이클 충전 중 절단) 셀 수 — na_ion_soh_drop 보고서 §유형 I.
    na_b1_hit, na_b2_hit = 5, 0

    bars = [
        ("Li-ion", L("XJTU\n(마지막 하강 교차 규칙 있음)", "XJTU\n(last-descending rule)"),
         n_xj_hit, len(xj), True),
        ("Li-ion", L("나머지 12개 서브셋\n(규칙 없음)", "other 12 subsets\n(no rule)"),
         n_nx_hit, len(nx), False),
        ("Na-ion", L("batch2 .csv\n(절단 가드 있음)", "batch2 .csv\n(truncation guard)"),
         na_b2_hit, len(b2), True),
        ("Na-ion", L("batch1 .xlsx\n(가드 없음)", "batch1 .xlsx\n(no guard)"),
         na_b1_hit, len(b1), False),
    ]

    fig, ax = plt.subplots(figsize=(W160, 76 * MM))
    xs = [0, 1, 2.6, 3.6]
    for x, (dom, lab, hit, tot, guarded) in zip(xs, bars):
        pct = 100.0 * hit / tot
        if guarded:
            ax.bar(x, pct, width=0.62, color=G1, edgecolor=G2, linewidth=0.6)
        else:
            ax.bar(x, pct, width=0.62, color="white", edgecolor=G3, linewidth=0.9, hatch="xxx")
        ax.text(x, pct + 2.4, f"{hit}/{tot}\n{pct:.1f}%", ha="center", va="bottom",
                fontsize=7.0, color=G3)
    ax.set_xticks(xs)
    ax.set_xticklabels([b[1] for b in bars])
    ax.set_ylim(0, 118)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel(L("해당 셀의 비율 (%)", "share of affected cells (%)"))
    ax.text(0.5, -0.215, "Li-ion", transform=ax.get_xaxis_transform(), ha="center",
            fontsize=8.5, color=G3)
    ax.text(3.1, -0.215, "Na-ion", transform=ax.get_xaxis_transform(), ha="center",
            fontsize=8.5, color=G3)
    ax.plot([-0.42, 1.42], [-0.185, -0.185], transform=ax.get_xaxis_transform(),
            color=G2, lw=0.6, clip_on=False)
    ax.plot([2.18, 4.02], [-0.185, -0.185], transform=ax.get_xaxis_transform(),
            color=G2, lw=0.6, clip_on=False)
    handles = [
        Patch(facecolor=G1, edgecolor=G2, label=L("방어 규칙 있음", "guard present")),
        Patch(facecolor="white", edgecolor=G3, hatch="xxx", label=L("방어 규칙 없음", "guard absent")),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False, borderaxespad=0.3)

    fig.text(0.0, -0.24,
             L(f"분모 정의 = 그 집단의 라벨 보유 셀 (Li-ion: XJTU 23 · 나머지 12개 서브셋 {len(nx)}; "
               f"Na-ion: batch2 {len(b2)} · batch1 {len(b1)}).\n"
               f"이 분모에는 라벨을 재현하지 못한 108셀(Tongji 104 · ISU-ILCC 3 · Stanford 1)이 포함되어 있습니다.\n"
               f"분모를 재현 가능 셀로 좁히면 비-XJTU 는 {n_nx_hit}/{len(nx_repro)} = "
               f"{100.0*n_nx_hit/len(nx_repro):.1f}% 가 됩니다. "
               f"Li-ion 분자는 m=0.02 기준 일시적 교차 셀입니다.",
               f"Denominator = labelled cells in each group (Li-ion: XJTU 23 vs other 12 subsets {len(nx)}; "
               f"Na-ion: batch2 {len(b2)} vs batch1 {len(b1)}).\n"
               f"It includes the 108 cells whose labels could not be reproduced "
               f"(Tongji 104 / ISU-ILCC 3 / Stanford 1).\n"
               f"Restricted to reproducible cells the non-XJTU share is {n_nx_hit}/{len(nx_repro)} = "
               f"{100.0*n_nx_hit/len(nx_repro):.1f}%."),
             fontsize=6.4, color=G2)

    save(fig, "fig6_guard_contrast")
    write_csv(
        "fig6_guard_contrast",
        ["domain", "group", "guard", "hits", "den_labelled", "pct_labelled",
         "den_reproduced", "pct_reproduced", "den_testable", "pct_testable", "source"],
        [
            ["Li-ion", "XJTU", "yes", n_xj_hit, len(xj), 0.0, len(xj_repro), 0.0,
             len(xj_test), "", "analysis/li_ion_temporary_crossing.csv (m=0.02)"],
            ["Li-ion", "other-12-subsets", "no", n_nx_hit, len(nx),
             round(100.0 * n_nx_hit / len(nx), 4), len(nx_repro),
             round(100.0 * n_nx_hit / len(nx_repro), 4), len(nx_test),
             round(100.0 * n_nx_hit / len(nx_test), 4),
             "analysis/li_ion_temporary_crossing.csv (m=0.02)"],
            ["Na-ion", "batch2_csv", "yes", na_b2_hit, len(b2), 0.0, "", "", "", "",
             "docs/reports/2026-08-06_na_ion_soh_drop.md:192 (type I)"],
            ["Na-ion", "batch1_xlsx", "no", na_b1_hit, len(b1),
             round(100.0 * na_b1_hit / len(b1), 4), "", "", "", "",
             "docs/reports/2026-08-06_na_ion_soh_drop.md:192 (type I)"],
        ],
    )
    CHECKS.append(f"fig6: XJTU {n_xj_hit}/{len(xj)} (재현 {len(xj_repro)}, 판정가능 {len(xj_test)}) · "
                  f"비-XJTU {n_nx_hit}/{len(nx)} = {100.0*n_nx_hit/len(nx):.1f}% "
                  f"(재현 {len(nx_repro)} → {100.0*n_nx_hit/len(nx_repro):.1f}%, "
                  f"판정가능 {len(nx_test)} → {100.0*n_nx_hit/len(nx_test):.1f}%)")


# ── 그림 7 — 도메인별 표본 크기와 실효 표본 ──────────────────────────────
# data_provider/data_split_recorder.py 의 분할 정의를 그대로 셌습니다.
SPLITS = [
    ("Li-ion", 510, 165, 162, "MIX_large_841 (라벨 미배포 6셀 제외)"),
    ("Zn-ion", 60, 20, 20, "ZNcoin — 논문 Table 2 는 95 (모집단 상이)"),
    ("Na-ion", 20, 6, 5, "NAion_2021"),
    ("CALB", 17, 5, 5, "CALB"),
]


def fig7() -> None:
    fig, ax = plt.subplots(figsize=(W160, 66 * MM))
    ys = list(range(len(SPLITS)))[::-1]
    styles = [
        dict(color=G1, edgecolor=G2, hatch=None),
        dict(color=G2, edgecolor=G3, hatch=None),
        dict(color="white", edgecolor=G3, hatch="///"),
    ]
    names = [L("train", "train"), L("val", "val"), L("test", "test")]

    for y, (dom, tr, va, te, note) in zip(ys, SPLITS):
        bounds = [1, tr, tr + va, tr + va + te]
        for k in range(3):
            ax.barh(y, bounds[k + 1] - bounds[k], left=bounds[k], height=0.62,
                    linewidth=0.7, **styles[k])
        total = tr + va + te
        ax.text(total * 1.10, y, f"{total}{L('셀', '')}", va="center", fontsize=7.2, color=G3)
        ax.text(total * 1.10, y - 0.30, L(f"시험 {te}셀", f"test {te}"),
                va="center", fontsize=6.6, color=G2)

    ax.set_xscale("log")
    ax.set_xlim(1, 3000)
    ax.set_yticks(ys)
    ax.set_yticklabels([s[0] for s in SPLITS])
    ax.set_ylim(-0.7, len(SPLITS) - 0.3)
    ax.set_xlabel(L("셀 수 (로그 눈금) — 막대 안 경계는 train | val | test 누적 위치",
                    "cells (log scale); internal boundaries mark cumulative train | val | test"))
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    handles = [
        Patch(facecolor=G1, edgecolor=G2, linewidth=0.7, label=names[0]),
        Patch(facecolor=G2, edgecolor=G3, linewidth=0.7, label=names[1]),
        Patch(facecolor="white", edgecolor=G3, linewidth=0.7, hatch="///", label=names[2]),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, borderaxespad=0.3, ncol=3)
    fig.text(0.0, -0.20,
             L("로그 눈금이므로 막대 안 구획의 길이는 분할 비율에 비례하지 않습니다 —\n"
               "경계 위치와 숫자를 읽으십시오. Zn-ion 은 코드 분할 기준 100셀입니다 (논문 Table 2 는 95).",
               "On a log axis the internal segment lengths are not proportional to the split ratio;\n"
               "read the boundaries and numbers. Zn-ion is 100 cells by the code split "
               "(paper Table 2 says 95)."),
             fontsize=6.4, color=G2)

    save(fig, "fig7_domain_sample_sizes")
    write_csv(
        "fig7_domain_sample_sizes",
        ["domain", "train_cells", "val_cells", "test_cells", "total_cells", "note"],
        [[d, tr, va, te, tr + va + te, note] for d, tr, va, te, note in SPLITS],
    )
    CHECKS.append("fig7: " + " · ".join(f"{d} {tr}/{va}/{te}={tr+va+te}"
                                        for d, tr, va, te, _ in SPLITS))


# ── 그림 8 — Li-ion 수명 라벨 분포 ───────────────────────────────────────
LIION_LABEL_FILES = {
    "CALCE": "CALCE_labels.json",
    "HNEI": "HNEI_labels.json",
    "HUST": "HUST_labels.json",
    "ISU-ILCC": "ISU-ILCC_labels.json",
    "MATR": "MATR_labels.json",
    "MICH": "MICH_labels.json",
    "MICH_EXP": "MICH_EXP_labels.json",
    "RWTH": "RWTH_labels.json",
    "SNL": "SNL_labels.json",
    "Stanford": "Stanford_labels.json",
    "Tongji": "Tongji_labels.json",
    "UL-PUR": "UL-PUR_labels.json",
    "XJTU": "XJTU_labels.json",
}


def fig8() -> None:
    labs = []
    for subset, fname in LIION_LABEL_FILES.items():
        d = jload(EXTRACT / "Life labels" / fname)
        for cell, v in d.items():
            labs.append((subset, cell, int(v)))
    assert len(labs) == 839, len(labs)

    # 분할 소속은 재집계된 CSV 에서 가져옵니다 (라벨 값은 위 JSON 이 정본).
    csvrows = {r["file"]: r for r in cload(ANALYSIS / "li_ion_label_vs_soh.csv")}
    mismatch = 0
    for subset, cell, v in labs:
        key = cell.replace("--", "-#") if subset == "Tongji" else cell
        alt = cell.replace("-#", "--")
        row = csvrows.get(cell) or csvrows.get(alt) or csvrows.get(key)
        if row is None or int(float(row["label"])) != v:
            mismatch += 1
    CHECKS.append(f"fig8: 배포 라벨 JSON {len(labs)}셀, li_ion_label_vs_soh.csv 와 불일치 {mismatch}건")

    vals = [v for _, _, v in labs]
    g40 = next(v for s, c, v in labs if c == "ISU-ILCC_G40C3.pkl")
    n_le100 = sum(1 for v in vals if v <= 100)

    fig, ax = plt.subplots(figsize=(W160, 66 * MM))
    lo, hi = min(vals), max(vals)
    bins = [10 ** e for e in [i * (math.log10(6000) - 0) / 40 for i in range(41)]]
    ax.hist(vals, bins=bins, color=G1, edgecolor=G2, linewidth=0.5)
    ax.set_xscale("log")
    ax.set_xlim(0.8, 6000)
    ax.set_xlabel(L("배포 수명 라벨 (사이클, 로그 눈금)", "shipped life label (cycles, log scale)"))
    ax.set_ylabel(L("셀 수", "cells"))

    ymax = ax.get_ylim()[1]
    ax.axvline(100, color=G3, lw=0.9, ls=(0, (4, 2)))
    ax.text(107, ymax * 0.94, L("규칙 5 경계: 라벨 ≤ 100 제외\n(data_loader.py:488)",
                                "rule 5: labels <= 100 dropped\n(data_loader.py:488)"),
            fontsize=6.6, color=G3, va="top")
    ax.annotate(L(f"ISU-ILCC_G40C3\n라벨 {g40} · 총 8,957 사이클\n분할 파일에는 train 으로 남아 있음",
                  f"ISU-ILCC_G40C3\nlabel {g40}, 8,957 cycles logged\nstill listed in the train split"),
                xy=(g40, 0.7), xytext=(2.0, ymax * 0.55), fontsize=6.6, color=G3,
                arrowprops=dict(arrowstyle="->", lw=0.7, color=G3))
    ax.set_title(L(f"n = {len(vals)}셀 · 최소 {lo} · 최대 {hi:,} · 라벨 ≤ 100 인 셀 {n_le100}개",
                   f"n = {len(vals)} cells; min {lo}, max {hi:,}; {n_le100} cells at label <= 100"),
                 fontsize=6.8, loc="left", color=G3, pad=5)

    save(fig, "fig8_liion_label_distribution")
    write_csv(
        "fig8_liion_label_distribution",
        ["subset", "cell", "life_label", "split", "n_cycles"],
        sorted(
            [[s, c, v,
              (csvrows.get(c) or csvrows.get(c.replace("-#", "--")) or {}).get("split", ""),
              (csvrows.get(c) or csvrows.get(c.replace("-#", "--")) or {}).get("n_cycles", "")]
             for s, c, v in labs],
            key=lambda r: r[2],
        ),
    )
    CHECKS.append(f"fig8: 라벨 최소 {lo} · 최대 {hi} · ≤100 인 셀 {n_le100}개 · G40C3 라벨 {g40}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    print(f"한글 폰트: {KOREAN or '없음 — 영문으로 대체'}")
    for fn in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8):
        print(f"[{fn.__name__}]")
        fn()
    print("\n── 재집계 확인값 ──")
    for c in CHECKS:
        print(" ", c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
