# CC_REPORT — 논문 재현 실행 목록 확정

작업일 2026-08-04 (2회차) · `D:\battery_archive` · `.venv-blife`

> 같은 날 1회차(학습 4종 실행 준비)의 보고서는 지시대로 덮어썼습니다.
> 그 내용은 `RUN.md` 와 `findings/registry.yaml` TRN-001~003 에 남아
> 있습니다.

**결론.** 실행 목록을 확정했습니다 — `PLAN.md`. 다만 **지금 당장 전부
돌릴 수 없습니다.** 이번 조사에서 재현을 가로막는 것 셋이 나왔습니다.

| # | 무엇 | 영향 |
|---|---|---|
| 1 | **셸 스크립트 하이퍼파라미터가 논문 문서와 거의 전부 다름** | 지금 `.build/` 8개로 돌리면 **Table 3 재현이 아님** |
| 2 | **Li-ion(`MIX_large`) 은 로딩 자체가 실패** | 4열 중 1열(9회) 전체가 막힘 |
| 3 | **`Transformer` 는 OOM 이 아니라 생성조차 안 됨** | 논문의 `-` 와 사유가 다름 |

셋 다 사람이 정할 것입니다 — §7.

**읽는 순서는 §8 에 있습니다.**

---

## 1. §1 seed 축 표 — 이번 작업의 핵심

`data_split_recorder` 의 분할 리스트를 실제로 로드해 **집합 비교**로
답했습니다. 코드를 읽은 추정이 아닙니다.

### 1-1. 세 계열은 실제로 다른 분할입니다

| 분기 | train | val | test | 셀 풀 | 기본 분기와 동일한 분할인가 | 기본과 test 겹침 | 기본과 train 겹침 |
|---|---:|---:|---:|---:|---|---:|---:|
| `CALB` | 17 | 5 | 5 | 27 | (기준) | 5/5 | 17/17 |
| `CALB42` | 17 | 5 | 5 | 27 | **아니오** | **2/5** | 11/17 |
| `CALB2024` | 17 | 5 | 5 | 27 | **아니오** | **1/5** | 9/17 |
| `ZN-coin` | 60 | 20 | 20 | 100 | (기준) | 20/20 | 60/60 |
| `ZN-coin42` | 60 | 20 | 20 | 100 | **아니오** | **6/20** | 36/60 |
| `ZN-coin2024` | 60 | 20 | 20 | 100 | **아니오** | **3/20** | 28/60 |
| `NAion` | 20 | 6 | 5 | 31 | (기준) | 5/5 | 20/20 |
| `NAion42` | 20 | 6 | 5 | 31 | **아니오** | **2/5** | 14/20 |
| `NAion2024` | 20 | 6 | 5 | 31 | **아니오** | **2/5** | 14/20 |

- **셀 풀은 셋 다 같습니다** (같은 27 / 100 / 31셀).
- **분할은 셋 다 다릅니다.** 같은 27셀을 다르게 나눈 것입니다.
- train ∩ test 누수는 9개 분기 전부 **0** 입니다.

### 1-2. 질문 6개에 대한 답

| # | 질문 | 답 |
|---|---|---|
| 1 | `CALB` 3분기의 파일 목록이 실제로 다른가 | **다릅니다.** 같은 27셀을 다르게 나눈 것 (위 표) |
| 2 | Zn · Na 계열도 동일한가 | **동일합니다.** 셋 다 풀은 같고 분할이 다름 |
| 3 | 접미사 없는 기본 분기는 seed 2021 인가 | **그렇게 읽었습니다 — 추론입니다.** 근거는 §1-3 |
| 4 | `--seed` 는 어디에 쓰이는가 | **모델 초기화·셔플 전용.** 분할에는 관여하지 않음. §1-4 |
| 5 | `MIX_large` 에 seed 변형이 있는가 | **없습니다.** 한 벌뿐. §1-5 |
| 6 | 분할 리스트는 어떻게 만들어지는가 | **전부 하드코딩된 파일명 목록.** 코드가 seed 로 나누지 않음 |

### 1-3. 기본 분기 ↔ seed 2021 (추론)

두 가지가 뒷받침합니다.

- **속성명.** Na 계열만 이름이 연도를 드러냅니다 —
  `NAion_2021_train_files` · `NAion_42_*` · `NAion_2024_*`. 즉 접미사
  없는 `--dataset NAion` 이 가리키는 것이 `_2021` 입니다.
- **문서의 seed 축.** `assets/Selected_hyperparameters.md` 가
  (모델, 도메인, **seed**) 로 행을 나누는데 그 seed 가 정확히
  **42 · 2021 · 2024** 셋입니다. 분기 접미사와 같은 집합입니다.

`CALB` · `ZNcoin` 은 이름에 연도가 없어 형제 관계로 유추했습니다.
**문서에 명시된 대응표는 찾지 못했습니다.**

### 1-4. `--seed` 의 쓰임

`run_main.py:134` 가 `set_seed(args.seed)` 를 부르고, 그것이
`accelerate.utils.set_seed` · `random.seed` · `np.random.seed` ·
`torch.manual_seed` 를 부릅니다 (`:34-38`). 데이터 로딩(`:205`)보다
먼저입니다.

분할은 seed 와 무관합니다 — `data_split_recorder.py` 의 **하드코딩된
파일명 리스트**이기 때문입니다. 따라서 seed 는 모델 초기화와
DataLoader 셔플에만 영향을 줍니다.

seed 는 체크포인트 폴더 이름에도 들어갑니다 (`run_main.py:150`
`..._bs{batch}_s{seed}`). 세 번을 돌려도 서로 덮어쓰지 않습니다.

### 1-5. `MIX_large` 에는 seed 변형이 없습니다 — 비대칭

`split_recorder` 의 속성 78개를 전수로 열거해 확인했습니다.

| 이름 | train | val | test | 합계 | `--dataset` 으로 도달 가능한가 |
|---|---:|---:|---:|---:|---|
| `MIX_large` | 515 | 165 | 163 | **843** | **가능** |
| `MIX_all` | 612 | 196 | 193 | 1001 | **불가능** |
| `MIX_all_42` | 612 | 196 | 193 | 1001 | **불가능** |
| `MIX_all_2024` | 612 | 196 | 193 | 1001 | **불가능** |

- `MIX_large` 는 **한 벌뿐**입니다. `MIX_large_42` 도 `MIX_large_2024` 도
  없습니다.
- `MIX_all` 은 1001셀 = `MIX_large` 843 + CALB 27 + ZN-coin 100 +
  NA-ion 31 입니다 (차집합 158셀을 확인).
- `MIX_all` 계열 셋은 `data_loader.py` 의 **어느 분기도 참조하지
  않습니다.** `--dataset` 으로 도달할 수 없는 죽은 정의입니다.

**따라서 "3회 반복" 의 정체가 도메인마다 다릅니다.**

| 도메인 | 반복 방식 |
|---|---|
| Zn-ion · Na-ion · CALB | `--dataset` 을 `X` · `X42` · `X2024` 로. **분할 3벌** |
| Li-ion | 분할 1벌. **`--seed` 만 2021 · 42 · 2024** (초기화·셔플만 달라짐) |

논문 §4.1 의 "we run each experiment three times" 만으로는 이 비대칭을
알 수 없습니다. `findings` TRN-009 에 기록했습니다.

---

## 2. §2 하이퍼파라미터 대조 — 거의 전부 불일치

`assets/Selected_hyperparameters.md` 는 **(모델, 도메인, seed) 48행**으로
7개 항목을 지정합니다. 모델은 CyclePatch 계열 넷(CPMLP · CPTransformer ·
CPGRU · CPLSTM), 도메인은 넷, seed 는 42 · 2021 · 2024.

### 2-1. 대조표

셸 스크립트가 실제로 지정한 (도메인, seed) 조합의 문서 행과 맞췄습니다.

| 모델 | 도메인 | seed | 항목 | 문서값 | 셸값 | 일치 |
|---|---|---:|---|---:|---:|---|
| CPMLP | CALB | 2021 | `learning_rate` | 5e-05 | 0.00005 | 일치 |
| CPMLP | CALB | 2021 | `batch_size` | 8 | 16 | **불일치** |
| CPMLP | CALB | 2021 | `d_model` | 32 | 128 | **불일치** |
| CPMLP | CALB | 2021 | `d_ff` | 32 | 256 | **불일치** |
| CPMLP | CALB | 2021 | `e_layers` | 12 | 4 | **불일치** |
| CPMLP | CALB | 2021 | `d_layers` | 6 | 2 | **불일치** |
| CPMLP | CALB | 2021 | `dropout` | 0.1 | 0 | **불일치** |
| CPTransformer | Li-ion | 2024 | `learning_rate` | 5e-05 | 0.00005 | 일치 |
| CPTransformer | Li-ion | 2024 | `dropout` | 0 | 0 | 일치 |
| CPTransformer | Li-ion | 2024 | `batch_size` | 128 | 32 | **불일치** |
| CPTransformer | Li-ion | 2024 | `d_model` | 256 | 128 | **불일치** |
| CPTransformer | Li-ion | 2024 | `d_ff` | 64 | 256 | **불일치** |
| CPTransformer | Li-ion | 2024 | `e_layers` | 1 | 6 | **불일치** |
| CPTransformer | Li-ion | 2024 | `d_layers` | 12 | 4 | **불일치** |
| **MLP** | Li-ion | 2021 | (17개 항목 전부) | — | — | **문서 없음** |

문서가 지정하지 않는 항목 (셸 값 말고 근거가 없음):
`n_heads` · `lstm_layers` · `train_epochs` · `patience` ·
`early_cycle_threshold` · `charge_discharge_length` · `seq_len` ·
`lradj` · `loss`.

### 2-2. 이것이 뜻하는 것

**셸 스크립트는 논문 최종 설정이 아닙니다.** 문서는 (모델, 도메인, seed)
별로 값을 나누는데 셸 스크립트는 조합 하나의 흔적입니다. `d_layers` 가
2 대 6, `e_layers` 가 4 대 12 처럼 **모델 규모 자체가 다릅니다.**

**따라서 1회차에서 만든 `.build/` 8개를 그대로 돌린 결과는 Table 3 과
비교할 수 없습니다.** 임의로 바꾸지 않고 보고만 합니다 (지시 §하지 말 것).

### 2-3. 배치 환산 주의

문서 머리말(`:3`)이 이렇게 적습니다.

> All results were reproduced on BatteryLife v4 with two GPUs. The
> `batch_size` values below are the per-process values passed to
> `accelerate`; the effective global batch size is therefore
> `batch_size * 2`.

단일 GPU 에서 실효 배치를 맞추려면 **문서 값의 2배**를 줘야 합니다.
예: Zn-ion CPMLP 문서 64 → 단일 GPU `batch_size=128`.

### 2-4. CALB 만 seed 별로 하이퍼파라미터가 다릅니다

곁가지 관찰. Li-ion · Zn-ion · Na-ion 은 seed 셋이 같은 값을 쓰는데
**CALB 만 seed 마다 다릅니다.**

| 모델 | CALB seed 42 | seed 2021 | seed 2024 |
|---|---|---|---|
| CPMLP | bs4 dm128 dff128 e7 d9 drop0.05 | bs8 dm32 dff32 e12 d6 drop0.1 | bs8 dm256 dff128 e12 d6 drop0 |
| CPTransformer | bs64 dm256 dff256 e6 d7 drop0.05 | bs8 dm64 dff256 e9 d9 drop0.1 | bs4 dm128 dff256 e7 d6 drop0 |

즉 CALB 는 **분할마다 따로 튜닝**했습니다. 이유는 확인하지 않았습니다.
재현할 때 seed 별로 다른 스크립트가 필요하다는 뜻입니다.

---

## 3. §3 `Transformer` 구조 관찰

**돌리지 않았습니다.** 구조만 봤고, 그 과정에서 **OOM 이전에 실행 자체가
불가능**하다는 것이 나왔습니다.

### 3-1. 실행 불가 — 세 가지

`Model(args)` 를 실제로 생성해 보고 확인했습니다 (CPU, 학습 없음).

| # | 무엇 | 위치 |
|---|---|---|
| 1 | `configs.num_class` 를 읽는데 실제 인자명은 `--class_num`. **생성 시점 `AttributeError`** | `Transformer.py:71` 대 `run_main.py:102` |
| 2 | `forward` 가 위치인자 4개(`x_enc, x_mark_enc, x_dec, x_mark_dec`)를 요구하는데 호출은 2개 | `Transformer.py:113` 대 `run_main.py:322` |
| 3 | 배치가 `[B, 100, 300, 3]` 4차원인데 `DataEmbedding` 은 3차원 가정 | `Transformer.py:22` |

같은 조건에서 나머지 셋은 전부 통과합니다.

| 모델 | 생성 | 2-인자 호출 | 파라미터 수 |
|---|---|---|---:|
| MLP | OK | OK → `(2, 1)` | 5,760,129 |
| CPMLP | OK | OK → `(2, 1)` | 667,841 |
| **Transformer** | **AttributeError** | 호출 불가 | — |
| CPTransformer | OK | OK → `(2, 1)` | 465,729 |

`configs.num_class` 를 쓰는 모델은 `Transformer.py` **하나뿐**입니다.
나머지는 `class_num` 또는 `output_num` 을 씁니다.

### 3-2. 입력 형태의 차이

로더가 내주는 배치는 `[B, early_cycle=100, charge_discharge_length=300,
num_var=3]` 입니다. 셀 하나당 **100 × 300 × 3 = 90,000 값**.

- **CPTransformer** — `intra_flatten(start_dim=2)` 로 `[B, 100, 900]` 을
  만들고 `Linear(900 → d_model)` 로 사이클 하나를 토큰 하나로 압축합니다
  (`CPTransformer.py:37-38`). 어텐션 길이는 **100**(사이클 수)입니다.
- **Transformer** — CyclePatch 가 없습니다. `DataEmbedding(enc_in=3)` 이
  `[B, L, 3]` 을 가정하므로 4차원을 그대로 받지 못합니다. 만약 시간축을
  펼쳐 넣는다면 길이가 **100 × 300 = 30,000** 이 됩니다.

### 3-3. 규모에 대한 정성적 기술

`FullAttention` 은 O(L²) 입니다 (`Transformer.py:13` 주석이 명시).
어텐션 길이가 100 대 30,000 이면 **어텐션 행렬의 원소 수가 4~5자릿수만큼
차이**납니다. 논문이 8× RTX 4090 에서도 OOM 으로 기록한 것과 방향이
맞습니다.

**수치 추정은 하지 않습니다.** 스모크에서 관측된 CPMLP/CALB 1290 MiB 는
기준점으로 쓸 수 없습니다 — 모델도 데이터셋도 어텐션 유무도 다릅니다.
그리고 애초에 §3-1 때문에 우리 환경에서는 메모리에 닿지 못합니다.

---

## 4. §4 측정값 — 로딩과 에폭을 분리

### 4-1. 계획이 바뀐 이유

지시는 `MIX_large` 로 CPMLP · CPTransformer 를 재라고 했습니다.
**CPMLP / `MIX_large` 가 로딩 도중 죽었습니다** (§4-3). 데이터 로더의
문제라 모델과 무관하므로 CPTransformer 도 같은 자리에서 죽습니다.

계획 수립에 필요한 값을 얻기 위해 **도는 도메인 중 가장 큰 `ZN-coin`
(100셀)** 으로 두 모델을 쟀습니다. 대체한 사실을 여기 적습니다.

### 4-2. 실측 (`train_epochs=3`)

| 조합 | 전체 wall | **데이터 로딩** | **학습 에폭** | 에폭 주기(평가 포함) | 최대 VRAM | 최대 RSS |
|---|---:|---:|---:|---:|---:|---:|
| CPMLP / ZN-coin | 54초 | **29초** (18+6+5) | 3.31 / 2.81 / 2.89 → **평균 3.00초** | ~8.3초 | 1430 MiB | 4215 MiB |
| CPTransformer / ZN-coin | 69초 | **25초** (16+5+4) | 9.50 / 8.23 / 7.51 → **평균 8.42초** | ~14.7초 | 1492 MiB | 4681 MiB |
| (참고) CPMLP / CALB | 12.2초 | ~2초 | 0.98초 | ~4초 | 1290 MiB | 2095 MiB |

- "데이터 로딩" 은 train/val/test 세 tqdm 막대의 합입니다.
- "학습 에폭" 은 `Epoch: N cost time` — 학습 루프만입니다.
- "에폭 주기" 는 `(wall − 로딩) / 3` 으로, 기동 시간이 얹혀 있어
  **상한**입니다. 소요 추정에는 이쪽을 씁니다.
- VRAM 은 유휴 860 MiB 를 포함한 값입니다. 실사용은 CPTransformer 가
  약 630 MiB.
- **VRAM 15 GB 를 넘지 않았습니다.** 중단 조건에 걸리지 않았습니다.

**로딩이 에폭보다 훨씬 비쌉니다.** ZN-coin 100셀에서 로딩 29초 대
에폭 3초 — 약 10배입니다. 100 에폭을 돌리면 비중이 뒤집히지만,
**짧은 실험을 여러 번 돌릴 때는 로딩이 지배합니다.**

### 4-3. `MIX_large` — 로딩 실패 (새 발견)

```
START 13:25:14 / END 13:29:36 / EXIT=1
ValueError: not enough values to unpack (expected 6, got 5)
  data_loader.py:487 ← :443
```

- `eol` 이 `None` 이면 `read_cell_df` 가 값을 **5개** 돌려주는데
  (`:443`), 호출부는 **6개**로 언팩합니다 (`:487`).
- 원인은 **라벨 누락**입니다. `MIX_large` 843셀 중 **6셀**의 라벨이
  배포 `Life labels` 에 없습니다.

| 빠진 셀 | split |
|---|---|
| `MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl` | train |
| `MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl` | train |
| `MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl` | train |
| `MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl` | train |
| `MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl` | train |
| `MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl` | test |

**여섯 전부 SOC 창이 `50-100` 인 `MICH_EXP` 셀입니다.** 배포
`MICH_EXP` 는 pkl 18개인데 `MICH_EXP_labels.json` 은 키가 12개이고,
`total_MICH_labels.json` 은 52개(MICH 40 + MICH_EXP 12)입니다. 즉
**pkl 만 배포되고 라벨이 없습니다.**

CALB · ZN-coin · NAion 은 라벨 누락이 **0** 이라 영향받지 않습니다.

**부분 실측 하나.** 죽기 전까지 train **490/515 셀을 4분 13초**에
읽었습니다 → **1.94 셀/초**. 843셀 전체면 약 7분입니다 (투영).

### 4-4. 이 측정값의 한계

**측정에 쓴 하이퍼파라미터는 셸 값이지 문서 값이 아닙니다** (§2).
Zn-ion CPMLP 만 봐도 `d_layers` 가 2(셸) 대 9(문서)입니다. **문서 값으로
바꾸면 위 시간표는 다시 재야 합니다.** 규모 감각용이지 확정이 아닙니다.

---

## 5. §5 `PLAN.md` 요약

### 총 몇 회인가

```
모델 3종 × 도메인 4종 × 반복 3회 = 36회      (Transformer 제외 — 논문과 동일)
모델 4종 × 도메인 4종 × 반복 3회 = 48회      (Transformer 포함 — 권장하지 않음)
```

**지금 실행 가능한 것은 27회** 입니다. Li-ion 9회는 §4-3 으로 막혀 있습니다.

### 예상 총 소요

| 단계 | 내용 | 회수 | 누적 | 완결되는 것 |
|---|---|---:|---|---|
| A | CALB 9회 | 9 | ~55분 | **Table 3 CALB 열** |
| B | Na-ion 9회 | 9 | ~2시간 | **Na-ion 열** |
| C | Zn-ion 9회 | 9 | **~4시간 40분** | **Zn-ion 열** |
| D | Li-ion 9회 | 9 | +22시간 (투영) | Li-ion 열 — 막힘 |

**A~C 27회 ≈ 4시간 40분에 Table 3 의 4열 중 3열이 완결됩니다.**
전체 36회는 27시간 안팎입니다 (Li-ion 은 투영값).

### 우선순위 규칙

조건을 줄이지 않고 순서만 정했습니다.

1. 조건(도메인 · seed · 에폭)을 깎지 않는다
2. **열을 완결시킨다** — 여러 열을 조금씩 채우면 어느 것도 보고 못 함
3. 작은 도메인부터 (CALB 27 → Na 31 → Zn 100 → Li 843)
4. 도메인 안에서는 CPMLP → MLP → CPTransformer (CyclePatch 대조 우선)

### 병렬 실행

**VRAM 은 여유가 크지만 RAM 이 병목입니다.** CPTransformer/ZN-coin 하나가
RSS 4.7 GB 를 씁니다 — 16 GB 에서 **동시 2개가 한계**입니다.
Li-ion 은 RSS 를 못 쟀으므로 단독 실행을 권합니다. `master_port` 는 이미
조합마다 다릅니다.

### 결과 수집

```
runs/<시각>_<모델>_<도메인>_<dataset인자>_s<seed>/log.txt
experiments/results/table3/<모델>_<도메인>_s<seed>.json
```

`table3/` 하위에 둬서 기존 라벨 검증 산출물을 덮어쓰지 않습니다.
`PLAN.md` §7-3 에 Table 3 대조표 빈 틀을 만들어 두었습니다 —
**"조건 차이" 열을 비워 두지 마십시오.**

---

## 6. 실패하거나 중단한 것

| 무엇 | 결과 |
|---|---|
| CPMLP / `MIX_large` 3에폭 측정 | **실패.** 로딩 중 `ValueError` (§4-3). 4분 22초 만에 종료. 20분 제한에는 걸리지 않음 |
| CPTransformer / `MIX_large` 3에폭 측정 | **실행하지 않음.** 데이터 로더 결함이라 같은 자리에서 죽습니다. 재현해도 새 정보가 없어 `ZN-coin` 으로 대체 (§4-1) |
| `Transformer` VRAM 규모 추정 | **하지 않음.** 지시대로 정성 기술만. 게다가 생성 자체가 불가 (§3-1) |

측정하지 않은 것:

- `MLP` 의 에폭 시간 (CPMLP · CPTransformer 만 쟀습니다)
- `MIX_large` 의 에폭 시간 · 최대 RSS (로딩에서 죽어 도달 못 함)
- 문서 하이퍼파라미터로 돌렸을 때의 시간 (§4-4)
- 동시 2개 실행의 실제 간섭 (RSS 합산으로만 판단)

### `findings/registry.yaml`

**10개 레코드를 추가했습니다** (TRN-001~010). 지시된 7개에 세 개를
더했습니다 — 이번 조사에서 새로 나온 것입니다.

| id | 내용 | 유도된 판정 |
|---|---|---|
| TRN-001 | deepspeed 가 조건 없이 필수인데 Windows 설치 불가 | 미정 |
| TRN-002 | wandb 가 무조건 import 되는데 어느 requirements 에도 없음 | 미정 |
| TRN-003 | `Transformer.sh` 부재 | 미정 |
| TRN-004 | `SDU` · `Stanford_2` 가 어느 분기에서도 참조되지 않음 | 미정 |
| TRN-005 | 인자명 `NAion` 대 디렉터리명 `NA-ion` | 미정 |
| TRN-006 | `UL_PUR` 단독 분기의 val · test 가 빔 | 미정 |
| TRN-007 | 셸 하이퍼파라미터가 문서와 불일치 (§2) | 미정 |
| **TRN-008** | **`Transformer` 가 생성조차 불가** (§3-1) | 미정 |
| **TRN-009** | **`MIX_large` 에 seed 변형 분기가 없음** (§1-5) | **불일치** |
| **TRN-010** | **`MIX_large` 로딩 실패 — 라벨 6개 누락** (§4-3) | 미정 |

`verdict` 는 쓰지 않았습니다 — `render.py` 가 슬롯에서 유도합니다.
`python run.py claims` 재생성 결과 **레코드 42개, 기록 요건 위반 0**.

대부분 `미정` 인 것은 **논문 슬롯이 `미조사`** 이기 때문입니다. 스키마
규칙상 논문을 보기 전에는 "코드 전용" 이라 말할 수 없습니다. 논문을
읽고 `paper` 슬롯을 채우면 판정이 바뀝니다.

---

## 7. 사람이 정할 것

### 7-1. 하이퍼파라미터를 어느 쪽으로 맞출 것인가 [가장 중요]

- **문서 값** — Table 3 재현이라면 이쪽. `.build/` 를 (모델 × 도메인 ×
  seed) 별로 다시 만들어야 합니다. 36개 스크립트가 됩니다.
  `train/make_scripts.py` 를 확장하면 됩니다.
- **셸 값** — 지금 그대로. 빠르지만 **Table 3 재현이 아닙니다.**

**하위 결정 둘.**

- 단일 GPU 배치 환산 — 문서 값의 2배를 줄 것인가 (§2-3)
- `MLP` 9회의 근거 — 문서에 없습니다. 셸 값을 쓰되 "문서 근거 없음" 으로
  표시하는 것 말고 다른 선택이 없어 보입니다

### 7-2. Li-ion 을 어떻게 할 것인가

| 갈래 | 결과 | 대가 |
|---|---|---|
| 6셀을 분할에서 뺀다 | 841셀 (train 510 / test 162) | 논문 843셀과 다름 |
| 라벨을 우리가 만든다 | 843셀 유지 | 배포 라벨이 아님. 라벨 생성 규칙 재현이 선행 |
| Li-ion 을 포기한다 | 3열만 보고 | Table 3 의 주 열이 빠짐 |

**임의로 고르지 않았습니다.** `LAB-015` 의 "우리만있음 33셀" 과 같은
방향의 현상인지도 확인하지 않았습니다.

### 7-3. `Transformer` 를 포함할 것인가

**제외를 권합니다** (3종 × 4도메인 × 3회 = 36회). 포함하려면
`num_class` · `forward` 시그니처 · 입력 차원 셋을 다 고쳐야 하는데
그것은 재현이 아니라 이식이고, 고치는 순간 논문과 같은 조건이 아닙니다.

다만 **"논문의 `-` 는 OOM 이 아니라 실행 불가였다"** 는 관찰 자체가
보고 가치가 있습니다. TRN-008 에 기록해 두었습니다. 논문 캡션과 배포
코드가 어긋나는 것이므로 `paper` 슬롯을 채우면 판정이 설 것입니다.

### 7-4. 순서를 지킬 것인가

`PLAN.md` §2 는 작은 도메인부터 열을 완결시키는 순서입니다. Zn-ion 을
먼저 보고 싶다면 순서가 달라집니다. **다만 어느 경우든 조건을 줄이지
않는 것이 원칙입니다.**

---

## 8. 읽는 순서

1. **§2 하이퍼파라미터 대조** — 지금 `.build/` 로 돌리면 재현이 아닙니다. 여기부터
2. **§4-3 `MIX_large` 로딩 실패** — Li-ion 열이 통째로 막혀 있습니다
3. **§1 seed 축 표** — 반복 3회의 정체. 도메인마다 다릅니다
4. **§3-1 `Transformer` 실행 불가** — 논문의 `-` 와 사유가 다릅니다
5. **§7 사람이 정할 것** — 셋 다 정해야 실행에 들어갈 수 있습니다
6. `PLAN.md` — 실행 행렬 36행과 우선순위
7. §4-2 측정값 — 소요 추정의 근거
8. `RUN.md` §8 — 갱신된 조건 차이표

---

## 9. 바뀐 파일

| 파일 | 무엇 |
|---|---|
| `PLAN.md` | **신규.** 실행 행렬 36행 · 우선순위 · 선결 과제 · Table 3 대조표 틀 |
| `CC_REPORT.md` | 이 문서 (덮어씀) |
| `RUN.md` | §8 조건 차이표에 4행 추가 + §8-4~8-7 신설 |
| `findings/registry.yaml` | TRN-001~010 추가 (32 → 42 레코드) |
| `findings/PAPER_CODE_MAP.md` | `run.py claims` 재생성 |
| `docs/OPEN_QUESTIONS.md` | `run.py claims` 재생성 |
| `train/make_scripts.py` | 측정용 사본 4개 생성 기능 추가 (`_timing_*`) |
| `.build/batterylife/` | `_timing_{CPMLP,CPTransformer}_{MIX_large,ZN-coin}.sh` 4개 추가 (gitignore) |
| `runs/` | 측정 로그 3개 (gitignore) |

**학습은 돌리지 않았습니다.** `train_epochs=3` 측정 3회뿐입니다.
`upstream/` · `notebooks/` · `experiments/results/` 는 건드리지
않았습니다. torch 변동 없습니다 (2.11.0+cu128).
