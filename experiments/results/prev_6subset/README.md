# prev_6subset — 직전 판(6서브셋 440셀) 산출물 보존본

2026-08-03 에 **보유 6개 서브셋 440셀** (CALB · MICH_EXP · NA-ion · SNL ·
Tongji · ZN-coin) 만으로 돌린 결과입니다. 같은 날 v11 배포 20개 zip 을 전부
받아 **18개 서브셋 1,382셀** 로 다시 돌리면서, 상위 폴더의 같은 이름 파일을
덮어쓰기 전에 여기로 옮겼습니다.

대조용입니다. **현재 상태를 나타내지 않습니다.**

| 파일 | 내용 |
|---|---|
| `LABEL_REPORT.md` | 440셀 기준 보고서 (절 번호가 지금과 다릅니다 — 1~9절) |
| `nb03_cells.json` | 440셀 `code` 변형 |
| `nb03_cells_nospan.json` | 440셀 `no_soc_span` 변형 |
| `nb03_rollup.json` | 440셀 롤업 |
| `nb03_mismatch.json` | 440셀 불일치 |
| `nb03_nolabel.json` | 440셀 라벨없음 |
| `nb02_variants.json` | 440셀 변형 비교 |
| `recount.json` | 440셀 재집계 (`findings/recount.json` 의 그때 사본) |

`experiments/results/tongji_cycle_numbers.json` 과 `TONGJI_REPORT.md` 는
Tongji 전용 별도 스크립트(`experiments/tongji_cycle_numbers.py`)의 산출물이라
이번 실행이 덮어쓰지 않습니다. 옮기지 않았습니다.
