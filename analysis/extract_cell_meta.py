"""
전 셀(1,440 pkl)의 메타데이터를 뽑아 CSV 로 저장한다. (T4 조건 다양성용)

포맷/화학계/온도/프로토콜은 라벨 json 에 없고 pkl 최상위 필드와 cycle_data 에만 있다.
온도는 top-level 필드가 없어 cycle_data[*]['temperature_in_C'] 의 중앙값을 쓴다.

사용법:
    .venv-blife/Scripts/python.exe analysis/extract_cell_meta.py
출력:
    analysis/out/cell_meta.csv
"""
import csv
import glob
import os
import pickle
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis", "out", "cell_meta.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

FIELDS = [
    "subset", "file", "cell_id", "form_factor", "anode_material", "cathode_material",
    "electrolyte_material", "nominal_capacity_in_Ah", "depth_of_charge",
    "depth_of_discharge", "soc_lo", "soc_hi", "min_voltage_limit_in_V",
    "max_voltage_limit_in_V", "charge_rate_C", "discharge_rate_C",
    "charge_protocol_n", "discharge_protocol_n", "n_cycles",
    "temp_median_C", "temp_p05_C", "temp_p95_C", "error",
]


def prot_rate(p):
    if not isinstance(p, list) or not p:
        return None, 0
    r = p[0].get("rate_in_C") if isinstance(p[0], dict) else None
    return r, len(p)


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "extracted", "*", "*.pkl")))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for i, path in enumerate(files):
            row = {k: "" for k in FIELDS}
            row["subset"] = os.path.basename(os.path.dirname(path))
            row["file"] = os.path.basename(path)
            try:
                with open(path, "rb") as f:
                    d = pickle.load(f)
                row["cell_id"] = d.get("cell_id")
                for k in ("form_factor", "anode_material", "cathode_material",
                          "electrolyte_material", "nominal_capacity_in_Ah",
                          "depth_of_charge", "depth_of_discharge",
                          "min_voltage_limit_in_V", "max_voltage_limit_in_V"):
                    row[k] = d.get(k)
                soc = d.get("SOC_interval") or [None, None]
                row["soc_lo"], row["soc_hi"] = soc[0], soc[1]
                row["charge_rate_C"], row["charge_protocol_n"] = prot_rate(d.get("charge_protocol"))
                row["discharge_rate_C"], row["discharge_protocol_n"] = prot_rate(d.get("discharge_protocol"))
                cyc = d.get("cycle_data") or []
                row["n_cycles"] = len(cyc)
                temps = []
                for c in cyc:
                    t = c.get("temperature_in_C") if isinstance(c, dict) else None
                    if t is None:
                        continue
                    a = np.asarray(t, dtype=float)
                    a = a[np.isfinite(a)]
                    if a.size:
                        temps.append(float(np.median(a)))
                if temps:
                    ta = np.asarray(temps)
                    row["temp_median_C"] = float(np.median(ta))
                    row["temp_p05_C"] = float(np.percentile(ta, 5))
                    row["temp_p95_C"] = float(np.percentile(ta, 95))
            except Exception as e:  # 손상/포맷 상이 셀은 사유를 남긴다
                row["error"] = f"{type(e).__name__}: {e}"[:200]
            w.writerow(row)
            if i % 100 == 0:
                print(i, len(files), flush=True)
    print("done", OUT)


if __name__ == "__main__":
    main()
