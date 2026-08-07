"""
upstream/BatteryLife/README.md 의 벤치마크 표를 파싱해 도메인별
최고 MAPE · 모델 간 간격 · Dummy 보고값을 뽑는다. (T3 판정 근거용)

사용법:
    .venv-blife/Scripts/python.exe analysis/reported_table.py
출력:
    analysis/out/reported_table.json
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "upstream", "BatteryLife", "README.md")
OUT = os.path.join(ROOT, "analysis", "out", "reported_table.json")

DOMAINS = ["Li-ion", "Zn-ion", "Na-ion", "CALB"]


def main():
    rows = {}
    for line in open(README, encoding="utf-8"):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 9:
            continue
        name = cells[0].replace("**", "")
        vals = cells[1:]
        if not re.match(r"^[0-9]", vals[0]):
            continue
        # 열 순서: (MAPE, 15%-Acc) x 4 도메인
        rows[name] = {DOMAINS[i]: {"mape": vals[2 * i], "acc15": vals[2 * i + 1]}
                      for i in range(4)}

    def num(s):
        return float(s.split("±")[0]), float(s.split("±")[1])

    out = {"models": {}, "by_domain": {}}
    for m, d in rows.items():
        out["models"][m] = {k: {"mape": num(v["mape"])[0], "mape_std": num(v["mape"])[1],
                                "acc15": num(v["acc15"])[0]} for k, v in d.items()}

    for dom in DOMAINS:
        vals = {m: v[dom]["mape"] for m, v in out["models"].items()}
        dummy = vals.pop("Dummy")
        ordered = sorted(vals.items(), key=lambda x: x[1])
        best_m, best = ordered[0]
        second_m, second = ordered[1]
        out["by_domain"][dom] = {
            "dummy_reported": dummy,
            "dummy_reported_std": out["models"]["Dummy"][dom]["mape_std"],
            "best_model": best_m, "best_mape": best,
            "best_model_std": out["models"][best_m][dom]["mape_std"],
            "second_model": second_m, "second_mape": second,
            "gap_best_to_second": round(second - best, 4),
            "worst_model": ordered[-1][0], "worst_mape": ordered[-1][1],
            "n_models": len(ordered),
            "model_mape_min_max_spread": round(ordered[-1][1] - best, 4),
            "ranking": ordered,
        }

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print("written", OUT)
    for dom in DOMAINS:
        b = out["by_domain"][dom]
        print(f"{dom:8s} dummy={b['dummy_reported']:.3f}±{b['dummy_reported_std']:.3f} "
              f"best={b['best_mape']:.3f}({b['best_model']})±{b['best_model_std']:.3f} "
              f"2nd={b['second_mape']:.3f} gap12={b['gap_best_to_second']:.3f} "
              f"spread={b['model_mape_min_max_spread']:.3f} n={b['n_models']}")


if __name__ == "__main__":
    main()
