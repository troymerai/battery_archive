# battery-repro

## 환경 요구사항

이 저장소는 **Windows 기준**으로 만들어졌습니다. macOS·Linux 에서도 동작하지만
검증은 Windows 에서 합니다.

| 항목 | 요구 | 비고 |
|---|---|---|
| Python | 3.11 이상 | |
| Git | 2.x | submodule 사용 |
| Git Bash | 모델 학습 시에만 | 라벨 검증에는 불필요 |
| 디스크 | 데이터 별도 확보 | 용량은 `python run.py data-list` 참조 |

### 처음 한 번만 — Windows 설정 3가지

**1. 긴 경로 허용**
HuggingFace 캐시 경로가 260자를 넘습니다.

    git config --global core.longpaths true

관리자 PowerShell 에서 다음도 실행합니다.

    New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
      -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

**2. UTF-8 모드**
한국어 Windows 의 Python 기본 인코딩이 cp949 라 중국어 컬럼명이 깨집니다.

    setx PYTHONUTF8 1
    setx PYTHONIOENCODING utf-8

설정 후 터미널을 새로 엽니다.

**3. 줄바꿈 변환 끄기**
이 저장소는 `.gitattributes` 로 LF 를 강제합니다. 전역 설정이 이를 덮지 않도록 확인합니다.

    git config --global core.autocrlf false

### clone

    git clone --recursive https://github.com/<계정>/battery-repro.git

`--recursive` 를 빠뜨리면 `upstream/BatteryMFormer/` 만 빈 폴더가 됩니다.
형제 폴더는 차 있어서 알아채기 어렵습니다. 빠뜨렸다면:

    git submodule update --init

### 실행

    python run.py check

`make` 를 쓰셔도 되지만 선택 사항이고 macOS·Linux 전용입니다.

### 결과가 LOCK 과 다르면

`python run.py check` 출력이 **어느 층이 어긋났는지** 알려줍니다.
코드 / 데이터 / 환경 셋이 다 맞는데 결과만 다르면 비결정성 문제이며,
그 자체가 보고할 만한 발견입니다. 출력을 그대로 노션에 붙여 주십시오.

---

## 어디에 무엇이 있는가

| 파일 | 무엇 |
|---|---|
| `LOCK.md` | 잠금 항목 (digest / interval). "모두가 같은 것을 본다" 의 계약서 |
| `docs/RUN.md` | 학습 실행법. 36회 실행 명령 · 권장 순서 · **조건 차이표** |
| `docs/PLAN.md` | 논문 Table 3 재현 실행 목록과 소요 시간 추정 |
| `docs/reports/` | 작업 보고서. 날짜순 누적 |

**보고서는 `docs/reports/YYYY-MM-DD_<작업명>.md` 에 새로 만듭니다.** 루트에
`CC_REPORT.md` 를 만들지 않고, 기존 보고서를 덮어쓰지도 않습니다 — 덮어쓰면
무엇을 언제 알았는지가 사라집니다.

---

## 무엇을 하는 저장소인가

**현 시점 상위 저장소 코드의 동작을 확정합니다. 논문 재현이 아닙니다.**
논문은 정답지가 아니라 **비교 대상**입니다.

1. 현재 버전 코드로 **라벨 생성과 모델 학습을 실제로 돌려본다**
2. 나온 값이 배포물·논문과 어떻게 갈리는지 **셀 단위·항목 단위로 짚는다**
3. 각 값에 **상태를 붙인다.** 상태 없는 값은 남기지 않는다

### 무엇이 실패인가

논문 시점과 현재 배포 데이터가 달라 라벨과 분포가 갈리는 것은 **정상입니다.**
그것 자체는 실패가 아닙니다.

| 실패 | 실패 아님 |
|---|---|
| 코드가 안 돌아감 | 배포 라벨과 우리 계산이 다름 → **발견** |
| 값이 다른데 **어느 셀이 어떻게 다른지 못 짚음** | 논문 근거를 못 찾음 → `조사했으나불명` 으로 기록하면 성립 |
| 값에 상태가 안 붙음 (설명 없이 통과) | 확인 경로 자체가 없음 → `구조적불가` 로 기록하면 성립 |
| `미조사` 를 `조사했으나불명` 으로 말함 | |

**"원인 불명이면 안 된다" 를 규칙으로 삼지 않습니다.** Farasis·CALB 라벨처럼
외부 자료 미배포로 구조적으로 확인 불가한 항목이 실재합니다. 그런 압력이
걸리면 그럴듯한 설명을 지어 붙이게 됩니다.

목표는 **불명이 0이 되는 것이 아니라, 불명이 불명으로 남아 있는 것**입니다.
원인 불명 값이 `설명됨` 으로 둔갑하지 않는 것이 이 저장소의 존재 이유입니다.

---

## 운영 원칙

- 조원들은 **clone 만** 합니다. push 하지 않습니다.
- **태그가 배포 단위**입니다. `LOCK.md` 가 "모두가 같은 것을 본다" 의 계약서입니다.
- 상위 저장소 코드는 **한 글자도 고치지 않습니다.** 경로 치환은 실행 시점
  사본(`.build/`)에서만 합니다.

---

## 명령

```
python run.py notebook     jupyter lab 실행 (실제 작업은 여기서)
python run.py labels       라벨 재현 (노트북 03 상당, 헤드리스)
python run.py check        LOCK 대조
python run.py lock-init    현재 상태로 LOCK.md 채우기
python run.py anchors      코드 앵커 유효성 확인
python run.py claims       registry 검증 → findings/PAPER_CODE_MAP.md 재생성
python run.py data-list    받을 데이터 목록 (다운로드 안 함)
python run.py papers       arXiv PDF 3편
```

`labels` 는 노트북 01 · 02 · 03 이 하는 일을 한 번에 냅니다. 계산 규칙은
`verify/labels.py` 를 그대로 쓰며 여기서 새 규칙을 만들지 않습니다.

```
python run.py labels                      상위 코드 규칙 그대로
python run.py labels --variant no_soc_span   SOC span 나눗셈을 뺀 변형 (LAB-005)
python run.py labels --recount            메타 재집계도 함께 (findings/recount.json)
```

두 변형은 **항상 함께** 계산됩니다 — 나란히 놓지 않으면 SOC span 나눗셈이 무엇을
바꾸는지 보이지 않습니다. `--variant` 는 화면 요약에 쓸 쪽만 고릅니다.
사람이 읽을 결과는 `experiments/results/LABEL_REPORT.md` 입니다.

`--subset` · `--limit` 을 준 부분 실행은 산출물을 `experiments/results/scratch/` 에
써서 LOCK 대상 파일을 덮어쓰지 않습니다. 훑어보기 결과가 대조표 자리에 앉지
않게 하기 위해서입니다.

`Makefile` 은 각 타깃이 `python run.py <명령>` 을 호출하기만 하는 껍데기입니다.

---

## 처음 시작할 때

```
1. python -m pip install -r envs/requirements.txt
2. copy config.env.example config.env      경로를 자기 기계에 맞게 고칩니다
3. python run.py check                     지금 상태를 봅니다
4. python run.py papers                    논문 PDF 3편
5. python run.py data-list                 받을 데이터 확인 → 사람이 받습니다
6. python run.py labels --recount          받은 뒤 라벨 재현 (헤드리스)
7. python run.py notebook                  00 → 01 → 02 → 03 순서로
```

6번과 7번은 같은 계산입니다. 6번은 결과를 빨리 보기 위한 것이고, 7번은 그 계산을
자기 손으로 따라가기 위한 것입니다. 6번만 하고 넘어가면 남의 결과를 읽는 것이
됩니다.

노트북은 **출력을 지운 상태로 커밋합니다.** 출력이 들어가면 조원이 자기
손으로 확인하지 않고 남의 결과를 읽게 됩니다.

    python -m pip install nbstripout
    nbstripout --install        # 이 저장소에서 한 번만

---

## 구조

```
LOCK.md              잠금 항목 (digest / interval)
run.py               유일한 공식 진입점
Makefile             run.py 를 호출만 하는 껍데기 (선택)

docs/                사람이 읽는 문서
  RUN.md             학습 실행법 (36회 목록 · 조건 차이표)
  PLAN.md            논문 Table 3 재현 실행 목록과 소요 추정
  OPEN_QUESTIONS.md  사람이 정해야 할 것
  reports/           작업 보고서. 날짜순으로 **누적**합니다

envs/                환경 고정
  requirements.txt   설치 목록
  blife-win.txt      이 기계의 실제 설치본
  constraints.txt    torch 재설치를 막는 제약

upstream/            남의 코드 전부. 읽기 전용 — 한 글자도 고치지 않습니다
  PROVENANCE.md      입수 경로 · 커밋 · 라이선스
  BatteryML/         MIT, 포함
  BatteryLife/       MIT, 포함
  BatteryMFormer/    라이선스 없음 → submodule (fork 참조)

papers/              PDF 는 .gitignore 대상. fetch.py 로 각자 받습니다
notebooks/           몇 분 안에 끝나는 것만
verify/              라벨 · 앵커 · 잠금 검증 (표준 라이브러리 + numpy)
train/               몇 시간 걸리는 것 (Windows 는 Git Bash 필요)
findings/            레코드 · 앵커 · 재집계 결과
manifests/           커밋 · 데이터 md5 · 하드웨어 · 환경 잠금
experiments/         설정과 결과
data/                .gitignore 대상. config.env 로 경로를 겁니다
```

### 노트북

| 노트북 | 무엇 |
|---|---|
| `00_lock_check` | submodule · config · LOCK · 앵커 · 기록 요건 |
| `01_pkl_structure` | pkl 스키마 + **전 서브셋 메타 재집계** → `findings/recount.json` |
| `02_soh_definition` | SOH 정의와 SOC span 변형, 0.825 밴드 |
| `03_label_repro` | 라벨 재현 → 배포 라벨과 셀 단위 대조 → 도메인 롤업 |
| `04_paper_code_walk` | 앵커 원문 읽기, 저장소 간 동명 파일 비교 |
| `05_results_read` | 학습 로그 → 지표 (첫 태그 범위 밖) |

---

## 라벨 경로가 하나가 아닙니다

`Extract_life_labels.py` 의 `cal_life_labels()` 안에 조기 `return` 분기가 있어
서브셋마다 다른 경로를 탑니다. 하나의 규칙으로 뭉뚱그리면 **XJTU 와 Farasis
에서 전부 틀린 답이 나옵니다.**

| 서브셋 | 방식 | 재현 |
|---|---|---|
| **XJTU** | 마지막 하강 구간 **선형 보간** (target 0.80) | 가능 |
| **Farasis** | 외부 Excel 에서 읽음. 단위가 사이클이 아니라 **EFC** | **불가** (파일 미배포) |
| **CALB** | 외부 Excel 요약표 필요. λ=0.9 | **불가** (파일 미배포) |
| 나머지 | SOH 가 λ 아래로 내려간 **첫 사이클 번호** | 가능 |

- **XJTU 라벨에는 비유한값(NaN)이 정상적으로 섞입니다.** 오류로 처리하지 말고
  `라벨없음(비유한)` 으로 둡니다.
- **Farasis · CALB 는 `재현불가(외부파일)`** 로 분류하고 대조에서 제외하되
  표에는 남깁니다. 지우면 "확인했는데 문제없음" 과 구별되지 않습니다.

---

## findings — 슬롯과 판정

레코드마다 `paper` / `upstream_doc` / `code` 세 슬롯이 있고, 슬롯 상태는
**5가지**입니다.

| 상태 | 뜻 | 기록 요건 |
|---|---|---|
| `미조사` | 아직 안 찾아봄 | — |
| `확인` | 있음 | `locus` 필수 |
| `부재확인` | 찾아봤고 없음 | **어디를 봤는지** `searched` 에 |
| `조사했으나불명` | 찾아봤고 근거를 못 댐 | `searched` + 왜 불명인지 |
| `구조적불가` | 확인 경로 자체가 없음 | 왜 불가한지 |

앞의 3개만 두면 "안 찾아봤다" 가 "없다" 로 둔갑합니다.

**`verdict` 는 사람이 쓰지 않습니다.** `python run.py claims` 가 슬롯에서
유도합니다. 판정을 바꾸고 싶으면 슬롯을 고치십시오.

**슬롯이 나뉘어 있어 분담이 됩니다.** 논문 담당이 `paper` 슬롯만 채우고 다른
사람이 `code` 슬롯만 채워도 판정이 나옵니다. 결론을 서로 조율할 필요가
없습니다.

자세한 것은 `findings/SCHEMA.md`.

---

## 태그

**`python run.py lock-init` 으로 `LOCK.md` 를 채우기 전에는 태그를 찍지
마십시오.** LOCK.md 가 비어 있으면 "같은 결과를 본다" 가 성립하지 않습니다.

첫 태그는 라벨 검증까지만 담는 것을 권합니다. `train/` 과 `experiments/` 는
자리만 잡아두고 비워둡니다.

---

## 라이선스

이 저장소가 직접 쓴 코드(`run.py`, `verify/`, `train/`, 노트북, 문서)는 랩
내부용입니다. `upstream/` 아래는 각 원저작자의 것이며 `NOTICE` 와
`upstream/PROVENANCE.md` 에 고지가 있습니다.

- BatteryML — MIT, Microsoft Corporation
- BatteryLife — MIT, Copyright (c) 2025 Ruifeng Tan
- BatteryMFormer — **라이선스 없음.** 재배포 불가라 submodule 로만 참조합니다
