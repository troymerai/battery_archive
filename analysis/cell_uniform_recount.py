"""셀 균등 재집계 선행 분석 — 셀당 샘플 수 분포와 도메인별 분할 대조.

두 가지를 계산한다.

1. **셀당 샘플 수** — `Dataset_original.read_samples_from_one_cell`
   (`upstream/BatteryLife/data_provider/data_loader.py:480-528`) 이 한 셀에서
   내놓는 샘플 개수. 이 값이 셀마다 다르면 샘플 가중 지표가 수명 가중이 되고,
   전부 같으면 샘플 가중과 셀 균등이 대수적으로 같아진다.

2. **도메인별 3회 반복의 분할 동일성** — `CALB`/`CALB42`/`CALB2024` 처럼
   seed 마다 다른 분할을 쓰는지, `MIX_large` 처럼 한 분할을 공유하는지.

학습·추론을 돌리지 않는다. 라벨 JSON 과 pkl 의 사이클 수만 읽는다.
"""

from __future__ import annotations

import json
import pickle
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPLIT_SRC = REPO / "upstream/BatteryLife/data_provider/data_split_recorder.py"
ROOT = REPO / "data/extracted"
LABELS = ROOT / "Life labels"

# args 기본값 — .build/batterylife 의 36개 스크립트가 모두 이 값을 쓴다.
SEQ_LEN = 1
EARLY_CYCLE_THRESHOLD = 100

# Li-ion 36회는 상위 `MIX_large` 가 아니라 `.build` 진입점이 만드는
# `MIX_large_841` 로 돌았다. 라벨이 배포되지 않은 6셀을 뺀 판이다
# (`.build/batterylife/run_main_nodeepspeed.py:97-105`). 그중 test 에 있는 것은
# `MICH_16R...` 1개라서 **실제로 쓰인 셀 집합은 달라지지 않는다** — 상위 판에서도
# 그 셀은 라벨없음으로 걸러진다. 목록 개수(163 vs 162)만 달라진다.
MIX_841_EXCLUDED = [
    "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl",
    "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl",
    "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl",
    "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl",
    "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl",
    "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl",
]

# 도메인 -> seed -> data_loader.py 의 dataset 이름과 split_recorder 접두사.
# 대응 근거: upstream/BatteryLife/data_provider/data_loader.py:164-203
DOMAINS = {
    "Li-ion": {2021: ("MIX_large_841", "MIX_large"), 42: ("MIX_large_841", "MIX_large"), 2024: ("MIX_large_841", "MIX_large")},
    "Zn-ion": {2021: ("ZN-coin", "ZNcoin"), 42: ("ZN-coin42", "ZN_42"), 2024: ("ZN-coin2024", "ZN_2024")},
    "Na-ion": {2021: ("NAion", "NAion_2021"), 42: ("NAion42", "NAion_42"), 2024: ("NAion2024", "NAion_2024")},
    "CALB": {2021: ("CALB", "CALB"), 42: ("CALB42", "CALB_42"), 2024: ("CALB2024", "CALB_2024")},
}

# 도메인 -> 시험 집합의 seen/unseen 기록 파일 (data_loader.py:211-226)
SEEN_UNSEEN = {
    ("Zn-ion", 42): "cal_for_test_ZN42.json",
    ("Zn-ion", 2024): "cal_for_test_ZN2024.json",
    ("CALB", 42): "cal_for_test_CALB42.json",
    ("CALB", 2024): "cal_for_test_CALB2024.json",
    ("Na-ion", 2021): "cal_for_test_NA2021.json",
    ("Na-ion", 42): "cal_for_test_NA42.json",
    ("Na-ion", 2024): "cal_for_test_NA2024.json",
}
SEEN_UNSEEN_DEFAULT = "cal_for_test.json"

# pkl 이 사는 하위 디렉터리 (data_loader.py:374-415 의 prefix 분기와 동일)
PREFIX_DIR = {
    "MATR": "MATR", "HUST": "HUST", "SNL": "SNL", "CALCE": "CALCE", "HNEI": "HNEI",
    "RWTH": "RWTH", "UL-PUR": "UL_PUR", "Tongji1": "Tongji", "Tongji2": "Tongji",
    "Tongji3": "Tongji", "Stanford": "Stanford", "ISU-ILCC": "ISU_ILCC", "XJTU": "XJTU",
    "ZN-coin": "ZN-coin", "CALB": "CALB", "NA-ion": "NA-ion",
}


def load_split_recorder():
    """split_recorder 를 그 자리에서 실행해 클래스만 꺼낸다 (import 부작용 없음)."""
    ns: dict = {}
    exec(compile(SPLIT_SRC.read_text(encoding="utf-8"), str(SPLIT_SRC), "exec"), ns)
    return ns["split_recorder"]


def pkl_path(file_name: str) -> Path:
    prefix = file_name.split("_")[0]
    if prefix.startswith("MICH"):
        return ROOT / "total_MICH" / file_name
    if prefix.startswith("SMICH"):
        return ROOT / "MICH_EXP" / file_name[1:]
    return ROOT / PREFIX_DIR[prefix] / file_name


def label_file(file_name: str) -> tuple[Path, str]:
    """(라벨 JSON 경로, 조회 키) — data_loader.py:417-431 과 같은 규칙."""
    prefix = file_name.split("_")[0]
    if prefix == "MICH":
        return LABELS / "total_MICH_labels.json", file_name
    if prefix.startswith("Tongji"):
        return LABELS / "Tongji_labels.json", file_name.replace("--", "-#")
    return LABELS / f"{prefix}_labels.json", file_name


_label_cache: dict[Path, dict] = {}


def get_eol(file_name: str):
    path, key = label_file(file_name)
    if path not in _label_cache:
        _label_cache[path] = json.loads(path.read_text(encoding="utf-8"))
    return _label_cache[path].get(key)


_cycle_cache: dict[str, int] = {}


def get_valid_cycle_number(file_name: str) -> int:
    """read_cell_df 의 valid_cycle_number = len(data['cycle_data'])."""
    if file_name not in _cycle_cache:
        with open(pkl_path(file_name), "rb") as fh:
            data = pickle.load(fh)
        _cycle_cache[file_name] = len(data["cycle_data"])
    return _cycle_cache[file_name]


def n_samples_for_cell(file_name: str):
    """이 셀이 시험 집합에 내놓는 샘플 수. 제외되면 (0, 사유)."""
    eol = get_eol(file_name)
    if eol is None:
        return 0, "라벨없음"
    # read_samples_from_one_cell:488 — eol <= early_cycle_threshold 면 통째로 제외
    if eol <= EARLY_CYCLE_THRESHOLD:
        return 0, f"eol={eol} <= {EARLY_CYCLE_THRESHOLD}"
    vcn = get_valid_cycle_number(file_name)
    # for i in range(seq_len, threshold+1): break if i >= eol or i > valid_cycle_number
    n = 0
    for i in range(SEQ_LEN, EARLY_CYCLE_THRESHOLD + 1):
        if i >= eol or i > vcn:
            break
        n += 1
    return n, ""


def describe(counts: list[int]) -> str:
    if not counts:
        return "(없음)"
    return (f"n={len(counts)} 합={sum(counts)} 최소={min(counts)} "
            f"중앙={statistics.median(counts):g} 최대={max(counts)}")


def main() -> int:
    sr = load_split_recorder()
    out: dict = {"per_domain": {}, "split_identity": {}}

    for domain, seeds in DOMAINS.items():
        print(f"\n{'='*70}\n{domain}\n{'='*70}")
        split_sets = {}
        for seed, (ds_name, prefix) in seeds.items():
            tr = list(getattr(sr, f"{prefix}_train_files"))
            va = list(getattr(sr, f"{prefix}_val_files"))
            te = list(getattr(sr, f"{prefix}_test_files"))
            if ds_name == "MIX_large_841":
                tr = [f for f in tr if f not in MIX_841_EXCLUDED]
                va = [f for f in va if f not in MIX_841_EXCLUDED]
                te = [f for f in te if f not in MIX_841_EXCLUDED]
            split_sets[seed] = {"train": tr, "val": va, "test": te, "dataset": ds_name}

        # --- 분할 동일성 -------------------------------------------------
        ids = sorted(seeds)
        base = ids[0]
        same_test = all(set(split_sets[s]["test"]) == set(split_sets[base]["test"]) for s in ids)
        same_train = all(set(split_sets[s]["train"]) == set(split_sets[base]["train"]) for s in ids)
        out["split_identity"][domain] = {
            "dataset_names": {s: split_sets[s]["dataset"] for s in ids},
            "test_identical_across_seeds": same_test,
            "train_identical_across_seeds": same_train,
            "test_sizes": {s: len(split_sets[s]["test"]) for s in ids},
            "train_sizes": {s: len(split_sets[s]["train"]) for s in ids},
        }
        print(f"  dataset 이름: {[split_sets[s]['dataset'] for s in ids]}")
        print(f"  train 셀수 {[len(split_sets[s]['train']) for s in ids]} / "
              f"test 셀수 {[len(split_sets[s]['test']) for s in ids]}")
        print(f"  seed 간 train 동일: {same_train} · test 동일: {same_test}")

        # --- 셀당 샘플 수 -------------------------------------------------
        out["per_domain"][domain] = {}
        for seed in ids:
            te = split_sets[seed]["test"]
            su_name = SEEN_UNSEEN.get((domain, seed), SEEN_UNSEEN_DEFAULT)
            su_path = ROOT / "seen_unseen_labels" / su_name
            su = json.loads(su_path.read_text(encoding="utf-8")) if su_path.exists() else {}

            rows, dropped = [], []
            for fn in te:
                n, why = n_samples_for_cell(fn)
                if n == 0:
                    dropped.append((fn, why))
                    continue
                rows.append({"file": fn, "n_samples": n,
                             "eol": get_eol(fn),
                             "n_cycles": get_valid_cycle_number(fn),
                             "seen_unseen": su.get(fn, "?")})
            counts = [r["n_samples"] for r in rows]
            seen_c = [r["n_samples"] for r in rows if r["seen_unseen"] == "seen"]
            unseen_c = [r["n_samples"] for r in rows if r["seen_unseen"] == "unseen"]

            # 샘플 가중 w_s(c)=n_c/N 과 셀 균등 w_u(c)=1/C 의 차이.
            # 두 지표의 차는 Δ = Σ_c (w_s−w_u)·ē_c 이고 Σ(w_s−w_u)=0 이므로
            # |Δ| <= (1/2)·Σ|w_s−w_u| · (ē_c 의 최대−최소). L1 이 0 이면 항등이다.
            N, C = sum(counts), len(counts)
            l1 = sum(abs(c / N - 1 / C) for c in counts) if N else 0.0
            out["per_domain"][domain][seed] = {
                "dataset": split_sets[seed]["dataset"],
                "seen_unseen_file": su_name,
                "test_cells_listed": len(te),
                "test_cells_used": len(rows),
                "dropped": dropped,
                "total_samples": sum(counts),
                "min": min(counts) if counts else None,
                "median": statistics.median(counts) if counts else None,
                "max": max(counts) if counts else None,
                "all_equal_100": bool(counts) and all(c == EARLY_CYCLE_THRESHOLD for c in counts),
                "all_counts_equal": bool(counts) and len(set(counts)) == 1,
                "weight_l1_deviation": l1,
                "metrics_algebraically_identical": bool(counts) and len(set(counts)) == 1,
                "seen_cells": len(seen_c), "unseen_cells": len(unseen_c),
                "seen_samples": sum(seen_c), "unseen_samples": sum(unseen_c),
                "cells": rows,
            }
            verdict = "항등" if len(set(counts)) == 1 else f"L1={l1:.6f}"
            print(f"  seed {seed:>4} [{split_sets[seed]['dataset']:>13}] test: {describe(counts)}"
                  f"  seen {len(seen_c)}셀/{sum(seen_c)} · unseen {len(unseen_c)}셀/{sum(unseen_c)}"
                  f"  [샘플가중 vs 셀균등: {verdict}]"
                  + (f"  제외 {len(dropped)}" if dropped else ""))
            for fn, why in dropped:
                print(f"        제외: {fn} — {why}")

    dest = REPO / "experiments/results/cell_sample_counts.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\n기록: {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
