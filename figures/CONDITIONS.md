# figures/ — 각 그림이 어느 실행에서 나왔는가

2026-08-05 · CC · 생성 스크립트 `train/curves.py` → `train/figures.py`

원자료는 `runs/2026-08-04/` 의 로그이고, 정규화 중간물은
`experiments/results/curves/*.json` 입니다. **학습을 새로 돌리지 않았습니다.**
그림에 찍힌 값은 전부 로그에 있던 값입니다 — 추정·보간한 점이 하나도
없습니다.

- 판본은 전부 **BatteryLife_Processed v11** · `Dataset_original` 입니다.
- `train_epochs` 는 진단 `x3_patience`(50) 를 뺀 전부가 **100**,
  `least_epochs` 는 전부 **5** 입니다.
- 그림에 **`superseded` 묶음(옛 셸 파라미터 기준 `timing_*` · `smoke_*` ·
  `test_*`)을 쓰지 않았습니다.**

## 0. 정본 기준

> **Zn-ion 은 `lr 5e-5` 판이 정본입니다.** 문서 지정값 `5e-4`(CPTransformer
> 는 `1e-3`)로는 학습되지 않아 다른 세 도메인과 같은 값으로 낮췄습니다.
> 5e-4 판은 `diagnostic` 으로 보존되어 있으며 그림 1 이 두 판을 대비합니다.

정본은 `zn_lr9.log` 의 9회이고 Table 3 대조표(보고서 부록 B)가 이 값으로
만들어졌습니다 — `Zn-ion CPMLP` 3 seed 의 Test MAPE 가 0.545 · 0.6375 ·
0.7047 로 **0.629 ± 0.080** 입니다. `runs/2026-08-04/README.md` 와 같습니다.

**파일명이 아니라 JSON 의 `group` 필드가 정본 여부의 근거입니다.**
Zn-ion 은 파일명을 그대로 두고 묶음만 맞바꿨기 때문에, 접미사 없는
`CPMLP_Zn-ion_s2021.json` 이 `diagnostic`(5e-4) 이고
`CPMLP_Zn-ion_s2021__lr5e-05.json` 이 `main` 입니다. 다른 세 도메인은
접미사 없는 쪽이 `main` 입니다. 재지정 스크립트는
`train/regroup_znion.py` 입니다.

---

## 1. 그림별 출처

| 그림 | 사용한 실행 | 묶음 | 판본 | patience | lr | batch | 비고 |
|---|---|---|---|---:|---|---:|---|
| **1** `fig1_znion_lr.png` | `CPMLP_Zn-ion_s2021` | diagnostic | v11 | 5 | **5e-4** | 128 | 문서 학습률. `20260804-154322_CPMLP_Zn-ion_s2021.log` |
| | `CPMLP_Zn-ion_s2021__x3_patience` | diagnostic | v11 | **100** | 5e-4 | 128 | 50에폭 강제. `zn_x3_patience.log` |
| | `CPMLP_Zn-ion_s2021__lr5e-05` | **main** | v11 | 5 | **5e-5** | 128 | `zn_lr9.log` 의 `lr_CPMLP_Zn-ion_s2021` |
| **2** `fig2_domains.png` | `CPMLP_CALB_s2021` | main | v11 | 5 | 5e-5 | 16 | 시험 5셀 |
| | `CPMLP_Na-ion_s2021` | main | v11 | 5 | 5e-5 | 128 | 시험 5셀 |
| | `CPMLP_Zn-ion_s2021__lr5e-05` | main | v11 | 5 | 5e-5 | 128 | 시험 20셀 · `zn_lr9.log` |
| | `CPMLP_Li-ion_s2021` | main | v11 | 5 | 5e-5 | 32 | 시험 162셀 |
| **3** `fig3_calb_seeds.png` | `CPMLP_CALB_s42` | main | v11 | 5 | 5e-5 | **8** | d_model 128 · d_ff 128 · e7/d9 · dropout 0.05 |
| | `CPMLP_CALB_s2021` | main | v11 | 5 | 5e-5 | 16 | d_model 32 · d_ff 32 · e12/d6 · dropout 0.1 |
| | `CPMLP_CALB_s2024` | main | v11 | 5 | 5e-5 | 16 | d_model 256 · d_ff 128 · e12/d6 · dropout 0 |
| **4** `fig4_liion_vs_calb.png` | `CPMLP_Li-ion_s2021` | main | v11 | 5 | 5e-5 | 32 | 시험 162셀 · `MIX_large_841` |
| | `CPMLP_CALB_s2021` | main | v11 | 5 | 5e-5 | 16 | 시험 5셀 · **에폭별 변동이지 반복 간 흩어짐이 아닙니다** — 아래 §2 |
| **5** `fig5_early_stop.png` | main 36회 전부 | main | v11 | 5 | **5e-5 (36회 전부)** | 8~256 | 학습률은 통일, `batch_size` 는 갈립니다 — 아래 §2 |
| **6** `fig6_seen_unseen.png` | `MLP_Li-ion_s2021` · `CPMLP_Li-ion_s2021` · `CPTransformer_Li-ion_s2021` | main | v11 | 5 | 5e-5 | 32 / 32 / 256 | **막대** — 에폭별 값이 로그에 없습니다 (§3) |

그림 3 의 CALB 3 seed 는 `learning_rate` 만 같고 `batch_size` ·
`d_model` · `d_ff` · `e_layers` · `d_layers` · `dropout` 이 seed 마다
다릅니다. 문서 하이퍼파라미터가 원래 그렇습니다
(`docs/reports/2026-08-04_calb_seed_hp.md` §1). 범례에 값을 적어 두었습니다.

---

## 2. 읽을 때 주의할 것

### 그림 2 — 네 칸의 학습률이 같습니다

CALB · Na-ion · Zn-ion · Li-ion 전부 `lr 5e-5` 입니다.
2026-08-05 묶음 재지정 전에는 Zn-ion 칸만 `5e-4` 라 `[조건 다름]` 각주를
달았으나, 정본이 5e-5 판으로 바뀌면서 **각주를 뗐습니다.** 지금 갈리는
것은 `batch_size`(16 · 128 · 128 · 32) 뿐이고 각 칸 제목에 적혀 있습니다.

### 그림 5 — 학습률은 통일, batch_size 는 갈립니다

36회 전부 `lr 5e-5` · `patience 5` · `least_epochs 5` · `train_epochs 100`
입니다. `batch_size` 만 8~256 으로 갈립니다 (문서 하이퍼파라미터).
그림 5 가 보는 것은 종료 시점이지 성능이 아니므로 한 축에 올렸습니다.

### 그림 4 — 에폭별 변동과 반복 간 흩어짐은 다른 얘기입니다

그림 4 는 **한 실행 안에서 에폭마다 변하는 정도**를 보여 줍니다.
표본 크기와 관련된 것은 **반복 3회의 결과가 벌어지는 정도**이고 그쪽은
**그림 3** 입니다. 그림 4 에서 Li-ion 곡선이 CALB 보다 더 흔들려 보인다고
해서 "표본이 크면 더 흔들린다" 로 읽으면 안 됩니다 — 두 그림이 재는
것이 다릅니다. 부제에 같은 취지를 한 줄 넣었습니다.

### 그림 1 — 5e-4 두 곡선은 에폭 1~17 이 완전히 같습니다

문서 학습률 판(patience 5) 과 `x3_patience`(patience 100 · 50에폭) 는
seed · 데이터 · 나머지 인자가 같아 **겹치는 17에폭의 Train Loss 와
Test MAPE 가 소수점까지 일치합니다** (프로그램으로 대조). 실선이 파선에
가려 보이는 것은 두 실행이 같기 때문이지 그림이 잘못된 것이 아닙니다.

이 그림은 정본 여부와 무관하게 **두 학습률을 나란히 놓는 것이 목적**이라
묶음 재지정의 영향을 받지 않습니다. 재지정 전후로 PNG 가 바이트 단위로
동일합니다.

---

## 3. 그림 6 이 막대인 이유

에폭 지표 줄에는 Seen/Unseen 이 없습니다. 로그의 실제 형식은

```
Epoch: 13 | Train Loss: ... | Train MAPE: ... | Vali MAPE: ... | Test MAPE: ...
```

이고 Seen/Unseen 은 학습이 끝난 뒤 한 번만 찍힙니다.

```
Best model performance: Test Seen MAPE: 0.1594 | Test Unseen MAPE: 0.2397
```

**에폭별 추이를 만들 자료가 없습니다.** 보간하지 않고 최종값 막대로
바꿨습니다. 15%-Acc 도 같습니다 — 에폭별로는 없고 최종값만 있습니다.

---

## 4. 색 규칙

`matplotlib` 기본 색상 순환입니다.

| 뜻 | 색 |
|---|---|
| Train | `C0` |
| Validation | `C1` |
| Test | `C2` |
| 최적 검증 에폭 세로선 | `C2` 파선 (그림 3·4 는 곡선 색을 따름) |
| 실제 종료 에폭 (그림 5) | `C4` ▽ |
| 기준선 (`y=1.0`) | `C3` 점선 |

조건이 갈리는 칸에 붉은 제목과 `[조건 다름]` 을 붙이는 장치가
`train/figures.py` 에 남아 있습니다. 지금은 네 도메인이 전부 `lr 5e-5`
라 발동하지 않습니다 — 묶음이 다시 바뀌면 자동으로 다시 뜹니다.

그림 1 은 갈래가 split 이 아니라 **조건**이라 조건별로 색을 줬습니다 —
`C0` 5e-4 계열(실선 patience 5 · 파선 50에폭 강제) · `C1` 5e-5.

한글 폰트는 `Malgun Gothic` 을 찾아 썼습니다.

---

## 5. 최적 검증 에폭을 어떻게 정했는가

로그에 "최적 에폭" 이 직접 찍히지 않습니다. 조기 종료 카운터로 되짚었습니다.

- 에폭 지표 줄 뒤에 `EarlyStopping counter:` 가 **따라오지 않으면** 그
  에폭이 검증 갱신입니다.
- 그런 마지막 에폭을 `best_val_epoch` 로 잡았습니다.

**36회 전부 교차 검증했습니다** — 그 에폭의 `Test MAPE` 가 로그 마지막
`Best model performance: ... Test MAPE:` 와 소수점까지 일치합니다
(불일치 0건). JSON 의 `best_epoch_agrees_with_final` 필드입니다.
