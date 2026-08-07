"""Zn-ion 9회의 묶음 표시를 맞바꿉니다 (1회성 정정).

경위 — 문서 지정 학습률(CPMLP 5e-4 · CPTransformer 1e-3)로는 Zn-ion 이
학습되지 않아(훈련 손실 1.00 고정) 다른 세 도메인과 같은 5e-5 로 낮춰
9회를 다시 돌렸고, 그 결과가 Table 3 대조표(부록 B)에 들어갔습니다.
따라서 **5e-5 판이 정본(main)** 이고 문서값 판은 진단 자료입니다.

    main       : zn_lr9.log 의 9회            (기존 tag=lr5e-05)
    diagnostic : 20260804-154322_* 의 9회     (기존 tag=None)

재학습·재파싱하지 않습니다. `group` · `tag` 필드만 바꾸고 숫자는 한 개도
건드리지 않습니다 (실행 후 값 해시로 대조합니다).

    .venv-blife/Scripts/python.exe -m train.regroup_znion
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CURVES = ROOT / "experiments" / "results" / "curves"

MODELS = ("MLP", "CPMLP", "CPTransformer")
SEEDS = (2021, 42, 2024)


def main() -> None:
    changed = []
    for model in MODELS:
        for seed in SEEDS:
            doc = CURVES / f"{model}_Zn-ion_s{seed}.json"          # 문서 지정 학습률
            low = CURVES / f"{model}_Zn-ion_s{seed}__lr5e-05.json"  # 낮춘 학습률
            if not low.exists():
                print(f"  건너뜀 — 5e-5 판이 없습니다: {low.name}")
                continue

            a = json.loads(doc.read_text(encoding="utf-8"))
            b = json.loads(low.read_text(encoding="utf-8"))

            # 파일명은 바꾸지 않습니다. `tag` 는 파일명 접미사와 같아야 하므로
            # 그대로 두고 `group` 만 맞바꿉니다 — 정본 판단의 근거는 `group` 입니다.
            a["group"] = "diagnostic"
            b["group"] = "main"

            doc.write_text(json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")
            low.write_text(json.dumps(b, indent=2, ensure_ascii=False), encoding="utf-8")
            changed.append((f"{model}_Zn-ion_s{seed}",
                            a["conditions"]["learning_rate"], b["conditions"]["learning_rate"]))

    print(f"묶음을 맞바꾼 실행 {len(changed)}건")
    for name, lr_doc, lr_low in changed:
        print(f"  {name:<28} main: lr{lr_low:g} (zn_lr9.log)   "
              f"diagnostic: lr{lr_doc:g} (20260804-154322_*)")

    main_runs = [json.loads(p.read_text(encoding="utf-8")) for p in CURVES.glob("*.json")]
    n_main = sum(1 for r in main_runs if r["group"] == "main")
    lrs = sorted({r["conditions"]["learning_rate"] for r in main_runs
                  if r["group"] == "main" and r["domain"] == "Zn-ion"})
    print(f"\nmain 실행 수 {n_main} · main Zn-ion 학습률 {[f'{x:g}' for x in lrs]}")


if __name__ == "__main__":
    main()
