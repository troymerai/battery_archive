# 무인 작업 보고서 — 36회 학습 준비 완료

작업일 2026-08-04 (3회차 · 무인) · `D:\battery_archive` · `.venv-blife`

> 이 보고서는 CC 가 한 일과 **관찰한 값**만 적습니다. 판정(`verdict`)은
> 쓰지 않았고, 원인 추정을 사실처럼 적지 않았습니다.

**결론 — 준비가 끝났습니다.** 돌아오셔서 아래 한 줄을 치면 36회가
시작됩니다.

```powershell
cd D:\battery_archive\upstream\BatteryLife
bash -c 'for d in CALB Na-ion Zn-ion Li-ion; do bash D:/battery_archive/.build/batterylife/run_domain.sh "$d"; done'
```

**다만 먼저 읽으실 것이 둘 있습니다.**

1. **Li-ion 9개는 RAM 에서 죽을 수 있습니다.** 새로 나온 것입니다 —
   `data_loader.py:234` 이 Li-ion train 을 **33.7 GiB 배열 한 덩어리**로
   만듭니다. 같은 명령이 한 번은 통과하고 한 번은 `_ArrayMemoryError` 로
   죽었습니다. **CALB · Na-ion · Zn-ion 세 열(27회)은 영향이 없습니다.**
   §8-2 · `findings` TRN-011.
2. **`MIX_large_841` 이라는 이름의 실제 셀 수는 837 입니다.** 이름일 뿐이라
   지금 돌리셔도 결과에는 영향이 없습니다. §8-1.

세 열만 먼저 돌리시려면 §9 의 두 번째 명령입니다 (약 5시간).

---

## 1. 단계별 성패

| 단계 | 내용 | 결과 |
|---|---|---|
| **A** | 저장소 구조 정리 · 참조 수정 · README 갱신 | **성공** (복원 1건 불가 — §2) |
| **B** | `META-005` 정정 | **성공** |
| **C** | 스크립트 36개 재생성 | **성공 — 검증 36/36 통과** |
| **D** | Li-ion 841셀 분할 | **성공 — 로딩 검증 8/8 통과.** 단 실제 셀 수는 **837**, 그리고 RAM 위험 발견 (TRN-011) |
| **E** | 새 기준 시간 실측 | **성공 — OOM 없음. VRAM 최대 1,518 MiB** (한도 15,000) |
| **F** | `docs/RUN.md` · `docs/PLAN.md` 갱신 | **성공** |

시간 상한을 넘긴 단계는 없습니다. D 의 로딩 검증만 620초로 10분 상한에
근접했으나 끝까지 갔습니다.

**계획에 없던 산출물 하나** — `findings/registry.yaml` 에 **`TRN-011`** 을
더했습니다 (Li-ion RAM). 지시에 없던 추가지만, 이 저장소가 그런 사실을
담는 자리가 거기이고 보고서에만 적으면 다음 사람이 못 찾습니다.
슬롯만 채웠고 `verdict` 는 쓰지 않았습니다. 레코드는 42개 → 43개,
기록 요건 위반 0건입니다.

---

## 2. A — 저장소 구조 정리

### 옮긴 파일 (`git mv`, 이력 유지)

| 이전 | 이후 |
|---|---|
| `RUN.md` | `docs/RUN.md` |
| `PLAN.md` | `docs/PLAN.md` |
| `requirements.txt` | `envs/requirements.txt` |
| `CC_REPORT.md` | `docs/reports/2026-08-04_plan.md` |

`envs/` 는 이미 추적 중이어서 `git add envs` 가 필요 없었습니다.

### 복원한 보고서

- `docs/reports/2026-08-03_lock-v11.md` — `git show 1f1d248:CC_REPORT.md`
  로 복원했습니다. 지시서는 `HEAD:CC_REPORT.md` 를 말했지만 `HEAD`
  (48d086c) 는 **2회차 보고서**입니다. lock v11 보고서는 그 앞
  커밋(1f1d248)에 있어 그쪽에서 꺼냈습니다.

### 복원하지 **못한** 것

- **`docs/reports/2026-08-04_train-prep.md` (1회차) — 복원 불가.**
  1회차 보고서는 커밋되기 전에 2회차가 덮어썼습니다. git 이력에
  `CC_REPORT.md` 가 있는 커밋은 셋뿐이고 (ad7f2b8 / 1f1d248 / 48d086c),
  1회차 내용은 어디에도 없습니다. 2회차 보고서 머리말 자체가 "같은 날
  1회차의 보고서는 지시대로 덮어썼습니다" 라고 적고 있습니다.
  그 내용은 `docs/RUN.md` 와 `findings/registry.yaml` TRN-001~003 에
  남아 있습니다.
- ad7f2b8 의 `CC_REPORT.md`(저장소 뼈대 생성, 2026-08-03)는 복원
  **가능**하지만 지시 목록에 없어 만들지 않았습니다. 필요하시면
  `git show ad7f2b8:CC_REPORT.md` 입니다.

### 고친 참조

| 파일 | 고친 것 |
|---|---|
| `run.py:249, :323` | `-r requirements.txt` → `-r envs/requirements.txt` |
| `README.md` | 같음 |
| `docs/RUN.md` | `requirements.txt` → `envs/…`, `PLAN.md` → `docs/PLAN.md` (2곳) |
| `docs/PLAN.md` | `CC_REPORT.md` → `docs/reports/2026-08-04_plan.md`, `RUN.md` → `docs/RUN.md` (2곳) |
| `LOCK.md:95` | "`CC_REPORT.md` 도 잠그지 않습니다" → "`docs/reports/` 아래 보고서도" |
| `train/make_scripts.py:16, :72` | `RUN.md` → `docs/RUN.md` |
| `verify/recount.py:23, :309` | `CC_REPORT.md` → `docs/reports/` |

### 고치지 않은 것

- **`notebooks/*.ipynb` — 해당 참조가 하나도 없었습니다.** 지시대로
  고치지 않았고, 고칠 것도 없었습니다.
- `findings/PAPER_CODE_MAP.md:449, :463` 와 `findings/registry.yaml:664,
  :686` 의 `requirements.txt` — 이것은 `BatteryLife/requirements.txt`
  (상위 저장소)를 가리킵니다. 우리 파일이 아니라 그대로 두었습니다.

### `README.md` 갱신

- 새 절 **"어디에 무엇이 있는가"** — `LOCK.md` · `docs/RUN.md` ·
  `docs/PLAN.md` · `docs/reports/` 넷의 위치와 한 줄 설명.
- **보고서 경로 규칙**을 같은 절에 한 문단으로 적었습니다 —
  `docs/reports/YYYY-MM-DD_<작업명>.md` 에 새로 만들고 루트에
  `CC_REPORT.md` 를 만들지 않으며 덮어쓰지 않습니다.
- "구조" 절의 트리에 `docs/` 와 `envs/` 를 넣었습니다.

### 부수 관찰 — LOCK 대조

`python run.py check` 가 `findings/registry.yaml` 의 digest 를
**FAIL** 로 냅니다.

```
[ FAIL ] findings/registry.yaml   코드/digest
         기준 48bc03c2…  실제 77aace00…
```

**이번 작업 이전부터 어긋나 있었습니다** (2회차에서 registry 를 고친 뒤
`lock-init` 을 돌리지 않았습니다). 이번 §3 의 `META-005` 수정으로 값이 또
바뀌었습니다. `lock-init` 은 **돌리지 않았습니다** — `LOCK.md` 는 계약서라
사람이 정할 일입니다. §8.

---

## 3. B — `META-005` 정정

### 무엇이 틀렸나

`note` 가 `total_MICH/` 를 **"로컬에서 만든 사본"** 이라고 적고
있었습니다. 사실이 아닙니다.

### 근거 (2회차 조사 재확인)

```
data_provider/data_loader.py:390-393
    elif prefix.startswith('MICH'):
        if not os.path.isdir(f'{self.root_path}/total_MICH/'):
            self.merge_MICH(f'{self.root_path}/total_MICH/')
        data = pickle.load(open(f'{self.root_path}/total_MICH/{file_name}', 'rb'))

data_provider/data_loader.py:698-711  merge_MICH()
    os.makedirs(merge_path)
    source_path1 = f'{self.root_path}/MICH/'        # 40개
    source_path2 = f'{self.root_path}/MICH_EXP/'    # 18개
    ... shutil.copy(...) ...
```

### 전 → 후

| 슬롯 | 전 | 후 |
|---|---|---|
| `code.status` | `미조사` | **`미조사` (그대로)** |
| `code.locus` | (빈칸) | `BatteryLife/data_provider/data_loader.py:390-393, 698-711` |
| `code.value` | (빈칸) | total_MICH/ 는 로더가 만든다는 관찰 + "990 이라는 수는 이 부근에 없다" |
| `code.checked_by` | (빈칸) | `CC` |
| `note` | "…로컬 사본을 세면…" | **"정정(2026-08-04): 초기 조사에서 total_MICH/ 를 로컬에서 만든 사본으로 오판했습니다. 실제로는 로더가 생성합니다…"** 추가 |
| `verdict` | (없음) | **(없음 — 쓰지 않았습니다)** |

**`code.status` 를 `미조사` 로 둔 이유.** 이 레코드의 질문은
"990셀 / 99,000샘플" 입니다. 코드에서 확인한 것은 `total_MICH/` 의 출처이지
990 이라는 수가 아닙니다. `확인` 으로 올리면 "코드가 990 을 확인해 준다" 로
읽히고, `부재확인`·`조사했으나불명` 으로 올리면 990 을 코드 전체에서
찾아봤다는 뜻이 되는데 그러지 않았습니다. **가장 덜 주장하는 쪽**을
택했습니다. `run.py claims` 는 기록 요건 위반으로 잡지 않습니다 (42개 전부
위반 없음). 유도 판정은 전후 모두 **미정**으로 같습니다.

`python run.py claims` 를 돌려 `findings/PAPER_CODE_MAP.md` 와
`docs/OPEN_QUESTIONS.md` 를 재생성했습니다.

### 함께 고친 것

`config.env:8` 의 주석도 같은 오판을 담고 있어 고쳤습니다.

```
- total_MICH/(로컬에서 만든 사본, pkl 58개)
+ total_MICH/(로더가 MICH+MICH_EXP 를 복사해 만든 것, pkl 58개)
```

**집계에서 total_MICH 를 뺀 판단 자체는 그대로 유효합니다.** 이중 계산이
되는 것은 사실이고, Zenodo v11 의 20개 파일에 `total_MICH.zip` 이 없는
것도 사실입니다. 바뀐 것은 **누가 그 폴더를 만드는가**뿐입니다.

---

## 4. C — 스크립트 36개

### 검증표 — **36/36 통과**

9개 항목 전부 통과했습니다. 어긋난 파일이 없습니다.

| 항목 | 결과 |
|---|---|
| `checkpoints` (`/path/to`·`/data/hwx` 아님) | 36/36 OK |
| `root_path` 실존 | 36/36 OK (`D:/battery_archive/data/extracted`) |
| `CUDA_VISIBLE_DEVICES=0` | 36/36 OK |
| `--multi_gpu` 없음 | 36/36 OK |
| `--num_workers` = `config.env` 값 (0) | 36/36 OK |
| `dataset` = 표대로 | 36/36 OK |
| `--seed` 명시 + `seed=` 값 일치 | 36/36 OK |
| `batch_size` = 문서값 × 2 | 36/36 OK |
| 모델 이름 3곳(`model_name`·`--model_id`·`comment`) 일치 | 36/36 OK |
| `master_port` 고유 | **36/36** (27000~27035) |

추가로 스크립트별 개별 확인 — `num_process=1` · `--num_processes 1` ·
진입점(`run_main_nodeepspeed.py`) 사용 · `--seed $seed` 전달이 36개 전부
정확히 1회씩 있습니다.

**독립 교차검증도 돌렸습니다** — 생성기를 거치지 않고 문서 표와 원본 셸을
다시 읽어 36개 파일의 7개 문서 항목과 9개 셸 유지 항목을 대조했습니다.
**불일치 0건.**

### `--dataset` 분포

```
9 MIX_large_841   (Li-ion, 3모델 × 3seed)
3 ZN-coin  3 ZN-coin42  3 ZN-coin2024
3 NAion    3 NAion42    3 NAion2024
3 CALB     3 CALB42     3 CALB2024
```

### 배치 환산 (문서값 × 2)

| 모델 | Li-ion | Zn-ion | Na-ion | CALB (2021/42/2024) |
|---|---|---|---|---|
| CPMLP | 16×2=**32** | 64×2=**128** | 64×2=**128** | 8×2=16 / 4×2=8 / 8×2=16 |
| CPTransformer | 128×2=**256** | 32×2=**64** | 16×2=**32** | 8×2=16 / 64×2=128 / 4×2=8 |
| MLP | **32 (셸값)** | 32 (셸값) | 32 (셸값) | 32 (셸값) |

### 문서값과 다르게 쓴 항목

**문서가 지정한 7개 중 다르게 쓴 것은 없습니다.** `batch_size` 만 문서값의
2배이며 그것이 지시된 환산입니다. 각 파일 머리에 계산이 적혀 있습니다.

```
# batch_size = 문서값 8 × 2 (단일 GPU 환산) = 16
```

**문서가 지정하지 않아 셸 값을 그대로 쓴 것 9개** — 이것도 각 파일
머리에 값과 함께 적혀 있습니다.

| 항목 | MLP.sh | CPMLP.sh | CPTransformer.sh |
|---|---|---|---|
| `n_heads` | 8 | 8 | 4 |
| `lstm_layers` | 2 | 2 | 6 |
| `train_epochs` | 100 | 100 | 100 |
| `patience` | 5 | 5 | 5 |
| `early_cycle_threshold` | 100 | 100 | 100 |
| `charge_discharge_length` | 300 | 300 | 300 |
| `seq_len` | 1 | 1 | 1 |
| `lradj` | constant | constant | constant |
| `loss` | MSE | MSE | MSE |

**`MLP` 12개는 하이퍼파라미터 전부가 셸 값입니다.** 문서 표에 `MLP` 이
없습니다 — CyclePatch 계열 넷(CPMLP · CPTransformer · CPGRU · CPLSTM)만
실려 있습니다. 파일 머리에 이렇게 적혀 있습니다.

```
# 문서 근거 없음 — 셸 스크립트 값 사용
#   ... 아래 하이퍼파라미터는 전부 원본 MLP.sh 의 값이며 논문 조건이 아닙니다.
#   바꾼 것은 dataset · model 이름 · seed · master_port 뿐입니다.
```

### 기존 파일 처리

`.build/batterylife/_old_shellparam/` 으로 **옮겼습니다. 지우지
않았습니다.** 14개입니다.

- 지시된 8개: `MLP_CALB` · `MLP_MIX_large` · `CPMLP_CALB` ·
  `CPMLP_MIX_large` · `CPTransformer_CALB` · `CPTransformer_MIX_large` ·
  `Transformer_CALB` · `Transformer_MIX_large`
- **추가로 옮긴 6개** (지시에 없던 판단): `_smoke_CPMLP_CALB.sh` ·
  `_timing_CPMLP_MIX_large.sh` · `_timing_CPMLP_ZN-coin.sh` ·
  `_timing_CPTransformer_MIX_large.sh` · `_timing_CPTransformer_ZN-coin.sh` ·
  `changes.txt`
  — **이유:** 전부 셸 파라미터로 만든 것이고, 새 생성기가 더는 만들지
  않습니다. 새 `_timing36_*.sh` 옆에 옛 `_timing_*.sh` 가 남아 있으면
  어느 쪽을 돌렸는지 나중에 못 가립니다. 지우지 않았으므로 되돌릴 수
  있습니다.

### 치환 내역

`.build/batterylife/changes_36.txt` — 파일별 38블록 1,660줄. 예:

```
=== CPTransformer_CALB_s2024.sh ===
CPTransformer.sh: 치환 13건
    23  [checkpoints]     - /data/hwx/BL_new    + D:/battery_archive/data/checkpoints
    26  [root_path]       - /data/trf/...       + D:/battery_archive/data/extracted
     7  [num_process]     - 2                   + 1
     8  [batch_size]      - 32                  + 8
    30  [CUDA_VISIBLE_DEVICES] - 2,3            + 0
    30  [--num_processes] - $num_process        + 1
    56  [--num_workers]   - 32                  + 0
    30  [--multi_gpu 제거 (NUM_PROCESSES=1)]    + (삭제)
     2  [dataset]         - MIX_large # MIX_large  + CALB2024
     6  [master_port]     - 25216               + 27035
    13  [e_layers (문서값)]   - 6               + 7
    14  [d_layers (문서값)]   - 4               + 6
     5  [learning_rate (문서값)] - 0.00005      + 5e-05
```

문서 항목이 원본 셸과 이미 같으면 치환 줄이 나오지 않습니다 (위 예의
`d_model` · `d_ff` · `dropout` · `seed` 가 그렇습니다). 그래서 파일마다
치환 건수가 9~17 로 다릅니다.

### 함께 만든 것

- `.build/batterylife/run_domain.sh` — 한 도메인 9개를 순차 실행. 하나가
  실패해도 다음이 이어집니다.
- `.build/batterylife/_timing36_CPMLP_CALB_s2021.sh` ·
  `_timing36_CPTransformer_CALB_s2021.sh` — 3에폭 사본 (§6).
- `train/templates/entrypoint.py` — 진입점 본문을 템플릿으로 분리했습니다.
  이전에는 `make_scripts.py` 안의 문자열이었습니다.

### 부수 수정 하나

`train/paths.py` 의 `dataset` 치환 규칙이 줄 끝 주석을 남기고 있었습니다.
`CPTransformer.sh` 의 `dataset=MIX_large # MIX_large` 가
`dataset=CALB # MIX_large` 로 남아 **읽는 사람을 속입니다.** 주석까지
지우도록 고쳤습니다.

---

## 5. D — Li-ion 분할

### **841 이 아니라 837 입니다**

지시서의 분할 수는 실측과 **정확히 일치**했습니다.

```
train 515 - 5 = 510      val 165 - 0 = 165      test 163 - 1 = 162
```

그런데 `510 + 165 + 162 = 837` 입니다. `843 - 6 = 837` 이기도 합니다.
**지시서의 "841" 은 지시서가 함께 준 분할 수와도 맞지 않습니다.**

**이름은 `MIX_large_841` 그대로 두었습니다.** 사람이 정한 이름이고
스크립트 9개·`docs/RUN.md`·`docs/PLAN.md` 가 그 이름을 씁니다. 이름을
바꾸는 쪽이 더 큰 변경이라 **원본을 덜 바꾸는 쪽**을 택했습니다. 대신
진입점이 실행할 때마다 로그에 이렇게 찍습니다.

```
- 2. MIX_large_841 분할 추가 — 라벨 미배포 6셀 제외.
     train 515->510 · val 165->165 · test 163->162  (합계 843 -> 837).
     MICH_EXP 단독 분기는 18셀 그대로.
-    주의 — 이름은 MIX_large_841 이지만 **실제 셀 수는 837** 입니다 (843 - 6).
     이름을 바꿀지는 사람이 정합니다.
```

**이름을 바꿀지는 사람이 정할 일입니다 — §8.** 지금 돌리셔도 결과에는
영향이 없습니다. 이름일 뿐이고 분할 내용은 옳습니다.

### 구현 — `upstream/` 을 고치지 않았습니다

`train/templates/entrypoint.py` → `.build/batterylife/run_main_nodeepspeed.py`
가 런타임에 두 가지를 겁니다.

1. **deepspeed 우회** (기존)
2. **`MIX_large_841` 분할 추가** — `--dataset MIX_large_841` 일 때만

패치 2 의 내용:

- `split_recorder.MIX_large_{train,val,test}_files` 를 6셀 뺀 판으로
  바꾸고, 같은 리스트를 `MIX_large_841_*_files` 로도 답니다.
  **`MICH_EXP_*_files` 는 건드리지 않습니다** — 거기서 빼면
  `--dataset MICH_EXP` 단독 분기까지 오염됩니다.
- `data_loader.py` 의 `elif` 사슬에는 `MIX_large_841` 가지가 없습니다.
  사슬을 고치는 대신 `Dataset_original.__init__` 을 감싸, **데이터셋
  객체에만** `dataset='MIX_large'` 로 보이게 합니다 (`copy.copy(args)`).
  최상위 `args.dataset` 은 `MIX_large_841` 그대로라 **체크포인트 폴더
  이름에 841 이 남습니다.**
- 분할 수·`MICH_EXP` 18셀·제외 6셀을 그 자리에서 확인하고, 하나라도
  어긋나면 **그 자리에서 멈춥니다** (`SystemExit(2)`).

### 진입점 규율 (§D-2)

실행할 때마다 로그 첫머리에 적용된 패치 목록을 찍습니다.

```
========================================================================
[.build 진입점] 원본이 아닙니다. 적용된 패치:
  - 1. deepspeed 우회 — DeepSpeedPlugin 제거, accelerate 기본 경로. 원본은 ZeRO stage-2 입니다 (조건 차이).
  - 2. MIX_large_841 분할 추가 — ...
이 목록을 결과와 함께 남기십시오. 논문과 같은 조건이 아닙니다.
========================================================================
```

`MIX_large_841` 이 아닌 데이터셋으로 돌리면 패치 2 가 꺼져 있다는 것도
함께 찍습니다.

### 검증 — **8/8 통과** (`python -m verify.check_841`)

| 검사 | 결과 |
|---|---|
| `MIX_large` 는 여전히 843 (원본 불변) | **OK** — 515 / 165 / 163 |
| `MICH_EXP` 단독 분기는 여전히 18 (오염 없음) | **OK** — 12 / 3 / 3 |
| 패치 없이는 `MIX_large_841` 이 존재하지 않음 | **OK** |
| `MIX_large_841` = train 510 / val 165 / test 162 | **OK** (= 837) |
| 라벨 미배포 6셀이 빠졌는가 | **OK** — 6셀 모두 |
| **로딩 train** | **OK** — 셀 510 · 샘플 50,300 · 387.5초 |
| **로딩 val** | **OK** — 셀 165 · 샘플 16,200 · 118.7초 |
| **로딩 test** | **OK** — 셀 162 · 샘플 15,800 · 114.2초 |

**로딩이 끝까지 갔습니다.** 전체 620.4초. 10분 상한을 20초 넘겼지만
중단하지 않고 끝냈습니다 — 상한 검사가 각 split 시작 시점이라 test 는
이미 시작한 뒤였습니다. 결과가 나왔으므로 그대로 기록합니다.

앞 두 검사는 **패치를 걸지 않은 별도 프로세스**에서 셌습니다. 같은
프로세스에서 재면 패치가 전역을 덮었는지 구별이 안 됩니다.

**TRN-010(라벨 미배포 6셀)은 해소되었습니다.** Li-ion 9개는 "미검증" 이
아니라 **로딩까지 검증됨** 입니다. 학습은 돌리지 않았습니다.

### 다만 — 새로 나온 것: **Li-ion 은 RAM 에서 죽을 수 있습니다** (TRN-011)

최대 RSS 를 재려고 같은 로딩을 **한 번 더** 돌렸더니 이번에는 죽었습니다.

```
numpy.core._exceptions._ArrayMemoryError: Unable to allocate 33.7 GiB
for an array with shape (50300, 100, 3, 300) and data type float64
```

출처는 `data_provider/data_loader.py:234` 입니다. 데이터셋 생성 마지막에
NaN 검사를 하면서 **리스트 전체를 float64 배열 한 덩어리로** 만듭니다.

```python
self.weights = self.get_loss_weight()
if np.any(np.isnan(self.total_charge_discharge_curves)):    # <- 여기
    raise Exception('Nan in the data')
```

| 분할 | 배열 모양 | 크기 |
|---|---|---:|
| CALB train | (1,689, 100, 3, 300) | 1.1 GiB |
| Zn-ion train | (5,900, 100, 3, 300) | 4.0 GiB |
| Li-ion test | (15,800, 100, 3, 300) | 10.6 GiB |
| Li-ion val | (16,200, 100, 3, 300) | 10.9 GiB |
| **Li-ion train** | **(50,300, 100, 3, 300)** | **33.7 GiB** |

이 기계: 물리 RAM **15.1 GiB**, 커밋 한도 **44.5 GiB**(pagefile 29.4 GiB).

**같은 명령이 한 번은 통과(387.5초)하고 한 번은 죽었습니다.** 갈린 것은
그때 남아 있던 커밋 용량입니다 — 실패 시점의 여유는 18.8 GiB 였습니다.
33.7 GiB 를 한 번에 요구하므로 **커밋 여유가 34 GiB 이상**이어야 합니다.

`upstream/` 은 고치지 않았습니다. 이 줄은 NaN 검사만 하므로 셀 단위로
나눠도 결과가 같아 보이지만 그것은 **추정**이고, 확인하지 않았습니다.
사람이 정할 일입니다 — §8-2.

**CALB · Na-ion · Zn-ion 세 열(27회)은 배열이 4 GiB 이하라 영향이
없습니다.** 그래서 §9 에 "세 열만 먼저" 명령을 따로 넣었습니다.

Li-ion 학습 중의 최대 RSS 는 **재지 못했습니다** (로딩에서 죽었습니다).

---

## 6. E — 새 기준 시간

### 측정 대상과 결과

`train_epochs=3` 사본 둘. **문서 하이퍼파라미터**입니다.
원자료: `runs/measure36.json`.

| 조합 | 파라미터 수 | 전체 wall | 데이터 로딩 | 에폭 평균 | **최대 VRAM** | 최대 RSS |
|---|---:|---:|---:|---:|---:|---:|
| `CPMLP_CALB_s2021` (batch 16) | 170,465 | **24.1초** | 5.1초 | **1.81초** | **1,350 MiB** | **2,128 MiB** |
| `CPTransformer_CALB_s2021` (batch 16) | 812,865 | **34.2초** | 5.1초 | **5.78초** | **1,518 MiB** | **2,279 MiB** |

에폭별: CPMLP 2.07 / 1.66 / 1.70초, CPTransformer 6.03 / 5.83 / 5.48초.

문서값이 실제로 들어갔는지 로그의 `args` 덤프로 확인했습니다 —
CPMLP CALB 2021 은 `d_model=32, e_layers=12, d_layers=6`, CPTransformer
CALB 2021 은 `d_model=64, e_layers=9, d_layers=9`. 문서 표와 같습니다.

### **VRAM 초과 여부 — 초과하지 않았습니다. OOM 도 없었습니다.**

- 최대 **1,518 MiB** / 한도 15,000 MiB / 카드 16,303 MiB
- 유휴 시 958 MiB 가 깔려 있으므로 **순증분은 약 0.4~0.6 GiB**
- 배치를 줄인 일이 없습니다. 문서값 × 2 그대로 돌았습니다.

`nvidia-smi --query-compute-apps` 는 이 기계(Windows WDDM)에서 프로세스별
값을 0 으로 돌려줍니다. 그래서 **GPU 전체 사용량**으로 기록했습니다.

**다만 이것은 CALB · batch 16 의 값입니다.** 실제 36회에는 batch 8~256 이
섞여 있고, `CPTransformer / Li-ion` 은 **batch 256 · 샘플 50,300** 입니다.
**미측정 구간입니다** — §8.

### 데이터 규모 (전부 실측)

| 도메인 | train 셀/샘플 | val | test | 샘플 합 | CALB 대비 | 로딩 |
|---|---|---|---|---:|---:|---:|
| CALB | 17 / 1,689 | 5 / 497 | 5 / 497 | 2,683 | 1.0 | 5.1초 |
| Na-ion | 20 / 2,000 | 6 / 600 | 5 / 500 | 3,100 | 1.2 | 9.6초 |
| Zn-ion | 60 / 5,900 | 20 / 2,000 | 20 / 2,000 | 9,900 | 3.7 | 36.2초 |
| Li-ion | 510 / 50,300 | 165 / 16,200 | 162 / 15,800 | 82,300 | **30.7** | **620.4초** |

### 재추정 — `docs/PLAN.md` §3 갱신

환산식:

```
한 회 = 12초(고정 기동) + 로딩(도메인) + 에폭수 × 에폭시간(모델) × 규모(도메인)
에폭시간: CPMLP 2.1초 · CPTransformer 6.1초 · MLP 2.1초(재지 않음, CPMLP 대입)
규모: 샘플 합 / 2,683
```

**100 에폭 상한:**

| 모델 | CALB | Na-ion | Zn-ion | Li-ion | 행 합계(×3 seed) |
|---|---:|---:|---:|---:|---:|
| MLP † | 3.8분 | 4.4분 | 13.7분 | 117.9분 | 7.0시간 |
| CPMLP | 3.8분 | 4.4분 | 13.7분 | 117.9분 | 7.0시간 |
| CPTransformer | 10.5분 | 12.1분 | 38.3분 | 322.4분 | 19.2시간 |
| **36회 총계** | | | | | **약 33시간** |

**30 에폭(조기 종료)이면 약 11시간.** † MLP 은 근거 없는 대입입니다.

도메인별 누적: CALB 0.9h → Na-ion 1.9h → Zn-ion 5.2h → Li-ion 33h.
**앞의 세 열(CALB · Na-ion · Zn-ion)이 5시간 남짓에 완결됩니다.**

**이전 표는 지우지 않고 `docs/PLAN.md` §3-9 에 "무효 (셸 파라미터 기준)"
로 표시해 남겼습니다.** 같은 기계·같은 코드로 잰 값이라 문서 값 전환이
무엇을 바꿨는지 볼 근거가 됩니다.

### 이 추정의 한계

1. 측정점이 **CALB 둘뿐**입니다. Li-ion 은 30.7배 외삽입니다.
2. 배치가 조합마다 다릅니다 (8~256). 잰 것은 16 둘뿐입니다.
3. VRAM 은 CALB · batch 16 에서만 쟀습니다.
4. **MLP 은 아예 재지 않았습니다.**
5. 조기 종료가 몇 에폭에서 걸릴지 모릅니다. 11시간과 33시간 사이입니다.

**CALB 9개가 끝나면 실측으로 다시 계산하십시오.** 그때는 외삽이 아니라
관측이 됩니다.

---

## 7. F — `docs/RUN.md` 갱신

36개 기준으로 다시 썼습니다. 8개 기준 서술은 전부 걷어냈습니다.

| 절 | 무엇 |
|---|---|
| §2 | **권장 순서** — CALB 9 → Na-ion 9 → Zn-ion 9 → Li-ion 9. 도메인별 셀/샘플/로딩 실측과 9개 추정 |
| §3-1 | **실행 명령 36줄** — 도메인별로 묶어 복사·붙여넣기 가능 |
| §3-2 | **연속 실행** — `run_domain.sh <도메인>`. 하나 실패해도 계속. 네 도메인 잇는 한 줄도 |
| §4 | **백그라운드** — `Start-Process ... -WindowStyle Hidden`. 창을 닫아도 유지 |
| §5 | **중단·재개** — 재개는 없고, 다시 돌리면 체크포인트가 지워진다는 것. `--seed` 를 전부 명시한 이유 |
| §8 | **조건 차이표 갱신** — 지시된 10항목 전부 포함 |
| §8-4 | 하이퍼파라미터가 문서 값이라는 것, 배치 × 2 환산, MLP 은 근거 없음 |
| §8-5 | Li-ion 841(실제 837)셀, 6셀 목록, 검증 명령 |
| §8-6 | Transformer 제외 — OOM 이 아니라 실행 불가 |
| §8-8 | wandb 가 `requirements` 에 없다는 것 |
| §8-9 | **메모리** — RAM 15.1 GiB, Li-ion 이 위험. 배치를 줄이지 말 것 |
| §9 | 재생성 · 재측정 명령 |
| §10 | 읽는 순서 |

조건 차이표는 지시된 항목을 전부 담았습니다 — torch 2.4.1→2.11.0+cu128 ·
pandas/scipy/sklearn · deepspeed 미사용 · wandb · GPU 단일과 배치 환산 ·
num_workers 0 · Li-ion 셀 수 · Transformer 제외 · MLP 문서 근거 없음.

---

## 8. 사람이 정할 것

### 8-1. `MIX_large_841` 이라는 이름 — 실제는 **837** 셀 [권장: 이름 변경]

지시서의 분할 수(510/165/162)는 실측과 정확히 맞았지만 합계는 841 이
아니라 **837** 입니다. `843 - 6 = 837`.

- **그대로 두기** — 지금 바로 돌릴 수 있습니다. 이름만 부정확합니다.
- **`MIX_large_837` 로 바꾸기** — `train/make_scripts.py` 의 `DATASETS`
  와 `train/templates/entrypoint.py` 의 `MIX_841` 상수 두 곳을 고치고
  `python -m train.make_scripts` 를 다시 돌리면 끝입니다. 1분 걸립니다.

**셀 수를 이름에 넣은 문서에서 그 수가 틀린 것은 이 저장소가 가장
경계하는 종류의 오류**라 바꾸는 쪽을 권합니다. 다만 사람이 정한 이름을
CC 가 임의로 바꾸지 않았습니다.

### 8-2. Li-ion 을 돌릴 것인가 — **RAM 이 마지노선입니다** [가장 중요]

`data_loader.py:234` 이 Li-ion train 을 33.7 GiB 배열 하나로 만듭니다
(§5, TRN-011). 선택지:

- **세 열만 먼저 돌리기** [권장] — CALB · Na-ion · Zn-ion 27회, 약
  5시간. Table 3 의 4열 중 3열이 완결됩니다. RAM 위험이 전혀 없습니다.
  명령은 §9 두 번째.
- **Li-ion 도 돌리기** — 돌리기 전에 다른 프로그램을 전부 닫고 커밋
  여유를 확인하십시오.

```powershell
$os = Get-CimInstance Win32_OperatingSystem
"커밋 여유: {0:N1} GiB / 한도 {1:N1} GiB" -f ($os.FreeVirtualMemory/1MB), ($os.TotalVirtualMemorySize/1MB)
```

  **34 GiB 이상**이어야 합니다. 모자라면 pagefile 을 키우는 방법이
  있습니다 (시스템 속성 → 고급 → 성능 → 가상 메모리).
- **`upstream` 을 고치기** — `:234` 를 셀 단위 검사로 바꾸면 이 배열이
  사라집니다. **CC 는 하지 않았습니다.** `upstream/` 은 읽기 전용이고,
  결과가 같을 것이라는 것은 추정입니다. 고치기로 정하시면 `.build/`
  진입점의 세 번째 패치로 넣는 것이 이 저장소의 방식과 맞습니다.

### 8-3. VRAM — `CPTransformer / Li-ion` (batch 256) 이 미측정입니다

잰 것은 CALB · batch 16 둘뿐이고 최대 1,518 MiB 였습니다. 실제 36회 중
가장 무거운 조합은

```
CPTransformer / Li-ion / batch 256 / d_model 256 / d_layers 12 / 샘플 50,300
```

입니다. **재보지 않았습니다.** 지시대로 3에폭 측정은 둘만 했습니다.

- OOM 이 나도 **배치를 줄이지 마십시오** — 줄이는 순간 Table 3 재현이
  아닙니다. `train/measure.py` 는 15,000 MiB 를 넘으면 죽이고 기록만
  합니다.
- 확인하고 싶으시면 Li-ion 을 돌리기 전에 3에폭 사본을 하나 더 만들어
  재는 방법이 있습니다 (`train/make_scripts.py` 의 `TIMING` 에 한 줄
  추가). CC 는 지시 범위를 넘지 않으려고 하지 않았습니다.

### 8-4. `num_workers`

`0` 을 올리지 마십시오 — Windows 는 워커마다 프로세스를 통째 복제합니다.
RAM 15.1 GiB 에서 §8-2 의 배열과 겹치면 확실히 죽습니다.

### 8-5. `LOCK.md` 를 다시 채울 것인가

`findings/registry.yaml` 의 digest 가 어긋나 있습니다 (2회차부터).
이번 `META-005` 수정으로 또 바뀌었습니다.

`python run.py lock-init` 을 돌리면 맞춰지지만 **CC 는 돌리지
않았습니다** — `LOCK.md` 는 "모두가 같은 것을 본다" 의 계약서라 사람이
정할 일입니다.

### 8-6. 1회차 보고서는 복원할 수 없습니다

`docs/reports/2026-08-04_train-prep.md` 는 만들지 못했습니다. git 이력에
없습니다 (§2). 지금부터는 누적되므로 다시 생길 일은 없습니다.

### 8-7. `MLP` 12개를 어떻게 읽을 것인가

문서에 근거가 없어 셸 값으로 돌립니다. **논문 `MLP` 행과 직접 비교할 수
없습니다.** CyclePatch 대조(CPMLP 대 MLP)로만 읽는 편이 안전합니다.
결과 표에 그 사실을 함께 적을지 정하십시오.

---

## 9. 돌아와서 바로 칠 명령

```powershell
cd D:\battery_archive; .\.venv-blife\Scripts\Activate.ps1
```

**36회 전부 (권장 순서대로, 백그라운드):**

```powershell
Start-Process -FilePath "C:\Program Files\Git\bin\bash.exe" `
  -ArgumentList "-c","for d in CALB Na-ion Zn-ion Li-ion; do bash D:/battery_archive/.build/batterylife/run_domain.sh \$d; done" `
  -WorkingDirectory "D:\battery_archive\upstream\BatteryLife" `
  -WindowStyle Hidden
```

**앞의 세 열만 (약 5시간, Table 3 의 3/4 완결):**

```powershell
cd D:\battery_archive\upstream\BatteryLife
bash -c 'for d in CALB Na-ion Zn-ion; do bash D:/battery_archive/.build/batterylife/run_domain.sh "$d"; done'
```

**한 도메인만:**

```powershell
cd D:\battery_archive\upstream\BatteryLife
bash D:/battery_archive/.build/batterylife/run_domain.sh CALB
```

**진행 확인:**

```powershell
Get-ChildItem D:\battery_archive\runs\*_summary.txt | Sort-Object LastWriteTime |
  Select-Object -Last 1 | Get-Content -Wait
```

**돌리기 전에 한 번 확인하고 싶으시면:**

```powershell
python -m train.make_scripts --check   # 36개 × 9항목 검증표
python -m verify.check_841 --structure # 841 분할 목록 검사 (수초)
```

**끝난 뒤 지표:**

```powershell
python -m train.collect --all
```

---

## 10. 읽는 순서

1. **§8 사람이 정할 것** — 특히 **8-2(Li-ion RAM — 가장 중요)** 와
   8-1(이름 837), 8-3(VRAM 미측정)
2. **§9 명령** — 바로 시작하시려면 여기만. 안전한 쪽은 "앞의 세 열만"
3. `docs/RUN.md` **§8 조건 차이표** — 논문과 무엇이 다른지. 이것 없이
   얻은 수치는 비교할 수 없습니다
4. `docs/PLAN.md` **§3** — 소요 시간의 근거와 한계
5. §5(D — Li-ion) · §6(E — 시간) — 이번에 실측한 것
6. §4(C — 36개) — 무엇을 어떻게 만들었는지
7. §2 · §3 — 구조 정리와 `META-005` 정정
