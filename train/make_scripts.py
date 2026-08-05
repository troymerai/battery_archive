#!/usr/bin/env python3
"""학습 스크립트 **36개**를 ``.build/batterylife/`` 에 만듭니다.

    python train/make_scripts.py            생성 + 검증표 출력
    python train/make_scripts.py --check    이미 만든 것만 검증

왜 36개인가
-----------

3 모델(MLP · CPMLP · CPTransformer) × 4 도메인(Li-ion · Zn-ion · Na-ion ·
CALB) × 3 seed(2021 · 42 · 2024).

``Transformer`` 는 **뺐습니다.** 배포 코드가 실행되지 않습니다 (TRN-008).
논문 Table 3 의 ``-`` 와 사유가 다르므로 같은 자리에 놓을 수 없습니다.

하이퍼파라미터는 어디서 오는가
------------------------------

``upstream/BatteryLife/assets/Selected_hyperparameters.md`` 를 **실행 시점에
읽어서** 씁니다. 표를 여기에 베껴 두지 않습니다 — 베끼면 상위가 고쳤을 때
조용히 갈립니다.

문서가 지정하는 것은 **7개뿐**입니다.

    batch_size · d_model · d_ff · e_layers · d_layers · dropout · learning_rate

나머지(``n_heads`` · ``lstm_layers`` · ``train_epochs`` · ``patience`` ·
``early_cycle_threshold`` · ``charge_discharge_length`` · ``seq_len`` ·
``lradj`` · ``loss``)는 문서에 없습니다. **원본 셸 스크립트 값을 그대로
둡니다.** 각 파일 머리에 그 사실이 적혀 있습니다.

``MLP`` 은 문서 표에 **아예 없습니다.** CyclePatch 계열 넷(CPMLP ·
CPTransformer · CPGRU · CPLSTM)만 실려 있습니다. ``MLP.sh`` 의 셸 값을
전부 그대로 쓰고 도메인과 seed 만 바꿉니다. 파일 머리에 "문서 근거 없음"
이라고 적습니다.

배치 크기 환산
--------------

문서 머리말이 명시합니다 — 표의 값은 **프로세스당** 값이고 GPU 2장이라
실효 배치는 그 2배입니다. 이 기계는 GPU 가 한 장이므로 **문서값 × 2** 를
한 프로세스에 줍니다. 그래야 실효 배치가 논문과 같아집니다.

seed 축
-------

Li-ion(``MIX_large_841``)만 분할이 **1벌**이라 ``--seed`` 로 3번 반복합니다.
Zn-ion · Na-ion · CALB 는 분할이 seed 별로 **3벌**입니다 (``ZN-coin`` /
``ZN-coin42`` / ``ZN-coin2024`` …). 그래도 **36개 전부에 ``--seed`` 를 명시**
합니다 — 체크포인트 이름이 seed 를 포함하지 않으면 겹칩니다.

Li-ion 은 ``MIX_large`` 가 아니라 ``MIX_large_841``
---------------------------------------------------

배포 ``MIX_large`` 843셀 중 6셀은 라벨이 배포되지 않아 로딩 도중 죽습니다
(TRN-010). 그 6셀을 뺀 841셀 정의를 ``run_main_nodeepspeed.py`` 가 런타임에
더합니다. **``upstream/`` 은 고치지 않습니다.**
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from train import paths as paths_mod
from verify import REPO_ROOT, load_config, read_text, use_utf8_stdout, write_text

use_utf8_stdout()

OUT_DIR = REPO_ROOT / ".build" / "batterylife"
OLD_DIR = OUT_DIR / "_old_shellparam"
SCRIPTS = "BatteryLife/train_eval_scripts"
HPARAM_DOC = (REPO_ROOT / "upstream" / "BatteryLife" / "assets"
              / "Selected_hyperparameters.md")

# (모델, 원본 셸 스크립트).  Transformer 는 없습니다 — TRN-008.
MODELS = [
    ("MLP", f"{SCRIPTS}/MLP.sh"),
    ("CPMLP", f"{SCRIPTS}/CPMLP.sh"),
    ("CPTransformer", f"{SCRIPTS}/CPTransformer.sh"),
]

DOMAINS = ["Li-ion", "Zn-ion", "Na-ion", "CALB"]
SEEDS = ["2021", "42", "2024"]

# 도메인 × seed → ``--dataset`` 인자. Li-ion 만 분할이 1벌입니다.
DATASETS = {
    ("Li-ion", "2021"): "MIX_large_841",
    ("Li-ion", "42"): "MIX_large_841",
    ("Li-ion", "2024"): "MIX_large_841",
    ("Zn-ion", "2021"): "ZN-coin",
    ("Zn-ion", "42"): "ZN-coin42",
    ("Zn-ion", "2024"): "ZN-coin2024",
    ("Na-ion", "2021"): "NAion",
    ("Na-ion", "42"): "NAion42",
    ("Na-ion", "2024"): "NAion2024",
    ("CALB", "2021"): "CALB",
    ("CALB", "42"): "CALB42",
    ("CALB", "2024"): "CALB2024",
}

# 문서가 지정하는 7개. 이것만 덮어씁니다.
DOC_KEYS = ["batch_size", "d_model", "d_ff", "e_layers", "d_layers",
            "dropout", "learning_rate"]

# 문서가 지정하지 **않는** 것. 원본 셸 값이 그대로 남습니다.
SHELL_KEYS = ["n_heads", "lstm_layers", "train_epochs", "patience",
              "early_cycle_threshold", "charge_discharge_length",
              "seq_len", "lradj", "loss"]

PORT_BASE = 27000  # 36개가 전부 다릅니다: 27000 ~ 27035

# 소요 시간 측정용 사본 (지시 §E-1). ``train_epochs=3`` 말고는 정식 파일과
# 같습니다. **지표로 쓰지 마십시오.** 포트는 27100 부터라 정식 36개와 겹치지
# 않습니다.
#
#   CPMLP · CALB          가장 작은 조합
#   CPTransformer · CALB  가장 무거운 모델
TIMING = [("CPMLP", "CALB", "2021"), ("CPTransformer", "CALB", "2021")]
TIMING_PORT_BASE = 27100
TIMING_EPOCHS = "3"


# --------------------------------------------------------------------------
# 문서 파싱
# --------------------------------------------------------------------------

def read_hparam_doc(path: Path = HPARAM_DOC) -> dict:
    """``Selected_hyperparameters.md`` 의 표를 읽습니다.

    Returns
    -------
    dict
        ``(model, domain, seed)`` -> ``{항목: 값}``. 값은 **문자열 그대로**
        둡니다. ``5e-05`` 를 float 로 바꾸면 다시 찍을 때 표기가 달라집니다.
    """
    text = read_text(path)
    table = {}
    header = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            if cells[:3] == ["model", "dataset", "seed"]:
                header = cells
            continue
        if set("".join(cells)) <= set("-: "):    # 구분선
            continue
        row = dict(zip(header, cells))
        table[(row["model"], row["dataset"], row["seed"])] = {
            k: row[k] for k in DOC_KEYS if k in row}
    if not table:
        raise RuntimeError(f"하이퍼파라미터 표를 읽지 못했습니다: {path}")
    return table


def _shell_value(source_text: str, key: str) -> str | None:
    found = re.search(rf"^\s*{re.escape(key)}=(\S+)", source_text, re.M)
    return found.group(1) if found else None


def _source_of(model: str) -> str:
    return dict(MODELS)[model]


# --------------------------------------------------------------------------
# 파일 머리의 근거 표시
# --------------------------------------------------------------------------

def _header(model, domain, seed, dataset, doc_row, shell_text) -> str:
    lines = [
        "#",
        f"# 조합: {model} · {domain} · seed {seed}   ( --dataset {dataset} )",
        "#",
    ]
    if doc_row is None:
        lines += [
            "# 문서 근거 없음 — 셸 스크립트 값 사용",
            "#   upstream/BatteryLife/assets/Selected_hyperparameters.md 의 표에",
            f"#   {model} 은 없습니다. CyclePatch 계열(CPMLP · CPTransformer ·",
            "#   CPGRU · CPLSTM)만 실려 있습니다. 아래 하이퍼파라미터는 전부",
            f"#   원본 {Path(_source_of(model)).name} 의 값이며 논문 조건이 아닙니다.",
            "#   바꾼 것은 dataset · model 이름 · seed · master_port 뿐입니다.",
        ]
    else:
        doc_batch = doc_row["batch_size"]
        lines += [
            "# 하이퍼파라미터 근거:",
            "#   upstream/BatteryLife/assets/Selected_hyperparameters.md",
            f"#   해당 행: | {model} | {domain} | {seed} | ...",
            "#",
            f"# batch_size = 문서값 {doc_batch} × 2 (단일 GPU 환산)"
            f" = {int(doc_batch) * 2}",
            "#   문서 머리말: 표의 값은 프로세스당이고 GPU 2장이라 실효 배치는",
            "#   그 2배입니다. 이 기계는 GPU 1장이므로 한 프로세스에 2배를 줍니다.",
            "#",
            "# 문서가 지정한 7개: " + " · ".join(DOC_KEYS),
            "# 문서가 지정하지 않은 것 — 원본 셸 값 그대로:",
        ]
        carried = [f"{k}={_shell_value(shell_text, k)}" for k in SHELL_KEYS
                   if _shell_value(shell_text, k) is not None]
        for i in range(0, len(carried), 3):
            lines.append("#   " + " · ".join(carried[i:i + 3]))
    lines.append("#")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# DeepSpeed 우회 + 분할 추가 진입점
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
# 그래서 **upstream 을 고치지 않고** 진입점을 .build/ 에 만듭니다. 원본
# 소스를 읽어 바꿔치고 exec 합니다. cwd 는 그대로 upstream/BatteryLife 이므로
# 상대경로(data_provider/life_classes.json 등)는 전부 그대로 동작합니다.
#
# **이것은 학습 조건의 변경입니다.** 원본은 ZeRO stage-2 로 돕니다.
# 이쪽은 accelerate 기본 경로(단일 GPU · fp32 · Adam)로 돕니다.
# docs/RUN.md 의 조건 차이표에 적혀 있습니다. 지우지 마십시오.
#
# 진입점은 이제 **두 가지**를 패치합니다 — deepspeed 우회와 MIX_large_841
# 분할 추가. 본문은 train/templates/entrypoint.py 에 있습니다.

def write_entrypoint() -> Path:
    source = (REPO_ROOT / "upstream" / "BatteryLife" / "run_main.py").resolve()
    template = read_text(REPO_ROOT / "train" / "templates" / "entrypoint.py")
    path = OUT_DIR / "run_main_nodeepspeed.py"
    write_text(path, template.replace("@@RUN_MAIN@@", source.as_posix()))
    return path


# --------------------------------------------------------------------------
# 생성
# --------------------------------------------------------------------------

def _note(model, domain, seed, dataset) -> str:
    if model == "MLP":
        return (f"{domain} / seed {seed} / --dataset {dataset} — "
                "하이퍼파라미터 문서 근거 없음, 셸 값 그대로")
    return (f"{domain} / seed {seed} / --dataset {dataset} — "
            "하이퍼파라미터는 Selected_hyperparameters.md, batch 는 문서값×2")


def _use_entrypoint(path: Path, entrypoint: Path) -> None:
    """스크립트의 ``run_main.py`` 호출을 .build 진입점으로 바꿉니다."""
    text = read_text(path)
    text = text.replace(" run_main.py ", f' "{entrypoint.as_posix()}" ')
    write_text(path, text)


def combos() -> list:
    """36개 조합을 정해진 순서로. 포트는 여기서 한 번에 배정합니다."""
    out = []
    index = 0
    for model, source in MODELS:
        for domain in DOMAINS:
            for seed in SEEDS:
                out.append({
                    "model": model, "source": source, "domain": domain,
                    "seed": seed, "dataset": DATASETS[(domain, seed)],
                    "port": str(PORT_BASE + index),
                    "name": f"{model}_{domain}_s{seed}.sh",
                })
                index += 1
    return out


def _stash_old() -> list:
    """셸 파라미터로 만든 기존 파일을 ``_old_shellparam/`` 으로 **옮깁니다.**

    지우지 않습니다. 새 36개와 섞여 있으면 어느 쪽을 돌렸는지 나중에 못
    가립니다.
    """
    moved = []
    if not OUT_DIR.is_dir():
        return moved
    keep = {"run_main_nodeepspeed.py", "changes_36.txt"}
    new_names = {c["name"] for c in combos()}
    for item in sorted(OUT_DIR.iterdir()):
        if not item.is_file() or item.name in keep or item.name in new_names:
            continue
        if item.name.startswith("_timing36_"):
            continue
        OLD_DIR.mkdir(parents=True, exist_ok=True)
        target = OLD_DIR / item.name
        if target.exists():
            target.unlink()
        item.replace(target)
        moved.append(item.name)
    return moved


def generate(config: dict | None = None) -> list:
    config = config if config is not None else load_config()
    doc = read_hparam_doc()
    moved = _stash_old()
    if moved:
        print(f"기존 {len(moved)}개를 {OLD_DIR.name}/ 으로 옮겼습니다 (지우지 "
              f"않았습니다):\n  " + ", ".join(moved) + "\n")

    entrypoint = write_entrypoint()
    made = []
    for combo in combos():
        model, seed = combo["model"], combo["seed"]
        shell_text = read_text(paths_mod.UPSTREAM / combo["source"])
        doc_row = doc.get((model, combo["domain"], seed))

        # 문서값 × 2. MLP 은 문서에 없으므로 셸 값을 그대로 씁니다.
        hparams = {"seed": seed}
        if doc_row is not None:
            hparams.update({k: v for k, v in doc_row.items() if k != "batch_size"})
            batch = str(int(doc_row["batch_size"]) * 2)
        else:
            batch = _shell_value(shell_text, "batch_size")

        # batch_size 는 paths._apply 의 BATCH_SIZE 규칙이 씁니다. 같은 줄을 두
        # 규칙이 건드리면 changes 가 헷갈리므로 여기 한 곳으로 모읍니다.
        local_config = dict(config, BATCH_SIZE=batch)

        result = paths_mod.build_variant(
            combo["source"], OUT_DIR / combo["name"],
            dataset=combo["dataset"], model=model, port=combo["port"],
            note=_note(model, combo["domain"], seed, combo["dataset"]),
            config=local_config, hparams=hparams,
            header=_header(model, combo["domain"], seed, combo["dataset"],
                           doc_row, shell_text),
        )
        _use_entrypoint(result["path"], entrypoint)
        # ``source`` 는 덮지 않습니다 — build_variant 가 넣은 Path 여야 합니다.
        result.update({k: v for k, v in combo.items() if k != "source"})
        result["doc_batch"] = doc_row["batch_size"] if doc_row else None
        result["batch"] = batch
        made.append(result)

    made += _timing_copies(config, doc)
    write_text(OUT_DIR / "run_domain.sh", _domain_runner())
    return made


# 한 도메인의 9개(3모델 × 3seed)를 **순차로** 돌립니다. 하나가 실패해도
# 다음이 이어집니다 — 밤새 돌리는 것이 목적이라 중간에 멈추면 안 됩니다.
_DOMAIN_RUNNER = """\
#!/usr/bin/env bash
# --- 생성물입니다. 고치려면 train/make_scripts.py 를 고치십시오. ---
#
# 한 도메인의 9개를 순차 실행합니다. GPU 가 한 장이므로 **동시에 돌리지
# 않습니다.** 하나가 실패해도 다음으로 넘어가고, 끝에 실패 목록을 냅니다.
#
#   cd D:/battery_archive/upstream/BatteryLife
#   bash D:/battery_archive/.build/batterylife/run_domain.sh CALB
#
# 도메인: CALB · Na-ion · Zn-ion · Li-ion
set -u
BUILD="{build}"
RUNS="{runs}"
DOMAIN="${{1:-}}"
case "$DOMAIN" in
  CALB|Na-ion|Zn-ion|Li-ion) ;;
  *) echo "도메인을 주십시오: CALB | Na-ion | Zn-ion | Li-ion"; exit 2 ;;
esac

# 가상환경을 켜지 않은 채 돌리면 9개가 전부 accelerate: command not found 로
# 죽습니다. 밤새 돌린 줄 알았는데 아침에 로그 9개가 전부 빈 경우가 그것입니다.
# 한 줄도 돌리기 전에 여기서 멈춥니다.
command -v accelerate >/dev/null || {{ echo "가상환경 미활성 — .venv-blife 를 켜십시오"; exit 1; }}

mkdir -p "$RUNS"
STAMP=$(date +%Y%m%d-%H%M%S)
SUMMARY="$RUNS/${{STAMP}}_${{DOMAIN}}_summary.txt"
FAILED=""

for MODEL in {models}; do
  for SEED in {seeds}; do
    NAME="${{MODEL}}_${{DOMAIN}}_s${{SEED}}"
    SCRIPT="$BUILD/$NAME.sh"
    LOG="$RUNS/${{STAMP}}_${{NAME}}.log"
    if [ ! -f "$SCRIPT" ]; then
      echo "없음: $SCRIPT" | tee -a "$SUMMARY"; FAILED="$FAILED $NAME(없음)"; continue
    fi
    echo "=== $NAME  시작 $(date +%H:%M:%S) ===" | tee -a "$SUMMARY"
    if bash "$SCRIPT" > "$LOG" 2>&1; then
      echo "    끝   $(date +%H:%M:%S)  ->  $LOG" | tee -a "$SUMMARY"
    else
      CODE=$?
      echo "    실패 $(date +%H:%M:%S)  종료코드 $CODE  ->  $LOG" | tee -a "$SUMMARY"
      FAILED="$FAILED $NAME($CODE)"
    fi
  done
done

echo "" | tee -a "$SUMMARY"
if [ -n "$FAILED" ]; then
  echo "실패:$FAILED" | tee -a "$SUMMARY"
  echo "각 로그의 마지막 40줄을 보십시오." | tee -a "$SUMMARY"
  exit 1
fi
echo "$DOMAIN 9개 전부 끝났습니다." | tee -a "$SUMMARY"
"""


def _domain_runner() -> str:
    return _DOMAIN_RUNNER.format(
        build=OUT_DIR.as_posix(),
        runs=(REPO_ROOT / "runs").as_posix(),
        models=" ".join(m for m, _ in MODELS),
        seeds=" ".join(SEEDS),
    )


def _timing_copies(config: dict, doc: dict) -> list:
    """``_timing36_*.sh`` — 3에폭 사본. 정식 36개와 하이퍼파라미터가 같습니다."""
    index = {(c["model"], c["domain"], c["seed"]): c for c in combos()}
    entrypoint = OUT_DIR / "run_main_nodeepspeed.py"
    made = []
    for offset, key in enumerate(TIMING):
        combo = index[key]
        model, domain, seed = key
        shell_text = read_text(paths_mod.UPSTREAM / combo["source"])
        doc_row = doc.get(key)
        hparams = {"seed": seed}
        if doc_row is not None:
            hparams.update({k: v for k, v in doc_row.items() if k != "batch_size"})
            batch = str(int(doc_row["batch_size"]) * 2)
        else:
            batch = _shell_value(shell_text, "batch_size")
        name = f"_timing36_{model}_{domain}_s{seed}.sh"
        result = paths_mod.build_variant(
            combo["source"], OUT_DIR / name,
            dataset=combo["dataset"], model=model,
            epochs=TIMING_EPOCHS, port=str(TIMING_PORT_BASE + offset),
            note=f"측정 전용 — train_epochs={TIMING_EPOCHS}. 지표로 쓰지 "
                 f"마십시오. 정식 파일은 {combo['name']} 입니다.",
            config=dict(config, BATCH_SIZE=batch), hparams=hparams,
            header=_header(model, domain, seed, combo["dataset"],
                           doc_row, shell_text),
        )
        _use_entrypoint(result["path"], entrypoint)
        result.update({k: v for k, v in combo.items() if k != "source"})
        result["name"] = name
        result["port"] = str(TIMING_PORT_BASE + offset)
        result["doc_batch"] = doc_row["batch_size"] if doc_row else None
        result["batch"] = batch
        made.append(result)
    return made


# --------------------------------------------------------------------------
# 검증 (§C-4)
# --------------------------------------------------------------------------

_CHECKS = ("checkpoints", "root_path", "CUDA_VISIBLE_DEVICES", "multi_gpu",
           "num_workers", "dataset", "seed", "batch_size", "name_agree")


def verify_one(combo: dict, doc: dict, config: dict) -> dict:
    path = OUT_DIR / combo["name"]
    if not path.exists():
        return {"file": combo["name"], "ok": False,
                "checkpoints": "FAIL 파일이 없습니다"}
    text = read_text(path)

    def one(pattern, flags=re.M):
        found = re.search(pattern, text, flags)
        return found.group(1).strip() if found else None

    checkpoints = one(r"^\s*checkpoints=(\S+)")
    root_path = one(r"^\s*root_path=(\S+)")
    devices = one(r"(CUDA_VISIBLE_DEVICES=[0-9,]+)")
    workers = one(r"--num_workers\s+(\S+)")
    dataset = one(r"^\s*dataset=(\S+)")
    seed = one(r"^\s*seed=(\S+)")
    batch = one(r"^\s*batch_size=(\S+)")
    model_name = one(r"^\s*model_name=(\S+)")
    model_id = one(r"--model_id\s+(\S+)")
    comment = one(r"^\s*comment='([^']*)'")

    doc_row = doc.get((combo["model"], combo["domain"], combo["seed"]))
    if doc_row is None:
        want_batch = _shell_value(
            read_text(paths_mod.UPSTREAM / combo["source"]), "batch_size")
        batch_note = f"셸값 {want_batch} (문서 근거 없음)"
    else:
        want_batch = str(int(doc_row["batch_size"]) * 2)
        batch_note = f"문서 {doc_row['batch_size']}x2={want_batch}"

    bad_ckpt = checkpoints is None or checkpoints.startswith(("/path/to", "/data/hwx"))
    row = {
        "file": combo["name"],
        "checkpoints": "OK" if not bad_ckpt else "FAIL",
        "root_path": "OK" if root_path and Path(root_path).is_dir() else "FAIL",
        "CUDA_VISIBLE_DEVICES": "OK" if devices == "CUDA_VISIBLE_DEVICES=0" else "FAIL",
        "multi_gpu": "OK" if "--multi_gpu" not in text else "FAIL",
        "num_workers": ("OK" if workers == config.get("NUM_WORKERS") else "FAIL")
                       + f" {workers}",
        "dataset": ("OK" if dataset == combo["dataset"] else "FAIL") + f" {dataset}",
        "seed": ("OK" if seed == combo["seed"] and "--seed $seed" in text
                 else "FAIL") + f" {seed}",
        "batch_size": ("OK" if batch == want_batch else "FAIL") + f" {batch}",
        "name_agree": "OK" if model_name == model_id == comment == combo["model"] else "FAIL",
        "batch_note": batch_note,
        "port": one(r"^\s*master_port=(\S+)"),
        "epochs": one(r"^\s*train_epochs=(\S+)"),
    }
    row["ok"] = all(not str(row[k]).startswith("FAIL") for k in _CHECKS)
    return row


def verify_all(config: dict | None = None) -> list:
    config = config if config is not None else load_config()
    doc = read_hparam_doc()
    return [verify_one(c, doc, config) for c in combos()]


def print_table(rows: list) -> None:
    columns = ["file"] + list(_CHECKS) + ["batch_note", "port", "epochs"]
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in columns}
    print(" | ".join(c.ljust(widths[c]) for c in columns))
    print("-+-".join("-" * widths[c] for c in columns))
    for row in rows:
        print(" | ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns))

    ports = [r.get("port") for r in rows]
    duplicated = sorted({p for p in ports if p and ports.count(p) > 1})
    failed = [r["file"] for r in rows if not r.get("ok")]
    print()
    print(f"master_port 고유: {len(set(ports))}/{len(ports)}"
          + (f" — 중복 {duplicated}" if duplicated else ""))
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
            batch = (f"batch {result['doc_batch']}x2={result['batch']}"
                     if result["doc_batch"] else f"batch {result['batch']} (셸값)")
            print(f"{result['name']:<34} <- {Path(result['source']).name:<18}"
                  f" {batch:<24} port {result['port']}"
                  f"  (치환 {len(result['changes'])}건)")
        write_text(OUT_DIR / "changes_36.txt",
                   "\n\n".join(f"=== {r['name']} ===\n"
                               + paths_mod.format_changes(r) for r in made))
        print(f"\n치환 내역: {OUT_DIR / 'changes_36.txt'}")
        print()

    rows = verify_all(config)
    print_table(rows)
    return 0 if all(r.get("ok") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
