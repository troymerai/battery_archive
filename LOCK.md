# LOCK — (태그 미정)

데이터 판본: v11 — Zenodo record 19688272 (2026-04-22)

생성: 2026-08-03   /   생성자: CC (Whitefox 지시)

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
| upstream/BatteryML tree | digest | 7368a9cdc0c375bb7a9ec9a548a7118279a997e1a35e0c245283fa7003c8bca4 | sha256, 정규화 후 |
| upstream/BatteryLife tree | digest | 79795d1fb9c2bc03c618c1990c95479a6d658b1e2a44d876a14df837755e0456 | sha256, 정규화 후 |
| upstream/BatteryMFormer commit | digest | febe174032ad4861fa057b9af23f5bcee8a8fb77 | submodule HEAD |
| verify/ tree | digest | 7909f0381cc103705198335ad6ec1c9e16c51c75e3ca4547e400b1a8ac995baa | 하니스 자신도 잠근다 |
| CALB.zip | digest | 2b1006e96e0ca42765a732060f964687 | md5 · v11(19688272) |
| CALCE.zip | digest | f0f5f1436bc7182d7d5cda05423de8c7 | md5 · v11(19688272) |
| HNEI.zip | digest | 27d009bbb908f04e90ecd9a145d81b62 | md5 · v11(19688272) |
| HUST.zip | digest | de6b6d1b0b20616fbb96c72f3231c082 | md5 · v11(19688272) |
| ISU_ILCC.zip | digest | 98c0561ff25eb68538572c54aeb279ea | md5 · v11(19688272) |
| Life labels.zip | digest | cd0cc01a7211972be45e8e38d86cdeca | md5 · v11(19688272). v12 는 17c78333… — 판본이 다르면 여기서 걸린다 |
| MATR.zip | digest | 83a1528858b9e1b7b6886757bb561669 | md5 · v11(19688272) |
| MICH.zip | digest | cc34ea7ed8edc6419cb30757548ca3da | md5 · v11(19688272) |
| MICH_EXP.zip | digest | e267051a90f0fc02f8e6701b9f3ecc58 | md5 · v11(19688272) |
| NA-ion.zip | digest | bf0a03ac84c74f87a02e203cfc1f9ebf | md5 · v11(19688272) |
| READMEs.zip | digest | f1b28ff26d2cbb1e81455518be9b0e23 | md5 · v11(19688272). v12 는 d6768d8a… — 판본이 다르면 여기서 걸린다 |
| RWTH.zip | digest | f5a0f039503b882613770ef138eb66f4 | md5 · v11(19688272) |
| SDU.zip | digest | 6d557d6e74e7b7cf13f54a9cedd7b38b | md5 · v11(19688272) |
| SNL.zip | digest | 900a5bb283ffb0b3255da618118510b7 | md5 · v11(19688272) |
| Stanford.zip | digest | 6d6892eb5bd1b836635e5786c2b90c6a | md5 · v11(19688272) |
| Stanford_2.zip | digest | 3484565dc7c1dd2baa3df02352bbe8a5 | md5 · v11(19688272) |
| Tongji.zip | digest | 432b52d30d655c4c45c6fc6a414dd443 | md5 · v11(19688272) |
| UL_PUR.zip | digest | 65551018b3d67d96eda724552a0360bd | md5 · v11(19688272) |
| XJTU.zip | digest | ec68d223209b9ddac6c7f5592b2463cd | md5 · v11(19688272). v12 는 2de8b797… 1.5GB 완전판 — 넣지 말 것. LAB-008 · LAB-011 검증에 필요 |
| ZN-coin.zip | digest | d7e98ad70a077ac8f44d5ff045befc73 | md5 · v11(19688272) |
| env repro | digest | e6ecaa73b10a9ef7499a9bb7db77bb2c46fa3135c3cee5d4e0a59861a0ed7120 | pip freeze sha256 — 라벨 검증 환경 |
| env blife | digest | b87483c37cc0f8027092a0010cd3611e1dc5411e06849dc233910032e15a9c33 | pip freeze sha256 — 학습 환경 |
| nb01 재집계 recount.json | digest | e3f9fdbe118219b490468b421d07968b5af0a7a1598a886a7f62bc75b2df5730 | `findings/recount.json` — 1,382셀 재집계. 정규화 JSON sha256 |
| nb02 변형 비교 | digest | eafaba8eec73ab3aaf514c540fc39a6a53db403db9086121f2e4556b759982e5 | `experiments/results/nb02_variants.json` |
| nb03 셀 단위 대조표 | digest | fb3e867ab10d2548f9d98d932766d4dddf2e9971899d393e8b1917b8b8654c60 | `experiments/results/nb03_cells.json` — `code` 변형 |
| nb03 no_soc_span 변형 | digest | c8d92e20a81a17f8fc4935ce17da13bec1c1fec0a1c2da4c924a8483f1c89219 | `experiments/results/nb03_cells_nospan.json` |
| nb03 discharge_denom 변형 | digest | 62078246b6118cd4502bd7279b304201be995b9a8d32f9ea816c9ede15e0a6b9 | `experiments/results/nb03_cells_discharge_denom.json` |
| nb03 도메인 롤업 표 | digest | 90e90782909139ffdaf4fe5df940a2f36a8613bd1f26753839d82bbedf86d6fe | `experiments/results/nb03_rollup.json` |
| nb03 불일치 셀 목록 | digest | 270ad81b3ea6d954c95585153f8fa596523101fb5ca4217a82bd4e57b43d11b6 | `experiments/results/nb03_mismatch.json` |
| nb03 라벨없음(비유한) 셀 목록 | digest | 226c19a73da775d9aa98aca945496848df0b1536d6a559fbb0c6c55144d25d80 | `experiments/results/nb03_nolabel.json` — XJTU NaN 은 정상 |
| nb04 cycle_number 롤업 | digest | 15a171a2eecd3ab5a9c7e67b6e623654d0996707f4ccf36221c2a77c4b0377cc | `experiments/results/nb04_cycle_numbers.json` |
| nb04 셀별 추가 측정 | digest | 58460a02b8577c81af70c52ce12eeda62b7bda3e056e094835b360916b44f284 | `experiments/results/nb04_extras.json` — 셀마다 잰 값 전부 |
| nb05 v2 대조표 원자료 | digest | 6105211369e4066f120a0d65d9e9b3c3945dcd1dad6baed816331c8981d10a87 | `experiments/results/nb05_v2_compare.json` |
| findings/na_ion_crate.json | digest | 06afdc6197fb096ac7d62228abfa9d3ef201083fadac7b4473e23c8d773c2de4 | NA-ion 파일명 ↔ C-rate 매핑 |
| findings/registry.yaml | digest | 48bc03c2ee7d8c8410eaa8fd9df312ef6a94655bfc324c03ea24e78775c7e502 | sha256 |
| findings/anchors.yaml | digest | d73aa1a3769189fb66ab83e97b32a96fb9f52b8baead0ec7c9011aca9c5b294d | sha256 |
| CPTransformer Li-ion MAPE | interval | 0.197 ± 0.019 | 3 seed(2021·42·2024) 평균±표준편차. 하드웨어 의존 — `manifests/hardware.txt` 참조 |
| CPTransformer Li-ion 15%-Acc | interval | 55.7 ± 4.5 | 백분율. 3 seed 평균±표준편차. 하드웨어 의존 — `manifests/hardware.txt` 참조 |

### zip 20개를 전부 잠급니다

이 저장소의 기준 판본은 **v11 (Zenodo record 19688272)** 입니다. 위 md5 는
`manifests/data_md5.txt` 와 같은 값이며, **그 파일이 원본이고 이 표가 사본**
입니다. 값을 고쳐야 하면 `manifests/data_md5.txt` 를 먼저 고치십시오.

v11 과 v12 는 세 파일에서 갈립니다 — `XJTU.zip` · `Life labels.zip` ·
`READMEs.zip`. 나머지 17개는 바이트 단위로 같습니다. 따라서 **v12 를 받은
사람은 정확히 그 세 행에서 불일치가 납니다.** 손상이 아니라 판본 차이입니다
(`findings/registry.yaml` `VER-001`).

`labels` 세트(8개)만 받은 사람은 나머지 12행이 `대상없음`(skip)으로
넘어갑니다. 불일치가 아니라 파일이 없는 것입니다.

### 잠그지 않는 것

`experiments/results/prev_6subset/` 는 6서브셋 440셀 시절의 **보존 사본**
이라 현재 상태의 기준이 아닙니다. `experiments/results/LABEL_REPORT.md` 와
`docs/reports/` 아래 보고서도 잠그지 않습니다 — 사람이 읽는 글이라 표현을 고치면 해시가
바뀌는데, 그것은 결과가 달라진 것과 다릅니다. 잠그는 것은 **정규화 JSON**
뿐입니다.

---

## 채우는 순서

`(미정)` 은 데이터를 받고 노트북을 한 번 돌린 뒤에야 채울 수 있습니다.

```
1. 데이터 다운로드 + 압축 해제 (v11 20개 전부. 부분만 받으면 그 행은 skip)
2. python run.py labels --recount        (노트북 01·02·03 상당, 헤드리스)
   또는 jupyter lab → 00 → 01 → 02 → 03
3. python run.py lock-init
4. git commit && git tag
```

**3번 이전에는 태그를 찍지 마십시오.** LOCK.md 가 비어 있으면
"같은 결과를 본다" 가 성립하지 않습니다.

> ### `lock-init` 을 어느 환경에서 부르는지 보십시오 — 함정입니다
>
> `verify/lock.py` 의 `init()` 은 **부른 인터프리터의 `pip freeze` 를
> `manifests/env_lock/repro.txt` 에 무조건 덮어씁니다.** `env repro` 행이
> 이미 차 있어도 그렇습니다.
>
> 즉 **`.venv-blife` 를 켠 채로 `lock-init` 을 부르면 라벨 검증 환경 기록이
> 학습 환경 것으로 덮여 쓰이고**, 바로 다음 `check` 가 `env repro` 를
> 불일치로 잡습니다. 환경이 바뀐 것이 아니라 기록이 지워진 것입니다.
>
> 2026-08-05 에 실제로 일어났고 백업에서 되돌렸습니다. 학습 환경에서
> `lock-init` 을 불러야 하면 **먼저 `repro.txt` 를 복사해 두십시오.**
>
> ```powershell
> Copy-Item manifests\env_lock\repro.txt manifests\env_lock\repro.bak
> python run.py lock-init
> Move-Item -Force manifests\env_lock\repro.bak manifests\env_lock\repro.txt
> ```

### `interval` 두 행 — 2026-08-04 에 채웠습니다

학습(`interval` 두 행)은 **첫 태그 범위 밖이었습니다.** 그 태그는 라벨
검증까지만 담았고 두 행은 `(미정)` 인 채로 `check` 가 넘어갔습니다.

**36회 학습이 끝나 이제 값이 있습니다.** 다만 `interval` 은 `digest` 와
성질이 다릅니다 — **재현되는 값이 아닙니다.** `lock-init` 이 이 두 행을
채우지 않고 `남김` 으로 넘기는 이유가 그것입니다 (기계가 계산할 수 없고
사람이 잽니다). `check` 는 이 두 행을 `구간` 으로 표시하고 **판정하지
않습니다.** 판정은 사람이 `manifests/hardware.txt` 를 보고 합니다.

| 항목 | 기준값 | 원자료 |
|---|---|---|
| CPTransformer Li-ion MAPE | 0.197 ± 0.019 | 0.1749 / 0.2037 / 0.2116 |
| CPTransformer Li-ion 15%-Acc | 55.7 ± 4.5 | 60.72 / 54.66 / 51.85 |

`runs/2026-08-04/run_liion.log` 의 `Best model performance:` 줄입니다.
**이 구간을 벗어나는 것은 고장이 아닙니다** — GPU 나 torch 가 다르면
당연히 다릅니다. 어긋났을 때 먼저 볼 것은 `manifests/hardware.txt` 이고,
거기 적힌 `[gpu]` · `[torch]` 가 같은데도 벗어나면 그때가 보고할 일입니다.

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
