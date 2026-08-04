# PLAN.md — 논문 Table 3 재현 실행 목록

작성 2026-08-04 · 근거는 `CC_REPORT.md` §1~§4 · 미해결 항목은 `findings/registry.yaml` TRN-001~010

> **원칙.** 시간이 모자라면 **조건을 줄이지 않고 순서를 정합니다.**
> 논문 조건을 바꾸어 완주하는 것보다, 논문 조건 그대로 일부만 완료하는
> 편이 낫습니다. 조건을 바꾼 결과는 논문과 비교할 수 없어 숫자가 있어도
> 쓸모가 없습니다.

---

## 0. 먼저 알아야 할 세 가지

이 계획은 **지금 당장 전부 실행할 수 없습니다.** 세 가지가 선결입니다.

| # | 무엇 | 영향 | 근거 |
|---|---|---|---|
| 1 | **Li-ion(`MIX_large`) 은 로딩 자체가 실패한다** | 4열 중 1열 전체가 막힘 | TRN-010. 실측 재현 |
| 2 | **셸 스크립트 하이퍼파라미터가 논문 문서와 다르다** | 지금 `.build/` 8개로 돌리면 Table 3 재현이 아님 | TRN-007 |
| 3 | **`Transformer` 는 생성조차 되지 않는다** | OOM 이 아니라 `AttributeError` | TRN-008 |

**2번을 해결하기 전에는 어떤 실행도 Table 3 재현이 아닙니다.** 순서상
§4 의 결정이 먼저입니다.

---

## 1. 실행 행렬

### 1-1. seed 축 — 도메인마다 정체가 다릅니다

논문 §4.1 은 "three times" 라고만 적습니다. 코드에서는 이렇게 갈립니다.

| 도메인 | 반복 1 | 반복 2 | 반복 3 | 반복의 정체 |
|---|---|---|---|---|
| **Li-ion** | `--dataset MIX_large --seed 2021` | `--dataset MIX_large --seed 42` | `--dataset MIX_large --seed 2024` | **분할 1벌.** 모델 초기화·셔플만 다름 |
| **Zn-ion** | `--dataset ZN-coin --seed 2021` | `--dataset ZN-coin42 --seed 42` | `--dataset ZN-coin2024 --seed 2024` | **분할 3벌** |
| **Na-ion** | `--dataset NAion --seed 2021` | `--dataset NAion42 --seed 42` | `--dataset NAion2024 --seed 2024` | **분할 3벌** |
| **CALB** | `--dataset CALB --seed 2021` | `--dataset CALB42 --seed 42` | `--dataset CALB2024 --seed 2024` | **분할 3벌** |

접미사 없는 기본 분기를 seed 2021 에 대응시킨 근거는 `split_recorder` 의
속성명입니다 — Na 계열만 이름이 `NAion_2021_*` 로 연도를 드러냅니다.
`CALB` · `ZNcoin` 은 이름에 연도가 없지만 형제가 `_42` · `_2024` 이므로
같은 규칙으로 읽었습니다. **추론이며 문서 근거는 찾지 못했습니다.**

`--seed` 는 `run_main.py:134` 에서 `accelerate.utils.set_seed` ·
`np.random.seed` · `torch.manual_seed` 를 부릅니다. 분할에는 관여하지
않습니다 — 분할은 `data_split_recorder.py` 에 **하드코딩된 목록**입니다.
seed 는 체크포인트 폴더 이름에도 들어가므로 (`run_main.py:150`) 세 번을
돌려도 서로 덮어쓰지 않습니다.

### 1-2. 조합 수

```
모델 3종 × 도메인 4종 × 반복 3회 = 36회        (Transformer 제외 — 논문과 동일)
모델 4종 × 도메인 4종 × 반복 3회 = 48회        (Transformer 포함 — §5 참조)
```

이 중 **지금 실행 가능한 것은 27회** 입니다 (Li-ion 9회는 TRN-010 으로 막힘).

### 1-3. 전체 목록 — 36행

우선순위는 §2 규칙으로 매겼습니다. 소요는 §3 근거입니다.
`상태` 열의 `막힘` 은 선결 과제가 있는 것입니다.

| # | 모델 | 도메인 | `--dataset` | `--seed` | 예상 소요 | 상태 |
|---:|---|---|---|---:|---|---|
| 1 | CPMLP | CALB | `CALB` | 2021 | ~5분 | 실행가능 |
| 2 | CPMLP | CALB | `CALB42` | 42 | ~5분 | 실행가능 |
| 3 | CPMLP | CALB | `CALB2024` | 2024 | ~5분 | 실행가능 |
| 4 | MLP | CALB | `CALB` | 2021 | ~5분 | 실행가능 · **HP 근거 없음** |
| 5 | MLP | CALB | `CALB42` | 42 | ~5분 | 실행가능 · **HP 근거 없음** |
| 6 | MLP | CALB | `CALB2024` | 2024 | ~5분 | 실행가능 · **HP 근거 없음** |
| 7 | CPTransformer | CALB | `CALB` | 2021 | ~8분 | 실행가능 |
| 8 | CPTransformer | CALB | `CALB42` | 42 | ~8분 | 실행가능 |
| 9 | CPTransformer | CALB | `CALB2024` | 2024 | ~8분 | 실행가능 |
| 10 | CPMLP | Na-ion | `NAion` | 2021 | ~6분 | 실행가능 |
| 11 | CPMLP | Na-ion | `NAion42` | 42 | ~6분 | 실행가능 |
| 12 | CPMLP | Na-ion | `NAion2024` | 2024 | ~6분 | 실행가능 |
| 13 | MLP | Na-ion | `NAion` | 2021 | ~6분 | 실행가능 · **HP 근거 없음** |
| 14 | MLP | Na-ion | `NAion42` | 42 | ~6분 | 실행가능 · **HP 근거 없음** |
| 15 | MLP | Na-ion | `NAion2024` | 2024 | ~6분 | 실행가능 · **HP 근거 없음** |
| 16 | CPTransformer | Na-ion | `NAion` | 2021 | ~9분 | 실행가능 |
| 17 | CPTransformer | Na-ion | `NAion42` | 42 | ~9분 | 실행가능 |
| 18 | CPTransformer | Na-ion | `NAion2024` | 2024 | ~9분 | 실행가능 |
| 19 | CPMLP | Zn-ion | `ZN-coin` | 2021 | **~14분** | 실행가능 · 측정치 |
| 20 | CPMLP | Zn-ion | `ZN-coin42` | 42 | ~14분 | 실행가능 |
| 21 | CPMLP | Zn-ion | `ZN-coin2024` | 2024 | ~14분 | 실행가능 |
| 22 | MLP | Zn-ion | `ZN-coin` | 2021 | ~14분 | 실행가능 · **HP 근거 없음** |
| 23 | MLP | Zn-ion | `ZN-coin42` | 42 | ~14분 | 실행가능 · **HP 근거 없음** |
| 24 | MLP | Zn-ion | `ZN-coin2024` | 2024 | ~14분 | 실행가능 · **HP 근거 없음** |
| 25 | CPTransformer | Zn-ion | `ZN-coin` | 2021 | **~25분** | 실행가능 · 측정치 |
| 26 | CPTransformer | Zn-ion | `ZN-coin42` | 42 | ~25분 | 실행가능 |
| 27 | CPTransformer | Zn-ion | `ZN-coin2024` | 2024 | ~25분 | 실행가능 |
| 28 | CPMLP | Li-ion | `MIX_large` | 2021 | ~2시간 (투영) | **막힘 — TRN-010** |
| 29 | CPMLP | Li-ion | `MIX_large` | 42 | ~2시간 (투영) | **막힘** |
| 30 | CPMLP | Li-ion | `MIX_large` | 2024 | ~2시간 (투영) | **막힘** |
| 31 | MLP | Li-ion | `MIX_large` | 2021 | ~2시간 (투영) | **막힘** · HP 근거 없음 |
| 32 | MLP | Li-ion | `MIX_large` | 42 | ~2시간 (투영) | **막힘** · HP 근거 없음 |
| 33 | MLP | Li-ion | `MIX_large` | 2024 | ~2시간 (투영) | **막힘** · HP 근거 없음 |
| 34 | CPTransformer | Li-ion | `MIX_large` | 2021 | ~3.5시간 (투영) | **막힘** |
| 35 | CPTransformer | Li-ion | `MIX_large` | 42 | ~3.5시간 (투영) | **막힘** |
| 36 | CPTransformer | Li-ion | `MIX_large` | 2024 | ~3.5시간 (투영) | **막힘** |

**합계.** 실행 가능한 27회 ≈ **4시간 40분**. Li-ion 9회를 더하면
**+22시간 (투영)** 이라 총 27시간 안팎입니다.

**"HP 근거 없음"** — `MLP` 은 `Selected_hyperparameters.md` 에 없습니다
(TRN-007). 셸 `MLP.sh` 값 말고는 근거가 없고, 그 값이 논문 설정이라는
보장이 없습니다. **9회(4·5·6·13·14·15·22·23·24)가 여기 해당합니다.**

---

## 2. 우선순위 규칙

### 규칙

1. **조건을 줄이지 않는다.** 도메인·seed·에폭 수를 깎아 개수를 맞추지
   않습니다. 깎은 결과는 Table 3 과 나란히 놓을 수 없습니다.
2. **열을 완결시킨다.** 한 도메인의 3모델 × 3seed 9회를 끝내면 Table 3 의
   한 열을 통째로 채울 수 있습니다. 여러 열을 조금씩 채우면 어느 것도
   보고할 수 없습니다.
3. **작은 도메인부터.** 같은 시간에 완결되는 열이 더 많습니다.
4. **같은 도메인 안에서는 CPMLP → MLP → CPTransformer.** CyclePatch 대조
   (CPMLP 대 MLP) 가 먼저 서야 그 열의 핵심 주장이 확인됩니다.

### 순서

| 단계 | 내용 | 회수 | 누적 시간 | 완결되는 것 |
|---|---|---:|---|---|
| **A** | CALB 9회 (#1~9) | 9 | ~55분 | **Table 3 CALB 열 완성** |
| **B** | Na-ion 9회 (#10~18) | 9 | ~2시간 | **Na-ion 열 완성** |
| **C** | Zn-ion 9회 (#19~27) | 9 | ~4시간 40분 | **Zn-ion 열 완성** |
| **D** | Li-ion 9회 (#28~36) | 9 | +22시간 | Li-ion 열 — **선결 과제 있음** |

A→B→C 만으로 **Table 3 의 4열 중 3열이 완결**됩니다. 여기서 멈춰도
보고할 것이 있습니다. D 는 TRN-010 이 풀린 뒤입니다.

---

## 3. 소요 시간의 근거

### 3-1. 실측값 (2026-08-04, `train_epochs=3`)

| 조합 | 데이터 로딩 | 학습 에폭 | 에폭 주기 (평가 포함) | 최대 VRAM | 최대 RSS |
|---|---:|---:|---:|---:|---:|
| CPMLP / ZN-coin (100셀) | **29초** | 3.00초 | ~8.3초 | 1430 MiB | 4215 MiB |
| CPTransformer / ZN-coin | **25초** | 8.42초 | ~14.7초 | 1492 MiB | 4681 MiB |
| CPMLP / CALB (27셀) | ~2초 | 0.98초 | ~4초 | 1290 MiB | 2095 MiB |

- "학습 에폭" 은 로그의 `Epoch: N cost time` 입니다 (학습 루프만).
- "에폭 주기" 는 `(전체 wall − 로딩) / 3` 입니다. 기동 시간이 에폭에
  얹혀 있어 **상한**입니다. 소요 추정에는 이쪽을 씁니다.
- 로딩은 train/val/test 세 막대의 합입니다 (ZN-coin: 18+6+5초).

### 3-2. 100 에폭 환산

`train_epochs=100` · `patience=5` · `least_epochs=5` 이므로 최대 100
에폭입니다. **조기종료가 걸리면 짧아집니다** — 아래는 상한입니다.

```
CPMLP / Zn-ion         29초 + 100 × 8.3초  ≈ 14분
CPTransformer / Zn-ion 25초 + 100 × 14.7초 ≈ 25분
```

CALB · Na-ion 은 train 셀 수 비율(17/60, 20/60)로 환산했습니다.
**측정하지 않은 투영값입니다.**

### 3-3. Li-ion 투영 — 측정 아님

로딩은 부분 실측이 있습니다. 죽기 전까지 **train 490/515 셀을 4분 13초**
에 읽었습니다 (1.94 셀/초). 843셀 전체면 **약 7분** 입니다.

에폭은 train 셀 수 비율(515/60 = 8.6배)로 환산했습니다.

```
CPMLP / Li-ion         7분 + 100 × 71초  ≈ 2시간
CPTransformer / Li-ion 7분 + 100 × 126초 ≈ 3.5시간
```

**셀당 사이클 수가 도메인마다 다르므로 셀 수 비례는 거친 가정입니다.**
Li-ion 이 실제로 풀리면 다시 재십시오.

### 3-4. 이 측정값의 한계 — 중요

**측정에 쓴 하이퍼파라미터는 셸 스크립트 값이지 논문 문서 값이
아닙니다** (TRN-007). 예를 들어 Zn-ion CPMLP 는

| 항목 | 측정에 쓴 값 (셸) | 논문 문서 값 |
|---|---:|---:|
| `batch_size` | 16 | 64 |
| `d_model` | 128 | 64 |
| `d_ff` | 256 | 64 |
| `e_layers` | 4 | 5 |
| `d_layers` | 2 | 9 |

`d_layers` 가 2 대 9 입니다. **문서 값으로 바꾸면 위 시간표는 다시
재야 합니다.** 위 숫자는 규모 감각을 잡기 위한 것이지 확정이 아닙니다.

---

## 4. 선결 과제 — 실행 전에 정할 것

### 4-1. 하이퍼파라미터를 어느 쪽으로 맞출 것인가 [가장 중요]

`assets/Selected_hyperparameters.md` 는 (모델, 도메인, seed) 48행으로
`batch_size` · `d_model` · `d_ff` · `e_layers` · `d_layers` · `dropout` ·
`learning_rate` 를 지정합니다. **셸 스크립트 값과 거의 전부 다릅니다.**

두 갈래입니다.

- **문서 값으로 맞춘다** — Table 3 재현을 하려면 이쪽입니다. `.build/`
  스크립트를 (모델 × 도메인 × seed) 별로 다시 만들어야 합니다.
  `train/make_scripts.py` 를 확장하면 됩니다. **문서에 없는 항목**
  (`n_heads` · `lstm_layers` · `train_epochs` · `patience` ·
  `early_cycle_threshold` · `charge_discharge_length` · `seq_len` ·
  `lradj` · `loss`) 은 셸 값을 그대로 씁니다 — 다른 근거가 없습니다.
- **셸 값을 쓴다** — 지금 `.build/` 그대로. 빠르지만 **Table 3 재현이
  아닙니다.** 저자가 마지막에 실행한 조합 하나의 흔적입니다.

**배치 환산 주의.** 문서 머리말은 값이 2 GPU 기준이고 `batch_size` 는
프로세스당 값이라 실효 배치가 2배라고 적습니다
(`Selected_hyperparameters.md:3`). 단일 GPU 에서 실효 배치를 맞추려면
문서 값의 **2배**를 줘야 합니다. 예: Zn-ion CPMLP 문서 64 → 실효 128 →
단일 GPU 에서 `batch_size=128`. VRAM 여유(측정 1.5 GB / 16 GB)를 보면
가능해 보이나 확인하지 않았습니다.

**`MLP` 은 문서에 없습니다.** 9회분(#4·5·6·13·14·15·22·23·24)의 근거를
어디서 가져올지 정해야 합니다. 셸 `MLP.sh` 값을 쓰되 "문서 근거 없음"
으로 표시하는 것이 지금으로선 유일한 선택입니다.

### 4-2. Li-ion 을 어떻게 할 것인가

`MIX_large` 843셀 중 6셀(`MICH_13R` · `14C` · `15H` · `16R` · `17C` ·
`18H`, 전부 SOC 창 50-100)의 라벨이 배포 `Life labels` 에 없습니다.
`data_loader.py:443` 이 그때 값 5개를 돌려주는데 호출부(`:487`)는 6개로
언팩해 `ValueError` 로 죽습니다.

갈래 셋. **어느 쪽도 논문과 완전히 같지 않습니다.**

| 갈래 | 결과 | 대가 |
|---|---|---|
| 6셀을 분할에서 뺀다 | 841셀로 실행 (train 510 / test 162) | 논문 843셀과 다름 |
| 라벨을 우리가 만든다 | 843셀 유지 | 배포 라벨이 아님. 라벨 생성 규칙 재현이 선행 |
| 상위 결함으로 두고 Li-ion 을 포기 | 3열만 보고 | Table 3 의 주 열이 빠짐 |

**임의로 고르지 않았습니다.** 사람이 정하십시오.

### 4-3. `Transformer` 를 포함할 것인가 — §5

---

## 5. `Transformer` 처리 — 두 갈래

논문 Table 3 은 `Transformer` 를 네 도메인 전부 `-` 로 적고, 캡션에서
`-` 를 out of memory 로 설명합니다.

**그러나 배포 코드에서는 메모리에 닿기 전에 죽습니다** (TRN-008).

```
models/Transformer.py:71   configs.num_class     ← 인자 이름이 없음
run_main.py:102            --class_num           ← 실제 인자 이름
→ Model(args) 생성 시점에 AttributeError. 2026-08-04 실측
```

추가로 `forward` 가 위치인자 4개를 요구하는데 `run_main.py:322` 는 2개만
넘기고, 배치가 `[B, 100, 300, 3]` 4차원인데 `DataEmbedding` 은 3차원을
가정합니다. 같은 조건에서 `MLP` · `CPMLP` · `CPTransformer` 는 셋 다
생성과 호출이 통과합니다.

| 갈래 | 실행 목록 | 뜻 |
|---|---|---|
| **제외** | 3종 × 4도메인 × 3회 = **36회** | 논문과 같은 결과(`-`). 다만 사유가 OOM 이 아니라 코드 결함이라는 것을 기록 |
| **포함** | 4종 × 4도메인 × 3회 = **48회** | OOM 재현 여부 자체를 검증 항목으로 삼음. **상위 코드를 고쳐야 하고, 고치는 순간 논문과 같은 조건이 아님** |

**권장은 "제외"입니다.** 포함하려면 `num_class` · `forward` 시그니처 ·
입력 차원 셋을 다 고쳐야 하는데, 그것은 재현이 아니라 이식입니다.
다만 **"논문의 `-` 는 OOM 이 아니라 실행 불가였다"** 는 관찰 자체가
보고 가치가 있습니다 — `findings` TRN-008 에 기록해 두었습니다.

현재 `.build/batterylife/Transformer_{CALB,MIX_large}.sh` 2개는
**돌리면 즉시 실패합니다.** 남겨 두되 실행 목록에서는 뺐습니다.

---

## 6. 병렬 실행 가능 여부

**VRAM 기준으로는 가능합니다. RAM 기준으로는 2개가 한계입니다.**

| 자원 | 측정 | 16 GB / 16.3 GB 대비 |
|---|---|---|
| VRAM (CPTransformer / ZN-coin) | 1492 MiB (유휴 860 포함) | 실사용 ~630 MiB. **여유 큼** |
| RAM (같은 실행) | python.exe 4681 MiB | **2개면 9.4 GB.** 16 GB 에서 위험 |

- `master_port` 는 이미 조합마다 다르게 설정되어 있어 충돌하지 않습니다.
- **RAM 이 병목입니다.** 데이터셋을 통째로 메모리에 올리는 구조라
  (`data_loader.read_data` 가 전 셀을 배열로 쌓음) 셀 수에 비례합니다.
- **동시 2개까지**를 권장합니다. Li-ion 은 RSS 를 재지 못했으므로
  (로딩 중 3031 MiB 에서 죽음) **Li-ion 은 단독 실행**하십시오.
- `NUM_WORKERS=0` 이므로 워커 복제로 인한 추가 RAM 은 없습니다. 올리면
  이 계산이 달라집니다.

동시 2개로 돌리면 §2 의 A~C 27회가 이론상 절반(~2시간 20분)이지만,
GPU 를 나눠 쓰므로 그대로 반이 되지는 않습니다.

---

## 7. 결과 수집

### 7-1. 파일명 규칙

체크포인트 폴더는 상위가 정합니다 (`run_main.py:140-150`) — `setting` 에
`dataset` 과 `seed` 가 이미 들어갑니다. 우리가 정할 것은 **run 디렉터리와
지표 JSON** 입니다.

```
runs/<YYYYMMDD-HHMMSS>_<모델>_<도메인>_<dataset인자>_s<seed>/
    log.txt
    pid.txt

experiments/results/table3/<모델>_<도메인>_s<seed>.json
```

예:

```
runs/20260804-140312_CPMLP_CALB_CALB42_s42/log.txt
experiments/results/table3/CPMLP_CALB_s42.json
```

**`experiments/results/` 의 기존 라벨 검증 산출물(`nb0*.json` ·
`LABEL_REPORT.md` 등)을 덮어쓰지 않도록 `table3/` 하위에 둡니다.**

### 7-2. 지표 뽑기

```powershell
python -m train.collect <run 디렉터리 이름> --out experiments\results\table3\<모델>_<도메인>_s<seed>.json
python -m train.collect --all --out experiments\results\table3\_all.json
```

`collect.py` 는 로그의 `Best model performance:` 줄에서 16개 지표를
뽑습니다. 주의 둘 — `MAPE` 는 **비율**입니다(백분율 아님).
`15%-accuracy` 는 `alpha1=0.15` 이며 `run_main.py:125-126` 의 도움말
문구가 값과 어긋나 있으니 따라가지 마십시오.

### 7-3. Table 3 대조표 — 빈 틀

세 번의 평균±표준편차를 넣습니다. 논문 값은 MAPE 입니다.

| 모델 | 도메인 | 논문 MAPE | 재현 MAPE (평균±표준편차) | seed 2021 | seed 42 | seed 2024 | 조건 차이 |
|---|---|---|---|---|---|---|---|
| MLP | Li-ion | 0.233±0.010 | | | | | HP 근거 없음 · TRN-010 |
| MLP | Zn-ion | 0.805±0.103 | | | | | HP 근거 없음 |
| MLP | Na-ion | 0.281±0.067 | | | | | HP 근거 없음 |
| MLP | CALB | 0.149±0.014 | | | | | HP 근거 없음 |
| CPMLP | Li-ion | 0.179±0.003 | | | | | TRN-010 |
| CPMLP | Zn-ion | 0.558±0.034 | | | | | |
| CPMLP | Na-ion | 0.274±0.026 | | | | | |
| CPMLP | CALB | 0.140±0.009 | | | | | |
| Transformer | Li-ion | — (OOM) | | | | | TRN-008 · 실행불가 |
| Transformer | Zn-ion | — (OOM) | | | | | TRN-008 |
| Transformer | Na-ion | — (OOM) | | | | | TRN-008 |
| Transformer | CALB | — (OOM) | | | | | TRN-008 |
| CPTransformer | Li-ion | 0.184±0.003 | | | | | TRN-010 |
| CPTransformer | Zn-ion | 0.515±0.067 | | | | | |
| CPTransformer | Na-ion | 0.255±0.036 | | | | | |
| CPTransformer | CALB | 0.149±0.005 | | | | | |

**"조건 차이" 열을 비워 두지 마십시오.** 비어 있으면 논문과 같은
조건에서 얻은 값이라는 뜻이 됩니다. 최소한 모든 행에 `RUN.md` §8 의
공통 차이(deepspeed 없음 · 단일 GPU · num_workers 0)가 걸립니다.

---

## 8. 이 계획을 실행하기 전에

1. §4-1 하이퍼파라미터 — **문서 값인가 셸 값인가**
2. §4-2 Li-ion — 6셀을 빼는가, 라벨을 만드는가, 포기하는가
3. §5 `Transformer` — 제외인가 포함인가
4. `RUN.md` §8 조건 차이표에 이번에 확인된 것 반영 (이미 갱신했습니다)

셋 다 정해지기 전에 27회를 돌리면, 돌린 뒤에 다시 돌려야 합니다.
