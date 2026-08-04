#!/usr/bin/env python3
"""학습 스크립트 8종(+스모크 1종)을 ``.build/batterylife/`` 에 만듭니다.

    python train/make_scripts.py            생성 + 검증표 출력
    python train/make_scripts.py --check    이미 만든 것만 검증

왜 8개인가
----------

원본은 ``MLP.sh`` 가 MIX_large, ``CPMLP.sh`` 가 CALB 를 씁니다. 서로 다른
데이터를 쓰므로 **CyclePatch 효과 비교가 성립하지 않습니다.** 데이터셋을
맞춘 두 벌(CALB / MIX_large)을 만듭니다.

``Transformer.sh`` 는 상위에 **없습니다.** ``models/Transformer.py`` 는
있으므로 ``CPTransformer.sh`` 의 하이퍼파라미터를 그대로 쓰고 모델 이름만
바꿉니다. 이것은 임의 선택이며 논문 조건이 아닙니다 — RUN.md 에 적혀
있습니다.

**dataset · model 이름 · epochs · master_port 말고는 원본 값을 그대로
둡니다.** 학습률·층수·d_model 은 모델마다 따로 튜닝된 값입니다.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from train import paths as paths_mod
from verify import REPO_ROOT, load_config, read_text, use_utf8_stdout, write_text

use_utf8_stdout()

OUT_DIR = REPO_ROOT / ".build" / "batterylife"
SCRIPTS = "BatteryLife/train_eval_scripts"

# (모델, 원본 스크립트, 기본 포트).  Transformer 는 원본이 없어 CPTransformer
# 를 빌립니다. 포트는 동시에 돌릴 때 겹치지 않도록 다르게 줍니다.
MODELS = [
    ("MLP",           f"{SCRIPTS}/MLP.sh",           25193),
    ("CPMLP",         f"{SCRIPTS}/CPMLP.sh",         20435),
    ("Transformer",   f"{SCRIPTS}/CPTransformer.sh", 25217),
    ("CPTransformer", f"{SCRIPTS}/CPTransformer.sh", 25216),
]
DATASETS = ["CALB", "MIX_large"]
PORT_OFFSET = {"CALB": 0, "MIX_large": 100}


# --------------------------------------------------------------------------
# DeepSpeed 우회 (§6 에서 실측으로 드러난 것)
# --------------------------------------------------------------------------
#
# run_main.py:136-137 이 DeepSpeedPlugin 을 **무조건** 만들어 Accelerator 에
# 넘깁니다. accelerate 0.29.3 은 plugin 이 있으면 deepspeed 가 없을 때
# ImportError 로 죽습니다 (accelerator.py:294-296). 조건 분기가 없습니다.
#
# 이 기계에는 deepspeed 를 넣을 수 없습니다. 소스 빌드만 가능한데
# CUDA Toolkit(nvcc) 도 MSVC 도 없습니다. 실제 확인:
#
#   pip install deepspeed                     -> torch 없이 pre-compile 불가
#   pip install --no-build-isolation deepspeed -> MissingCUDAException:
#                                                 CUDA_HOME does not exist
#
# 그래서 **upstream 을 고치지 않고** 아래 진입점을 .build/ 에 만듭니다.
# 원본 소스를 읽어 딱 두 줄을 바꾸고 exec 합니다. cwd 는 그대로
# upstream/BatteryLife 이므로 상대경로(data_provider/life_classes.json 등)는
# 전부 그대로 동작합니다.
#
# **이것은 학습 조건의 변경입니다.** 원본은 ZeRO stage-2 로 돕니다.
# 이쪽은 accelerate 기본 경로(단일 GPU · fp32 · Adam)로 돕니다.
# RUN.md 의 조건 차이표에 적혀 있습니다. 지우지 마십시오.
_ENTRYPOINT = '''\
"""DeepSpeed 없이 run_main.py 를 돌리는 진입점. **생성물입니다.**

upstream/BatteryLife/run_main.py 를 읽어 아래 두 줄만 바꾸고 exec 합니다.
upstream 파일은 건드리지 않습니다.

    - deepspeed_plugin = DeepSpeedPlugin(hf_ds_config=...)
    + deepspeed_plugin = None
    - Accelerator(..., deepspeed_plugin=deepspeed_plugin, ...)
    + Accelerator(..., ...)                      # deepspeed_plugin 인자 삭제

왜 필요한가 — 이 기계에는 deepspeed 를 설치할 수 없습니다. 소스 빌드만
가능한데 CUDA Toolkit(nvcc) 도 MSVC 도 없습니다. accelerate 는 plugin 이
주어지면 deepspeed 가 없을 때 ImportError 로 죽습니다.

**조건 차이** — 원본은 ZeRO stage-2 (ds_config_zero2_baseline.json,
bf16 off) 로 돕니다. 이쪽은 accelerate 기본 경로입니다. GPU 가 한 장이라
ZeRO 의 파티셔닝은 어차피 효과가 없지만, **같은 조건이라고 말할 수는
없습니다.** 논문 수치와 비교할 때 이 항목을 반드시 함께 적으십시오.
"""
import re
import sys
from pathlib import Path

SOURCE = Path(r"{source}")

# python 은 sys.path[0] 을 **실행한 스크립트의 디렉터리** 로 잡습니다. 그건
# .build/batterylife 라서 utils/ · models/ · data_provider/ 가 안 보입니다.
# run_main.py 가 원래 있던 자리를 앞에 꽂아 줍니다.
sys.path.insert(0, str(SOURCE.parent))

text = SOURCE.read_text(encoding="utf-8")

patched, n1 = re.subn(
    r"^deepspeed_plugin = DeepSpeedPlugin\\(.*\\)$",
    "deepspeed_plugin = None  # .build 진입점이 지웠습니다",
    text, count=1, flags=re.M)
patched, n2 = re.subn(r"deepspeed_plugin=deepspeed_plugin,\\s*", "", patched, count=1)

if n1 != 1 or n2 != 1:
    sys.exit(
        f"run_main.py 가 예상과 다릅니다 (plugin={{n1}}, arg={{n2}}). "
        "상위가 바뀌었습니다. train/make_scripts.py 를 다시 보십시오."
    )

print("[.build 진입점] deepspeed 를 우회했습니다. "
      "원본은 ZeRO stage-2 로 돕니다 — 조건이 다릅니다.", flush=True)

sys.argv[0] = str(SOURCE)
exec(compile(patched, str(SOURCE), "exec"), {{"__name__": "__main__", "__file__": str(SOURCE)}})
'''


def write_entrypoint() -> Path:
    source = (REPO_ROOT / "upstream" / "BatteryLife" / "run_main.py").resolve()
    path = OUT_DIR / "run_main_nodeepspeed.py"
    write_text(path, _ENTRYPOINT.format(source=source))
    return path


def _note(model: str, source: str, dataset: str) -> str:
    borrowed = "CPTransformer" in source and model == "Transformer"
    parts = [f"dataset={dataset} 로 통일 (§4-2)"]
    if borrowed:
        parts.append("원본 Transformer.sh 가 없어 CPTransformer.sh 의 "
                     "하이퍼파라미터를 그대로 씁니다")
    return " / ".join(parts)


def _use_entrypoint(path: Path, entrypoint: Path) -> None:
    """스크립트의 ``run_main.py`` 호출을 .build 진입점으로 바꿉니다."""
    text = read_text(path)
    text = text.replace(" run_main.py ", f' "{entrypoint.as_posix()}" ')
    write_text(path, text)


def generate(config: dict | None = None) -> list:
    config = config if config is not None else load_config()
    entrypoint = write_entrypoint()
    made = []
    for dataset in DATASETS:
        for model, source, port in MODELS:
            name = f"{model}_{dataset}.sh"
            result = paths_mod.build_variant(
                source, OUT_DIR / name,
                dataset=dataset, model=model,
                port=str(port + PORT_OFFSET[dataset]),
                note=_note(model, source, dataset), config=config,
            )
            _use_entrypoint(result["path"], entrypoint)
            result["name"] = name
            made.append(result)

    # 스모크 사본. 정식 8개는 원본 epochs(100) 를 유지합니다.
    smoke = paths_mod.build_variant(
        f"{SCRIPTS}/CPMLP.sh", OUT_DIR / "_smoke_CPMLP_CALB.sh",
        dataset="CALB", model="CPMLP", epochs="1", port="20999",
        note="스모크 전용 — train_epochs=1. 정식 파일은 100 입니다.",
        config=config,
    )
    _use_entrypoint(smoke["path"], entrypoint)
    smoke["name"] = "_smoke_CPMLP_CALB.sh"
    made.append(smoke)

    # 소요 시간 측정용 사본. 로딩 시간과 에폭 시간을 **분리해서** 재려는
    # 것이므로 3 에폭이면 충분합니다. 결과를 얻으려는 것이 아닙니다.
    # 정식 8개는 100 에폭 그대로입니다.
    #
    # MIX_large 와 ZN-coin 둘 다 만듭니다. MIX_large 는 라벨 6개가 없어
    # 로딩 도중 죽습니다 (TRN-010) — 그 사실 자체를 재현하려고 남겨 둡니다.
    # 실제 에폭 시간은 ZN-coin(100셀, 도는 도메인 중 가장 큼)에서 잽니다.
    offset = {"MIX_large": 300, "ZN-coin": 400}
    for timing_dataset in ("MIX_large", "ZN-coin"):
        for model, source, port in MODELS:
            if model not in ("CPMLP", "CPTransformer"):
                continue
            name = f"_timing_{model}_{timing_dataset}.sh"
            timing = paths_mod.build_variant(
                source, OUT_DIR / name,
                dataset=timing_dataset, model=model, epochs="3",
                port=str(port + offset[timing_dataset]),
                note="측정 전용 — train_epochs=3. 지표로 쓰지 마십시오.",
                config=config,
            )
            _use_entrypoint(timing["path"], entrypoint)
            timing["name"] = name
            made.append(timing)

    return made


# --------------------------------------------------------------------------
# 검증 (§4-4)
# --------------------------------------------------------------------------

_CHECKS = ("checkpoints", "root_path", "CUDA_VISIBLE_DEVICES", "multi_gpu",
           "num_workers", "dataset", "name_agree")


def verify_one(path: Path, expect_dataset: str, expect_model: str,
               config: dict) -> dict:
    text = read_text(path)

    def one(pattern, flags=re.M):
        found = re.search(pattern, text, flags)
        return found.group(1).strip() if found else None

    checkpoints = one(r"^\s*checkpoints=(\S+)")
    root_path = one(r"^\s*root_path=(\S+)")
    devices = one(r"(CUDA_VISIBLE_DEVICES=[0-9,]+)")
    workers = one(r"--num_workers\s+(\S+)")
    dataset = one(r"^\s*dataset=(\S+)")
    model_name = one(r"^\s*model_name=(\S+)")
    model_id = one(r"--model_id\s+(\S+)")
    comment = one(r"^\s*comment='([^']*)'")

    bad_ckpt = checkpoints is None or checkpoints.startswith(("/path/to", "/data/hwx"))
    row = {
        "file": path.name,
        "checkpoints": ("OK" if not bad_ckpt else "FAIL") + f"  {checkpoints}",
        "root_path": ("OK" if root_path and Path(root_path).is_dir() else "FAIL")
                     + f"  {root_path}",
        "CUDA_VISIBLE_DEVICES": ("OK" if devices == "CUDA_VISIBLE_DEVICES=0"
                                 else "FAIL") + f"  {devices}",
        "multi_gpu": "OK  없음" if "--multi_gpu" not in text else "FAIL  남아있음",
        "num_workers": ("OK" if workers == config.get("NUM_WORKERS") else "FAIL")
                       + f"  {workers}",
        "dataset": ("OK" if dataset == expect_dataset else "FAIL") + f"  {dataset}",
        "name_agree": ("OK" if model_name == model_id == comment == expect_model
                       else "FAIL") + f"  {model_name}/{model_id}/{comment}",
        "batch_size": one(r"^\s*batch_size=(\S+)"),
        "train_epochs": one(r"^\s*train_epochs=(\S+)"),
        "num_process": one(r"^\s*num_process=(\S+)"),
        "num_processes": one(r"--num_processes\s+(\S+)"),
    }
    row["ok"] = all(not str(row[k]).startswith("FAIL") for k in _CHECKS)
    return row


def verify_all(config: dict | None = None) -> list:
    config = config if config is not None else load_config()
    rows = []
    for dataset in DATASETS:
        for model, _, _ in MODELS:
            path = OUT_DIR / f"{model}_{dataset}.sh"
            if not path.exists():
                rows.append({"file": path.name, "ok": False,
                             "checkpoints": "FAIL  파일이 없습니다"})
                continue
            rows.append(verify_one(path, dataset, model, config))
    smoke = OUT_DIR / "_smoke_CPMLP_CALB.sh"
    if smoke.exists():
        rows.append(verify_one(smoke, "CALB", "CPMLP", config))
    return rows


def print_table(rows: list) -> None:
    columns = ["file"] + list(_CHECKS) + ["batch_size", "train_epochs",
                                          "num_process", "num_processes"]
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in columns}
    print(" | ".join(c.ljust(widths[c]) for c in columns))
    print("-+-".join("-" * widths[c] for c in columns))
    for row in rows:
        print(" | ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns))
    failed = [r["file"] for r in rows if not r.get("ok")]
    print()
    print(f"통과 {len(rows) - len(failed)}/{len(rows)}"
          + (f" — 실패: {', '.join(failed)}" if failed else ""))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="train/make_scripts.py")
    parser.add_argument("--check", action="store_true", help="생성하지 않고 검증만")
    args = parser.parse_args(argv)

    config = load_config()
    if not args.check:
        made = generate(config)
        for result in made:
            print(f"{result['name']}  <- upstream/{Path(result['source']).name}"
                  f"  (치환 {len(result['changes'])}건)")
        write_text(OUT_DIR / "changes.txt",
                   "\n\n".join(paths_mod.format_changes(r) for r in made))
        print(f"\n치환 내역: {OUT_DIR / 'changes.txt'}")
        print()

    rows = verify_all(config)
    print_table(rows)
    return 0 if all(r.get("ok") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
