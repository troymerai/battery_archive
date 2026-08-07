"""입력 텐서 `.npy` 캐시 만들기 — A/B 라벨 실험 선행 작업.

왜 필요한가
-----------
Li-ion 1회 학습 13분 중 **약 5분이 데이터 읽기**입니다. A/B 라벨 실험은
4모델 × 2조건 × 5시드 = 40회라 읽기만 3시간이 넘습니다. 그런데 **A/B 는
라벨만 바뀌고 입력 텐서는 같습니다.** 한 번 만들어 두면 두 조건이 나눠 씁니다.

무엇을 캐시하는가 — 그리고 무엇을 **캐시하지 않는가**
--------------------------------------------------
`Dataset_original.read_cell_df`
(`upstream/BatteryLife/data_provider/data_loader.py:433-477`) 가 셀 하나에서
내놓는 것 중 **결정적인 부분만** 담습니다.

* `charge_discharge_curves` — `[100, 3, 300]` float64. pkl 적재 + DataFrame
  조립 + 보간 리샘플링의 결과. 여기가 비싼 곳입니다 (0.36초/셀).
* `eol` · `valid_cycle_number` — 샘플 개수를 정하는 두 값.

`cj_aug_charge_discharge_curves` 는 **일부러 캐시하지 않습니다.**
`BatchAugmentation_battery_revised.batch_aug` 는 `m.uniform_(0, 1)`
(`upstream/BatteryLife/utils/augmentation.py:25`) 로 **torch 난수를 뽑습니다.**
건너뛰면 난수열이 밀려서 학습 로더의 셔플 순서가 달라지고, 결과가 기존 36회와
대응하지 않게 됩니다. 그래서 캐시한 텐서에 `batch_aug` 를 **그대로 다시
겁니다.** 0.008초/셀이라 아껴도 의미가 없습니다.

산출물
------
* `data/tensor_cache/<tag>_curves.npy` — `[C, 100, 3, 300]` float64
* `data/tensor_cache/<tag>_index.json` — 행 순서대로의 셀 이름과 셀별 `eol` ·
  `valid_cycle_number`, 그리고 만든 조건

사용
----
    py -3.12 train/build_tensor_cache.py --domain Li-ion
    py -3.12 train/build_tensor_cache.py --domain Li-ion --verify

`--verify` 는 캐시에서 읽은 텐서와 원래 경로로 새로 만든 텐서를
`np.array_equal` 로 대조합니다. **학습을 돌리지 않습니다.**
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BL = REPO / "upstream/BatteryLife"
CACHE_DIR = REPO / "data/tensor_cache"

# 도메인 -> (split_recorder 접두사, 캐시 태그, 제외할 셀)
# Li-ion 은 `.build` 진입점이 만드는 MIX_large_841 판을 따른다
# (`.build/batterylife/run_main_nodeepspeed.py`).
MIX_841_EXCLUDED = [
    "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl",
    "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl",
    "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl",
    "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl",
    "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl",
    "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl",
]

DOMAINS = {
    "Li-ion": {"prefixes": ["MIX_large"], "tag": "liion", "exclude": MIX_841_EXCLUDED},
    "Zn-ion": {"prefixes": ["ZNcoin", "ZN_42", "ZN_2024"], "tag": "znion", "exclude": []},
    "Na-ion": {"prefixes": ["NAion_2021", "NAion_42", "NAion_2024"], "tag": "naion", "exclude": []},
    "CALB": {"prefixes": ["CALB", "CALB_42", "CALB_2024"], "tag": "calb", "exclude": []},
}

SHAPE = (100, 3, 300)


def _install_stubs() -> None:
    """denseweight 가 없어도 data_loader 를 import 할 수 있게 한다.

    학습 환경(.venv-blife)에는 들어 있지만, 라벨 검증 환경에는 없을 수 있다.
    이 스크립트는 `get_loss_weight` 를 부르지 않으므로 스텁으로 충분하다.
    """
    try:
        import denseweight  # noqa: F401
    except ImportError:
        mod = types.ModuleType("denseweight")

        class DenseWeight:  # noqa: D401
            def __init__(self, *a, **k): pass
            def fit(self, x): pass
            def __call__(self, x): return [1.0]

        mod.DenseWeight = DenseWeight
        sys.modules["denseweight"] = mod


def _make_reader(root_path: str):
    """`read_cell_df` 를 부를 수 있는 최소한의 Dataset_original 인스턴스."""
    from data_provider.data_loader import Dataset_original
    from utils.augmentation import BatchAugmentation_battery_revised

    ds = Dataset_original.__new__(Dataset_original)
    ds.args = argparse.Namespace(root_path=root_path, seq_len=1,
                                 charge_discharge_length=300,
                                 early_cycle_threshold=100)
    ds.root_path = root_path
    ds.seq_len = 1
    ds.charge_discharge_len = 300
    ds.early_cycle_threshold = 100
    ds.flag = "train"
    ds.dataset = "MIX_large"
    ds.need_keys = ["current_in_A", "voltage_in_V", "charge_capacity_in_Ah",
                    "discharge_capacity_in_Ah", "time_in_s"]
    # 상위 원본 값 그대로 (data_loader.py:92)
    ds.ZN_coin_charge_first_file_names = [
        'ZN-coin_402-1_20231209225636_01_1.pkl', 'ZN-coin_402-2_20231209225727_01_2.pkl',
        'ZN-coin_402-3_20231209225844_01_3.pkl', 'ZN-coin_403-1_20231209225922_01_4.pkl',
        'ZN-coin_428-1_20231212185048_01_2.pkl', 'ZN-coin_428-2_20231212185058_01_4.pkl',
        'ZN-coin_429-1_20231212185129_01_5.pkl', 'ZN-coin_429-2_20231212185157_01_8.pkl',
        'ZN-coin_430-1_20231212185250_02_6.pkl', 'ZN-coin_430-2_20231212185305_02_7.pkl',
        'ZN-coin_430-3_20231212185323_03_2.pkl']
    ds.aug_helper = BatchAugmentation_battery_revised()
    return ds


def cell_list(domain: str) -> list[str]:
    from data_provider.data_split_recorder import split_recorder
    spec = DOMAINS[domain]
    names: list[str] = []
    for prefix in spec["prefixes"]:
        for flag in ("train", "val", "test"):
            names += list(getattr(split_recorder, f"{prefix}_{flag}_files"))
    excl = set(spec["exclude"])
    # 순서를 고정한다 — 캐시 행 순서가 재현되어야 한다.
    return sorted({n for n in names if n not in excl})


def build(domain: str, root_path: str) -> None:
    import numpy as np

    spec = DOMAINS[domain]
    ds = _make_reader(root_path)
    names = cell_list(domain)
    print(f"{domain}: 후보 {len(names)}셀")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    curves_path = CACHE_DIR / f"{spec['tag']}_curves.npy"
    index_path = CACHE_DIR / f"{spec['tag']}_index.json"

    kept, rows, meta = [], [], {}
    t0 = time.perf_counter()
    for i, fn in enumerate(names, 1):
        try:
            out = ds.read_cell_df(fn)
        except Exception as exc:  # 상위가 던지면 그대로 남기고 건너뛴다
            print(f"  [건너뜀] {fn} — {type(exc).__name__}: {exc}")
            continue
        # eol 이 없으면 상위는 5-튜플을 돌려준다 (data_loader.py:443).
        if len(out) != 6 or out[0] is None:
            print(f"  [건너뜀] {fn} — 라벨없음")
            continue
        _df, curves, eol, _nominal, _cj, vcn = out
        if curves.shape != SHAPE:
            print(f"  [건너뜀] {fn} — shape {curves.shape} != {SHAPE}")
            continue
        kept.append(fn)
        rows.append(np.ascontiguousarray(curves, dtype=np.float64))
        meta[fn] = {"eol": eol, "valid_cycle_number": vcn}
        if i % 50 == 0 or i == len(names):
            el = time.perf_counter() - t0
            print(f"  {i}/{len(names)}  담은 셀 {len(kept)}  {el:.0f}s "
                  f"({el/max(i,1):.3f}s/셀)")

    stacked = np.stack(rows, axis=0)
    np.save(curves_path, stacked)
    index = {
        "domain": domain,
        "tag": spec["tag"],
        "cells": kept,                     # 행 순서 = 이 목록의 순서
        "meta": meta,
        "shape": list(stacked.shape),
        "dtype": str(stacked.dtype),
        "config": {"seq_len": 1, "charge_discharge_length": 300,
                   "early_cycle_threshold": 100, "root_path": root_path},
        "source": "upstream/BatteryLife/data_provider/data_loader.py:read_cell_df",
        "excluded": sorted(spec["exclude"]),
        "note": ("cj_aug 는 담지 않는다 — batch_aug 가 torch 난수를 뽑으므로 "
                 "로더가 캐시된 curves 에 그대로 다시 건다."),
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    size = curves_path.stat().st_size
    print(f"\n담은 셀 {len(kept)} / 후보 {len(names)}")
    print(f"  {curves_path.relative_to(REPO)}  {stacked.shape} {stacked.dtype}  "
          f"{size/1e9:.3f} GB")
    print(f"  {index_path.relative_to(REPO)}")
    print(f"  총 {time.perf_counter()-t0:.0f}s")


def verify(domain: str, root_path: str, n_check: int) -> int:
    """캐시와 원래 경로가 같은 텐서를 내는지 대조. 학습을 돌리지 않는다."""
    import numpy as np

    spec = DOMAINS[domain]
    curves_path = CACHE_DIR / f"{spec['tag']}_curves.npy"
    index_path = CACHE_DIR / f"{spec['tag']}_index.json"
    if not curves_path.exists():
        print(f"캐시가 없습니다: {curves_path}")
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    cached = np.load(curves_path, mmap_mode="r")
    cells = index["cells"]
    ds = _make_reader(root_path)

    # 앞·중간·뒤에서 고르게 뽑는다 (한쪽에 몰리면 검증이 약해진다)
    if n_check >= len(cells):
        picks = list(range(len(cells)))
    else:
        step = len(cells) / n_check
        picks = sorted({int(i * step) for i in range(n_check)})

    ok = bad = 0
    for row in picks:
        fn = cells[row]
        out = ds.read_cell_df(fn)
        fresh = out[1]
        same = np.array_equal(np.asarray(cached[row]), fresh)
        eol_same = out[2] == index["meta"][fn]["eol"]
        vcn_same = out[5] == index["meta"][fn]["valid_cycle_number"]
        if same and eol_same and vcn_same:
            ok += 1
            print(f"  [일치] row {row:4d}  {fn}")
        else:
            bad += 1
            d = np.abs(np.asarray(cached[row]) - fresh)
            print(f"  [불일치] row {row:4d}  {fn}  "
                  f"array_equal={same} eol={eol_same} vcn={vcn_same} "
                  f"maxdiff={d.max():.3e}")

    print(f"\n대조 {len(picks)}셀 — 일치 {ok} · 불일치 {bad}")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", default="Li-ion", choices=sorted(DOMAINS))
    ap.add_argument("--root-path", default=str((REPO / "data/extracted").as_posix()))
    ap.add_argument("--verify", action="store_true", help="만들지 않고 대조만")
    ap.add_argument("--n-check", type=int, default=12, help="--verify 로 볼 셀 수")
    a = ap.parse_args()

    _install_stubs()
    sys.path.insert(0, str(BL))
    os.chdir(BL)  # data_provider/life_classes.json 이 상대 경로다

    if a.verify:
        return verify(a.domain, a.root_path, a.n_check)
    build(a.domain, a.root_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
