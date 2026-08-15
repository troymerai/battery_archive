"""
`Stanford` 와 `Stanford_2` 에 **파일명이 같은 38셀** 이 정말 같은 셀인지 본다.

왜 필요한가
-----------
`total_MICH/` 는 집합 비교로 파생임을 확인하고 전수 대상에서 뺐는데, 이 38셀은
파일명만 보고 양쪽에 그대로 두었습니다. 같은 종류의 판단을 두 번 다르게 한
상태라 총계 1,382 안에 38셀이 중복일 수 있습니다.

방법 (2026-08-13 지시 §2-1 순서)
--------------------------------
1. 원시 바이트 sha256 비교
2. 바이트가 다르면 내용 비교 — 사이클 수, 사양 필드, 첫·끝 SOH
3. 어느 축에서 갈리는지 기록

한 쌍씩 열고 닫습니다. 두 파일을 동시에 올리므로 최대 상주량은 그 쌍의 합입니다.

사용법:
    .venv-blife/Scripts/python.exe analysis/stanford_overlap_check.py
출력:
    analysis/out/stanford_overlap.csv
"""
import csv
import hashlib
import os
import pickle
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "data", "extracted", "Stanford")
B = os.path.join(ROOT, "data", "extracted", "Stanford_2")
OUT = os.path.join(ROOT, "analysis", "out", "stanford_overlap.csv")

SPEC = ("form_factor", "anode_material", "cathode_material", "electrolyte_material",
        "nominal_capacity_in_Ah", "depth_of_charge", "depth_of_discharge",
        "max_voltage_limit_in_V", "min_voltage_limit_in_V", "already_spent_cycles")

FIELDS = ["file", "size_a", "size_b", "sha_a", "sha_b", "bytes_equal",
          "n_cycles_a", "n_cycles_b", "cycle_max_a", "cycle_max_b",
          "spec_equal", "spec_diff", "qd_first_a", "qd_first_b",
          "qd_last_a", "qd_last_b", "verdict", "error"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def summarize(path):
    """pkl 하나에서 비교에 쓸 스칼라만 뽑는다. 배열은 밖으로 내보내지 않는다."""
    with open(path, "rb") as fh:
        d = pickle.load(fh)
    cyc = d.get("cycle_data") or []
    spec = {k: d.get(k) for k in SPEC}
    nums = [c.get("cycle_number") for c in cyc if isinstance(c, dict)]
    nums = [int(n) for n in nums if n is not None]

    def qmax(c):
        a = np.asarray(c.get("discharge_capacity_in_Ah"), dtype=float)
        a = a[np.isfinite(a)]
        return float(a.max()) if a.size else None

    out = {
        "n": len(cyc),
        "cycle_max": max(nums) if nums else None,
        "spec": spec,
        "qd_first": qmax(cyc[0]) if cyc else None,
        "qd_last": qmax(cyc[-1]) if cyc else None,
    }
    del cyc, d
    return out


def main():
    shared = sorted(set(os.listdir(A)) & set(os.listdir(B)))
    print(f"[overlap] 동명 파일 {len(shared)}쌍", file=sys.stderr, flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    n_same = n_diff = n_err = 0
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for i, fn in enumerate(shared):
            row = {k: "" for k in FIELDS}
            row["file"] = fn
            pa, pb = os.path.join(A, fn), os.path.join(B, fn)
            try:
                row["size_a"], row["size_b"] = os.path.getsize(pa), os.path.getsize(pb)
                ha, hb = sha(pa), sha(pb)
                row["sha_a"], row["sha_b"] = ha[:16], hb[:16]
                row["bytes_equal"] = int(ha == hb)
                if ha == hb:
                    row["verdict"] = "동일(바이트)"
                    n_same += 1
                else:
                    sa, sb = summarize(pa), summarize(pb)
                    row["n_cycles_a"], row["n_cycles_b"] = sa["n"], sb["n"]
                    row["cycle_max_a"], row["cycle_max_b"] = sa["cycle_max"], sb["cycle_max"]
                    diff = [k for k in SPEC if sa["spec"][k] != sb["spec"][k]]
                    row["spec_equal"] = int(not diff)
                    row["spec_diff"] = "|".join(diff)
                    row["qd_first_a"], row["qd_first_b"] = sa["qd_first"], sb["qd_first"]
                    row["qd_last_a"], row["qd_last_b"] = sa["qd_last"], sb["qd_last"]
                    axes = []
                    if sa["n"] != sb["n"]:
                        axes.append("사이클수")
                    if diff:
                        axes.append("사양")
                    if sa["qd_first"] != sb["qd_first"] or sa["qd_last"] != sb["qd_last"]:
                        axes.append("용량")
                    row["verdict"] = "상이:" + ("+".join(axes) if axes else "바이트만")
                    n_diff += 1
            except Exception as e:
                row["error"] = f"{type(e).__name__}: {e}"[:300]
                row["verdict"] = "읽기실패"
                n_err += 1
            w.writerow(row)
            fh.flush()
            print(f"  {i + 1}/{len(shared)} {fn} -> {row['verdict']}", file=sys.stderr, flush=True)

    print(f"[overlap] 동일 {n_same} · 상이 {n_diff} · 실패 {n_err} / {len(shared)}쌍",
          file=sys.stderr)
    print(f"[overlap] {OUT}", file=sys.stderr)
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
