"""
T4 (조건 다양성 분해) 중 프로토콜 부분 + T5 (보고값 대조).

- 프로토콜(aging condition) 수는 upstream/BatteryLife/name2agingConditionID.json 에서 센다.
  (aging_conditions.py 가 생성하는 파일. 셀이름 -> 조건 ID)
- 990 batteries 재계산은 upstream/BatteryLife/dataset_overview_calculation.py 의
  get_agingCondition_battery_num 규칙을 그대로 따른다:
    * Stanford_labels.json 은 건너뛴다
    * life label <= 100 인 셀은 제외한다
    * 그 다음 대상 split 파일 목록과 교집합

사용법:
    .venv-blife/Scripts/python.exe analysis/conditions_and_reported.py
출력:
    analysis/out/conditions_reported.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_PY = os.path.join(ROOT, "upstream", "BatteryLife", "data_provider", "data_split_recorder.py")
COND_JSON = os.path.join(ROOT, "upstream", "BatteryLife", "name2agingConditionID.json")
LABEL_DIR = os.path.join(ROOT, "data", "extracted", "Life labels")
OUT = os.path.join(ROOT, "analysis", "out", "conditions_reported.json")

from domain_discriminability import LI_GROUPS, load_labels, load_splits, lookup  # noqa: E402


def domain_files(splits, domain, seed=2021):
    """도메인별 (train, val, test) 셀 파일명 목록 — split 코드 그대로."""
    if domain == "Li-ion":
        pres = [p for p, _ in LI_GROUPS]
    elif domain == "Zn-ion":
        pres = [{2021: "ZNcoin", 42: "ZN_42", 2024: "ZN_2024"}[seed]]
    elif domain == "CALB":
        pres = [{2021: "CALB", 42: "CALB_42", 2024: "CALB_2024"}[seed]]
    elif domain == "Na-ion":
        pres = [{2021: "NAion_2021", 42: "NAion_42", 2024: "NAion_2024"}[seed]]
    out = {}
    for flag in ("train", "val", "test"):
        out[flag] = [n for p in pres for n in splits[f"{p}_{flag}_files"]]
    return out


def main():
    splits = load_splits()
    labels = load_labels()
    cond = json.load(open(COND_JSON, encoding="utf-8"))
    res = {}

    # ---- T4: 도메인별 고유 프로토콜(aging condition) 수 -------------------
    prot = {}
    for domain in ["Li-ion", "Zn-ion", "Na-ion", "CALB"]:
        df = domain_files(splits, domain)
        allf = df["train"] + df["val"] + df["test"]
        ids, missing = [], 0
        for n in allf:
            if n in cond:
                ids.append(cond[n])
            else:
                missing += 1
        prot[domain] = {
            "n_cells_in_split": len(allf),
            "n_cells_with_condition_id": len(ids),
            "n_cells_missing_condition_id": missing,
            "n_unique_conditions": len(set(ids)),
            "cells_per_condition": (len(ids) / len(set(ids))) if ids else None,
        }
        # test 조건이 train/val 에 있었는지 (seen/unseen)
        tv = {cond[n] for n in df["train"] + df["val"] if n in cond}
        te = {cond[n] for n in df["test"] if n in cond}
        prot[domain]["test_conditions_seen"] = len(te & tv)
        prot[domain]["test_conditions_unseen"] = len(te - tv)
    res["protocols_by_domain"] = prot
    res["n_condition_ids_total_in_json"] = len(set(cond.values()))
    res["n_cells_total_in_json"] = len(cond)

    # ---- T5: 990 batteries 재계산 ---------------------------------------
    # 논문 규칙(dataset_overview_calculation.py): Stanford_labels 제외, life<=100 제외
    kept = set()
    for stem, dd in labels.items():
        if stem == "Stanford":          # Stanford_labels.json 은 코드가 건너뛴다
            continue
        for k, v in dd.items():
            if v <= 100:
                continue
            kept.add(k)

    # 16개 데이터셋(=MIX_all) 전체 split 파일 목록
    mix_all = (splits["MIX_all_train_files"] + splits["MIX_all_val_files"]
               + splits["MIX_all_test_files"])
    mix_all_keyed = [n.replace("--", "-#") if "Tongji" in n else n for n in mix_all]
    res["recount_990"] = {
        "definition": "dataset_overview_calculation.py 규칙: Stanford_labels.json 제외 + life<=100 제외 + MIX_all split 교집합",
        "n_mix_all_split_cells": len(mix_all),
        "n_after_rules": len([n for n in mix_all_keyed if n in kept]),
    }

    # 필터 없이 순수하게 센 값들
    res["raw_counts"] = {
        "n_cells_in_all_label_json": sum(len(v) for v in labels.values()),
        "n_label_json_files": len(labels),
        "cells_per_label_file": {k: len(v) for k, v in sorted(labels.items())},
        "n_cells_in_mix_all_split": len(mix_all),
        "n_cells_life_le_100": sum(1 for v in labels.values() for x in v.values() if x <= 100),
    }

    # split 목록에 있는데 라벨이 없는 셀 / 라벨은 있는데 split 에 없는 셀
    all_label_keys = {k for v in labels.values() for k in v}
    in_split_no_label = [n for n in mix_all_keyed if n not in all_label_keys]
    split_set = set(mix_all_keyed)
    label_no_split = sorted(k for k in all_label_keys if k not in split_set)
    res["coverage"] = {
        "in_split_but_no_label": in_split_no_label,
        "n_in_split_but_no_label": len(in_split_no_label),
        "n_label_but_not_in_split": len(label_no_split),
        "label_but_not_in_split_by_prefix": {},
    }
    byp = {}
    for k in label_no_split:
        p = k.split("_")[0]
        byp[p] = byp.get(p, 0) + 1
    res["coverage"]["label_but_not_in_split_by_prefix"] = dict(sorted(byp.items()))

    # Stanford / Stanford_2 라벨 키 겹침
    s1, s2 = set(labels.get("Stanford", {})), set(labels.get("Stanford_2", {}))
    res["stanford_overlap"] = {"n_Stanford": len(s1), "n_Stanford_2": len(s2),
                               "n_overlap": len(s1 & s2)}

    # ---- 데이터셋별 셀 수 / 소속 도메인 (T2) ------------------------------
    ds_rows = {}
    for domain in ["Li-ion", "Zn-ion", "Na-ion", "CALB"]:
        if domain == "Li-ion":
            pres = [(p, lab) for p, lab in LI_GROUPS]
        elif domain == "Zn-ion":
            pres = [("ZNcoin", "ZN-coin")]
        elif domain == "CALB":
            pres = [("CALB", "CALB")]
        else:
            pres = [("NAion_2021", "NA-ion")]
        for p, lab in pres:
            tr, va, te = (splits[f"{p}_{f}_files"] for f in ("train", "val", "test"))
            withlab = sum(1 for n in tr + va + te if lookup(labels[lab], n) is not None)
            ds_rows[p] = {
                "domain": domain, "label_file": lab,
                "n_split_train": len(tr), "n_split_val": len(va), "n_split_test": len(te),
                "n_split_total": len(tr) + len(va) + len(te),
                "n_with_label": withlab,
            }
    res["datasets"] = ds_rows

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print("written", OUT)


if __name__ == "__main__":
    main()
