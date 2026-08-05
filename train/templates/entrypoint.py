"""run_main.py 진입점 템플릿. **`train/make_scripts.py` 가 이 파일을 읽어
`@@RUN_MAIN@@` 를 실제 경로로 바꿔 `.build/batterylife/` 에 씁니다.**

여기를 고치고 `python train/make_scripts.py` 를 다시 돌리십시오. 생성물을
직접 고치면 다음 생성 때 지워집니다.

패치는 **둘**입니다.

패치 1 — deepspeed 우회
-----------------------

`upstream/BatteryLife/run_main.py` 를 읽어 두 줄을 바꾸고 exec 합니다.

    - deepspeed_plugin = DeepSpeedPlugin(hf_ds_config=...)
    + deepspeed_plugin = None
    - Accelerator(..., deepspeed_plugin=deepspeed_plugin, ...)
    + Accelerator(..., ...)                      # 인자 삭제

왜 필요한가 — 이 기계에는 deepspeed 를 설치할 수 없습니다. 소스 빌드만
가능한데 CUDA Toolkit(nvcc) 도 MSVC 도 없습니다. accelerate 는 plugin 이
주어지면 deepspeed 가 없을 때 ImportError 로 죽습니다.

**조건 차이** — 원본은 ZeRO stage-2 (ds_config_zero2_baseline.json, bf16
off) 로 돕니다. 이쪽은 accelerate 기본 경로입니다. GPU 가 한 장이라 ZeRO 의
파티셔닝은 어차피 효과가 없지만, **같은 조건이라고 말할 수는 없습니다.**

패치 2 — `MIX_large_841` 분할 추가 (`--dataset MIX_large_841` 일 때만)
----------------------------------------------------------------------

배포 `MIX_large` 843셀 중 아래 6셀은 `Life labels` 에 라벨이 없어 로딩
도중 죽습니다 (TRN-010). 그 6셀을 뺀 841셀 분할을 **새 이름으로 더합니다.**
원본 `MIX_large` 는 건드리지 않습니다 — 그 이름으로 부르면 여전히 843 입니다.

제외는 **`MIX_large_*_files` 층에서** 합니다. `MICH_EXP_*_files` 에서 빼면
`--dataset MICH_EXP` 단독 분기까지 오염됩니다. 그 분기는 18셀 그대로여야
합니다.

`data_loader.py` 의 elif 사슬에는 `MIX_large_841` 가지가 없습니다. 사슬을
고치는 대신 `Dataset_original.__init__` 을 감싸, 데이터셋 객체에만
`dataset='MIX_large'` 로 보이게 합니다. 그때 `split_recorder` 의
`MIX_large_*_files` 는 이미 841 판으로 바뀌어 있습니다. 최상위 `args.dataset`
은 `MIX_large_841` 그대로라 **체크포인트 이름에 841 이 남습니다.**

패치가 하나라도 실패하면 그 자리에서 멈춥니다. 조용히 843 으로 도는 것이
가장 나쁩니다.
"""
import copy
import re
import sys
from pathlib import Path

SOURCE = Path(r"@@RUN_MAIN@@")

# python 은 sys.path[0] 을 **실행한 스크립트의 디렉터리** 로 잡습니다. 그건
# .build/batterylife 라서 utils/ · models/ · data_provider/ 가 안 보입니다.
# run_main.py 가 원래 있던 자리를 앞에 꽂아 줍니다.
sys.path.insert(0, str(SOURCE.parent))

APPLIED = []


def _die(message):
    print("[.build 진입점] 패치 실패 — 멈춥니다.", flush=True)
    print(f"  {message}", flush=True)
    print("  train/templates/entrypoint.py 를 다시 보십시오. 상위가 "
          "바뀌었을 수 있습니다.", flush=True)
    raise SystemExit(2)


# --------------------------------------------------------------------------
# 패치 1 — deepspeed 우회
# --------------------------------------------------------------------------

text = SOURCE.read_text(encoding="utf-8")

patched, n1 = re.subn(
    r"^deepspeed_plugin = DeepSpeedPlugin\(.*\)$",
    "deepspeed_plugin = None  # .build 진입점이 지웠습니다",
    text, count=1, flags=re.M)
patched, n2 = re.subn(r"deepspeed_plugin=deepspeed_plugin,\s*", "", patched, count=1)

if n1 != 1 or n2 != 1:
    _die(f"run_main.py 가 예상과 다릅니다 (plugin={n1}, arg={n2}).")

APPLIED.append("1. deepspeed 우회 — DeepSpeedPlugin 제거, accelerate 기본 경로. "
               "원본은 ZeRO stage-2 입니다 (조건 차이).")


# --------------------------------------------------------------------------
# 패치 2 — MIX_large_841 (요청했을 때만)
# --------------------------------------------------------------------------

MIX_841 = "MIX_large_841"

# 라벨이 배포되지 않은 6셀. 5개가 train, 1개가 test 에 있습니다.
NO_LABEL_CELLS = [
    "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl",   # train
    "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl",   # train
    "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl",   # train
    "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl",   # train
    "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl",   # train
    "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl",   # test
]
# train 510 / val 165 / test 162 = **837** 입니다. 841 이 아닙니다.
#
# 이름은 `MIX_large_841` 그대로 둡니다 — 사람이 정한 이름이고 스크립트 9개와
# 문서가 그 이름을 씁니다. 하지만 **실제 셀 수는 837 입니다.** 배포
# `MIX_large` 가 843 이고 6셀을 빼므로 843-6=837 입니다. 지시서의 "841" 은
# 같은 지시서가 준 분할 수(510/165/162)와도 맞지 않습니다.
# 이름을 바꿀지는 사람이 정합니다 — docs/reports/2026-08-04_unattended.md §8.
EXPECT = {"train": 510, "val": 165, "test": 162}
EXPECT_TOTAL = 837


def _requested_dataset(argv):
    for i, item in enumerate(argv):
        if item == "--dataset" and i + 1 < len(argv):
            return argv[i + 1]
        if item.startswith("--dataset="):
            return item.split("=", 1)[1]
    return None


def _apply_841():
    from data_provider.data_split_recorder import split_recorder
    from data_provider import data_loader as dl

    # (a) MIX_large_*_files 를 841 판으로. **MICH_EXP_*_files 는 그대로 둡니다.**
    excluded = []
    before = {}
    for flag in ("train", "val", "test"):
        name = f"MIX_large_{flag}_files"
        original = list(getattr(split_recorder, name))
        before[flag] = len(original)
        kept = [f for f in original if f not in NO_LABEL_CELLS]
        excluded += [f for f in original if f in NO_LABEL_CELLS]
        setattr(split_recorder, name, kept)
        setattr(split_recorder, f"{MIX_841}_{flag}_files", kept)
        if len(kept) != EXPECT[flag]:
            _die(f"{flag} 이 {len(kept)}셀입니다. {EXPECT[flag]} 이어야 합니다 "
                 f"(원본 {before[flag]}). 상위 분할이 바뀌었습니다.")
    if len(excluded) != len(NO_LABEL_CELLS):
        _die(f"뺀 셀이 {len(excluded)}개입니다. {len(NO_LABEL_CELLS)} 이어야 "
             f"합니다: {sorted(set(NO_LABEL_CELLS) - set(excluded))} 를 "
             "분할에서 못 찾았습니다.")

    # (b) MICH_EXP 단독 분기가 오염되지 않았는지 그 자리에서 확인합니다.
    exp_total = sum(len(getattr(split_recorder, f"MICH_EXP_{f}_files"))
                    for f in ("train", "val", "test"))
    if exp_total != 18:
        _die(f"MICH_EXP 단독 분기가 {exp_total}셀입니다. 18 이어야 합니다.")

    # (c) elif 사슬에 MIX_large_841 가지가 없으므로, 데이터셋 객체에만
    #     dataset='MIX_large' 로 보이게 합니다. 최상위 args 는 그대로입니다.
    original_init = dl.Dataset_original.__init__

    def init_841(self, *a, **kw):
        args = kw["args"] if "args" in kw else (a[0] if a else None)
        use_target = kw.get("use_target_dataset", False)
        field = "target_dataset" if use_target else "dataset"
        if args is not None and getattr(args, field, None) == MIX_841:
            shim = copy.copy(args)
            setattr(shim, field, "MIX_large")
            if "args" in kw:
                kw["args"] = shim
            else:
                a = (shim,) + tuple(a[1:])
        return original_init(self, *a, **kw)

    dl.Dataset_original.__init__ = init_841

    total_before = sum(before.values())
    APPLIED.append(
        f"2. {MIX_841} 분할 추가 — 라벨 미배포 6셀 제외. "
        f"train {before['train']}->{EXPECT['train']} · "
        f"val {before['val']}->{EXPECT['val']} · "
        f"test {before['test']}->{EXPECT['test']}  "
        f"(합계 {total_before} -> {EXPECT_TOTAL}). "
        "MICH_EXP 단독 분기는 18셀 그대로.")
    APPLIED.append(
        f"   주의 — 이름은 {MIX_841} 이지만 **실제 셀 수는 {EXPECT_TOTAL}** "
        f"입니다 ({total_before} - {len(NO_LABEL_CELLS)}). 이름을 바꿀지는 "
        "사람이 정합니다.")


requested = _requested_dataset(sys.argv)
if requested == MIX_841:
    _apply_841()


# --------------------------------------------------------------------------
# 적용된 패치 목록 — 로그 첫머리에 반드시 찍습니다
# --------------------------------------------------------------------------

print("=" * 72, flush=True)
print("[.build 진입점] 원본이 아닙니다. 적용된 패치:", flush=True)
for line in APPLIED:
    print(f"  - {line}", flush=True)
if requested != MIX_841:
    print(f"  (MIX_large_841 패치는 --dataset {MIX_841} 일 때만 켜집니다. "
          f"지금은 --dataset {requested})", flush=True)
print("이 목록을 결과와 함께 남기십시오. 논문과 같은 조건이 아닙니다.", flush=True)
print("=" * 72, flush=True)

sys.argv[0] = str(SOURCE)
exec(compile(patched, str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": str(SOURCE)})
