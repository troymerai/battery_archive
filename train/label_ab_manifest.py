"""A/B 라벨 매니페스트 — 배포 라벨 A 와 재생성 라벨 B 가 셀 단위로 어떻게 다른가.

**이것 없이는 나중에 성능 차이를 해석할 수 없다.** 라벨이 바뀌면 지표만
바뀌는 것이 아니라 **표본 자체**가 바뀔 수 있기 때문이다.

* `read_samples_from_one_cell` 은 `eol <= early_cycle_threshold(100)` 인 셀을
  **통째로 버린다** (`data_provider/data_loader.py:488`). 이 문서가 "규칙 5"
  라 부르는 필터다
* 라벨이 없으면(`eol is None`) 그 셀도 버려진다 (`:342-344`)
* 그래서 라벨이 100 을 넘나들거나 조회에 실패하면 **그 셀이 학습·평가에서
  나타나거나 사라진다.** 성능 비교 이전의 문제다

두 가지 시선으로 본다
---------------------
1. **로더 시선** — 학습 코드가 실제로 무엇을 받는가.
   `data_loader.py:417-431` 의 조회 규칙(접두사로 파일 고르기, Tongji 는
   `--` → `-#` 치환)을 그대로 흉내 낸다. **규칙 5 판정은 이쪽이 정본이다.**
2. **파일 시선** — 라벨 값 자체가 얼마나 다른가. 셀 이름이 서브셋 사이에
   겹치므로(Stanford 와 Stanford_2 가 38셀 공유) `(서브셋, 셀)` 로 센다.
   Tongji 는 두 판의 키 표기가 달라 `-#` 로 맞춘 뒤 비교한다.

A 는 `data/extracted/Life labels/`, B 는 `data/labels_B/`. **둘 다 읽기만 한다.**

    py -3.12 train/label_ab_manifest.py
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
A_DIR = REPO / "data/extracted/Life labels"
B_DIR = REPO / "data/labels_B"
EXTRACTED = REPO / "data/extracted"
SPLIT_SRC = REPO / "upstream/BatteryLife/data_provider/data_split_recorder.py"
OUT = REPO / "experiments/results/label_ab_manifest.json"

EARLY_CYCLE_THRESHOLD = 100

# B 의 `ISU_ILCC_labels.json` 은 증거로 남긴 중복(labels_B/README.md). 값 비교에서 뺀다.
SKIP_B_FILES = {"ISU_ILCC_labels.json"}

MIX_841_EXCLUDED = {
    "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl",
    "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl",
    "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl",
    "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl",
    "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl",
    "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl",
}


# ---------------------------------------------------------------- 공통

def finite(v) -> bool:
    return v is not None and isinstance(v, (int, float)) and math.isfinite(v)


def passes_rule5(v) -> bool:
    """`data_loader.py:488` 과 같은 판정. 없거나 비유한이면 탈락."""
    return finite(v) and v > EARLY_CYCLE_THRESHOLD


def load_dir(d: Path, skip: set[str]) -> dict[str, dict]:
    out = {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_") or p.name in skip:
            continue
        out[p.name] = json.loads(p.read_text(encoding="utf-8"))
    return out


def loader_lookup(file_name: str, store: dict[str, dict]):
    """`data_loader.py:417-431` 을 그대로 흉내 낸다.

    돌려주는 값: (eol 또는 None, 읽으려 한 파일명, 조회 키)
    """
    prefix = file_name.split("_")[0]
    if prefix == "MICH":
        fname, key = "total_MICH_labels.json", file_name
    elif prefix.startswith("Tongji"):
        fname, key = "Tongji_labels.json", file_name.replace("--", "-#")
    else:
        fname, key = f"{prefix}_labels.json", file_name
    table = store.get(fname)
    if table is None:
        return None, fname, key
    return table.get(key), fname, key


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


# ---------------------------------------------------------------- 본체

def main() -> int:
    A = load_dir(A_DIR, set())
    B = load_dir(B_DIR, SKIP_B_FILES)

    # ===== 시선 2: 파일 시선 — 값이 얼마나 다른가 =====================
    # (서브셋, 셀) 로 센다. Tongji 는 `-#` 로 맞춘다.
    def canon(subset: str, cell: str) -> str:
        return cell.replace("--", "-#") if subset.startswith("Tongji") else cell

    pairs: dict[str, dict] = {}
    for fname in sorted(set(A) | set(B)):
        subset = fname.replace("_labels.json", "")
        a_map, b_map = A.get(fname, {}), B.get(fname, {})
        a_canon = {canon(subset, k): v for k, v in a_map.items()}
        b_canon = {canon(subset, k): v for k, v in b_map.items()}
        for cell in sorted(set(a_canon) | set(b_canon)):
            a, b = a_canon.get(cell), b_canon.get(cell)
            in_a, in_b = cell in a_canon, cell in b_canon
            rec = {"subset": subset, "cell": cell, "a": a, "b": b,
                   "in_a": in_a, "in_b": in_b,
                   "a_pass_rule5": passes_rule5(a), "b_pass_rule5": passes_rule5(b)}
            if finite(a) and finite(b):
                rec["equal"] = (a == b)
                rec["abs_diff"] = abs(b - a)
                rec["rel_diff"] = abs(b - a) / a if a else None
            else:
                rec["equal"] = in_a and in_b and (not finite(a)) and (not finite(b))
                rec["abs_diff"] = rec["rel_diff"] = None
            pairs[f"{subset}::{cell}"] = rec

    subsets: dict[str, dict] = {}
    for r in pairs.values():
        s = subsets.setdefault(r["subset"], {
            "total": 0, "in_a": 0, "in_b": 0, "both": 0, "equal": 0, "differ": 0,
            "only_a": 0, "only_b": 0, "rel_diffs": []})
        s["total"] += 1
        s["in_a"] += r["in_a"]
        s["in_b"] += r["in_b"]
        if r["in_a"] and r["in_b"]:
            s["both"] += 1
            if r["equal"]:
                s["equal"] += 1
            else:
                s["differ"] += 1
                if r["rel_diff"] is not None:
                    s["rel_diffs"].append(r["rel_diff"])
        elif r["in_a"]:
            s["only_a"] += 1
        else:
            s["only_b"] += 1
    for s in subsets.values():
        rd = s.pop("rel_diffs")
        s["rel_diff_median"] = statistics.median(rd) if rd else None
        s["rel_diff_p90"] = pct(rd, 0.90) if rd else None
        s["rel_diff_max"] = max(rd) if rd else None

    # ===== 시선 1: 로더 시선 — 규칙 5 =================================
    sr_ns: dict = {}
    exec(compile(SPLIT_SRC.read_text(encoding="utf-8"), str(SPLIT_SRC), "exec"), sr_ns)
    sr = sr_ns["split_recorder"]

    splits = {}
    for flag in ("train", "val", "test"):
        raw = list(getattr(sr, f"MIX_large_{flag}_files"))
        splits[flag] = [f for f in raw if f not in MIX_841_EXCLUDED]

    liion = {}
    for flag, files in splits.items():
        rows = []
        for f in files:
            a, a_file, a_key = loader_lookup(f, A)
            b, b_file, b_key = loader_lookup(f, B)
            rows.append({
                "file": f, "a": a, "b": b,
                "a_pass": passes_rule5(a), "b_pass": passes_rule5(b),
                "a_found": a is not None, "b_found": b is not None,
                "label_file": b_file, "lookup_key": b_key,
                "equal": (a == b) if (finite(a) and finite(b)) else (a is None and b is None),
            })
        a_pass = [r for r in rows if r["a_pass"]]
        b_pass = [r for r in rows if r["b_pass"]]
        differ = [r for r in rows if r["a_found"] and r["b_found"] and not r["equal"]]
        by_sub = {}
        for r in differ:
            k = r["label_file"].replace("_labels.json", "")
            by_sub[k] = by_sub.get(k, 0) + 1
        b_missing = {}
        for r in rows:
            if not r["b_found"]:
                k = r["label_file"].replace("_labels.json", "")
                b_missing[k] = b_missing.get(k, 0) + 1
        liion[flag] = {
            "listed": len(files),
            "a_pass": len(a_pass), "b_pass": len(b_pass),
            "a_pass_b_fail": sorted(r["file"] for r in rows if r["a_pass"] and not r["b_pass"]),
            "b_pass_a_fail": sorted(r["file"] for r in rows if r["b_pass"] and not r["a_pass"]),
            "n_label_differs": len(differ),
            "label_differs_by_subset": by_sub,
            "b_not_found_by_subset": b_missing,
            "b_not_found_total": sum(b_missing.values()),
            "rows": rows,
        }

    # ===== ISU_ILCC 히스토그램 · 상위 20 ==============================
    isu = [r["rel_diff"] for r in pairs.values()
           if r["subset"].startswith("ISU") and r["rel_diff"] is not None]
    edges = [0, 1e-12, 0.01, 0.05, 0.10, 0.25, 0.50, 1.0, 2.0, 5.0, float("inf")]
    hist = [{"lo": lo, "hi": hi, "n": sum(1 for v in isu if lo <= v < hi)}
            for lo, hi in zip(edges[:-1], edges[1:])]

    top20 = sorted((r for r in pairs.values() if r["rel_diff"] is not None),
                   key=lambda r: -r["rel_diff"])[:20]

    out = {
        "threshold": EARLY_CYCLE_THRESHOLD,
        "equality_rule": ("라벨은 정수이므로 정확 일치로 판정한다. 허용 오차를 두지 "
                          "않는다 — 부동소수점 연산을 거쳐 저장되는 값이 아니다. "
                          "XJTU 처럼 양쪽 다 NaN 이고 양쪽 다 존재하면 일치로 센다."),
        "views": {
            "loader": "data_loader.py:417-431 의 조회 규칙. 규칙 5 판정의 정본",
            "file": "(서브셋, 셀) 단위 값 비교. Tongji 키는 -# 로 맞춘 뒤",
        },
        "subsets": subsets,
        "liion_mix_large_841": liion,
        "isu_ilcc_hist": hist,
        "isu_ilcc_n": len(isu),
        "top20_rel_diff": top20,
        "pairs": pairs,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True),
                   encoding="utf-8")

    # ===== 콘솔 =======================================================
    print("=== 시선 2: 파일 시선 (값 비교) ===")
    print(f"{'서브셋':<14}{'셀':>5}{'A':>5}{'B':>5}{'일치':>6}{'불일치':>7}"
          f"{'A만':>5}{'B만':>5}{'상대차중앙':>12}{'p90':>9}{'최대':>9}")
    tot = dict.fromkeys(("total", "equal", "differ", "only_a", "only_b"), 0)
    for name in sorted(subsets):
        s = subsets[name]
        for k in tot:
            tot[k] += s[k]
        f = lambda v: f"{v:.4f}" if v is not None else "-"
        print(f"{name:<14}{s['total']:>5}{s['in_a']:>5}{s['in_b']:>5}{s['equal']:>6}"
              f"{s['differ']:>7}{s['only_a']:>5}{s['only_b']:>5}"
              f"{f(s['rel_diff_median']):>12}{f(s['rel_diff_p90']):>9}{f(s['rel_diff_max']):>9}")
    print(f"{'합계':<14}{tot['total']:>5}{'':>5}{'':>5}{tot['equal']:>6}"
          f"{tot['differ']:>7}{tot['only_a']:>5}{tot['only_b']:>5}")

    print("\n=== 시선 1: 로더 시선 — Li-ion MIX_large_841 규칙 5 ===")
    for flag in ("train", "val", "test"):
        v = liion[flag]
        print(f"  {flag:<6} 목록 {v['listed']:>4}  A통과 {v['a_pass']:>4}  B통과 {v['b_pass']:>4}"
              f"  (A통과·B탈락 {len(v['a_pass_b_fail'])} · B통과·A탈락 {len(v['b_pass_a_fail'])})")
        print(f"         라벨값 다름 {v['n_label_differs']:>4}  {v['label_differs_by_subset']}")
        print(f"         B 조회 실패 {v['b_not_found_total']:>4}  {v['b_not_found_by_subset']}")

    print(f"\n기록: {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
