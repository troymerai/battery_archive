# CALB seed별 하이퍼파라미터 — 검증 결과

2026-08-05 · CC

> **결론 먼저.** 지시가 전제한 결함이 **없습니다.** `.build/` 의 CALB
> 스크립트 6개는 처음부터 각자 제 seed 의 문서 값으로 만들어져 있고,
> 2026-08-04 에 실행된 6회도 각자 제 seed 의 문서 값으로 돌았습니다.
> 로그에 찍힌 인자 사전으로 확인했습니다 (§3).
>
> 따라서 **스크립트 수정 · 기존 결과 이관 · 4회 재실행 · §7-3 갱신 ·
> LOCK 해시 재계산을 하지 않았습니다.** 고칠 것이 없고, 재실행하면 같은
> 설정을 한 번 더 도는 것이며, `prev_calb_seed2021hp/` 라는 이름의
> 디렉터리를 만들면 존재한 적 없는 조건을 있었던 것처럼 남기게 됩니다.
>
> 실제로 한 일은 **전수 검증**과 **관찰 1건 기록**(TRN-015)입니다.

---

## 1. 문서에서 읽은 CALB 12행

`upstream/BatteryLife/assets/Selected_hyperparameters.md:24-26, 36-38,
48-50, 60-62` 원문 그대로입니다.

| model | dataset | seed | batch_size | d_model | d_ff | e_layers | d_layers | dropout | learning_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CPMLP | CALB | 42 | 4 | 128 | 128 | 7 | 9 | 0.05 | 5e-05 |
| CPMLP | CALB | 2021 | 8 | 32 | 32 | 12 | 6 | 0.1 | 5e-05 |
| CPMLP | CALB | 2024 | 8 | 256 | 128 | 12 | 6 | 0 | 5e-05 |
| CPTransformer | CALB | 42 | 64 | 256 | 256 | 6 | 7 | 0.05 | 5e-05 |
| CPTransformer | CALB | 2021 | 8 | 64 | 256 | 9 | 9 | 0.1 | 5e-05 |
| CPTransformer | CALB | 2024 | 4 | 128 | 256 | 7 | 6 | 0 | 5e-05 |
| CPGRU | CALB | 42 | 4 | 32 | 256 | 2 | 2 | 0 | 5e-05 |
| CPGRU | CALB | 2021 | 4 | 32 | 256 | 2 | 2 | 0 | 5e-05 |
| CPGRU | CALB | 2024 | 4 | 32 | 256 | 2 | 2 | 0 | 5e-05 |
| CPLSTM | CALB | 42 | 4 | 32 | 32 | 8 | 2 | 0.05 | 5e-05 |
| CPLSTM | CALB | 2021 | 4 | 32 | 32 | 8 | 2 | 0.05 | 5e-05 |
| CPLSTM | CALB | 2024 | 4 | 32 | 32 | 8 | 2 | 0.05 | 5e-05 |

**지시서의 6행 표와 문서 값이 전부 일치합니다.** 어긋난 항목은 없습니다.

### 1-1. 지시서 표현을 한 군데 좁혀야 합니다

지시서는 "**CALB 만** seed 마다 다르다"고 적었습니다. 48행 전수로 세면
그보다 좁습니다.

| 모델 | 도메인 | seed 간 값이 갈리는 항목 |
|---|---|---|
| CPMLP | CALB | `batch_size` `d_model` `d_ff` `e_layers` `d_layers` `dropout` (6) |
| CPTransformer | CALB | `batch_size` `d_model` `e_layers` `d_layers` `dropout` (5) |
| CPGRU | CALB | **없음 — 3 seed 동일** |
| CPLSTM | CALB | **없음 — 3 seed 동일** |
| 4개 모델 | Li-ion · Zn-ion · Na-ion | **없음 — 전부 3 seed 동일** |

- 48행 중 seed 가 값을 가르는 것은 **6행뿐**이고, 나머지 42행은 동일합니다.
- 가르는 것은 도메인이 아니라 **(CALB, CyclePatch-MLP 계열)** 조합입니다.
  같은 CALB 라도 CPGRU · CPLSTM 은 갈리지 않습니다.
- CPTransformer/CALB 는 `d_ff` 가 세 seed 모두 `256` 이라 지시서 표에서
  세어야 할 항목이 6이 아니라 **5** 입니다.
- `learning_rate` 는 CALB 12행 전부 `5e-05` — 지시서 기술과 일치합니다.

이 관찰을 `findings/registry.yaml` 에 **TRN-015** 로 넣었습니다 (§5).

---

## 2. 스크립트 4개 — 이미 문서 값입니다

수정하지 않았습니다. 아래는 **현재 디스크 값**이며 문서와의 대조입니다.

| 파일 | batch | d_model | d_ff | e_layers | d_layers | dropout | seed | dataset |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `CPMLP_CALB_s42.sh` | **8** | 128 | 128 | 7 | 9 | 0.05 | 42 | `CALB42` |
| `CPMLP_CALB_s2024.sh` | **16** | 256 | 128 | 12 | 6 | 0 | 2024 | `CALB2024` |
| `CPTransformer_CALB_s42.sh` | **128** | 256 | 256 | 6 | 7 | 0.05 | 42 | `CALB42` |
| `CPTransformer_CALB_s2024.sh` | **8** | 128 | 256 | 7 | 6 | 0 | 2024 | `CALB2024` |
| `CPMLP_CALB_s2021.sh` (참고) | 16 | 32 | 32 | 12 | 6 | 0.1 | 2021 | `CALB` |
| `CPTransformer_CALB_s2021.sh` (참고) | 16 | 64 | 256 | 9 | 9 | 0.1 | 2021 | `CALB` |

**문서값 일치 여부 · 배치 ×2 여부**

| 파일 | 6개 항목 문서 일치 | 배치 환산 | `--seed` | `--dataset` |
|---|---|---|---|---|
| `CPMLP_CALB_s42.sh` | 일치 | 문서 4 × 2 = **8** ✔ | 42 ✔ | `CALB42` ✔ |
| `CPMLP_CALB_s2024.sh` | 일치 | 문서 8 × 2 = **16** ✔ | 2024 ✔ | `CALB2024` ✔ |
| `CPTransformer_CALB_s42.sh` | 일치 | 문서 64 × 2 = **128** ✔ | 42 ✔ | `CALB42` ✔ |
| `CPTransformer_CALB_s2024.sh` | 일치 | 문서 4 × 2 = **8** ✔ | 2024 ✔ | `CALB2024` ✔ |

여섯 스크립트의 값이 **서로 다릅니다.** "6개가 전부 seed 2021 값"이라면
`batch_size` 가 여섯 다 16 이어야 하는데 8 · 16 · 128 · 8 · 16 · 16 입니다.

`learning_rate` 는 6개 전부 `5e-05` 로 문서와 같습니다. 경로 치환 ·
`CUDA_VISIBLE_DEVICES=0` · `--multi_gpu` 부재 · `num_workers 0` ·
`master_port` 고유성 · 진입점(`run_main_nodeepspeed.py`)은
`make_scripts.py --check` 가 36/36 통과로 확인했습니다.

---

## 3. 재실행하지 않았습니다 — 기존 6회가 이미 문서 설정입니다

`runs/2026-08-04/20260804-152940_*.log` 각 로그 머리의 인자 사전에서
직접 뽑았습니다. 스크립트가 아니라 **실제로 돌아간 프로세스가 받은 값**입니다.

| 로그 | seed | dataset | batch | d_model | d_ff | e_layers | d_layers | dropout | lr | Test MAPE |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|
| `CPMLP_CALB_s42` | 42 | `CALB42` | 8 | 128 | 128 | 7 | 9 | 0.05 | 5e-05 | 0.2461 |
| `CPMLP_CALB_s2021` | 2021 | `CALB` | 16 | 32 | 32 | 12 | 6 | 0.1 | 5e-05 | 0.1385 |
| `CPMLP_CALB_s2024` | 2024 | `CALB2024` | 16 | 256 | 128 | 12 | 6 | 0.0 | 5e-05 | 0.1066 |
| `CPTransformer_CALB_s42` | 42 | `CALB42` | 128 | 256 | 256 | 6 | 7 | 0.05 | 5e-05 | 0.1981 |
| `CPTransformer_CALB_s2021` | 2021 | `CALB` | 16 | 64 | 256 | 9 | 9 | 0.1 | 5e-05 | 0.3101 |
| `CPTransformer_CALB_s2024` | 2024 | `CALB2024` | 8 | 128 | 256 | 7 | 6 | 0.0 | 5e-05 | 0.1051 |

**여섯 행 전부 §1 문서 표와 일치합니다** (배치는 문서값 ×2).

그리고 오른쪽 끝 MAPE 6개가 지시서가 "이전 (seed2021 설정 고정)" 열에
적어 둔 값 — 0.2461 · 0.1385 · 0.1066 · 0.1981 · 0.3101 · 0.1051 —
**과 정확히 같습니다.**

즉 지시서가 "이전"이라 부른 그 숫자들이 이미 **"이후"** 입니다. 두 조건이
아니라 한 조건이며, 비교표의 두 열이 같은 열입니다.

### 3-1. 전후 비교표 · 표준편차 비교를 내지 않았습니다

| 모델 | seed | 이전 (지시서) | 이후 (재실행) | 논문 |
|---|---|---:|---|---:|
| CPMLP | 42 | 0.2461 | — 실행 안 함 (설정 동일) | |
| CPMLP | 2021 | 0.1385 | 변화 없음 | |
| CPMLP | 2024 | 0.1066 | — 실행 안 함 (설정 동일) | 0.140 ± 0.009 |
| CPTransformer | 42 | 0.1981 | — 실행 안 함 (설정 동일) | |
| CPTransformer | 2021 | 0.3101 | 변화 없음 | |
| CPTransformer | 2024 | 0.1051 | — 실행 안 함 (설정 동일) | 0.149 ± 0.005 |

3회 평균 ± 표준편차는 이전 값이 그대로 유지됩니다.

| 모델 | 이전 | 이후 | 논문 |
|---|---|---|---|
| CPMLP · CALB | 0.164 ± 0.073 | **변화 없음** | 0.140 ± 0.009 |
| CPTransformer · CALB | 0.204 ± 0.103 | **변화 없음** | 0.149 ± 0.005 |

지시서 §4 가 보려던 것 — **"표준편차가 줄어드는가"** — 은 이 방식으로는
답이 나오지 않습니다. 줄어들 여지가 있으려면 두 설정이 실제로 달라야 하는데
같은 설정이라 차이가 0 입니다. 흩어짐의 원인을 가리는 근거로 쓸 수 없습니다.

**해석은 적지 않습니다.** 다만 지시서가 이 관찰에서 결론을 유도하려 했으므로,
그 유도가 성립하지 않는다는 사실만 남깁니다.

---

## 4. `make_scripts.py` — 이미 (모델, 도메인, seed) 로 조회합니다

수정하지 않았습니다. 조회 키가 처음부터 3튜플입니다.

- `train/make_scripts.py:153` — 파싱: `table[(row["model"], row["dataset"], row["seed"])]`
- `train/make_scripts.py:320` — 생성: `doc_row = doc.get((model, combo["domain"], seed))`
- `train/make_scripts.py:433` — 측정 사본: `doc_row = doc.get(key)`, `key = (model, domain, seed)`
- `train/make_scripts.py:490` — 검증: `doc.get((combo["model"], combo["domain"], combo["seed"]))`

seed 를 빠뜨린 2튜플 조회는 파일에 없습니다. `git log -- train/make_scripts.py`
에도 그런 상태로 커밋된 이력이 없습니다.

### 재생성 diff

`.build/batterylife/` 를 스크래치패드에 통째로 복사한 뒤 재생성하고
`diff -r` 했습니다.

```
$ PYTHONPATH=. python train/make_scripts.py
master_port 고유: 36/36
통과 36/36

$ diff -r <backup> .build/batterylife
(차이 없음)
```

**36개 전부 바이트 단위로 동일합니다.** CALB 4개를 포함해 달라진 파일이
하나도 없습니다 — 생성기가 이미 옳은 값을 내고 있었다는 뜻입니다.

재생성 부작용이 하나 있어 되돌렸습니다: `_stash_old()` 의 `keep` 집합에
`run_domain.sh` 가 없어 이 파일이 `_old_shellparam/` 으로 한 번 옮겨졌다가
다시 쓰입니다. 최상위 `run_domain.sh` 는 내용이 같고 `_old_shellparam/`
쪽 사본만 늘어나므로, 지우고 백업과 동일함을 재확인했습니다. **결함이라기보다
재생성할 때마다 사본이 하나 쌓이는 성질**이며 이번 지시 범위 밖이라
`make_scripts.py` 는 손대지 않았습니다.

---

## 5. 갱신한 문서

| 문서 | 한 일 |
|---|---|
| `findings/registry.yaml` | **TRN-015 신규.** §1-1 의 전수 집계를 `upstream_doc` 슬롯에 관찰로 기록. `verdict` 는 쓰지 않았고 `render.py` 가 **미정**으로 유도했습니다 (`code` 미조사) |
| `findings/PAPER_CODE_MAP.md` | `run.py claims` 재생성 (파생물) |
| `docs/OPEN_QUESTIONS.md` | `run.py claims` 재생성 (파생물) |
| `docs/reports/2026-08-04_calb_seed_hp.md` | 이 문서 |

`run.py claims` 결과: **레코드 50개 · 기록 요건 위반 없음.**

### 갱신하지 **않은** 문서와 이유

| 문서 | 지시 | 하지 않은 이유 |
|---|---|---|
| `docs/PLAN.md` §7-3 | CALB 열 갱신 | 이미 옳습니다. 표의 CALB 6개 값이 §3 로그 MAPE 와 같고, 그 로그가 문서 설정으로 돈 것입니다 |
| `LOCK.md` | 해당 산출물 해시 재계산 | 산출물이 바뀌지 않았습니다. 재계산하면 같은 해시가 나오고, 커밋만 남아 무언가 바뀐 것처럼 읽힙니다 |
| `experiments/results/table3/` | 갱신 | 이 디렉터리는 존재하지 않습니다. Table 3 대조표는 `docs/PLAN.md` §7-3 이 유일한 자리입니다 |
| `experiments/results/prev_calb_seed2021hp/` | 기존 결과 이관 | 이관할 것이 없습니다. `experiments/results/` 에 CALB 학습 산출물이 없고(`train_metrics.json` 은 smoke · timing36 4건뿐), 있었다 해도 잘못된 조건의 것이 아닙니다 |
| `runs/prev_calb_seed2021hp/` | CALB 로그 이관 | 같은 이유. `runs/2026-08-04/` 의 CALB 로그 6개는 **정상 결과**이며 §7-3 의 근거입니다. 옮기면 §7-3 의 출처 표기가 끊깁니다 |

---

## 6. 실패한 것 · 판단이 필요한 것

**실패한 것은 없습니다.** 검증은 전부 완료했습니다.

**판단이 필요한 것 셋.**

1. **지시서의 전제가 어디서 왔는지 확인되지 않았습니다.** "현재 6개
   스크립트가 전부 seed 2021 값으로 만들어져 있다"는 진술의 근거를
   저장소에서 찾지 못했습니다. 디스크 · git 이력 · 실행 로그 셋 다
   그렇지 않습니다. 다른 작업 트리나 이전 세션의 기억이라면 그쪽을
   확인해 주십시오 — 저장소 상태와 어긋납니다.

2. **CALB 표준편차 문제는 그대로 열려 있습니다.** 이번 작업이 그 원인을
   가리는 데 기여하지 못했습니다. CPMLP 0.073 · CPTransformer 0.103 은
   논문(0.009 · 0.005)보다 한 자릿수 큽니다. 하이퍼파라미터 축은
   여기서 배제되었으므로, 남은 축은 27셀 분할 3벌의 차이 · 조건 차이
   (deepspeed 부재 · 단일 GPU · fp32) · seed 자체입니다. 어느 쪽을
   먼저 볼지는 사람이 정할 일입니다.

3. **TRN-015 의 `code` 슬롯을 미조사로 두었습니다.** 배포 셸 스크립트는
   조합 하나의 흔적이라(TRN-007) 이 질문에 대응하는 코드측 주장이
   없습니다. 판정은 **미정**입니다. 이 레코드를 upstream_doc 단독
   관찰로 닫을지, 아니면 "왜 그 여섯 행만 갈리는가"를 논문 부록에서
   찾아 `paper` 슬롯을 채울지는 결정이 필요합니다.

**`git add` 만 했고 커밋 · 태그 · 푸시는 하지 않았습니다.**
