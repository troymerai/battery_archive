# RUN.md — MLP · CPMLP · Transformer · CPTransformer 실행법

이 기계(117호 Whitefox · RTX 5080 단일)에서 BatteryLife 베이스라인 4종을
돌리는 방법입니다. 명령을 그대로 복사해 붙이면 됩니다.

**먼저 §8 조건 차이표를 읽으십시오.** 논문과 다른 조건이 여덟 항목
있습니다. 그것을 모르고 얻은 수치는 논문 표와 비교할 수 없습니다.

---

## 1. 실행 전 한 줄

```powershell
cd D:\battery_archive; .\.venv-blife\Scripts\Activate.ps1
```

확인 (선택):

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_capability())"
# 2.11.0+cu128 True (12, 0)
```

**torch 를 재설치하지 마십시오.** `requirements.txt` 를 그대로 설치하면
`accelerate` 의 `torch>=1.10.0` 해석 때문에 pip 이 torch 를 2.4.1(비 cu128)
로 되돌립니다. 2.4.1 은 sm_120 을 지원하지 않아 5080 에서 못 씁니다.
불가피하면 `pip install -c envs\constraints.txt ...` 를 쓰십시오.

---

## 2. 권장 순서와 예상 소요

CALB 는 27셀, MIX_large 는 843셀입니다. 30배 차이입니다.

| # | 조합 | 셀 수 | 예상 |
|---|---|---|---|
| 1 | `CPMLP_CALB` | 27 | 수 분. **스모크로 이미 확인됨** |
| 2 | `MLP_CALB` | 27 | 수 분. CyclePatch 대조군 |
| 3 | `CPTransformer_CALB` | 27 | 수 분 |
| 4 | `Transformer_CALB` | 27 | 수 분 ← 여기까지 CALB 2×2 완성 |
| 5 | `CPMLP_MIX_large` | 843 | 오래 걸림. 백그라운드 |
| 6 | `MLP_MIX_large` | 843 | 오래 걸림 |
| 7 | `CPTransformer_MIX_large` | 843 | 오래 걸림 |
| 8 | `Transformer_MIX_large` | 843 | 오래 걸림 |

**"수 분"의 근거.** 스모크(`CPMLP_CALB`, `train_epochs=1`)가 처음부터 끝까지
**12.2초**였습니다. 1 에폭 학습 자체는 0.98초, 나머지는 accelerate 기동과
데이터 로딩입니다. 정식 실행은 `train_epochs=100` · `patience=5` 이므로
최대 100 에폭입니다.

**MIX_large 에는 근거가 없습니다.** 측정하지 않았습니다. 셀 수가 31배이고
셀마다 사이클 수도 다르므로 CALB 값을 곱해서 추정하지 마십시오. 5번을
먼저 하나 돌려 실측하고 나머지를 판단하는 편이 낫습니다.

**MIX_large 첫 실행은 `data/extracted/total_MICH/` 를 만듭니다.**
`data_loader.py:391-393` 이 `MICH/`(40) 와 `MICH_EXP/`(18) 를 합쳐 58개
pkl 을 복사합니다. 한 번만 생깁니다. CALB 실행에는 해당 없습니다.

---

## 3. 실행 명령 8줄

작업 디렉터리는 `upstream\BatteryLife` 여야 합니다. 스크립트가 진입점을
상대경로로 부르고, 그 안에서 `data_provider/life_classes.json` 을 또
상대경로로 열기 때문입니다.

### 3-1. 런처로 (권장)

로그·pid·스크립트 사본을 `runs/<시각>_<이름>/` 에 남기고 백그라운드로
띄웁니다. 작업 디렉터리는 런처가 맞춥니다.

```powershell
python -m train.launch .build\batterylife\CPMLP_CALB.sh              --built
python -m train.launch .build\batterylife\MLP_CALB.sh                --built
python -m train.launch .build\batterylife\CPTransformer_CALB.sh      --built
python -m train.launch .build\batterylife\Transformer_CALB.sh        --built
python -m train.launch .build\batterylife\CPMLP_MIX_large.sh         --built
python -m train.launch .build\batterylife\MLP_MIX_large.sh           --built
python -m train.launch .build\batterylife\CPTransformer_MIX_large.sh --built
python -m train.launch .build\batterylife\Transformer_MIX_large.sh   --built
```

`python train\launch.py` 가 아니라 **`python -m train.launch`** 입니다.
전자는 `train` 패키지를 못 찾습니다.

`--dry-run` 을 붙이면 명령만 보고 실행하지 않습니다.

### 3-2. bash 로 직접

터미널에 진행 상황을 그대로 보고 싶을 때.

```powershell
cd D:\battery_archive\upstream\BatteryLife
bash D:/battery_archive/.build/batterylife/CPMLP_CALB.sh 2>&1 | Tee-Object D:\battery_archive\runs\CPMLP_CALB.log
```

bash 는 `C:\Program Files\Git\usr\bin\bash.exe` 에 있습니다. `.ps1` 사본은
만들지 않았습니다 — bash 가 있으므로 필요 없습니다.

---

## 4. 백그라운드 실행 (창을 닫아도 유지)

§3-1 의 런처는 이미 백그라운드로 띄웁니다. 다만 **터미널을 닫으면 자식
프로세스가 같이 죽을 수 있습니다.** 확실히 살려두려면 창을 분리하십시오.

```powershell
cd D:\battery_archive
Start-Process -FilePath "$PWD\.venv-blife\Scripts\python.exe" `
  -ArgumentList "-m","train.launch",".build\batterylife\CPMLP_MIX_large.sh","--built" `
  -WorkingDirectory "$PWD" -WindowStyle Hidden
```

여러 개를 동시에 돌려도 accelerate 포트는 겹치지 않습니다 — 8개 스크립트에
서로 다른 `master_port` 를 넣어 두었습니다. 다만 **GPU 는 한 장입니다.**
동시에 돌리면 VRAM 을 나눠 쓰고 서로 느려집니다. MIX_large 는 하나씩
돌리십시오.

진행 확인:

```powershell
Get-Content D:\battery_archive\runs\<시각>_<이름>\log.txt -Tail 20 -Wait
```

---

## 5. 중단 · 재개

### 중단

```powershell
Get-Content D:\battery_archive\runs\<시각>_<이름>\pid.txt
Stop-Process -Id <pid>
```

`pid.txt` 는 bash 래퍼의 pid 입니다. 실제 학습은 그 아래 `python.exe`
입니다. 남으면 이렇게 잡습니다.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run_main_nodeepspeed*' } |
  Select-Object ProcessId, CommandLine
```

### 재개 — **없습니다**

상위 코드에 재개 기능이 없습니다. 그리고 더 나쁜 것이 있습니다.

> `run_main.py:213-215` 가 시작할 때 같은 이름의 체크포인트 폴더를
> **통째로 지웁니다** (`del_files` → `shutil.rmtree`).

폴더 이름은 `{model}_sl..._dataset{dataset}_..._bs{batch}_s{seed}-{comment}`
로 정해집니다. **`train_epochs` 는 이름에 들어가지 않습니다.** 따라서
같은 조합을 다시 돌리면 이전 결과가 사라집니다.

지키고 싶으면 먼저 옮기십시오.

```powershell
Move-Item D:\battery_archive\data\checkpoints\<폴더> D:\battery_archive\data\checkpoints\<폴더>_keep
```

중간에 죽은 실행을 이어받을 방법은 없습니다. 처음부터 다시 돌려야 합니다.

---

## 6. 결과 위치

| 무엇 | 어디 |
|---|---|
| 체크포인트 | `data\checkpoints\<setting>-<comment>\model.safetensors` |
| 스케일러 | 같은 폴더의 `label_scaler` · `life_class_scaler` (joblib) |
| 실행 인자 | 같은 폴더의 `args.json` |
| 로그 | `runs\<시각>_<이름>\log.txt` (런처) 또는 지정한 경로 |
| 치환 내역 | `.build\batterylife\changes.txt` |
| 지표 | **파일로 저장되지 않습니다.** 로그의 `Best model performance:` 줄 |

스모크가 만든 실제 예:

```
data\checkpoints\CPMLP_sl1_lr5e-05_dm128_nh8_el4_dl2_df256_lradjconstant_datasetCALB_lossMSE_wd0.0_wlFalse_bs16_s2021-CPMLP\
```

상위 코드는 지표를 wandb 로 보내고 stdout 에 찍을 뿐입니다
(`run_main.py:427-435`). **이 환경에서는 wandb 를 껐습니다**
(`WANDB_MODE=disabled`). 로그인하지 않은 기계에서 `wandb.init` 이 멈추기
때문입니다. 지표는 stdout 에 그대로 남으므로 §7 로 뽑습니다.

---

## 7. `train/collect.py` — 로그에서 지표 뽑기

구현되어 있습니다. 로그의 `Best model performance:` 줄을 파싱합니다.

```powershell
python -m train.collect                       # 도움말
python -m train.collect --all                 # runs/ 전부
python -m train.collect 20260804-130117_CPMLP_CALB
python -m train.collect --all --out experiments\results\my_metrics.json
```

기본 출력은 `experiments\results\train_metrics.json` 입니다.

**주의 둘.**

- `MAPE` 는 비율입니다. 백분율이 아닙니다 (`utils/metrics.py:26` —
  `mean(|(pred-true)/true|)`). 논문 표와 맞출 때 100 을 곱해야 하는지
  확인하십시오. 반면 `15%-accuracy` · `10%-accuracy` 는 이미 백분율입니다
  (스모크 값 51.71 · 45.67).
- `run_main.py:125-126` 의 `--alpha1` · `--alpha2` **도움말 문구가 서로
  바뀌어 있습니다.** 값과 출력 라벨은 맞습니다 — `alpha1=0.15` 가
  `15%-accuracy` 로 찍힙니다. 도움말만 보고 따라가면 뒤집어 읽습니다.

`collect.py` 는 `runs/<...>/` 아래에서 `args.json` 을 찾습니다. 실제
`args.json` 은 `CKPT_ROOT` 아래에 생기므로 못 찾습니다. 이때는 note 에
그 사실을 적고 지표만 냅니다. 설정이 필요하면 체크포인트 폴더의
`args.json` 을 직접 보십시오.

---

## 8. 알려진 조건 차이 — **이 표 없이는 논문과 비교할 수 없습니다**

| 항목 | 논문 / 원본 | 이 기계 | 왜 |
|---|---|---|---|
| torch | 2.4.1 | **2.11.0+cu128** | 2.4.1 은 sm_120(Blackwell) 미지원. 5080 에서 못 씀 |
| pandas | 2.2.3 | 3.0.5 | |
| scipy | 1.15.2 | 1.17.1 | |
| scikit-learn | 1.4.2 | 1.9.0 | |
| **deepspeed** | **0.15.0 · ZeRO stage-2** | **미설치 · 우회** | 아래 별항 |
| GPU | 원본 스크립트는 2장 가정 (`--multi_gpu`, `num_process=2`) | RTX 5080 **1장** | `--multi_gpu` 제거, `num_processes=1` |
| num_workers | 8 (MLP·CPMLP) / 32 (CPTransformer) | **0** | Windows 는 워커마다 프로세스를 통째 복제. 16GB RAM |
| batch_size | 32 (MLP·CPTransformer) / 16 (CPMLP) | **16** 전부 | `config.env` 의 `BATCH_SIZE` 로 통일 |
| wandb | 사용 | `WANDB_MODE=disabled` | 로그인 없는 기계에서 `wandb.init` 이 멈춤 |
| **Transformer 하이퍼파라미터** | **원본 스크립트 없음** | **CPTransformer 값 그대로** | 아래 별항 |
| dataset (MLP) | `MIX_large` | CALB / MIX_large 두 벌 | 아래 별항 |
| **하이퍼파라미터 전반** | `assets/Selected_hyperparameters.md` 가 (모델·도메인·seed) 별로 지정 | **셸 스크립트 값** — 문서와 거의 전부 다름 | 아래 §8-4. **이대로는 Table 3 재현이 아닙니다** |
| **Li-ion (`MIX_large`)** | 843셀 | **로딩 실패** | 아래 §8-5 |
| **Transformer 실행** | Table 3 에서 `-` (OOM) | **생성 불가 (`AttributeError`)** | 아래 §8-6 |
| 반복 3회의 정체 | 논문 §4.1 "three times" | 도메인마다 다름 | 아래 §8-7 |

### 8-1. deepspeed — 조건이 실제로 다릅니다

`run_main.py:136-137` 이 `DeepSpeedPlugin` 을 **조건 없이** 만들어
`Accelerator` 에 넘깁니다. accelerate 0.29.3 은 plugin 이 있으면 deepspeed
가 없을 때 `ImportError` 로 죽습니다 (`accelerator.py:294-296`). 분기가
없습니다. 즉 **deepspeed 는 "스크립트 미사용"이 아니라 필수**입니다.

이 기계에는 넣을 수 없습니다. PyPI 에 Windows 휠이 없어 소스 빌드만
가능한데, CUDA Toolkit(`nvcc`) 도 MSVC(`cl`) 도 없습니다. 실측:

```
pip install deepspeed                        -> Unable to pre-compile ops without torch installed
pip install --no-build-isolation deepspeed   -> MissingCUDAException: CUDA_HOME does not exist
```

그래서 `upstream/` 을 고치지 않고 `.build/batterylife/run_main_nodeepspeed.py`
를 만들었습니다. 원본 소스를 읽어 **두 줄만** 바꾸고 exec 합니다.

```
- deepspeed_plugin = DeepSpeedPlugin(hf_ds_config='./ds_config_zero2_baseline.json')
+ deepspeed_plugin = None
- Accelerator(kwargs_handlers=[ddp_kwargs], deepspeed_plugin=deepspeed_plugin, ...)
+ Accelerator(kwargs_handlers=[ddp_kwargs], ...)
```

**원본은 ZeRO stage-2 로 돕니다. 이쪽은 accelerate 기본 경로입니다.**
GPU 가 한 장이면 ZeRO 의 옵티마이저 상태 파티셔닝은 나눌 상대가 없지만,
`ds_config_zero2_baseline.json` 은 그 외에도 그래디언트 버킷 크기 등을
지정합니다. 같은 조건이라고 말할 수 없습니다. **수치를 논문과 비교할 때
이 항목을 반드시 함께 적으십시오.**

### 8-2. Transformer 는 논문 조건이 아닙니다

`upstream/BatteryLife/train_eval_scripts/` 에 **`Transformer.sh` 가
없습니다.** `models/Transformer.py` 는 있습니다.

그래서 `CPTransformer.sh` 를 그대로 베끼고 `model_name` · `--model_id` ·
`comment` 셋만 바꿨습니다. 즉 `Transformer_CALB.sh` ·
`Transformer_MIX_large.sh` 의 학습률·층수·`d_model`·`n_heads` 는 전부
**CPTransformer 용으로 튜닝된 값**입니다.

```
learning_rate=0.00005  lstm_layers=6  e_layers=6  d_layers=4
d_model=128  d_ff=256  n_heads=4  seed=2024
```

Transformer 에 맞춰진 값이 아닙니다. **Transformer 결과를 논문의
Transformer 행과 직접 비교하지 마십시오.** CPTransformer 와의 CyclePatch
대조로만 읽는 편이 안전합니다.

원본 형태의 템플릿은 `train/templates/Transformer.sh` 에 있습니다.

### 8-3. 데이터셋을 통일했습니다

원본은 `MLP.sh` 가 `MIX_large`, `CPMLP.sh` 가 `CALB` 를 씁니다. 서로 다른
데이터로 학습한 두 모델을 비교하면 **CyclePatch 효과 비교가 성립하지
않습니다.** 그래서 CALB 한 벌, MIX_large 한 벌씩 총 8개를 만들었습니다.

**dataset · 모델 이름 · `master_port` 말고 학습 하이퍼파라미터는 원본
값을 그대로 두었습니다.** 학습률·층수·`d_model` 은 모델마다 따로 튜닝된
값이라 임의로 맞추면 비교가 오염됩니다.

바뀐 것은 `batch_size` 뿐입니다 — MLP·CPTransformer 의 원본 32 가
`config.env` 의 `BATCH_SIZE=16` 으로 내려갔습니다. 이것은 실행 자원
항목이지만 **학습 결과에 영향을 줍니다.** 위 표에 적혀 있습니다.

### 8-4. 셸 스크립트는 논문 설정이 아닙니다

`assets/Selected_hyperparameters.md` 가 (모델, 도메인, seed) 48행으로
`batch_size` · `d_model` · `d_ff` · `e_layers` · `d_layers` · `dropout` ·
`learning_rate` 를 지정합니다. **셸 스크립트 값과 거의 전부 다릅니다.**

| 조합 | 항목 | 문서 | 셸 |
|---|---|---:|---:|
| CPMLP / CALB / 2021 | `batch_size` | 8 | 16 |
| | `d_model` | 32 | 128 |
| | `d_ff` | 32 | 256 |
| | `e_layers` | 12 | 4 |
| | `d_layers` | 6 | 2 |
| | `dropout` | 0.1 | 0 |
| CPTransformer / Li-ion / 2024 | `batch_size` | 128 | 32 |
| | `d_model` | 256 | 128 |
| | `d_ff` | 64 | 256 |
| | `e_layers` | 1 | 6 |
| | `d_layers` | 12 | 4 |

`learning_rate` 만 양쪽이 같습니다. `MLP` 과 `Transformer` 는 문서에
아예 없습니다. 문서는 값이 2 GPU 기준이며 `batch_size` 는 프로세스당
값이라 실효 배치가 2배라고 적습니다 (`:3`).

**따라서 `.build/` 의 8개를 그대로 돌린 결과는 Table 3 과 비교할 수
없습니다.** `PLAN.md` §4-1 을 먼저 정하십시오. (`findings` TRN-007)

### 8-5. Li-ion(`MIX_large`) 은 지금 돌지 않습니다

843셀 중 6셀(`MICH_13R` · `14C` · `15H` · `16R` · `17C` · `18H` — 전부
SOC 창 50-100)의 라벨이 배포 `Life labels` 에 없습니다. `eol` 이 `None`
이 되면 `data_loader.py:443` 이 값 5개를 돌려주는데 호출부(`:487`)는
6개로 언팩해 `ValueError: not enough values to unpack (expected 6, got 5)`
로 로딩 도중 죽습니다. 실측 재현: `runs/timing_CPMLP_MIX_large.log`.

CALB · ZN-coin · NAion 은 라벨 누락이 0이라 영향이 없습니다.
대응은 `PLAN.md` §4-2. (`findings` TRN-010)

### 8-6. `Transformer` 는 OOM 이 아니라 실행 불가입니다

`models/Transformer.py:71` 이 `configs.num_class` 를 읽는데 실제 인자
이름은 `--class_num` 입니다 (`run_main.py:102`). `Model(args)` 생성
시점에 `AttributeError` 로 죽습니다. 추가로 `forward` 가 위치인자 4개를
요구하는데 `run_main.py:322` 는 2개만 넘기고, 배치가 4차원인데
`DataEmbedding` 은 3차원을 가정합니다.

`MLP` · `CPMLP` · `CPTransformer` 는 셋 다 통과합니다.
`.build/batterylife/Transformer_*.sh` 2개는 **돌리면 즉시 실패합니다.**
(`findings` TRN-008)

### 8-7. 반복 3회의 정체가 도메인마다 다릅니다

| 도메인 | 반복 방식 |
|---|---|
| Zn-ion · Na-ion · CALB | `--dataset` 을 `X` · `X42` · `X2024` 로 바꿈. **분할이 3벌** |
| Li-ion | 분할이 1벌. **`--seed` 만 2021 · 42 · 2024 로 바꿈** |

`MIX_large` 에는 seed 변형 분기가 없습니다. `MIX_all` 계열(1001셀)이
`split_recorder` 에 있으나 `data_loader.py` 의 어느 분기도 참조하지 않아
도달할 수 없습니다. (`findings` TRN-009)

---

## 9. 스크립트를 다시 만들려면

`config.env` 를 고쳤거나 상위가 바뀌었을 때.

```powershell
python -m train.make_scripts          # 8개 + 스모크 생성, 검증표 출력
python -m train.make_scripts --check  # 생성 없이 검증만
```

`.build/` 는 `.gitignore` 대상입니다. 지워도 위 명령으로 복원됩니다.
**`upstream/` 은 절대 고치지 마십시오** — 치환본은 `.build/` 에만 둡니다.

---

## 10. 이 문서를 읽는 순서

1. §8 조건 차이 — 무엇이 논문과 다른지
2. §1 활성화 → §3 실행
3. §5 재개가 없다는 것 (다시 돌리면 이전 체크포인트가 지워집니다)
4. §7 지표 뽑기
