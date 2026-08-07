"""라벨 B 생성 — 공개 코드를 **고치지 않고** 돌려 얻는 라벨.

무엇을 묻는 실험인가
--------------------
"누구의 라벨이 옳은가"가 아니라 **"저장소를 clone 한 사람이 실제로 무엇을
얻는가"** 를 묻는다. 그래서 B 는 "잘 만든 라벨"이 아니라 **"공개 코드가
그대로 내놓는 라벨"** 이어야 한다.

그래서 이 스크립트가 하지 않는 일
---------------------------------
* 상위 코드를 고치지 않는다. `upstream/` 은 읽기만 한다
* 생성된 라벨이 이상해 보여도 손대지 않는다 — 이상한 것이 발견이다
* 외부 파일이 없어 못 만드는 서브셋을 우회해서 만들지 않는다.
  **"B 생성 불가"** 로 분류하고 사유를 남긴다
* 오류가 나면 고치지 않는다. 전문을 로그로 남긴다

무엇을 바꾸는가 — 전부 기록한다
-------------------------------
`upstream/BatteryLife/process_scripts/Extract_life_labels.py` 는 **CLI 가
없다.** 실행할 서브셋을 `__main__` 블록의 변수로 적어야 한다 (246행
`dataset_name = ('CALCE')`). 따라서 "인자를 그대로" 줄 방법이 존재하지 않는다.

이 드라이버는 `.build/labels_B/` 에 사본을 두고 **아래 네 줄만** 다시 쓴다.
그 밖의 줄은 바이트 단위로 같은지 매 실행 검사하고, 다르면 멈춘다.

| 행 | 원본 | 바꾸는 이유 |
|---|---|---|
| 246 | `dataset_name = ('CALCE')` | 서브셋 지정 — CLI 가 없어 다른 방법이 없다 |
| 247 | `output_path = './Life_labels'` | 산출물을 `data/labels_B/` 로 |
| 248 | `dataset_root_path = '../datasets/processed/'` | 데이터를 `data/extracted/` 로 |
| 256 | `CALB_summary_file = 'D:/python_project/...xlsx'` | CALB 전용. 그 파일이 없으면 애초에 못 돈다 |

사용
----
    py -3.12 train/build_labels_B.py
    py -3.12 train/build_labels_B.py --only ISU_ILCC
"""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "upstream/BatteryLife/process_scripts"
SRC = SRC_DIR / "Extract_life_labels.py"
WORK = REPO / ".build/labels_B"
OUT = REPO / "data/labels_B"
LOGS = OUT / "_logs"
EXTRACTED = REPO / "data/extracted"

# 바꾸는 줄 (1-기반). 값은 아래 render() 가 채운다.
LINE_DATASET = 246
LINE_OUTPUT = 247
LINE_ROOT = 248
LINE_CALB_XLSX = 256

# 돌려 볼 서브셋: data/extracted 의 디렉터리 이름 그대로 넣는다.
# 스크립트의 출력 파일명 분기(230-241행)를 거치면 배포 라벨과 같은 이름이 나온다:
#   UL_PUR -> UL-PUR_labels.json · ZNcoin -> ZN-coin_labels.json · NAion -> NA-ion_labels.json
#   그 밖 -> {dataset_name}_labels.json
# 우리 배포 트리의 디렉터리는 `ZN-coin` · `NA-ion` 이라 else 분기로도 같은 이름이 나온다.
SUBSETS = [
    "CALCE", "HNEI", "HUST", "ISU_ILCC", "MATR", "MICH", "MICH_EXP",
    "RWTH", "SDU", "SNL", "Stanford", "Stanford_2", "Tongji",
    "total_MICH", "UL_PUR", "XJTU", "ZN-coin", "NA-ion",
    "CALB",   # 외부 Excel 필요 — 못 돌 것으로 보이지만 **그대로 시도해 기록한다**
]


def prepare_work() -> list[str]:
    """`.build/labels_B/` 에 사본을 만든다. 원본 줄을 돌려준다."""
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copy2(SRC, WORK / "Extract_life_labels.py")
    shutil.copytree(SRC_DIR / "Extract_life_labels_tools",
                    WORK / "Extract_life_labels_tools")
    return SRC.read_text(encoding="utf-8").splitlines(keepends=True)


def render(original: list[str], dataset_name: str) -> tuple[str, list[str]]:
    """네 줄만 다시 쓴 본문과, 바꾼 줄의 사람 읽을 기록을 돌려준다."""
    lines = list(original)
    changes = []

    def swap(idx1: int, new: str):
        old = lines[idx1 - 1].rstrip("\n")
        lines[idx1 - 1] = new + "\n"
        changes.append(f"{idx1}: {old.strip()}  ->  {new.strip()}")

    swap(LINE_DATASET, f"    dataset_name = ('{dataset_name}')")
    swap(LINE_OUTPUT, f"    output_path = r'{OUT.as_posix()}'")
    swap(LINE_ROOT, f"    dataset_root_path = r'{EXTRACTED.as_posix()}'")
    if dataset_name == "CALB":
        # 배포되지 않은 파일이다. 경로만 이 기계 기준으로 바꿔 **없다는 것을 확인**한다.
        swap(LINE_CALB_XLSX,
             f"        CALB_summary_file = r'{(EXTRACTED / 'CALB_capacity/汇总表-L148N58-循环.xlsx').as_posix()}'")
    return "".join(lines), changes


def assert_only_expected(original: list[str], rendered: str, dataset_name: str) -> None:
    """바꾼 줄 말고 다른 곳이 달라지면 즉시 멈춘다."""
    allowed = {LINE_DATASET, LINE_OUTPUT, LINE_ROOT}
    if dataset_name == "CALB":
        allowed.add(LINE_CALB_XLSX)
    new = rendered.splitlines(keepends=True)
    if len(new) != len(original):
        raise SystemExit(f"[{dataset_name}] 줄 수가 달라졌습니다 — 멈춥니다.")
    diff = {i + 1 for i, (a, b) in enumerate(zip(original, new)) if a != b}
    if not diff <= allowed:
        raise SystemExit(f"[{dataset_name}] 허용하지 않은 줄이 바뀌었습니다: "
                         f"{sorted(diff - allowed)} — 멈춥니다.")


def run_one(dataset_name: str, original: list[str], python: str) -> dict:
    rendered, changes = render(original, dataset_name)
    assert_only_expected(original, rendered, dataset_name)
    target = WORK / "Extract_life_labels.py"
    target.write_text(rendered, encoding="utf-8")

    before = {p.name: p.stat().st_mtime_ns for p in OUT.glob("*.json")}
    t0 = time.perf_counter()
    proc = subprocess.run([python, "Extract_life_labels.py"], cwd=WORK,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    elapsed = time.perf_counter() - t0

    after = {p.name: p.stat().st_mtime_ns for p in OUT.glob("*.json")}
    produced = sorted(n for n in after if before.get(n) != after[n])

    log = LOGS / f"{dataset_name}.log"
    log.write_text(
        f"# 서브셋: {dataset_name}\n"
        f"# 실행: {python} Extract_life_labels.py   (cwd={WORK})\n"
        f"# 종료 코드: {proc.returncode}   경과 {elapsed:.1f}s\n"
        f"# 바꾼 줄 (그 밖은 상위 원본과 바이트 동일):\n"
        + "".join(f"#   {c}\n" for c in changes)
        + f"# 만들어진 파일: {produced}\n"
        + "\n===== STDOUT =====\n" + proc.stdout
        + "\n===== STDERR =====\n" + proc.stderr,
        encoding="utf-8")

    n_labels = None
    if len(produced) == 1:
        try:
            n_labels = len(json.loads((OUT / produced[0]).read_text(encoding="utf-8")))
        except Exception:
            pass

    return {
        "dataset": dataset_name, "returncode": proc.returncode,
        "elapsed_s": round(elapsed, 1), "produced": produced,
        "n_labels": n_labels, "changed_lines": changes,
        "stderr_tail": proc.stderr.strip().splitlines()[-6:] if proc.stderr.strip() else [],
        "log": str(log.relative_to(REPO)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", help="이 서브셋만")
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    original = prepare_work()

    todo = a.only if a.only else SUBSETS
    results = []
    for name in todo:
        d = EXTRACTED / name
        if not d.is_dir():
            print(f"  [건너뜀] {name} — {d} 가 없습니다")
            results.append({"dataset": name, "returncode": None,
                            "produced": [], "n_labels": None,
                            "note": "데이터 디렉터리 없음"})
            continue
        r = run_one(name, original, a.python)
        results.append(r)
        mark = "OK " if r["returncode"] == 0 and r["produced"] else "실패"
        print(f"  [{mark}] {name:<12} rc={r['returncode']} "
              f"{r['elapsed_s']:>6.1f}s  라벨 {r['n_labels']}  {r['produced']}")
        for line in r["stderr_tail"][-2:]:
            print(f"          {line[:120]}")

    (OUT / "_generation_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = [r for r in results if r.get("produced")]
    print(f"\n생성 성공 {len(ok)} / 시도 {len(results)}")
    print(f"기록: {(OUT / '_generation_summary.json').relative_to(REPO)}")
    print(f"      {LOGS.relative_to(REPO)}/*.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
