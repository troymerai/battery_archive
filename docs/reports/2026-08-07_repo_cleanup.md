# 워킹 트리 정리 — 작업 보고

2026-08-07 · CC · 파일 수정·이동·생성·검증까지. **커밋·태그·push 하지 않았습니다.**

모든 사실 주장에 `[확인]`(직접 실행·열람으로 검증) / `[추론]`(정황 추정) /
`[미확인]` 을 붙입니다.

---

## ★ 한 줄

정리는 끝났으나 **`python run.py check` 는 여전히 실패합니다.** 코드 층 3건이고,
그중 둘은 이번 정리가 만든 것이 아니라 **원래 깨져 있던 것**입니다. 그리고
지시가 복구 수단으로 지목한 `lock-init` 은 **이 문제를 고칠 수 없는 명령**입니다
(§8). 남은 결정 3건을 §10 에 올립니다.

| 완료 조건 | 결과 |
|---|---|
| 루트에 `CC_REPORT.md` 가 없다 | **충족** `[확인]` |
| `docs/OPEN_QUESTIONS.md` 의 불일치가 6건 | **미충족 — 5건 그대로.** 사유 §5 |
| `run.py check` 전 층 통과 | **미충족 — 코드 층 3건 FAIL.** 원인 §8 |
| 인덱스가 비어 있다 | **충족** `[확인]` — `git add` 를 한 번도 실행하지 않았습니다 |

---

## 0. 전제 확인 `[확인]`

`git log --stat -3` 으로 지시가 전제한 커밋을 확인했습니다.

| 커밋 | 내용 | 확인 |
|---|---|---|
| `3815325` | 학습 곡선 58건 · 그림 6종 + CONDITIONS.md · train 스크립트 3개 · 보고서 5건 = **73파일 25,473행** | 일치 |
| `3f7d62b` | TRN-015 3종 (`registry.yaml` · `PAPER_CODE_MAP.md` · `OPEN_QUESTIONS.md`) | 일치 |

작업 시작 시 미추적은 루트 `CC_REPORT.md` 와 `analysis/` 뿐이었고 인덱스는
비어 있었습니다 `[확인]`.

---

## 1. `.gitignore` 갱신

`analysis/out/` **한 줄만** 추가했습니다.

지시는 세 줄을 요구했으나 나머지 둘은 **넣지 않았습니다.**

| 지시된 규칙 | 처리 | 사유 |
|---|---|---|
| `analysis/out/` | **추가함** | 전량 재생성 검증 완료 (§2) |
| `analysis/*_cycle_scan.csv` | **버림** | 재생성 불가 판정 (§2-2). 지시 자신이 "재생성이 안 되면 제외 결정을 보류한다" 고 적었습니다 |
| `analysis/*_cell_meta.csv` | **버림** | 위와 같음. 추가로 이 패턴은 너무 넓습니다 — §10-B |

`analysis/__pycache__/` 는 기존 `__pycache__/` 규칙에 이미 걸립니다 `[확인]`.

> **최종형 (후속 지시 반영).** 패턴 둘을 버리고
> **`analysis/li_ion_cycle_scan.csv` 파일명 한 줄**로 바꿨습니다. 최상위 CSV
> 10개 중 **9개를 커밋**하고 185 MB 하나만 제외합니다. 근거는 §10-B 와 §11.

---

## 2. 재생성 가능성 검증 — 2단계

### 2-1. `analysis/out/` 14개 — **전량 재생성 확인** `[확인]`

기존 산출물을 세션 스크래치패드에 백업한 뒤, 8개 스크립트를 **의존 순서대로 전부
다시 실행**해 덮어쓰고 sha256 을 대조했습니다. **14/14 비트 단위 일치** 입니다.

| 산출물 | 스크립트 | 판정 |
|---|---|---|
| `reported_table.json` | `reported_table.py` | MATCH |
| `cell_meta.csv` | `extract_cell_meta.py` | MATCH |
| `domain_stats.json` · `hist_*.png` 5장 | `domain_discriminability.py` | MATCH (6/6) |
| `conditions_reported.json` | `conditions_and_reported.py` | MATCH |
| `discriminability.json` · `.md` | `discriminability_table.py` | MATCH (2/2) |
| `condition_mean_baseline.json` | `condition_mean_baseline.py` | MATCH |
| `diversity.json` | `diversity_breakdown.py` | MATCH |
| `label_filter_recount.csv` | `recount_label_filters.py` | MATCH |

근거 해시(무거운 둘):

```
cell_meta.csv             29b5d7ae7a2a991d8c472f273d803f374214df482f76ad9b8b5dc4c3f52a2183
label_filter_recount.csv  811b005e6d29e017039c1de59171430977bd0405af3885def8452d4f870132be
```

**PNG 5장도 바이트 단위로 같았습니다** `[확인]`. matplotlib 3.8.4 기준이며 다른
판본에서도 같다고는 말하지 못합니다 `[미확인]`.
`condition_mean_baseline.py` 의 부트스트랩 1,000회는 `np.random.default_rng(1)`
로 씨앗이 박혀 결정적입니다 `[확인]`.

실측 소요 — pkl 1,440개를 여는 둘이 사실상 전부입니다.

| 스크립트 | 소요 |
|---|---:|
| `extract_cell_meta.py` | 6분 37초 (17:08:24 → 17:15:01) |
| `recount_label_filters.py` | 5분 20초 (17:15:01 → 17:20:21) |
| 나머지 6개 합계 | 7초 |

### 2-2. `analysis/*.csv` 10개 — **재생성 불가** `[확인]`

> **§11 이 이 절을 부분적으로 뒤집습니다.** 여기 "재생성 불가" 는 *스크립트가
> 없다* 는 뜻이고, 그 뒤 원인을 파고들어 **`li_ion_cycle_scan.csv` 는 pkl 에서
> 다시 계산되는 캐시**임을 확인했습니다. 나머지 9개는 여전히 저장소가 유일한
> 사본이라 커밋합니다. 아래 표의 판정은 **진단 이전 상태**로 남겨 둡니다.

**이 10개(합계 188.7 MB)를 만드는 스크립트가 저장소에 없습니다.**

근거 셋:

1. `analysis/*.py` 8개의 출력 경로를 전수로 읽었고 **전부 `analysis/out/` 아래**
   입니다 `[확인]`.
2. 저장소 전체에서 `cycle_scan` 을 찾으면 **보고서 본문에서만** 나오고 코드에서는
   안 나옵니다 `[확인]`.
3. 보고서 자신이 이 파일들을 **"재사용 캐시"** 라 부르고
   (`2026-08-06_li_ion_temporary_crossing.md:43`), 그 조사는 원본 `.pkl` 을
   **0건 개봉**했다고 적습니다 `[확인]`.

즉 2026-08-06 조사의 **저장되지 않은 일회성 코드**가 만든 것입니다.

| 파일 | 크기 | 행 | sha256[:16] | 판정 |
|---|---:|---:|---|---|
| `li_ion_cycle_scan.csv` | 185,391,825 B | 1,846,308 | `f63db8690cf5eaf4` | 재생성 불가 · **커밋 불가**(100 MiB 한계) |
| `na_ion_cycle_scan.csv` | 2,588,049 B | 12,604 | `cfa6d89931579ae9` | 재생성 불가 |
| `li_ion_cell_meta.csv` | 489,055 B | 884 | `f7063a44cad2e6d3` | 재생성 불가 |
| `li_ion_label_vs_soh.csv` | 151,793 B | 839 | `4e6250a30e2c20d9` | 재생성 불가 |
| `li_ion_temporary_crossing.csv` | 15,924 B | 107 | `396f95bf2a4f3d43` | 재생성 불가 |
| `na_ion_cell_summary.csv` | 8,555 B | 64 | `10c63fec6b02c771` | 재생성 불가 |
| `na_ion_label_vs_soh.csv` | 7,642 B | 64 | `27ccd316ff06d6e1` | 재생성 불가 |
| `na_ion_cell_meta.csv` | 4,970 B | 64 | `42c90bf81f1967c6` | 재생성 불가 |
| `na_ion_detector_grid.csv` | 2,640 B | 80 | `8399a2af07cf5fe0` | 재생성 불가 |
| `na_ion_drop_events.csv` | 457 B | 4 | `d7b6361d2206a7e4` | 재생성 불가 |

행 수가 보고서 서술과 전부 교차 검증됩니다 — `1,846,308` · `12,604` · `884` ·
`107`(일시적 교차 셀) · `4`(급락 셀) `[확인]`.

**어떤 파일도 지우지 않았습니다.** 전부 디스크에 그대로 있습니다.
Git LFS / 외부 보관 결정은 §10-A 로 올립니다.

---

## 3. `analysis/README.md` 신규 작성

지시된 열(파일명 / 생성 스크립트 / 명령 / 크기 / 커밋 권장 / 재생성 검증)을 담고,
§1 은 재생성되는 것, §2 는 **재생성 불가로 지우면 안 되는 것**으로 나눴습니다.
의존 순서(`cell_meta.csv` → `diversity.json`, `reported_table.json` →
`discriminability.*`)도 적었습니다.

---

## 4. `CC_REPORT.md` 이동 `[확인]`

`docs/reports/2026-08-06_na_ion_soh_drop.md` 로 옮기고 루트 파일을 지웠습니다.

- **본문은 한 글자도 고치지 않았습니다.**
- 두 겹으로 쌓여 있던 "이전 내용을 옮겼다" 메모는 `[원문 유지]` 표시를 붙여
  **인용 블록으로 보존**했습니다.
- 문서 맨 앞에 이동 경위와, 루트 파일을 거쳐 간 세 조사의 순서표를 붙였습니다.

루트 `CC_REPORT.md` 를 세 조사가 차례로 덮어쓴 흔적이 남아 있었습니다 —
README 가 금지한 이유가 실제로 발생했다는 증거입니다 `[확인]`.

---

## 5. 유형 H 등록 — `DAT-004`. **판정은 `미정` 이고 불일치는 6건이 되지 않습니다**

### 5-1. 등록한 것

`findings/registry.yaml` 에 `DAT-004` 를 추가했습니다. 기존 DAT 는 001~003 이라
충돌이 없습니다 `[확인]`.

| 슬롯 | 상태 | 근거 |
|---|---|---|
| `paper` | **미조사** | 원 보고서 512행이 논문 대조를 "이번 조사 범위 밖" 으로 명시 |
| `upstream_doc` | **확인** | `assets/Further_details_of_processed_charge_and_discharge_capacity_data.md` — NA-ion 은 **Format 2**, "충전·방전 용량이 서로 다른 열에 기록된다" |
| `code` | **확인** | `preprocess_NA.py:42-43` — 단일 `Capacity/Ah` 를 두 열에 각각 대입 |

코드 근거는 레코드를 쓰면서 직접 열어 재확인했습니다 `[확인]`.
셀 범위도 재측정했습니다 — NA-ion pkl 64개 중 두 열이 **전 사이클 100% 동일 5셀 ·
0% 동일 59셀 · 부분 동일 0셀** 로 보고서와 같았습니다 `[확인]`.

### 5-2. 왜 불일치가 되지 않는가 — 지시의 완료 조건과 어긋납니다

지시는 "불일치가 5건 → 6건이 되는지 확인" 하라고 적었습니다. **되지 않았습니다.
5건 그대로입니다** `[확인]`.

`verify/render.py:84-122` 의 `derive_verdict()` 는 **`paper` × `code` 로만**
판정을 유도합니다. `upstream_doc` 은 보조 근거라 판정에 들어가지 않습니다 —
docstring 이 명시합니다: *"상위 저장소 README 는 논문도 코드도 아니어서, 여기
있는 서술이 논문 근거를 대신할 수 없습니다."* `SCHEMA.md` 41-43행도 같습니다.

따라서 `paper=미조사` × `code=확인` → **`미정`** 입니다.

**불일치로 만들려면 논문 슬롯을 `확인` 으로 적어야 하는데, 그러려면 없는 `locus`
를 지어내야 합니다.** 그것은 이 저장소가 금지한 바로 그 행위이며(`실패: 미조사를
조사했으나불명으로 말함`), `run.py claims` 도 `확인` 인데 `locus` 가 없으면
위반으로 잡습니다 `[확인]`.

**그래서 미정으로 두었습니다.** 값이 커 보이는 발견이라도 논문 근거를 안 찾아본
것은 안 찾아본 것입니다. 이 레코드를 불일치로 올리는 일은 논문에서 용량 열의
의미를 규정한 곳을 찾은 뒤에 자동으로 됩니다.

> **다만 이 발견의 무게는 판정보다 큽니다.** 상위 문서가 NA-ion 을 "서로 다른
> 열" 이라 적어 놓고 코드가 한 열을 두 번 쓰는 것은 **문서 대 코드의 명백한
> 어긋남**입니다. 판정 표에 안 뜬다고 작은 일이 아닙니다 — 논문 집필 때
> `DAT-004` 의 `upstream_doc` 슬롯을 반드시 읽으십시오.

### 5-3. 파급

`Extract_life_labels.py:120` 이 `max(last_cycle['discharge_capacity_in_Ah'])` 로
SOH 를 재므로, 이 5셀에서는 방전 용량이 아니라 **그 사이클의 용량 카운터
최댓값(실질 충전 용량)** 이 분모 계산에 들어갑니다 `[확인]`.

앵커는 만들지 않았습니다. `findings/anchors.yaml` 은 LOCK 잠금이 **유일하게 살아
있는** findings 파일이라(§8) 이번 범위에서 건드리지 않았습니다.

`python run.py claims` 재생성 결과: 레코드 51개 · **기록 요건 위반 없음** `[확인]`.

---

## 6. 문서 최신화

### 6-1. `docs/PLAN.md` §7-1 · §7-2

`experiments/results/table3/` 를 실제 경로로 고쳤습니다. 코드로 확인한 실제
출력처는 이렇습니다 `[확인]`.

| 산출물 | 실제 경로 | 근거 |
|---|---|---|
| 지표 | `experiments/results/train_metrics.json` | `train/collect.py:159` 의 기본값 |
| 에폭별 곡선 | `experiments/results/curves/<모델>_<도메인>_s<seed>[__<태그>].json` | `train/curves.py:24` |

옛 경로를 기억하고 찾아올 사람을 위해 **정정 문단을 남겼습니다** — 지우면
`2026-08-04_calb_seed_hp.md:202` 의 지적이 무엇을 가리켰는지 알 수 없게 됩니다.
`group` 필드 함정 경고도 함께 넣었습니다.

### 6-2. `README.md` 「구조」

`figures/` 와 `analysis/` 두 줄을 추가하고, 지시대로 `figures/` 에 **"정본
판별은 파일명이 아니라 `group` 필드 — Zn-ion 은 접미사 없는 쪽이 diagnostic"**
경고를 넣었습니다. `analysis/out/` 이 커밋되지 않는다는 것과
`analysis/README.md` 로 가는 길도 적었습니다.

---

## 7. LOCK 불일치 경위 기록

`docs/reports/2026-08-07_lock_drift.md` 에 별도로 적었습니다. 요약만 옮깁니다.

- **깨진 시점: `48d086c` (2026-08-04).** 마지막으로 성립한 커밋은 `1f1d248` `[확인]`
- 전 이력 8커밋을 저장소 자신의 `sha256_file()` 로 재계산해 표로 만들었습니다
- 그 기간에 **레코드 18개**가 잠금 밖에서 들어왔습니다 (32개 → 50개) `[확인]`
- `findings/anchors.yaml` 은 `d73aa1a3…` 로 **전 기간 무사** `[확인]`
- **`c4cbc6b` 는 제목이 `lock: train session 1` 이면서 잠금 두 행을 동시에
  깨뜨렸습니다** — `verify/ tree` 와 `registry.yaml` `[확인]`

---

## 8. 잠금 복구 — **실행하지 않았습니다.** `lock-init` 이 고칠 수 없는 문제입니다

### 8-1. 먼저 환경을 확정했습니다 `[확인]`

`lock-init` 은 현재 인터프리터의 `pip freeze` 를 `manifests/env_lock/repro.txt`
에 **덮어씁니다**(`verify/lock.py:316-319`). 그래서 어느 인터프리터가 라벨 검증
환경인지부터 확정했습니다.

| 후보 | 판정 |
|---|---|
| `C:\msys64\ucrt64\bin\python.exe` | **아님** — `pip freeze` 0줄. Git Bash 의 기본 `python` 이 이것이라 위험합니다 |
| `C:\Users\taeyo\AppData\Local\Programs\Python\Python312\python.exe` | **라벨 검증 환경** — `pip freeze` 127줄이 `repro.txt` 와 **완전 일치** |
| `.venv-blife\Scripts\python.exe` | 학습 환경 (`blife.txt`) |

`check` 는 이 Python312 로 돌렸습니다.

### 8-2. `run.py check` 전문 `[확인]`

```
=== LOCK 대조 =====================================================
[ FAIL ] upstream/BatteryML tree         코드/digest
                                         기준 7368a9cdc0c375bb7a9ec9a548a7118279a997e1a35e0c245283fa7003c8bca4
                                         실제 e1e948ca84d1addd2b5b6f684c4a18c937b0bcb2db5184d3b587a44cbe288621
[  ok  ] upstream/BatteryLife tree       코드/digest
[  ok  ] upstream/BatteryMFormer commit  코드/digest
[ FAIL ] verify/ tree                    코드/digest
                                         기준 7909f0381cc103705198335ad6ec1c9e16c51c75e3ca4547e400b1a8ac995baa
                                         실제 fbeb9c95ce91a58cf3d4f0b3382f23c159917ca2ae6a1b8883e608c17e3e153c
[  ok  ] CALB.zip                        데이터/digest
[  ok  ] CALCE.zip                       데이터/digest
[  ok  ] HNEI.zip                        데이터/digest
[  ok  ] HUST.zip                        데이터/digest
[  ok  ] ISU_ILCC.zip                    데이터/digest
[  ok  ] Life labels.zip                 데이터/digest
[  ok  ] MATR.zip                        데이터/digest
[  ok  ] MICH.zip                        데이터/digest
[  ok  ] MICH_EXP.zip                    데이터/digest
[  ok  ] NA-ion.zip                      데이터/digest
[  ok  ] READMEs.zip                     데이터/digest
[  ok  ] RWTH.zip                        데이터/digest
[  ok  ] SDU.zip                         데이터/digest
[  ok  ] SNL.zip                         데이터/digest
[  ok  ] Stanford.zip                    데이터/digest
[  ok  ] Stanford_2.zip                  데이터/digest
[  ok  ] Tongji.zip                      데이터/digest
[  ok  ] UL_PUR.zip                      데이터/digest
[  ok  ] XJTU.zip                        데이터/digest
[  ok  ] ZN-coin.zip                     데이터/digest
[  ok  ] env repro                       환경/digest
[  ok  ] env blife                       환경/digest
[  ok  ] nb01 재집계 recount.json           결과/digest
[  ok  ] nb02 변형 비교                      결과/digest
[  ok  ] nb03 셀 단위 대조표                   결과/digest
[  ok  ] nb03 no_soc_span 변형             결과/digest
[  ok  ] nb03 discharge_denom 변형         결과/digest
[  ok  ] nb03 도메인 롤업 표                   결과/digest
[  ok  ] nb03 불일치 셀 목록                   결과/digest
[  ok  ] nb03 라벨없음(비유한) 셀 목록             결과/digest
[  ok  ] nb04 cycle_number 롤업            결과/digest
[  ok  ] nb04 셀별 추가 측정                   결과/digest
[  ok  ] nb05 v2 대조표 원자료                 결과/digest
[  ok  ] findings/na_ion_crate.json      결과/digest
[ FAIL ] findings/registry.yaml          코드/digest
                                         기준 48bc03c2ee7d8c8410eaa8fd9df312ef6a94655bfc324c03ea24e78775c7e502
                                         실제 0189fcf0ace96bca79c6c9b68576aa32ed5fb4b574ceb7493d85195a4f0223e8
[  ok  ] findings/anchors.yaml           코드/digest
[ 구간 ] CPTransformer Li-ion MAPE       결과/interval
                                         기준 0.197 ± 0.019  (3 seed(2021·42·2024) 평균±표준편차. 하드웨어 의존 — `manifests/hardware.txt` 참조)
[ 구간 ] CPTransformer Li-ion 15%-Acc    결과/interval
                                         기준 55.7 ± 4.5  (백분율. 3 seed 평균±표준편차. 하드웨어 의존 — `manifests/hardware.txt` 참조)

어긋난 층: 코드
- 코드: 상위 저장소나 verify/ 가 달라졌습니다. 커밋을 확인하십시오 (manifests/upstream_commits.txt).
```

**데이터 층 zip 20개 · 환경 층 2개 · 결과 층 13개는 전부 통과합니다.**
어긋난 것은 코드 층 3건뿐입니다.

### 8-3. 셋의 성격이 다릅니다

| FAIL | 진단 | 근거 |
|---|---|---|
| `upstream/BatteryML tree` | **오탐.** 상위 코드는 안 바뀜 | `BatteryML.egg-info/` 하나만 빼고 재계산하면 기준값 `7368a9cd…` 가 **정확히 재현**됩니다 `[확인]` |
| `verify/ tree` | 진짜 드리프트 | `c4cbc6b` 가 `check_841.py` 230행을 추가하고 LOCK 을 안 고침 `[확인]` |
| `findings/registry.yaml` | 진짜 드리프트 | `48d086c` 이후 레코드 18개 + 이번 `DAT-004` `[확인]` |

`upstream/BatteryML` 은 **읽기 전용 규칙이 지켜졌습니다.** 어긋난 원인은
`pip install -e` 가 만든 빌드 부산물 24 KB 이고, `tree_digest()` 의 제외 목록
(`verify/__init__.py:59-66`)에 `*.egg-info` 가 없어서 걸린 것입니다.

### 8-4. `lock-init` 을 돌리지 않은 이유 `[확인]`

`verify/lock.py:333-335` 는 **`(미정)` 인 행만** 채웁니다. 값이 있으면 건너뜁니다.
docstring 이 이유를 적습니다 — *"이미 값이 들어 있는 행은 건드리지 않습니다.
기준값을 덮어쓰면 '모두가 같은 것을 본다' 가 무너집니다. 값을 바꿔야 한다면 새
태그를 찍으십시오."*

그리고 **`LOCK.md` 표 42행에 `(미정)` 이 하나도 없습니다** `[확인]`.

따라서 지금 `lock-init` 을 돌리면 **채우는 행 0개 · 고쳐지는 FAIL 0건**,
실제로 일어나는 일은 `repro.txt` 덮어쓰기 하나뿐입니다. **효과 없이 부작용만
남습니다.** 지시가 "임의로 우회하지 말라" 고 했으므로 실행하지 않고 올립니다.

---

## 9. 건드리지 않은 것 (절대 규칙 준수) `[확인]`

| 규칙 | 준수 |
|---|---|
| `git commit` · `tag` · `push` · **`add` 금지** | 한 번도 실행하지 않음. 인덱스 비어 있음 |
| `upstream/` 무수정 | 무수정. `BatteryML tree` FAIL 은 빌드 부산물 탓임을 §8-3 에서 증명 |
| `Transformer.py` AttributeError 무수정 | 열지 않음 |
| `group: superseded` 5건 무삭제 | 무삭제. 58건 그대로 |
| 파일명 아닌 `group` 으로 판별 | `curves/*.json` 을 파싱해 main 36 / diagnostic 17 / superseded 5 로 확인 |
| `torch` 무재설치 | 설치 명령 실행 안 함 |
| `lock-init` 을 `.venv-blife` 에서 금지 | 실행 자체를 안 함. 환경은 §8-1 에서 확정만 |
| 루트 `CC_REPORT.md` 무생성 | 이 보고서는 `docs/reports/2026-08-07_repo_cleanup.md` |
| 185 MB CSV 커밋 제안 금지 | 제안하지 않음. 커밋 안내에서 명시 제외 |

---

## 10. 판단이 필요했으나 지시에 없던 사항 — **임의로 정하지 않았습니다**

### A. 재생성 불가 CSV 의 보관 방식 — **해결됨 (2026-08-07 후속)**

사용자 지시로 **9개를 커밋하고 `li_ion_cycle_scan.csv` 하나만 보류**로
확정했습니다. 그리고 §11 의 원인 진단으로 **그 하나가 캐시임이 밝혀져** 보류의
위험이 사라졌습니다. Git LFS / 외부 보관은 지금 정하지 않아도 됩니다.

### B. `.gitignore` 패턴 — **해결됨.** 파일명으로 못박았습니다

`analysis/*_cell_meta.csv` 는 `na_ion_cell_meta.csv`(**4,970 B**) 까지 잡고,
`analysis/*_cycle_scan.csv` 는 `na_ion_cycle_scan.csv`(2.5 MB) 까지 잡습니다.
크기 때문에 빼려던 것이 아닌데 같이 빠집니다.

**그래서 패턴을 버리고 `analysis/li_ion_cycle_scan.csv` 한 줄로 바꿨습니다.**
검증했습니다 `[확인]`:

```
analysis/li_ion_cycle_scan.csv    제외됨
analysis/na_ion_cycle_scan.csv    커밋대상
analysis/li_ion_cell_meta.csv     커밋대상
analysis/na_ion_cell_meta.csv     커밋대상
analysis/out/cell_meta.csv        제외됨
```

### C. `upstream/BatteryML tree` 오탐을 어떻게 고치는가

`_TREE_EXCLUDE_DIRS` 에 `*.egg-info` 를 넣는 것이 맞아 보이지만 `verify/` 수정이라
`verify/ tree` 기준값이 또 바뀝니다 `[추론]`. 잠금 갱신과 순서가 얽혀 이번 범위
밖으로 두었습니다.

### D. 세 FAIL 의 기준값 갱신 — 새 태그가 필요합니다

`lock.py` 가 기준값 덮어쓰기를 의도적으로 자동화하지 않았으므로(§8-4), 셋 다
사람이 `LOCK.md` 를 직접 고쳐야 합니다. 그리고 그 모듈의 지침대로라면 **기준값을
바꾸는 것은 새 태그를 찍는 일**입니다. `pre-label-swap` 태그를 이 갱신 **뒤에**
찍을지 **앞에** 찍을지가 갈립니다.

### E. 재발 방지 (§7 보고서 §7)

`registry.yaml` 은 `run.py claims` 로 자주 바뀌는데 digest 로 잠겨 있어 구조적으로
어긋나기 쉽습니다. `claims` 끝에 "LOCK 의 registry digest 가 낡았습니다" 경고를
붙이는 것이 가장 싼 방어로 보입니다 `[추론]`. 구현하지 않았습니다.

---

## 11. 후속 — `li_ion_cycle_scan.csv` 원인 진단 (a)(b)(c)

2026-08-07 추가 지시. **먼저 지시의 전제를 하나 바로잡습니다.**

지시 (a) 는 "재생성 **실패**의 원인" 을 묻고 비결정성 / 입력·스크립트 변경 /
실제 내용 차이 셋 중에서 고르라고 합니다. **셋 다 아닙니다.** 재생성을 시도해
결과가 어긋난 것이 아니라 **생성 스크립트가 없어 시도 자체를 못 했습니다.**
§2-2 의 판정은 "돌렸더니 달랐다" 가 아니라 "돌릴 것이 없다" 였습니다.

그래서 진단하려면 스캐너를 **새로 써야** 했고, 그렇게 했습니다.

### (a) 원인 — 스크립트 유실이며, 논리는 대부분 복원됩니다 `[확인]`

산출물 CSV 를 역산해 스캐너를 새로 쓰고, 전 13개 서브셋에서 셀 2개씩
**26셀 · 14,899행**으로 대조했습니다.

| 열 | 재현 | 정의 |
|---|---|---|
| `cycle_number` `n_points` | **완전** | 사이클 번호, `len(voltage_in_V)` |
| `dis_ah_max` `chg_ah_max` | **완전** | `max(discharge/charge_capacity_in_Ah)`, 6자리 반올림 |
| `v_min` `v_max` `i_min` `i_max` | **완전** | 전 구간 min/max, 5자리 반올림 |
| `dis_points` `dis_duration` `v_end_dis` | **미확정** | 방전 **구간**의 점 수 · 시간폭 · 끝 전압 |

전열 일치율:

| 가설 | 일치 |
|---|---:|
| 방전 = `I<0` 의 **최장 연속 구간** | **90.295%** |
| 방전 = `I < -0.01` | 81.173% |

**결론: 원인은 비결정성도, 입력 변경도, 내용 차이도 아닙니다.**
생성 규칙이 어디에도 적히지 않았고, 산출물만 보고는 **방전 구간을 어떻게
고르는지** 를 유일하게 복원할 수 없습니다. 두 가설이 같은 셀에서 갈리는데
어느 쪽이 원본인지 가릴 근거가 없습니다.

진단 중 확인한 부수 사실 `[확인]`:

- Li-ion **884셀 전부 `disc_sign = -1`** — 방전이 음전류입니다. 전류 부호의
  단순 다수결로 판정하면 **뒤집힙니다**(충전 점이 더 많음). `dQd>0` 인 점의
  전류 부호로 재야 합니다. 처음에 이걸 틀려 일치율이 17.9% 로 나왔습니다.
- 열마다 반올림 자릿수가 다릅니다 — 용량 6자리, 전압·전류 5자리, 시간 4자리.
- 행 순서는 알파벳도, `glob` 도, `data_split_recorder` 의 분할 순서도
  아닙니다. **무엇인지 밝히지 못했습니다** `[미확인]`.

부분 재구성을 **`analysis/rebuild_cycle_scan.py`** 로 남겼습니다. 한계를
docstring 에 그대로 적었고, 원본을 덮지 않도록 `analysis/out/` 에 씁니다.

### (b) 파생 요약은 재현 불가 3열에 **의존하지 않습니다** `[확인]`

지시의 판정 기준은 "파생 요약이 일치하면 원시 스캔은 캐시" 였습니다.
sha256 동일 비교는 **성립하지 않습니다** — 파생 요약을 만든 스크립트도 저장되지
않아, 비교하려면 그 파생 논리까지 새로 써야 하고 그러면 부동소수점 표기
하나까지 맞춰야 합니다. 그래서 **더 강한 검사**를 했습니다.

두 파생 요약의 열을 전수로 읽으면 값이 전부 **SOH 에서** 나옵니다.

| 파일 | 값의 출처 |
|---|---|
| `li_ion_label_vs_soh.csv` | `soh_at_label` `soh_before` `max_soh_after` `first/last_crossing` — 전부 SOH 수열 |
| `li_ion_temporary_crossing.csv` | `soh_before` `soh_at_label` `drop1` `max_soh_after` `ratio` — 전부 SOH 수열 |

그리고 SOH 는 `dis_ah_max / nominal / SOC_span` 입니다
(`Extract_life_labels.py:120`). **`dis_ah_max` 는 완전히 재현되는 열입니다.**

직접 확인했습니다 — 13개 서브셋 26셀 표본에서 `cycle_number_at_label` 의
`dis_ah_max` 로 SOH 를 다시 계산해 기존 `soh_at_label_repo` 와 대조:

```
soh_at_label_repo 재현: 일치 22 / 불일치 0 / 건너뜀 4
```

건너뛴 4건은 라벨이 없거나 해당 사이클 번호가 pkl 에 없는 셀입니다.
RWTH 1.85 · SNL 20-80 3.2 의 상수 덮어쓰기도 반영했습니다.

**즉 재현 안 되는 3열(`dis_points` · `dis_duration` · `v_end_dis`)은 파생 요약
어디에도 쓰이지 않습니다.** 그 셋은 방전 구간 기하이고, 두 요약은 용량만
씁니다.

**판정: `li_ion_cycle_scan.csv` 는 캐시입니다.** 잃어도 파생 요약은 pkl 에서
다시 만들 수 있습니다. 제외해도 정보가 유실되지 않습니다.

다만 정직하게 적습니다 — **파생 요약 CSV 를 실제로 재생성해 sha256 을 맞춘 것은
아닙니다** `[미확인]`. 확인한 것은 "파생값이 재현 가능한 열에서만 나온다" 는
의존 관계이고, 그것이 캐시 여부를 가리는 실질 기준입니다.

### (c) 신규 레코드 — **등록하지 않았습니다.** 전제가 성립하지 않습니다

지시는 "**원인이 스크립트 비결정성으로 확인되면**" 등록하라는 조건부였습니다.
**비결정성이 아닙니다** (a). 오히려 반대 증거가 있습니다 — 저장소의 자체 분석
스크립트 8개는 `analysis/out/` 14개 산출물을 **전부 비트 단위로 재현**했고
(§2-1), PNG 5장과 부트스트랩 1,000회까지 결정적이었습니다. **이 저장소의
스크립트는 결정적입니다.**

등록하지 않은 두 번째 이유는 **`registry.yaml` 의 용도**입니다. 이 파일은
논문·상위문서·코드 세 슬롯을 가진 **주장 대조표**이고 id 접두사도
`LAB-` `DAT-` `META-` `REP-` `VER-` `TRN-` 로 전부 BatteryLife 를 가리킵니다
(`SCHEMA.md` 144-152행). "우리가 스크립트를 저장하지 않았다" 는 이 저장소의
작업 위생 문제라 세 슬롯 중 어디에도 들어가지 않습니다. 억지로 넣으면 판정
유도가 무의미해집니다.

**대신 기록은 남겼습니다** — 이 절, `analysis/README.md` §2, 그리고
`analysis/rebuild_cycle_scan.py` 의 docstring 셋입니다. 다음 사람이 같은 것을
다시 역산하지 않도록 90.3% 가설과 실패한 가설을 둘 다 적었습니다.

### (a)(b)(c) 요약

| 물음 | 답 |
|---|---|
| 재생성 실패 원인 | **셋 다 아님.** 스크립트가 없어 시도 자체가 불가했음 |
| 복원 가능한가 | 11열 중 8열 완전 복원. 3열은 규칙 미상 (전열 90.3%) |
| 파생 요약이 의존하는가 | **아니오.** 전부 `dis_ah_max` → SOH 경로. 22/22 정확 재계산 |
| 원시 스캔은 캐시인가 | **예.** 보존 대상이 아님 |
| 비결정성 레코드 등록 | **안 함.** 전제 불성립 + registry 용도와 불일치 |
| 원본 삭제 | **안 함.** 디스크에 그대로, 미추적 |

---

## 12. 최종 상태

```
 M .gitignore
 M README.md
 M docs/OPEN_QUESTIONS.md
 M docs/PLAN.md
 M findings/PAPER_CODE_MAP.md
 M findings/registry.yaml
?? analysis/                                     (li_ion_cycle_scan.csv 는 제외됨)
?? docs/reports/2026-08-06_na_ion_soh_drop.md
?? docs/reports/2026-08-07_lock_drift.md
?? docs/reports/2026-08-07_repo_cleanup.md
```

- 인덱스 **비어 있음** — `git add` 를 한 번도 실행하지 않았습니다 `[확인]`
- 루트 `CC_REPORT.md` **없음** `[확인]`
- `curves/` 58건 무손상 — main 36 / diagnostic 17 / superseded 5 `[확인]`
- `run.py check` 코드 층 3건 FAIL 유지 (§8) — 복구는 사람의 결정 대기
