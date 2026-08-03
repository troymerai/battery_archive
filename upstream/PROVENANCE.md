# PROVENANCE — 상위 저장소 입수 기록

`upstream/` 아래는 **전부 남의 코드**입니다. 읽기 전용입니다.
한 글자도 고치지 마십시오. 경로 치환이 필요하면 `train/paths.py` 가
`.build/` 에 사본을 만들어 거기서만 바꿉니다.

입수 시점: 2026-08-03
입수 방식: sparse-checkout (포함 2개) + submodule (1개)

| 저장소 | 커밋 | 기준 커밋과 일치 | 방식 | 라이선스 |
|---|---|---|---|---|
| BatteryML | `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd` | 예 (`2861ae3`) | 포함 | MIT |
| BatteryLife | `9572e47b1d36ecb31fe58f7d2874a7355dbb6fea` | 예 (`9572e47`) | 포함 | MIT |
| BatteryMFormer | `febe174032ad4861fa057b9af23f5bcee8a8fb77` | 예 (`febe174`) | submodule | **없음** |

기계 판독용 사본은 `manifests/upstream_commits.txt` 에 있습니다.

---

## 1. BatteryML — 포함

- 원본: <https://github.com/microsoft/BatteryML>
- 커밋: `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd` (2024-12-18)
- 라이선스: MIT — Copyright (c) Microsoft Corporation
- 입수 방식: **포함** (clone 후 `.git` 제거 → 일반 디렉터리)

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/microsoft/BatteryML.git upstream/BatteryML
cd upstream/BatteryML
git sparse-checkout set batteryml configs bin
cd ../.. && rm -rf upstream/BatteryML/.git
```

sparse-checkout 경로: `batteryml`, `configs`, `bin`

sparse-checkout 을 지정해도 저장소 루트의 파일들(`LICENSE`, `README.md`,
`setup.py`, `requirements.txt`, `*.ipynb`, `*.sh`, `*.md`)은 함께 내려옵니다.
sparse-checkout 은 **디렉터리** 를 거르지 루트 파일을 거르지 않습니다.
**`LICENSE` 는 이 때문에 자동으로 유지되며, 어떤 경우에도 지우지 마십시오.**

제외한 것: 위 3개 디렉터리 밖의 하위 디렉터리 전부. 저장소 대부분이
데이터셋 예제와 노트북 출력이라 라벨 검증에 쓰이지 않습니다.

### `.git` 을 제거한 이유

MIT 는 재배포를 허용하므로 submodule 로 둘 필요가 없습니다. 일반 디렉터리로
포함하면 조원이 `git clone` 한 번으로 코드를 다 받습니다(`--recursive` 를
빠뜨려도 됩니다). 대신 상위 이력이 사라지므로 **커밋 해시를 이 문서와
`manifests/upstream_commits.txt` 에 기록해 추적성을 대신합니다.**

---

## 2. BatteryLife — 포함

- 원본: <https://github.com/Ruifeng-Tan/BatteryLife>
- 커밋: `9572e47b1d36ecb31fe58f7d2874a7355dbb6fea` (2026-07-06)
- 라이선스: MIT — Copyright (c) 2025 Ruifeng Tan（谭瑞锋）
- 입수 방식: **포함** (clone 후 `.git` 제거)

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/Ruifeng-Tan/BatteryLife.git upstream/BatteryLife
cd upstream/BatteryLife
git sparse-checkout set models layers utils data_provider process_scripts \
  assets train_eval_scripts read_structure dataset
cd ../.. && rm -rf upstream/BatteryLife/.git
```

sparse-checkout 경로: `models`, `layers`, `utils`, `data_provider`,
`process_scripts`, `assets`, `train_eval_scripts`, `read_structure`, `dataset`

### 반드시 확인할 것 — `Extract_life_labels_tools/`

`process_scripts/` 안에 `Extract_life_labels_tools/` 가 딸려 옵니다.
**라벨 경로 분기에 필수입니다.** 입수 시점에 존재를 확인했습니다.

```
process_scripts/Extract_life_labels_tools/Farasis_tools.py   (295 줄)
process_scripts/Extract_life_labels_tools/XJTU_tools.py      (136 줄)
```

이 두 파일이 없으면 `verify/labels.py` 의 XJTU·Farasis 분기가 성립하지
않습니다. 재입수 시 가장 먼저 확인하십시오.

제외한 것: 위 9개 디렉터리 밖의 하위 디렉터리. 원본이 약 52 MB 인데
sparse-checkout 후 2.6 MB 입니다. 차이는 대부분 노트북 출력과 그림입니다.

---

## 3. BatteryMFormer — submodule (미포함)

- 원본(저자): <https://github.com/Ruifeng-Tan/BatteryMFormer>
- 참조(fork): <https://github.com/troymerai/BatteryMFormer>
- 커밋: `febe174032ad4861fa057b9af23f5bcee8a8fb77` (2026-06-19)
- 라이선스: **없음**
- 입수 방식: **submodule** — 이 저장소에 파일을 복사하지 않습니다

```bash
git submodule add https://github.com/troymerai/BatteryMFormer.git upstream/BatteryMFormer
cd upstream/BatteryMFormer && git checkout febe174
```

### 왜 포함하지 않는가

1. 원본 저장소에 **LICENSE 파일이 없습니다.** 입수 시점에 저장소 루트를
   확인했고 라이선스 파일이 없음을 확인했습니다. GitHub API 의 `license`
   필드도 `null` 입니다.
2. 라이선스 부재는 허용이 아니라 **기본 저작권**입니다. 저작권자가 아무
   권한도 부여하지 않은 상태이므로 **재배포할 수 없습니다.**
3. 반면 GitHub 이용약관(Section D.5, "License Grant to Other Users")은
   GitHub 내에서의 **fork 는 허용**합니다. 그래서 fork 를 하나 두고
   그것을 submodule 로 참조합니다. 파일은 이 저장소에 들어오지 않고,
   조원은 GitHub 에서 직접 받아갑니다.

### 미결 사항 — 라이선스 문의

저자 `rtan474@connect.hkust-gz.edu.cn` 에게 LICENSE 추가를 요청해 둘 수
있습니다.

| 항목 | 상태 |
|---|---|
| 문의 발송 | (미발송 / 발송일 미기재) |
| 회신 | (없음) |
| 라이선스 명시 여부 | 아니오 |
| 조치 | fork 를 submodule 로 참조 중 |

**회신이 와서 라이선스가 명시되면** submodule 을 걷어내고 포함으로 전환하고,
`NOTICE` 에 고지를 추가한 뒤 이 표를 갱신하십시오. 그 전까지는 이 상태가
정상입니다.

### 조원이 겪는 함정

`--recursive` 없이 clone 하면 `upstream/BatteryMFormer/` 만 **빈 폴더**가
됩니다. 형제 폴더(`BatteryML/`, `BatteryLife/`)는 차 있어서 알아채기
어렵습니다. `notebooks/00_lock_check.ipynb` 첫 셀이 이것을 잡아냅니다.

```bash
git submodule update --init
```

---

## 재입수 절차

커밋이 위 표와 다르게 받아졌다면 **위 해시로 checkout 한 뒤 sparse-checkout
을 적용**하고, 다르다는 사실을 `CC_REPORT.md` 에 기록하십시오.

```bash
git -C upstream/BatteryML checkout 2861ae3
```

단, `.git` 을 제거한 뒤에는 checkout 이 불가능합니다. 그 경우 디렉터리를
지우고 처음부터 다시 clone 하십시오.
