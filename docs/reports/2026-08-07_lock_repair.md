# LOCK 코드 층 3건 복구 — 작업 보고

2026-08-07 · CC · 파일 수정과 검증까지. **커밋·태그·push 하지 않았습니다.**

모든 사실 주장에 `[확인]`(직접 실행·열람으로 검증) / `[추론]`(정황 추정) /
`[미확인]` 을 붙입니다.

전제 진단: `docs/reports/2026-08-07_repo_cleanup.md` §8 ·
`docs/reports/2026-08-07_lock_drift.md`.

---

## ★ 한 줄

**`python run.py check` 가 전 층 통과합니다 — 불일치 없음 (일치 40), exit 0** `[확인]`.
셋 중 하나(`upstream/BatteryML tree`)는 **기준값을 바꾸지 않고** 오탐 제거로
해결했고, 나머지 둘만 기준값을 갱신했습니다.

| 완료 조건 | 결과 |
|---|---|
| `run.py check` 전 층 통과 | **충족** — 일치 40 · exit 0 |
| `upstream/BatteryML tree` 가 기준값 변경 없이 통과 | **충족** — `7368a9cd…` 그대로 |
| `claims` 가 digest 불일치 시 경고 | **충족** — 양방향 검증 §5 |
| 인덱스가 비어 있다 | **충족** — `git add` 미실행 |
| `repro.txt` 무변경 | **충족** `[확인]` |

**실행 환경.** 모든 명령을 `C:\Users\taeyo\AppData\Local\Programs\Python\Python312\python.exe`
에서 돌렸습니다. `.venv-blife` 를 쓰지 않았고 `run.py lock-init` 을 실행하지
않았습니다 `[확인]`.

---

## 0. 순서를 하나 바꿨습니다 — 근거는 지시 자신입니다

지시는 1 → 2 → 3 → 4 → 5 순이었으나 **5번을 2번 앞으로 옮겼습니다.**

5번(경고 추가)의 구현 자리가 `verify/lock.py` 라 **`verify/` 트리 해시를 다시
바꿉니다.** 지시된 순서대로 하면 2번에서 갱신한 값이 5번 뒤에 곧바로 낡습니다.
이는 지시가 1번과 2번 사이에 대해 적은 것과 같은 이유입니다 —
*"`verify/` 를 수정하면 `verify/ tree` 해시가 다시 바뀐다 … 순서를 뒤집으면
갱신을 두 번 해야 한다."*

실제 순서: **1(오탐 제거) → 5(경고 추가) → 2·3(기준값 갱신) → 4·6(검증)**.

---

## 1. `*.egg-info` 제외 — 기준값 `7368a9cd…` 가 정확히 재현됩니다 `[확인]`

### 1-1. 기존 방식 확인

`_TREE_EXCLUDE_DIRS` 는 **정확 문자열 매칭**입니다 — `verify/__init__.py` 의
`tree_digest()` 가 `part in _TREE_EXCLUDE_DIRS` 로 씁니다 `[확인]`.
따라서 `*.egg-info` 를 그 집합에 넣으면 **동작하지 않습니다.** 이름이
패키지마다 달라(`BatteryML.egg-info`) 고정 문자열로는 못 잡습니다.

그래서 기존 집합은 그대로 두고 **glob 전용 목록을 따로** 두었습니다.

```python
_TREE_EXCLUDE_DIR_GLOBS = ("*.egg-info",)

def _excluded_dir(part: str) -> bool:
    if part in _TREE_EXCLUDE_DIRS:
        return True
    return any(fnmatch.fnmatch(part, pattern) for pattern in _TREE_EXCLUDE_DIR_GLOBS)
```

`tree_digest()` 의 판정 한 줄만 `_excluded_dir(part)` 로 바꿨습니다.
정확 매칭 경로가 먼저 걸리므로 기존 5개의 동작은 바뀌지 않습니다 `[확인]`.

### 1-2. 다른 트리에 영향이 없는지 먼저 봤습니다 `[확인]`

제외 규칙을 넓히면 **지금 통과 중인 트리를 깨뜨릴 수** 있어 먼저 셌습니다.

| 잠금 트리 | `*.egg-info` · `*.dist-info` 개수 |
|---|---:|
| `upstream/BatteryML` | **1** (`BatteryML.egg-info`) |
| `upstream/BatteryLife` | 0 |
| `verify/` | 0 |

영향 범위가 `BatteryML` 하나뿐임을 확인한 뒤 넣었습니다.

### 1-3. 재현 확인 — **기준값과 일치합니다**

```
upstream/BatteryML tree     LOCK 7368a9cdc0c375bb7a9ec9a548a7118279a997e1a35e0c245283fa7003c8bca4
                            현재 7368a9cdc0c375bb7a9ec9a548a7118279a997e1a35e0c245283fa7003c8bca4   MATCH
upstream/BatteryLife tree   LOCK 79795d1fb9c2bc03c618c1990c95479a6d658b1e2a44d876a14df837755e0456
                            현재 79795d1fb9c2bc03c618c1990c95479a6d658b1e2a44d876a14df837755e0456   MATCH
```

**진단이 맞았습니다.** 상위 코드는 한 글자도 바뀌지 않았고, 어긋난 원인은
`pip install -e` 가 만든 빌드 부산물 24 KB 였습니다.
`LOCK.md` 의 `upstream/BatteryML tree` 행은 **고치지 않았습니다** `[확인]`.

`BatteryLife` 가 그대로인 것이 이 수정이 과하지 않았다는 증거입니다 — 제외를
넓혔는데도 egg-info 가 없는 트리는 값이 안 변했습니다.

---

## 2. `verify/ tree` 기준값 갱신

### 2-1. 무엇이 바뀌어 해시가 달라졌는가 `[확인]`

기준값이 박힌 커밋은 `1f1d248`(2026-08-04) 입니다. 그 뒤 `verify/` 변경은
**`c4cbc6b` 하나뿐**입니다.

| 커밋 | 파일 | 변경 |
|---|---|---|
| `c4cbc6b` (`lock: train session 1`) | `verify/check_841.py` | **신규 230행** |
| | `verify/recount.py` | 4행 |
| (이번 작업) | `verify/__init__.py` | `*.egg-info` 제외 (§1) |
| (이번 작업) | `verify/lock.py` | `stale()` 추가 (§5) |

**예상치 못한 변경은 없습니다** `[확인]`. `verify/__pycache__/` 는 트리 해시
제외 대상이라 무관합니다.

### 2-2. 갱신

```
옛 기준  7909f0381cc103705198335ad6ec1c9e16c51c75e3ca4547e400b1a8ac995baa   (1f1d248 시점)
새 기준  2374f542b9326aa9b334e950a94febbf9499b2aaf22cfcb412b2385c458e8f83   (§1·§5 반영 후)
```

`LOCK.md:37` 을 새 값으로 바꾸고 비고에 옛값을 남겼습니다. 지우면 이 행이
언제 왜 바뀌었는지 알 수 없게 됩니다.

> 중간값 기록 — §1 만 반영하고 §5 전에 잰 값은 `a0ae523d7dead01d5…` 였습니다.
> 이 값은 **어디에도 넣지 않았습니다.** §0 의 순서 조정이 없었다면 이 값이
> `LOCK.md` 에 들어갔다가 곧바로 낡았을 것입니다 `[확인]`.

---

## 3. `findings/registry.yaml` 기준값 갱신

저장소 자신의 `verify.sha256_file()` 로 쟀습니다 (텍스트 정규화 후 sha256 —
`sha256sum` 을 그대로 쓰면 값이 다릅니다).

```
옛 기준  48bc03c2ee7d8c8410eaa8fd9df312ef6a94655bfc324c03ea24e78775c7e502   (1f1d248 시점)
새 기준  0189fcf0ace96bca79c6c9b68576aa32ed5fb4b574ceb7493d85195a4f0223e8   (DAT-004 포함)
```

`LOCK.md:72` 를 갱신하고 비고에 **옛값이 `48d086c`(2026-08-04)부터 낡아
있었다**는 사실을 적었습니다. 그 나흘 동안 레코드 18개가 들어왔습니다
(`2026-08-07_lock_drift.md` §3).

`findings/anchors.yaml` 은 `d73aa1a3769189fb66ab83e97b32a96fb9f52b8baead0ec7c9011aca9c5b294d`
로 **전 기간 무사**하여 건드리지 않았습니다 `[확인]`.

---

## 4. `run.py check` 최종 출력 전문 `[확인]`

```
=== LOCK 대조 =====================================================
[  ok  ] upstream/BatteryML tree         코드/digest
[  ok  ] upstream/BatteryLife tree       코드/digest
[  ok  ] upstream/BatteryMFormer commit  코드/digest
[  ok  ] verify/ tree                    코드/digest
[  ok  ] CALB.zip                        데이터/digest
[  ok  ] CALCE.zip                       데이터/digest
[  ok  ] HNEI.zip                        데이터/digest
[  ok  ] HUST.zip                        데이터/digest
[  ok  ] ISU_ILCC.zip                    데이터/digest
[  ok  ] Life labels.zip                 데이터/digest
[  ok  ] MATR.zip                        데이터/digest
[  ok  ] MICH.zip                        데이터/digest
[  ok  ] MICH_EXP.zip                    데이터/digest
[  ok  ] NA-ion.zip                      데이터/digest
[  ok  ] READMEs.zip                     데이터/digest
[  ok  ] RWTH.zip                        데이터/digest
[  ok  ] SDU.zip                         데이터/digest
[  ok  ] SNL.zip                         데이터/digest
[  ok  ] Stanford.zip                    데이터/digest
[  ok  ] Stanford_2.zip                  데이터/digest
[  ok  ] Tongji.zip                      데이터/digest
[  ok  ] UL_PUR.zip                      데이터/digest
[  ok  ] XJTU.zip                        데이터/digest
[  ok  ] ZN-coin.zip                     데이터/digest
[  ok  ] env repro                       환경/digest
[  ok  ] env blife                       환경/digest
[  ok  ] nb01 재집계 recount.json           결과/digest
[  ok  ] nb02 변형 비교                      결과/digest
[  ok  ] nb03 셀 단위 대조표                   결과/digest
[  ok  ] nb03 no_soc_span 변형             결과/digest
[  ok  ] nb03 discharge_denom 변형         결과/digest
[  ok  ] nb03 도메인 롤업 표                   결과/digest
[  ok  ] nb03 불일치 셀 목록                   결과/digest
[  ok  ] nb03 라벨없음(비유한) 셀 목록             결과/digest
[  ok  ] nb04 cycle_number 롤업            결과/digest
[  ok  ] nb04 셀별 추가 측정                   결과/digest
[  ok  ] nb05 v2 대조표 원자료                 결과/digest
[  ok  ] findings/na_ion_crate.json      결과/digest
[  ok  ] findings/registry.yaml          코드/digest
[  ok  ] findings/anchors.yaml           코드/digest
[ 구간 ] CPTransformer Li-ion MAPE       결과/interval
                                         기준 0.197 ± 0.019  (3 seed(2021·42·2024) 평균±표준편차. 하드웨어 의존 — `manifests/hardware.txt` 참조)
[ 구간 ] CPTransformer Li-ion 15%-Acc    결과/interval
                                         기준 55.7 ± 4.5  (백분율. 3 seed 평균±표준편차. 하드웨어 의존 — `manifests/hardware.txt` 참조)

불일치 없음 (일치 40)
```

exit code **0** `[확인]`. `interval` 두 행은 사람이 재는 항목이라 판정 대상이
아닙니다(설계대로).

---

## 5. 재발 방지 — `claims` 의 digest 경고

### 5-1. 구현

`verify/lock.py` 에 `stale(items)` 를 추가했습니다. `check()` 는 데이터 층에서
zip 20개(29 GB)를 md5 해 분 단위가 걸리므로, **지정한 항목만 재는 얇은 함수**를
따로 두었습니다.

`run.py` 의 `cmd_claims()` 끝에서 `findings/registry.yaml` 하나를 재고, 어긋나면
경고를 냅니다. **고치지 않습니다** — `init()` 이 값 있는 행을 건드리지 않는
설계를 그대로 따릅니다.

경고가 본 작업을 막지 않도록 예외를 삼킵니다. `claims` 는 문서 생성이 본업이고,
LOCK 대조 실패로 그것이 멈추면 안 됩니다.

### 5-2. 양방향 동작 검증 `[확인]`

**A. 갱신 후 — 경고가 뜨지 않아야 정상**

```
=== registry 검증 =================================================
레코드 51개
기록 요건 위반 없음

생성: findings/PAPER_CODE_MAP.md
생성: docs/OPEN_QUESTIONS.md
```
경고 없음. exit 0. ✔

**B. `LOCK.md` 를 옛값으로 되돌린 상태 — 경고가 떠야 정상**

```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
경고 — LOCK.md 의 기준값이 낡았습니다: findings/registry.yaml
  LOCK.md:72  기준 48bc03c2ee7d8c8410eaa8fd9df312ef6a94655bfc324c03ea24e78775c7e502
             실제 0189fcf0ace96bca79c6c9b68576aa32ed5fb4b574ceb7493d85195a4f0223e8

  낡은 쪽은 LOCK.md 입니다. 파일이 바뀌었는데 기준값이 안 따라왔습니다.
  `run.py lock-init` 은 (미정) 행만 채우므로 이것을 고치지 못합니다.
  LOCK.md 의 해당 행을 위 '실제' 값으로 직접 고치십시오.
  기준값 변경은 계약 변경입니다 — 새 태그를 찍는 것을 권합니다.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

행 번호(`LOCK.md:72`)까지 찍어 바로 열 수 있게 했습니다.

**C. 원복 검증** — 검증용 임시 수정을 되돌린 뒤 `LOCK.md` 전체 바이트 sha256 을
대조했습니다.

```
before  dea59be9a9f6a0e24147e8095925eea5bccfd53632a81069660c219613c39ff4
after   dea59be9a9f6a0e24147e8095925eea5bccfd53632a81069660c219613c39ff4   RESTORED
```

임시 수정과 원복을 `try/finally` 로 묶어 중간에 실패해도 원본이 남게 했습니다 `[확인]`.

---

## 6. `anchors.yaml` 에도 같은 검사가 필요한가 — **판단 재료만 올립니다**

지시대로 결정하지 않았습니다. 근거는 이렇습니다.

| | `registry.yaml` | `anchors.yaml` |
|---|---|---|
| 크기 | 78 KB · 레코드 51개 | 작음 · 앵커 11개 |
| 무엇이 바꾸는가 | **`run.py claims` 를 돌릴 때마다 사람이 손으로 레코드를 추가** | 사람이 앵커를 새로 만들 때만 |
| 실제 드리프트 이력 | **나흘간 깨짐. 레코드 18개 유입** | **없음. 전 기간 무사** |
| 변경 빈도 | 이 저장소에서 가장 잦음 | 드묾 |

**필요성이 다릅니다.** `registry.yaml` 은 워크플로가 자주 건드리는데 잠겨 있어
구조적으로 어긋났고, `anchors.yaml` 은 그런 압력을 받은 적이 없습니다.

넣는다면 비용은 거의 없습니다 — `lock.stale()` 이 이미 목록을 받으므로
`["findings/registry.yaml", "findings/anchors.yaml"]` 로 한 단어만 늘리면
됩니다. 다만 `claims` 는 앵커를 건드리지 않는 명령이라, **그 명령의 끝에서
앵커를 경고하는 것이 자리에 맞는지**가 걸립니다. 앵커를 검사하는 자연스러운
자리는 `run.py anchors` 로 보입니다 `[추론]`.

**결정은 사용자 몫입니다.**

---

## 7. 지시에 없던 판단이 필요했던 사항

### A. `*.egg-info` 를 어떤 방식으로 넣을 것인가

지시는 "기존 방식에 맞춰 넣으라" 고 했는데 기존은 **정확 문자열 매칭**이라
`*.egg-info` 를 그대로 넣으면 동작하지 않습니다. 선택지가 둘이었습니다.

| 안 | 내용 | 택함 |
|---|---|---|
| A-1 | `BatteryML.egg-info` 를 문자열로 추가 | ✗ — 다른 패키지의 egg-info 는 계속 새어 들어옴 |
| A-2 | glob 목록을 따로 두고 `fnmatch` | **✓** — 지시가 요구한 `*.egg-info` 패턴을 그대로 씀 |

A-2 를 택했고 기존 정확 매칭 집합은 건드리지 않았습니다.

### B. `*.dist-info` 도 넣을 것인가 — **넣지 않았습니다**

같은 계열의 빌드 부산물이지만 지시에 없고, 세 트리 어디에도 존재하지 않습니다.
없는 문제를 미리 막는 것은 이번 범위 밖이라 판단했습니다.

### C. 경고가 exit code 를 바꿔야 하는가 — **바꾸지 않았습니다**

지시는 "경고만 낸다" 였습니다. 그대로 따라 `claims` 의 exit code 는 기존처럼
**기록 요건 위반이 있을 때만 1** 입니다. digest 가 낡아도 0 입니다.

**대가가 있습니다** — CI 나 스크립트에서 `claims` 를 돌리면 경고를 놓칩니다.
사람이 터미널에서 볼 때만 보입니다. 이것을 강제하려면 exit code를 바꾸거나
`check` 를 별도로 돌려야 하는데, 둘 다 지시 범위 밖이라 하지 않았습니다.

### D. 순서 조정 (§0)

지시된 5번을 2번 앞으로 옮겼습니다. 지시 자신의 근거를 적용한 것이지만
순서를 바꾼 것은 사실이라 여기 적습니다.

---

## 8. 건드리지 않은 것 `[확인]`

| 규칙 | 준수 |
|---|---|
| `commit` · `tag` · `push` · `add` 금지 | 한 번도 실행 안 함. 인덱스 0개 |
| `upstream/` 무수정 | `git status upstream/` 비어 있음 |
| Python312 에서만 실행 | 모든 `run.py` 호출이 Python312 |
| `lock-init` 금지 | 실행 안 함 |
| 데이터·환경·결과 층 기준값 무수정 | 코드 층 2행만 고침 (`LOCK.md:37` · `:72`) |
| `repro.txt` 무변경 | `git status` 로 확인 |
| 루트 `CC_REPORT.md` 무생성 | 이 보고서는 `docs/reports/2026-08-07_lock_repair.md` |

변경된 파일은 넷입니다.

```
 M LOCK.md              코드 층 2행 갱신
 M run.py               claims 끝에 digest 경고
 M verify/__init__.py   *.egg-info 트리 제외
 M verify/lock.py       stale() 추가
```
