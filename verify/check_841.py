#!/usr/bin/env python3
"""``MIX_large_841`` 분할을 **학습 없이** 검증합니다 (지시 §D-3).

    python -m verify.check_841              전부
    python -m verify.check_841 --structure  로딩 없이 목록 검사만 (수초)

무엇을 보는가
-------------

1. ``MIX_large_841`` 이 train 510 / val 165 / test 162 = **841** 인가
2. 라벨 미배포 6셀이 실제로 빠졌는가
3. ``MIX_large`` 로 부르면 여전히 **843** 인가 (원본 불변)
4. ``MICH_EXP`` 단독 분기가 여전히 **18셀** 인가 (오염 없음)
5. ``Dataset_original`` 이 세 flag 모두 **끝까지 로딩되는가**

3·4 는 **패치를 걸지 않은 별도 프로세스**에서 셉니다. 같은 프로세스에서
재면 패치가 전역을 덮었는지 아닌지 구별이 안 됩니다.

5 는 진짜 pkl 을 읽습니다. 시간이 걸립니다 — ``--structure`` 로 건너뛸 수
있습니다. 학습은 **하지 않습니다.**
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from verify import REPO_ROOT, load_config, use_utf8_stdout

use_utf8_stdout()

BATTERYLIFE = REPO_ROOT / "upstream" / "BatteryLife"
ENTRYPOINT = REPO_ROOT / ".build" / "batterylife" / "run_main_nodeepspeed.py"

# **실제 합계는 837 입니다.** 510+165+162=837 이고 843-6=837 입니다. 이름만
# `MIX_large_841` 입니다 — 사람이 정한 이름이라 바꾸지 않았습니다.
EXPECT_841 = {"train": 510, "val": 165, "test": 162}
EXPECT_841_TOTAL = 837
EXPECT_MIX = {"train": 515, "val": 165, "test": 163}
NO_LABEL_CELLS = [
    "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl",
    "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl",
    "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl",
    "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl",
    "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl",
    "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl",
]

# ``upstream/`` 을 고치지 않으므로, 패치는 진입점 파일의 소스를 읽어
# `exec` 로 걸어 씁니다. 진입점이 마지막에 run_main 을 exec 하는 부분은
# 잘라냅니다 — 여기서는 학습을 돌리지 않습니다.
_CUT = "sys.argv[0] = str(SOURCE)"


def _entrypoint_patch_source() -> str:
    text = ENTRYPOINT.read_text(encoding="utf-8")
    if _CUT not in text:
        raise RuntimeError(f"진입점이 예상과 다릅니다: {ENTRYPOINT}")
    return text.split(_CUT)[0]


# --------------------------------------------------------------------------
# 원본 불변 확인 — 패치 없는 별도 프로세스
# --------------------------------------------------------------------------

_UNPATCHED = r"""
import json, sys
sys.path.insert(0, '.')
from data_provider.data_split_recorder import split_recorder as S
out = {}
for name in ('MIX_large', 'MICH_EXP'):
    out[name] = {f: len(getattr(S, f'{name}_{f}_files')) for f in ('train','val','test')}
out['MIX_large_841_exists'] = hasattr(S, 'MIX_large_841_train_files')
print('@@JSON@@' + json.dumps(out))
"""


def unpatched_counts() -> dict:
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1")
    done = subprocess.run([sys.executable, "-c", _UNPATCHED], cwd=BATTERYLIFE,
                          capture_output=True, text=True, encoding="utf-8", env=env)
    for line in done.stdout.splitlines():
        if line.startswith("@@JSON@@"):
            return json.loads(line[len("@@JSON@@"):])
    raise RuntimeError(f"별도 프로세스가 실패했습니다:\n{done.stdout}\n{done.stderr}")


# --------------------------------------------------------------------------
# 검사 본체 — 여기서는 패치를 겁니다
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="verify/check_841.py")
    parser.add_argument("--structure", action="store_true",
                        help="pkl 로딩을 건너뛰고 목록만 검사")
    parser.add_argument("--budget", type=float, default=600.0,
                        help="로딩 상한(초). 넘기면 중단하고 그때까지를 기록")
    args = parser.parse_args(argv)

    config = load_config()
    root = Path(config.get("EXTRACT_DIR", "./data/extracted"))
    if not root.is_absolute():
        root = REPO_ROOT / root
    root = root.resolve()

    results = []

    def record(name, ok, detail):
        results.append({"name": name, "ok": ok, "detail": detail})
        print(f"[{'  ok  ' if ok else ' FAIL '}] {name}\n           {detail}",
              flush=True)

    # --- 3 · 4. 원본 불변 (패치 없는 프로세스) -----------------------------
    print("\n=== 원본 불변 확인 (패치를 걸지 않은 별도 프로세스) ===")
    plain = unpatched_counts()
    mix = plain["MIX_large"]
    record("MIX_large 는 여전히 843",
           mix == EXPECT_MIX and sum(mix.values()) == 843,
           f"train {mix['train']} / val {mix['val']} / test {mix['test']} "
           f"= {sum(mix.values())}  (기대 843)")
    exp = plain["MICH_EXP"]
    record("MICH_EXP 단독 분기는 여전히 18",
           sum(exp.values()) == 18,
           f"train {exp['train']} / val {exp['val']} / test {exp['test']} "
           f"= {sum(exp.values())}  (기대 18)")
    record("패치 없이는 MIX_large_841 이 존재하지 않음",
           not plain["MIX_large_841_exists"],
           f"hasattr(split_recorder, 'MIX_large_841_train_files') = "
           f"{plain['MIX_large_841_exists']}")

    # --- 진입점 패치를 이 프로세스에 겁니다 -------------------------------
    print("\n=== 진입점 패치 적용 ===")
    os.chdir(BATTERYLIFE)
    sys.path.insert(0, str(BATTERYLIFE))
    namespace = {"__name__": "__patchcheck__", "__file__": str(ENTRYPOINT)}
    saved_argv = sys.argv
    sys.argv = [str(ENTRYPOINT), "--dataset", "MIX_large_841"]
    try:
        exec(compile(_entrypoint_patch_source(), str(ENTRYPOINT), "exec"), namespace)
    finally:
        sys.argv = saved_argv

    from data_provider.data_split_recorder import split_recorder as S

    # --- 1. 841 인가 ------------------------------------------------------
    print("\n=== MIX_large_841 ===")
    counts = {f: len(getattr(S, f"MIX_large_841_{f}_files"))
              for f in ("train", "val", "test")}
    record(f"train 510 / val 165 / test 162 = {EXPECT_841_TOTAL}",
           counts == EXPECT_841 and sum(counts.values()) == EXPECT_841_TOTAL,
           f"train {counts['train']} / val {counts['val']} / test "
           f"{counts['test']} = {sum(counts.values())}   "
           f"(이름은 MIX_large_841 이지만 실제는 {EXPECT_841_TOTAL}셀 "
           f"— 843-6. 지시서의 841 은 지시서가 준 분할 수와도 맞지 않습니다)")

    # --- 2. 6셀이 빠졌는가 ------------------------------------------------
    everything = set()
    for f in ("train", "val", "test"):
        everything |= set(getattr(S, f"MIX_large_841_{f}_files"))
    still = [c for c in NO_LABEL_CELLS if c in everything]
    record("라벨 미배포 6셀이 빠졌는가", not still,
           "6셀 모두 빠졌습니다" if not still else f"남아 있습니다: {still}")

    # --- 5. 실제 로딩 -----------------------------------------------------
    if args.structure:
        print("\n=== 로딩 검사 건너뜀 (--structure) ===")
    else:
        print(f"\n=== 실제 로딩 (상한 {args.budget:.0f}초) ===")
        _load_check(root, args.budget, record)

    failed = [r["name"] for r in results if not r["ok"]]
    print(f"\n통과 {len(results) - len(failed)}/{len(results)}"
          + (f" — 실패: {'; '.join(failed)}" if failed else ""))
    return 0 if not failed else 1


def _load_check(root: Path, budget: float, record) -> None:
    """세 flag 를 실제로 만들어 봅니다. **학습은 하지 않습니다.**"""
    from argparse import Namespace
    from data_provider.data_loader import Dataset_original

    base = Namespace(
        root_path=root.as_posix(),
        seq_len=1,
        charge_discharge_length=300,
        dataset="MIX_large_841",
        target_dataset="None",
        early_cycle_threshold=100,
        weighted_loss=False,
    )

    started = time.time()
    scaler = None
    life_scaler = None
    for flag in ("train", "val", "test"):
        left = budget - (time.time() - started)
        if left <= 0:
            record(f"로딩 {flag}", False,
                   f"상한 {budget:.0f}초를 넘겨 중단했습니다. "
                   f"{flag} 은 시작하지 못했습니다.")
            return
        mark = time.time()
        try:
            dataset = Dataset_original(
                args=base, flag=flag,
                label_scaler=scaler, life_class_scaler=life_scaler,
                use_target_dataset=False)
        except Exception as error:                      # noqa: BLE001
            record(f"로딩 {flag}", False,
                   f"{type(error).__name__}: {error}  "
                   f"({time.time() - mark:.1f}초 만에)")
            return
        if flag == "train":
            scaler = dataset.label_scaler
            life_scaler = dataset.life_class_scaler
        want = EXPECT_841[flag]
        record(f"로딩 {flag}", len(dataset.files) == want,
               f"셀 {len(dataset.files)} (기대 {want}) · 샘플 "
               f"{len(dataset.total_charge_discharge_curves)} · "
               f"{time.time() - mark:.1f}초")
    print(f"  로딩 전체 {time.time() - started:.1f}초")


if __name__ == "__main__":
    raise SystemExit(main())
