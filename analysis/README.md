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

전량 재생성에 **약 12분**이 듭니다. 나머지 6개 스크립트는 합쳐서 7초입니다 `[확인]`.

```
label_filter_recount.csv  811b005e6d29e017039c1de59171430977bd0405af3885def8452d4f870132be
cell_meta.csv             29b5d7ae7a2a991d8c472f273d803f374214df482f76ad9b8b5dc4c3f52a2183
```

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

**정의가 논문에 없는 것이 섞여 있습니다.** '화학계' 를 (양극·음극·전해질) 삼중조합
으로 센 것, '온도' 를 `cycle_data` 중앙값의 정수 반올림으로 센 것은 이 저장소가
정한 것이고 논문 정의는 확인되지 않았습니다 — 각 스크립트 docstring 에
적혀 있습니다. 다른 정의를 쓰면 값이 달라집니다.
