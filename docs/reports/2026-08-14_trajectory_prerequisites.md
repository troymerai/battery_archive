# 궤적 확보와 실험 착수 전제 확인

2026-08-14 · CC (Whitefox 지시) · 열화 궤적 예측 실험 1a 단계 착수 전 전제

**학습을 돌리지 않았습니다** `[확인]`. 원시 데이터(`data/extracted/`)는 읽기 전용으로만
열었습니다 `[확인]`. 상위 저장소(`upstream/`)는 한 글자도 고치지 않았습니다 `[확인]`.
파이프라인의 Step 4(`time_normalization.py`)만 부르지 않았습니다 — **그 스크립트는
`cleaned_data` 를 제자리에서 덮어씁니다**(§1-1).

이 보고서는 네 가지를 담습니다.

| 작업 | 무엇 | 절 |
|---|---|---|
| 0 | 실험 전제 — 데이터 판본 · 프롬프트 생성 경로 · 미공개 필터 | §0 |
| 1 | SOH 궤적 생성과 필터 제거율 | §1 |
| 2 | 종속변수 후보 정량화 (**결정하지 않음**) | §2 |
| 3 | 검정력 계산과 1a 실행 가능성 판정 | §3 |

---

## 0. 전제 확인

### 0-1. 데이터 판본 — **v11 로 확정** `[확인]`

이 기계의 데이터는 **BatteryLife v11 (Zenodo record 19688272)** 입니다.
`upstream/BatteryMFormer` 가 전제하는 판본과 **같습니다.**

| 무엇 | 근거 | 판정 |
|---|---|---|
| 이 기계의 판본 | `LOCK.md:3` · `manifests/data_md5.txt` | v11 (19688272) |
| md5 실측 | `CALB.zip 2b1006e9…` · `Life labels.zip cd0cc01a…` · `READMEs.zip f1b28ff2…` · `XJTU.zip ec68d223…` | LOCK 기준값과 **4/4 일치** `[확인]` |
| BatteryMFormer 전제 | `README.md:15,27` · `assets/Data_download.md:3,15,20` (`--revision v11`) | **v11** `[확인]` |
| 저장소 설정 | `config.env` `HF_REVISION=v11` | v11 |

md5 를 확인한 네 파일 중 **셋(`Life labels.zip` · `READMEs.zip` · `XJTU.zip`)이 v11 과
v12 를 가르는 파일**입니다(`LOCK.md:83-86`). 셋 다 v11 값과 같으므로 v12 가 섞여 있지
않습니다 `[확인]`.

#### v9 와 v11 의 차이 — 기록이 있습니다 `[확인]`

`upstream/BatteryLife/assets/` 에 판본별 갱신 기록이 있습니다.
`Version10_Update_Details.md` 가 v9→v10 을, `Version11_Update_Details.md` 가
v10→v11 을 적습니다. 둘을 합치면 v9→v11 입니다.

| 판 | 항 | 내용 | Zn-coin | CALB |
|---|---|---|:-:|:-:|
| v10 | 1 | `XJTU` · `ZN-coin` · `CALB` 의 방전 열 분리 (이전에는 원시 용량 열을 충·방전으로 나누지 않았음) | ● | ● |
| v10 | 2 | 위 1항 때문에 세 데이터셋의 수명 라벨 재계산 | ● | ● |
| v10 | 3 | **`ZN-coin` 의 formation 9사이클 삭제 누락 수정** | ● | |
| v10 | 4 | 시간 정규화 스크립트 수정 (전 데이터셋) | ● | ● |
| v11 | 1 | **`CALB` 충전 용량 수정** (Issue #21) | | ● |
| v11 | 2 | **Zn-ion 로딩을 바로잡도록 dataloader 수정** (Issue #24) | ● | |
| v11 | 3 | `MATR_b3c0.pkl` seen/unseen 정정 (Issue #26) | | |
| v11 | 4 | `XJTU` 의 `system_time` 정렬 제거 (Issue #22) | | |
| v11 | 5 | `CALCE` 에 `charge_protocol`·`discharge_protocol` 추가 | | |
| v11 | 6 | `RWTH` 에 `rate_in_C` 추가 및 전처리 수정 (Issue #22) | | |
| v11 | 7 | **`CALB` 수명 라벨 정정** (v10 에서 일부 셀이 잘못 계산됨) | | ● |

#### Zn-coin·CALB 전처리 수정이 이 기계의 판에 반영되었는가 — **반영되었습니다** `[확인]`

공지된 Zn-coin·CALB 전처리 수정은 위 표의 ● 표시 여섯 항입니다. 이 기계는 v11 이고,
**v11 은 v10 을 포함하므로 여섯 항 모두 들어 있습니다** `[확인]`.

다만 성질이 하나 다릅니다. **v11 2항은 데이터가 아니라 코드(dataloader) 수정입니다.**
zip 안이 아니라 `upstream/BatteryLife/data_provider/` 쪽에 있습니다. 이 저장소가 그 판
코드를 가지고 있는지는 `upstream/PROVENANCE.md` 의 커밋
`9572e47b1d36ecb31fe58f7d2874a7355dbb6fea` (2026-07-06) 로 확인됩니다 — v12 공지
(2026.07) 이후 시점이므로 v11 수정을 포함합니다 `[확인]`.

방증이 하나 더 있습니다. `generate_CALB_soh.py:96-99` 의 주석이
`CALB_35_B229` 의 라벨을 **"BatteryLife v11 이 같은 방식으로 정정했다"** 고 적습니다.
상위 코드 자신이 v11 라벨 정정을 전제합니다 `[확인]`.

#### 판정할 수 없었던 것

**v9 실물이 이 기계에 없습니다.** 따라서 v9 파일과 v11 파일을 바이트로 대조하는
방식의 확인은 하지 못했습니다. 위 판정은 **공개된 갱신 기록과 md5 일치**에 근거합니다.
또 `upstream/BatteryLife` 와 `upstream/BatteryML` 은 `.git` 을 제거하고 들여왔으므로
(`PROVENANCE.md:45-50`) **커밋 로그로 차이를 볼 수는 없습니다** `[확인]`.
`upstream/BatteryMFormer` 는 submodule 이라 이력이 있습니다 — §1-4 에서 씁니다.

---

### 0-2. 프롬프트 생성 경로 — **pkl 을 읽지 않습니다** `[확인]`

#### 어느 필드를 읽는가

**pkl 의 어떤 필드도 읽지 않습니다.** 프롬프트는 두 조각을 이어 붙인 순수 문자열입니다.

```
generate_aging_condition_embeddings.ipynb  cell 7
    prompt = bg_prompt + Mapping_helper(prompt_type='PROTOCOL', cell_name=…).do_mapping()
```

| 조각 | 어디서 오는가 | pkl 참조 |
|---|---|:-:|
| `bg_prompt` | 노트북 cell 7 에 직접 적힌 문자열. `'CALB' in cell_name` 이면 90% 판, 아니면 80% 판 | 없음 |
| 프로토콜 문장 | `Prompts/Mapping_helper.py` 의 **셀이름 → 조건 ID 사전** → `Prompts/<서브셋>_protocol_prompt.py` 의 **하드코딩 문자열** | 없음 |

`Prompts/` 18개 파일 전체(16,455줄)에 `pickle` · `cathode_material` · `anode_material`
어느 것도 나오지 않습니다 `[확인]`. 분기 조건은 `cell_name.startswith(...)` 뿐입니다
(`Mapping_helper.py:1529-1603`).

#### ZN-coin 140셀의 극 반전이 프롬프트에 들어가는가 — **들어가지 않습니다** `[확인]`

census 는 ZN-coin **140셀 전부**에 `polarity_swapped=1` 을 매깁니다
(`analysis/out/dataset_cell_census.csv`). 실물로 확인한 한 셀입니다.

```
셀    ZN-coin_202_20231213213655_03_3.pkl
pkl   cathode_material='Zinc'   anode_material='MnO2'          ← 뒤집혀 있음
프롬프트  "Its positive electrode is MnO2. Its negative electrode is Zinc metal."  ← 물리적으로 맞음
```

프롬프트가 pkl 을 읽지 않으므로 **극 반전은 프롬프트로 전파되지 않습니다.**
이 경로에 한해서는 pkl 의 반전이 무해합니다. 다만 **pkl 을 직접 읽는 다른 경로
(census · 특징 추출 등)에서는 그대로 반전된 값이 나옵니다.**

#### 그런데 같은 문장의 공칭용량은 pkl 과 어긋납니다 `[확인]`

프롬프트가 pkl 을 읽지 않는다는 사실의 부작용입니다. 프롬프트 문장이 말하는
`The nominal capacity is X Ah` 를 pkl 의 `nominal_capacity_in_Ah` 와 셀마다
대조했습니다(`analysis/out/prompt_capacity_check.csv`).

| 서브셋 | 일치 / 대상 | 최대 상대차 |
|---|---:|---:|
| **RWTH** | **0 / 48** | **0.622** |
| **ZN-coin** | **82 / 139** | **0.157** |
| **SNL** | **53 / 61** | **0.111** |
| 그 외 13개 서브셋 | 전부 일치 | 0 |

RWTH 는 세 값이 서로 다릅니다 — **프롬프트 3 Ah / pkl 1.85 Ah /
`generate_soh.py:69` 가 SOH 계산에 쓰는 값 1.85 Ah**. `generate_soh.py` 의
`nominal_capacity = 1.85 if 'RWTH' in cell_name` 은 v11 pkl 에서는 이미 1.85 이므로
결과를 바꾸지 않지만(무해한 덮어쓰기), **프롬프트만 3 Ah 로 남아 있습니다.**

#### 논문이 정의한 10개 필드 중 pkl 에 없는 것을 어떻게 처리하는가

**pkl 에서 가져오지 않습니다. 사람이 원논문을 보고 직접 적었습니다.** 처리 방식은
필드마다, 서브셋마다 다릅니다.

| 필드 | 처리 | 예 |
|---|---|---|
| 전해질 | 대부분 `"The electrolyte formula is unknown."` **고정 문자열**. 아는 곳만 실제 조성 | MICH: `"1.0 M LiPF6 salt in solvents of EC and EMC with a ratio of 3:7 together with 2 wt% additive of vinylene carbonate"` / Stanford: `"1 M LiPF6 in EC/EMC/DMC (1:1:1 by volume) with 2% VC"` |
| 제조사 | 아는 곳은 이름, 모르는 곳은 `"The battery manufacturer is unknown."` | HNEI `LG Chemical Limited` · CALB `CALB Co., Ltd.` · ZN-coin `ME` · CALCE·UL_PUR·MICH·Stanford `unknown` |
| formation 프로토콜 | 대부분 `"The working history of this battery is just after formation."` 한 문장. **Stanford 만 문단 단위 상세** | Stanford: 형성 온도·전류·전압·CV 유지·degassing·72시간 휴지까지 기술 |

**세 가지 처리가 섞여 있습니다** — ① 생략(NA-ion 은 `"Operating condition:"` 뒤에
working history 문장 자체가 없음) ② `unknown` 고정 문자열 ③ 원논문에서 가져온 실제 값.
어느 것이 쓰이는지는 서브셋마다 다르고, **코드에 규칙이 없습니다.** 사람이 파일마다
적어 넣은 것입니다.

#### 프롬프트가 붙지 않는 셀 `[확인]`

배포 데이터 1,382셀을 전부 `Mapping_helper` 에 넣었습니다
(`analysis/out/prompt_coverage.csv`).

| 결과 | 셀 수 |
|---|---:|
| 매핑 성공 | **1,295** |
| 매핑 실패 — `SDU` | **86** (`do_mapping()` 에 `SDU` 분기가 없어 `Exception('Not implemented!')`) |
| 매핑 실패 — `ZN-coin_2_432-1_20231227204455_01_1.pkl` | **1** (`KeyError`) |

**`SDU` 는 BatteryMFormer 의 처리 대상이 아닙니다** — `generate_soh.py:319-323` 의 기본
목록에도, `generate_split.py:12` 의 목록에도 없습니다.

#### 서브셋별 프롬프트 실물

전문은 `analysis/out/prompt_samples.md` 에 있습니다. 아래는 서브셋마다 1개씩,
`bg_prompt` 를 뺀 프로토콜 문장 부분입니다. **ZN-coin 은 지시대로 반드시 포함했고,
전문(bg_prompt 포함)을 함께 싣습니다.**

**ZN-coin — `ZN-coin_202_20231213213655_03_3.pkl` (전문)**

> pkl 실제 값: `cathode_material='Zinc'` · `anode_material='MnO2'` ·
> `nominal_capacity_in_Ah=0.00045019471645355225` · `SOC_interval=[0, 1]`

```text
Task description: The end of life of a battery is the number of charge-discharge cycles
until the battery's discharge capacity reaches 80% of its nominal capacity. The discharge
capacity is calculated under the described operating condition. The state of the health
(SOH) is computed by the ratio of the remaining capacity to the nominal capacity. The
target is the SOH degradation trajecotry until the end of life of the battery.Please
directly output the target of the battery based on the provided data. Battery
specifications: The data comes from a Zinc-ion battery in a format of CR2016 coin battery.
Its positive electrode is MnO2. Its negative electrode is Zinc metal. The electrolyte
formula is unknown. The battery manufacturer is ME. The nominal capacity is
0.0004751693904399872 Ah. Operating condition: The working history of this battery is just
after formation. The working ambient temperature of this battery is 25 degrees Celsius. In
the cycling, the battery was charged at a constant current of 8 C until reaching 1.8 V, The
battery was then discharged at a constant current of 8 C until reaching 0.8 V. The cycling
state-of-charge of this battery ranges from 0% to 100%.
```

> 원문의 `trajecotry` 오타와 `battery.Please` 붙임은 상위 코드 그대로입니다.
> 공칭용량 `0.000475…` 는 pkl 의 `0.000450…` 과 다릅니다(위 표).

나머지 16개 서브셋(프로토콜 문장만, pkl 값 병기):

| 서브셋 | 셀 | pkl `cathode`/`anode` | 프롬프트가 말하는 양극 / 음극 |
|---|---|---|---|
| CALB | `CALB_0_B182` | `NMC` / `graphite` | NCM / graphite |
| CALCE | `CALCE_CS2_33` | `LiCoO2` / `graphite` | LiCoO2 (LCO) / graphite |
| HNEI | `HNEI_18650_NMC_LCO_25C_0-100_0.5-1.5C_a` | `LiCoO2+LiNi0.4Co0.4Mn0.2O2` / `graphite` | LCO + NCM442 혼합 / graphite |
| HUST | `HUST_1-1` | `LFP` / `graphite` | LFP / graphite |
| ISU_ILCC | `ISU-ILCC_G10C1` | `NMC` / `graphite` | NCM / graphite |
| MATR | `MATR_b1c0` | `LiFePO4` / `graphite` | LiFePO4 / graphite |
| MICH | `MICH_BLForm10_pouch_NMC_25C_0-100_1-1C_j` | `NMC111` / `graphite` | NCM111 / graphite |
| MICH_EXP | `MICH_01R_pouch_NMC_25C_0-100_0.2-0.2C` | `NMC111` / `graphite` | NCM111 / graphite |
| NA-ion | `NA-ion_270040-1-2-63` | `Unknown` / `Unknown` | not disclosed / not disclosed |
| RWTH | `RWTH_002` | `NMC` / `graphite` | NCM / **carbon** |
| SNL | `SNL_18650_LFP_25C_0-100_0.5-3C_a` | `LFP` / `graphite` | LiFePO4 / graphite |
| Stanford | `Stanford_Nova_Regular_191` | `LiNi0.5Mn0.3Co0.2O2` / `graphite` | NCM523 / artificial graphite |
| Stanford_2 | `Stanford_Nova_Regular_100` | `LiNi0.5Mn0.3Co0.2O2` / `graphite` | NCM523 / artificial graphite |
| Tongji | `Tongji1_CY25-025_1--1` | `Li0.86Ni0.86Co0.11Al0.03 O2 (NCA)` / `Graphite/Si` | NCA861103 / graphite+2 wt.% Si |
| UL_PUR | `UL-PUR_N10-NA7_18650_NCA_23C_0-100_0.5-0.5C_g` | `LiNi0.8Co0.15Al0.05O2` / `graphite` | NCA801505 / graphite |
| XJTU | `XJTU_2C_battery-1` | `LiNi0.5Co0.2Mn0.3O2` / `graphite` | NCM523 / graphite |

**극이 뒤집힌 서브셋은 ZN-coin 하나뿐이고, 그 하나에서만 프롬프트와 pkl 이 반대입니다.**
나머지 16개는 표기 방식(`NMC` 대 `NCM`)만 다르고 물질은 같습니다. RWTH 만
음극을 `carbon`(프롬프트) 대 `graphite`(pkl)로 다르게 부릅니다.

---

### 0-3. 미공개 필터 — 코드가 셀을 버리는 조건 전부

#### `generate_soh.py` 가 **셀을 버리는** 조건 다섯 `[확인]`

| # | 코드 위치 | 조건 | 임계값 | 반환 사유 |
|---|---|---|---|---|
| 1 | `generate_soh.py:36-40,53-54` | 이름이 `EXCLUDED_CELLS` 에 있음 | ISU-ILCC 12개 이름 하드코딩 | `In EXCLUDED_CELLS list` |
| 2 | `:101-102` | `cycle_data` 가 비어 SOH 가 하나도 안 나옴 | — | `No SOH data generated (empty cycle data)` |
| 3 | `:114-115` | **마지막 SOH > `filter_threshold`** | **0.925 (CALB) / 0.825 (그 외)** | `Final SOH … > threshold …` |
| 4 | `:151-152` | 말기 회귀 기울기 `a >= 0` | 0 | `Slope is non-negative …` |
| 5 | `:154-155` | **`abs(a) < MIN_SLOPE_THRESHOLD`** | **1e-4 (SOH/사이클)** | `Slope too small …` |

조건 4·5 는 **조건 3 을 통과했지만 아직 EOL 에 닿지 않은 셀에만** 걸립니다
(`:129` 의 `else` 가지). 이미 EOL 을 지난 셀은 `:117-128` 에서 잘라 쓰고 끝납니다.

#### `MIN_SLOPE_THRESHOLD = 1e-4` 가 정확히 무엇을 버리는가 `[확인]`

- **무엇에 대한 기울기인가**: SOH(무차원) 대 **사이클 번호**. 단위는 **SOH/사이클**.
- **어느 구간인가**: 마지막 `N = min(20, 셀의 사이클 수)` 개 사이클
  (`:131,140-141`).
- **어떤 값에 맞추는가**: 그 구간의 SOH 를 `np.minimum.accumulate` 로
  **단조 비증가로 강제한 뒤**(`:143`) 최소제곱 직선을 맞춥니다.
- **무엇을 버리는가**: 그 직선의 기울기 크기가 **1e-4 SOH/사이클 미만**이면 버립니다.
  즉 **"100 사이클 더 돌아도 SOH 가 0.01 도 안 떨어지는 셀"** 입니다.

수치로 옮기면 이렇습니다. 조건 3 을 통과한 비-CALB 셀은 마지막 SOH 가
`0.8 < s ≤ 0.825` 구간에 있으므로 EOL 까지 남은 낙폭이 최대 0.025 입니다.
기울기 1e-4 로 그 0.025 를 메우려면 **250 사이클**이 필요합니다. 그런데 외삽은
**50 사이클로 잘립니다**(`MAX_EXTRAPOLATE_CYCLES`, `:133,167-168`).
따라서 **1e-4 를 갓 넘겨 살아남은 셀도 EOL 에 닿지 못한 채 궤적이 끝납니다.**

실측했습니다. **살아남은 1,297셀 중 98셀(7.6%)의 궤적이 EOL 임계값에 닿지 못합니다** `[확인]`.

| 서브셋 | 남은 셀 | EOL 미달 | 비율 |
|---|---:|---:|---:|
| HUST | 77 | **51** | **0.662** |
| RWTH | 48 | 17 | 0.354 |
| UL_PUR | 10 | 2 | 0.200 |
| MATR | 169 | 19 | 0.112 |
| NA-ion | 40 | 2 | 0.050 |
| Tongji | 108 | 4 | 0.037 |
| CALB | 27 | 1 | 0.037 |
| SDU | 86 | 1 | 0.012 |
| ZN-coin | 120 | 1 | 0.008 |
| 나머지 9개 | 612 | 0 | 0 |
| **합계** | **1,297** | **98** | **0.076** |

이것이 왜 문제인가 — 로더는 `eol_cycle = len(soh_trajectory)` 로 EOL 사이클을 잡습니다
(`data_loader_soh_optimized.py:795`). 위 98셀에서는 **그 값이 EOL 이 아니라
"관측이 끝난 지점 + 최대 50"** 입니다. 궤적의 마지막 SOH 가 EOL 임계값보다 높습니다.

#### 논문 부록 D 와 코드의 대조 `[확인]`

논문 부록 D(`Further Details of Data Preprocessing`)가 기술한 것은 셋뿐입니다.

| 논문 부록 D | 코드 | 일치 |
|---|---|---|
| 단일 사이클 SOH 낙폭이 **직전 사이클 SOH 의 3%** 를 넘으면 직전 값으로 clip | `fix_spike_drops(…, max_drop_per_cycle=0.03)` — **절대값 0.03** 비교 (`:26-29`) | **어긋남**(상대 대 절대) |
| SOH 가 `λ + 2.5%` 아래로 내려가지 않은 셀 제외. λ=0.9(CALB)/0.8(그 외) | `filter_threshold = 0.925 / 0.825` (`:59`) | 일치 |
| `λ+2.5%` 는 지났으나 λ 에 못 닿은 셀은 **마지막 20 사이클 선형 외삽**으로 λ 까지 채움 | `N=20`, `LinearRegression` (`:131,140-157`) | 일치(단, 아래 조건들이 덧붙음) |

**코드에 있는데 논문 부록 D 에 없는 조건 — 11개** `[확인]`

| # | 무엇 | 코드 위치 | 효과 |
|---|---|---|---|
| 1 | `EXCLUDED_CELLS` 12개 이름 하드코딩 | `generate_soh.py:36-40` | v11 배포본에는 **12개 중 1개만 실재**(§1-2). 나머지 11개는 이미 없는 이름 |
| 2 | **`MIN_SLOPE_THRESHOLD = 1e-4`** | `:132,154-155` | **SNL LFP 3셀 제거**(§1-2). 논문 Table 1 은 이 3셀을 세고 있음(§1-4) |
| 3 | 기울기 `a >= 0` 제외 | `:151-152` | 이번 실행에서 해당 셀 0 |
| 4 | **`MAX_EXTRAPOLATE_CYCLES = 50`** | `:133,167-168` | 외삽을 50사이클로 자름. **λ 미달 궤적을 만듦**(위 표 98셀) |
| 5 | `eol_cycle_cont <= last_cycle` 이면 외삽하지 않고 통과 | `:160-161` | 셀은 남되 궤적이 λ 에 못 닿음 |
| 6 | 회귀 구간 SOH 를 `np.minimum.accumulate` 로 단조 강제 | `:143` | 기울기를 실제보다 가파르게 만들 수 있음 |
| 7 | `RWTH` 공칭용량 1.85 로 덮어쓰기 | `:69` | v11 pkl 이 이미 1.85 라 결과 불변. 프롬프트(3 Ah)와는 어긋남(§0-2) |
| 8 | `ZN-coin_441-1_20231227204855_08_4.` 만 마지막 5사이클 제외 후 clip | `:104-108` | 셀 1개 특례 |
| 9 | `raw_sohs[:eol]` — **`eol` 은 사이클 번호인데 리스트 인덱스로 씀** | `:124-126` | 사이클 번호가 1부터 연속이 아니면 자르는 위치가 어긋남 |
| 10 | `fix_spike_drops` 의 비교 기준이 두 스크립트에서 다름 | `generate_soh.py:26` 은 `raw_sohs[i-1]`, `generate_CALB_soh.py:17` 은 `fixed[i-1]` | 연속 급락에서 결과가 갈림 |
| 11 | 로더의 **`eol_cycle <= early_cycle_threshold(=100)` 제외** | `data_loader_soh_optimized.py:798` · `run_main.py:583` | 궤적 길이 100 이하 셀을 학습·평가에서 뺌 |

11번은 **논문과 정면으로 어긋납니다.** 부록 C 는 `"we use at most the first 100 cycles
as input, and if fewer cycles are available, we pad the missing cycles with all-zero
sequences"` 라고 적어 **100 미만도 쓴다**고 말합니다. 코드는 뺍니다.

여기에 부록 D 에 없는 관문이 하나 더 있습니다 — **`name2agingConditionID.json` 에
이름이 없는 셀은 분할에 들어가지 못합니다**(`generate_split.py:36`). 이 관문이
Na-ion 과 Zn-ion 의 셀 수를 실제로 결정합니다(§1-4).

---

## 1. SOH 궤적 생성

### 1-1. 무엇을 어떻게 돌렸는가

`analysis/soh_pipeline_run.py` 가 `upstream/BatteryMFormer/process_scripts/` 의 스크립트를
**고치지 않고 자식 프로세스로** 부릅니다. `run_soh_pipeline.sh` 의 Step 1·1b·2·3·5 를
그대로 따르고 **Step 4 만 부르지 않습니다.**

> **Step 4(`time_normalization.py`)를 부르지 않은 이유.** 이 스크립트는
> `output_dir = self.input_dir` · `Always modify in-place` 로 **`cleaned_data` 를
> 제자리에서 덮어씁니다**(`time_normalization.py:367,418,442`). 이 저장소에서
> `data/extracted/` 는 읽기 전용입니다. 그리고 BatteryLife v11 은 이미 시간 정규화가
> 적용된 판입니다(`Version10_Update_Details.md` 4항). 건너뛴 사실을
> `data/soh_v11/soh_generation_log.csv` 에 `SKIPPED_WOULD_MODIFY_RAW_DATA` 로 남겼습니다.

산출 위치와 파일 수입니다. 원시 데이터는 한 바이트도 바뀌지 않았습니다 `[확인]`.

| 경로 | 무엇 | 파일 수 |
|---|---|---:|
| `data/soh_v11/SOH/` | Step 1 산출. 외삽 꼬리 포함, PCHIP 평활 전 | **1,297** (18 서브셋) |
| `data/soh_v11/CALB_from_pkl/` | Step 1 의 CALB(pkl 경로) 산출. Step 1b 가 덮어쓰기 전 사본 | 8 |
| `data/soh_v11/processed_SOH/` | Step 2·3·5 산출. PCHIP 평활 포함 | **1,263** (18 디렉터리) |
| `data/soh_v11/logs/` | 자식 프로세스 30회의 표준출력·표준오류 원문 | 30 |
| `data/soh_v11/soh_generation_log.csv` | 단계별 소요·입출력 셀 수·종료 코드 | 30행 |
| `data/soh_v11/soh_skipped_cells.csv` | 제외된 셀과 사유 원문 | 104행 |

**전 단계 종료 코드 0. 실패한 서브셋 없음** `[확인]`. 총 소요 **435초**(Step 1 만 417초).

| 서브셋 | 입력 | Step 1 산출 | 제외 | 소요(s) |
|---|---:|---:|---:|---:|
| CALCE | 13 | 13 | 0 | 2.5 |
| HNEI | 14 | 14 | 0 | 3.2 |
| MATR | 169 | 169 | 0 | 37.0 |
| UL_PUR | 10 | 10 | 0 | 2.0 |
| SNL | 61 | 49 | 12 | 5.6 |
| MICH_EXP | 18 | 12 | 6 | 3.6 |
| MICH | 40 | 40 | 0 | 4.8 |
| RWTH | 48 | 48 | 0 | 13.4 |
| HUST | 77 | 77 | 0 | 20.5 |
| Tongji | 130 | 108 | 22 | 31.8 |
| Stanford | 41 | 41 | 0 | 19.3 |
| XJTU | 23 | 23 | 0 | 15.8 |
| ISU_ILCC | 240 | 239 | 1 | 133.7 |
| NA-ion | 64 | 40 | 24 | 4.6 |
| CALB (pkl 경로) | 27 | **8** | 19 | 1.6 |
| ZN-coin | 140 | 120 | 20 | 15.4 |
| Stanford_2 | 181 | 181 | 0 | 83.9 |
| SDU (상위 기본 목록 밖) | 86 | 86 | 0 | 18.3 |
| **CALB (엑셀 경로, Step 1b)** | — | **27** | — | 4.7 |

두 가지를 짚어 둡니다.

1. **CALB 는 pkl 경로로는 27셀 중 8셀만 남습니다.** 배포본의 CALB 27셀은
   `generate_CALB_soh.py` 가 엑셀(`overall_CALB_cycling_data.xlsx`)에서 만든 것이고,
   같은 디렉터리에 **덮어씁니다.** 파이프라인을 순서대로 돌리면 pkl 경로 산출이
   사라지므로 이번에는 `CALB_from_pkl/` 에 사본을 남겼습니다.
2. **`SDU` 는 `processed_SOH` 에 없습니다.** `preprocess.py` 의 `DATASETS_TO_PROCESS`
   에도 `DATASETS_COPY_ONLY` 에도 `SDU` 가 없어 Step 2 가 건너뜁니다. Step 1 산출
   86개는 `SOH/SDU/` 에 그대로 있습니다.

### 1-2. 필터 제거율

**입력 1,382셀 → `generate_soh.py` 통과 1,278셀 → 로더 100사이클 조건 통과 1,219셀** `[확인]`
(CALB 는 pkl 경로 기준. 엑셀 경로를 쓰면 27셀 전부 남습니다.)

#### 필터 조건별

| 조건 | 제거 수 | 어느 서브셋 |
|---|---:|---|
| `FILTER_THRESHOLD` (마지막 SOH > 0.925/0.825) | **100** | CALB 19 · NA-ion 24 · Tongji 22 · ZN-coin 20 · SNL 9 · MICH_EXP 6 |
| `SLOPE_BELOW_MIN` (`abs(a) < 1e-4`) | **3** | SNL 3 |
| `EXCLUDED_CELLS` | **1** | ISU_ILCC 1 |
| `SLOPE_NON_NEGATIVE` | 0 | — |
| `EMPTY_CYCLE_DATA` | 0 | — |
| **합계** | **104** | |

`EXCLUDED_CELLS` 는 이름 12개를 담고 있는데 **v11 배포본에 실재하는 것은
`ISU-ILCC_G40C3.pkl` 하나뿐입니다** `[확인]`. 나머지 11개(`G26C1`~`G26C4` ·
`G11C1`~`G11C4` · `G42C4` · `G9C4` · `G25C4`)는 `data/extracted/ISU_ILCC/` 에 아예
없습니다. 목록의 11/12 가 이미 죽은 조건입니다.

#### 정규화 화학별 — `docs/reports/filter_removal_by_chemistry.csv`

화학 정규화는 census 의 `cathode_normalized` 열을 그대로 씁니다
(`analysis/out/dataset_cell_census.csv`). ZN-coin 은 census 가 극 반전을 바로잡아
`MnO2` 로 매깁니다.

| 화학 | 입력 | 제거 | 제거율 | `FILTER_THRESHOLD` | `SLOPE_BELOW_MIN` | `EXCLUDED` | 남음 | 로더 ≤100 탈락 | 최종 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 미상 (NA-ion) | 64 | 24 | **0.375** | 24 | 0 | 0 | 40 | 9 | 31 |
| MnO2 | 140 | 20 | **0.143** | 20 | 0 | 0 | 120 | 21 | 99 |
| NMC | 780 | 43 | 0.055 | 42 | 0 | 1 | 737 | 20 | 717 |
| NCA | 98 | 5 | 0.051 | 5 | 0 | 0 | 93 | 9 | 84 |
| **LFP** | **264** | **12** | **0.045** | 9 | **3** | 0 | 252 | 0 | 252 |
| LCO | 13 | 0 | 0 | 0 | 0 | 0 | 13 | 0 | 13 |
| 블렌드 | 23 | 0 | 0 | 0 | 0 | 0 | 23 | 0 | 23 |
| **합계** | **1,382** | **104** | 0.075 | 100 | 3 | 1 | **1,278** | 59 | **1,219** |

#### 가설 확인 — **집계에서는 반대, 같은 실험실 안에서는 맞습니다** `[확인]`

가설은 *"열화가 느린 셀을 버리는 필터이므로 LFP 가 다른 화학보다 많이 제거될 것"* 이었습니다.

**전체 집계로는 틀렸습니다.** LFP 제거율 **4.5%** 는 0 이 아닌 화학 중 **가장 낮습니다.**
MnO2 (14.3%)와 미상/Na-ion (37.5%)이 LFP 보다 3~8배 높습니다.

**그러나 이 비교는 성립하지 않습니다 — 화학과 서브셋이 거의 같은 축이기 때문입니다.**
LFP 264셀은 HUST 77 · MATR 169 · SNL 18 셋에만 있고, 앞의 둘은 **제거 0** 입니다.

| 화학 | 서브셋 | 입력 | 제거 | 제거율 |
|---|---|---:|---:|---:|
| LFP | HUST | 77 | 0 | 0 |
| LFP | MATR | 169 | 0 | 0 |
| **LFP** | **SNL** | **18** | **12** | **0.667** |

**세 화학이 한 실험실 안에 같이 있는 서브셋은 SNL 하나뿐입니다.** 거기서는 가설대로입니다.

| SNL 안에서 | 입력 | 남음 | 제거 | 제거율 |
|---|---:|---:|---:|---:|
| **LFP** | 18 | 6 | **12** | **0.667** |
| NCA | 22 | 22 | 0 | **0** |
| NMC | 21 | 21 | 0 | **0** |

같은 실험실·같은 프로토콜 계열 안에서 **LFP 만 12셀이 빠지고 NCA·NMC 는 한 셀도 빠지지
않습니다.** 제거된 12셀은 전부 `0-100%` SOC · 15~35°C 조건이고, 9셀은
`FILTER_THRESHOLD`(아직 0.825 위), 3셀은 `SLOPE_BELOW_MIN`(기울기 −4.4e-5 · −6.8e-5 ·
−6.6e-5) 입니다.

**`SLOPE_BELOW_MIN` 이 버린 셀은 3개이고 3개 전부 LFP 입니다** `[확인]`. "열화가 너무 느려
외삽할 수 없다" 는 조건이 실제로 걸린 화학은 LFP 하나입니다.

정리하면 — **집계 수치만 보면 가설은 기각되지만, 그 기각은 LFP 가 잘 살아남아서가 아니라
LFP 대부분이 애초에 EOL 을 지난 뒤까지 측정된 서브셋(HUST·MATR)에 몰려 있기 때문입니다.**
교란을 통제할 수 있는 유일한 지점(SNL)에서는 가설이 맞습니다. 화학별 집계표를 인과적으로
읽으면 안 됩니다.

### 1-3. 궤적이 EOL 에 닿지 못하는 셀

§0-3 에서 적은 대로 **살아남은 1,297셀 중 98셀(7.6%)의 궤적이 EOL 임계값에
닿지 못합니다.** 외삽 실황은 이렇습니다(`analysis/out/traj_boundary.csv`).

| 분기 | 셀 수 |
|---|---:|
| `TRUNCATED_AT_EOL` — 이미 EOL 을 지나 잘라 씀 | 1,104 |
| `EXTRAPOLATED` — 외삽 꼬리가 붙음 | **171** |
| `EXTRAPOLATED_CANDIDATE` — 외삽 가지에 들어갔으나 실제로 붙지 않음 | 22 |

외삽 사이클은 합계 **4,479**, 셀당 중앙 **32**, 최대 **88** 입니다.
**50 을 넘는 것은 `CALB_25_T25-2.pkl` (88) 하나뿐이고, CALB 이기 때문입니다** —
`generate_CALB_soh.py` 에는 `MAX_EXTRAPOLATE_CYCLES` 가 아예 없습니다
(`generate_soh.py:133` 에만 있음). 같은 일을 하는 두 스크립트가 다른 규칙을 씁니다.

### 1-4. 논문 Table 1 과 대조 — **Li-ion·CALB·Na-ion 은 재현, Zn-ion 은 관문을 특정** `[확인]`

셀 수를 결정하는 관문은 네 개입니다. 순서대로 좁혀집니다.

```
관문 1  generate_soh.py 필터 통과            → SOH 파일 생성
관문 2  name2agingConditionID.json 에 이름   → generate_split.py:36. 없으면 분할에 못 들어감
관문 3  배포 분할 JSON 에 이름               → 배포 실물
관문 4  eol_cycle > 100                      → data_loader_soh_optimized.py:798
```

| 도메인 | 논문 Table 1 | 배포 zip 실물 | 관문 1 (이번 생성) | 관문 2 | 관문 3 (배포 분할) | 관문 4 (이번 최종) |
|---|---:|---:|---:|---:|---:|---:|
| Li-ion | **963** | 1,151 | 983 | 973 | 979 | **960** |
| CALB | **27** | 27 | 27 | 27 | 27 | **27** ✓ |
| Na-ion | **31** | 64 | 40 | **31** | 31 | **31** ✓ |
| Zn-ion | **95** | 140 | 120 | 100 | **95** | 99 |

> 배포 zip 실물의 Li-ion 1,151 은 census 18서브셋 1,382 에서 CALB 27 · NA-ion 64 ·
> ZN-coin 140 을 뺀 값입니다.

#### CALB 27 · Na-ion 31 — 정확히 재현됩니다 `[확인]`

- **CALB 27**: 엑셀 경로가 27셀을 만들고 관문 2·3·4 를 전부 통과합니다.
- **Na-ion 31**: 64셀 중 24셀이 `FILTER_THRESHOLD` 로 빠져 40셀이 남고,
  그 40셀 중 **`name2agingConditionID.json` 에 이름이 있는 31셀**만 분할에 들어갑니다.
  이 31셀은 전부 100사이클을 넘으므로 최종도 31 입니다. **논문 수치와 일치.**

#### Zn-ion 95 — **재현됩니다. 단, 조건 매핑의 옛 판을 써야 합니다** `[확인]`

이번 생성으로 120셀이 남고 현재 `name2agingConditionID.json` 과 교집합하면 **100** 이라
95 가 나오지 않습니다. 원인을 submodule 이력에서 찾았습니다.

```
upstream/BatteryMFormer HEAD = febe174 "update aging condition ID"  (2026-06-19)
    name2agingConditionID.json:  1,133키 → 1,138키
    ZN-coin 항목:                    95 → 100   (5개 추가)
    조건 ID 값이 바뀐 셀:            102
```

**HEAD 직전 판(`febe174^`)의 매핑에는 ZN-coin 이 정확히 95개 있습니다.**
이번 생성 120셀과 그 옛 매핑을 교집합하면 **배포 분할 JSON 의 95셀과 집합이 완전히
같습니다** `[확인]`.

즉 **논문 Table 1 의 Zn-ion 95 는 `febe174` 이전 매핑 기준이고, 이 저장소가 잠근
HEAD 는 그보다 5셀 많은 매핑을 담고 있습니다.** 추가된 5셀은
`ZN-coin_402-1_…_01_1` · `403-1_…_01_4` · `410-1_…_09_1` · `418-1_…_11_1` ·
`428-2_…_01_4` 이고, 모두 궤적 길이 101~109 로 모든 필터를 통과합니다.

#### Li-ion 963 — **관문 세 개로 정확히 맞습니다** `[추론]`

```
배포 분할 JSON                                979
− Stanford_Nova_Regular_Ref_100/101/102        3   로더가 닿을 수 없는 셀
− 궤적 길이 ≤ 100                             13
= 963                                              논문 Table 1
```

- **닿을 수 없는 3셀**: 이 셀들은 `data/extracted/Stanford/` 에만 있고
  `Stanford_2/` 에는 없습니다. 그런데 로더는 `Stanford` 로 시작하는 이름을 전부
  `Stanford_2` 디렉터리에서 찾습니다(`data_loader_soh_optimized.py:777-778`).
  따라서 어떤 실행에서도 `No file found for:` 로 건너뜁니다 `[확인]`.
- **≤100 인 13셀**: 이번 생성에서 길이가 `1, 1, 1, 18, 20, 21, 21, 24, 24, 27, 29, 29, 99`
  입니다 `[확인]`.

이 산술이 성립하려면 **배포 `processed_SOH` 에 SNL LFP 3셀이 들어 있어야** 합니다.
그 3셀은 배포 분할 JSON 에 있지만 이번 생성에서는 `MIN_SLOPE_THRESHOLD` 로 빠졌습니다.
따라서 **`MIN_SLOPE_THRESHOLD = 1e-4` 는 논문·분할이 만들어진 뒤에 들어온 조건이라고
보는 것이 이 수치와 맞습니다** `[추론]`. 이 3셀은 사이클이 3,342 · 3,798 · 3,856 이고
마지막 SOH 가 0.818 · 0.814 · 0.811 이라 100사이클 조건에는 걸리지 않습니다 `[확인]`.

#### 결론

**미공개 필터가 차이의 원인이라는 것이 확인됩니다.** 다만 원인은 하나가 아니라 셋이고,
그중 둘은 `generate_soh.py` 밖에 있습니다.

| 도메인 | 차이를 만든 것 |
|---|---|
| Na-ion (64 → 31) | `FILTER_THRESHOLD`(24셀) + **`name2agingConditionID.json` 미등재**(9셀) |
| Zn-ion (140 → 95) | `FILTER_THRESHOLD`(20셀) + **`name2agingConditionID.json` 미등재**(25셀) |
| Li-ion (1,151 → 963) | 조건 매핑 미등재 · **`Stanford` → `Stanford_2` 경로 불일치** · **로더 100사이클 조건** |

`name2agingConditionID.json` 은 **생성 스크립트가 저장소에 없습니다.** 어떤 규칙으로
셀이 등재되고 빠지는지 코드로 확인할 수 없습니다 — 논문 부록 D 에도 없습니다.
**이것이 이번 조사에서 찾은 가장 큰 미공개 관문입니다.**

---

## 2. 종속변수 후보 정량화

> **이 절은 어느 정의가 낫다고 말하지 않습니다.** 수치만 제시합니다.
> 권고·추천·"따라서 A 를 쓰자" 는 한 줄도 넣지 않았습니다.

### 2-1. 산출 조건

`analysis/dv_candidates.py` 가 **1,211셀**(`processed_SOH` 18디렉터리에서
`MICH`·`MICH_EXP` 를 빼고 `total_MICH` 를 쓴 것)에 대해 산출했습니다.

| 궤적 판 | 정의 | 자료 |
|---|---|---|
| `observed` | 실제 측정된 사이클까지. 외삽 꼬리 제외, PCHIP 평활 전 | `data/soh_v11/SOH/` 를 `n_measured` 로 자름 |
| `processed` | 파이프라인 산출 그대로. 외삽 꼬리와 PCHIP 평활 포함 | `data/soh_v11/processed_SOH/` |

**경계 `n_measured` 는 추정이 아니라 되짚기입니다.** `analysis/soh_measured_boundary.py`
가 원본 pkl(과 CALB 는 엑셀)에서 `generate_soh.py` 의 계산을 **외삽 직전까지** 다시 밟아
길이를 재고, 되짚은 앞부분이 산출 pkl 과 값이 같은지 셀마다 대조했습니다.

> **1,297 / 1,297 셀이 일치했습니다** `[확인]`. 최대 절대차 < 1e-9.
> CALB 27셀은 엑셀 경로로 따로 되짚어 역시 전부 일치했습니다.

**두 판의 차이에는 외삽 꼬리와 PCHIP 평활 두 가지가 함께 들어 있습니다.** 어느 쪽이
얼마나 기여했는지 나누어 보려면 `dv_candidates.csv` 의 `n_extrapolated` ·
`extrap_frac` · `pchip_changed` · `pchip_max_abs_diff` 열을 보십시오.
**두 판이 실제로 다른 셀은 1,211 중 285개뿐입니다** — 외삽이 붙은 셀 163개,
PCHIP 이 값을 바꾼 셀 122개. 나머지 926셀은 두 판이 완전히 같습니다.

### 2-2. knee 정의 3종과 산출 실패

| 방법 | 구현 | 실패 셀 | 주된 사유 |
|---|---|---:|---|
| `curvature_max` | (사이클, SOH)를 각각 [0,1]로 정규화 → Savitzky-Golay(3차) 평활 → κ=&#124;s''&#124;/(1+s'²)^1.5 최대점. 양 끝 5% 제외 | **13** | `TOO_SHORT`(15점 미만) |
| `bilinear` | 연속 조각선형 `y = b0 + b1·t + b2·max(t−t_b,0)` 를 절점 격자 200개로 탐색, SSE 최소 | **173** | `BREAKPOINT_AT_GRID_EDGE` 160 · `TOO_SHORT` 13 |
| `tangent_cross` | 앞 25% · 뒤 25% 구간 직선의 교점 | **342** | `INTERSECTION_OUT_OF_RANGE` 329 · `TOO_SHORT` 13 |

**산출 실패율이 방법마다 크게 다릅니다 — 1.1% / 14.3% / 28.2%.**
셀 단위 실패 목록은 `analysis/out/dv_failures.csv` 입니다.

### 2-3. 곡률 정의 3종

| 방법 | 구현 | 실패 셀 |
|---|---|---:|
| `quad_coef` | 2차 다항 적합의 이차항 계수 | 13 |
| `resid_signmean` | 직선 적합 잔차 부호의 평균. 양수면 잔차가 대체로 직선 위 | 13 |
| `slope_ratio` | 전반부 회귀기울기 / 후반부 회귀기울기 | 13 |

시간축은 **사이클 번호**와 **수명 비율**(사이클/EOL) 두 가지로 각각 냈습니다.

### 2-4. 정의 간 차이 — 이 절이 핵심입니다

#### knee 3종 사이 (Spearman, `processed` · 사이클 단위)

| | curvature_max | bilinear | tangent_cross |
|---|---:|---:|---:|
| **curvature_max** | 1.000 | **0.327** | **0.317** |
| **bilinear** | 0.327 | 1.000 | **0.966** |
| **tangent_cross** | 0.317 | 0.966 | 1.000 |

`observed` 판도 거의 같습니다 (0.331 / 0.327 / 0.965).

**`bilinear` 과 `tangent_cross` 는 셀 순위를 거의 같게 매깁니다(ρ=0.966).
`curvature_max` 는 두 방법 어느 쪽과도 ρ≈0.32 로, 사실상 다른 양을 재고 있습니다.**

#### 곡률 6종 사이 (Spearman, `processed`)

| | quad·사이클 | quad·수명비 | resid·사이클 | resid·수명비 | ratio·사이클 | ratio·수명비 |
|---|---:|---:|---:|---:|---:|---:|
| **quad·사이클** | 1.000 | 0.779 | −0.633 | −0.633 | 0.833 | 0.833 |
| **quad·수명비** | 0.779 | 1.000 | −0.637 | −0.637 | 0.909 | 0.909 |
| **resid·사이클** | −0.633 | −0.637 | 1.000 | **1.000** | −0.709 | −0.709 |
| **resid·수명비** | −0.633 | −0.637 | 1.000 | 1.000 | −0.709 | −0.709 |
| **ratio·사이클** | 0.833 | 0.909 | −0.709 | −0.709 | 1.000 | **1.000** |
| **ratio·수명비** | 0.833 | 0.909 | −0.709 | −0.709 | 1.000 | 1.000 |

세 가지 사실이 나옵니다.

1. **시간축 정규화가 값을 바꾸는 지표는 `quad_coef` 하나뿐입니다** — 사이클 축과
   수명비 축의 순위상관이 0.779 입니다. `resid_signmean` 과 `slope_ratio` 는
   두 축에서 ρ=1.000 입니다(x 를 아핀 변환해도 잔차 부호와 기울기 비가 바뀌지 않음).
2. 부호 규약이 반대입니다 — `resid_signmean` 은 나머지 둘과 음의 상관(−0.63 ~ −0.71)입니다.
3. 같은 부호로 맞춰 보면 세 정의의 순위상관 크기는 **0.63 ~ 0.91** 범위입니다.

#### 관측 구간만 대 전처리 포함

| 지표 | Spearman ρ | n | 상대차 중앙 | 상대차 p95 |
|---|---:|---:|---:|---:|
| `knee_curvature_max_cycle` | 0.960 | 1,201 | 0 | 0.585 |
| `knee_bilinear_cycle` | 0.999 | 1,119 | 0 | 0.044 |
| `knee_tangent_cross_cycle` | 0.999 | 1,031 | 0 | 0.056 |
| `knee_curvature_max_lifefrac` | 0.939 | 1,201 | 0 | 0.585 |
| `knee_bilinear_lifefrac` | 0.993 | 1,119 | 0 | 0.056 |
| `knee_tangent_cross_lifefrac` | 0.996 | 1,031 | 0 | 0.066 |
| `curv_quad_coef_cycle` | 0.999 | 1,201 | 0 | 0.078 |
| `curv_quad_coef_lifefrac` | 0.999 | 1,201 | 0 | 0.089 |
| `curv_resid_signmean_*` | 0.995 | 1,201 | 0 | 0.296 |
| `curv_slope_ratio_*` | 0.999 | 1,201 | 0 | 0.044 |
| `eol_cycle` | 1.000 | 1,204 | 0 | 0.025 |
| `fade_rate_per_cycle` | 0.999 | 1,204 | 0 | 0.034 |

상대차 중앙값이 전부 0 인 것은 **1,211셀 중 926셀에서 두 판이 완전히 같기 때문**입니다.
차이는 나머지 285셀에 몰려 있고, p95 열이 그 크기를 보여 줍니다.

**정의 선택이 만드는 차이(knee 3종 사이 ρ≈0.32)가 궤적 판 선택이 만드는 차이(ρ≥0.94)
보다 훨씬 큽니다.**

#### 화학별 — **LFP 예상은 외삽 비율에서는 맞고, 순위 차이에서는 나타나지 않습니다** `[확인]`

예상은 *"LFP 는 외삽 비율이 높아 관측/전처리 차이가 클 것"* 이었습니다.

| 화학 | n | 외삽이 붙은 셀 비율 | 외삽 분율 중앙 | 외삽 분율 평균 |
|---|---:|---:|---:|---:|
| **LFP** | 252 | **0.552** | 0.00099 | 0.0078 |
| 미상 (Na-ion) | 40 | 0.150 | 0 | 0.0259 |
| NCA | 93 | 0.097 | 0 | 0.0099 |
| MnO2 | 120 | 0.025 | 0 | 0.00076 |
| NMC | 670 | 0.009 | 0 | 0.00079 |
| LCO · 블렌드 | 36 | 0 | 0 | 0 |

**외삽이 붙은 셀의 비율은 LFP 가 55.2% 로 압도적입니다** — 두 번째인 Na-ion(15.0%)의
3.7배. 예상한 방향이 맞습니다.

그런데 **순위상관으로는 그 차이가 드러나지 않습니다.**

| 화학 | `knee_bilinear_lifefrac` ρ(관측 대 전처리) | `curv_quad_lifefrac` ρ | 곡률 상대차 중앙 |
|---|---:|---:|---:|
| LCO | 1.000 | 1.000 | 0 |
| **LFP** | **0.9997** | **0.985** | **0.0068** |
| MnO2 | 0.9999 | 0.9998 | 0 |
| NCA | 0.985 | 0.990 | 0 |
| NMC | 0.998 | 0.9999 | 0 |
| 미상 | 0.989 | 0.988 | 0 |
| 블렌드 | 0.907 | 0.967 | 0.025 |

**LFP 는 외삽이 붙은 셀은 많지만 붙는 양이 적습니다** — 외삽 분율 중앙값이 0.00099,
즉 궤적의 0.1% 입니다. 사이클이 수천인 LFP 셀에 30~50 사이클을 덧붙여도 지표 순위는
거의 바뀌지 않습니다. **순위상관이 가장 낮은 화학은 LFP 가 아니라 블렌드(0.907)이고,
표본이 23셀뿐이라 그 값 자체가 불안정합니다.**

화학별 knee 정의 3종 상관도 크게 갈립니다.

| 화학 | n | curv↔bilin | curv↔tan | bilin↔tan |
|---|---:|---:|---:|---:|
| LFP | 252 | 0.134 | 0.161 | **0.992** |
| NMC | 670 | 0.304 | 0.293 | 0.914 |
| MnO2 | 120 | 0.623 | 0.162 | 0.637 |
| NCA | 93 | 0.585 | 0.452 | 0.925 |
| 미상 | 40 | −0.017 | −0.033 | 0.928 |
| LCO | 13 | 0.364 | 0.100 | 0.700 |
| 블렌드 | 23 | −0.182 | −0.348 | 0.338 |

**`bilinear`↔`tangent_cross` 의 일치도조차 화학마다 0.338 ~ 0.992 로 갈립니다.**

### 2-5. 불일치가 큰 셀

`docs/reports/dv_disagreement_cells.csv` — **392셀**. 문턱은
knee/곡률 **순위 폭 ≥ 0.7**, 관측 대 전처리 knee 수명비 **차이 ≥ 0.05** 입니다.

문턱 자체가 자의적이므로 다른 문턱에서의 개수를 함께 남깁니다
(`analysis/out/dv_correlations.json`).

| 문턱 | ≥0.3 | ≥0.5 | ≥0.7 | ≥0.9 |
|---|---:|---:|---:|---:|
| knee 순위 폭 | 705 | 429 | **175** | 15 |
| 곡률 순위 폭 | 989 | 651 | **263** | 26 |

| 문턱 | ≥0.02 | ≥0.05 | ≥0.10 | ≥0.20 |
|---|---:|---:|---:|---:|
| 관측 대 전처리 knee 수명비 차이 | 53 | **22** | 11 | 4 |

**정의 3종이 셀을 서로 반대편에 놓는 일(순위 폭 ≥0.7)이 knee 175셀 · 곡률 263셀에서
일어납니다. 반면 궤적 판 차이로 knee 위치가 수명의 5% 이상 움직이는 셀은 22개뿐입니다.**

불일치 셀의 분포입니다.

| 서브셋 | 셀 | | 화학 | 셀 |
|---|---:|---|---|---:|
| MATR | 82 | | NMC | 215 |
| Tongji | 82 | | LFP | 84 |
| ISU_ILCC | 70 | | NCA | 53 |
| SNL | 31 | | 미상 | 14 |
| RWTH | 29 | | 블렌드 | 14 |
| Stanford_2 | 29 | | MnO2 | 11 |
| XJTU | 21 | | LCO | 1 |
| 그 외 8개 | 48 | | | |

CSV 에는 셀마다 `severity`(순위 폭 최대) · `n_total` · `n_measured` ·
`n_extrapolated` · `extrap_frac` · `pchip_changed` · `eol_cycle` · `soh_first` ·
`soh_last` · knee 3종의 수명비 값을 함께 담았습니다.

---

## 3. 검정력 계산

전체 표는 `docs/reports/power_analysis.md`, 원자료는 `analysis/out/power_analysis.json`
입니다.

### 3-1. 클러스터 구조

**지시는 서브셋 18개를 클러스터로 두라고 했으나, 1a 가 실제로 쓸 수 있는 클러스터는
15개입니다** `[확인]`.

| 왜 빠지는가 | 개수 |
|---|---:|
| `MICH` + `MICH_EXP` 가 `total_MICH` 하나로 합쳐짐 (파이프라인 Step 3) | −1 |
| `SDU` 는 BatteryMFormer 처리 경로 자체가 없음 (§1-1) | −1 |
| `Stanford` 는 로더가 닿지 않고, 41셀 중 38개가 `Stanford_2` 와 바이트 동일 중복 | −1 |

남은 15 클러스터 · 1,170셀. **크기는 10 ~ 239 로 극심하게 불균등합니다.**

| 클러스터 | 셀 | | 클러스터 | 셀 |
|---|---:|---|---|---:|
| ISU_ILCC | 239 | | RWTH | 48 |
| Stanford_2 | 181 | | NA-ion | 40 |
| MATR | 169 | | CALB | 27 |
| ZN-coin | 120 | | XJTU | 23 |
| Tongji | 108 | | HNEI | 14 |
| HUST | 77 | | CALCE | 13 |
| total_MICH | 52 | | UL_PUR | 10 |
| SNL | 49 | | | |

### 3-2. 급내상관과 유효 표본

일원 변량효과 ANOVA 로 `ICC = (MSB − MSW) / (MSB + (m₀−1)·MSW)` 를 냈습니다.
`m₀` 는 불균형 보정 평균 크기 `(N − Σnᵢ²/N)/(k−1)` 입니다.

| 종속변수 | k | N | m̄ | m₀ | **ICC ρ** | 설계효과 1+(m̄−1)ρ | **유효표본** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 곡률 (`quad_coef`·수명비) | 15 | 1,160 | 77.3 | 73.0 | **0.614** | 47.8 | **24.2** |
| knee 위치 (`bilinear`·수명비) | 15 | 1,080 | 72.0 | 68.1 | **0.485** | 35.4 | **30.5** |
| EOL 사이클 | 15 | 1,170 | 78.0 | 73.7 | **0.426** | 33.8 | **34.6** |
| 페이드율 (사이클당) | 15 | 1,163 | 77.5 | 73.2 | **0.192** | 15.7 | **74.2** |

보정 크기 `m₀` 를 쓰면 유효표본이 25.7 / 32.2 / 36.6 / 78.4 로 조금 커집니다.

**셀 1,170개가 유효표본 24 ~ 78 로 줄어듭니다.** 곡률은 분산의 61%가 서브셋 사이에서
나옵니다 — 셀을 하나 더 넣어도 정보가 거의 늘지 않습니다.

### 3-3. 증분 R² 0.05 의 검정력 — **달성 불가** `[확인]`

`f² = ΔR²/(1−R²_full)`, `λ = f²·(u+v+1)`, `α=0.05`.
`u` 는 검정 대상 블록의 예측변수 수, 분모 자유도 `v = N_eff − 13 − 1`.

| 종속변수 | R²_full | u=1 | u=3 | u=13 |
|---|---:|---:|---:|---:|
| 곡률 | 0.3 | 0.136 | 0.096 | 0.072 |
| 곡률 | 0.5 | 0.171 | 0.116 | 0.083 |
| 곡률 | 0.7 | 0.254 | 0.165 | 0.108 |
| knee 위치 | 0.3 | 0.192 | 0.128 | 0.087 |
| knee 위치 | 0.5 | 0.249 | 0.163 | 0.104 |
| knee 위치 | 0.7 | 0.380 | 0.251 | 0.149 |
| EOL | 0.3 | 0.228 | 0.150 | 0.097 |
| EOL | 0.5 | 0.300 | 0.196 | 0.119 |
| EOL | 0.7 | 0.457 | 0.309 | 0.179 |
| **페이드율** | 0.3 | 0.546 | 0.384 | 0.212 |
| **페이드율** | 0.5 | 0.690 | 0.520 | 0.298 |
| **페이드율** | 0.7 | **0.887** | 0.763 | 0.509 |

**36칸 중 0.80 을 넘는 것은 한 칸뿐입니다** — 페이드율, `R²_full=0.7`, `u=1` (0.887).

클러스터를 무시하고 셀 1,170개를 독립 표본으로 세면 36칸 전부 1.000 이 나옵니다.
**클러스터 구조를 넣느냐 마느냐가 판정을 완전히 뒤집습니다.**

### 3-4. 탐지 가능한 최소 증분 R²

80% 검정력이 나오는 최소 ΔR² 를 역산했습니다(유효표본 `m̄` 기준).
칸 안은 `u=1 / u=3 / u=13` 입니다.

| 종속변수 | R²_full=0.3 | R²_full=0.5 | R²_full=0.7 |
|---|---|---|---|
| **곡률** | 0.550 / 0.790 / 탐지 불가 | 0.393 / 0.564 / 0.851 | 0.236 / 0.338 / 0.511 |
| **knee 위치** | 0.336 / 0.473 / 0.719 | 0.240 / 0.338 / 0.514 | 0.144 / 0.203 / 0.308 |
| **EOL** | 0.268 / 0.375 / 0.574 | 0.191 / 0.268 / 0.410 | 0.115 / 0.161 / 0.246 |
| **페이드율** | 0.091 / 0.127 / 0.200 | 0.065 / 0.091 / 0.143 | **0.039** / 0.054 / 0.086 |

### 3-5. 판정

| 결과 | 해당 |
|---|---|
| 증분 R² 0.05 를 80% 검정력으로 탐지 가능 | **페이드율, `R²_full=0.7`, `u=1` 인 경우에만** |
| 불가. 탐지 가능 최소치가 0.05 보다 큼 | **나머지 전부** |

**설계안의 중단 기준 ΔR² = 0.05 는 지금 표본으로 지킬 수 없습니다.**
설계 수정의 근거가 되는 수치는 이것입니다.

| 종속변수 | 80% 검정력으로 탐지 가능한 **최소 증분 R²** (`R²_full=0.5`, `u=3` 기준) |
|---|---:|
| 곡률 | **0.564** |
| knee 위치 | **0.338** |
| EOL | **0.268** |
| 페이드율 | **0.091** |

가장 유리한 조합(페이드율 · `R²_full=0.7` · `u=1`)에서도 **0.039**, 가장 불리한 조합
(곡률 · `R²_full=0.3` · `u=13`)에서는 **어떤 ΔR² 로도 80% 에 닿지 않습니다** —
유효표본 24.2 에서 분모 자유도가 `24.2 − 13 − 1 = 10.2` 밖에 남지 않기 때문입니다.

**곡률을 종속변수로 쓰면서 예측변수 13개를 한 블록으로 검정하는 조합은 자유도가 모자라
검정 자체가 성립하지 않습니다.** 이것이 이번 계산에서 가장 강한 제약입니다.

### 3-6. 클러스터 15개라는 조건에서 대안 방법의 적합성

> **어느 방법을 쓰라고 정하지 않습니다.** 이 데이터 구조에서 각각이 무엇을 요구하고
> 무엇이 성립하지 않는지만 적습니다.

계량경제 문헌의 통상 기준은 클러스터 **30~40개**입니다. 여기는 **15개**이고
크기가 10~239 로 불균등합니다. 지시가 든 우려가 이 데이터에서는 지시보다 더 강하게
성립합니다 — 18 이 아니라 15 입니다.

| 방법 | 이 데이터에서 요구하는 것 | 성립 여부 |
|---|---|---|
| **묶음(cluster-robust) 표준오차** | 클러스터 수가 크고 크기가 비슷할 것. 점근 논거가 `k→∞` 에 기댐 | k=15. 크기 비 239/10 = 23.9. **하한 조건을 못 미침.** 표준오차가 아래로 치우쳐 1종 오류가 과다해지는 전형적 구간 |
| **wild cluster bootstrap** | 소수 클러스터용으로 제안된 방법이나 **크기 불균등에 약함**. 큰 클러스터 하나가 재표집을 지배 | k=15 는 문헌이 다루는 범위 안이지만, ISU_ILCC(239) 하나가 전체의 20%. **불균등이 주된 위험** |
| **혼합효과 모형** (서브셋 변량절편) | 변량효과 분산을 추정할 만큼의 클러스터 수. 통상 최소 5~10 | k=15 로 **추정은 가능**. 다만 ICC 0.19~0.61 이 커서 변량절편이 고정효과 상당 부분을 흡수함. **서브셋 사이에서만 변하는 예측변수(제조사·포맷 등)는 식별되지 않음** — 1a 의 예측변수 13개 중 몇 개가 여기 해당하는지 먼저 확인해야 함 |
| **Ibragimov–Müller** | 클러스터마다 따로 추정한 뒤 그 추정치들에 t 검정. **클러스터마다 모형이 추정 가능해야 함** | 최소 클러스터가 UL_PUR 10셀, CALCE 13셀, HNEI 14셀. **예측변수 13개로는 이 셋에서 회귀가 성립하지 않음**(자유도 음수). 예측변수를 줄이거나 작은 클러스터를 빼야 적용 가능 |
| **순열 검정** (서브셋 라벨 재배열) | 귀무가설 아래 교환 가능성. 클러스터 단위 순열이면 가능한 배열 수가 `k` 에 좌우됨 | k=15 이면 클러스터 단위 순열의 해상도는 충분(15! 은 매우 큼). 다만 **크기가 불균등해 교환 가능성 가정이 약함** — 239셀 클러스터와 10셀 클러스터를 맞바꾸는 것이 귀무가설 아래 같은 분포를 준다고 보기 어려움 |

추가로 확인해 둘 것 하나. **위 ICC 는 `processed` 판 기준이고, `observed` 판으로 바꿔도
거의 같습니다** — §2-4 에서 두 판의 순위상관이 0.94 이상이었기 때문입니다.
**종속변수 정의를 바꾸는 것은 ICC 를 크게 바꿉니다** (곡률 0.614 대 페이드율 0.192).
검정력 판정이 §2 의 정의 선택에 직접 매달려 있습니다.

---

## 4. 산출물

| 파일 | 내용 | 커밋 |
|---|---|---|
| `docs/reports/2026-08-14_trajectory_prerequisites.md` | 이 보고서 | 함 |
| `docs/reports/filter_removal_by_chemistry.csv` | 작업 1-2 화학별 제거율 | 함 |
| `docs/reports/dv_candidates.csv` | 셀 1,211 × 45열. knee 3종 × 곡률 3종 × 궤적 2판 | 함 |
| `docs/reports/dv_disagreement_cells.csv` | 정의가 갈리는 392셀 | 함 |
| `docs/reports/power_analysis.md` | 작업 3 전체 표 | 함 |
| `data/soh_v11/SOH/` · `processed_SOH/` | SOH 궤적 1,297 · 1,263 파일 | 안 함 (`data/*` 제외) |
| `data/soh_v11/soh_generation_log.csv` · `soh_skipped_cells.csv` · `logs/` | 생성 기록 | 안 함 |
| `analysis/out/traj_boundary.csv` | 셀별 측정/외삽 경계와 되짚기 검증 | 안 함 (`analysis/out/` 제외) |
| `analysis/out/dv_correlations.json` · `dv_failures.csv` | 순위상관 행렬 · 지표 실패 목록 | 안 함 |
| `analysis/out/power_analysis.json` | 검정력 원자료 | 안 함 |
| `analysis/out/prompt_samples.md` · `prompt_coverage.csv` · `prompt_capacity_check.csv` | 프롬프트 실물과 대조 | 안 함 |
| `analysis/out/table1_reconcile.json` · `table1_gate_cells.csv` | Table 1 관문별 셀 | 안 함 |
| `analysis/out/filter_removal_by_subset.csv` · `filter_removal_cells.csv` · `removal_by_chemistry_subset.csv` · `filter_removal_summary.json` | 제거율 보조 표 | 안 함 |

### 스크립트 — 전부 `analysis/` 에 두었고 재현 가능합니다

저장소 루트에서 `.venv-blife/Scripts/python.exe analysis/<이름>.py` 로 부릅니다.
**순서가 있습니다.**

| # | 스크립트 | 무엇 | 소요 |
|---|---|---|---:|
| 1 | `soh_pipeline_run.py` | 상위 파이프라인 Step 1·1b·2·3·5 호출, 제외 사유 수집 | **7.3분** |
| 2 | `filter_removal_report.py` | 화학별·서브셋별·조건별 제거율 | 6초 |
| 3 | `table1_reconcile.py` | 논문 Table 1 관문별 대조 (submodule 이력 사용) | 8초 |
| 4 | `prompt_probe.py` | 프롬프트 실물·매핑 적용률·공칭용량 대조 | **9.6분** |
| 5 | `soh_measured_boundary.py` | 측정/외삽 경계 되짚기와 검증 | **7.1분** |
| 6 | `dv_candidates.py` | 종속변수 후보 산출과 정의 간 차이 | 40초 |
| 7 | `power_cluster.py` | ICC · 설계효과 · 검정력 · 최소 탐지 ΔR² | 2초 |

2·3 은 1 뒤에, 6 은 5 뒤에, 7 은 6 뒤에 돌려야 합니다.
1·4·5 는 `data/extracted/` 86.45 GB 를 읽습니다.
3 은 `upstream/BatteryMFormer` 의 git 이력(`febe174^`)을 읽으므로
submodule 이 초기화되어 있어야 합니다.

---

## 5. 정리 — 1a 착수 전 확인된 것

| 지시 항목 | 결과 |
|---|---|
| 데이터 판본 | **v11 확정** `[확인]`. BatteryMFormer 전제와 일치. Zn-coin·CALB 전처리 수정 6항 전부 반영 |
| 프롬프트 생성 경로 | **pkl 을 읽지 않음** `[확인]`. ZN-coin 극 반전은 프롬프트로 전파되지 않음. 대신 공칭용량이 RWTH 48/48 · ZN-coin 57/139 셀에서 pkl 과 어긋남 |
| 미공개 필터 | 논문 부록 D 에 없는 조건 **11개** 열거. 가장 큰 것은 `generate_soh.py` 밖의 `name2agingConditionID.json` 관문 |
| SOH 궤적 생성 | **1,297 + 1,263 파일. 실패 서브셋 없음** `[확인]` |
| 필터 제거율 (화학별) | 완료. **가설은 집계에서 기각, SNL 안에서는 확인** |
| Table 1 대조 | **Na-ion 31 · CALB 27 재현** `[확인]`. **Zn-ion 95 는 조건 매핑 옛 판에서 재현** `[확인]`. **Li-ion 963 은 979 − 3 − 13 으로 맞음** `[추론]` |
| 종속변수 후보 정량화 | 완료. **결정하지 않음.** knee 3종 중 둘은 ρ=0.966 으로 사실상 같고 하나는 ρ≈0.32 로 다름 |
| 검정력 | **1a 를 설계대로 진행할 수 없음.** ΔR² 0.05 는 36칸 중 1칸에서만 80% 도달 |

### 1a 설계에 되돌려야 할 수치

1. **탐지 가능한 최소 증분 R²** — 곡률 0.564 · knee 0.338 · EOL 0.268 · 페이드율 0.091
   (`R²_full=0.5`, `u=3` 기준). 중단 기준을 이 값들로 올리거나 점추정 대신
   신뢰구간 기준으로 바꾸는 것이 이 수치가 가리키는 두 갈래입니다.
2. **클러스터는 18개가 아니라 15개** 이고 크기가 10~239 입니다.
3. **곡률 + 예측변수 13개 블록 검정은 자유도가 모자랍니다** (유효표본 24.2).
4. **`Stanford` 41셀은 배포 모집단이 아닙니다** — 로더가 `Stanford_2` 만 봅니다.
5. **궤적 98셀(7.6%)의 마지막 SOH 가 EOL 임계값 위**입니다. 그 셀들에서
   `len(trajectory)` 는 EOL 사이클이 아닙니다.

### 이번 조사로는 답하지 못한 것

| 무엇 | 왜 |
|---|---|
| `name2agingConditionID.json` 의 등재 규칙 | 생성 스크립트가 상위 저장소에 없습니다. 논문 부록에도 없습니다 |
| 배포 `processed_SOH` 실물과의 바이트 대조 | 이 기계에 배포 `processed_SOH` 가 없습니다(HF 게이트 저장소). §1-4 의 Li-ion 산술이 `[추론]` 인 이유입니다 |
| v9 파일과 v11 파일의 직접 대조 | v9 실물이 이 기계에 없습니다 |
| ZN-coin 궤적 길이가 정확히 100 인 1셀이 배포본에서는 101 이상인가 | 위와 같은 이유. Zn-ion 관문 4 가 94 로 나오고 논문이 95 인 차이가 여기서 옵니다 |
