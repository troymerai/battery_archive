# LOCK — (태그 미정)

생성: (미정)   /   생성자: (미정)

이 파일이 **"모두가 같은 것을 본다" 의 계약서**입니다.
태그가 배포 단위이고, 태그마다 이 파일이 하나 있습니다.

```
python run.py check       기준값과 현재 상태를 대조
python run.py lock-init   현재 상태로 (미정) 을 채움
```

---

## digest 와 interval — 우열이 아니라 대상의 성질이다

`digest` 는 순수 함수 출력이라 바이트가 같아야 하고, `interval` 은 난수
초기화와 GPU 커널 비결정성 때문에 구간으로만 같다. **우열이 아니라 대상의
성질이다.**

`digest` 항목이 어긋나면 어딘가가 실제로 달라진 것입니다.
`interval` 항목은 기계가 다르면 당연히 다릅니다. 어떤 기계에서 잰
구간인지는 `manifests/hardware.txt` 를 보십시오. 그 파일이 비어 있으면
`interval` 기준값은 의미가 없습니다.

---

## 잠금 항목

| 항목 | 검사 | 기준값 | 비고 |
|---|---|---|---|
| upstream/BatteryML tree | digest | (미정) | sha256, 정규화 후 |
| upstream/BatteryLife tree | digest | (미정) | sha256, 정규화 후 |
| upstream/BatteryMFormer commit | digest | febe174032ad4861fa057b9af23f5bcee8a8fb77 | submodule HEAD |
| verify/ tree | digest | (미정) | 하니스 자신도 잠근다 |
| Life labels.zip | digest | 17c7833302b85f475a81b8d3f8614566 | md5 |
| READMEs.zip | digest | d6768d8a185cdf60c11bff4a4be0f9e3 | md5 |
| CALB.zip | digest | 2b1006e96e0ca42765a732060f964687 | md5 |
| MICH_EXP.zip | digest | e267051a90f0fc02f8e6701b9f3ecc58 | md5 |
| SNL.zip | digest | 900a5bb283ffb0b3255da618118510b7 | md5 |
| NA-ion.zip | digest | bf0a03ac84c74f87a02e203cfc1f9ebf | md5 |
| ZN-coin.zip | digest | d7e98ad70a077ac8f44d5ff045befc73 | md5 |
| Tongji.zip | digest | 432b52d30d655c4c45c6fc6a414dd443 | md5 |
| XJTU.zip | digest | (미정) | md5. LAB-008 검증에 필요 |
| env repro | digest | (미정) | pip freeze sha256 — 라벨 검증 환경 |
| env blife | digest | (미정) | pip freeze sha256 — 학습 환경 |
| nb01 재집계 recount.json | digest | (미정) | 정규화 JSON sha256 |
| nb03 셀 단위 대조표 | digest | (미정) | 정규화 JSON sha256 |
| nb03 도메인 롤업 표 | digest | (미정) | 정규화 JSON sha256 |
| nb03 불일치 셀 목록 | digest | (미정) | 정규화 JSON sha256 |
| nb03 라벨없음(비유한) 셀 목록 | digest | (미정) | XJTU NaN 은 정상 |
| findings/registry.yaml | digest | (미정) | sha256 |
| findings/anchors.yaml | digest | (미정) | sha256 |
| CPTransformer Li-ion MAPE | interval | (미정) | 하드웨어 의존 — `manifests/hardware.txt` 참조 |
| CPTransformer Li-ion 15%-Acc | interval | (미정) | 하드웨어 의존 — `manifests/hardware.txt` 참조 |

---

## 채우는 순서

`(미정)` 은 데이터를 받고 노트북을 한 번 돌린 뒤에야 채울 수 있습니다.

```
1. 데이터 labels 세트 다운로드 + 압축 해제
2. jupyter lab → 00 → 01 → 02 → 03 실행
3. python run.py lock-init
4. git commit && git tag
```

**3번 이전에는 태그를 찍지 마십시오.** LOCK.md 가 비어 있으면
"같은 결과를 본다" 가 성립하지 않습니다.

학습(`interval` 두 행)은 첫 태그 범위 밖입니다. 라벨 검증까지만 담고,
`train/` 과 `experiments/` 는 자리만 잡아둡니다. 그 두 행은 `(미정)` 인
채로 두어도 `python run.py check` 가 `skipped` 로 넘어갑니다.

---

## 어긋났을 때

`python run.py check` 는 **어느 층이 어긋났는지** 알려줍니다.

| 어긋난 층 | 뜻 |
|---|---|
| 코드 tree | 상위 저장소나 `verify/` 가 달라졌다 |
| 데이터 md5 | 받은 zip 이 다르다. 판본(v11/v12) 확인 |
| 환경 해시 | 패키지 버전이 다르다 |
| 결과만 | 위 셋이 다 맞는데 결과가 다르다 |

**셋이 맞는데 결과만 다르면** 비결정성 문제입니다. 시드 · 정렬 ·
부동소수점 누적 순서를 확인하십시오. 그 자체가 보고할 만한 발견이며,
`python run.py check` 출력을 그대로 붙여 공유하면 됩니다.
