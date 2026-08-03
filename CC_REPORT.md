# CC_REPORT

작업: `battery-repro` 저장소 뼈대 생성
일자: 2026-08-03
위치: `D:\battery_archive` (빈 폴더에서 시작)

---

## 1. 생성한 파일

파일 55개 / 6,713 줄 / 257 KB (`upstream/` 제외).

### 진입점 · 설정

| 줄 | 파일 |
|---:|---|
| 285 | `run.py` — 유일한 공식 진입점 |
| 36 | `Makefile` — `python run.py <명령>` 을 호출만 하는 껍데기 |
| 237 | `README.md` — §9-2 환경 요구사항 절이 맨 앞 |
| 92 | `LOCK.md` — **값은 비워둠** (§6) |
| 87 | `NOTICE` |
| 49 | `config.env.example` |
| 24 | `requirements.txt` |
| 15 | `.gitignore` |
| 14 | `.editorconfig` |
| 13 | `.gitattributes` |
| 3 | `.gitmodules` (submodule 추가 시 자동 생성) |

### `verify/` — 표준 라이브러리 + numpy

| 줄 | 파일 |
|---:|---|
| 489 | `labels.py` — 경로 판정 · 4경로 재현 · 대조 · 도메인 롤업 |
| 345 | `lock.py` — digest/interval 판정, 층 진단, `init()` |
| 344 | `render.py` — 슬롯 → 판정 유도, 두 문서 생성 |
| 258 | `__init__.py` — 인코딩 · 정규화 · 해시 · config |
| 252 | `_minyaml.py` — PyYAML 없을 때의 축소 파서 |
| 180 | `anchors.py` — 스니펫 재탐색, 유효/행이동/내용변경/소실 |
| 162 | `soh.py` — SOH 계산과 SOC span 변형 |

### `train/` — 자리만 잡음

| 줄 | 파일 |
|---:|---|
| 194 | `paths.py` — 하드코딩 치환, `.build/` 사본 |
| 162 | `collect.py` — 로그 파싱 → 지표 JSON |
| 156 | `launch.py` — Git Bash 백그라운드 실행 |
| 22 | `__init__.py` |

### `findings/`

| 줄 | 파일 |
|---:|---|
| 472 | `registry.yaml` — 씨앗 레코드 **23개** |
| 320 | `PAPER_CODE_MAP.md` — 생성물 |
| 165 | `SCHEMA.md` |
| 149 | `anchors.yaml` — 앵커 **11개** |
| 44 | `recount.json` — 빈 틀 |
| 135 | `snippets/*.txt` — 11개 파일 합계 |

### `notebooks/` — 출력을 지운 상태

| 줄 | 파일 | 셀 |
|---:|---|---:|
| 335 | `01_pkl_structure.ipynb` | 13 |
| 335 | `03_label_repro.ipynb` | 20 |
| 237 | `00_lock_check.ipynb` | 15 |
| 200 | `02_soh_definition.ipynb` | 10 |
| 194 | `04_paper_code_walk.ipynb` | 11 |
| 194 | `05_results_read.ipynb` | 12 |

전 노트북 `outputs: []`, `execution_count: null`.

### 나머지

| 줄 | 파일 |
|---:|---|
| 168 | `upstream/PROVENANCE.md` |
| 136 | `papers/NOTES.md` |
| 118 | `papers/fetch.py` |
| 85 | `manifests/data_md5.txt` |
| 83 | `papers/SOURCES.md` |
| 41 | `manifests/hardware.txt` |
| 40 | `docs/OPEN_QUESTIONS.md` — 생성물 |
| 11 | `manifests/upstream_commits.txt` |

빈 자리: `data/.gitkeep`, `experiments/configs/.gitkeep`,
`experiments/results/.gitkeep`, `manifests/env_lock/.gitkeep`

---

## 2. 상위 커밋 — 셋 다 기준과 일치

| 저장소 | 받은 커밋 | §3 기준 | 일치 |
|---|---|---|---|
| BatteryML | `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd` | `2861ae3` | 예 |
| BatteryLife | `9572e47b1d36ecb31fe58f7d2874a7355dbb6fea` | `9572e47` | 예 |
| BatteryMFormer | `febe174032ad4861fa057b9af23f5bcee8a8fb77` | `febe174` | 예 |

`--depth 1` clone 의 HEAD 가 그대로 기준 커밋이었습니다. 재checkout 은
필요하지 않았습니다.

확인한 것:

- `upstream/BatteryML/LICENSE` **있음** (MIT, Microsoft Corporation)
- `upstream/BatteryLife/LICENSE` **있음** (MIT, Copyright (c) 2025 Ruifeng Tan（谭瑞锋）)
- `upstream/BatteryMFormer/LICENSE` **없음** — GitHub API 의 `license` 도 `null`.
  재배포 불가 → submodule 로만 참조. `PROVENANCE.md` 에 기록했습니다.
- fork 의 부모가 `Ruifeng-Tan/BatteryMFormer` 임을 GitHub API 로 확인했습니다
  (인수인계 문서에 원본 URL 이 없어 직접 확인했습니다).
- **`process_scripts/Extract_life_labels_tools/` 딸려 옴 확인** —
  `Farasis_tools.py` (295줄), `XJTU_tools.py` (136줄). 라벨 경로 분기의 전제입니다.

---

## 3. sparse-checkout 후 크기

| 저장소 | 크기 | 파일 수 | §3 예상 |
|---|---|---|---|
| BatteryML | 1.3 MB | 202 | 약 1 MB |
| BatteryLife | 1.8 MB | 134 | 약 1.8 MB |
| BatteryMFormer | 17 MB (`.git` 포함) | 128 | — |

BatteryMFormer 는 submodule 이라 자체 `.git` 을 가집니다. 저장소에 담기는
것은 커밋 해시 한 줄뿐입니다.

sparse-checkout 을 지정해도 **저장소 루트의 파일들은 함께 내려옵니다**
(`LICENSE`, `README.md`, `setup.py` 등). sparse-checkout 은 디렉터리를 거르지
루트 파일을 거르지 않습니다. LICENSE 가 이 덕분에 자동으로 유지되었습니다.

---

## 4. 실행해본 검증

| 검사 | 결과 |
|---|---|
| `python -m py_compile` (우리 `.py` 20개 전부) | **통과** |
| `python run.py --help` | **통과** (아래 4-1 참조) |
| `python run.py check` | **통과** exit 0 — 일치 1 / 미정 15 / 대상없음 8 |
| `python run.py anchors` | **통과** exit 0 — 앵커 11개 전부 `유효` |
| `python run.py claims` | **통과** exit 0 — 레코드 23개, 기록 요건 위반 0 |
| `python run.py data-list` | **통과** (아래 4-2 참조) |
| `python run.py papers --list` | **통과** — 받지 않음 |
| `lock.init()` 사본 시험 | **통과** (아래 4-3 참조) |
| `.gitattributes` 에 `eol=lf` | **있음** (3행 `* text=auto eol=lf`) |
| 작업 트리 CRLF | **0건** / 55개 파일 전부 LF |
| `encoding=` 없는 `open(` · `read_text(` · `write_text(` | **0건** (아래 4-4) |
| `.sh` 파일 생성 (상위 제외) | **0개** |
| `Makefile` 탭 들여쓰기 | 레시피 9줄 전부 탭, 공백 들여쓰기 0줄 |
| `.gitkeep` 4개가 실제로 추적되는가 | **통과** (아래 4-5 — `data/.gitkeep` 은 고쳐야 했습니다) |
| 노트북 JSON 유효성 · 출력 비움 | 6개 전부 유효, `outputs` 0개 |
| `.ipynb` 안의 인코딩 위반 | **0건** |

### 4-1. `run.py --help` 이 처음에 죽었습니다 — 고쳤습니다

```
UnicodeEncodeError: 'cp949' codec can't encode character '\u2014'
```

§9-1 ⑤ 는 **파일 입출력** 의 인코딩을 말하는데, 같은 문제가 **표준 출력**
에도 있었습니다. 한국어 Windows 콘솔의 기본 인코딩이 cp949 라, 한국어 출력에
섞인 `—` 하나로 도구가 죽습니다.

README 가 `setx PYTHONIOENCODING utf-8` 을 안내하지만 **그 설정에 기대지 않도록**
진입점에서 `sys.stdout.reconfigure(encoding="utf-8")` 을 겁니다. 조원이 README
의 그 절을 건너뛰어도 돌아가야 합니다. `run.py`, `train/launch.py`,
`train/collect.py`, `papers/fetch.py` 에 적용했고 `verify.use_utf8_stdout()` 로
공용화했습니다.

### 4-2. `data-list` 가 `Life labels.zip` 에서 깨졌습니다 — 고쳤습니다

공백으로 자르니 `Life` 가 파일명, `labels.zip` 이 md5 가 됐습니다.
§9-1 ⑥ 이 경고한 그 함정입니다. md5 토큰(32자리 hex 또는 `(미확인)`)을
기준으로 잡는 정규식으로 바꿨습니다.

### 4-3. `lock-init` 이 빈 환경을 정상값으로 잠갔습니다 — 고쳤습니다

이 기계의 Python(msys2)에는 pip 이 없어 `pip freeze` 가 빈 결과를 냈고,
`env repro` 에 **빈 문자열의 sha256** 이 채워졌습니다. "아무것도 설치되지 않은
환경" 이 정상 환경인 것처럼 잠기는 상태입니다.

빈 결과면 파일을 만들지 않고 항목을 `(대상없음)` 으로 남기도록 고쳤습니다.
재시험에서 `env repro` 는 채워지지 않고 남았습니다.

시험은 `LOCK.md` **사본** 으로 했습니다. 실제 `LOCK.md` 는 손대지 않았습니다
(§6). `git status` 로 확인 가능합니다 — `(미정)` 19곳 그대로입니다.

### 4-4. 인코딩 검사 방법

단순 grep 은 우리 래퍼(`verify.read_text`)까지 잡아 25건이 나옵니다. 실제
위반은 **내장 `open()` 의 텍스트 모드** 와 **`Path.read_text/write_text`
메서드 호출** 뿐이므로 그것만 가려내는 스크립트로 셌습니다. `.py` 20개와
`.ipynb` 6개 전부에서 **0건** 입니다. 바이너리 `open(..., "rb")` 는 pickle
로딩 등 정당한 용도입니다.

### 4-5. `.gitignore` 의 `data/` 가 `.gitkeep` 을 삼켰습니다 — 고쳤습니다

명세의 `.gitignore` 는 `data/` 다음에 `!data/.gitkeep` 을 둡니다. 그런데 git
은 **제외된 디렉터리 안으로 내려가지 않아** 부정 패턴이 적용되지 않습니다.
`git check-ignore -v data/.gitkeep` 이 `.gitignore:1:data/` 로 잡혔습니다.
그대로 두면 clone 했을 때 `data/` 폴더가 아예 생기지 않습니다.

`data/*` 로 바꿔 해결했습니다. `git status` 에 `?? data/` 가 나옵니다.

### 4-6. 실행하지 못한 검사

- **`make -n`** — 이 기계에 `make` 가 없습니다. Git for Windows 에도 없습니다.
  이것이 §9-1 ① 의 근거이기도 합니다. 대신 탭 들여쓰기를 확인했습니다.
- **`bash -n`** — `.sh` 파일을 만들지 않았으므로 대상이 없습니다 (§9-1 ②).
- **`verify/labels.py` · `verify/soh.py` 의 import·실행 시험** — 이 기계에
  numpy 가 없습니다. **문법 검사(`py_compile`)만 통과했고 한 번도 돌려보지
  못했습니다.** 데이터를 받은 뒤 03 노트북에서 처음 실행됩니다. 여기서 오류가
  날 가능성이 이 저장소에서 가장 높은 곳입니다.

---

## 5. 명세대로 못 만든 것 · 명세에 없는데 만든 것

### 5-1. 값을 비워둔 것 (의도된 것)

- **`LOCK.md`** — §6 대로 값을 채우지 않았습니다. `(미정)` 19곳.
  기준값이 이미 알려진 것(BatteryMFormer 커밋, zip md5 8개)은 채워 넣었습니다.
- `manifests/hardware.txt` — 빈 틀. 학습을 처음 돌린 사람이 채웁니다.
- `manifests/data_md5.txt` 의 용량 칸 — 전부 `(미확인)`. §5-1 절차를 파일
  헤더에 적어 두었습니다.
- `findings/recount.json` — 빈 틀. 01 노트북이 덮어씁니다.
- `papers/NOTES.md` — 빈 틀.

### 5-2. 트리에 없는데 만든 것 (4개)

| 파일 | 왜 |
|---|---|
| `verify/_minyaml.py` | 이 기계에 PyYAML 이 없습니다. 조원은 clone 만 하므로 아무것도 설치하지 않은 상태에서 `check`·`anchors`·`claims` 가 돌아가야 합니다. PyYAML 이 있으면 그쪽을 씁니다. |
| `train/__init__.py` | `from train import paths` 가 되려면 필요합니다. `sys.path` 설정도 겸합니다. |
| `requirements.txt` | 노트북이 numpy·pandas·scikit-learn 을 씁니다. 버전은 고정하지 않았습니다 — LOCK 의 `env repro` 가 pip freeze 해시로 잠급니다. |
| `.editorconfig` | §4 가 `[Makefile] indent_style = tab` 을 지시했는데 트리에는 없었습니다. |

`docs/OPEN_QUESTIONS.md` 는 §4 SCHEMA 절이 참조하는데 트리에 없어 **생성물**
로 만들었습니다 (`python run.py claims` 가 `PAPER_CODE_MAP.md` 와 함께 씁니다).
미해결 절과 **확인불가 종결 절** 이 분리되어 있습니다.

### 5-3. `papers/fetch.sh` → `papers/fetch.py`

§4 본문은 `fetch.sh` 로, 트리와 §9-1 ② 는 `fetch.py` 로 적혀 있습니다.
**§9-1 ② 를 따랐습니다** (충돌하면 Windows 를 택한다). `requests` 없이
`urllib` 만 씁니다. 실행하지 않았습니다.

### 5-4. 인수인계 문서와 실제가 다른 곳

**치환 대상 9개의 위치.** 표는 정확하나 한 파일에 모여 있지 않습니다.
실제 확인한 위치입니다.

| 원본 | 실제 위치 |
|---|---|
| `checkpoints=/data/hwx/BL_new` | `BatteryLife/train_eval_scripts/CPTransformer.sh:24` **한 곳뿐** |
| `root_path=/data/trf/.../dataset` | 같은 파일 `:26` |
| `CUDA_VISIBLE_DEVICES=2,3` | 같은 파일 `:30`. 다른 15개 스크립트는 `0,1` |
| `processed_SOH_path=` · `cache_root=` | **BatteryLife 가 아니라 BatteryMFormer** 의 `train_*.sh` (값은 `/path/to/your/...` 자리표시자) |
| `--num_workers 32` | BatteryLife 스크립트 7개 |
| `num_process=2` · `batch_size=32` | 대부분의 스크립트 앞부분 |
| `/data/trf/...` 절대경로 | `aging_conditions.py:340`, `dataset_overview_calculation.py:76`, `view_monotonicity_results.py:16,19` |

BatteryLife 의 나머지 스크립트는 이미 자리표시자(`/path/to/your/saving/folder`,
`./dataset`)입니다. `train/paths.py` 는 값이 무엇이든 덮어쓰는 정규식으로
썼으니 양쪽 다 처리됩니다.

**서브셋 개수.** §4 는 본 경로를 "나머지 13개" 로 적었는데, Zenodo v12 에
데이터 zip 이 18개이고 Farasis 는 미배포입니다. 숫자가 맞지 않아
`verify/labels.py` 에 개수를 박지 않고 **디스크에 있는 것을 세도록** 했습니다.
01 노트북이 실제 개수를 냅니다.

### 5-5. 코드를 읽다 발견한 것 (registry 에 반영)

- **`--alpha1` 의 도움말이 값과 어긋납니다.** `run_main.py:125-126` 에서
  `--alpha1` (기본 0.15) 의 help 가 `the 10 percent alpha`, `--alpha2`
  (기본 0.1) 의 help 가 `the 15 percent alpha` 입니다. 값과 출력 라벨은
  맞습니다(`alpha_acc1` → `15%-accuracy`). **도움말만 보고 따라가면 15%-Acc 와
  10%-Acc 를 뒤집어 읽습니다.** `train/collect.py` 와 05 노트북에 경고를 넣었습니다.
- **본 경로 외삽이 사이클 20개 미만 셀에서 깨집니다.** `range(n-20, n)` 은
  `n<20` 이어도 20개를 만드는데 `cycle_data[-20:]` 는 n개입니다. 상위 코드는
  여기서 예외로 죽습니다. XJTU 경로는 `min(20, len)` 으로 잘라 쓰므로
  어긋나지 않습니다. `LAB-002` 의 note 와 `verify/labels.py` 의
  `본경로:외삽불가` 상태에 적었습니다.
- **CALB 분기의 `use_extrapolation` 이 이전 반복의 값을 쓸 수 있습니다.**
  `min(SOH)>=0.925` 이면서 EOL 미도달인 셀에서 그렇습니다. `LAB-007` 의 note
  에 적었습니다. CALB 는 어차피 재현불가라 실행으로는 확인되지 않습니다.
- **Farasis 의 λ=0.9 는 실제로 호출되는 경로에 없습니다.** 호출되는 것은
  Excel 의 `efc life` 열을 그대로 읽는 함수이고, 90% SOH 를 계산하는 함수
  (`extract_farasis_life_labels`)는 따로 있으나 쓰이지 않습니다. `LAB-009` 에
  적었습니다.

### 5-6. 현재 판정 분포

`python run.py claims` 기준 — 레코드 23개.

| 판정 | 개수 |
|---|---|
| 미정 | 21 |
| 일치 | 1 (`DAT-001`) |
| 불일치 | 1 (`DAT-002`) |

**`미정` 21개가 정상입니다.** 논문 슬롯이 아직 비어 있기 때문입니다.
`미정` 을 줄이려고 슬롯을 억지로 채우지 마십시오.

`LAB-004` 는 의도대로 **판정 보류** 로 나옵니다 — `paper` 는 `확인` 이지만
`value` 가 비어 있어 값을 비교할 수 없습니다. `render.py` 가 이 경우를
`미정` 으로 유도합니다.

**`확인불가` 는 지금 0개입니다.** Farasis · CALB 의 구조적 확인 불가는 현재
`verify/labels.py` 안에 `재현불가(외부파일)` 로만 있고 registry 슬롯이
아닙니다. 03 노트북에서 셀 단위 표가 나온 뒤 해당 레코드의 슬롯을
`구조적불가` 로 채우면 `확인불가` 종결로 넘어갑니다. 기계는 준비되어 있고
`docs/OPEN_QUESTIONS.md` 에 빈 절이 있습니다.

### 5-7. 하지 않은 것 (§6)

`git add` · `git commit` · `git tag` · `git push`, 데이터 다운로드, 논문 PDF
다운로드, `upstream/` 수정, HuggingFace 접근 — **전부 하지 않았습니다.**

`git init` 과 `git submodule add` 는 §3 이 지시한 것이라 실행했습니다.
`git submodule add` 는 `.gitmodules` 와 submodule 항목을 index 에 올립니다.
커밋은 하지 않았습니다.

---

## 6. 사람이 이어서 할 일

```
1. 이 보고서 확인
2. git add . && git commit -m "init: repro harness skeleton"
3. python run.py papers            논문 PDF 3편
4. 데이터 labels 세트 다운로드 + 압축 해제
   (용량은 zenodo.org/records/21149533 의 Files 표에서 확인)
5. copy config.env.example config.env   → 경로를 자기 기계에 맞게
6. python -m pip install -r requirements.txt
7. jupyter lab → 00 → 01 → 02 → 03
8. python run.py lock-init         LOCK.md 의 (미정) 채우기
9. git commit && git tag v2026.08-meeting5
10. 조원에게 태그 clone 안내
```

**8번 이전에는 태그를 찍지 마십시오.** LOCK.md 가 비어 있으면 "같은 결과를
본다" 가 성립하지 않습니다.

### 먼저 손봐야 할 것

1. **`verify/labels.py` 를 한 번도 돌려보지 못했습니다** (numpy 부재).
   03 노트북에서 처음 실행됩니다. 오류가 날 가능성이 가장 높은 곳입니다.
2. **`manifests/data_md5.txt` 의 용량과 `core`/`full` md5** — Zenodo Files 표
   에서 옮겨 적으십시오. 다운로드 없이 됩니다. 같은 화면에서 `VER-001`
   (v11↔v12 차이)과 `VER-002` (용량) 슬롯이 함께 닫힙니다.
3. **`LAB-004` 의 논문 위치** — 논문에 서술이 있다는 것까지는 확인됐고 절·쪽만
   미확정입니다. `locus` 와 `value` 를 채우면 바로 판정이 납니다.
4. **`REP-001` 의 파일 목록** — 04 노트북 3절이 동명 파일을 해시로 비교해
   실제 목록을 냅니다. 씨앗 레코드의 "13개 전부 상이" 가 맞는지 그 결과로
   확인하고, 틀렸으면 고치십시오. 문서가 아니라 측정이 기준입니다.
5. **BatteryMFormer 라이선스 문의** — `rtan474@connect.hkust-gz.edu.cn`.
   발송 여부를 `upstream/PROVENANCE.md` 의 표에 기록하십시오.

### 조원에게 안내할 때

`README.md` 첫 절(환경 요구사항)을 그대로 보여주면 됩니다. 특히:

- `git clone --recursive` — 빠뜨리면 `upstream/BatteryMFormer/` 만 빈 폴더가
  됩니다. 형제 폴더는 차 있어서 알아채기 어렵습니다. 00 노트북 첫 셀이
  이것을 잡습니다.
- `git config --global core.autocrlf false` — `.gitattributes` 가 LF 를
  강제하지만 전역 설정을 확인해 두는 편이 안전합니다.
- 노트북은 **출력을 지우고** 커밋합니다 (`nbstripout --install`).
