"""
T4 — 도메인별 조건 다양성 분해 (포맷 / 화학계 / 온도 / 프로토콜).

입력:
    analysis/out/cell_meta.csv          (extract_cell_meta.py 산출: pkl 최상위 메타 + 온도)
    upstream/BatteryLife/name2agingConditionID.json
    upstream/BatteryLife/data_provider/data_split_recorder.py

정의 주의:
- '화학계'는 논문이 정의를 명시하지 않는다. 여기서는 (cathode | anode | electrolyte)
  삼중조합을 고유 화학계로 센다. 다른 정의를 쓰면 값이 달라진다.
- '온도'는 pkl 최상위 필드가 없다. cycle_data 의 temperature_in_C 중앙값을
  정수로 반올림해 고유값을 센다. 논문이 쓴 정의는 확인되지 않았다.

사용법:
    .venv-blife/Scripts/python.exe analysis/diversity_breakdown.py
출력:
    analysis/out/diversity.json
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "analysis", "out", "cell_meta.csv")
COND_JSON = os.path.join(ROOT, "upstream", "BatteryLife", "name2agingConditionID.json")
OUT = os.path.join(ROOT, "analysis", "out", "diversity.json")

from conditions_and_reported import domain_files  # noqa: E402
from domain_discriminability import load_labels, load_splits, lookup  # noqa: E402

DOMAINS = ["Li-ion", "Zn-ion", "Na-ion", "CALB"]


def main():
    meta = {r["file"]: r for r in csv.DictReader(open(META, encoding="utf-8"))}
    cond = json.load(open(COND_JSON, encoding="utf-8"))
    splits, labels = load_splits(), load_labels()

    res = {"note": "화학계=(cathode|anode|electrolyte) 삼중조합, 온도=cycle 온도 중앙값의 반올림 정수",
           "by_domain": {}, "totals": {}}

    all_cells = []
    for domain in DOMAINS:
        df = domain_files(splits, domain)
        cells = df["train"] + df["val"] + df["test"]
        all_cells += [(domain, c) for c in cells]

        fmt, chem, temp, prot = set(), set(), set(), set()
        temp_counts, prot_counts, fmt_counts, chem_counts = {}, {}, {}, {}
        missing_meta = []
        for c in cells:
            m = meta.get(c)
            if m is None:
                missing_meta.append(c)
            else:
                f = m["form_factor"] or "(none)"
                ch = f"{m['cathode_material'] or '(none)'}|{m['anode_material'] or '(none)'}|{m['electrolyte_material'] or '(none)'}"
                fmt.add(f); chem.add(ch)
                fmt_counts[f] = fmt_counts.get(f, 0) + 1
                chem_counts[ch] = chem_counts.get(ch, 0) + 1
                if m["temp_median_C"]:
                    t = int(round(float(m["temp_median_C"])))
                    temp.add(t)
                    temp_counts[t] = temp_counts.get(t, 0) + 1
            if c in cond:
                prot.add(cond[c])
                prot_counts[cond[c]] = prot_counts.get(cond[c], 0) + 1

        n = len(cells)
        res["by_domain"][domain] = {
            "n_cells": n,
            "n_cells_missing_meta": len(missing_meta),
            "cells_missing_meta": missing_meta,
            "n_formats": len(fmt), "formats": sorted(fmt_counts.items(), key=lambda x: -x[1]),
            "n_chemistries": len(chem),
            "chemistries": sorted(chem_counts.items(), key=lambda x: -x[1]),
            "n_temperatures": len(temp),
            "temperatures": sorted(temp_counts.items()),
            "n_protocols": len(prot),
            "cells_per_format": round(n / len(fmt), 2) if fmt else None,
            "cells_per_chemistry": round(n / len(chem), 2) if chem else None,
            "cells_per_temperature": round(n / len(temp), 2) if temp else None,
            "cells_per_protocol": round(n / len(prot), 2) if prot else None,
            "protocol_size_hist": sorted(
                {k: sum(1 for v in prot_counts.values() if v == k)
                 for k in set(prot_counts.values())}.items()),
        }

    # 4개 도메인 합집합 (=논문의 16 데이터셋 벤치마크 모집단)
    fmt, chem, temp, prot = set(), set(), set(), set()
    for _, c in all_cells:
        m = meta.get(c)
        if m:
            fmt.add(m["form_factor"] or "(none)")
            chem.add(f"{m['cathode_material'] or '(none)'}|{m['anode_material'] or '(none)'}|{m['electrolyte_material'] or '(none)'}")
            if m["temp_median_C"]:
                temp.add(int(round(float(m["temp_median_C"]))))
        if c in cond:
            prot.add(cond[c])
    res["totals"] = {"n_cells": len(all_cells), "n_formats": len(fmt),
                     "n_chemistries": len(chem), "n_temperatures": len(temp),
                     "n_protocols": len(prot),
                     "formats": sorted(fmt), "temperatures": sorted(temp)}

    # 논문 필터(life>100, Stanford_labels 제외) 적용 후 프로토콜 수
    keep = set()
    for stem, dd in labels.items():
        if stem == "Stanford":
            continue
        for k, v in dd.items():
            if v > 100:
                keep.add(k)
    filt = set()
    n_filt = 0
    for _, c in all_cells:
        key = c.replace("--", "-#") if "Tongji" in c else c
        if key in keep:
            n_filt += 1
            if c in cond:
                filt.add(cond[c])
    res["totals"]["with_paper_filter"] = {
        "rule": "life>100 & Stanford_labels.json 제외 (dataset_overview_calculation.py)",
        "n_cells": n_filt, "n_protocols": len(filt)}

    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("written", OUT)
    for d in DOMAINS:
        b = res["by_domain"][d]
        print(f"{d:8s} n={b['n_cells']:4d} fmt={b['n_formats']} chem={b['n_chemistries']:2d} "
              f"temp={b['n_temperatures']:2d} prot={b['n_protocols']:3d} "
              f"cells/prot={b['cells_per_protocol']} cells/temp={b['cells_per_temperature']}")
    print("TOTAL", res["totals"])


if __name__ == "__main__":
    main()
