# RUN.md — 36회 학습 실행법

이 기계(117호 Whitefox · RTX 5080 단일)에서 논문 Table 3 에 해당하는
**36회**를 돌리는 방법입니다. 명령을 그대로 복사해 붙이면 됩니다.

> **3 모델**(MLP · CPMLP · CPTransformer) × **4 도메인**(Li-ion · Zn-ion ·
> Na-ion · CALB) × **3 seed**(2021 · 42 · 2024) = **36회**
>
> `Transformer` 는 뺐습니다 — 배포 코드가 실행되지 않습니다 (§8-6).

**먼저 §8 조건 차이표를 읽으십시오.** 논문과 다른 조건이 열 항목 넘게
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

**torch 를 재설치하지 마십시오.** `envs/requirements.txt` 를 그대로 설치하면
`accelerate` 의 `torch>=1.10.0` 해석 때문에 pip 이 torch 를 2.4.1(비 cu128)
로 되돌립니다. 2.4.1 은 sm_120 을 지원하지 않아 5080 에서 못 씁니다.
불가피하면 `pip install -c envs\constraints.txt ...` 를 쓰십시오.

---

## 2. 권장 순서 — 열을 하나씩 완결시킵니다

**CALB 9 → Na-ion 9 → Zn-ion 9 → Li-ion 9.**

작은 것부터가 아니라 **열(도메인)을 완결시키는** 순서입니다. 도메인 하나가
끝나면 그 열은 3모델 × 3seed 가 다 차서 **그 자체로 읽을 수 있는 표**가
됩니다. 모델 순서로 돌면 마지막 하나가 끝날 때까지 아무 열도 완성되지
않습니다.

| 순서 | 도메인 | 셀 (train/val/test) | 샘플 | 로딩 실측 | 9개 추정 |
|---|---|---|---|---|---|
| 1 | **CALB** | 17 / 5 / 5 | 2,683 | 5.1초 | 약 0.3시간 |
| 2 | **Na-ion** | 20 / 6 / 5 | 3,100 | 9.6초 | 약 0.3시간 |
| 3 | **Zn-ion** | 60 / 20 / 20 | 9,900 | 36.2초 | 약 1.1시간 |
| 4 | **Li-ion** | 510 / 165 / 162 | 82,300 | **620.4초** | 약 9.3시간 |

추정 근거와 총계는 `docs/PLAN.md` §3 에 있습니다. **최대 100 에폭 기준
36회 합계 약 33시간**, 조기 종료가 30 에폭쯤에서 걸리면 약 11시간입니다.

**Li-ion 을 마지막에 두는 이유가 하나 더 있습니다.** 로딩만 10분이고,
**RAM 이 모자라면 거기서 죽습니다** — 33.7 GiB 짜리 배열을 한 덩어리로
만듭니다 (§8-9, `findings` TRN-011). 앞의 세 열은 그 영향이 없으므로
먼저 끝내 두는 편이 안전합니다.

---

## 3. 실행 명령 36줄

작업 디렉터리는 `upstream\BatteryLife` 여야 합니다. 스크립트가 진입점을
상대경로로 부르고, 그 안에서 `data_provider/life_classes.json` 을 또
상대경로로 열기 때문입니다. **런처(`-m train.launch`)가 이것을 맞춰
줍니다.**

### 3-1. 런처로 하나씩 (권장)

로그·pid·스크립트 사본을 `runs/<시각>_<이름>/` 에 남기고 백그라운드로
띄웁니다.

```powershell
# --- CALB 9 -------------------------------------------------------------
python -m train.launch .build\batterylife\MLP_CALB_s2021.sh             --built
python -m train.launch .build\batterylife\MLP_CALB_s42.sh               --built
python -m train.launch .build\batterylife\MLP_CALB_s2024.sh             --built
python -m train.launch .build\batterylife\CPMLP_CALB_s2021.sh           --built
python -m train.launch .build\batterylife\CPMLP_CALB_s42.sh             --built
python -m train.launch .build\batterylife\CPMLP_CALB_s2024.sh           --built
python -m train.launch .build\batterylife\CPTransformer_CALB_s2021.sh   --built
python -m train.launch .build\batterylife\CPTransformer_CALB_s42.sh     --built
python -m train.launch .build\batterylife\CPTransformer_CALB_s2024.sh   --built

# --- Na-ion 9 -----------------------------------------------------------
python -m train.launch .build\batterylife\MLP_Na-ion_s2021.sh           --built
python -m train.launch .build\batterylife\MLP_Na-ion_s42.sh             --built
python -m train.launch .build\batterylife\MLP_Na-ion_s2024.sh           --built
python -m train.launch .build\batterylife\CPMLP_Na-ion_s2021.sh         --built
python -m train.launch .build\batterylife\CPMLP_Na-ion_s42.sh           --built
python -m train.launch .build\batterylife\CPMLP_Na-ion_s2024.sh         --built
python -m train.launch .build\batterylife\CPTransformer_Na-ion_s2021.sh --built
python -m train.launch .build\batterylife\CPTransformer_Na-ion_s42.sh   --built
python -m train.launch .build\batterylife\CPTransformer_Na-ion_s2024.sh --built

# --- Zn-ion 9 -----------------------------------------------------------
python -m train.launch .build\batterylife\MLP_Zn-ion_s2021.sh           --built
python -m train.launch .build\batterylife\MLP_Zn-ion_s42.sh             --built
python -m train.launch .build\batterylife\MLP_Zn-ion_s2024.sh           --built
python -m train.launch .build\batterylife\CPMLP_Zn-ion_s2021.sh         --built
python -m train.launch .build\batterylife\CPMLP_Zn-ion_s42.sh           --built
python -m train.launch .build\batterylife\CPMLP_Zn-ion_s2024.sh         --built
python -m train.launch .build\batterylife\CPTransformer_Zn-ion_s2021.sh --built
python -m train.launch .build\batterylife\CPTransformer_Zn-ion_s42.sh   --built
python -m train.launch .build\batterylife\CPTransformer_Zn-ion_s2024.sh --built

# --- Li-ion 9 -----------------------------------------------------------
python -m train.launch .build\batterylife\MLP_Li-ion_s2021.sh           --built
python -m train.launch .build\batterylife\MLP_Li-ion_s42.sh             --built
python -m train.launch .build\batterylife\MLP_Li-ion_s2024.sh           --built
python -m train.launch .build\batterylife\CPMLP_Li-ion_s2021.sh         --built
python -m train.launch .build\batterylife\CPMLP_Li-ion_s42.sh           --built
python -m train.launch .build\batterylife\CPMLP_Li-ion_s2024.sh         --built
python -m train.launch .build\batterylife\CPTransformer_Li-ion_s2021.sh --built
python -m train.launch .build\batterylife\CPTransformer_Li-ion_s42.sh   --built
python -m train.launch .build\batterylife\CPTransformer_Li-ion_s2024.sh --built
```

`python train\launch.py` 가 아니라 **`python -m train.launch`** 입니다.
전자는 `train` 패키지를 못 찾습니다. `--dry-run` 을 붙이면 명령만 봅니다.

**위 36줄을 한꺼번에 붙이지 마십시오.** 런처는 기다리지 않고 바로
돌아옵니다. 36개가 동시에 뜨면 GPU 한 장을 36등분합니다. 하나씩 돌리거나
§3-2 를 쓰십시오.

### 3-2. 한 도메인 9개를 순차로 — **이쪽을 권합니다**

```powershell
cd D:\battery_archive\upstream\BatteryLife
bash D:/battery_archive/.build/batterylife/run_domain.sh CALB
```

도메인 이름은 `CALB` · `Na-ion` · `Zn-ion` · `Li-ion` 넷입니다.

- **하나가 실패해도 다음이 이어집니다.** 끝에 실패 목록을 냅니다.
- 로그는 `runs\<시각>_<이름>.log`, 요약은 `runs\<시각>_<도메인>_summary.txt`.
- 동시에 돌리지 않습니다. GPU 가 한 장이라 그것이 맞습니다.

네 도메인을 이어서 돌리려면:

```powershell
cd D:\battery_archive\upstream\BatteryLife
bash -c 'for d in CALB Na-ion Zn-ion Li-ion; do bash D:/battery_archive/.build/batterylife/run_domain.sh "$d"; done'
```

바깥 루프도 `run_domain.sh` 의 종료 코드를 무시하므로 한 도메인이 통째로
실패해도 다음 도메인으로 갑니다.

### 3-3. bash 로 직접 하나만

터미널에 진행 상황을 그대로 보고 싶을 때.

```powershell
cd D:\battery_archive\upstream\BatteryLife
bash D:/battery_archive/.build/batterylife/CPMLP_CALB_s2021.sh 2>&1 | Tee-Object D:\battery_archive\runs\CPMLP_CALB_s2021.log
```

bash 는 `C:\Program Files\Git\usr\bin\bash.exe` 에 있습니다.

---

## 4. 백그라운드 실행 (창을 닫아도 유지)

`Start-Process` 로 창을 분리합니다. 이 프로세스는 띄운 터미널과 무관하게
살아 있습니다.

```powershell
cd D:\battery_archive
Start-Process -FilePath "C:\Program Files\Git\bin\bash.exe" `
  -ArgumentList "D:/battery_archive/.build/batterylife/run_domain.sh","CALB" `
  -WorkingDirectory "D:\battery_archive\upstream\BatteryLife" `
  -WindowStyle Hidden
```

네 도메인 전부를 한 번에 던지려면:

```powershell
Start-Process -FilePath "C:\Program Files\Git\bin\bash.exe" `
  -ArgumentList "-c","for d in CALB Na-ion Zn-ion Li-ion; do bash D:/battery_archive/.build/batterylife/run_domain.sh \$d; done" `
  -WorkingDirectory "D:\battery_archive\upstream\BatteryLife" `
  -WindowStyle Hidden
```

진행 확인:

```powershell
Get-ChildItem D:\battery_archive\runs\*_summary.txt | Sort-Object LastWriteTime | Select-Object -Last 1 | Get-Content -Wait
Get-Content D:\battery_archive\runs\<시각>_<이름>.log -Tail 20 -Wait
```

**GPU 는 한 장입니다.** 여러 도메인을 동시에 던지지 마십시오. 포트는 36개
전부 다르게(27000~27035) 넣어 두어 충돌은 나지 않지만, VRAM 을 나눠 쓰고
서로 느려집니다.

---

## 5. 중단 · 재개

### 중단

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run_main_nodeepspeed*' } |
  Select-Object ProcessId, CommandLine
Stop-Process -Id <pid>
```

`run_domain.sh` 로 돌리는 중이라면 bash 프로세스도 함께 잡아야 다음
스크립트가 뜨지 않습니다.

```powershell
Get-CimInstance Win32_Process -Filter "Name='bash.exe'" |
  Where-Object { $_.CommandLine -like '*run_domain*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId }
```

런처(`-m train.launch`)로 띄운 것은 `runs\<시각>_<이름>\pid.txt` 에 bash
래퍼의 pid 가 있습니다.

### 재개 — **없습니다**

상위 코드에 재개 기능이 없습니다. 그리고 더 나쁜 것이 있습니다.

> `run_main.py:213-215` 가 시작할 때 같은 이름의 체크포인트 폴더를
> **통째로 지웁니다** (`del_files` → `shutil.rmtree`).

폴더 이름은 `{model}_sl..._dataset{dataset}_..._bs{batch}_s{seed}-{comment}`
로 정해집니다. **`train_epochs` 는 이름에 들어가지 않습니다.** 따라서
같은 조합을 다시 돌리면 이전 결과가 사라집니다.

**36개 스크립트에 `--seed` 를 전부 명시해 둔 이유가 이것입니다.** seed 가
폴더 이름에 들어가므로 seed 3벌이 서로 덮어쓰지 않습니다. Zn-ion ·
Na-ion · CALB 는 `--dataset` 도 달라 이중으로 갈립니다.

지키고 싶으면 먼저 옮기십시오.

```powershell
Move-Item D:\battery_archive\data\checkpoints\<폴더> D:\battery_archive\data\checkpoints\<폴더>_keep
```

중간에 죽은 실행을 이어받을 방법은 없습니다. 처음부터 다시 돌려야 합니다.
**그래서 `run_domain.sh` 는 실패한 하나를 건너뛰고 계속 갑니다** — 밤새
돌린 것이 두 번째 스크립트에서 통째로 멈추는 것이 가장 나쁩니다.

---

## 6. 결과 위치

| 무엇 | 어디 |
|---|---|
| 체크포인트 | `data\checkpoints\<setting>-<comment>\model.safetensors` |
| 스케일러 | 같은 폴더의 `label_scaler` · `life_class_scaler` (joblib) |
| 실행 인자 | 같은 폴더의 `args.json` |
| 로그 | `runs\<시각>_<이름>.log` 또는 `runs\<시각>_<이름>\log.txt` |
| 도메인 요약 | `runs\<시각>_<도메인>_summary.txt` |
| 치환 내역 | `.build\batterylife\changes_36.txt` |
| 3에폭 실측 | `runs\measure36.json` |
| 지표 | **파일로 저장되지 않습니다.** 로그의 `Best model performance:` 줄 |

상위 코드는 지표를 wandb 로 보내고 stdout 에 찍을 뿐입니다
(`run_main.py:427-435`). **이 환경에서는 wandb 를 껐습니다**
(`WANDB_MODE=disabled`). 지표는 stdout 에 그대로 남으므로 §7 로 뽑습니다.

---

## 7. `train/collect.py` — 로그에서 지표 뽑기

```powershell
python -m train.collect                       # 도움말
python -m train.collect --all                 # runs/ 전부
python -m train.collect --all --out experiments\results\my_metrics.json
```

기본 출력은 `experiments\results\train_metrics.json` 입니다.

**주의 둘.**

- `MAPE` 는 비율입니다. 백분율이 아닙니다 (`utils/metrics.py:26` —
  `mean(|(pred-true)/true|)`). 논문 표와 맞출 때 100 을 곱해야 하는지
  확인하십시오. 반면 `15%-accuracy` · `10%-accuracy` 는 이미 백분율입니다.
- `run_main.py:125-126` 의 `--alpha1` · `--alpha2` **도움말 문구가 서로
  바뀌어 있습니다.** 값과 출력 라벨은 맞습니다 — `alpha1=0.15` 가
  `15%-accuracy` 로 찍힙니다. 도움말만 보고 따라가면 뒤집어 읽습니다.

---

## 8. 알려진 조건 차이 — **이 표 없이는 논문과 비교할 수 없습니다**

| 항목 | 논문 / 원본 | 이 기계 | 왜 |
|---|---|---|---|
| torch | 2.4.1 | **2.11.0+cu128** | 2.4.1 은 sm_120(Blackwell) 미지원. 5080 에서 못 씀 |
| pandas | 2.2.3 | 3.0.5 | |
| scipy | 1.15.2 | 1.17.1 | |
| scikit-learn | 1.4.2 | 1.9.0 | |
| **deepspeed** | **0.15.0 · ZeRO stage-2** | **미사용 (Windows 빌드 불가). accelerate 기본 경로** | §8-1 |
| wandb | 사용 | **`requirements` 미기재. 별도 설치 · `WANDB_MODE=disabled`** | §8-8 |
| GPU | 2장 가정 (`--multi_gpu`, `num_process=2`) | **RTX 5080 단일.** `--multi_gpu` 제거, `num_processes=1` | |
| **batch_size** | 문서값(프로세스당) × 2 GPU | **문서값 × 2 를 한 프로세스에** | §8-4 |
| num_workers | 8 (MLP·CPMLP) / 32 (CPTransformer) | **0** | Windows 는 워커마다 프로세스를 통째 복제. RAM 15.1 GiB |
| **Li-ion** | 843셀 | **841셀** (라벨 미배포 6셀 제외) | §8-5 |
| **Transformer** | Table 3 에 행 있음 | **제외 — 배포 코드가 실행 불가** | §8-6 (TRN-008) |
| **MLP** | 하이퍼파라미터 문서에 **없음** | **셸 값 사용** | §8-4 |
| 반복 3회의 정체 | 논문 §4.1 "three times" | 도메인마다 다름 | §8-7 |

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
를 만들었습니다. 원본 소스를 읽어 두 줄을 바꾸고 exec 합니다.

```
- deepspeed_plugin = DeepSpeedPlugin(hf_ds_config='./ds_config_zero2_baseline.json')
+ deepspeed_plugin = None
- Accelerator(kwargs_handlers=[ddp_kwargs], deepspeed_plugin=deepspeed_plugin, ...)
+ Accelerator(kwargs_handlers=[ddp_kwargs], ...)
```

**원본은 ZeRO stage-2 로 돕니다. 이쪽은 accelerate 기본 경로입니다.**
같은 조건이라고 말할 수 없습니다.

**진입점은 실행할 때마다 적용한 패치 목록을 로그 첫머리에 찍습니다.**

```
========================================================================
[.build 진입점] 원본이 아닙니다. 적용된 패치:
  - 1. deepspeed 우회 — ...
  - 2. MIX_large_841 분할 추가 — ...
========================================================================
```

패치가 하나라도 실패하면 **그 자리에서 멈춥니다.** 조용히 원본 조건으로
도는 것이 가장 나쁩니다.

### 8-4. 하이퍼파라미터는 문서 값입니다 — 셸 값이 아닙니다

`assets/Selected_hyperparameters.md` 가 (모델, 도메인, seed) 48행으로
**7개**를 지정합니다.

    batch_size · d_model · d_ff · e_layers · d_layers · dropout · learning_rate

36개 스크립트는 이 값을 씁니다. 셸 스크립트 값은 폐기했습니다 (옛
8개는 `.build/batterylife/_old_shellparam/` 에 남겨 두었습니다).

**배치 환산.** 문서 머리말(`:3`)이 명시합니다 — 표의 값은 **프로세스당**
값이고 GPU 2장이라 실효 배치는 2배입니다. 이 기계는 GPU 한 장이므로
**문서값 × 2** 를 한 프로세스에 줍니다. 각 스크립트 머리에 그 계산이
적혀 있습니다.

```
# batch_size = 문서값 8 × 2 (단일 GPU 환산) = 16
```

**문서가 지정하지 않는 것은 원본 셸 값 그대로입니다.**

    n_heads · lstm_layers · train_epochs · patience · early_cycle_threshold
    charge_discharge_length · seq_len · lradj · loss

이것도 각 스크립트 머리에 값과 함께 적혀 있습니다.

**`MLP` 은 문서 표에 아예 없습니다.** CyclePatch 계열 넷(CPMLP ·
CPTransformer · CPGRU · CPLSTM)만 실려 있습니다. `MLP.sh` 의 셸 값을
전부 그대로 쓰고 도메인·seed 만 바꿨습니다. 파일 머리에
`# 문서 근거 없음 — 셸 스크립트 값 사용` 이라고 적혀 있습니다.
**MLP 행을 논문 수치와 직접 비교하지 마십시오.**

### 8-5. Li-ion 은 843셀이 아니라 841셀입니다

배포 `MIX_large` 843셀 중 6셀의 라벨이 배포 `Life labels` 에 없습니다.
`eol` 이 `None` 이 되면 `data_loader.py:443` 이 값 5개를 돌려주는데
호출부(`:487`)는 6개로 언팩해 `ValueError` 로 로딩 도중 죽습니다.

| 파일 | 원래 분할 |
|---|---|
| `MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl` | train |
| `MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl` | train |
| `MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl` | train |
| `MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl` | train |
| `MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl` | train |
| `MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl` | test |

Li-ion 9개는 `--dataset MIX_large_841` 을 씁니다. 진입점이 **런타임에**
이 이름을 더합니다. `upstream/` 은 고치지 않았습니다.

```
train 515 -> 510 · val 165 -> 165 · test 163 -> 162
```

> **이름은 `MIX_large_841` 이지만 실제 셀 수는 837 입니다.**
> 843 - 6 = 837 이고 510+165+162 = 837 입니다. 이름을 바꿀지는 사람이
> 정합니다 — `docs/reports/2026-08-04_unattended.md` §8.

제외는 `MIX_large_*_files` 층에서 합니다. `MICH_EXP_*_files` 에서 빼면
`--dataset MICH_EXP` 단독 분기까지 오염됩니다 — 그쪽은 18셀 그대로입니다.
`--dataset MIX_large` 로 부르면 여전히 843 입니다. 검증:

```powershell
python -m verify.check_841              # 실제 로딩까지 (약 10분)
python -m verify.check_841 --structure  # 목록만 (수초)
```

`data_loader.py:390-393` 이 `MICH` 접두 파일을 `total_MICH/` 에서 읽고,
그 폴더가 없으면 `merge_MICH()`(`:698-711`)가 `MICH/`(40)와
`MICH_EXP/`(18)를 복사해 만듭니다. **Li-ion 첫 실행 때 한 번 생깁니다.**
사람이 만든 폴더가 아닙니다.

### 8-6. `Transformer` 는 뺐습니다 — OOM 이 아니라 실행 불가

`models/Transformer.py:71` 이 `configs.num_class` 를 읽는데 실제 인자
이름은 `--class_num` 입니다 (`run_main.py:102`). `Model(args)` 생성
시점에 `AttributeError` 로 죽습니다. 추가로 `forward` 가 위치인자 4개를
요구하는데 `run_main.py:322` 는 2개만 넘기고, 배치가 4차원인데
`DataEmbedding` 은 3차원을 가정합니다.

논문 Table 3 의 `Transformer` 행은 `-` 이고 사유는 OOM 으로 적혀
있습니다. **사유가 다릅니다.** 같은 자리에 놓을 수 없어 36회에서
제외했습니다. `MLP` · `CPMLP` · `CPTransformer` 는 셋 다 통과합니다.
(`findings` TRN-008)

### 8-7. 반복 3회의 정체가 도메인마다 다릅니다

| 도메인 | 반복 방식 | `--dataset` |
|---|---|---|
| Zn-ion | **분할이 3벌** | `ZN-coin` · `ZN-coin42` · `ZN-coin2024` |
| Na-ion | **분할이 3벌** | `NAion` · `NAion42` · `NAion2024` |
| CALB | **분할이 3벌** | `CALB` · `CALB42` · `CALB2024` |
| Li-ion | 분할이 1벌. **`--seed` 만 바뀝니다** | `MIX_large_841` 셋 다 |

`MIX_large` 에는 seed 변형 분기가 없습니다. `MIX_all` 계열(1001셀)이
`split_recorder` 에 있으나 `data_loader.py` 의 어느 분기도 참조하지 않아
도달할 수 없습니다. (`findings` TRN-009)

**36개 전부에 `--seed` 를 명시했습니다.** 분할이 3벌인 도메인도
마찬가지입니다 — 체크포인트 폴더 이름에 seed 가 들어가야 서로 덮어쓰지
않습니다 (§5).

### 8-8. wandb

`upstream/BatteryLife/requirements.txt` 에 wandb 가 **없습니다.** 그런데
`run_main.py:13` 이 import 하고 `:224` 가 `wandb.init` 을 **조건 없이**
부릅니다. 별도로 설치해야 import 가 통과하고, 로그인하지 않은 기계에서는
`WANDB_MODE=disabled` 가 없으면 거기서 멈춥니다. 36개 스크립트가 전부
그 환경변수를 export 합니다. (`findings` TRN-002)

### 8-9. 메모리 — **Li-ion 은 RAM 에서 막힙니다. VRAM 이 아닙니다**

이 기계 RAM 은 **15.1 GiB**, 커밋 한도는 **44.5 GiB**(pagefile 29.4 GiB)
입니다. `num_workers=0` 인 이유가 이것입니다 (워커마다 프로세스를 통째
복제합니다).

VRAM 은 여유가 있습니다 — 3에폭 실측(CALB · batch 16)에서 최대
**1,518 MiB** / 16,303 MiB 였습니다.

**문제는 RAM 입니다.** `data_loader.py:234` 이 데이터셋 생성 마지막에
NaN 검사를 하면서 **전체를 float64 배열 한 덩어리로** 만듭니다.

```python
if np.any(np.isnan(self.total_charge_discharge_curves)):
```

| 분할 | 배열 모양 | 크기 |
|---|---|---:|
| CALB train | (1,689, 100, 3, 300) | 1.1 GiB |
| Zn-ion train | (5,900, 100, 3, 300) | 4.0 GiB |
| Li-ion test | (15,800, 100, 3, 300) | 10.6 GiB |
| Li-ion val | (16,200, 100, 3, 300) | 10.9 GiB |
| **Li-ion train** | **(50,300, 100, 3, 300)** | **33.7 GiB** |

**같은 명령이 통과하기도 실패하기도 했습니다.** 2026-08-04 실측 두 번 —
한 번은 387.5초에 통과, 한 번은 이렇게 죽었습니다.

```
numpy.core._exceptions._ArrayMemoryError: Unable to allocate 33.7 GiB
for an array with shape (50300, 100, 3, 300) and data type float64
```

갈린 것은 **그때 남아 있던 커밋 용량**입니다. (`findings` TRN-011)

**Li-ion 9개를 돌리기 전에 할 것:**

1. 다른 프로그램을 전부 닫으십시오. 브라우저 하나가 몇 GiB 를 씁니다.
2. 커밋 여유를 확인하십시오. **34 GiB 이상** 있어야 합니다.

```powershell
$os = Get-CimInstance Win32_OperatingSystem
"커밋 여유: {0:N1} GiB / 한도 {1:N1} GiB" -f ($os.FreeVirtualMemory/1MB), ($os.TotalVirtualMemorySize/1MB)
```

3. 모자라면 pagefile 을 키우거나(시스템 속성 → 고급 → 성능 → 가상 메모리)
   Li-ion 을 뒤로 미루십시오. **CALB · Na-ion · Zn-ion 세 열은 영향이
   없습니다** (배열이 4 GiB 이하).
4. 통과하더라도 페이징 때문에 느립니다 — Li-ion train 로딩만 6분 반이고,
   val·test 는 각각 2분입니다.

**upstream 을 고치지 않았습니다.** 이 줄은 NaN 검사만 하므로 셀 단위로
나눠도 결과가 같아 보이지만, 그것은 추정이고 `upstream/` 은 읽기
전용입니다. 사람이 정할 일입니다.

**VRAM 이 모자라도 배치를 임의로 줄이지 마십시오.** 배치는 문서값 × 2
이고, 줄이면 그 시점부터 Table 3 재현이 아닙니다. OOM 이 나면 그 사실을
기록하고 사람이 정할 일입니다.

---

## 9. 스크립트를 다시 만들려면

`config.env` 를 고쳤거나 상위가 바뀌었을 때.

```powershell
python -m train.make_scripts          # 36개 + 3에폭 사본 2개 + run_domain.sh
python -m train.make_scripts --check  # 생성 없이 검증만
```

검증표는 36개 × 9항목입니다 — `checkpoints` · `root_path` 실존 ·
`CUDA_VISIBLE_DEVICES=0` · `--multi_gpu` 없음 · `--num_workers` ·
`dataset` · `--seed` · `batch_size` 가 문서값×2 인가 · 모델 이름 3곳 일치.
`master_port` 36개가 전부 다른지도 함께 봅니다.

`.build/` 는 `.gitignore` 대상입니다. 지워도 위 명령으로 복원됩니다.
**`upstream/` 은 절대 고치지 마십시오** — 치환본은 `.build/` 에만 둡니다.

시간을 다시 재려면:

```powershell
python -m train.measure               # _timing36_*.sh 둘 (3에폭)
```

`--vram-limit`(기본 15000 MiB)를 넘으면 그 자리에서 죽이고 기록합니다.
**배치는 줄이지 않습니다.**

---

## 10. 이 문서를 읽는 순서

1. **§8 조건 차이** — 무엇이 논문과 다른지. 특히 §8-4(하이퍼파라미터) ·
   §8-5(841 이라는 이름 vs 837 이라는 실제) · §8-6(Transformer 제외)
2. §1 활성화 → §2 순서 → **§3-2 로 도메인 하나씩**
3. §5 재개가 없다는 것 (다시 돌리면 이전 체크포인트가 지워집니다)
4. §7 지표 뽑기
