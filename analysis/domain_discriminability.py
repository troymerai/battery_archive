"""
BatteryLife 도메인 판별력 검증 (T2/T3/T4/T5)

라벨만으로 계산한다. 모델 학습을 하지 않는다.

- 도메인 매핑은 upstream/BatteryLife/data_provider/data_split_recorder.py 에서 읽는다.
- Dummy MAPE 는 upstream/BatteryLife/models/Dummy.py 의 정의를 그대로 따른다:
    * train 평균은 **데이터셋(=Life labels json 파일) 단위**로 계산한다.
    * 예측은 각 test 셀이 속한 데이터셋의 train 평균.
    * MAPE 는 sklearn.metrics.mean_absolute_percentage_error(y_true, y_pred).
- 비교용으로 도메인 전체 단일 평균(pooled) Dummy 도 같이 계산한다.

사용법:
    .venv-blife/Scripts/python.exe analysis/domain_discriminability.py
출력:
    analysis/out/domain_stats.json
    analysis/out/hist_<domain>.png
"""
import json
import os
import re
import sys

import numpy as np
from sklearn.metrics import mean_absolute_percentage_error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_PY = os.path.join(ROOT, "upstream", "BatteryLife", "data_provider", "data_split_recorder.py")
LABEL_DIR = os.path.join(ROOT, "data", "extracted", "Life labels")
OUT_DIR = os.path.join(ROOT, "analysis", "out")
os.makedirs(OUT_DIR, exist_ok=True)

RNG = np.random.default_rng(0)
N_BOOT = 1000


# ---------------------------------------------------------------- split lists
def load_splits():
    """data_split_recorder.split_recorder 의 클래스 속성을 그대로 읽는다."""
    src = open(SPLIT_PY, encoding="utf-8").read()
    ns = {}
    exec(compile(src, SPLIT_PY, "exec"), ns)
    rec = ns["split_recorder"]
    return {k: v for k, v in vars(rec).items() if k.endswith("_files")}


# --------------------------------------------------------------------- labels
def load_labels():
    out = {}
    for fn in sorted(os.listdir(LABEL_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(LABEL_DIR, fn), encoding="utf-8") as f:
            out[fn[: -len("_labels.json")]] = json.load(f)
    return out


def lookup(labels_of_group, name):
    """Dummy.py 와 동일한 키 보정: Tongji 는 '--' -> '-#'."""
    if "Tongji" in name:
        name = name.replace("--", "-#")
    return labels_of_group.get(name)


# ------------------------------------------------------------- domain mapping
# Li-ion = MIX_large 의 구성 데이터셋. MICH/MICH_EXP 는 Dummy.py 가 total_MICH
# 라벨 파일 하나로 묶어 평균을 낸다(=한 그룹).
LI_GROUPS = [
    # (split prefix, Life labels 파일 stem)
    ("UL_PUR", "UL-PUR"),
    ("RWTH", "RWTH"),
    ("HUST", "HUST"),
    ("MATR", "MATR"),
    ("Stanford", "Stanford"),
    ("Tongji", "Tongji"),
    ("ISU_ILCC", "ISU-ILCC"),
    ("CALCE", "CALCE"),
    ("HNEI", "HNEI"),
    ("SNL", "SNL"),
    ("MICH", "total_MICH"),
    ("MICH_EXP", "total_MICH"),
    ("XJTU", "XJTU"),
]

SEEDS = [2021, 42, 2024]


def domain_groups(domain, seed):
    """(split 변수 prefix, 라벨 파일 stem, Dummy 평균 그룹키) 리스트."""
    if domain == "Li-ion":
        # MICH 와 MICH_EXP 는 같은 평균 그룹('total_MICH')을 공유한다.
        return [(p, lab, lab) for p, lab in LI_GROUPS]
    if domain == "Zn-ion":
        pre = {2021: "ZNcoin", 42: "ZN_42", 2024: "ZN_2024"}[seed]
        return [(pre, "ZN-coin", "ZN-coin")]
    if domain == "CALB":
        pre = {2021: "CALB", 42: "CALB_42", 2024: "CALB_2024"}[seed]
        return [(pre, "CALB", "CALB")]
    if domain == "Na-ion":
        pre = {2021: "NAion_2021", 42: "NAion_42", 2024: "NAion_2024"}[seed]
        return [(pre, "NA-ion", "NA-ion")]
    raise ValueError(domain)


def collect(domain, seed, splits, labels):
    """도메인×seed 의 train/val/test 라벨과 Dummy 예측을 만든다."""
    groups = domain_groups(domain, seed)
    per_group = {}          # 평균 그룹키 -> train 라벨 목록
    rows = {"train": [], "val": [], "test": []}   # (그룹키, 셀이름, 라벨)

    for prefix, labfile, gkey in groups:
        lab = labels[labfile]
        for flag, suffix in (("train", "train"), ("val", "val"), ("test", "test")):
            var = f"{prefix}_{suffix}_files"
            if var not in splits:
                raise KeyError(var)
            for name in splits[var]:
                y = lookup(lab, name)
                if y is None:
                    continue          # Dummy.py 와 동일하게 라벨 없는 셀은 건너뛴다
                rows[flag].append((gkey, name, float(y)))

    for gkey, _, y in rows["train"]:
        per_group.setdefault(gkey, []).append(y)
    group_mean = {g: float(np.mean(v)) for g, v in per_group.items()}

    return rows, group_mean


def mape(y_true, y_pred):
    return float(mean_absolute_percentage_error(np.asarray(y_true), np.asarray(y_pred)))


def desc(v):
    v = np.asarray(v, dtype=float)
    if v.size == 0:
        return None
    q1, q3 = np.percentile(v, [25, 75])
    return {
        "n": int(v.size),
        "mean": float(v.mean()),
        "std": float(v.std(ddof=1)) if v.size > 1 else 0.0,
        "min": float(v.min()),
        "max": float(v.max()),
        "median": float(np.median(v)),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "cv": float(v.std(ddof=1) / v.mean()) if v.size > 1 else 0.0,
    }


def main():
    splits = load_splits()
    labels = load_labels()
    result = {"domains": {}, "label_files": sorted(labels), "n_cells_per_label_file":
              {k: len(v) for k, v in labels.items()}}

    for domain in ["Li-ion", "Zn-ion", "Na-ion", "CALB"]:
        result["domains"][domain] = {}
        for seed in SEEDS:
            rows, gmean = collect(domain, seed, splits, labels)

            ytr = [y for _, _, y in rows["train"]]
            yte = [y for _, _, y in rows["test"]]
            yva = [y for _, _, y in rows["val"]]

            # repo 정의: 데이터셋별 train 평균
            pred_te = [gmean[g] for g, _, _ in rows["test"]]
            pred_va = [gmean[g] for g, _, _ in rows["val"]]
            m_test = mape(yte, pred_te) if yte else None
            m_val = mape(yva, pred_va) if yva else None

            # 비교용: 도메인 전체 단일 평균
            pooled = float(np.mean(ytr))
            m_test_pooled = mape(yte, [pooled] * len(yte)) if yte else None

            # bootstrap 95% CI (test 셀 복원추출, 예측은 고정)
            ci = None
            if yte:
                yte_a = np.asarray(yte, dtype=float)
                pr_a = np.asarray(pred_te, dtype=float)
                n = yte_a.size
                boots = np.empty(N_BOOT)
                for b in range(N_BOOT):
                    idx = RNG.integers(0, n, n)
                    boots[b] = np.mean(np.abs(yte_a[idx] - pr_a[idx]) / np.abs(yte_a[idx]))
                ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]

            result["domains"][domain][str(seed)] = {
                "n_cells_train": len(ytr),
                "n_cells_val": len(yva),
                "n_cells_test": len(yte),
                "group_train_mean": gmean,
                "pooled_train_mean": pooled,
                "dummy_test_mape_repo": m_test,
                "dummy_val_mape_repo": m_val,
                "dummy_test_mape_pooled_mean": m_test_pooled,
                "dummy_test_mape_ci95": ci,
                "train_label_stats": desc(ytr),
                "test_label_stats": desc(yte),
                "val_label_stats": desc(yva),
                "all_label_stats": desc(ytr + yva + yte),
                "test_cells": [n for _, n, _ in rows["test"]],
            }

    with open(os.path.join(OUT_DIR, "domain_stats.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)

    # 히스토그램 (seed 2021 기준, 도메인 전체 셀)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, domain in zip(axes.ravel(), ["Li-ion", "Zn-ion", "Na-ion", "CALB"]):
        rows, _ = collect(domain, 2021, splits, labels)
        y = [v for f in ("train", "val", "test") for _, _, v in rows[f]]
        ax.hist(y, bins=40, color="#4878A8")
        s = desc(y)
        ax.set_title(f"{domain}  n={s['n']}  mean={s['mean']:.0f}  CV={s['cv']:.2f}")
        ax.set_xlabel("life label (cycles)")
        ax.set_ylabel("cells")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "hist_domains.png"), dpi=130)

    # 도메인별 개별 파일도 저장
    for domain in ["Li-ion", "Zn-ion", "Na-ion", "CALB"]:
        rows, _ = collect(domain, 2021, splits, labels)
        ytr = [v for _, _, v in rows["train"]]
        yte = [v for _, _, v in rows["test"]]
        f2, a2 = plt.subplots(figsize=(6, 4))
        a2.hist([ytr, yte], bins=30, stacked=True, label=["train", "test"],
                color=["#4878A8", "#D1885C"])
        a2.legend()
        a2.set_title(f"{domain} life labels (seed 2021)")
        a2.set_xlabel("life label (cycles)")
        a2.set_ylabel("cells")
        f2.tight_layout()
        f2.savefig(os.path.join(OUT_DIR, f"hist_{domain}.png"), dpi=130)
        plt.close(f2)

    print("written:", OUT_DIR)


if __name__ == "__main__":
    main()
