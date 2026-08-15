# analysis/ — 학습 없이 라벨·메타만으로 재는 분석

2026-08-07 · 이 디렉터리의 파일이 **어디서 나왔고 다시 만들 수 있는가** 를 적습니다.

`.gitignore` 로 `analysis/out/` 을 제외하는 순간 그 정보가 저장소에서 사라지므로
이 파일이 반드시 있어야 합니다.

> **읽는 순서.** 재생성되는 것과 안 되는 것이 섞여 있습니다. §2 의
> **`재생성 불가`** 표를 먼저 보십시오 — 그 파일들은 지우면 되돌릴 수 없습니다.

---

## 0. 실행 환경

```
.venv-blife/Scripts/python.exe        Python 3.12.3 · numpy 1.26.4 · scikit-learn 1.9.0 · matplotlib 3.8.4
```

`analysis/*.py` 는 서로를 평범한 이름으로 import 합니다
(`from domain_discriminability import …`). **저장소 루트에서
`python analysis/<이름>.py` 로 부르십시오** — 그래야 `analysis/` 가
`sys.path[0]` 에 들어갑니다.

---

## 1. `analysis/out/` — 전량 재생성 검증됨, 커밋하지 않음

2026-08-07 에 **14개 파일 전부를 지우지 않고 덮어쓰기로 재생성해 기존본과
sha256 을 대조했습니다. 14/14 비트 단위 일치** `[확인]`. 검증 절차와 해시는
`docs/reports/2026-08-07_repo_cleanup.md` §2 에 있습니다.

의존 순서가 있습니다. `cell_meta.csv` 가 먼저 있어야 `diversity.json` 이 나오고,
`reported_table.json` 이 먼저 있어야 `discriminability.*` 가 나옵니다.
아래 표 순서대로 돌리면 됩니다.

| # | 산출물 | 생성 스크립트 | 명령 | 크기 | 소요 | 재생성 검증 |
|---|---|---|---|---:|---:|---|
| 1 | `out/reported_table.json` | `reported_table.py` | `python analysis/reported_table.py` | 9.0 KB | <1초 | **일치** `[확인]` |
| 2 | `out/cell_meta.csv` | `extract_cell_meta.py` | `python analysis/extract_cell_meta.py` | 214 KB | **6분 37초** | **일치** `[확인]` |
| 3 | `out/domain_stats.json` | `domain_discriminability.py` | `python analysis/domain_discriminability.py` | 38.7 KB | 3초 | **일치** `[확인]` |
| 4 | `out/hist_domains.png` | 〃 (같은 실행) | 〃 | 60.7 KB | — | **일치** `[확인]` |
| 5 | `out/hist_Li-ion.png` | 〃 | 〃 | 21.0 KB | — | **일치** `[확인]` |
| 6 | `out/hist_Zn-ion.png` | 〃 | 〃 | 21.1 KB | — | **일치** `[확인]` |
| 7 | `out/hist_Na-ion.png` | 〃 | 〃 | 23.5 KB | — | **일치** `[확인]` |
| 8 | `out/hist_CALB.png` | 〃 | 〃 | 19.5 KB | — | **일치** `[확인]` |
| 9 | `out/conditions_reported.json` | `conditions_and_reported.py` | `python analysis/conditions_and_reported.py` | 5.6 KB | 1초 | **일치** `[확인]` |
| 10 | `out/discriminability.json` | `discriminability_table.py` | `python analysis/discriminability_table.py` | 7.8 KB | 1초 | **일치** `[확인]` |
| 11 | `out/discriminability.md` | 〃 (같은 실행) | 〃 | 631 B | — | **일치** `[확인]` |
| 12 | `out/condition_mean_baseline.json` | `condition_mean_baseline.py` | `python analysis/condition_mean_baseline.py` | 2.8 KB | 1초 | **일치** `[확인]` |
| 13 | `out/diversity.json` | `diversity_breakdown.py` | `python analysis/diversity_breakdown.py` | 5.5 KB | 1초 | **일치** `[확인]` |
| 14 | `out/label_filter_recount.csv` | `recount_label_filters.py` | `python analysis/recount_label_filters.py` | 203 KB | 수 분 | 아래 §1-1 |
| 15 | `out/stanford_overlap.csv` | `stanford_overlap_check.py` | `python analysis/stanford_overlap_check.py` | 8 KB | 수십 초 | 아래 §1-2 |
| 16 | `out/dataset_cell_census.csv` | `dataset_metadata_survey.py` | `python analysis/dataset_metadata_survey.py` | 833 KB | **6.4분** (86.4 GB 읽기) | 아래 §1-2 |
| 17 | `out/survey_tables.md` | 〃 (같은 실행) | 〃 | 12 KB | — | 〃 |

> **순서가 있습니다.** 15번을 **먼저** 돌려야 16번이 `duplicate_of` 를 채웁니다.
> 없으면 경고를 내고 중복 표시를 비운 채 진행하며, 고유 셀이 1,344 가 아니라
> 1,382 로 나옵니다.
>
> **16번은 `out/` 밖에도 하나를 씁니다.** 같은 실행이
> `docs/reports/datasets_metadata.csv` (18행 × 44열) 를 함께 만듭니다. 그쪽은
> 보고서와 짝이라 **커밋 대상**이고, `out/` 쪽 셀 단위 1,382행은 커밋하지
> 않습니다. 두 파일을 같이 지우고 위 명령 하나로 되살립니다.

**PNG 5장도 바이트 단위로 같았습니다** `[확인]`. matplotlib 3.8.4 에서 이 그림들은
결정적입니다 — 다른 판본에서는 갈릴 수 있습니다 `[추론]`.
`condition_mean_baseline.py` 는 부트스트랩 1,000회를 쓰지만
`np.random.default_rng(1)` 로 씨앗이 박혀 있어 결정적입니다 `[확인]`.

### 1-1. 무거운 둘의 실측 소요

`out/` 14개 중 pkl 1,440개를 실제로 여는 것은 둘뿐이고 나머지는 라벨 JSON 과
상위 코드만 읽어 1초 안에 끝납니다.

| 스크립트 | 소요 | 결과 |
|---|---:|---|
| `extract_cell_meta.py` | **6분 37초** (17:08:24 → 17:15:01) | `cell_meta.csv` 일치 `[확인]` |
| `recount_label_filters.py` | **5분 20초** (17:15:01 → 17:20:21) | `label_filter_recount.csv` 일치 `[확인]` |
| `dataset_metadata_survey.py` | **6.4분** (2026-08-13 2판, 86.4 GB 읽기) | `dataset_cell_census.csv` 신규 (§1-2) |

전량 재생성에 **약 12분**이 듭니다. 나머지 6개 스크립트는 합쳐서 7초입니다 `[확인]`.

```
label_filter_recount.csv  811b005e6d29e017039c1de59171430977bd0405af3885def8452d4f870132be
cell_meta.csv             29b5d7ae7a2a991d8c472f273d803f374214df482f76ad9b8b5dc4c3f52a2183
```

### 1-2. `dataset_metadata_survey.py` — `extract_cell_meta.py` 와 무엇이 다른가

2026-08-13 신설, 같은 날 2판으로 개정. 보고서는
`docs/reports/2026-08-13_dataset_metadata_survey.md` (1차) 와
`…_survey_fix.md` (정정 · **총계 정본**) 입니다.

> **2판에서 바뀐 것.** 1판은 셀 census 만 만들고 보고서 본문 표는 저장소에 없는
> 일회성 스크립트로 따로 계산했습니다. 그 스크립트가 중앙값을 상위 중앙값으로
> 잡아, 셀 수가 짝수인 서브셋 7곳에서 보고서와 CSV 의 숫자가 갈렸습니다.
> 2판은 census · 요약표 · 보고서 표 조각을 **한 실행, 같은 메모리 상의 행
> 목록**에서 만들고 중앙값 규약을 `np.median` 하나로 통일합니다. 상위 중앙값이
> 필요하면 `n_cycle_records_median_upper` 열을 보십시오.
> 두 CSV 첫 줄은 `#` 로 시작하는 실행 식별자(시각 · git sha · Python · numpy)이고,
> 읽을 때는 `read_csv_with_run_header()` 나 pandas 의 `comment='#'` 를 씁니다.

**둘은 겹치지만 서로를 대체하지 않습니다.**

| | `extract_cell_meta.py` | `dataset_metadata_survey.py` |
|---|---|---|
| 목적 | 조건 다양성(T4) 용 **사양 필드** | 사양 + **셀마다 갈리는 값** |
| 대상 | `data/extracted/*/*.pkl` **1,440개** | **1,382개** — `total_MICH/` 58개를 뺌 |
| 고유 셀 | (중복 미구분) | **1,344개** — Stanford 동명 38개를 `duplicate_of` 로 표시 |
| 열 | 23 | 60 |
| 추가로 재는 것 | — | 첫·끝·최소 SOH, EOL 재현값과 분기, 사이클 번호 결번, 배포 라벨 대조, 부가 채널(온도·내부저항·`Qdlin`)의 **실제 유무**, 화학 정규화, 셀 단위 부문 분류 |
| 사이클 수 | `n_cycles` 하나 | `n_cycle_records` 와 `cycle_number_max` **둘로 분리** — 211셀에서 값이 다름 |

`total_MICH/` 는 `data_loader.py:391-393` 의 `merge_MICH()` 가 `MICH`+`MICH_EXP`
를 복사해 만든 파생 디렉터리라 셀이 두 번 잡힙니다. `cell_meta.csv` 가 1,440행인
이유가 이것입니다 — 다만 `diversity_breakdown.py:35` 가 **파일명을 키로 하는
dict** 으로 읽어 중복이 접히므로, 기존 산출물의 수치는 영향을 받지 않습니다
`[확인]`.

**전수성 보증.** 이 스크립트는 루프 **전에** 대상 셀 수를 세고 루프 **뒤** 기록
행 수와 대조합니다. 어긋나면 종료 코드 1 입니다. 셀 단위 `try/except` 를 걸되
실패한 셀은 건너뛰지 않고 `error` 열에 사유를 남깁니다.
2026-08-13 2판 실행은 **1,382 / 1,382 · 읽기 실패 0 · 종료 코드 0 · 6.4분**
입니다 `[확인]`. 1판과 2판을 셀 1,382개 × 공통 39열로 대조한 결과
**값 차이 0건**입니다 `[확인]`.

### 1-3. `stanford_overlap_check.py`

`Stanford` 와 `Stanford_2` 의 동명 38쌍이 같은 셀인지 봅니다. sha256 을 먼저
비교하고, 다르면 사이클 수·사양·첫끝 용량을 비교합니다. 2026-08-13 실행에서
**38쌍 전부 바이트 동일**이었습니다 `[확인]`. `dataset_metadata_survey.py` 가 이
결과를 읽어 중복 셀을 표시하므로 **먼저 돌려야 합니다.**

---

## 2. `analysis/*.csv` — 생성 스크립트가 없습니다. **9개는 커밋합니다**

> **2026-08-07 갱신.** 처음에는 10개 전부를 "재생성 불가" 로 적었습니다. 그 뒤
> 원인을 파고들어 **원시 스캔이 pkl 에서 다시 계산되는 캐시**임을 확인했습니다.
> 진단은 `docs/reports/2026-08-07_repo_cleanup.md` §11 에 있고, 부분 재구성
> 스크립트를 `analysis/rebuild_cycle_scan.py` 로 남겼습니다.
>
> 결론이 바뀐 부분: **`li_ion_cycle_scan.csv` 는 잃어도 파생 요약을 되살릴 수
> 있습니다.** 나머지 9개는 저장소가 유일한 사본이므로 **커밋합니다.**

**최상위 CSV 10개(합계 188.7 MB)를 만드는 스크립트가 이 저장소에 없습니다** `[확인]`.

근거는 셋입니다.

1. `analysis/*.py` 8개의 출력 경로를 전수로 읽었고 **전부 `analysis/out/` 아래**
   입니다 (`grep -n "OUT" analysis/*.py`) `[확인]`.
2. 저장소 전체에서 `cycle_scan` 문자열을 찾으면 **보고서 본문에서만** 나오고
   코드에서는 안 나옵니다 `[확인]`.
3. 보고서 자신이 이 파일들을 **"재사용 캐시"** 로 부르고
   (`docs/reports/2026-08-06_li_ion_temporary_crossing.md:43`), 그 조사는
   원본 `.pkl` 을 **0건 개봉**했다고 적습니다 `[확인]`.

즉 이 CSV 들은 2026-08-06 조사에서 **저장되지 않은 일회성 코드**가 만든 것이고,
**지우면 되돌릴 방법이 지금은 없습니다.** 다시 만들려면 스캔 코드를 새로 써야
하며, 그렇게 만든 결과가 아래 해시와 같다는 보장이 없습니다.

| 파일 | 크기 | 행 | sha256[:16] | 커밋 | 되살릴 수 있는가 |
|---|---:|---:|---|---|---|
| `li_ion_cycle_scan.csv` | **185,391,825 B** | 1,846,308 | `f63db8690cf5eaf4` | **제외 — 100 MiB 한계** | **캐시.** pkl 에서 재계산 (§2-1) |
| `na_ion_cycle_scan.csv` | 2,588,049 B | 12,604 | `cfa6d89931579ae9` | **함** | 스크립트 없음 |
| `li_ion_cell_meta.csv` | 489,055 B | 884 | `f7063a44cad2e6d3` | **함** | 스크립트 없음 |
| `li_ion_label_vs_soh.csv` | 151,793 B | 839 | `4e6250a30e2c20d9` | **함** | 스크립트 없음 |
| `li_ion_temporary_crossing.csv` | 15,924 B | 107 | `396f95bf2a4f3d43` | **함** | 스크립트 없음 |
| `na_ion_cell_summary.csv` | 8,555 B | 64 | `10c63fec6b02c771` | **함** | 스크립트 없음 |
| `na_ion_label_vs_soh.csv` | 7,642 B | 64 | `27ccd316ff06d6e1` | **함** | 스크립트 없음 |
| `na_ion_cell_meta.csv` | 4,970 B | 64 | `42c90bf81f1967c6` | **함** | 스크립트 없음 |
| `na_ion_detector_grid.csv` | 2,640 B | 80 | `8399a2af07cf5fe0` | **함** | 스크립트 없음 |
| `na_ion_drop_events.csv` | 457 B | 4 | `d7b6361d2206a7e4` | **함** | 스크립트 없음 |

행 수는 보고서 본문의 서술과 교차 검증됩니다 — `1,846,308` · `12,604` · `884`
· `107`(일시적 교차 셀) · `4`(급락 셀) 가 모두 보고서 수치와 같습니다 `[확인]`.

**커밋하는 9개는 합쳐 약 3.3 MB** 입니다. 스크립트가 없어 저장소가 유일한
사본이므로, 크기가 문제되지 않는 한 넣는 것이 맞습니다.

### 2-1. `li_ion_cycle_scan.csv` 만 제외합니다 — 크기 때문이고, **캐시라 안전합니다**

185 MB 는 GitHub 파일당 100 MiB 하드 한계를 넘어 `push` 자체가 실패합니다.
크기가 유일한 제외 사유이므로 `.gitignore` 에 **패턴이 아니라 파일명으로**
못박았습니다 — `analysis/*_cycle_scan.csv` 로 쓰면 `na_ion`(2.5 MB) 까지 같이
빠집니다.

제외해도 안전한 근거는 `docs/reports/2026-08-07_repo_cleanup.md` §11 입니다 `[확인]`.

- 11개 열 중 **8개는 pkl 에서 완전히 재현**됩니다
- 재현 안 되는 3개(`dis_points` · `dis_duration` · `v_end_dis`)는 **방전 구간
  기하**이고 **파생 요약 두 개 어디에도 쓰이지 않습니다**
- 파생 요약의 핵심량 `soh_at_label_repo` 는 `dis_ah_max` 에서 나오며 표본
  22셀에서 **22/22 정확히 재계산**됩니다

즉 이 파일을 잃어도 `li_ion_label_vs_soh.csv` ·
`li_ion_temporary_crossing.csv` 는 pkl 에서 다시 만들 수 있습니다.
부분 재구성은 `analysis/rebuild_cycle_scan.py` 입니다 (전열 일치 90.3%).

**원본은 지우지 않았습니다.** 디스크에 그대로 있고 미추적으로 남습니다.

---

## 3. `analysis/__pycache__/`

`.gitignore` 의 `__pycache__/` 규칙에 이미 걸립니다 `[확인]`. 따로 적을 것 없습니다.

---

## 4. 이 분석들이 무엇을 재는가

| 스크립트 | 질문 |
|---|---|
| `domain_discriminability.py` | 도메인별 Dummy MAPE. 상위 `models/Dummy.py` 정의 그대로 |
| `discriminability_table.py` | 라벨 100 이하 셀이 빠진 **평가 모집단** 기준 Dummy — 모델 행과 비교 가능한 유일한 대조군 |
| `condition_mean_baseline.py` | aging condition 별 train 평균. 무학습 baseline 의 상한 |
| `diversity_breakdown.py` | 포맷 · 화학계 · 온도 · 프로토콜 다양성 (META- 계열 대조용) |
| `conditions_and_reported.py` | 논문 990셀 재계산 · 프로토콜 수 |
| `reported_table.py` | 상위 README 벤치마크 표 파싱 |
| `extract_cell_meta.py` | 전 셀 1,440 pkl 메타 추출 |
| `recount_label_filters.py` | 0.825 폐기 임계 · 중도절단 · 라벨 단조성 위반 재집계 |
| `soh_pipeline_run.py` | 상위 SOH 파이프라인 호출과 셀 단위 제외 사유 (§5) |
| `filter_removal_report.py` | 필터 제거율 — 서브셋별 · 정규화 화학별 · 조건별 (§5) |
| `table1_reconcile.py` | 논문 Table 1 셀 수를 관문 넷으로 분해 (§5) |
| `prompt_probe.py` | aging condition 프롬프트가 pkl 을 읽는가, 셀마다 붙는가 (§5) |
| `soh_measured_boundary.py` | 궤적의 측정/외삽 경계를 되짚고 검증 (§5) |
| `dv_candidates.py` | knee 3종 × 곡률 3종 × 궤적 2판. **고르지 않고 재기만 함** (§5) |
| `power_cluster.py` | 급내상관 · 설계효과 · 검정력 · 최소 탐지 ΔR² (§5) |

**정의가 논문에 없는 것이 섞여 있습니다.** '화학계' 를 (양극·음극·전해질) 삼중조합
으로 센 것, '온도' 를 `cycle_data` 중앙값의 정수 반올림으로 센 것은 이 저장소가
정한 것이고 논문 정의는 확인되지 않았습니다 — 각 스크립트 docstring 에
적혀 있습니다. 다른 정의를 쓰면 값이 달라집니다.

---

## 5. 궤적 확보와 1a 전제 확인 — 2026-08-14 신설 7개

보고서는 `docs/reports/2026-08-14_trajectory_prerequisites.md` 입니다.

이 7개는 앞의 8개와 성격이 다릅니다. **상위 저장소의 전처리 파이프라인을 실제로
돌려 SOH 궤적을 만들고**, 그 궤적 위에서 종속변수 후보와 검정력을 잽니다.
`analysis/out/` 밖에도 씁니다 — 궤적은 `data/soh_v11/` 로, 보고서용 CSV 넷은
`docs/reports/` 로 나갑니다.

### 5-1. 실행 순서와 소요

`.venv-blife/Scripts/python.exe analysis/<이름>.py` 로 **저장소 루트에서** 부릅니다.

| # | 스크립트 | 주 산출 | 소요 | 앞에 필요한 것 |
|---|---|---|---:|---|
| 1 | `soh_pipeline_run.py` | `data/soh_v11/{SOH,processed_SOH,logs}/` · `soh_generation_log.csv` · `soh_skipped_cells.csv` | **7.3분** | `data/extracted/` |
| 2 | `filter_removal_report.py` | `docs/reports/filter_removal_by_chemistry.csv` · `out/filter_removal_{by_subset,cells,summary}` | 6초 | 1 · `out/dataset_cell_census.csv` |
| 3 | `table1_reconcile.py` | `out/table1_reconcile.json` · `out/table1_gate_cells.csv` · `out/removal_by_chemistry_subset.csv` | 8초 | 1 · 2 |
| 4 | `prompt_probe.py` | `out/prompt_samples.md` · `out/prompt_coverage.csv` · `out/prompt_capacity_check.csv` | **9.6분** | `data/extracted/` |
| 5 | `soh_measured_boundary.py` | `out/traj_boundary.csv` | **7.1분** | 1 |
| 6 | `dv_candidates.py` | `docs/reports/dv_candidates.csv` · `dv_disagreement_cells.csv` · `out/dv_correlations.json` · `out/dv_failures.csv` | 40초 | 5 |
| 7 | `power_cluster.py` | `docs/reports/power_analysis.md` · `out/power_analysis.json` | 2초 | 6 |

1·4·5 는 `data/extracted/` 86.45 GB 를 각각 한 번씩 읽습니다. 전량 재생성 약 **25분**.

3 은 `upstream/BatteryMFormer` 의 **git 이력**(`febe174^`)을 읽습니다. submodule 이
초기화되어 있지 않으면 그 관문 열이 비고 사유가 JSON 에 남습니다.

### 5-2. 원시 데이터를 지키기 위해 건너뛴 것

`soh_pipeline_run.py` 는 `run_soh_pipeline.sh` 의 Step 1·1b·2·3·5 만 부르고
**Step 4(`time_normalization.py`)를 부르지 않습니다.** 그 스크립트는
`output_dir = self.input_dir` 로 **`cleaned_data` 를 제자리에서 덮어씁니다**
(`time_normalization.py:367,418,442`). BatteryLife v11 은 이미 시간 정규화가 적용된
판이라(`Version10_Update_Details.md` 4항) 결과에 영향이 없습니다.
건너뛴 사실은 `soh_generation_log.csv` 에 `SKIPPED_WOULD_MODIFY_RAW_DATA` 로 남습니다.

`CALB` 는 두 경로가 같은 디렉터리를 씁니다 — `generate_soh.py` (pkl, 8셀 생존) 뒤에
`generate_CALB_soh.py` (엑셀, 27셀)가 **덮어씁니다.** 앞 산출을
`data/soh_v11/CALB_from_pkl/` 에 사본으로 남깁니다.

### 5-3. 되짚기 검증 — `soh_measured_boundary.py`

`generate_soh.py` 는 외삽 여부를 기록하지 않으므로 산출 pkl 만 보면 어디까지가
측정값인지 알 수 없습니다. 이 스크립트는 원본 pkl(CALB 는 엑셀)에서 상위 코드의
계산을 **외삽 직전까지** 다시 밟아 `n_measured` 를 재고, 되짚은 앞부분이 산출 pkl 과
값이 같은지 셀마다 대조합니다.

> **2026-08-14 실행에서 1,297 / 1,297 셀이 일치했습니다** `[확인]`. 최대 절대차 < 1e-9.

되짚기가 어긋나면 `prefix_match=0` 과 사유가 CSV 에 남습니다. 이 열이 0 인 셀이
있으면 §6 의 `observed` 판 지표를 믿을 수 없습니다.

### 5-4. `dv_candidates.py` 는 고르지 않습니다

의도적으로 **어느 종속변수 정의가 낫다는 판단을 넣지 않았습니다.** 후보마다 값을 내고
정의 사이의 순위상관과 값 차이만 냅니다. 문턱(불일치 셀 선별의 0.7 · 0.05)은 자의적이라
다른 문턱에서의 개수를 `out/dv_correlations.json` 의
`disagreement_counts_by_threshold` 에 함께 남깁니다.

`power_cluster.py` 도 같습니다 — **통계 방법을 고르지 않고** ICC · 설계효과 ·
검정력 · 최소 탐지 ΔR² 만 냅니다.

### 5-5. 재생성 검증은 아직 하지 않았습니다

앞의 8개(§1)와 달리 이 7개는 **두 번 돌려 sha256 을 대조하는 검증을 거치지
않았습니다** `[확인]`. 결정성이 의심되는 지점을 미리 적어 둡니다.

| 지점 | 결정적인가 |
|---|---|
| `generate_soh.py` · `preprocess*.py` | 난수를 쓰지 않습니다 `[확인]`. `num_workers=1` 로 부르므로 프로세스 순서 영향도 없습니다 |
| `dv_candidates.py` 의 격자 탐색·`savgol_filter`·`polyfit` | 난수 없음 `[확인]`. 부동소수점 누적 순서는 입력 순서에 좌우되고 입력은 `sorted()` 로 고정 |
| `power_cluster.py` | 닫힌 식과 `scipy.stats.ncf` 뿐 `[확인]` |
| `soh_pipeline_run.py` 의 `elapsed_s` 열 | **결정적이지 않습니다** — 벽시계입니다. 이 열만 실행마다 달라집니다 |
