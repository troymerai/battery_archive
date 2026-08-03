<!-- 자동 생성물입니다. 손으로 고치지 마십시오. -->
<!-- 원본은 findings/registry.yaml 이고, 이 파일은 -->
<!--   python run.py claims -->
<!-- 로 다시 만들어집니다. 여기서 고친 것은 다음 실행에 지워집니다. -->

# PAPER ↔ CODE MAP

레코드 32개. `findings/registry.yaml` 에서 생성했습니다.

판정은 슬롯에서 유도한 것입니다. 판정을 바꾸려면 슬롯을 고치십시오.
유도 규칙은 `findings/SCHEMA.md` 에 있습니다.

## 판정 분포

| 판정 | 개수 | 뜻 |
|---|---|---|
| 일치 | 1 | 논문과 코드가 같다 |
| 불일치 | 2 | 논문과 코드가 다르다 — 발견 |
| 코드전용 | 1 | 논문에서 찾아봤고 없었다 |
| 미정 | 28 | 아직 판정할 수 없다 (대개 논문 미조사) |

## 레코드

| id | 질문 | paper | upstream_doc | code | 판정 |
|---|---|---|---|---|---|
| `DAT-001` | Zn-ion 공칭용량 = 10번째 사이클 방전용량 | 확인 · `부록 A.2 (쪽 확정 필요)` | 미조사 | 확인 · `BatteryLife/process_scripts/preprocess_ZNion.py:52` | **일치** |
| `DAT-002` | 논문 식(1) Qi = ∫\|I\|dt 를 코드가 적분하는가 | 확인 · `식 (1) (절·쪽 확정 필요)` | 미조사 | 확인 · `BatteryLife/process_scripts/preprocess_Farasis.py:362` | **불일치** |
| `DAT-003` | 논문 990셀 / 59화학계 / 421프로토콜 대 배포 데이터 재집계 | 미조사 | 미조사 | 미조사 | **미정** |
| `LAB-001` | 폐기 임계 0.825 의 근거 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:124` | **미정** |
| `LAB-002` | 외삽 창 20 사이클의 근거 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:132` | **미정** |
| `LAB-003` | 외삽이 SOH→cycle 역회귀인 이유 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:143` | **미정** |
| `LAB-004` | CALB λ=0.9 의 근거 | 확인 · `(미확정) 논문에 λ 설정 서술이 있음 — 절·쪽 확정 필요` | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:187,217` | **미정** |
| `LAB-005` | SOC span 나눗셈의 타당성 | 부재확인 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:117-121` | **코드전용** |
| `LAB-006` | nominal 상수 덮어쓰기 2건의 근거 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:111-114` | **미정** |
| `LAB-007` | CALB_25_T25-2.pkl 예외 분기의 근거 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:204-213` | **미정** |
| `LAB-008` | XJTU 가 첫 교차가 아니라 선형 보간을 쓰는 근거 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels_tools/XJTU_tools.py:57-85` | **미정** |
| `LAB-009` | Farasis 라벨 단위가 EFC 인 근거와 다른 서브셋과의 비교 가능성 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels_tools/Farasis_tools.py:37-53` | **미정** |
| `LAB-010` | 논문에 실린 라벨과 현재 스크립트가 같은가 | 미조사 | 확인 · `BatteryLife_Processed v11 릴리스 노트` | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py` | **미정** |
| `LAB-011` | XJTU 라벨의 NaN 이 배포 라벨 파일에도 그대로 들어 있는가 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:81-88 + experiments/results/LABEL_REPORT.md 5절` | **미정** |
| `LAB-012` | MICH_EXP 는 pkl 18개인데 배포 라벨은 12개다. 빠진 6개가 무엇인가 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:124-127 + experiments/results/LABEL_REPORT.md 11절` | **미정** |
| `LAB-013` | SNL 20-80 4셀에 span 나눗셈과 nominal 3.2 덮어쓰기가 겹치는가 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/Extract_life_labels.py:111-121 + experiments/results/LABEL_REPORT.md 12절` | **미정** |
| `LAB-014` | Tongji 배포 라벨이 재현값보다 정확히 1 큰 것이 전 셀에 걸친 현상인가 | 확인 · `논문 §2.2` | 미조사 | 확인 · `experiments/results/nb03_mismatch.json + experiments/results/nb04_extras.json + BatteryLife/process_scripts/Extract_life_labels.py:152-156` | **불일치** |
| `LAB-015` | NA-ion 배포 라벨 34개와 pkl 64개의 차이 30개가 전부 폐기 셀인가 | 미조사 | 미조사 | 확인 · `experiments/results/nb03_cells.json (match=우리만있음) + Extract_life_labels.py:124-127` | **미정** |
| `LAB-016` | RPT · formation 사이클 제거 뒤 cycle_number 를 다시 매겼는가 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/preprocess_ISU_ILCC.py:190-210 + experiments/results/nb04_cycle_numbers.json` | **미정** |
| `LAB-017` | ISU_ILCC 의 SOH 분모가 충전 기준인가 방전 기준인가 | 미조사 | 미조사 | 확인 · `BatteryLife/process_scripts/preprocess_ISU_ILCC.py:266-284,164 + Extract_life_labels.py:121` | **미정** |
| `META-001` | 화학계 59종 — 어느 pkl 필드 조합으로 세는가 | 미조사 | 미조사 | 미조사 | **미정** |
| `META-002` | 포맷 8종 | 미조사 | 미조사 | 미조사 | **미정** |
| `META-003` | 운전온도 9종 | 미조사 | 미조사 | 미조사 | **미정** |
| `META-004` | 프로토콜 421종 | 미조사 | 미조사 | 미조사 | **미정** |
| `META-005` | 990셀 / 99,000샘플 | 미조사 | 미조사 | 미조사 | **미정** |
| `META-006` | 4도메인 분할 기준 (Li / Zn / Na / CALB) | 미조사 | 미조사 | 미조사 | **미정** |
| `META-007` | cycle_data[0]['cycle_number'] 이 서브셋마다 · 서브셋 안에서도 다른가 | 미조사 | 미조사 | 확인 · `experiments/results/nb04_cycle_numbers.json + experiments/results/LABEL_REPORT.md 6절` | **미정** |
| `META-008` | NA-ion 셀별 C-rate 가 pkl 메타에 있는가 | 미조사 | 확인 · `READMEs/NA-ion_README.md 의 Charge/discharge protocols 표` | 부재확인 | **미정** |
| `META-009` | NA-ion README 본문의 25도 단일 서술과 표의 온도가 맞는가 | 미조사 | 확인 · `READMEs/NA-ion_README.md 본문 3행 대 Charge/discharge protocols 표` | 부재확인 | **미정** |
| `REP-001` | BatteryLife 와 BatteryMFormer 의 동명 파일 13개가 전부 다른가 | 미조사 | 미조사 | 확인 · `upstream/BatteryLife 대 upstream/BatteryMFormer 동명 파일 비교` | **미정** |
| `VER-001` | v11 과 v12 의 차이가 XJTU 와 Farasis 뿐인가 | 미조사 | 확인 · `Zenodo record 19688272 (v11) 과 21149533 (v12) 의 Files 표` | 확인 · `manifests/data_md5.txt (v11 20개 전체) + data/zenodo_v11/ 실측 md5 8개` | **미정** |
| `VER-002` | v11 과 v12 각각의 다운로드 용량과 해제 후 디스크 소요 | 미조사 | 확인 · `Zenodo record 19688272 Files 표` | 확인 · `data/zenodo_v11/ 과 data/extracted/ 실측 (117호, 2026-08-03, v11 20개 전부)` | **미정** |

## 레코드 상세

### `DAT-001` — Zn-ion 공칭용량 = 10번째 사이클 방전용량

**판정: 일치** — 양쪽 값이 같습니다

- **paper** — 확인
    - locus: 부록 A.2 (쪽 확정 필요)
    - value: 10번째 사이클의 방전용량을 공칭용량으로 쓴다
    - searched: 부록 A.2
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/preprocess_ZNion.py:52
    - value: 10번째 사이클의 방전용량을 공칭용량으로 쓴다
    - checked_by: CC
- **note** — 일치 사례. 코드는 循环序号 == 10 행의 放电容量/mAh 에 0.001 을 곱해 Ah 로 씁니다. 부록에만 있고 본문에는 없습니다 — 부록을 반드시 보라는 근거.
- **anchors** — ZNION_NOMINAL_CYCLE10

### `DAT-002` — 논문 식(1) Qi = ∫\|I\|dt 를 코드가 적분하는가

**판정: 불일치** — 논문 'Qi = ∫|I|dt 로 정의 — 전류를 시간 적분' 대 코드 '실제 적분은 Farasis 전처리에만 있음. 나머지 서브셋은 사이클러 기록 컬럼을 그대로 사용'

- **paper** — 확인
    - locus: 식 (1) (절·쪽 확정 필요)
    - value: Qi = ∫\|I\|dt 로 정의 — 전류를 시간 적분
    - searched: 본문 수식 절
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/preprocess_Farasis.py:362
    - value: 실제 적분은 Farasis 전처리에만 있음. 나머지 서브셋은 사이클러 기록 컬럼을 그대로 사용
    - checked_by: CC
- **note** — 불일치 사례. 식이 전 서브셋에 적용된 것처럼 읽히지만 적분 구현은 한 곳뿐입니다. 사이클러가 기록한 용량 컬럼은 기기 내부 적산이라 값이 반드시 같지는 않습니다. 어느 서브셋이 어느 방식인지 셀 단위로 짚어야 합니다.
- **anchors** — FARASIS_INTEGRATE

### `DAT-003` — 논문 990셀 / 59화학계 / 421프로토콜 대 배포 데이터 재집계

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 미조사
- **note** — META- 계열 전체의 상위 항목입니다. 01 노트북의 재집계(findings/recount.json)가 나온 뒤 논문 Table 1 과 대조합니다. 순서를 뒤집지 마십시오.

### `LAB-001` — 폐기 임계 0.825 의 근거

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:124
    - value: last_cycle_soh >= 0.825 이면 셀을 데이터셋에서 제외
    - checked_by: CC
- **note** — 0.8 이 EOL 인데 왜 0.825 에서 자르는지가 쟁점. 0.025 라는 여유폭의 출처를 논문에서 찾아야 합니다.
- **anchors** — EXTRACT_LABELS_ABANDON

### `LAB-002` — 외삽 창 20 사이클의 근거

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:132
    - value: regress_cycle_num = 20
    - checked_by: CC
- **note** — 본 경로는 사이클이 20개 미만인 셀에서 길이가 어긋납니다 (range(n-20, n) 은 항상 20개, cycle_data[-20:] 는 n개). XJTU 경로는 min(20, len) 으로 잘라 쓰므로 어긋나지 않습니다. verify/labels.py 가 이 경우를 본경로:외삽불가 로 표시합니다.
- **anchors** — EXTRACT_LABELS_ABANDON

### `LAB-003` — 외삽이 SOH→cycle 역회귀인 이유

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:143
    - value: fit(total_SOHs, total_cycle_numbers) — SOH 를 설명변수로 둠
    - checked_by: CC
- **note** — 통상적인 방향(cycle→SOH)의 반대입니다. 잔차를 어느 축에서 최소화하는지가 달라 예측값이 갈립니다. XJTU_tools 의 꼬리 외삽도 같은 방향입니다.
- **anchors** — EXTRACT_LABELS_ABANDON

### `LAB-004` — CALB λ=0.9 의 근거

**판정: 미정** — 양쪽 확인이나 value 가 비어 비교할 수 없습니다

- **paper** — 확인
    - locus: (미확정) 논문에 λ 설정 서술이 있음 — 절·쪽 확정 필요
    - searched: 초기 조사에서 서술의 존재만 확인. 정확한 위치를 다시 잡아야 함
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:187,217
    - value: CALB 만 0.9, 나머지는 0.8
    - checked_by: CC
- **note** — 초기 조사에서 '코드 전용' 으로 오판했던 항목. 논문에 서술이 있음. 위치 미확정이므로 판정 보류.
- **anchors** — EXTRACT_LABELS_CALB_LAMBDA

### `LAB-005` — SOC span 나눗셈의 타당성

**판정: 코드전용** — 논문에서 찾아봤고 없었습니다

- **paper** — 부재확인
    - searched: 논문 전문 검색 — SOC · span · partial cycling 관련 서술 없음. 이 결과는 데이터셋 보고서 v2 작성 과정에서 사람이 수행한 검색이며 CC 가 논문을 직접 읽어 확인한 것이 아닙니다. 슬롯을 닫을지는 사람이 정합니다
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:117-121
    - value: soh = Qd / nominal / (SOC_interval[1] - SOC_interval[0]), 0 이면 1. v11 전수 1,382셀 중 span 이 1 이 아닌 셀은 239개(17.3%) — ISU_ILCC 181 · RWTH 48 · MICH_EXP 6 · SNL 4. RWTH 48셀은 SOC_interval 이 전부 [0.2, 0.8](span 0.6)이고, span 을 적용하면 48/48 배포 라벨과 일치하며 빼면 0/48 이 됩니다
    - checked_by: CC
- **note** — 랩미팅 미해결. 부분 구간만 순환한 셀의 SOH 를 전구간 기준으로 되돌리려는 보정으로 보이나 근거 미확인. 본 경로는 부호를 취하지 않아 interval 이 역순이면 SOH 부호가 뒤집힙니다 (XJTU 경로는 abs). 1,382셀 전수에도 역순 interval 은 없었습니다. 2026-08-03 v11 전수 실행에서 RWTH 48셀이 더해졌습니다 — pkl 의 nominal_capacity_in_Ah 가 48셀 전부 1.85 로 하드코딩 상수와 같아 nominal 덮어쓰기는 값을 바꾸지 않고(LAB-006), 실제로 결과를 바꾸는 것은 span 나눗셈 하나뿐입니다. span 0.6 을 적용하면 48/48 이 배포 라벨과 일치하고 빼면 0/48 입니다. 즉 SNL 4셀에 이어 RWTH 48셀에서도 이 나눗셈이 배포값을 맞추는 쪽이고, MICH_EXP 6셀에서만 반대로 라벨을 없앱니다. 같은 나눗셈이 서브셋에 따라 정반대로 작동하는데 근거는 여전히 논문에서 확인되지 않습니다. 표는 LABEL_REPORT.md 3절(RWTH) · 11절(MICH_EXP) · 12절(SNL) · 15절(변형 비교). 아래는 6서브셋 440셀 시점의 기록입니다 — MICH_EXP 6셀은 span 을 적용하면 SOH 가 0.9956~0.9992 로 평평해 전부 폐기(>=0.825)되어 라벨이 안 생기고, 빼면 정확히 그 절반(0.4978~0.4996)이라 첫 사이클에서 교차해 라벨이 전부 1 이 됩니다. 어느 쪽도 수명 라벨이 아닙니다. SNL 4셀은 span 을 적용해야 배포 라벨과 일치하고(711/976/792/840 전부 일치) 빼면 전부 1 이 됩니다. 즉 같은 나눗셈이 한 서브셋에서는 배포값을 맞추고 다른 서브셋에서는 라벨을 없앱니다. 근거는 여전히 미확인. 그때의 표는 experiments/results/prev_6subset/LABEL_REPORT.md 3·4·7 절에 보존했습니다.
- **anchors** — EXTRACT_LABELS_SOC_SPAN

### `LAB-006` — nominal 상수 덮어쓰기 2건의 근거

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:111-114
    - value: RWTH → 1.85, SNL_18650_NCA_25C_20-80 → 3.2. v11 전수 실행 결과 두 건 모두 pkl 원값과 같아 덮어쓰기가 값을 바꾸지 않습니다 — RWTH 48셀의 pkl nominal 은 전부 1.85, SNL 20-80 4셀은 전부 3.2
    - checked_by: CC
- **note** — pkl 의 nominal_capacity_in_Ah 를 무시하고 파일명 접두사로 덮어씁니다. 왜 그 두 건만인지, 그 값이 어디서 왔는지가 쟁점. SOH 전체가 이 값으로 나뉘므로 라벨에 직접 영향합니다. 2026-08-03 v11 전수 관찰 — 두 건 다 pkl 원값과 상수가 같아 **이 덮어쓰기는 현재 배포본에서 아무 값도 바꾸지 않습니다.** 코드가 하는 일이 없다는 것이 근거를 대신하지는 않습니다: 왜 그 두 접두사만 하드코딩되어 있는지, 그 값이 어디서 왔는지는 그대로 미확인입니다. v2 는 RWTH 공칭용량으로 세 값이 돌아다닌다고 적습니다 — 부록 A.3 3 Ah, 저장소 문서 2.05 Ah, 코드 1.85. **pkl 은 1.85 입니다** (48셀 전부, 고유값 하나). 즉 코드와 pkl 은 맞고 논문 부록·저장소 문서와 갈립니다. 논문 부록 A.3 을 직접 읽어 확인하지 않았으므로 paper 슬롯은 미조사로 둡니다. 표는 LABEL_REPORT.md 3절.
- **anchors** — EXTRACT_LABELS_NOMINAL_RWTH

### `LAB-007` — CALB_25_T25-2.pkl 예외 분기의 근거

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:204-213
    - value: 이 셀만 마지막 20 사이클 대신 SOH<=0.925 도달 지점 앞 20 사이클로 회귀
    - checked_by: CC
- **note** — 코드 주석은 the last several cycles have sudden capacity rise 라고만 적혀 있습니다. 같은 블록에 CALB_35_B229 의 696번 사이클 건너뛰기(:191-193)와 use_extrapolation 변수가 있는데, 후자는 min(SOH)>=0.925 이면서 EOL 미도달인 셀에서 이전 반복의 값이 남아 쓰일 수 있는 구조입니다. CALB 는 어차피 재현불가라 실행으로는 확인되지 않습니다.
- **anchors** — EXTRACT_LABELS_CELL_EXCEPTION

### `LAB-008` — XJTU 가 첫 교차가 아니라 선형 보간을 쓰는 근거

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels_tools/XJTU_tools.py:57-85
    - value: 마지막 하강 교차점을 선형 보간 (max(crossings)), 실패 시 0.8<last<0.825 이면 꼬리 20사이클 외삽
    - checked_by: CC
- **note** — 본 경로는 첫 교차, XJTU 는 마지막 교차입니다. 정반대입니다. 용량이 되살아난 셀에서 라벨 값이 크게 갈립니다. XJTU.zip 이 있어야 검증됩니다 (data_md5.txt 의 core 세트).
- **anchors** — EXTRACT_LABELS_XJTU_BRANCH; XJTU_INTERPOLATE

### `LAB-009` — Farasis 라벨 단위가 EFC 인 근거와 다른 서브셋과의 비교 가능성

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels_tools/Farasis_tools.py:37-53
    - value: 외부 Excel 의 efc life 열을 그대로 읽음. 사이클 번호가 아니라 EFC
    - checked_by: CC
- **note** — 단위가 다르면 도메인 간 비교가 성립하는지 자체가 쟁점입니다. 같은 파일의 다른 함수 extract_farasis_life_labels 는 90% SOH EFC 를 계산하지만, 실제로 호출되는 것은 Excel 을 읽는 쪽입니다 (Extract_life_labels.py:94).
- **anchors** — EXTRACT_LABELS_FARASIS_BRANCH; FARASIS_EXCEL

### `LAB-010` — 논문에 실린 라벨과 현재 스크립트가 같은가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 확인
    - locus: BatteryLife_Processed v11 릴리스 노트
    - value: CALB 수명 라벨 재계산, 새 계산 스크립트를 GitHub 에 업데이트
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py
    - value: 현 스크립트 (커밋 9572e47)
    - checked_by: CC
- **note** — 불일치 정황. 릴리스 노트가 라벨 재계산을 명시하므로 논문 시점 라벨과 현 스크립트 산출이 다를 수 있습니다. 다만 upstream_doc 은 판정에 들어가지 않으므로 판정은 보류입니다 — 논문에 실린 라벨 값을 직접 확인해야 확정됩니다. 이 레코드가 이 저장소 전체의 전제입니다: 논문은 정답지가 아니라 비교 대상입니다.

### `LAB-011` — XJTU 라벨의 NaN 이 배포 라벨 파일에도 그대로 들어 있는가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:81-88 + experiments/results/LABEL_REPORT.md 5절
    - value: v11 배포 XJTU_labels.json 에 비유한 값이 **0개** 입니다 (키 23개, 원문에 NaN 리터럴 없음, null 0개). XJTU.zip 을 보유해 23셀을 재계산한 결과도 비유한 라벨이 0개이고 23/23 이 배포값과 일치합니다. 상태는 XJTU:보간 22셀 · XJTU:꼬리외삽 1셀
    - checked_by: CC
- **note** — 2026-08-03 v11 전수 실행. 직전 판(6서브셋)에서는 XJTU.zip 미보유라 배포 파일만 열어보고 code 슬롯을 미조사 로 두었습니다. 이번에 pkl 23개를 받아 재계산했고 배포 파일과 재계산 양쪽에서 NaN 이 0개임을 확인했습니다. **NaN 이 나오지 않는 것은 v11 XJTU 배포본이 23셀뿐이기 때문일 수 있습니다** — v12 의 XJTU.zip 은 396.9MB 에서 1.5GB 로 바뀐 완전판이고 Life labels.zip 도 함께 바뀌었으므로(VER-001), v12 에서는 다를 수 있습니다. 이 레코드는 v11 에 대한 것입니다. 상위 코드에 NaN 을 만들 수 있는 경로가 있다는 것(cycle_life_label_to_int 가 비유한값을 그대로 반환)은 코드에서 확인되며, 그 경로가 v11 데이터에서는 한 번도 타지 않았습니다. route_of() 가 XJTU 를 선형 보간 경로로 올바르게 분기하는 것도 함께 확인했습니다 (23셀 전부 route=XJTU).
- **anchors** — EXTRACT_LABELS_XJTU_BRANCH

### `LAB-012` — MICH_EXP 는 pkl 18개인데 배포 라벨은 12개다. 빠진 6개가 무엇인가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:124-127 + experiments/results/LABEL_REPORT.md 11절
    - value: 빠진 6개는 파일명이 50-100 인 6셀 전부이며 다른 셀은 하나도 빠지지 않음. 6셀 모두 SOC_interval 이 [0.5, 1] 이고 last SOH 가 0.9956~0.9992 라 폐기 임계 0.825 를 넘어 상위 코드가 continue 로 건너뜀
    - checked_by: CC
- **note** — 2026-08-03 실행 관찰. 파일명의 50-100 과 pkl 의 SOC_interval [0.5, 1] 이 일치합니다 — 이름과 필드가 어긋난 것이 아닙니다. 6셀 모두 첫 SOH · 마지막 SOH · 곡선 최소 SOH 가 세 자리까지 같아 곡선이 평평합니다 (171~557 사이클). 대조군인 MICH_01R · 02C · 03H 는 SOC 구간만 0-100 으로 다르고 전류·온도가 같은데, 셋 다 정상적으로 라벨이 생기고 배포값과 일치합니다 (269 · 204 · 107). no_soc_span 변형에서는 6셀 전부 라벨이 1 이 되는데 이것도 수명 라벨로 쓸 수 없습니다. 왜 곡선이 평평한지는 조사하지 않았습니다 — 전처리에서 방전용량이 어떻게 만들어졌는지를 봐야 합니다. 2026-08-03 v11 전수 추가 관찰 — **이 현상은 MICH_EXP 전용이 아닙니다.** 첫 SOH 와 곡선 최소 SOH 의 차가 0.01 미만인 셀을 1,382셀에서 세면 26개이고 CALB 17 · MICH_EXP 6 · NA-ion 2 · ZN-coin 1 입니다. CALB 17셀은 전부 사이클 99개짜리이고 첫 SOH 가 1.00~1.03 으로 1 을 넘습니다(다만 CALB 는 상위 코드가 외부 Excel 용량을 쓰므로 여기 값과 기준이 다릅니다). 서브셋별로 평평한 이유가 같은지는 확인하지 않았습니다. 목록은 LABEL_REPORT.md 7절과 nb04_extras.json 의 curve_flat_code.
- **anchors** — EXTRACT_LABELS_ABANDON; EXTRACT_LABELS_SOC_SPAN

### `LAB-013` — SNL 20-80 4셀에 span 나눗셈과 nominal 3.2 덮어쓰기가 겹치는가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/Extract_life_labels.py:111-121 + experiments/results/LABEL_REPORT.md 12절
    - value: 겹칩니다. SNL_18650_NCA_25C_20-80_0.5-0.5C_a~d 4셀은 접두사 일치로 nominal 이 3.2 로 덮어써지고 동시에 SOC_interval [0.2, 0.8] 이라 span 0.6 으로 나뉩니다. 다만 이 4셀의 pkl 원 nominal 도 3.2 여서 덮어쓰기는 값을 바꾸지 않습니다 — 실제로 결과를 바꾸는 것은 span 나눗셈뿐
    - checked_by: CC
- **note** — 2026-08-03 실행 관찰. 4셀 모두 배포 라벨과 일치합니다 (711 · 976 · 792 · 840). span 을 빼면 넷 다 라벨이 1 이 되므로, 이 4셀에서는 span 나눗셈이 배포값을 맞추는 쪽입니다 (MICH_EXP 6셀에서는 반대로 라벨을 없앱니다 — LAB-005). span 적용 시 첫 SOH 가 1.03~1.06 으로 1 을 넘습니다. SNL 중도절단 9셀(폐기)에 이 4셀은 들어 있지 않습니다. RWTH → 1.85 덮어쓰기는 2026-08-03 v11 전수에서 확인했습니다 — RWTH 48셀의 pkl nominal 이 전부 1.85 라 SNL 쪽과 똑같이 덮어쓰기가 값을 바꾸지 않고, 실제로 결과를 바꾸는 것은 span 나눗셈뿐입니다(LAB-005 · LAB-006). 즉 nominal 덮어쓰기 2건은 **둘 다** 현재 배포본에서 아무 값도 바꾸지 않습니다.
- **anchors** — EXTRACT_LABELS_NOMINAL_RWTH; EXTRACT_LABELS_SOC_SPAN

### `LAB-014` — Tongji 배포 라벨이 재현값보다 정확히 1 큰 것이 전 셀에 걸친 현상인가

**판정: 불일치** — 논문 '라벨은 SOH 가 80% 이하가 되는 cycle number 다 (consider the cycle number at which the SOH becomes no larger than 80% as the battery life)' 대 코드 '배포 Tongji 라벨은 실제 cycle_number 가 아니라 **배열 인덱스 + 2** 입니다. 첫 교차 100셀에서 배포 − 재현 이 96셀은 +1, 4셀은 0 이고, 교차 지점의 실제 cycle_number 는 재현값보다 1~18 만큼 큽니다(중앙 무리는 +1 이 51셀, 나머지는 +2 ~ +18 로 흩어짐). 배포 라벨이 실제 cycle_number 와 같아지는 것은 교차 지점 앞에 결번이 하나도 없는 셀뿐입니다(50셀). v11 전수 1,382셀의 불일치는 259셀이고 ISU_ILCC 155셀(분모 문제 — LAB-017)과 Tongji 104셀뿐입니다. 나머지 16개 서브셋의 불일치는 0'

- **paper** — 확인
    - locus: 논문 §2.2
    - value: 라벨은 SOH 가 80% 이하가 되는 cycle number 다 (consider the cycle number at which the SOH becomes no larger than 80% as the battery life)
    - searched: §2.2 라벨 정의 문단. 이 인용은 데이터셋 보고서 v2 경유로 들어온 것이며 CC 가 논문 PDF 를 직접 열어 확인한 것이 아닙니다
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: experiments/results/nb03_mismatch.json + experiments/results/nb04_extras.json + BatteryLife/process_scripts/Extract_life_labels.py:152-156
    - value: 배포 Tongji 라벨은 실제 cycle_number 가 아니라 **배열 인덱스 + 2** 입니다. 첫 교차 100셀에서 배포 − 재현 이 96셀은 +1, 4셀은 0 이고, 교차 지점의 실제 cycle_number 는 재현값보다 1~18 만큼 큽니다(중앙 무리는 +1 이 51셀, 나머지는 +2 ~ +18 로 흩어짐). 배포 라벨이 실제 cycle_number 와 같아지는 것은 교차 지점 앞에 결번이 하나도 없는 셀뿐입니다(50셀). v11 전수 1,382셀의 불일치는 259셀이고 ISU_ILCC 155셀(분모 문제 — LAB-017)과 Tongji 104셀뿐입니다. 나머지 16개 서브셋의 불일치는 0
    - checked_by: CC
- **note** — 2026-08-03 v11 전수(18서브셋 1,382셀) 실행에서 남은 볼 곳 하나가 좁혀졌습니다. 논문 §2.2 의 정의(실제 cycle_number)와 배포 라벨을 셀 단위로 맞춰 본 결과, **배포 라벨은 실제 cycle_number 가 아닙니다.** Tongji 첫 교차 100셀에서 교차 지점의 실제 cycle_number − 재현 라벨 이 1 부터 18 까지 흩어지는데(결번이 교차 앞에 몇 개 있느냐에 따라), 배포 − 재현 은 96셀에서 일정하게 +1 입니다. 즉 배포 라벨은 배열 인덱스에 상수 1 을 더한 값이지 번호를 읽은 값이 아닙니다. 결번이 있는 다른 두 서브셋이 이것을 뒷받침합니다 — RWTH 48셀은 셀마다 결번이 15~18개 있는데도 배포 라벨이 재현값(인덱스 기반)과 48/48 일치하고 실제 cycle_number 와는 48/48 갈립니다. HNEI 14셀도 결번이 15~18개씩 있으나 전부 교차 지점 뒤라 세 값이 같습니다. 따라서 이 +1 은 cycle_number 의미로 설명되지 않으며, 남은 볼 곳은 LAB-010(배포 라벨이 현 스크립트가 아니라 이전 판으로 만들어졌는가) 하나입니다. 확인 전이며 사실로 기록하지 않습니다. 표는 LABEL_REPORT.md 6절. 아래는 6서브셋 440셀 시점의 기록입니다. 차이값 분포가 한 줄입니다 — 104셀 전부 delta=+1 이고 흩어진 값이 없습니다. 첫교차 분기 96셀과 외삽 분기 8셀 양쪽에서 같은 크기로 어긋납니다. 배포 라벨 키가 -# 를 쓰고 pkl 파일명이 -- 를 쓰는 차이는 대조 전에 맞췄으므로 이 현상의 원인이 아닙니다(전수 확인함, 위 value). 같은 날 후속 전수 조사에서 앞서 적어 둔 볼 곳 (1) 이 좁혀졌습니다 — cycle_number 오프셋은 130셀에 균일하므로(전부 2) 일치 4셀과 불일치 104셀을 가르지 못합니다. 결번도 가르지 못합니다. 교차 지점 SOH 도 두 무리가 구별되지 않습니다(일치 4셀 교차직전 0.8005~0.8074, 대조군 6셀 0.8006~0.8127 로 겹침). 앞서 적어 둔 볼 곳 (2) already_spent_cycles 도 130셀 전부 0 이라 가르지 못합니다. 즉 pkl 쪽에서 잰 값 중 두 무리를 가르는 것을 찾지 못했습니다. 남은 볼 곳은 (3) 배포 라벨이 현 스크립트가 아니라 이전 판으로 만들어졌는지(LAB-010) 하나입니다. 확인 전이며 사실로 기록하지 않습니다. 상세 표는 experiments/results/TONGJI_REPORT.md 입니다. 곁가지 관찰 하나 — cycle_number[0]=2 는 Tongji 전용이 아닙니다. CALB 27셀 중 17셀도 2 에서 시작합니다(나머지 10셀은 1). MICH_EXP · NA-ion · SNL · ZN-coin 은 전 셀이 1 입니다. CALB 는 재현불가(외부 Excel)라 라벨 대조 대상이 아니어서 이 현상과 이어지는지는 확인 전입니다.

### `LAB-015` — NA-ion 배포 라벨 34개와 pkl 64개의 차이 30개가 전부 폐기 셀인가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: experiments/results/nb03_cells.json (match=우리만있음) + Extract_life_labels.py:124-127
    - value: 아닙니다. 30개 중 21개만 폐기(last SOH >= 0.825)이고, 나머지 9개는 상위 규칙대로면 라벨이 만들어져야 하는데 배포 JSON 에 키가 없음. 9셀의 재현 라벨은 1 · 1 · 1 · 1 · 62 · 65 · 81 · 87 · 96
    - checked_by: CC
- **note** — 2026-08-03 v11 전수 재확인 — NA-ion 30셀 구도는 그대로입니다(폐기 21 + 우리만있음 9). 전수로 넓히면 우리만있음 은 33셀이고 SDU 16 · NA-ion 9 · UL_PUR 8 입니다. 첫 교차로 한정하면 30셀(SDU 16 · NA-ion 9 · UL_PUR 5)이 되어 v2 의 30 과 서브셋별로 정확히 맞습니다. 이하는 6서브셋 시점의 기록입니다. 폐기 21셀은 직전 조사의 Na-ion 21 과 맞습니다 — 즉 기존의 21 은 폐기 셀 수이고, 배포 라벨에서 빠진 셀 수(30)는 그보다 많습니다. 9셀 중 4개는 재현 라벨이 1 인데(첫 사이클에서 이미 SOH<=0.8) 이런 셀이 배포에서 빠진 것인지, 다른 기준이 있는지는 확인 전입니다. 상위 코드에는 라벨 100 미만을 거르는 분기가 주석 처리된 채 남아 있습니다 (:157-160) — 그 분기가 살아 있던 판본으로 배포 라벨이 만들어졌다면 62 · 65 · 87 · 96 중 일부가 남는 것을 설명하지 못하므로, 이것도 추정일 뿐 확인이 아닙니다.
- **anchors** — EXTRACT_LABELS_ABANDON

### `LAB-016` — RPT · formation 사이클 제거 뒤 cycle_number 를 다시 매겼는가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/preprocess_ISU_ILCC.py:190-210 + experiments/results/nb04_cycle_numbers.json
    - value: 서브셋마다 다릅니다. ISU_ILCC 전처리는 RPT 뒤 사이클을 버린 다음 :207-209 에서 1..N 으로 **다시 매깁니다** — 그래서 240셀 전부 결번이 없습니다. 반면 배포 pkl 전체 1,382셀 중 결번이 남아 있는 셀이 134개 있습니다: Tongji 72 · RWTH 48 · HNEI 14. 나머지 15개 서브셋은 결번이 0
    - checked_by: CC
- **note** — 2026-08-03 v11 전수 관찰. 부록 A.1 이 RPT · formation 사이클 제거를 밝히지만 **제거 후 번호를 다시 매기는지는 논문에 적혀 있지 않습니다**(논문 미확인이므로 paper 슬롯은 미조사). 데이터에서는 두 가지가 함께 나옵니다 — 재번호가 된 서브셋(ISU_ILCC, 결번 0)과 결번이 그대로 남은 서브셋(Tongji · RWTH · HNEI)입니다. 결번이 있다고 해서 라벨이 갈리는 것은 아닙니다: HNEI 14셀은 셀마다 15~18개의 결번이 있는데 전부 교차 지점 **뒤** 라 실제 cycle_number · 재현 라벨 · 배포 라벨 셋이 같습니다. RWTH 48셀은 결번이 교차 앞에 있어 실제 cycle_number 가 48/48 배포 라벨과 갈립니다. 즉 갈림을 만드는 것은 결번의 유무가 아니라 **교차 지점 앞에 결번이 있는가** 입니다. 표는 LABEL_REPORT.md 6절.

### `LAB-017` — ISU_ILCC 의 SOH 분모가 충전 기준인가 방전 기준인가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: BatteryLife/process_scripts/preprocess_ISU_ILCC.py:266-284,164 + Extract_life_labels.py:121
    - value: 충전 기준입니다. calculate_soc_start_and_end() 는 충전 쪽 charge_start_soc 와 방전 쪽 discharge_end_soc 를 **둘 다** 계산하지만(:269-279), :164 의 soc_interval = [charge_start_soc[name], 1] 이 충전 쪽만 저장합니다. 그 결과 Extract_life_labels.py:121 의 분모 nominal x span 이 min(Qc1, 0.25) 와 항등이 됩니다. 재현 결과 코드 그대로는 240셀 중 85셀 일치(35.4%)이고, 분모만 방전 기준 min(Qd1, nominal) 로 바꾸면 239셀 일치입니다
    - checked_by: CC
- **note** — 2026-08-03 v11 전수 관찰. verify/labels.py 에 --variant discharge_denom 을 더해 확인했습니다. 이 변형은 ISU_ILCC 에만 걸리며 다른 17개 서브셋에서는 code 와 한 셀도 갈리지 않는 것을 확인했습니다(갈리는 셀 155개가 전부 ISU_ILCC). 잔여 1셀은 ISU-ILCC_G14C4 이고 분모 문제가 아닙니다 — 이 셀만 외삽 분기를 타서 재현 166 대 배포 169 로 갈립니다(Qc1 0.1936 · Qd1 0.1903 · 사이클 168). ISU_ILCC 240셀 중 181셀이 자기만의 SOC_interval 값을 갖고 59셀이 [0, 1] 을 공유하는데, 후자는 Qc1 이 0.25 이상이라 span 이 1 로 잘린 셀입니다. **이 결과가 방전 기준이 옳다는 뜻은 아닙니다.** 배포 라벨을 무엇으로 만들었는지를 좁힌 것이고, 상위 코드가 무엇을 하는지는 위 value 그대로입니다. 어느 쪽이 옳은지는 논문 정의를 봐야 하며 아직 보지 않았습니다. 표는 LABEL_REPORT.md 2절.
- **anchors** — EXTRACT_LABELS_SOC_SPAN

### `META-001` — 화학계 59종 — 어느 pkl 필드 조합으로 세는가

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 미조사
- **note** — cathode_material + anode_material + electrolyte_material 조합으로 추정. 01 노트북이 이 조합의 고유값을 셉니다. 조합 방식이 다르면 종수가 달라지므로, 59 를 맞추려 조합을 고르지 마십시오 — 세고 나서 갈리면 갈린다고 적습니다.

### `META-002` — 포맷 8종

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 미조사
- **note** — form_factor 고유값을 세면 즉시 나옵니다. META- 중 가장 빨리 닫히는 항목.

### `META-003` — 운전온도 9종

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 미조사
- **note** — temperature_in_C 는 셀마다 없을 수 있습니다. 필드가 없는 셀의 온도가 어디서 오는지 불명 — 파일명이나 서브셋 README 일 수 있습니다. 01 노트북이 보유 셀 비율을 냅니다. 못 찾으면 조사했으나불명 입니다.

### `META-004` — 프로토콜 421종

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 미조사
- **note** — charge_protocol 이 다단이면 값이 multi 라 데이터만으로 구별되지 않습니다. 01 노트북이 multi 비율을 냅니다. 부록에 프로토콜 목록이 없으면 이 항목은 조사했으나불명 으로 닫힙니다 — 그것이 정상 결말입니다.

### `META-005` — 990셀 / 99,000샘플

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 미조사
- **note** — 배포 데이터 재집계와 대조합니다. 샘플 수는 셀 수와 정의가 다릅니다 — 어떤 단위로 세는지(사이클 창? 셀당 고정 개수?)를 먼저 확정해야 합니다. 2026-08-03 재집계는 보유 6서브셋 440셀뿐이라 990 과 직접 대조되지 않습니다. total_MICH 를 집계에서 제외했습니다 — Zenodo v11 의 20개 파일에 total_MICH.zip 이 없어 배포 pkl 서브셋이 아니고, 로컬 사본을 세면 MICH 와 MICH_EXP 셀이 이중 계산됩니다. 다만 배포 Life labels.zip 안에는 total_MICH_labels.json(키 52개)이 실제로 들어 있습니다 — 라벨 파일은 배포되고 pkl 서브셋은 배포되지 않는 비대칭입니다. 재집계 결과는 findings/recount.json.

### `META-006` — 4도메인 분할 기준 (Li / Zn / Na / CALB)

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 미조사
- **note** — CALB 만 화학계가 아니라 제조사 이름입니다. 나머지 셋과 분류 축이 다른데 왜 같은 층위에 놓이는지가 쟁점. verify/labels.py 의 _DOMAIN 은 파일 이름에서 읽어낸 추정일 뿐이며, 근거를 찾기 전까지 우리가 이렇게 묶었다 이상의 뜻이 없습니다.

### `META-007` — cycle_data[0]['cycle_number'] 이 서브셋마다 · 서브셋 안에서도 다른가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: experiments/results/nb04_cycle_numbers.json + experiments/results/LABEL_REPORT.md 6절
    - value: 다릅니다. v11 전수 1,382셀에서 첫 번호가 1 이 아닌 셀이 148개 있습니다 — Tongji 130셀 전부 2, CALB 27셀 중 17셀이 2(나머지 10셀은 1), CALCE 13셀 중 1셀이 2, HUST 77셀 중 1셀이 3. 나머지 14개 서브셋은 전 셀이 1. 즉 서브셋 사이에서도 갈리고 CALB · CALCE · HUST 는 **같은 서브셋 안에서도** 갈립니다
    - checked_by: CC
- **note** — 2026-08-03 v11 전수 집계. 이 값이 왜 서브셋마다 다른지, 왜 한 서브셋 안에서도 갈리는지는 이 집계가 말하지 않습니다 — 서브셋마다 전처리 스크립트가 다르므로 각 preprocess_*.py 를 봐야 합니다. 라벨과의 관계는 LAB-016 에 있습니다: 첫 번호가 2 라고 해서 라벨이 갈리는 것도 아니고(Tongji 는 갈리고 CALB 는 라벨 자체가 재현불가), 첫 번호가 1 이라고 안전한 것도 아닙니다(RWTH 48셀은 첫 번호가 1 인데 결번 때문에 갈립니다). 결번이 남아 있는 서브셋은 Tongji 72셀 · RWTH 48셀 · HNEI 14셀 셋뿐이고 합 134셀입니다.

### `META-008` — NA-ion 셀별 C-rate 가 pkl 메타에 있는가

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 확인
    - locus: READMEs/NA-ion_README.md 의 Charge/discharge protocols 표
    - value: File_name · Current · Temperature · Nominal capacity 4열 표에 셀별 C-rate 가 있음. 표 행 69개
    - checked_by: CC
- **code** — 부재확인
    - searched: 배포 pkl 의 charge_protocol · discharge_protocol 필드를 NA-ion 64셀 전부에서 집계(findings/recount.json). 셀별 C-rate 를 구별할 수 있는 값이 없음
    - checked_by: CC
- **note** — 2026-08-03 v11 전수 관찰. C-rate 는 README 표가 유일한 출처이므로 findings/na_ion_crate.json 에 파일명 ↔ C-rate 매핑을 정규화해 두었습니다. 파싱 규칙(어느 열을 무엇으로 읽었는지)은 그 파일의 parse_rule 과 LABEL_REPORT.md 8절에 있습니다. **v2 와 갈리는 점이 하나 있습니다** — v2 는 5셀이 매핑되지 않았고 그 이름이 2750-30_… · 5000-25_… 형태라고 적지만, 이번 파싱에서는 pkl 64셀이 전부 매핑됩니다. 매핑되지 않는 5개는 셀이 아니라 README 행입니다(표에는 있는데 배포 pkl 이 없는 행: 2750-30_…45_2 · 4000-30_…45_7 · 5000-25_…38_5 · 38_7 · 38_8). 즉 5 라는 수는 맞고 어느 쪽에 남는가가 갈립니다. C-rate 구간별 집계는 파일명이 일반형(270040-…)인 59셀로 한정하면 v2 의 28/31 과 맞고, 타임스탬프형 5셀을 넣으면 64셀이 되면서 v2 의 세 구간이 덮지 않는 3.9C 가 하나 생깁니다.

### `META-009` — NA-ion README 본문의 25도 단일 서술과 표의 온도가 맞는가

**판정: 미정** — code 슬롯이 미조사입니다

- **paper** — 미조사
- **upstream_doc** — 확인
    - locus: READMEs/NA-ion_README.md 본문 3행 대 Charge/discharge protocols 표
    - value: 본문은 There are 12 different charge/discharge protocols in this dataset at 25 degrees Celsius 라고 적는데, 표 69행 중 5행의 Temperature 열이 30 입니다 (25도 64행 · 30도 5행). 그 5행 중 3행은 배포 pkl 이 실재하는 셀입니다
    - checked_by: CC
- **code** — 부재확인
    - searched: 배포 pkl 의 cycle_data[*].temperature_in_C 를 NA-ion 64셀에서 집계(findings/recount.json). 시험 설정 온도를 담은 필드가 없어 README 서술과 대조할 코드 쪽 값이 없음
    - checked_by: CC
- **note** — 2026-08-03 v11 전수 관찰. 서술과 표가 어긋난다는 것만 적습니다. 어느 쪽이 옳은지는 이 레코드가 말하지 않습니다 — 30 이 실제 시험 온도인지 표기 오류인지 확인할 방법이 배포물 안에 없습니다. 온도 열 원값은 findings/na_ion_crate.json 의 temperature_histogram 과 mapping[*].temperature_C 에 있습니다. 이 어긋남이 라벨에 영향을 주지는 않습니다 — 온도는 라벨 계산식에 들어가지 않습니다.

### `REP-001` — BatteryLife 와 BatteryMFormer 의 동명 파일 13개가 전부 다른가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 미조사
- **code** — 확인
    - locus: upstream/BatteryLife 대 upstream/BatteryMFormer 동명 파일 비교
    - value: 동명 파일 13개가 전부 상이
- **note** — 병합 불가의 근거입니다. 두 저장소를 하나로 합치거나 한쪽 코드를 다른 쪽에 끼워 쓰면 안 됩니다. 재검증 방법은 04 노트북에 있습니다. 어느 13개인지 파일 목록을 code 슬롯에 채워 넣으십시오.

### `VER-001` — v11 과 v12 의 차이가 XJTU 와 Farasis 뿐인가

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 확인
    - locus: Zenodo record 19688272 (v11) 과 21149533 (v12) 의 Files 표
    - value: 20개 중 md5 가 다른 것은 3개 — XJTU.zip · Life labels.zip · READMEs.zip. 나머지 17개는 동일
    - checked_by: CC
- **code** — 확인
    - locus: manifests/data_md5.txt (v11 20개 전체) + data/zenodo_v11/ 실측 md5 8개
    - value: 보유 8개 zip 의 md5 가 v11 표기와 8/8 일치. XJTU v11 ec68d223 396.9MB → v12 2de8b797 1.5GB, Life labels v11 cd0cc01a → v12 17c78333, READMEs v11 f1b28ff2 → v12 d6768d8a. Farasis 는 v11 · v12 어느 쪽 20개 파일에도 없음
    - checked_by: CC
- **note** — 질문의 전제가 절반 틀렸습니다 — 차이는 XJTU 와 Farasis 가 아니라 XJTU · Life labels · READMEs 셋이고, Farasis 는 애초에 배포 목록에 없습니다. 라벨 재현 관점에서는 XJTU 를 빼면 두 판본이 같은 답을 내야 합니다. 주의: LOCK.md 의 zip 행은 저장소를 세울 때 v12 md5 로 채워져 있어, v11 을 보유한 상태에서 python run.py check 를 돌리면 Life labels.zip 과 READMEs.zip 두 행이 데이터층 불일치로 나옵니다. 손상이 아니라 기준 판본이 다른 것입니다. 어느 판본으로 잠글지는 사람이 정합니다 (LOCK.md 를 CC 가 고치지 않았습니다).

### `VER-002` — v11 과 v12 각각의 다운로드 용량과 해제 후 디스크 소요

**판정: 미정** — 논문을 아직 안 봤습니다. '코드 전용' 이라 말할 수 없습니다

- **paper** — 미조사
- **upstream_doc** — 확인
    - locus: Zenodo record 19688272 Files 표
    - value: v11 다운로드 합계 30.9 GB / 20 files. 해제 후 약 82 GB 로 안내됨
    - checked_by: CC
- **code** — 확인
    - locus: data/zenodo_v11/ 과 data/extracted/ 실측 (117호, 2026-08-03, v11 20개 전부)
    - value: zip 20개 30,871,539,631 바이트 = 28.75 GiB, 해제 후 86,447,546,564 바이트 = 80.51 GiB. 압축비 약 2.80배. 파일 수 pkl 1,382 + json 19 + md 18
    - checked_by: CC
- **note** — 2026-08-03 v11 20개 전부를 받아 실측했습니다. 직전 판의 보유 8개분(다운로드 2.80 GiB → 해제 8.61 GiB, 압축비 3.1배) 은 전체와 압축비가 달랐습니다 — 8개분으로 외삽하면 약 96 GB 가 나왔지만 실측은 80.51 GiB(86.4 GB)입니다. 서브셋마다 압축률이 다르므로 부분 실측을 곱하지 마십시오. 배포 안내의 약 82 GB 는 GiB 를 뜻했다면 실측 80.51 GiB 와 근사하고, GB 를 뜻했다면 실측 86.4 GB 와 4 GB 남짓 갈립니다. 어느 단위인지는 확인되지 않았습니다. 다운로드 합계는 28.75 GiB = 30.9 GB 로 Zenodo Files 표의 30.9 GB 와 맞습니다 — 즉 안내 표는 GB(10진) 단위입니다. 그 기준을 해제 후 값에도 적용하면 86.4 GB 이므로 82 GB 와는 갈립니다. 작업에 실제로 든 디스크는 zip 28.75 + 해제 80.51 = 109.3 GiB 입니다.

