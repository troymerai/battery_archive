"""experiments/results/curves/*.json 으로 보고서용 그림 6종을 만듭니다.

학습하지 않습니다. 로그에서 뽑아 둔 값만 씁니다.
없는 값은 추정하지 않습니다 — 필드가 없으면 그 그림을 만들지 않습니다.

    .venv-blife/Scripts/python.exe -m train.figures

출력: figures/fig1..fig6*.png (150 dpi, 흰 배경)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CURVES = ROOT / "experiments" / "results" / "curves"
FIGS = ROOT / "figures"

# ── 스타일 ───────────────────────────────────────────────────────────────
# matplotlib 기본 색상 순환을 씁니다 (논문·동료 그래프와 맞춤).
#   Train=C0 · Validation=C1 · Test=C2
#   최적 검증 에폭=C2 파선 · 조기 종료=C4 일점쇄선 · 기준선=C3 점선
_INSTALLED = {f.name for f in fm.fontManager.ttflist}
KOREAN = next((n for n in ("Malgun Gothic", "NanumGothic", "Gulim", "Batang")
               if n in _INSTALLED), None)
if KOREAN:
    plt.rcParams["font.family"] = KOREAN
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["figure.dpi"] = 150

NOTES: list[str] = []


def L(ko: str, en: str) -> str:
    """한글 폰트가 없으면 영문으로 대체합니다."""
    return ko if KOREAN else en


def load(stem: str) -> dict:
    return json.loads((CURVES / f"{stem}.json").read_text(encoding="utf-8"))


def load_all() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CURVES.glob("*.json"))]


def main_run(model: str, domain: str, seed: int) -> dict:
    """정본(main) 실행을 파일명이 아니라 `group` 필드로 고릅니다.

    Zn-ion 은 문서 지정 학습률 판과 낮춘 판이 둘 다 남아 있어 파일명만으로
    고르면 정본이 아닌 쪽을 집습니다 (`train/regroup_znion.py`).
    """
    hits = [r for r in load_all()
            if r["group"] == "main" and r["model"] == model
            and r["domain"] == domain and r["seed"] == seed]
    if len(hits) != 1:
        raise LookupError(f"main 실행이 {len(hits)}건입니다: {model}·{domain}·s{seed}")
    return hits[0]


def series(rec: dict, key: str) -> tuple[list[int], list[float]]:
    xs, ys = [], []
    for e in rec["epochs"]:
        if e.get(key) is not None:
            xs.append(e["epoch"])
            ys.append(e[key])
    return xs, ys


def cond_title(rec: dict, extra: str = "") -> str:
    c = rec["conditions"]
    lr = f"{c['learning_rate']:g}".replace("0.0005", "5e-4").replace("5e-05", "5e-5")
    return (f"{rec['model']}_{rec['domain']}_s{rec['seed']}_v11"
            f"_bs{c['batch_size']}_lr{lr}_patience{c['patience']}{extra}")


def grid(ax) -> None:
    ax.grid(alpha=0.3)


def int_xticks(ax) -> None:
    from matplotlib.ticker import MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))


def fmt_lr(lr: float) -> str:
    return {5e-05: "5e-5", 5e-04: "5e-4", 1e-03: "1e-3"}.get(lr, f"{lr:g}")


def save(fig, name: str) -> None:
    FIGS.mkdir(exist_ok=True)
    fig.savefig(FIGS / name, bbox_inches="tight")
    plt.close(fig)
    print(f"  저장 figures/{name}")


# ── 그림 1 — Zn-ion 학습률 대비 ─────────────────────────────────────────
def fig1() -> None:
    # 이 그림만은 묶음과 무관하게 두 학습률을 나란히 놓는 것이 목적이라
    # 파일을 직접 지정합니다.
    a = load("CPMLP_Zn-ion_s2021")             # diagnostic, 문서 학습률 5e-4
    b = load("CPMLP_Zn-ion_s2021__lr5e-05")    # main(정본), 낮춘 학습률 5e-5
    c = load("CPMLP_Zn-ion_s2021__x3_patience")  # diagnostic, 5e-4 · 50에폭 강제

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    conds = [
        (a, "C0", "-", L("lr 5e-4 (문서값, patience 5)", "lr 5e-4 (paper, patience 5)")),
        (c, "C0", "--", L("lr 5e-4 · 50에폭 강제 (patience 100)",
                          "lr 5e-4, forced 50 epochs (patience 100)")),
        (b, "C1", "-", L("lr 5e-5 (낮춘 값, patience 5)", "lr 5e-5 (lowered, patience 5)")),
    ]
    for rec, color, ls, label in conds:
        x, y = series(rec, "train_loss")
        ax1.plot(x, y, color=color, ls=ls, marker="o", ms=3, lw=1.6, label=label)
        x, y = series(rec, "test_mape")
        ax2.plot(x, y, color=color, ls=ls, marker="o", ms=3, lw=1.6, label=label)

    ax1.axhline(1.0, color="C3", ls=":", lw=1.5)
    ax1.annotate(L("Train Loss = 1.00", "Train Loss = 1.00"), xy=(0.985, 1.0),
                 xycoords=("axes fraction", "data"), ha="right", va="bottom",
                 color="C3", fontsize=9)
    ax1.set_ylabel(L("Train Loss (MSE)", "Train Loss (MSE)"))
    ax1.set_title(L("그림 1 — Zn-ion 학습률 대비 · CPMLP_Zn-ion_s2021_v11_bs128",
                    "Fig 1 — Zn-ion learning rate · CPMLP_Zn-ion_s2021_v11_bs128"),
                  fontsize=12)
    grid(ax1)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_ylabel("Test MAPE")
    ax2.set_xlabel(L("에폭", "Epoch"))
    grid(ax2)
    ax2.legend(frameon=True, fontsize=9)
    save(fig, "fig1_znion_lr.png")


# ── 그림 2 — 도메인 4종 학습 곡선 ───────────────────────────────────────
def fig2() -> None:
    recs = [main_run("CPMLP", d, 2021) for d in ("CALB", "Na-ion", "Zn-ion", "Li-ion")]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, rec in zip(axes.ravel(), recs):
        for key, color, label in (("train_mape", "C0", "Train MAPE"),
                                  ("vali_mape", "C1", "Validation MAPE"),
                                  ("test_mape", "C2", "Test MAPE")):
            x, y = series(rec, key)
            ax.plot(x, y, color=color, marker="o", ms=3, lw=1.5, label=label)
        if rec["best_val_epoch"] is not None:
            ax.axvline(rec["best_val_epoch"], color="C2", ls="--", lw=1.2,
                       label=L(f"최적 검증 에폭 {rec['best_val_epoch']}",
                               f"best val epoch {rec['best_val_epoch']}"))
        c = rec["conditions"]
        lr = fmt_lr(c["learning_rate"])
        # 네 칸의 조건이 같지 않습니다 — Zn-ion 만 학습률이 다릅니다.
        odd = "  [조건 다름]" if c["learning_rate"] != 5e-05 else ""
        ax.set_title(
            L(f"{rec['domain']} (시험 {rec['test_cells']}셀) · bs{c['batch_size']} lr{lr}{odd}",
              f"{rec['domain']} ({rec['test_cells']} test cells) · bs{c['batch_size']} lr{lr}"
              f"{'  (differing condition)' if odd else ''}"),
            fontsize=10, color="C3" if odd else "black")
        ax.set_xlabel(L("에폭", "Epoch"))
        ax.set_ylabel("MAPE")
        int_xticks(ax)
        grid(ax)
        ax.legend(frameon=True, fontsize=8)
    fig.suptitle(L("그림 2 — CPMLP seed 2021 · 도메인 4종 (y축은 칸마다 자유)",
                   "Fig 2 — CPMLP seed 2021 · four domains (independent y axes)"),
                 fontsize=12)
    fig.tight_layout()
    save(fig, "fig2_domains.png")


# ── 그림 3 — CALB 3 seed 흔들림 ─────────────────────────────────────────
def fig3() -> None:
    recs = [load(f"CPMLP_CALB_s{s}") for s in (42, 2021, 2024)]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, rec in enumerate(recs):
        c = rec["conditions"]
        x, y = series(rec, "test_mape")
        ax.plot(x, y, color=f"C{i}", marker="o", ms=3.5, lw=1.6,
                label=f"seed {rec['seed']} · bs{c['batch_size']} d_model{c['d_model']} "
                      f"e{c['e_layers']}/d{c['d_layers']} drop{c['dropout']:g}")
        # 최종 보고값은 마지막 에폭이 아니라 '최적 검증 에폭'의 값입니다.
        # 오른쪽 끝에 달되, 높이는 그 에폭의 값에 맞추고 점선으로 이어 둡니다.
        be = rec["best_val_epoch"]
        final = rec["final"]["test_mape"]
        ax.plot([be], [final], color=f"C{i}", marker="o", ms=9, mfc="none", mew=1.8)
        ax.plot([be, x[-1]], [final, final], color=f"C{i}", ls=":", lw=0.9, alpha=0.7)
        ax.annotate(f"{final:.4f}", xy=(x[-1], final), xytext=(7, 0),
                    textcoords="offset points", color=f"C{i}", fontsize=9,
                    va="center", fontweight="bold")
        ax.axvline(be, color=f"C{i}", ls="--", lw=0.9, alpha=0.5)
    int_xticks(ax)
    ax.set_xlabel(L("에폭", "Epoch"))
    ax.set_ylabel("Test MAPE")
    ax.set_title(L("그림 3 — CPMLP_CALB 3 seed · v11_lr5e-5_patience5 · 시험 5셀\n"
                   "빈 원 = 최적 검증 에폭의 값 = 오른쪽 끝 주석의 최종 보고값 "
                   "(파선 = 그 에폭)",
                   "Fig 3 — CPMLP_CALB 3 seeds · v11_lr5e-5_patience5 · 5 test cells\n"
                   "open circle = value at the best val epoch = the reported number at right "
                   "(dashed = that epoch)"), fontsize=11)
    ax.margins(x=0.08)
    grid(ax)
    ax.legend(frameon=True, fontsize=9)
    save(fig, "fig3_calb_seeds.png")


# ── 그림 4 — Li-ion 대 CALB (같은 y축) ──────────────────────────────────
def fig4() -> None:
    li, calb = load("CPMLP_Li-ion_s2021"), load("CPMLP_CALB_s2021")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, rec in enumerate((li, calb)):
        x, y = series(rec, "test_mape")
        ax.plot(x, y, color=f"C{i}", marker="o", ms=3.5, lw=1.6,
                label=L(f"{rec['domain']} ({rec['test_cells']}셀) · bs{rec['conditions']['batch_size']}",
                        f"{rec['domain']} ({rec['test_cells']} cells) · bs{rec['conditions']['batch_size']}"))
        ax.axvline(rec["best_val_epoch"], color=f"C{i}", ls="--", lw=0.9, alpha=0.5)
    int_xticks(ax)
    ax.set_xlabel(L("에폭", "Epoch"))
    ax.set_ylabel("Test MAPE")
    # 에폭별 변동과 반복 간 흩어짐은 다른 얘기입니다. 표본 크기와 관련된
    # 것은 뒤쪽이므로, 이 그림만 보고 뒤집어 읽지 않도록 부제에 적어 둡니다.
    ax.set_title(L("그림 4 — CPMLP seed 2021 · Li-ion 대 CALB (같은 y축)\n"
                   "v11_lr5e-5_patience5 · 파선 = 최적 검증 에폭\n"
                   "이 그림은 한 실행 안의 에폭별 변동입니다. "
                   "반복 간 흩어짐은 그림 3 을 보십시오.",
                   "Fig 4 — CPMLP seed 2021 · Li-ion vs CALB (shared y axis)\n"
                   "v11_lr5e-5_patience5 · dashed = best val epoch\n"
                   "This shows epoch-to-epoch variation within one run. "
                   "For run-to-run spread see Fig 3."), fontsize=11)
    grid(ax)
    ax.legend(frameon=True, fontsize=9)
    save(fig, "fig4_liion_vs_calb.png")


# ── 그림 5 — 조기 종료 시점 분포 ────────────────────────────────────────
DOMAIN_ORDER = ["CALB", "Na-ion", "Zn-ion", "Li-ion"]
MODEL_ORDER = ["MLP", "CPMLP", "CPTransformer"]
SEED_ORDER = [42, 2021, 2024]


def fig5() -> list[tuple[str, int, int, int]]:
    main = [r for r in load_all() if r["group"] == "main"]
    main.sort(key=lambda r: (DOMAIN_ORDER.index(r["domain"]),
                             MODEL_ORDER.index(r["model"]),
                             SEED_ORDER.index(r["seed"])))
    fig, ax = plt.subplots(figsize=(13, 6))
    labels, gaps = [], []
    for i, r in enumerate(main):
        last, best = r["last_epoch"], r["best_val_epoch"]
        ax.plot([i, i], [best, last], color="0.6", lw=1.0, zorder=1)
        ax.scatter(i, best, color="C2", marker="o", s=34, zorder=3,
                   label=L("최적 검증 에폭", "best val epoch") if i == 0 else None)
        ax.scatter(i, last, color="C4", marker="v", s=34, zorder=3,
                   label=L("실제 종료 에폭", "last epoch") if i == 0 else None)
        labels.append(f"{r['domain']}·{r['model']}·s{r['seed']}")
        gaps.append((labels[-1], last, best, last - best))
    # 도메인 경계
    for i in range(1, len(main)):
        if main[i]["domain"] != main[i - 1]["domain"]:
            ax.axvline(i - 0.5, color="0.85", lw=1.0)
    ax.set_xticks(range(len(main)))
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_ylabel(L("에폭", "Epoch"))
    ax.set_title(L("그림 5 — 36회 정규 실행의 조기 종료 시점 (patience 5, 최대 100에폭)\n"
                   "세로선 = 최적 검증 에폭과 실제 종료 에폭의 간격",
                   "Fig 5 — early-stop points across the 36 main runs (patience 5, max 100 epochs)\n"
                   "vertical line = gap between best val epoch and last epoch"), fontsize=11)
    grid(ax)
    ax.legend(frameon=True, fontsize=9)
    save(fig, "fig5_early_stop.png")
    return gaps


# ── 그림 6 — Seen 대 Unseen ─────────────────────────────────────────────
def fig6() -> None:
    recs = [load(f"{m}_Li-ion_s2021") for m in MODEL_ORDER]
    have_epochwise = any(e.get("test_seen_mape") is not None
                         for r in recs for e in r["epochs"])
    if have_epochwise:
        raise AssertionError("에폭별 Seen/Unseen 이 생겼습니다 — 그림 6 을 곡선으로 다시 짜십시오")
    NOTES.append("그림 6: 에폭별 Seen/Unseen 이 로그에 없습니다. "
                 "최종 보고값(최적 검증 에폭)만 막대로 그렸습니다.")

    import numpy as np
    x = np.arange(len(recs))
    w = 0.36
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    seen = [r["final"]["test_seen_mape"] for r in recs]
    unseen = [r["final"]["test_unseen_mape"] for r in recs]
    ax1.bar(x - w / 2, seen, w, color="C0", label="Seen")
    ax1.bar(x + w / 2, unseen, w, color="C1", label="Unseen")
    for xi, (s, u) in enumerate(zip(seen, unseen)):
        ax1.text(xi - w / 2, s, f"{s:.4f}", ha="center", va="bottom", fontsize=8)
        ax1.text(xi + w / 2, u, f"{u:.4f}", ha="center", va="bottom", fontsize=8)
    ax1.set_ylabel("Test MAPE")
    ax1.set_title(L("Test MAPE (낮을수록 좋음)", "Test MAPE (lower is better)"), fontsize=10)

    s15 = [r["final"]["test_seen_acc15"] for r in recs]
    u15 = [r["final"]["test_unseen_acc15"] for r in recs]
    ax2.bar(x - w / 2, s15, w, color="C0", label="Seen")
    ax2.bar(x + w / 2, u15, w, color="C1", label="Unseen")
    for xi, (s, u) in enumerate(zip(s15, u15)):
        ax2.text(xi - w / 2, s, f"{s:.2f}", ha="center", va="bottom", fontsize=8)
        ax2.text(xi + w / 2, u, f"{u:.2f}", ha="center", va="bottom", fontsize=8)
    ax2.set_ylabel("Test 15%-Acc (%)")
    ax2.set_title(L("Test 15%-정확도 (높을수록 좋음)", "Test 15%-accuracy (higher is better)"),
                  fontsize=10)

    for ax in (ax1, ax2):
        ax.set_xticks(x)
        ax.set_xticklabels(MODEL_ORDER)
        grid(ax)
        ax.legend(frameon=True, fontsize=9)
    fig.suptitle(L("그림 6 — Li-ion(MIX_large_841) seed 2021 · Seen 대 Unseen\n"
                   "v11_lr5e-5_patience5 · 에폭별 값이 로그에 없어 최종 보고값만 막대로 그렸습니다",
                   "Fig 6 — Li-ion (MIX_large_841) seed 2021 · Seen vs Unseen\n"
                   "v11_lr5e-5_patience5 · no per-epoch values in the logs; final values only"),
                 fontsize=11)
    fig.tight_layout()
    save(fig, "fig6_seen_unseen.png")


def main() -> None:
    if not KOREAN:
        NOTES.append("한글 폰트를 찾지 못해 영문 라벨로 그렸습니다.")
    print(f"한글 폰트: {KOREAN or '없음 — 영문 라벨로 대체'}")
    fig1()
    fig2()
    fig3()
    fig4()
    gaps = fig5()
    fig6()

    print("\n그림 5 — 종료 에폭과 최적 에폭이 가장 벌어진 실행")
    for name, last, best, gap in sorted(gaps, key=lambda g: -g[3])[:8]:
        print(f"  {name:<34} 종료 {last:>3} · 최적 {best:>3} · 간격 {gap}")
    print("\n비고")
    for n in NOTES:
        print(f"  - {n}")


if __name__ == "__main__":
    main()
