# BatteryLife 도메인 판별력 검증 리포트

> 이 파일의 이전 내용(Li-ion 일시적 SOH 교차 조사, 2026-08-06)은 git 에 커밋되어
> 있지 않아 덮어쓰기 전에 `docs/reports/2026-08-06_li_ion_temporary_crossing.md`
> 로 옮겨 두었습니다.

## 0. 실행 정보

| 항목 | 값 |
|---|---|
| 작성일 | 2026-08-06 |
| repo | `D:\battery_archive` · branch `main` · commit `d56171e1c91860021eb0fd95abc4edf9a01f749c` (2026-08-05) |
| BatteryLife | vendored `upstream/BatteryLife` @ `9572e47b1d36ecb31fe58f7d2874a7355dbb6fea` (취득 2026-07-06) |
| 데이터 버전 | **v11** — `config.env: HF_REVISION=v11`, `ZENODO_DIR=./data/zenodo_v11` `[확인]` |
| 원본 | `data/zenodo_v11/` zip 20개 (29 GB) |
| 전개본 | `data/extracted/` 18개 셀 디렉터리 + `Life labels` + `seen_unseen_labels` (87.7 GB) |
| pkl 파일 수 | **1,440개** — 그러나 **고유 셀 이름은 1,344개** (중복 96개, 아래 참조) `[확인]` |
| 라벨 파일 | `data/extracted/Life labels/*_labels.json` 19개, 키 합계 1,324개 `[확인]` |
| 파이썬 | `.venv-blife/Scripts/python.exe` · numpy 1.26.4 · scikit-learn 1.9.0 · pandas 3.0.5 |

**이 리포트의 모든 수치는 v11 기준이다.** 지시서가 물은 v4~v8 은 이 저장소에 없다.

- **SDU 포함** — `SDU_labels.json` (70키) · pkl 86개. 단, **4개 도메인 분할 어디에도 들어가지 않는다** `[확인]`.
- **Farasis 미포함** — `zenodo_v11` 과 `extracted` 둘 다 Farasis 없음. `process_scripts/preprocess_Farasis.py` 는 있으나 데이터가 없다 `[확인]`.

### pkl 중복 96개

| 중복 쌍 | 개수 | 비고 |
|---|---:|---|
| `MICH` ↔ `total_MICH` | 40 | `total_MICH` 은 `MICH` + `MICH_EXP` 의 복사본 |
| `MICH_EXP` ↔ `total_MICH` | 18 | |
| `Stanford` ↔ `Stanford_2` | 38 | `Stanford_2`(181) 가 `Stanford`(41) 을 거의 포함 (교집합 38) |

96쌍 전부 `last_cycle_soh` · 분기 판정이 완전히 동일하다 `[확인]`. 즉 내용 중복이다.
**"1,440 pkl" 을 셀 수로 인용하면 96개를 이중 계산한다.**

---

## 1. 결론 요약

1. **지시서의 가설 — "CALB 는 라벨 분포가 좁아 평균만 예측해도 MAPE 가 낮다" — 은 이 데이터에서 성립하지 않는다** `[확인]`. CALB 의 Dummy MAPE 는 **1.865** 로 네 도메인 중 **가장 나쁘고**, 라벨 CV(0.626)도 Na-ion 보다 크다. 라벨이 가장 좁은 도메인은 **Na-ion (CV 0.396)** 이다.
2. **그러나 CALB 에 판별력이 없다는 결론 자체는 더 강한 근거로 성립한다** `[확인]`. CALB 는 aging condition 이 **온도 4개(0/25/35/45 °C)뿐**이고 수명이 그 4개로 거의 결정된다. 학습 없이 **"같은 조건의 train 평균"** 만 내놓는 baseline 이 **MAPE 0.108** 로, 논문 최고 모델(0.140)을 **이긴다**.
3. **CALB 27셀 중 19셀은 99~100 사이클만 있고 마지막 SOH 가 1.00~1.05 — 열화가 관측되지 않았는데 라벨은 792~1411 이 붙어 있다** `[확인]`. 라벨이 제공 곡선에서 유도 불가능하다.
4. **Na-ion 은 Dummy 와의 격차가 가장 작다** (best/Dummy = **0.631**). test 셀이 **5개**뿐이라 Dummy MAPE 의 95% CI 폭(0.41)이 13개 모델의 MAPE 전체 폭(0.141)보다 **2.9배** 넓다 → **Na-ion 의 모델 순위는 노이즈다** `[확인]`.
5. **네 도메인 중 판별력이 확인되는 것은 Li-ion 뿐이다.** Zn-ion 은 셀마다 프로토콜 ID 가 1:1 로 부여되어(100셀 = 100프로토콜) 조건 일반화를 아예 측정하지 못한다 `[확인]`.

---

## 2. 도메인별 기초 통계 (T2)

### 2-1. 도메인 매핑 — 근거

추측이 아니라 `upstream/BatteryLife/data_provider/data_split_recorder.py:63` 에서 읽었다 `[확인]`.

```
MIX_large_train_files = UL_PUR + RWTH + HUST + MATR + Stanford + Tongji
                      + ISU_ILCC + CALCE + HNEI + SNL + MICH + MICH_EXP + XJTU
```

| 도메인 | 코드상 정의 | 데이터셋 수 |
|---|---|---:|
| Li-ion | `MIX_large_*_files` (위 13개) | 13 |
| Zn-ion | `ZNcoin_*` / `ZN_42_*` / `ZN_2024_*` | 1 |
| Na-ion | `NAion_2021_*` / `NAion_42_*` / `NAion_2024_*` | 1 |
| CALB | `CALB_*` / `CALB_42_*` / `CALB_2024_*` | 1 |

**Li-ion 분할만 seed 에 무관하다** (seed 변형 변수가 없다). Zn/Na/CALB 만 seed 2021·42·2024 별 분할을 가진다 `[확인]`. 논문 표에서 Li-ion Dummy 의 표준편차가 `±0.000` 인 이유가 이것이다.

### 2-2. 도메인별 셀 수 · 분할

| 도메인 | 분할 목록 셀 | 라벨 보유 셀 | train | val | test | 평가 모집단 train | 평가 모집단 test |
|---|---:|---:|---:|---:|---:|---:|---:|
| Li-ion | 843 | **837** | 510 | 165 | 162 | 503 | **158** |
| Zn-ion | 100 | **100** | 60 | 20 | 20 | 59 | **20** |
| Na-ion | 31 | **31** | 20 | 6 | 5 | 20 | **5** |
| CALB | 27 | **27** | 17 | 5 | 5 | 17 | **5** |
| 합계 | 1,001 | 995 | 607 | 196 | 192 | 599 | 188 |

`[확인]` · seed 2021 기준. Zn-ion 은 seed 42 에서 test 평가 모집단이 19가 된다.

**"평가 모집단" 열이 중요하다.** `data_provider/data_loader.py:488` 이

```python
if df is None or eol <= self.early_cycle_threshold:   # early_cycle_threshold 기본 100
    return None, None, None, None, None
```

로 **라벨 ≤ 100 인 셀을 학습·평가에서 통째로 버린다** `[확인]`. Li-ion 에서 837 → 661셀(train+test)로 줄어든다.

Li-ion 843 중 6셀은 라벨이 없다 — `MICH_EXP` 의 `50-100` SOC 6셀 전부다 (6절 참조) `[확인]`.

### 2-3. 개별 데이터셋 16개

| 데이터셋 | 도메인 | 라벨 파일 | train | val | test | 계 | 라벨 보유 |
|---|---|---|---:|---:|---:|---:|---:|
| UL_PUR | Li-ion | `UL-PUR_labels.json` | 2 | 0 | 0 | 2 | 2 |
| RWTH | Li-ion | `RWTH_labels.json` | 30 | 9 | 9 | 48 | 48 |
| HUST | Li-ion | `HUST_labels.json` | 47 | 15 | 15 | 77 | 77 |
| MATR | Li-ion | `MATR_labels.json` | 102 | 34 | 33 | 169 | 169 |
| Stanford | Li-ion | `Stanford_labels.json` | 25 | 8 | 8 | 41 | 41 |
| Tongji | Li-ion | `Tongji_labels.json` | 66 | 21 | 21 | 108 | 108 |
| ISU_ILCC | Li-ion | `ISU-ILCC_labels.json` | 144 | 48 | 48 | 240 | 240 |
| CALCE | Li-ion | `CALCE_labels.json` | 9 | 2 | 2 | 13 | 13 |
| HNEI | Li-ion | `HNEI_labels.json` | 9 | 3 | 2 | 14 | 14 |
| SNL | Li-ion | `SNL_labels.json` | 30 | 10 | 10 | 50 | 50 |
| MICH | Li-ion | `total_MICH_labels.json` | 24 | 8 | 8 | 40 | 40 |
| MICH_EXP | Li-ion | `total_MICH_labels.json` | 12 | 3 | 3 | 18 | **12** |
| XJTU | Li-ion | `XJTU_labels.json` | 15 | 4 | 4 | 23 | 23 |
| ZN-coin | Zn-ion | `ZN-coin_labels.json` | 60 | 20 | 20 | 100 | 100 |
| NA-ion | Na-ion | `NA-ion_labels.json` | 20 | 6 | 5 | 31 | 31 |
| CALB | CALB | `CALB_labels.json` | 17 | 5 | 5 | 27 | 27 |

`[확인]` · seed 2021. **UL_PUR 은 val·test 가 비어 있다** — 학습에만 2셀 기여하고 평가에는 전혀 안 들어간다. `Dummy.py:434` 도 `UL_PUR has no enough samples to evaluate` 로 명시적으로 거부한다.

### 2-4. 표본(sample) 수

**미확인 — 7절 참조.** 다만 생성 규칙은 코드에서 확인했다 `[확인]`:
`data_loader.py:501` `for i in range(seq_len, early_cycle_threshold+1)` → 기본값(`seq_len=5`, `early_cycle_threshold=100`)에서 **적격 셀당 정확히 96개 표본**, 라벨은 셀 라벨 그대로 복제.
셀마다 표본 수가 같으므로 **표본 단위 MAPE = 셀 단위 MAPE** 이다 `[추론]`. 3절의 Dummy 를 셀 단위로 계산해도 모델 행과 비교 가능한 이유가 이것이다.

---

## 3. 라벨 분포와 Dummy 격차 (T3) ← 핵심

### 3-1. MAPE 정의 — repo 를 그대로 따랐다

`upstream/BatteryLife/models/Dummy.py` 의 정의 `[확인]`:

- 예측 `ŷ` = **데이터셋(=`Life labels` json 파일) 단위** train 라벨 평균. 도메인 전체 평균이 아니다. Li-ion 은 12개 평균 그룹을 쓴다.
- `MAPE = sklearn.metrics.mean_absolute_percentage_error(y_true, y_pred)` = `mean(|y−ŷ| / max(|y|, eps))`. 지시서의 식과 동일하다.
- 라벨 json 에 키가 없는 셀은 건너뛴다. Tongji 키만 `--` → `-#` 로 치환한다.

**검증: 내 재구현이 `Dummy.py` 실행 결과와 소수 4자리까지 일치한다** `[확인]`.

| 도메인 | seed | `Dummy.py` 실행값 | 내 재구현 |
|---|---|---:|---:|
| CALB | 2021 / 42 / 2024 | 1.5518 / 2.7043 / 1.3381 | 1.5518 / 2.7043 / 1.3381 |
| ZN-coin | 2021 / 42 / 2024 | 1.2806 / 1.5787 / 1.0513 | 1.2806 / 1.5787 / 1.0513 |
| NA-ion | 2021 / 42 / 2024 | 0.4452 / 0.3796 / 0.3866 | 0.4452 / 0.3796 / 0.3866 |
| MIX_large(Li-ion) | 전 seed | 0.80319 | 0.80319 |

> **`Dummy.py` 는 v11 라벨 번들에서 `MIX_large` 로 그냥 돌리면 죽는다** `[확인]`.
> `find_dataset()` 에 `'MICH'` · `'SDU'` · `'Stanford_2'` 분기가 없어 `MICH_EXP_labels.json` 차례에서
> `TypeError: 'NoneType' object is not iterable` 로 중단된다. 위 Li-ion 값은
> `MICH_labels.json` · `MICH_EXP_labels.json` · `SDU_labels.json` · `Stanford_2_labels.json`
> 4개를 뺀 라벨 디렉터리(=논문 시점 구성 추정)로 돌려 얻었다.

### 3-2. 라벨 분포 통계 (seed 2021)

| 도메인 | 구간 | n | mean | std | **CV** | min | median | max | IQR |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Li-ion | 전체 | 837 | 865.1 | 760.9 | **0.880** | 1 | 614 | 4999 | 536 |
| | train | 510 | 867.5 | 767.8 | 0.885 | 1 | 604 | 4999 | 582 |
| | test | 162 | 879.4 | 764.8 | 0.870 | 20 | 642 | 3842 | 520 |
| Zn-ion | 전체 | 100 | 390.8 | 394.9 | **1.010** | 100 | 188 | 1621 | 326 |
| | train | 60 | 399.4 | 392.1 | 0.982 | 100 | 188 | 1481 | 453 |
| | test | 20 | 341.9 | 396.2 | 1.159 | 101 | 178 | 1621 | 120 |
| Na-ion | 전체 | 31 | 184.5 | 54.0 | **0.293** | 102 | 180 | 307 | 92 |
| | train | 20 | 183.8 | 56.7 | 0.308 | 117 | 171 | 307 | 100 |
| | test | 5 | 188.0 | 77.3 | 0.411 | 102 | 227 | 268 | 127 |
| CALB | 전체 | 27 | 878.9 | 506.3 | **0.576** | 104 | 1171 | 1411 | 1081 |
| | train | 17 | 852.3 | 548.8 | 0.644 | 104 | 1233 | 1267 | 1103 |
| | test | 5 | 883.6 | 476.8 | 0.540 | 108 | 993 | 1272 | 461 |

`[확인]` · `analysis/out/domain_stats.json`

**가설과 반대다.** 라벨 CV 는 Zn-ion(1.010) > Li-ion(0.880) > CALB(0.576) > **Na-ion(0.293)** 순이다.
CALB 는 좁은 게 아니라 **양극단으로 갈라져 있다** — 0 °C 군 104~189, 나머지 792~1411. 단일 평균이 최악의 예측이 되므로 Dummy MAPE 가 오히려 가장 높다.

히스토그램:

| 파일 | 내용 |
|---|---|
| `analysis/out/hist_domains.png` | 4개 도메인 2×2 비교 |
| `analysis/out/hist_Li-ion.png` · `hist_Zn-ion.png` · `hist_Na-ion.png` · `hist_CALB.png` | 도메인별 train/test 누적 |

### 3-3. 판별력 표

모델이 실제로 평가받는 모집단(라벨 > 100)에서 계산했다. seed 3개 평균 ± 표준편차.

| 도메인 | 셀 수 | test 셀 수 | 라벨 CV(test) | Dummy MAPE | Dummy 95% CI | 보고 최고 MAPE | 비율 | 판별력 |
|---|---:|---:|---:|---:|---|---:|---:|---|
| Li-ion | 837 | **158** | 0.847 | 0.579 ± 0.000 | [0.449, 0.733] | 0.179 (CPMLP) | **0.309** | **있음** |
| Zn-ion | 100 | **20** | 1.043 | 1.289 ± 0.217 | [0.938, 1.651] | 0.515 (CPTransformer) | **0.399** | **의심** |
| Na-ion | 31 | **5** | 0.396 | 0.404 ± 0.036 | [0.203, 0.615] | 0.255 (CPTransformer) | **0.631** | **없음** |
| CALB | 27 | **5** | 0.626 | 1.865 ± 0.735 | [0.137, 4.555] | 0.140 (CPMLP) | **0.075** | **없음** |

절대 차이 `Dummy − 최고` : Li-ion 0.400 · Zn-ion 0.774 · Na-ion 0.149 · CALB 1.725.

> 지시서는 CALB 최고 MAPE 를 0.141 로 적었으나, README 표에서 가장 낮은 값은 **CPMLP 0.140** 이다
> (0.141 은 CPGRU). 이 리포트는 0.140 을 썼다. 비율은 0.076 → 0.075 로 바뀔 뿐 결론에 영향이 없다 `[확인]`.

#### 판정 기준 (표 아래 명시)

세 조건을 모두 본다. **하나라도 실격이면 "없음"**, 경계면 "의심".

| 기준 | 통과 조건 |
|---|---|
| (A) Dummy 대비 비율 | `보고최고 / Dummy ≤ 0.5` — 평균 예측 대비 최소 2배 개선 |
| (B) CI 폭 대 모델 폭 | `Dummy 95% CI 폭 < 13개 모델 MAPE 전체 폭` — 순위가 표본 노이즈에 묻히지 않음 |
| (C) 무학습 상한 baseline | `보고최고 < CondMean` — 조건별 train 평균(학습 없음)보다는 나아야 함 |

| 도메인 | (A) 비율 | (B) CI폭 / 모델폭 | (C) 최고 vs CondMean | 판정 |
|---|---:|---:|---|---|
| Li-ion | 0.309 ✅ | 0.284 / 0.407 = **0.70** ✅ | 0.179 < 0.349 ✅ | **있음** |
| Zn-ion | 0.399 ✅ | 0.713 / 0.472 = **1.51** ❌ | 0.515 < 1.289 ✅ | **의심** |
| Na-ion | 0.631 ❌ | 0.412 / 0.141 = **2.92** ❌ | 0.255 < 0.353 ✅(간신히) | **없음** |
| CALB | 0.075 ✅ | 4.418 / 0.621 = **7.11** ❌ | 0.140 > **0.108** ❌ | **없음** |

- Li-ion 도 **1위와 2위의 차(0.005)는 CI 폭(0.284)의 1/57** 이다. 전체 순위 경향은 유의미하지만 **상위 1~2위 구분은 이 데이터로 불가능하다** `[추론]`.
- Zn-ion 은 (A)(C) 를 통과하지만 CI 폭이 모델 전체 폭보다 넓다. 4-1 의 프로토콜 1:1 문제까지 겹쳐 "의심" 으로 둔다.

#### CondMean — 무학습 상한 baseline

Dummy 보다 한 칸 강한 baseline 을 추가했다. **test 셀이 속한 aging condition 의 train 평균**을 예측으로 쓰고, 그 조건이 train 에 없으면 Dummy 로 되돌아간다. 곡선을 전혀 보지 않는다.

| 도메인 | CondMean MAPE | 보고 최고 | test 셀 중 조건이 train 에 있던 수 |
|---|---:|---:|---|
| Li-ion | 0.349 ± 0.000 | 0.179 | 97 / 158 |
| Zn-ion | 1.289 ± 0.217 | 0.515 | **0 / 20** |
| Na-ion | 0.353 ± 0.027 | 0.255 | 2~3 / 5 |
| CALB | **0.108 ± 0.042** | 0.140 | 3~4 / 5 |

**CALB 에서 CondMean(0.108)이 논문 최고 모델(0.140)을 이긴다** `[확인]`.
즉 CALB 벤치마크에서 13개 모델이 겨루는 것은 조기 곡선으로부터의 수명 추정 능력이 아니라 **"온도 조건 → 수명" 조회표**이며, 그 조회표조차 모델이 제대로 못 맞추고 있다.
Zn-ion 은 test 20셀의 조건이 train 에 **하나도 없어** CondMean 이 Dummy 로 완전히 축퇴한다.

### 3-4. Bootstrap CI 폭이 뜻하는 것

test set 복원추출 1000회, 백분위 95% CI (`analysis/out/discriminability.json` 에 seed 별 수록).

| 도메인 | CI 폭 (평균) | 1위–2위 격차 | 13개 모델 MAPE 전체 폭 | CI 폭 / 1-2위 격차 |
|---|---:|---:|---:|---:|
| Li-ion | 0.284 | 0.005 | 0.407 | 57× |
| Zn-ion | 0.713 | 0.043 | 0.472 | 17× |
| Na-ion | 0.412 | 0.017 | 0.141 | 24× |
| CALB | 4.418 | 0.001 | 0.621 | **4418×** |

**test 셀이 5개인 Na-ion·CALB 에서는 어떤 모델 순위도 통계적 의미를 갖지 못한다** `[확인]`.
CALB 의 CI 하한 0.137 은 보고된 최고 MAPE 0.140 과 거의 같다 — **표본을 다시 뽑으면 Dummy 가 최고 모델과 같은 성능을 낼 수 있다는 뜻이다.**

### 3-5. 논문 Dummy 행과의 차이

| 도메인 | 논문 README Dummy | v11 재계산 (`Dummy.py` 정의) | 차이 |
|---|---:|---:|---:|
| Li-ion | 0.831 ± 0.000 | 0.803 ± 0.000 | −0.028 |
| Zn-ion | 1.297 ± 0.214 | 1.304 ± 0.264 | +0.007 |
| Na-ion | 0.404 ± 0.029 | **0.404** ± 0.036 | 0.000 |
| CALB | 1.811 ± 0.550 | 1.865 ± 0.735 | +0.054 |

Na-ion 은 완전 일치, Zn-ion 은 0.5% 이내. **Li-ion 만 3.4% 낮다** — 계산 방식이 아니라 **라벨 버전 차이**로 본다 `[추론]`. (계산 일치는 3-1 에서 별도 검증했다.)

> **논문 표의 Dummy 행과 모델 행은 서로 다른 모집단에서 계산된 값이다** `[확인]`.
> Dummy 행은 `Dummy.py` 경로 = 셀 단위 · 라벨 필터 없음(Li-ion 162셀).
> 모델 행은 loader 경로 = 표본 단위 · `eol > 100` 필터(Li-ion 158셀).
> 같은 정의로 맞추면 Li-ion Dummy 는 0.803 이 아니라 **0.579** 다. 두 행을 나란히 읽을 때 주의가 필요하다.

---

## 4. 조건 다양성 분해 (T4)

### 4-1. 도메인별 분해

| 도메인 | 셀 | 포맷 | 화학계 | 온도 | 프로토콜 | 셀/프로토콜 | 셀/온도 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Li-ion | 843 | 4 | 13 | 19 | **424** | 1.99 | 44.4 |
| Zn-ion | 100 | 1 | 1 | 0 | **100** | **1.00** | — |
| Na-ion | 31 | 1 | 1 | 0 | 12 | 2.58 | — |
| CALB | 27 | 1 | 1 | **4** | **4** | 6.75 | 6.75 |
| 4도메인 합집합 | 1,001 | 6 | 15 | 21 | 540 | — | — |

`[확인]` · 포맷/화학계는 pkl 최상위 필드, 프로토콜은 `name2agingConditionID.json`.
**온도·화학계 정의는 논문과 다를 수 있다 — 5절·7절 참조.**

**논문이 주장하는 다양성은 사실상 전부 Li-ion 에서 나온다** `[확인]`.

- **Zn-ion: 셀당 프로토콜 1개.** `aging_conditions.py:1432-1435` 가 ZN-coin 셀마다 `protocols[file] = max_value + 1` 로 **새 ID 를 발급**한다. 100셀 = 100프로토콜. 조건 효과와 셀 개체차를 원리적으로 분리할 수 없고, test 20셀의 조건은 train 에 하나도 없다(3-3).
- **Na-ion: 화학계 `Unknown|Unknown|(none)`.** 31셀 전부 미상이다 → **"59 chemical systems" 에 0 기여** `[확인]`. 온도 데이터도 없다.
- **CALB: 프로토콜 4개 = 온도 4개.** 정확히 일치한다 (`cond ID 396/397/398/399` ↔ `0/25/35/45 °C`) `[확인]`.
- **Li-ion 도 424개 중 321개(76%)가 셀 1개짜리 프로토콜이다** `[확인]`. 조건당 반복이 1이면 조건 효과를 셀 개체차와 분리할 수 없다.

Li-ion 프로토콜 크기 분포 (셀 수 → 프로토콜 개수): 1→321, 2→31, 3→21, 4→24, 5→7, 6~17→각 1~4, 24→1, 26→1, 48→1.

test 조건의 seen/unseen:

| 도메인 | test 조건 중 train·val 에 있던 것 | 없던 것 |
|---|---:|---:|
| Li-ion | 61 | 56 |
| Zn-ion | **0** | 20 |
| Na-ion | 3 | 1 |
| CALB | **4** | **0** |

`[확인]` · CALB 는 test 조건이 100% train 에 있고, Zn-ion 은 0% 다. 정반대 극단이다.

### 4-2. CALB — 온도가 수명을 거의 결정한다

| 온도 | cond ID | n | 라벨 |
|---|---:|---:|---|
| 0 °C | 396 | 8 | 104, 105, 108, 123, 161, 164, 176, 189 |
| 25 °C | 397 | 2 | 792, 982 |
| 35 °C | 398 | 14 | 1171, 1233, 1241, 1243, 1253, 1260, 1260, 1267, 1272, 1283, 1301, 1318, 1352, 1411 |
| 45 °C | 399 | 3 | 981, 987, 993 |

`[확인]` · 35 °C 14셀의 라벨은 1171~1411 범위 안에 전부 들어간다(CV 0.05). 45 °C 3셀은 981~993(CV 0.006).
**파일명 접두 `CALB_35_` 만 보고 1260 이라고 답하면 그 셀의 MAPE 는 수 % 다.** CondMean 0.108 의 정체다.

### 4-3. 온도 분포

| 도메인 | 온도 값 (측정 중앙값 반올림, 셀 수) |
|---|---|
| Li-ion | 17(1) 18(3) 19(2) 20(2) 25(5) 26(9) 27(7) 28(6) 29(1) 30(3) 31(6) 32(29) 33(42) 34(29) 35(25) 36(22) 37(15) 38(10) 39(4) — **843셀 중 221셀만 온도 데이터 보유** |
| Zn-ion | 없음 (`temperature_in_C` 전무) |
| Na-ion | 없음 |
| CALB | 0(8) 25(2) 35(14) 45(3) |

`[확인]` · Li-ion 값이 32~39 에 몰린 연속 분포인 것은 **설정 온도가 아니라 측정 실온 드리프트**로 보인다 `[추론]`. 논문의 "9 operation temperatures" 는 공칭 설정 온도일 것이나, pkl 에 공칭 온도 필드가 없어 재현할 수 없다(7절).

### 4-4. 포맷 · 화학계

| 도메인 | 포맷 (셀 수) |
|---|---|
| Li-ion | `cylindrical_18650`(491) · `502030-size Li-polymer`(240) · `pouch`(99) · `prismatic`(13) |
| Zn-ion | `coin`(100) |
| Na-ion | `cylindrical_18650`(31) |
| CALB | `Prismatic`(27) — Li-ion 의 `prismatic` 과 대소문자만 다르다 |

Li-ion 상위 화학계: `NMC|graphite`(309) · `LiFePO4|graphite`(169) · `LFP|graphite`(86) · `NCA|Graphite/Si`(61) · `NMC111|graphite`(58) · `LiNi0.5Mn0.3Co0.2O2|graphite`(41) …
**`NMC`/`NMC111`/`LiNi0.5Mn0.3Co0.2O2` 처럼 같은 조성이 다른 문자열로 들어가 있다** `[확인]` — 화학계 개수는 정규화 방식에 좌우된다.

---

## 5. 보고값 대조 (T5)

| 논문/README 값 | v11 재계산 | 판정 |
|---|---|---|
| **990 batteries** | **977** (코드 자체 규칙 적용) / 1,001 (분할 목록 전체) / 995 (라벨 보유) | **불일치, 근접** |
| **99,000 samples** | 미확인 — 규칙은 확인 (2-4절) | **미확인** |
| **16 datasets** | **16** (분할 코드 기준) | **일치** |
| **8 battery formats** | **6** 문자열 / 실질 **5** (`Prismatic`·`prismatic` 중복) | **불일치** |
| **59 chemical systems** | **15** (cathode\|anode\|electrolyte 삼중조합) | **불일치 — 정의 불명** |
| **9 operation temperatures** | **21** (측정 중앙값 반올림) | **불일치 — 정의 불명** |
| **421 protocols** | **540** / 논문 필터 적용 시 **532** | **불일치** |

`[확인]` · `analysis/out/conditions_reported.json`, `analysis/out/diversity.json`

### 990 재계산의 근거

`dataset_overview_calculation.py:get_agingCondition_battery_num` 의 규칙을 그대로 썼다 `[확인]`:
`Stanford_labels.json` 을 건너뛰고 → **라벨 ≤ 100 인 셀 제외** → 분할 목록과 교집합.
결과 **977**. 13개 차이의 원인은 특정하지 못했다(7절).

- 라벨 ≤ 100 인 셀은 전체에서 **40개** `[확인]`.
- `Stanford_labels.json` 을 건너뛰는 이유는 확인했다 — `Stanford`(41키) 중 38키가 `Stanford_2`(181키)에 중복되기 때문이다 `[확인]`.

### 초기 arXiv 판(998 / 80 / 12 / 646) vs 현재판(990 / 59 / 9 / 421)

**셀 수만 놓고 보면 현재판(990) 쪽에 가깝다** — 재계산 977 은 990 과 13 차이, 998 과는 21 차이 `[확인]`.
포맷·화학계·온도·프로토콜은 두 판 모두와 맞지 않는다. 다만 **프로토콜 재계산값 540 은 421 보다 646 에 가깝다** `[확인]` — 이것만으로 초기판 기준이라 판정하기엔 근거가 약하다 `[추론]`.

### 분할에 들어가지 않는 라벨 239개

| 접두 | 개수 | 비고 |
|---|---:|---|
| Stanford | 143 | `Stanford_2` 의 비중복분 |
| SDU | 70 | 분할·`Dummy.py` 어디에도 없음 |
| ZN-coin | 21 | |
| NA-ion | 3 | |
| SNL | 2 | |

`[확인]` · **SDU 70셀은 v11 에 배포되었으나 4개 도메인 벤치마크에 전혀 쓰이지 않는다.**

---

## 6. 기존 감사 항목 교차 (T6)

`analysis/recount_label_filters.py` 로 **v11 pkl 1,344 고유 셀 전수를 다시 계산했다** — 기존 결과를 받아쓰지 않았다.
규칙은 `process_scripts/Extract_life_labels.py:110-155` 그대로:

```
soh(c) = max(c['discharge_capacity_in_Ah']) / nominal_capacity / SOC_interval
         (RWTH → 1.85, SNL_18650_NCA_25C_20-80 → 3.2, SOC_interval==0 → 1)
last_soh >= 0.825      -> 폐기 (라벨 JSON 에 키 없음)
0.8 < last_soh < 0.825 -> 외삽 (마지막 20사이클 선형회귀)
last_soh <= 0.8        -> 첫 교차
```

### 6-1. 0.825 폐기 임계가 도메인별로 제거한 셀

**벤치마크 모집단(분할 1,001셀) 기준:**

| 도메인 | 셀 | 폐기(≥0.825) | 외삽 | 첫교차 | 라벨 없음 | 단조성 위반 셀 |
|---|---:|---:|---:|---:|---:|---:|
| Li-ion | 843 | 6 | 173 | 664 | **6** | 824 |
| Zn-ion | 100 | 0 | 3 | 97 | **0** | 100 |
| Na-ion | 31 | 0 | 6 | 25 | **0** | 29 |
| CALB | 27 | **19** | 4 | 4 | **0** | 26 |

**디스크 전수(1,344 고유 셀) 서브셋별:**

| 서브셋 | 셀 | 폐기 | 외삽 | 첫교차 | 라벨 없음 | 단조위반 셀 |
|---|---:|---:|---:|---:|---:|---:|
| CALB | 27 | 19 | 4 | 4 | 0 | 26 |
| CALCE | 13 | 0 | 0 | 13 | 0 | 13 |
| HNEI | 14 | 0 | 0 | 14 | 0 | 14 |
| HUST | 77 | 0 | 77 | 0 | 0 | 77 |
| ISU_ILCC | 240 | 0 | 0 | 240 | 0 | 240 |
| MATR | 169 | 0 | 81 | 88 | 0 | 169 |
| MICH | 40 | 0 | 0 | 40 | 0 | 40 |
| MICH_EXP | 18 | **6** | 1 | 11 | **6** | 10 |
| NA-ion | 64 | **21** | 6 | 37 | **30** | 58 |
| RWTH | 48 | 0 | 0 | 48 | 0 | 48 |
| SDU | 86 | 0 | 9 | 77 | 16 | 86 |
| SNL | 61 | **9** | 3 | 49 | **9** | 61 |
| Stanford | 41 | 0 | 0 | 41 | 0 | 41 |
| Stanford_2 | 143 | 0 | 0 | 143 | 0 | 143 |
| Tongji | 130 | **22** | 8 | 100 | **22** | 111 |
| UL_PUR | 10 | 0 | 5 | 5 | 8 | 10 |
| XJTU | 23 | 0 | 1 | 22 | 0 | 23 |
| ZN-coin | 140 | **19** | 3 | 118 | **19** | 136 |

`[확인]` · `analysis/out/label_filter_recount.csv`

### 6-2. censored cell 77개 — 독립 재계산으로 확인됨

| 서브셋 | 기존 보고 | 이번 재계산 (폐기 ≥0.825) | 일치 |
|---|---:|---:|---|
| NA-ion | 21 | **21** | ✅ |
| ZN-coin | 19 | **19** | ✅ |
| Tongji | 22 | **22** | ✅ |
| SNL | 9 | **9** | ✅ |
| MICH_EXP | 6 | **6** | ✅ |
| **합계** | **77** | **77** | ✅ |

`[확인]` · **기존 감사의 77 은 v11 에서 그대로 재현된다.** "폐기(≥0.825)만" 정의일 때만 77 이다.
"폐기+외삽" 으로 세면 98, "배포 라벨에 키 없음" 으로 세면 86 이 된다.

**추가로 확인된 것:** 0.825 폐기가 아닌 사유로 라벨이 빠진 셀이 **33개** 더 있다 `[확인]`.

| 서브셋 | 개수 | 특징 |
|---|---:|---|
| SDU | 16 | 첫교차 분기인데 라벨 없음 |
| NA-ion | 9 | 첫교차, 사이클 수 91~134 |
| UL_PUR | 8 | 외삽/첫교차, SOH 0.80~0.824 |

`Extract_life_labels.py:155-159` 에 주석 처리된 `if eol < 100: continue` 가 배포 라벨 생성 시점에는 살아 있었을 가능성이 크다 `[추론]`.

### 6-3. 라벨 단조성 위반

`soh[i] > soh[i-1] + 1e-9` 지점이 하나라도 있는 셀을 위반으로 셌다.

**거의 모든 셀이 위반한다** — Li-ion 843셀 중 824, Zn-ion 100/100, Na-ion 29/31, CALB 26/27 `[확인]`.
측정 노이즈 수준의 미세 상승을 전부 잡는 정의라 **이 임계값으로는 도메인 간 구분이 되지 않는다.** 의미 있는 임계값 설정은 하지 않았다(7절).

### 6-4. CALB 의 낮은 MAPE 는 "어려운 셀을 걸러낸 결과" 인가 — **아니다**

지시서가 검토를 요청한 가설이다. **기각한다** `[확인]`.

- CALB 는 pkl 27개 · 라벨 27개 · **제거된 셀 0개**다. 필터가 전혀 걸리지 않았다.
- 오히려 반대다: CALB 27셀 중 **19셀이 last SOH ≥ 0.825** 로, 다른 도메인이었다면 **전부 폐기됐을 셀**이다. `Extract_life_labels.py:107` 의 `if dataset_name != 'CALB'` 분기가 CALB 만 이 경로에서 제외하고 외부 파일에서 라벨을 읽는다.

**그리고 그 19셀의 상태가 이 리포트에서 가장 심각한 발견이다:**

| 셀 | 배포 라벨 | 보유 사이클 | last SOH |
|---|---:|---:|---:|
| CALB_25_T25-1 | 792 | 99 | 1.021 |
| CALB_25_T25-2 | 982 | 99 | 1.022 |
| CALB_35_B173 | 1233 | 99 | 1.022 |
| CALB_35_B247 | 1411 | 99 | 0.999 |
| CALB_45_B253 | 981 | 100 | 1.044 |
| … (19셀 전부 동일 양상) | 792~1411 | 99~100 | 0.999~1.051 |

`[확인]` · 전체는 `analysis/out/label_filter_recount.csv`

**99~100 사이클 동안 SOH 가 1.0 아래로 내려간 적이 없는데, 수명 라벨은 그 8~14배인 792~1411 이다.**
제공된 곡선에서 이 라벨을 유도할 방법이 없다. 반면 나머지 8셀(0 °C)은 100~208 사이클 안에 실제로 EOL 에 도달했고 라벨도 104~189 로 관측과 맞는다.

즉 CALB 벤치마크는 **"열화가 안 보이는 100사이클을 주고 1250 을 맞히라"** 는 과제이며, 유일한 신호는 온도군이다. 4-2·3-3 의 CondMean 결과와 정확히 들어맞는다 `[추론]`.

---

## 7. 미확인 항목과 사유

| # | 항목 | 사유 |
|---|---|---|
| 1 | **도메인별 표본(sample) 수** | 표본은 loader 가 런타임에 만든다. 정확히 세려면 `Dataset_original` 을 4개 도메인 × 3 seed 로 인스턴스화해야 하고, 82 GB pkl 을 전 셀 재파싱한다. 지시서의 "학습 금지" 취지(시간·비용)에 맞춰 실행하지 않았다. **규칙은 확인**: 적격 셀당 96표본(기본 인자), 라벨 ≤ 100 셀 제외 (2-4절). |
| 2 | **"99,000 samples" 대조** | 위와 같음. 990셀 × 100 = 99,000 으로 맞아떨어지나, 코드 규칙은 셀당 96 이므로 논문이 어느 정의를 썼는지 불명 `[추론]`. |
| 3 | **"59 chemical systems" 의 정의** | 논문·README·코드 어디에도 정의가 없다. 삼중조합(cathode\|anode\|electrolyte)으로는 15다. 양극 표기가 `NMC`·`NMC111`·`LiNi0.5Mn0.3Co0.2O2` 처럼 혼재해, 정규화 방식에 따라 값이 크게 달라진다. |
| 4 | **"9 operation temperatures" 의 정의** | pkl 에 공칭 온도 필드가 없다. `cycle_data[*].temperature_in_C` 측정값만 있고 Zn-ion·Na-ion 은 그마저 없다. 측정 중앙값 반올림으로는 21이다. |
| 5 | **"8 battery formats" 의 2개 차이** | 분할 1,001셀에서 나온 `form_factor` 문자열은 6종(대소문자 중복 제외 5종). 분할 밖 셀(SDU 등)을 포함해도 8이 되지 않았다. |
| 6 | **990 vs 977 의 13셀 차이** | 코드 규칙을 그대로 적용해도 13 부족하다. 논문 집계 시점의 라벨 파일 구성이 v11 과 다를 가능성이 크나(3-5 의 Li-ion Dummy 차이와 같은 원인) 특정하지 못했다. |
| 7 | **의미 있는 단조성 위반 임계** | `>1e-9` 로는 거의 전 셀이 위반이라 도메인 비교에 못 쓴다. 노이즈와 실제 용량 회복을 가르는 임계값은 정하지 않았다. |
| 8 | **CALB 라벨 792~1411 의 출처** | `Extract_life_labels.py` 가 CALB 만 외부 파일에서 읽는데, 그 파일이 배포본에 없다. 라벨 유도 근거를 확인할 수 없다. |
| 9 | **v4~v8 데이터** | 이 저장소에 없다. v11 만 있다. |
| 10 | **Farasis** | 데이터 미배포. `preprocess_Farasis.py` 만 존재. |

---

## 8. 재현 방법

전부 `D:\battery_archive` 에서, `.venv-blife` 파이썬으로 실행한다. **모델 학습은 하지 않는다.**

```bash
# T3 핵심 — 라벨 분포, Dummy MAPE, bootstrap CI, 히스토그램
.venv-blife/Scripts/python.exe analysis/domain_discriminability.py

# 아래 3개는 analysis/ 안에서 실행 (같은 폴더 모듈을 import 한다)
cd analysis
../.venv-blife/Scripts/python.exe conditions_and_reported.py   # T4 프로토콜 + T5 보고값 대조
../.venv-blife/Scripts/python.exe condition_mean_baseline.py   # CondMean baseline
cd ..

# 논문 표 파싱
.venv-blife/Scripts/python.exe analysis/reported_table.py

# T4 입력 — 전 셀 메타 추출 (약 8분, 1,440 pkl 전수 로드)
.venv-blife/Scripts/python.exe analysis/extract_cell_meta.py
cd analysis && ../.venv-blife/Scripts/python.exe diversity_breakdown.py && cd ..

# T6 — 0.825 폐기 · 분기 · 단조성 재계산 (약 8분)
.venv-blife/Scripts/python.exe analysis/recount_label_filters.py

# T3 최종 표
cd analysis && ../.venv-blife/Scripts/python.exe discriminability_table.py
```

의존 순서: `extract_cell_meta.py` → `diversity_breakdown.py` · `reported_table.py` → `discriminability_table.py`.

### 상위 `Dummy.py` 직접 실행 (3-1 검증)

```bash
# 라벨/조건 파일을 작업 디렉터리에 배치
mkdir -p /tmp/dummyrun/dataset
cp -r "data/extracted/Life labels" /tmp/dummyrun/dataset/
cp -r upstream/BatteryLife/dataset/seen_unseen_labels /tmp/dummyrun/dataset/
cp upstream/BatteryLife/models/Dummy.py /tmp/dummyrun/

cd /tmp/dummyrun
python Dummy.py CALB 2021        # -> Test MAPE: 1.5518387101757631
python Dummy.py ZN-coin 2021     # -> Test MAPE: 1.2805655614842744
python Dummy.py NA-ion 2021      # -> Test MAPE: 0.4452344902225548

# MIX_large 는 그대로면 TypeError 로 죽는다. 아래 4개를 뺀 라벨 디렉터리로 실행:
#   MICH_labels.json  MICH_EXP_labels.json  SDU_labels.json  Stanford_2_labels.json
python Dummy.py MIX_large 2021   # -> Test MAPE: 0.8031889911881935
```

### 스크립트

| 경로 | 역할 |
|---|---|
| `analysis/domain_discriminability.py` | T2/T3 — 분할·라벨 통계·Dummy·bootstrap·히스토그램 |
| `analysis/conditions_and_reported.py` | T4 프로토콜 · T5 보고값 대조 · 커버리지 |
| `analysis/condition_mean_baseline.py` | 조건별 train 평균 baseline |
| `analysis/extract_cell_meta.py` | 1,440 pkl 메타 추출 |
| `analysis/diversity_breakdown.py` | T4 포맷/화학계/온도/프로토콜 분해 |
| `analysis/recount_label_filters.py` | T6 — 0.825 폐기·외삽·단조성 재계산 |
| `analysis/reported_table.py` | README 벤치마크 표 파싱 |
| `analysis/discriminability_table.py` | T3 최종 판별력 표 |

### 산출물

| 경로 | 내용 |
|---|---|
| `analysis/out/domain_stats.json` | 도메인×seed 별 분할 크기·라벨 통계·Dummy·CI |
| `analysis/out/discriminability.json` · `.md` | 3-3 판별력 표 |
| `analysis/out/condition_mean_baseline.json` | CondMean baseline |
| `analysis/out/conditions_reported.json` | 프로토콜 수 · 990 재계산 · 커버리지 |
| `analysis/out/diversity.json` | 포맷/화학계/온도/프로토콜 분해 |
| `analysis/out/reported_table.json` | 논문 표 13모델 × 4도메인 |
| `analysis/out/cell_meta.csv` | 1,440행 셀 메타 |
| `analysis/out/label_filter_recount.csv` | 1,440행 SOH·분기·단조성 |
| `analysis/out/hist_domains.png` 외 4개 | 라벨 히스토그램 |
