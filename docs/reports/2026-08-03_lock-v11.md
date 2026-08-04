# CC_REPORT

작업: **`LOCK.md` 를 v11 전수 기준으로 채우기**
일자: 2026-08-03
위치: `D:\battery_archive`
실행 인터프리터: `C:\Users\taeyo\AppData\Local\Programs\Python\Python312\python.exe`
(CPython 3.12.3, numpy 2.5.1, scikit-learn 1.9.0)

> 이 보고서는 CC 가 한 일과 **관찰한 값** 만 적습니다.
> 태그명과 생성자는 채우지 않았습니다 — 사람이 정합니다.

---

## 요약

| 항목 | 결과 |
|---|---|
| v12 md5 두 줄 → v11 | 교체 완료. `manifests/data_md5.txt` 와 **20/20 동일** |
| zip 항목 | 9행 → **20행** (11행 추가 + `XJTU.zip` `(미정)` 채움) |
| 산출물 항목 | 5행 → **12행** (7행 추가) |
| `lock-init` | **18항목 채움**, 3항목 `(미정)` 으로 남김 |
| `check` 1회차 | **일치 39 · 불일치 0 · 미정 3**, exit 0 |
| 2회차 실행 후 `check` | (아래 6절) |

남은 `(미정)` 3개는 **전부 학습 관련** 입니다 — `env blife`(학습 환경 미구성)와
`interval` 두 행(학습 미실행). 라벨 검증 범위에서는 빈 항목이 없습니다.

**코드를 한 곳 고쳤습니다.** 지시문은 코드 수정을 금지했으나 그대로는 신규
산출물 7개를 잠글 수 없어 먼저 보고하고 승인을 받았습니다 (7절).

---

## 1. 교체한 두 줄

| 파일 | 이전 (v12) | 이후 (v11) |
|---|---|---|
| `Life labels.zip` | `17c7833302b85f475a81b8d3f8614566` | `cd0cc01a7211972be45e8e38d86cdeca` |
| `READMEs.zip` | `d6768d8a185cdf60c11bff4a4be0f9e3` | `f1b28ff26d2cbb1e81455518be9b0e23` |

**대조부터 했습니다.** 새 값 둘 다 `manifests/data_md5.txt` 의 v11 행과 글자
그대로 같습니다. 같은 파일 5-1 절이 이전 값 둘을 v12 값으로 명시하고 있어,
이전 값이 v12 였다는 것도 파일 안에서 확인됩니다.

```
# 5-1. v11 ↔ v12 대조 (record 19688272 ↔ 21149533) — 확인 완료
#   XJTU.zip         v11 ec68d223… 396.9MB  →  v12 2de8b797… 1.5GB  (완전판 교체)
#   Life labels.zip  v11 cd0cc01a… 12.6kB   →  v12 17c78333… 12.8kB (XJTU 라벨 증가분)
#   READMEs.zip      v11 f1b28ff2… 17.2kB   →  v12 d6768d8a… 17.4kB
```

이 두 행이 `python run.py check` 를 실패시키던 원인이었습니다 (`VER-001`).
이제 통과합니다.

---

## 2. 추가한 zip 행

이전 9행 → **20행**. `manifests/data_md5.txt` 의 v11 값을 그대로 옮겼고,
스크립트로 **20/20 이 같은지 대조해 확인** 했습니다.

### 새로 추가한 11행

| 파일 | md5 |
|---|---|
| `CALCE.zip` | `f0f5f1436bc7182d7d5cda05423de8c7` |
| `HNEI.zip` | `27d009bbb908f04e90ecd9a145d81b62` |
| `HUST.zip` | `de6b6d1b0b20616fbb96c72f3231c082` |
| `ISU_ILCC.zip` | `98c0561ff25eb68538572c54aeb279ea` |
| `MATR.zip` | `83a1528858b9e1b7b6886757bb561669` |
| `MICH.zip` | `cc34ea7ed8edc6419cb30757548ca3da` |
| `RWTH.zip` | `f5a0f039503b882613770ef138eb66f4` |
| `SDU.zip` | `6d557d6e74e7b7cf13f54a9cedd7b38b` |
| `Stanford.zip` | `6d6892eb5bd1b836635e5786c2b90c6a` |
| `Stanford_2.zip` | `3484565dc7c1dd2baa3df02352bbe8a5` |
| `UL_PUR.zip` | `65551018b3d67d96eda724552a0360bd` |

### 값을 채운 1행

| 파일 | 이전 | 이후 |
|---|---|---|
| `XJTU.zip` | `(미정)` | `ec68d223209b9ddac6c7f5592b2463cd` |

**v11 값을 넣었습니다.** 비고에 `v12 는 2de8b797… 1.5GB 완전판 — 넣지 말 것`
을 적어 두었습니다. v11 과 v12 가 갈리는 세 파일(`XJTU` · `Life labels` ·
`READMEs`) 전부 비고에 v12 값을 함께 적어, 판본이 다른 사람이 어디서 걸리는지
바로 알 수 있게 했습니다.

### 그 밖

- 비고 열을 20행 전부 `md5 · v11(19688272)` 로 통일했습니다. 저장소가 v11
  기준임이 파일에서 드러납니다.
- 행 순서를 `manifests/data_md5.txt` 와 같은 알파벳 순으로 맞췄습니다. 두
  파일을 나란히 놓고 볼 수 있습니다.
- 표 아래에 `zip 20개를 전부 잠급니다` 절을 넣어, **`labels` 세트 8개만 받은
  사람은 나머지 12행이 `대상없음`(skip) 으로 넘어간다** 는 것을 적었습니다.
  불일치가 아닙니다.

---

## 3. 산출물 행

이전 5행 → **12행**.

### 그대로 둔 5행 (이름을 바꾸지 않았습니다)

| 항목 이름 | 실제 파일 |
|---|---|
| `nb01 재집계 recount.json` | `findings/recount.json` |
| `nb03 셀 단위 대조표` | `experiments/results/nb03_cells.json` |
| `nb03 도메인 롤업 표` | `experiments/results/nb03_rollup.json` |
| `nb03 불일치 셀 목록` | `experiments/results/nb03_mismatch.json` |
| `nb03 라벨없음(비유한) 셀 목록` | `experiments/results/nb03_nolabel.json` |

**지시문의 "이름이 바뀐 행은 실제 파일명에 맞춘다" 를 그대로 따르지
않았습니다.** 이 다섯 이름은 `verify/lock.py` 의 `_ITEMS` 대응표 **키** 라서,
파일명으로 바꾸면 `compute()` 가 `(모르는 항목)` 을 돌려주어 다섯 행이 전부
잠기지 않게 됩니다. 대신 **비고 열에 실제 파일명을 적었습니다** — 표에서
어느 파일인지 바로 보이고, 대응표는 깨지지 않습니다.

### 새로 추가한 7행

| 항목 이름 | 실제 파일 |
|---|---|
| `nb02 변형 비교` | `experiments/results/nb02_variants.json` |
| `nb03 no_soc_span 변형` | `experiments/results/nb03_cells_nospan.json` |
| `nb03 discharge_denom 변형` | `experiments/results/nb03_cells_discharge_denom.json` |
| `nb04 cycle_number 롤업` | `experiments/results/nb04_cycle_numbers.json` |
| `nb04 셀별 추가 측정` | `experiments/results/nb04_extras.json` |
| `nb05 v2 대조표 원자료` | `experiments/results/nb05_v2_compare.json` |
| `findings/na_ion_crate.json` | 같음 |

### 잠그지 않은 것 — 표 아래에 이유를 적었습니다

- `experiments/results/prev_6subset/` — 440셀 시절 보존 사본. 현재 상태의
  기준이 아닙니다 (지시문대로).
- `experiments/results/LABEL_REPORT.md` · `CC_REPORT.md` — 사람이 읽는 글.
  표현을 고치면 해시가 바뀌는데 그것은 결과가 달라진 것과 다릅니다.
  잠그는 것은 **정규화 JSON** 뿐입니다.

---

## 4. `lock-init` 결과

**18항목 채움 / 3항목 남김.**

| 층 | 채운 항목 |
|---|---|
| 코드 | `upstream/BatteryML tree` · `upstream/BatteryLife tree` · `verify/ tree` · `findings/registry.yaml` · `findings/anchors.yaml` |
| 환경 | `env repro` (`manifests/env_lock/repro.txt` 생성) |
| 결과 | 산출물 12행 전부 |

`upstream/BatteryMFormer commit` 은 이미 값이 있어 건드리지 않았습니다
(`lock-init` 은 값이 든 행을 덮어쓰지 않습니다).

### `(미정)` 으로 남은 3항목 — 전부 학습 관련

| 항목 | 왜 남았나 |
|---|---|
| `env blife` | `manifests/env_lock/blife.txt` 가 없습니다. 학습 환경을 아직 구성하지 않았습니다 → `(대상없음)` |
| `CPTransformer Li-ion MAPE` | `interval` 은 사람이 잽니다. 학습 미실행 |
| `CPTransformer Li-ion 15%-Acc` | 〃 |

지시문이 확인하라고 한 `interval` 두 행은 `(미정)` 인 채로 남았고 `check` 에서
넘어갑니다 (아래 5절).

> **알아두어야 할 것** — `lock-init` 은 마지막에 항상
> `(미정) 이 남아 있습니다. 이 상태로 태그를 찍지 마십시오.` 를 출력합니다.
> 이 메시지는 **항목 종류를 구별하지 않습니다.** 지금 남은 3개는 전부 학습
> 항목이고, `LOCK.md` 자신이 "학습 두 행은 첫 태그 범위 밖" 이라고 적고
> 있습니다. 라벨 검증 태그를 찍는 데는 걸림돌이 아닙니다 — 다만 메시지가
> 그렇게 읽히므로 여기 적어 둡니다.

---

## 5. `check` 1회차 — 전 항목 상태

**일치 39 · 불일치 0 · 미정 3. exit code 0.**

| 층 | 항목 수 | 상태 |
|---|---|---|
| 코드 | 6 | 전부 `ok` — upstream tree 2 · submodule 1 · `verify/` tree 1 · registry · anchors |
| 데이터 | 20 | **전부 `ok`** — zip 20개 md5 |
| 환경 | 2 | `env repro` `ok` / `env blife` `미정` |
| 결과 | 14 | 산출물 12개 `ok` / `interval` 2개 `미정` |

이전에 실패하던 `Life labels.zip` · `READMEs.zip` 두 행이 `ok` 로 바뀌었고,
`XJTU.zip` 을 포함한 zip 20행이 전부 통과합니다.

```
불일치 없음 (일치 39). 미정 3 — `python run.py lock-init` 으로 채웁니다
```

---

## 6. 2회차 실행 후 `check` 재통과

`lock-init` 으로 잠근 **뒤에** 전체를 다시 돌렸습니다. 산출물이 결정적인지를
잠금 기준값으로 실제 검증하는 절차입니다.

```
python run.py labels --recount                      606초  exit 0
python run.py labels --variant no_soc_span          591초  exit 0
python run.py labels --variant discharge_denom      575초  exit 0
python run.py check                                        exit 0
```

### 산출물 대조 — 잠근 12개 파일

| 결과 | 값 |
|---|---|
| 3회 실행 뒤 sha256 이 바뀐 파일 | **0개** |
| 바뀌지 않은 파일 | **12개 전부** |

`IDENTICAL 12 files unchanged after 3 runs`

### 2회차 `check`

**일치 39 · 불일치 0 · 미정 3. exit code 0.** 1회차와 **글자 그대로 같습니다.**

```
불일치 없음 (일치 39). 미정 3 — `python run.py lock-init` 으로 채웁니다
```

즉 pkl 80.5 GiB 를 세 번 다시 읽어 세 변형을 다시 계산해도 잠금 기준값이
그대로입니다. 산출물이 결정적이라는 것을 **기준값에 대고** 확인했습니다
— 직전 작업에서 확인한 "3회 바이트 동일" 과 달리, 이번에는 잠근 뒤에 돌려
`check` 로 판정했습니다.

---

## 7. 남은 문제

### 규칙에서 벗어난 판단 — 코드 1곳 수정 (승인받음)

지시문은 `verify/` 수정을 금지했습니다. 그러나 **그대로는 신규 산출물 7개를
잠글 수 없었습니다.** `verify/lock.py:50-64` 의 `_ITEMS` 는 항목 이름 → 파일
경로 대응표이고, 여기 없는 이름은 `compute()` 가 `(모르는 항목)` 을 돌려주어
`lock-init` 이 채우지 못한 채 `(미정)` 으로 남습니다. 실제로 표에 넣기 전에
7개 이름을 `compute()` 에 넣어 전부 `(모르는 항목)` 이 나오는 것을 확인했습니다.

작업을 멈추고 세 선택지(대응표에 7줄 추가 / 행만 넣고 `(미정)` 방치 / 7행을
아예 빼기)를 보고했고, **대응표에 7줄 추가** 로 승인받아 진행했습니다.

- 고친 곳: `verify/lock.py` 의 `_ITEMS` 에 항목 7개 추가
- 계산 방법은 기존과 같은 `"json"` (정규화 JSON → sha256)
- **판정 규칙 · 계산 로직 · 임계값은 하나도 건드리지 않았습니다.** 늘어난 것은
  "어느 파일을 볼지" 뿐입니다
- 순서가 중요했습니다 — `verify/ tree` 자신이 잠금 대상이라 **`lock-init`
  이전에** 고쳐야 합니다. 그렇게 했고, 그래서 `verify/ tree` 가 `ok` 입니다

### 그대로 남은 것

| 항목 | 상태 |
|---|---|
| 태그명 | `(태그 미정)` — **사람이 정합니다.** 채우지 않았습니다 |
| 생성자 | `(미정)` — **사람이 정합니다.** 채우지 않았습니다 |
| `env blife` | 학습 환경 미구성. 구성한 뒤 `lock-init` 재실행하면 채워집니다 |
| `interval` 2행 | 학습 미실행. 사람이 재서 넣습니다 |

### 사람이 정할 것

1. **태그명과 생성자.** 이 둘이 비어 있으면 태그를 찍을 수 없습니다.
2. **지금 태그를 찍을지.** 라벨 검증 범위(코드 · 데이터 · 결과)는 39/39
   통과했습니다. 남은 3개는 전부 학습 항목이고 `LOCK.md` 가 첫 태그 범위
   밖이라고 적고 있습니다.
3. **`manifests/data_md5.txt` 가 원본입니다.** `LOCK.md` 의 md5 20개는 그
   파일의 사본이고, 두 곳에 같은 값이 있습니다. 값을 고쳐야 하면 원본을 먼저
   고치십시오. 그 관계를 `LOCK.md` 표 아래에 적어 두었습니다.

### 하지 않은 것

`git add` · `commit` · `tag` · `push` 없음. 태그명·생성자 임의 기입 없음.
`manifests/data_md5.txt` 의 md5 값 수정 없음 (LOCK 을 거기 맞췄습니다).
`verify/` 는 승인받은 `_ITEMS` 7줄 외에 고치지 않았습니다.

---

## 8. 읽는 순서

1. **이 파일**
2. `LOCK.md` — 잠금 항목 42행 (digest 40 · interval 2)
3. `python run.py check` — 직접 돌려 39/39 를 확인
4. `manifests/data_md5.txt` — md5 원본과 v11↔v12 대조표
5. 직전 작업(v11 전수 재현)의 결과는
   `experiments/results/LABEL_REPORT.md` 와
   `experiments/results/prev_6subset/` 에 있습니다
