"""
T6 — 0.825 폐기 임계 · 중도절단 · 라벨 단조성 위반을 v11 데이터에서 다시 센다.

규칙은 upstream/BatteryLife/process_scripts/Extract_life_labels.py:110-155 그대로:

    nominal_capacity = 1.85                      if file.startswith('RWTH')
                     = 3.2                       if file.startswith('SNL_18650_NCA_25C_20-80')
                     = data['nominal_capacity_in_Ah']  otherwise
    SOC_interval     = SOC_interval[1] - SOC_interval[0]   (0 이면 1)
    soh(cycle)       = max(cycle['discharge_capacity_in_Ah']) / nominal_capacity / SOC_interval

    last_cycle_soh >= 0.825       -> 폐기 (라벨 JSON 에 키가 생기지 않음)
    0.8 < last_cycle_soh < 0.825  -> 외삽 (마지막 20사이클 선형회귀)
    last_cycle_soh <= 0.8         -> 첫 교차

CALB 는 상위 코드가 이 경로를 타지 않고 외부 파일에서 라벨을 읽는다. 그래도
soh 는 같은 식으로 계산해 분포만 기록한다.

단조성 위반: soh 수열에서 soh[i] > soh[i-1] + 1e-9 인 지점 수와 최대 상승폭.

사용법:
    .venv-blife/Scripts/python.exe analysis/recount_label_filters.py
출력:
    analysis/out/label_filter_recount.csv
"""
import csv
import glob
import json
import os
import pickle

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL_DIR = os.path.join(ROOT, "data", "extracted", "Life labels")
OUT = os.path.join(ROOT, "analysis", "out", "label_filter_recount.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

FIELDS = ["subset", "file", "nominal_capacity", "soc_interval", "n_cycles",
          "last_cycle_soh", "branch", "has_deployed_label", "deployed_label",
          "n_monotonicity_violations", "max_soh_rise", "first_soh", "min_soh", "error"]


def load_label_keys():
    keys = {}
    for fn in os.listdir(LABEL_DIR):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(LABEL_DIR, fn), encoding="utf-8") as f:
            for k, v in json.load(f).items():
                keys[k] = v
    return keys


def main():
    labels = load_label_keys()
    files = sorted(glob.glob(os.path.join(ROOT, "data", "extracted", "*", "*.pkl")))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for i, path in enumerate(files):
            fn = os.path.basename(path)
            row = {k: "" for k in FIELDS}
            row["subset"] = os.path.basename(os.path.dirname(path))
            row["file"] = fn
            # 배포 라벨 키는 Tongji 만 '--' -> '-#'
            key = fn.replace("--", "-#") if "Tongji" in fn else fn
            row["has_deployed_label"] = int(key in labels)
            row["deployed_label"] = labels.get(key, "")
            try:
                with open(path, "rb") as f:
                    d = pickle.load(f)
                cyc = d["cycle_data"]
                if fn.startswith("RWTH"):
                    nom = 1.85
                elif fn.startswith("SNL_18650_NCA_25C_20-80"):
                    nom = 3.2
                else:
                    nom = d["nominal_capacity_in_Ah"]
                si = d["SOC_interval"]
                si = si[1] - si[0]
                if si == 0:
                    si = 1
                row["nominal_capacity"], row["soc_interval"] = nom, si
                row["n_cycles"] = len(cyc)

                sohs = np.array([max(c["discharge_capacity_in_Ah"]) for c in cyc],
                                dtype=float) / nom / si
                last = float(sohs[-1])
                row["last_cycle_soh"] = last
                row["first_soh"] = float(sohs[0])
                row["min_soh"] = float(sohs.min())
                row["branch"] = ("폐기" if last >= 0.825
                                 else "외삽" if last > 0.8 else "첫교차")
                dif = np.diff(sohs)
                row["n_monotonicity_violations"] = int((dif > 1e-9).sum())
                row["max_soh_rise"] = float(dif.max()) if dif.size else 0.0
            except Exception as e:
                row["error"] = f"{type(e).__name__}: {e}"[:200]
            w.writerow(row)
            if i % 100 == 0:
                print(i, len(files), flush=True)
    print("done", OUT)


if __name__ == "__main__":
    main()
