# BatteryLife 하위 데이터셋 메타데이터 전수 조사

2026-08-13 · CC (Whitefox 지시)

**학습을 돌리지 않았습니다** `[확인]`. 원시 데이터는 읽기 전용으로만 열었습니다 `[확인]`.
새로 만든 것은 `analysis/dataset_metadata_survey.py` 와 그 산출물 둘입니다.

---

## 0. 한 줄

| # | 결과 |
|---|---|
| **전수성** | **1,382셀 전부를 열었습니다.** 대상 1,382 · 기록 1,382 · **읽기 실패 0건** `[확인]` |
| **원시 파일** | **전 서브셋 실물이 있습니다.** 18개 디렉터리 87.7 GB. "파일 없음" 인 서브셋은 없습니다 `[확인]` |
| **사양** | 공통이라고 알려진 필드가 **셀마다 갈리는 곳이 여럿**입니다 — SNL 정격용량 5종, CALB 컷오프 3종, ZN-coin 140종 `[확인]` |
| **부문** | 소형 IT 6 · 전동공구/경형 4 · 전기차 4 · ESS 2 · 실험실 전용 4 로 나뉩니다. **전부 `[추론]`** 입니다 |
| **궤도 예측** | BatteryLife 의 학습 타깃은 **스칼라 하나**입니다. 궤도 회귀는 같은 저장소의 **BatteryMFormer** 에만 있고, 그쪽이 요구하는 SOH 산출물은 **배포되지 않습니다** `[확인]` |
| **재확인 4건** | ISU-ILCC 분모 · Tongji 오프셋 · CALB 분기 · γ 하드코딩 — **네 건 모두 현재 코드에서 그대로 유효**합니다 `[확인]` |

---

## 1. 조사 환경

### 1-1. 저장소와 보고 규칙

| 항목 | 값 |
|---|---|
| 저장소 루트 | `D:\battery_archive` (git, 브랜치 `main`, 조사 시작 시 작업 트리 깨끗함) |
| 보고서 관례 | `docs/reports/YYYY-MM-DD_<주제>.md` — 기존 23개 파일이 전부 이 형식 `[확인]` |
| 이 보고서 | 그 관례를 따릅니다. **루트 `CC_REPORT.md` 는 만들지 않았습니다** |
| 실행 환경 | `.venv-blife/Scripts/python.exe` · Python 3.12.3 · numpy 1.26.4 (`analysis/README.md` §0) |

루트의 실제 디렉터리는 다음과 같습니다 `[확인]`.

```
.build  .claude  analysis  data  docs  envs  experiments  figures  findings
manifests  notebooks  papers  runs  train  upstream  verify
config.env  LOCK.md  Makefile  NOTICE  README.md  run.py
```

### 1-2. 원시 데이터의 존재 형태 — **실물이 있습니다**

세 가지를 구분해야 한다는 지시에 따라 나누면, 이 저장소는 **세 가지를 다 갖고 있습니다** `[확인]`.

| 형태 | 위치 | 실측 |
|---|---|---|
| 배포 zip 원본 | `data/zenodo_v11/` | 21개 · 30.1 GB. `LOCK.md` 가 21개 md5 를 전부 잠그고 있음 |
| 전처리 산출물 (pkl) | `data/extracted/` | **1,440 pkl · 87.7 GB** |
| 다운로드·전처리 스크립트 | `upstream/BatteryLife/process_scripts/` | `preprocess_*.py` 19개 + 라벨 스크립트 |

`data/` 는 `.gitignore` 의 `data/*` 로 제외됩니다. **저장소를 clone 해도 따라오지 않고,
이 기계에만 있습니다** `[확인]`. 따라서 아래 모든 실측값은 이 기계의 v11 트리 기준입니다.

`data/extracted/` 의 22개 디렉터리 중 셀 pkl 을 담은 것은 18개입니다.

- **셀 디렉터리 18개** — 아래 §2 표.
- **파생 1개** `total_MICH/` (58 pkl) — 배포물이 아니라 `data_loader.py:391-393` 의
  `merge_MICH()` 가 `MICH`+`MICH_EXP` 를 복사해 만든 것입니다. 실제로
  `MICH ∪ MICH_EXP == total_MICH` 임을 집합 비교로 확인했습니다 `[확인]`.
  **전수 대상에서 제외**했습니다. 넣으면 58셀이 두 번 세어집니다
  (`findings/registry.yaml` META-005 과 같은 판단).
- **비셀 3개** — `Life labels/`(19 json) · `READMEs/`(18 md) · `seen_unseen_labels/`(8 json).

그래서 **고유 셀은 1,440 − 58 = 1,382개**입니다 `[확인]`.
이 값은 `findings/recount.json` 의 1,382 와 같습니다.

### 1-3. 전수성 검증 — 지시 6절 대응

| 항목 | 결과 |
|---|---|
| 루프 **전** 대상 셀 수 | **1,382** (디렉터리를 훑어 `.pkl` 을 센 값) |
| 루프 **후** 기록 행 수 | **1,382** |
| 대조 | **일치** `[확인]` — 스크립트가 종료 코드 0 으로 끝남 |
| 읽기 실패 | **0건** `[확인]` |
| 컨테이너 문제 | 해당 없음. 이 배포는 **pkl 1개 = 셀 1개**이고, 셀 딕셔너리 안에 다른 셀이 들어 있지 않음을 스키마 확인으로 봤습니다 |
| 최대 단일 파일 | `ISU_ILCC/ISU-ILCC_G6C3.pkl` **452 MB** — 이 기계(물리 RAM 15.1 GiB)에서 한 개씩 올리는 데 문제 없음 |

방법은 지시대로입니다 — **셀 하나 열기 → 스칼라만 뽑기 → 무거운 배열 참조 해제 →
행 1개 append 후 flush → 다음 셀**. 원시 배열은 누적하지 않으므로 최대 상주량이
가장 큰 pkl 1개로 묶입니다. 셀 단위 `try/except` 를 걸었고 첫 예외에서 멈추지
않습니다. 처리 순서는 `sorted()` 로 고정했습니다.

**샘플링은 스키마 파악에만 썼습니다** — 서브셋 6개에서 각 1개씩 열어 키 이름과
배열 모양을 봤고(§4-1 의 `cycle_keys`), 그 뒤 본 조사는 1,382셀 전수입니다.

### 1-4. 산출물

| 산출물 | 경로 | 성격 |
|---|---|---|
| 이 보고서 | `docs/reports/2026-08-13_dataset_metadata_survey.md` | 커밋 대상 |
| 데이터셋 단위 표 | `docs/reports/datasets_metadata.csv` | 18행. 커밋 대상 |
| **셀 단위 전수 표** | `analysis/out/dataset_cell_census.csv` | **1,382행 · 46열.** `analysis/out/` 는 `.gitignore` 대상이라 커밋되지 않습니다 — 아래 스크립트로 재생성합니다 |
| 추출 스크립트 | `analysis/dataset_metadata_survey.py` | 커밋 대상. 저장소 관례대로 `analysis/` 에 두었고 루트에서 실행합니다 |

```
.venv-blife/Scripts/python.exe analysis/dataset_metadata_survey.py
```

87.7 GB 를 전부 읽습니다. **이번 실행의 소요 시간은 계측하지 않았습니다** —
사후에 확인할 수 있는 기록을 남기지 않았고, 파일 시각으로 되짚는 것은 값이
믿을 만하지 않아 적지 않습니다. 다음 실행부터는 스크립트가 `[census] 소요 …분`
을 직접 출력합니다.

기존 `analysis/extract_cell_meta.py` 와 목적이 다릅니다 — 그쪽은 조건 다양성용
사양 필드만 보고, 이쪽은 **셀마다 갈리는 값**(첫·끝 SOH, EOL 도달 사이클,
사이클 번호 결번, 배포 라벨, 부가 채널 유무)을 함께 잽니다.

---

## 2. 데이터셋 인벤토리

### 2-1. 목록의 근거 — 다섯 곳 교차 확인

한 곳만 보면 갈립니다. 실제로 **다섯 곳이 서로 다른 목록을 줍니다** `[확인]`.

| # | 근거 위치 | 담긴 목록 | 개수 |
|---|---|---|---|
| 1 | `data_provider/data_loader.py:28-51` `datasetName2ids` | 코드가 ID 를 부여하는 이름 | 22개 (시드 변형 포함) |
| 2 | `data_provider/data_loader.py:380-415` 파일명 접두사 분기 | 코드가 **실제로 pkl 을 여는** 디렉터리 | 16개 |
| 3 | `process_scripts/preprocess_*.py` | 전처리 스크립트가 있는 서브셋 | 19개 (Farasis 포함) |
| 4 | `assets/Further_details_of_data_statistics.md` 요약표 | 상위 문서가 사양을 적은 서브셋 | **16개** |
| 5 | `data/extracted/READMEs/*.md` | 배포물에 동봉된 서브셋 README | **18개** |

**세 가지가 어긋납니다** `[확인]`.

- **`SDU` (86셀) 는 코드에서 도달할 수 없습니다.** `preprocess_SDU.py` 가 있고
  README 도 있는데, `datasetName2ids` 에도 `read_cell_data_according_to_prefix`
  분기에도 `SDU` 가 **한 줄도 없습니다**. `upstream/BatteryLife` 전체에서 `SDU`
  는 `preprocess_scripts.py` · `preprocess_SDU.py` · `README.md` 세 곳에만
  나옵니다. BatteryMFormer 쪽에도 없습니다.
- **`Stanford_2` (181셀) 는 BatteryLife 로더에 없고 BatteryMFormer 에만 있습니다**
  (`data_loader_soh_optimized.py:201,778`). 상위 요약표에도 없습니다.
- **`Farasis` 는 반대입니다** — 라벨 코드에 전용 분기가 있으나
  (`Extract_life_labels.py:91-104`) **v11 배포 트리에 파일이 없습니다.**
  이 조사에서 **"파일 없음"** 으로 기록하는 유일한 항목입니다 `[확인]`.

즉 배포된 1,382셀 중 **267셀(19.3%)이 BatteryLife 자신의 학습 경로에서
도달 불가**합니다(SDU 86 + Stanford_2 181).

### 2-2. 인벤토리 표 — 실측

파일 개수·용량·셀 개수는 **직접 세었습니다** `[확인]`.
"README 주장" 은 `data/extracted/READMEs/<이름>_README.md` 의 본문·표 수치입니다 `[추론]`.

| 코드상 식별자 | 디렉터리 | 존재 | 포맷 | 파일 수 | 용량 | **실측 셀 수** | README 주장 | 배포 라벨 수 |
|---|---|---|---|---:|---:|---:|---:|---:|
| `CALB` | `data/extracted/CALB` | 있음 | pkl | 27 | 49 MB | **27** | 27 | 27 |
| `CALCE` | `…/CALCE` | 있음 | pkl | 13 | 198 MB | **13** | 13 | 13 |
| `HNEI` | `…/HNEI` | 있음 | pkl | 14 | 380 MB | **14** | 14 | 14 |
| `HUST` | `…/HUST` | 있음 | pkl | 77 | 3,944 MB | **77** | 77 | 77 |
| `ISU_ILCC` | `…/ISU_ILCC` | 있음 | pkl | 240 | 28,280 MB | **240** | 240 | 240 |
| `MATR` | `…/MATR` | 있음 | pkl | 169 | 7,938 MB | **169** | 169 | 169 |
| `MICH` | `…/MICH` | 있음 | pkl | 40 | 756 MB | **40** | 40 | 40 |
| `MICH_EXP` | `…/MICH_EXP` | 있음 | pkl | 18 | 478 MB | **18** | **12** ⚠ | 12 |
| `NAion` / `NA-ion` | `…/NA-ion` | 있음 | pkl | 64 | 670 MB | **64** | **31** ⚠ | 34 |
| `RWTH` | `…/RWTH` | 있음 | pkl | 48 | 2,470 MB | **48** | 48 | 48 |
| `SDU` | `…/SDU` | 있음 | pkl | 86 | 3,777 MB | **86** | 86 | 70 |
| `SNL` | `…/SNL` | 있음 | pkl | 61 | 601 MB | **61** | **52** ⚠ | 52 |
| `Stanford` | `…/Stanford` | 있음 | pkl | 41 | 4,049 MB | **41** | 41 | 41 |
| `Stanford_2` | `…/Stanford_2` | 있음 | pkl | 181 | 19,422 MB | **181** | 181 | 181 |
| `Tongji1/2/3` | `…/Tongji` | 있음 | pkl | 130 | 3,981 MB | **130** | **108** ⚠ | 108 |
| `UL_PUR` | `…/UL_PUR` | 있음 | pkl | 10 | 27 MB | **10** | 10 | **2** |
| `XJTU` | `…/XJTU` | 있음 | pkl | 23 | 2,396 MB | **23** | 23 | 23 |
| `ZN-coin` / `ZNcoin` | `…/ZN-coin` | 있음 | pkl | 140 | 3,040 MB | **140** | **100** ⚠ | 121 |
| `Farasis` | — | **없음** | — | 0 | — | **0** | — | — |
| (파생) `total_MICH` | `…/total_MICH` | 있음 | pkl | 58 | 1,233 MB | (제외) | — | 52 |
| **합계 (고유)** | | | | **1,382** | **87.7 GB** | **1,382** | | |

⚠ 표시 5개가 **README 와 실측이 어긋나는 서브셋**입니다. 전부 실측이 더 많습니다 —
MICH_EXP 12→18 · NA-ion 31→64 · SNL 52→61 · Tongji 108→130 · ZN-coin 100→140.
합 **73셀 차이**입니다. 배포 라벨 수가 README 주장과 같은 것으로 보아,
**README 는 라벨이 만들어진 셀만 센 것으로 보입니다** `[추론]` — 라벨 코드가
`last_cycle_soh >= 0.825` 인 셀을 버리기 때문입니다(§5-1). 다만 NA-ion 은
README 31 · 라벨 34 로 이 설명과도 맞지 않아 남는 질문입니다(§7).

`Stanford` 41셀과 `Stanford_2` 181셀은 **38셀이 파일명이 같습니다.
합집합은 184셀입니다** `[확인]`. 위 합계 1,382 는 두 디렉터리를 따로 센 값입니다.

---

## 3. 셀 사양 메타데이터 — 전수 실측

아래 세 표는 **1,382셀을 전부 읽어 만든 값**입니다 `[확인]`.
근거는 pkl 최상위 스칼라 필드이고, 필드 이름은 표 머리에 적힌 그대로입니다.
`<N종>` 은 고유값이 6개를 넘어 개수만 적은 것입니다.
셀 단위 원자료는 `analysis/out/dataset_cell_census.csv` 입니다.

### 3-1. 조성·폼팩터·전압 (pkl 필드 실측)

| subset | n | `form_factor` | `anode_material` | `cathode_material` | `nominal_capacity_in_Ah` | `max_voltage_limit_in_V` | `min_voltage_limit_in_V` | `SOC_interval` |
|---|---:|---|---|---|---|---|---|---|
| CALB | 27 | Prismatic | graphite | NMC | 58 | 4.25 \| 4.35 | 2.2 \| 2.5 \| 2.75 | [0,1] |
| CALCE | 13 | prismatic | graphite | LiCoO2 | 1.1 \| 1.35 | 4.2 | 2.7 | [0,1] |
| HNEI | 14 | cylindrical_18650 | graphite | LiCoO2+LiNi0.4Co0.4Mn0.2O2 | 2.8 | 4.3 | 3 | [0,1] |
| HUST | 77 | cylindrical_18650 | graphite | LFP | 1.1 | 3.6 | 2.0 | [0,1] |
| ISU_ILCC | 240 | ` 502030-size Li-polymer` | graphite | NMC | 0.25 | 4.2 | 3.0 | **<182종>** |
| MATR | 169 | cylindrical_18650 | graphite | LiFePO4 | 1.1 | 3.5 | 2.0 | [0,1] |
| MICH | 40 | pouch | graphite | NMC111 | 2.36 | 4.2 | 3 | [0,1] |
| MICH_EXP | 18 | pouch | graphite | NMC111 | 5.0 | 4.2 | 3 | [0,1]×12 \| [0.5,1]×6 |
| NA-ion | 64 | cylindrical_18650 | **Unknown** | **Unknown** | 1.0 | 4.0 | 2.0 | [0,1] |
| RWTH | 48 | cylindrical_18650 | graphite | NMC | **1.85** | 3.9 | 3.5 | [0.2,0.8] |
| SDU | 86 | cylindrical | graphite | NMC_532 | 2.4 | 4.2 | 3 | [0,1] |
| SNL | 61 | cylindrical_18650 | graphite | LFP \| NCA \| NMC | **<5종>** 1.1·2.7·2.88·3·3.2 | 3.6 \| 4.2 | 2.0 \| 2.5 | [0,1] \| [0.2,0.8] |
| Stanford | 41 | pouch | graphite | LiNi0.5Mn0.3Co0.2O2 | 0.24 | 4.4 | 3 | [0,1] |
| Stanford_2 | 181 | pouch | graphite | LiNi0.5Mn0.3Co0.2O2 | 0.24 | 4.4 | 3 | [0,1] |
| Tongji | 130 | cylindrical_18650 | Graphite \| Graphite/Si | NCA861103 \| NCM831107 \| NCM+NCA 블렌드 | 3.5×121 \| 2.5×9 | 4.2 | 2.5 \| 2.65 | [0,1] |
| UL_PUR | 10 | cylindrical_18650 | graphite | LiNi0.8Co0.15Al0.05O2 | 3.4 | 4.2 | 2.7 | [0,1] |
| XJTU | 23 | cylindrical_18650 | graphite | LiNi0.5Co0.2Mn0.3O2 | 2.0 | 4.2 | 2.5 | [0,1] |
| **ZN-coin** | 140 | coin | **MnO2** | **Zinc** | **<140종>** 0.208–0.537 mAh | 1.8 | 0.8 | [0,1] |

**전해질(`electrolyte_material`)은 1,382셀 전부에서 `None` 입니다** `[확인]`.
조성을 알려면 문서를 봐야 합니다 — 상위 요약표
(`assets/Further_details_of_data_statistics.md`)가 MICH·MICH_EXP·Stanford·
Tongji·ZN-coin 다섯 곳의 전해질을 적습니다 `[추론]`.

**"공통이라고 알려진 필드도 전수로 확인" 지시의 결과** — 실제로 갈립니다 `[확인]`.

| 갈리는 곳 | 실측 |
|---|---|
| `SNL` 정격용량 | **5종** (1.1 / 2.7 / 2.88 / 3 / 3.2 Ah). 문서·README 는 **3종**이라고 적습니다 |
| `CALB` 상한 컷오프 | 4.35 V × 24셀, **4.25 V × 3셀**. 문서는 4.35 V 하나만 적습니다 |
| `CALB` 하한 컷오프 | 2.75 V × 16 · **2.2 V × 8** · **2.5 V × 3**. 문서는 2.75 V 하나만 적습니다 |
| `CALCE` 정격용량 | 1.1 과 1.35 두 값이 섞임 (문서와 일치) |
| `Tongji` 정격용량 | 3.5 Ah × 121 · 2.5 Ah × 9 |
| `ZN-coin` 정격용량 | **셀마다 다름 (140종)**. 10번째 사이클 방전용량을 정격으로 쓰기 때문 `[추론]` (ZN-coin README) |
| `ISU_ILCC` SOC 구간 | **182종.** span 이 정확히 1 인 셀은 59개뿐 |
| `MICH_EXP` SOC 구간 | [0,1] 12셀 · [0.5,1] 6셀 |

`SOC_interval` 의 span 이 1 이 아닌 셀을 전수로 세면 **239개**이고
**ISU_ILCC 181 · RWTH 48 · MICH_EXP 6 · SNL 4** 입니다 `[확인]`.
이 값은 `findings/registry.yaml` LAB-005 의 기록과 같습니다 — 독립 재현했습니다.

### 3-2. 프로토콜·온도·사이클

`charge_rate_C` / `discharge_rate_C` 는 `charge_protocol` · `discharge_protocol`
리스트 안의 `rate_in_C` 고유값입니다. **다단충전셀** 은 `charge_protocol` 의
단계 수가 2 이상인 셀 수입니다.

"온도배열 있는 셀" 은 `temperature_in_C` 가 `None` 이 아닌 셀 수이고,
"온도 중앙값" 이 `—` 인 곳은 **배열은 있으나 유한값이 하나도 없다**는 뜻입니다.

| subset | 충전 C-rate | 방전 C-rate | 다단충전 셀 | 온도배열 있는 셀 | 온도 중앙값 | 사이클 수 min/중앙/max | 첫 사이클 번호 | 결번 있는 셀 |
|---|---|---|---:|---:|---:|---|---|---:|
| CALB | 1 \| 5 \| `stepcharge` | 1 \| 15 \| `stepcharge` | 0 | 27 | 35.0 °C | 99 / 99 / 208 | 1 \| **2** | 0 |
| CALCE | 0.5 | 0.5 \| 1 | 0 | 0 | — | 632 / 1072 / 1579 | 1 \| **2** | 0 |
| HNEI | 2 | 1 | 0 | 14 | — | 1075 / 1082 / 1107 | 1 | **14** |
| HUST | 1 \| 5 | <13종> | **77** | 0 | — | 1142 / 1873 / 2689 | 1 \| **3** | 0 |
| ISU_ILCC | <39종> | <35종> | 0 | 0 | — | 168 / 3107 / **22037** | 1 | 0 |
| MATR | **<62종>** | 4 | **169** | 169 | 33.6 °C | 169 / 811 / 2235 | 1 | 0 |
| MICH | 1 | 1 | 0 | 40 | — | 426 / 492 / 589 | 1 | 0 |
| MICH_EXP | 0.2 \| 1.5 \| 2 | 0.2 \| 1.5 \| 2 | 0 | 18 | — | 103 / 379 / 573 | 1 | 0 |
| NA-ion | 2.5 | 2.5 | 0 | 0 | — | 91 / 225 / 251 | 1 | 0 |
| RWTH | 2 | 2 | **48** | 0 | — | 1488 / 2264 / 2448 | 1 | **48** |
| SDU | (빈 값) | (빈 값) | 0 | 86 | 25.7 °C | 66 / 461 / 1426 | 1 | 0 |
| SNL | 0.5 | 0.5 \| 1 \| 2 \| 3 | 0 | 61 | 26.5 °C | 389 / 786 / **4569** | 1 | 0 |
| Stanford | 1 | 0.75 | 0 | 41 | — | 719 / 936 / 1420 | 1 | 0 |
| Stanford_2 | 1 | 0.75 | 0 | 181 | — | 736 / 1019 / 1624 | 1 | 0 |
| Tongji | (빈 값) | (빈 값) | 0 | 0 | — | 27 / 399 / 1251 | **2 (130셀 전부)** | **72** |
| UL_PUR | 2 | 1 | 0 | 10 | 27.8 °C | 164 / 212 / 309 | 1 | 0 |
| XJTU | 2 \| 3 | 1 | 0 | 0 | — | 130 / 298 / 419 | 1 | 0 |
| ZN-coin | 8 | 8 | 0 | 0 | — | 41 / 391 / 1737 | 1 | 0 |

**온도는 세 단계로 갈립니다** `[확인]`. 배열이 있다는 것과 쓸 수 있다는 것이
다릅니다 — 전수로 세면 이렇습니다.

| 상태 | 셀 수 | 서브셋 |
|---|---:|---|
| **실수치가 있음** | **353** | MATR 169 · SDU 86 · SNL 61 · CALB 27 · UL_PUR 10 |
| 배열은 있으나 **유한값이 하나도 없음** (전부 NaN) | **294** | Stanford_2 181 · Stanford 41 · MICH 40 · MICH_EXP 18 · HNEI 14 |
| `temperature_in_C` 가 전 사이클 `None` | **735** | CALCE · HUST · ISU_ILCC · NA-ion · RWTH · Tongji · XJTU · ZN-coin |

즉 **온도를 실제로 쓸 수 있는 셀은 1,382셀 중 353개(25.5%)뿐입니다.**
나머지 1,029셀의 온도는 pkl 이 아니라 문서에서만 알 수 있습니다 `[추론]`
(상위 요약표의 `Ambient temperature` 열).

**`Tongji` 와 `SDU` 는 `rate_in_C` 가 빈 문자열입니다** `[확인]` — 프로토콜
리스트는 있는데 C-rate 값이 비어 있어, 이 두 서브셋의 C-rate 는 pkl 에서
읽을 수 없습니다.

**사이클 번호가 1 에서 시작하지 않는 셀이 149개** 있습니다 `[확인]` —
Tongji 130셀 전부가 2 · CALB 17셀이 2 · CALCE 1셀이 2 · HUST 1셀이 3.
**결번이 남은 셀은 134개**이고 Tongji 72 · RWTH 48 · HNEI 14 입니다 `[확인]`.

> `findings/registry.yaml:480` 은 이 첫 항목을 **148개**라고 적는데, 같은 줄의
> 내역(130+17+1+1)을 더하면 **149** 입니다. 이번 전수 실측도 149 입니다.
> 레코드 본문의 합계 숫자 한 자리가 어긋나 있습니다 `[확인]`.

### 3-3. EOL 기준과 라벨 정의 — 코드에서 직접

라벨은 `upstream/BatteryLife/process_scripts/Extract_life_labels.py` 가 만듭니다.
**하나의 규칙이 아니라 서브셋마다 경로가 다릅니다.**

**SOH 정의** `[확인]` — `:117-121`

```
soh = max(cycle['discharge_capacity_in_Ah']) / nominal_capacity / SOC_span
      단, SOC_span = SOC_interval[1] - SOC_interval[0], 0 이면 1 (:119-120)
```

- **분자**: 그 사이클의 `discharge_capacity_in_Ah` 배열의 **최댓값** (:121)
- **분모**: `nominal_capacity_in_Ah` **×** SOC 구간 폭

**EOL(수명 라벨) 정의** — 마지막 사이클 SOH 로 세 갈래 `[확인]`

| 마지막 SOH | 코드 위치 | 처리 | 라벨 값의 뜻 |
|---|---|---|---|
| `>= 0.825` | `:124-128` | **셀을 버림** — 라벨이 만들어지지 않음 | — |
| `0.8 < soh < 0.825` | `:129-145` | 마지막 20 사이클 선형회귀로 SOH=0.80 지점 **외삽** | 외삽된 사이클 수 |
| `<= 0.8` | `:146-155` | SOH 가 0.80 이하로 내려간 **첫 지점** | **배열 인덱스 + 1** (`:153`) — 사이클 번호가 아님 |
| (CALB 전용) | `:167-222` | 외부 Excel 용량, **λ=0.9** | 별도 |

**서브셋별 예외 분기 전수 열거** `[확인]` — `Extract_life_labels.py` 안에서
데이터셋 이름이나 파일명으로 갈라지는 곳은 **13군데**입니다.

| # | 행 | 분기 조건 | 하는 일 |
|---|---|---|---|
| 1 | `:74-89` | `dataset_name == 'XJTU'` | 전용 도구로 조기 `return`. 임계 0.80 은 같으나 **마지막 하강 구간 선형보간 + `ceil`** 이라 본경로와 값이 다름 |
| 2 | `:91-104` | `dataset_name == 'Farasis'` | 전용 도구로 조기 `return`. 단위가 사이클이 아니라 **EFC** |
| 3 | `:107` | `dataset_name != 'CALB'` | 본경로 진입 |
| 4 | `:111-112` | `file_name.startswith('RWTH')` | `nominal_capacity = 1.85` **하드코딩** |
| 5 | `:113-114` | `startswith('SNL_18650_NCA_25C_20-80')` | `nominal_capacity = 3.2` **하드코딩** |
| 6 | `:119-120` | `SOC_interval` span == 0 | span 을 1 로 치환 |
| 7 | `:124-128` | `last_cycle_soh >= 0.825` | 셀 폐기 |
| 8 | `:129-145` | `0.8 < last_cycle_soh < 0.825` | 20 사이클 외삽 |
| 9 | `:146-155` | 그 밖 | 첫 교차, `인덱스+1` |
| 10 | `:167-222` | `dataset_name == 'CALB'` | 외부 Excel `汇总表-L148N58-循环.xlsx`, 정격 = **1사이클 방전용량**, **λ=0.9**, 필터 0.925 |
| 11 | `:191-193` | `startswith('CALB_35_B229')` | **696번 사이클 건너뛰기** |
| 12 | `:204-213` | `file_name != 'CALB_25_T25-2.pkl'` | 그 한 셀만 외삽 창을 다르게 잡음 |
| 13 | `:230-238` | `UL_PUR` / `ZNcoin` / `NAion` | 출력 파일명을 `UL-PUR` / `ZN-coin` / `NA-ion` 으로 바꿔 씀 |

**표기 주의**: `nominal_capacity` 하드코딩(#4·#5)은 λ 가 아니라 **분모**를 바꿉니다.
CALB 의 λ=0.9(#10)만이 임계 자체를 바꾸는 유일한 예외입니다.

---

## 4. 재확인 대상 4건 — 현재 코드에서 다시 확인

지시가 지목한 네 지점을 **현재 코드와 이번 전수 실측으로 다시** 확인했습니다.
네 건 모두 **그대로 유효합니다** `[확인]`.

### 4-1. ISU-ILCC 방전/충전 분모 불일치 — **유효**

`preprocess_ISU_ILCC.py:266-284` 의 `calculate_soc_start_and_end()` 는
충전 쪽 `charge_start_soc` 와 방전 쪽 `discharge_end_soc` 를 **둘 다** 계산합니다.
그런데 **`:164` 가 충전 쪽만 저장합니다** `[확인]`.

```python
:164   soc_interval = [charge_start_soc[name], 1]     # discharge_end_soc 는 버려짐
```

그 결과 `Extract_life_labels.py:121` 의 분모가 충전 기준이 됩니다.
**이번 전수 재현에서 ISU_ILCC 240셀 중 배포 라벨과 일치 85 · 불일치 155**
입니다 `[확인]`. 이 값은 `findings/registry.yaml` LAB-017 의 85/155 와 같습니다 —
독립 재현했습니다. 저장소의 `verify/labels.py` 에 `--variant discharge_denom`
(분모만 방전 기준)이 남아 있고, 그 변형에서는 239셀이 일치한다는 기록이 있습니다.

> **어느 쪽이 옳은지는 이 조사가 판정하지 않습니다.** 논문 정의 대조는
> 이번 범위 밖입니다(§7).

### 4-2. Tongji 사이클 넘버링 오프셋 — **유효**

Tongji 130셀 **전부**가 `cycle_number[0] == 2` 입니다 `[확인]`.
그리고 첫 교차 분기를 탄 100셀에서 **재현값 == 배포값이 4셀, 어긋나는 것이
96셀**이고 어긋남은 전부 **배포 = 재현 + 1** 입니다 `[확인]`.

원인은 사이클 번호가 아니라 `:153` 의 `eol = correct_cycle_index + 1` 입니다 —
**라벨이 실제 `cycle_number` 가 아니라 배열 인덱스 기반**입니다. 결번이 있는
다른 서브셋이 이를 뒷받침합니다: RWTH 48셀은 셀마다 결번이 있는데도 배포
라벨과 **48/48 일치**합니다(인덱스 기반이므로).

### 4-3. CALB 특수 분기 — **유효**, 그리고 코드 결함 하나

CALB 27셀은 `:167-222` 의 전용 경로를 탑니다. 정격용량을 pkl 이 아니라
**외부 Excel 의 1사이클 방전용량**에서 얻고, EOL 임계가 **λ=0.9** 입니다.
그 Excel(`汇总表-L148N58-循环.xlsx`)은 **배포 트리에 없습니다** — 그래서
CALB 27셀은 **재현 불가**이며, 이번 census 도 `CALB_external_excel` 로만
표시하고 EOL 을 재현하지 않았습니다 `[확인]`.

특수 분기 두 개도 그대로 있습니다 — `CALB_35_B229` 의 696번 사이클
건너뛰기(`:191-193`)와 `CALB_25_T25-2.pkl` 의 외삽 창(`:204-213`).

**추가로 발견한 것** `[확인]` — `use_extrapolation` 변수가 루프 안에서
**초기화되지 않습니다**.

```python
:185      if min(total_SOHs) < 0.925:
:186          use_extrapolation = True      # ← 이 조건에서만 대입
:187      if min(total_SOHs) <= 0.9: ...
:200      if not find_eol:
:202          if use_extrapolation:          # ← 대입 안 된 셀에서는 이전 셀 값이 남음
```

`min(SOH) >= 0.925` 이면서 EOL 에 도달하지 않은 셀에서는 **직전 셀의 값**이
쓰입니다(첫 셀이면 `NameError`). 처리 순서에 따라 결과가 달라지는 구조입니다.
CALB 는 어차피 외부 파일이 없어 실행으로는 확인할 수 없어, **코드 읽기에
근거한 지적**으로만 남깁니다. 이 지적은
`findings/registry.yaml:153` 의 기존 기록과 같습니다.

### 4-4. γ⁺ / γ⁻ 하드코딩 — **유효**

이 항목은 BatteryLife 가 아니라 **`upstream/BatteryMFormer`** 쪽입니다 `[확인]`.

논문 Appendix D 는 γ⁺·γ⁻ 를 "학습 분할에서 계산한 99·1 백분위" 라고 적는데,
**`process_scripts/` 전체에 `percentile` 이나 `quantile` 호출이 한 줄도 없습니다**
`[확인]` (재확인함). 값은 전부 **모듈 최상단 상수**입니다.

| 파일:행 | γ⁺ | γ⁻ |
|---|---|---|
| `preprocess_HNEI.py:18-19` | 1.1 | −1.4 |
| `preprocess_MICH.py:23-24` | 1.0 | −1.7 |
| `preprocess_MICH_EXP.py:20-21` | 0.5 | −0.7 |
| `preprocess_RWTH.py:24-25` | 0.06 | −0.6 |
| `preprocess_SNL.py:19-20` | 0.05 | −0.5 |

주석이 백분위를 **본 뒤 사람이 고른 값**임을 드러냅니다 — `preprocess_MICH.py:24`
는 1 백분위를 −4.78% 라고 적어 놓고 값은 −1.7 을 씁니다 `[확인]`.
`preprocess_Tongji.py` 와 `preprocess_ISU_ILCC.py` 에는 γ⁺·γ⁻ 자체가 없습니다.

---

## 5. 응용 부문 매핑

### 5-1. 분류 규칙과 한계

**분류 결과는 원칙적으로 `[추론]` 입니다.** 판단 축은 지시대로 정격용량 +
폼팩터 + 화학 + 프로토콜 + 온도입니다. 근거를 한 줄로 함께 적었습니다.

> **한계 — 반드시 함께 읽어야 합니다.**
> 이 데이터는 전부 **단일 셀 시험** 결과입니다. **단일 셀의 거동은 실제
> 팩·시스템의 거동과 같지 않습니다.** 팩에서는 셀 간 불균형, BMS 밸런싱,
> 냉각 설계, 실제 부하 프로파일이 열화를 지배하는데 이 데이터에는 그 어느
> 것도 들어 있지 않습니다. 아래 "부문" 은 **셀이 어느 부문 제품에 쓰이는
> 규격인가** 이지, **그 부문의 시스템 수명을 이 데이터로 예측할 수 있다**
> 는 뜻이 아닙니다.

### 5-2. 매핑 표

| subset | 정격용량 | 폼팩터 | 화학 | **부문** | 판정 | 근거 한 줄 |
|---|---|---|---|---|---|---|
| CALCE | 1.1–1.35 Ah | prismatic | LCO/graphite | **소형 IT기기** | `[추론]` | LCO 각형 1 Ah 대는 휴대기기 셀 규격 |
| HNEI | 2.8 Ah | 18650 | LCO+NCM442 | **소형 IT기기** | `[추론]` | 2.8 Ah 18650 LCO 계열은 노트북 팩 셀 |
| ISU_ILCC | 0.25 Ah | 502030 Li-polymer | NMC/graphite | **소형 IT기기** | `[추론]` | 502030 파우치 0.25 Ah 는 웨어러블·소형기기 규격 |
| Stanford | 0.24 Ah | pouch | NCM523/인조흑연 | **실험실 연구 전용** | `[추론]` | 0.24 Ah 파우치는 상용 제품 대응이 불명확. 원논문 주제가 formation 공정 연구 |
| Stanford_2 | 0.24 Ah | pouch | NCM523/인조흑연 | **실험실 연구 전용** | `[추론]` | 위와 같음 |
| MICH | 2.36 Ah | pouch | NMC111/graphite | **소형 IT기기** | `[추론]` | 2.36 Ah 파우치. 원논문은 formation 프로토콜 연구 |
| XJTU | 2.0 Ah | 18650 | NCM523/graphite | **소형 IT기기** | `[추론]` | 2 Ah 18650 NCM 은 범용 소형 팩 규격 |
| RWTH | 1.85 Ah (pkl) | 18650 | NMC/carbon | **경형 이동수단** | `[추론]` | SOC 20–80% 부분 순환 · 2 C 다단 — 실사용 모사 프로파일 |
| MATR | 1.1 Ah | 18650 | LFP/graphite | **전동공구 / 경형** | `[추론]` | A123 LFP 18650 은 고출력 셀. 다만 데이터 자체는 급속충전 연구용 |
| HUST | 1.1 Ah | 18650 | LFP/graphite | **전동공구 / 경형** | `[추론]` | MATR 과 같은 셀 규격 |
| SNL | 1.1 / 2.7 / 2.88 / 3.0 / 3.2 Ah | 18650 | LFP·NCA·NMC | **혼합 (전동공구+전기차)** | `[추론]` | 한 서브셋 안에 LFP 고출력과 NCA/NMC 고에너지가 섞임 |
| UL_PUR | 3.4 Ah | 18650 | NCA801505/graphite | **전기차** | `[추론]` | 3.4 Ah NCA 18650 은 EV 팩 셀 규격 |
| Tongji | 2.5 / 3.5 Ah | 18650 | NCA·NCM·블렌드 | **전기차** | `[추론]` | 3.5 Ah 18650 NCA/NCM 은 EV 팩 셀. Si 첨가 음극 포함 |
| MICH_EXP | 5.0 Ah | pouch | NMC111/graphite | **전기차** | `[추론]` | 5 Ah 대형 파우치 |
| CALB | 58 Ah | prismatic | NMC/graphite | **전기차 / ESS** | `[추론]` | 58 Ah 각형은 대형 셀. 제공사 CALB 는 EV·ESS 셀 제조사이고 데이터 출처가 `Industrial test` |
| **SDU** | 2.4 Ah | 18650 | NMC532/graphite | **ESS (2차 활용)** | **`[확인]`** | README 인용 원논문 제목이 `Deep sorting of reused batteries for … grouping` — **재사용 배터리 선별**을 명시 |
| NA-ion | 1.0 Ah | 18650 | 미상 / 미상 | **실험실 연구 전용** | `[추론]` | Na-ion 18650. 전극 조성이 pkl·문서 모두 `Unknown` 이라 제품 대응 불명 |
| ZN-coin | 0.208–0.537 mAh | CR2032/2025/2026 coin | Zn / MnO2 | **실험실 연구 전용** | `[추론]` | 코인셀 0.2–0.5 mAh. 상용 제품 대응 없음 |

### 5-3. 부문별 집계

| 부문 | 서브셋 | 셀 수 |
|---|---|---:|
| 소형 IT기기 | CALCE · HNEI · ISU_ILCC · MICH · XJTU | 330 |
| 전동공구 / 경형 이동수단 | MATR · HUST · RWTH | 294 |
| 전기차 | UL_PUR · Tongji · MICH_EXP · CALB(EV/ESS) | 185 |
| ESS / 그리드 | SDU | 86 |
| 혼합 (전동공구+전기차) | SNL | 61 |
| 실험실 연구 전용 | Stanford · Stanford_2 · NA-ion · ZN-coin | 426 |
| **합** | | **1,382** |

CALB 27셀은 전기차 행에만 한 번 셌습니다. ESS 로도 읽을 수 있으나(대형 각형)
중복 계상하지 않았습니다.

**가장 큰 덩어리가 실험실 연구 전용 셀(426셀, 30.8%)** 입니다 `[추론]`.
Stanford + Stanford_2 만으로 222셀이고, 이 둘은 38셀이 겹칩니다.

**ESS 부문은 사실상 비어 있습니다** — 명시적으로 ESS 를 겨냥한 것은 SDU
86셀뿐이고, 그마저도 **BatteryLife 코드에서 도달 불가**합니다(§2-1).

---

## 6. 열화 궤도 예측 관련 정보

### 6-1. 학습 타깃은 스칼라입니다 `[확인]`

`upstream/BatteryLife/data_provider/data_loader.py` 를 따라가면 타깃은
**셀당 정수 하나**입니다.

```
:428    eol = life_labels[file_name]            # Life labels/*.json 에서 읽은 정수
:521    labels.append(eol)                      # 샘플마다 같은 스칼라를 반복
:371    return …, np.array(total_labels), …     # (샘플 수,) 벡터
```

**시계열 궤도가 아닙니다.** `read_samples_from_one_cell` 의 docstring(`:481`)은
`history_sohs, future_sohs` 를 돌려준다고 적지만 실제 반환은
`charge_discharge_curves, attn_masks, labels, eol, …` 입니다 —
**문서 문자열과 코드가 어긋납니다** `[확인]`.

### 6-2. 궤도 회귀는 BatteryMFormer 에만 있습니다 `[확인]`

같은 저장소가 vendoring 한 `upstream/BatteryMFormer` 는 **SOH 궤도 예측**입니다.

| 근거 | 내용 |
|---|---|
| `data_provider/data_factory.py:8` | 주석 15단어 이내 인용: `Data provider for SOH trajectory prediction` |
| `data_loader_soh_optimized.py:851-852` | 샘플에 `soh_trajectory` · `trajectory_mask` 를 담음 |
| `:789` | `soh_trajectory = np.array(soh_data['SOH'], …)` — **미리 만들어 둔 SOH 파일**에서 읽음 |
| `:127` | 그 파일 위치는 `args.processed_SOH_path` 로 받음 |

**그 SOH 산출물이 배포 트리에 없습니다** `[확인]`. `data/` 와 `upstream/` 어디에도
생성된 SOH 파일이 없고, 만드는 스크립트(`process_scripts/generate_soh.py`,
`generate_CALB_soh.py`)만 있습니다. 즉 **궤도 예측을 돌리려면 SOH 산출 단계를
먼저 실행해야 합니다.**

그 산출 단계는 셀을 **버립니다** `[확인]` — `generate_soh.py:115` 가 최종 SOH 가
필터 임계보다 건강한 셀을 버리고, `:154-155` 의 `MIN_SLOPE_THRESHOLD = 1e-4` 가
**열화가 너무 느린 셀을 통째로 버립니다**. 궤도 연구에서 이 두 필터가 무엇을
얼마나 지우는지는 이번 조사에서 재지 않았습니다(§7).

세 번째 upstream 인 `BatteryML` 의 `batteryml/label/soh.py` 는
`SOHLabelAnnotator(cycle_index=100)` 로 **특정 사이클 한 지점의 SOH** 를
돌려줍니다 — 이것도 궤도가 아니라 스칼라입니다 `[확인]`.

### 6-3. 데이터셋별 궤도 예측 가용성 — 전수 실측

**결론부터 — 사이클별 용량 시퀀스와 전압–용량 원시 곡선은 1,382셀 **전부**에
있습니다** `[확인]`. 갈리는 것은 **부가 채널**입니다.

`cycle_data` 의 키 구성은 **MATR 을 뺀 17개 서브셋이 동일**합니다 —
`cycle_number` · `time_in_s` · `current_in_A` · `voltage_in_V` ·
`charge_capacity_in_Ah` · `discharge_capacity_in_Ah` ·
`temperature_in_C` · `internal_resistance_in_ohm`.
**MATR 만 `Qdlin` 이 하나 더 있습니다** `[확인]`.
다만 키가 있다는 것과 값이 들어 있다는 것은 다릅니다 — 아래는 **값이 실제로
있는 셀 수**입니다.

온도 열은 **실수치가 있는 셀 수**입니다(배열만 있고 전부 NaN 인 셀은 0 으로 셉니다).

| subset | 셀 | 사이클별 용량 시퀀스 | 전압–용량 원시곡선 (사이클당 점 수 중앙값) | **IC/DV 산출** | 온도(실수치) | 내부저항 | `Qdlin` |
|---|---:|---|---:|---|---:|---:|---:|
| CALB | 27 | 27/27 | 385 | 가능 | 27 | 0 | 0 |
| CALCE | 13 | 13/13 | 319 | 가능 | 0 | 0 | 0 |
| HNEI | 14 | 14/14 | 368 | 가능 | 0 (배열 14, 전부 NaN) | 0 | 0 |
| HUST | 77 | 77/77 | 641 | 가능 | 0 | 0 | 0 |
| ISU_ILCC | 240 | 240/240 | 789 | 가능 | 0 | 0 | 0 |
| MATR | 169 | 169/169 | 848 | 가능 | **169** | **169** | **169** |
| MICH | 40 | 40/40 | 700 | 가능 | 0 (배열 40, 전부 NaN) | 0 | 0 |
| MICH_EXP | 18 | 18/18 | 1444 | 가능 | 0 (배열 18, 전부 NaN) | 0 | 0 |
| NA-ion | 64 | 64/64 | 1106 | 가능 | 0 | 0 | 0 |
| RWTH | 48 | 48/48 | 545 | 가능 | 0 | 0 | 0 |
| SDU | 86 | 86/86 | 1191 | 가능 | **86** | 0 | 0 |
| SNL | 61 | 61/61 | **77** | **주의** | **61** | 0 | 0 |
| Stanford | 41 | 41/41 | 1997 | 가능 | 0 (배열 41, 전부 NaN) | 0 | 0 |
| Stanford_2 | 181 | 181/181 | 2000 | 가능 | 0 (배열 181, 전부 NaN) | 0 | 0 |
| Tongji | 130 | 130/130 | 884 | 가능 | 0 | 0 | 0 |
| UL_PUR | 10 | 10/10 | 223 | 가능 | **10** | 0 | 0 |
| XJTU | 23 | 23/23 | **6352** | 가능 | 0 | 0 | 0 |
| ZN-coin | 140 | 140/140 | 756 | 가능 | 0 | 0 | 0 |

- **IC/DV (dQ/dV) 산출 가능 여부**: `voltage_in_V` 와 `charge/discharge_capacity_in_Ah`
  가 같은 길이의 사이클 내 시계열로 함께 있으므로 **원리적으로 18개 서브셋
  전부에서 산출 가능**합니다 `[확인]`.
  다만 **SNL 은 사이클당 점이 중앙값 77개**로 다른 서브셋의 1/10 수준이라
  미분 곡선의 분해능이 떨어집니다 `[추론]` — 실제 사용 전에 확인이 필요합니다.
  반대편 끝은 XJTU(6,352점)와 Stanford_2(2,000점)입니다.
- **내부저항은 MATR 169셀에만 값이 있습니다** `[확인]`. 나머지 1,213셀은
  키는 있으나 전 사이클 `None` 입니다.
- **`Qdlin`(전압 격자에 재표본한 방전용량 1,000점)도 MATR 에만 있습니다** `[확인]`.

### 6-4. 부문별 — 궤도 예측 연구가 실제로 가능한 곳

| 부문 | 궤도 연구가 가능한 서브셋 | 셀 수 | 비고 |
|---|---|---:|---|
| 소형 IT기기 | CALCE · HNEI · ISU_ILCC · MICH · XJTU | 330 | ISU_ILCC 는 사이클 수 중앙값 3,107 로 궤도 길이가 충분 |
| 전동공구 / 경형 | MATR · HUST · RWTH | 294 | **MATR 만 온도·내부저항·`Qdlin` 3채널을 다 갖춤** — 궤도 연구에 가장 재료가 많음 |
| 전기차 | UL_PUR · Tongji · MICH_EXP · CALB | 185 | UL_PUR 은 10셀뿐. CALB 는 사이클 99개로 짧고 라벨 재현 불가 |
| ESS | SDU | 86 | 온도 있음. **다만 BatteryLife 로더에서 도달 불가** |
| 실험실 전용 | Stanford(41) · Stanford_2(181) · NA-ion(64) · ZN-coin(140) | 426 | Stanford 계열은 점 수가 많아 IC/DV 에 유리. 두 디렉터리가 38셀 중복 |

**부문 관점에서 가장 빈약한 곳은 ESS 와 전기차**입니다 `[추론]`.
ESS 는 SDU 86셀 하나뿐이고, 전기차 185셀 중 CALB 27셀은 사이클이 99개로 짧고
라벨이 재현 불가이며 UL_PUR 은 10셀입니다.

### 6-5. 저장소 안 문서의 궤도 관련 언급

원문 발췌는 15단어 이내로 제한했습니다.

| 위치 | 요약 |
|---|---|
| `upstream/BatteryLife/README.md:116` | `check_soh_curves.ipynb : for checking the degradation trajectory` — **그 노트북은 트리에 없습니다** `[확인]` |
| `upstream/BatteryLife/README.md:179` | 미처리 데이터셋 목록에 `early battery trajectory prediction` 논문 1건을 링크 |
| `data/extracted/READMEs/RWTH_README.md` | 인용 원논문 제목이 `One-shot battery degradation trajectory prediction with deep learning` |
| `upstream/BatteryMFormer/data_provider/data_factory.py:8` | `Data provider for SOH trajectory prediction` |
| `upstream/BatteryMFormer/…/data_loader_soh_optimized.py:836-839` | `trajectory_mask` 로 유효 궤적 구간을 지정 |
| `docs/reports/2026-08-07_prep_ab.md:429-441` | 이 저장소의 기존 분석 — MFormer 지표가 `(샘플 × 미래 사이클)` 궤적 점 단위이고 셀당 유효 점이 `100·eol − 5050` 이라 **수명 가중**이라는 관찰 |
| `findings/registry.yaml:1030` (REP-002) | MFormer 논문 2.2절 `Degradation Trajectory` 의 식 `SOH_i = Qd_i / (Qd_0 × DoD)` 기록 |

**`knee point`(니 포인트) 를 다루는 코드·문서는 저장소 안에 없습니다** `[확인]` —
`knee` 로 전 트리를 검색해 일치하는 것이 없었습니다.

---

## 7. 불일치·이상 항목

이번 조사에서 **직접 확인한** 것만 적습니다.

| # | 항목 | 내용 | 판정 |
|---|---|---|---|
| 1 | README 셀 수 ≠ 실측 | MICH_EXP 12→18 · NA-ion 31→64 · SNL 52→61 · Tongji 108→130 · ZN-coin 100→140. 합 73셀 | `[확인]` |
| 2 | **ZN-coin 극 필드가 뒤바뀜** | pkl 이 `anode_material='MnO2'` · `cathode_material='Zinc'` 로 **140셀 전부** 기록. Zn–MnO2 셀에서 MnO2 는 양극, Zn 이 음극이므로 두 필드가 반대 | `[확인]` |
| 3 | 상위 문서도 같은 축이 뒤바뀜 | `assets/Further_details_of_data_statistics.md` 의 "aging factors" 표에서 **`Cathodes` 열에 Graphite·Carbon 이, `Anodes` 열에 LiCoO2·LFP 가** 들어 있음 | `[확인]` |
| 4 | **RWTH 정격용량이 세 값** | pkl `1.85` · 상위 요약표 `2.05Ah` · 배포 README `3 Ah`. 라벨 코드는 `1.85` 를 하드코딩(`:111-112`) | `[확인]` |
| 5 | SNL 정격용량 종수 | 실측 **5종**(1.1/2.7/2.88/3/3.2), 문서·README 는 **3종** | `[확인]` |
| 6 | CALB 컷오프가 셀마다 다름 | 상한 4.35/4.25, 하한 2.75/2.2/2.5. 문서는 각각 하나만 적음 | `[확인]` |
| 7 | **SDU 86셀 도달 불가** | 전처리 스크립트·README 는 있으나 `datasetName2ids` 와 로더 분기에 없음. MFormer 에도 없음 | `[확인]` |
| 8 | **Stanford_2 181셀은 BatteryLife 로더에 없음** | MFormer 에만 있음(`:201,778`). 상위 요약표에도 없음 | `[확인]` |
| 9 | Stanford / Stanford_2 중복 | 파일명 기준 **38셀 중복**, 합집합 184 | `[확인]` |
| 10 | ISU-ILCC 분모 | 충전 기준만 저장(`preprocess_ISU_ILCC.py:164`). 240셀 중 배포 라벨과 **85 일치 / 155 불일치** | `[확인]` |
| 11 | Tongji 라벨 오프셋 | 첫 교차 100셀 중 **96셀이 배포 = 재현 + 1**. 원인은 `인덱스+1`(`:153`) | `[확인]` |
| 12 | CALB 재현 불가 | 외부 Excel 미배포. 27셀 전부 | `[확인]` |
| 13 | **CALB `use_extrapolation` 미초기화** | `:185-187` 대비 `:202`. 셀 순서에 따라 이전 셀 값이 새어 들어갈 수 있는 구조 | `[확인]` (코드 읽기) |
| 14 | γ⁺·γ⁻ 하드코딩 | MFormer `process_scripts/` 에 `percentile` 호출 0건. 값은 모듈 상수 | `[확인]` |
| 15 | 온도 채널 부재 | 8개 서브셋 **735셀**은 `temperature_in_C` 가 전 사이클 `None`. 추가로 5개 서브셋 **294셀**은 배열은 있으나 **유한값이 하나도 없음**. 실수치가 있는 셀은 **353개(25.5%)** 뿐 | `[확인]` |
| 16 | C-rate 값 부재 | Tongji · SDU 는 `rate_in_C` 가 빈 문자열 | `[확인]` |
| 17 | 배포 라벨 < 재현 가능 셀 | UL_PUR 재현 10 vs 배포 **2** · SDU 86 vs **70** · NA-ion 43 vs **34**. 나머지 **14개** 서브셋은 일치. CALB 는 재현 0 vs 배포 27 이나 외부 파일 미배포라 대조 대상이 아님 | `[확인]` |
| 18 | 문서 문자열과 코드 불일치 | `data_loader.py:481` docstring 이 `history_sohs, future_sohs` 반환이라 적으나 실제는 스칼라 라벨 | `[확인]` |
| 19 | 참조된 노트북 부재 | `README.md:116` 이 가리키는 `check_soh_curves.ipynb` 가 트리에 없음 | `[확인]` |
| 20 | 기존 레코드 합계 오기 | `findings/registry.yaml:480` 이 첫 번호≠1 셀을 **148** 이라 적으나 자체 내역 합과 이번 실측이 모두 **149** | `[확인]` |
| 21 | 문서 오탈자 | 상위 요약표의 Stanford 정격 `024Ah`(0.24 의 오기), Tongji 하한 `2..65V` | `[확인]` |

**#10~#14 는 이번에 새로 찾은 것이 아니라 재확인한 것입니다** — 기존
`findings/registry.yaml` 의 LAB-017 · LAB-014 · LAB-004/013 과 
`docs/reports/2026-08-08_closing_checks.md` 에 이미 기록돼 있고, 이번에 현재
코드와 전수 실측으로 **독립 재현**해 같은 값을 얻었습니다.

---

## 8. 추가 조사 필요

**저장소 바깥 문헌 조사는 이번 범위 밖입니다.** 필요한 항목만 남깁니다.

| # | 남은 질문 | 왜 이번에 못 했는가 |
|---|---|---|
| 1 | ISU-ILCC 의 SOH 분모가 충전·방전 중 **어느 쪽이 옳은가** | 원논문(2024 Cell Reports Physical Science)의 SOH 정의를 봐야 함. 저장소 밖 |
| 2 | Tongji 배포 라벨이 **현재 스크립트가 아닌 이전 판**으로 만들어졌는가 | 저장소에 이전 판이 없음 (기존 LAB-010 과 같은 질문) |
| 3 | CALB Excel `汇总表-L148N58-循环.xlsx` 확보 | 배포되지 않음. 확보 전에는 27셀 라벨 재현 불가 |
| 4 | γ⁺·γ⁻ 상수의 **출처 데이터** | 코드가 계산하지 않아 흔적이 없음 |
| 5 | README 셀 수와 실측이 어긋나는 5개 서브셋 중 **NA-ion(31 vs 64 vs 라벨 34)** 의 설명 | 폐기 필터로 설명되지 않음 |
| 6 | UL_PUR 이 재현 10셀인데 **배포 라벨이 2개뿐**인 이유 | 배포 시점의 필터가 현 코드와 다를 가능성. 확인 수단 없음 |
| 7 | `SDU` 와 `Stanford_2` 가 **왜 배포되었으나 도달 불가인가** | 상위 저장소의 의도를 물어야 함 |
| 8 | MFormer SOH 필터(`filter_threshold`, `MIN_SLOPE_THRESHOLD=1e-4`)가 **어느 셀을 얼마나 지우는가** | SOH 산출 단계를 실행해야 함. 이번 조사는 읽기 전용 |
| 9 | 전해질 조성 | pkl 1,382셀 전부 `None`. 문서에도 5개 서브셋만 있음 |
| 10 | SNL 의 사이클당 77점이 **IC/DV 에 실제로 충분한가** | 미분 곡선을 실제로 산출해 봐야 함 |
| 11 | 부문 매핑 17건의 `[추론]` 을 `[확인]` 으로 올리기 | 각 원논문이 셀의 목표 응용을 명시하는지 봐야 함. 저장소 밖 |

---

## 9. 재현 방법

```
# 셀 단위 전수 census + 데이터셋 단위 요약표 (87.7 GB 를 전부 읽습니다)
.venv-blife/Scripts/python.exe analysis/dataset_metadata_survey.py
```

| 산출 | 경로 |
|---|---|
| 셀 1,382행 | `analysis/out/dataset_cell_census.csv` |
| 데이터셋 18행 | `docs/reports/datasets_metadata.csv` |

스크립트는 루프 전 대상 수와 루프 후 기록 수를 대조하고, **어긋나면 종료 코드
1 로 끝납니다.** 이번 실행은 **1,382 / 1,382 · 실패 0 · 종료 코드 0** 입니다 `[확인]`.
