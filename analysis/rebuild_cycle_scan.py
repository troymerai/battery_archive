"""
li_ion_cycle_scan.csv 의 **부분 재구성**. 2026-08-07 에 역산해 새로 쓴 것입니다.

원래 스캔을 만든 스크립트는 저장소에 저장되지 않았습니다(2026-08-06 조사의
일회성 코드). 이 파일은 산출물 CSV 를 역산해 다시 만든 것이고 **원본과 완전히
같지 않습니다.**

재현 상태 (표본 26셀 · 14,899행 기준, docs/reports/2026-08-07_repo_cleanup.md §11):

    8개 열 완전 재현    cycle_number n_points dis_ah_max chg_ah_max
                        v_min v_max i_min i_max
    3개 열 미확정       dis_points dis_duration v_end_dis
    전열 일치 행        90.3%

미확정 3열은 **방전 구간을 어떻게 고르는가** 에 달려 있고, 그 규칙이 어디에도
적혀 있지 않습니다. 여기서는 `I<0` 의 최장 연속 구간을 씁니다 — 가장 잘 맞는
가설이지만(90.3%) 원본 규칙이라는 증거는 없습니다. `I<-0.01` 은 81.2% 입니다.

**중요 — 이 3열은 파생 요약에 쓰이지 않습니다.**
`li_ion_label_vs_soh.csv` 와 `li_ion_temporary_crossing.csv` 의 값은 전부
SOH 에서 나오고, SOH 는 `dis_ah_max` 에서 나옵니다. `dis_ah_max` 는 완전히
재현됩니다. 따라서 원시 스캔은 **캐시**이고, 잃어도 파생 요약은 pkl 에서 다시
계산할 수 있습니다.

사용법:
    .venv-blife/Scripts/python.exe analysis/rebuild_cycle_scan.py [--limit N]
출력:
    analysis/out/li_ion_cycle_scan_rebuilt.csv   (원본을 덮어쓰지 않습니다)

주의: 행 순서가 원본과 다릅니다. 원본의 셀 순서는 알파벳도, glob 도,
data_split_recorder 의 분할 순서도 아니며 무엇인지 밝히지 못했습니다.
"""
import argparse
import csv
import glob
import os
import pickle

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "analysis", "li_ion_cell_meta.csv")
OUT = os.path.join(ROOT, "analysis", "out", "li_ion_cycle_scan_rebuilt.csv")

FIELDS = ["subset", "file", "cycle_number", "n_points", "dis_ah_max", "chg_ah_max",
          "dis_points", "dis_duration", "v_end_dis", "v_min", "v_max", "i_min", "i_max"]

# 열마다 반올림 자릿수가 다릅니다. 원본 CSV 에서 역산한 값입니다.
ROUND = {"dis_ah_max": 6, "chg_ah_max": 6, "dis_duration": 4,
         "v_end_dis": 5, "v_min": 5, "v_max": 5, "i_min": 5, "i_max": 5}


def discharge_index(current):
    """방전 구간의 인덱스. **원본 규칙이 아니라 최적 가설입니다.**

    Li-ion 884셀은 disc_sign 이 전부 -1 이므로(li_ion_cell_meta.csv) 방전은
    음전류입니다. 음전류가 여러 토막으로 끊길 때 어느 토막을 쓰는지가
    원본에 안 적혀 있어, 최장 연속 토막을 씁니다.
    """
    idx = np.flatnonzero(current < 0)
    if idx.size == 0:
        return idx
    segments = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return max(segments, key=len)


def scan_cell(path):
    cycles = pickle.load(open(path, "rb")).get("cycle_data") or []
    rows = []
    for cycle in cycles:
        v = np.asarray(cycle["voltage_in_V"], float)
        i = np.asarray(cycle["current_in_A"], float)
        t = np.asarray(cycle["time_in_s"], float)
        qd = np.asarray(cycle["discharge_capacity_in_Ah"], float)
        qc = np.asarray(cycle["charge_capacity_in_Ah"], float)
        idx = discharge_index(i)
        rows.append({
            "cycle_number": cycle.get("cycle_number"),
            "n_points": len(v),
            "dis_ah_max": float(qd.max()) if qd.size else None,
            "chg_ah_max": float(qc.max()) if qc.size else None,
            "dis_points": int(len(idx)),
            "dis_duration": float(t[idx].max() - t[idx].min()) if len(idx) else None,
            "v_end_dis": float(v[idx[-1]]) if len(idx) else None,
            "v_min": float(v.min()) if v.size else None,
            "v_max": float(v.max()) if v.size else None,
            "i_min": float(i.min()) if i.size else None,
            "i_max": float(i.max()) if i.size else None,
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="앞에서 N셀만 (훑어보기용)")
    args = parser.parse_args()

    with open(META, encoding="utf-8", newline="") as fh:
        cells = [(r["subset"], r["file"]) for r in csv.DictReader(fh)]
    if args.limit:
        cells = cells[:args.limit]

    paths = {os.path.basename(p): p for p in glob.glob(os.path.join(ROOT, "data", "extracted", "*", "*.pkl"))}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    missing = 0
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for n, (subset, name) in enumerate(cells):
            if name not in paths:          # 데이터 미배포 셀은 사유 없이 건너뛰지 않습니다
                missing += 1
                print(f"  pkl 없음: {name}", flush=True)
                continue
            for row in scan_cell(paths[name]):
                row["subset"], row["file"] = subset, name
                for key, digits in ROUND.items():
                    if row[key] is not None:
                        row[key] = round(row[key], digits)
                writer.writerow(row)
            if n % 50 == 0:
                print(n, len(cells), flush=True)
    print(f"done {OUT}  (pkl 없음 {missing}셀)")


if __name__ == "__main__":
    main()
