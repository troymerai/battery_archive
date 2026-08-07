"""캐시 경로와 원래 경로가 **같은 Dataset** 을 만드는지 대조한다.

`train/build_tensor_cache.py --verify` 는 셀 하나짜리 텐서만 봤다. 이쪽은
`Dataset_original` 을 통째로 두 번 지어서 비교한다.

세 가지를 본다.

1. `total_charge_discharge_curves` — 입력 텐서 전부가 바이트 단위로 같은가
2. `total_labels` · `total_seen_unseen_IDs` · `class_labels` — 라벨 층이 같은가
3. **torch 난수 상태** — 데이터셋을 다 지은 뒤 RNG 가 같은 자리에 있는가.
   `batch_aug` 가 난수를 뽑으므로, 캐시가 이걸 건너뛰면 학습 로더의 셔플
   순서가 달라진다. 텐서가 같아도 이게 다르면 결과가 대응하지 않는다.

학습을 돌리지 않는다.

    py -3.12 train/verify_tensor_cache.py --dataset CALB --tag calb
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BL = REPO / "upstream/BatteryLife"
CACHE_DIR = REPO / "data/tensor_cache"


def _install_stubs() -> None:
    try:
        import denseweight  # noqa: F401
    except ImportError:
        mod = types.ModuleType("denseweight")

        class DenseWeight:
            def __init__(self, *a, **k): pass
            def fit(self, x): pass
            def __call__(self, x): return [1.0]

        mod.DenseWeight = DenseWeight
        sys.modules["denseweight"] = mod


def install_cache(tag: str):
    """`.build` 진입점 패치 3 과 **같은 코드** 를 적용한다."""
    import numpy as np
    from data_provider import data_loader as dl

    index = json.loads((CACHE_DIR / f"{tag}_index.json").read_text(encoding="utf-8"))
    cfg = index["config"]
    rows = {name: i for i, name in enumerate(index["cells"])}
    meta = index["meta"]
    curves = np.load(CACHE_DIR / f"{tag}_curves.npy", mmap_mode="r")

    original = dl.Dataset_original.read_cell_df
    stats = {"hit": 0, "miss": 0}

    def read_cell_df_cached(self, file_name):
        row = rows.get(file_name)
        same_cfg = (self.charge_discharge_len == cfg["charge_discharge_length"]
                    and self.early_cycle_threshold == cfg["early_cycle_threshold"]
                    and self.seq_len == cfg["seq_len"])
        if row is None or not same_cfg:
            stats["miss"] += 1
            return original(self, file_name)
        stats["hit"] += 1
        arr = np.array(curves[row], dtype=np.float64)
        m = meta[file_name]
        cj_aug, _fm = self.aug_helper.batch_aug(arr)
        return True, arr, m["eol"], None, cj_aug, m["valid_cycle_number"]

    dl.Dataset_original.read_cell_df = read_cell_df_cached
    return original, stats


def build_dataset(dataset: str, flag: str, root_path: str, seed: int):
    """run_main.py:204-211 과 같은 순서로 train -> val -> test 를 짓는다.

    val/test 는 train 이 만든 스케일러를 받아야 하고(`data_loader.py:251`),
    무엇보다 **난수 소비 순서가 그 순서에 달려 있다.** 한 벌만 지으면
    RNG 대조가 실제 학습과 다른 것을 보게 된다.
    """
    import numpy as np
    import torch
    from data_provider.data_loader import Dataset_original

    torch.manual_seed(seed)
    np.random.seed(seed)

    args = argparse.Namespace(
        root_path=root_path, seq_len=1, charge_discharge_length=300,
        early_cycle_threshold=100, dataset=dataset, data="Dataset_original",
        weighted_loss=False, target_dataset="None",
    )
    built = {"train": Dataset_original(args=args, flag="train")}
    if flag != "train":
        ls = built["train"].return_label_scaler()
        lcs = built["train"].return_life_class_scaler()
        for f in ("val", "test"):
            built[f] = Dataset_original(args=args, flag=f, label_scaler=ls,
                                        life_class_scaler=lcs)
            if f == flag:
                break
    rng_after = torch.randint(0, 2 ** 31 - 1, (8,)).tolist()
    return built[flag], rng_after


def snapshot(ds):
    import numpy as np
    return {
        "curves": np.asarray(ds.total_charge_discharge_curves, dtype=np.float64),
        "labels": np.asarray(ds.total_labels, dtype=np.float64),
        "raw_labels": np.asarray(ds.raw_labels, dtype=np.float64),
        "seen_unseen": np.asarray(ds.total_seen_unseen_IDs),
        "class_labels": np.asarray(ds.class_labels),
        "dataset_ids": np.asarray(ds.total_dataset_ids),
        "attn": np.asarray(ds.total_curve_attn_masks),
    }


def main() -> int:
    import numpy as np

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="CALB", help="data_loader 의 dataset 이름")
    ap.add_argument("--tag", default="calb", help="캐시 태그")
    ap.add_argument("--flag", default="test", choices=["train", "val", "test"])
    ap.add_argument("--seed", type=int, default=2021)
    ap.add_argument("--root-path", default=str((REPO / "data/extracted").as_posix()))
    ap.add_argument("--mix841", action="store_true",
                    help="Li-ion 용. 라벨 미배포 6셀을 빼 .build 패치 2 와 맞춘다")
    a = ap.parse_args()

    _install_stubs()
    sys.path.insert(0, str(BL))
    os.chdir(BL)
    from data_provider import data_loader as dl

    if a.mix841:
        # `.build` 진입점 패치 2 와 같은 제외. 라벨이 없는 6셀을 남겨 두면
        # read_cell_df 가 5-튜플을 돌려주어 양쪽 경로가 똑같이 죽는다(TRN-010).
        from data_provider.data_split_recorder import split_recorder
        excluded = [
            "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl",
            "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl",
            "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl",
            "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl",
            "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl",
            "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl",
        ]
        for f in ("train", "val", "test"):
            name = f"MIX_large_{f}_files"
            kept = [x for x in getattr(split_recorder, name) if x not in excluded]
            setattr(split_recorder, name, kept)
        print(f"  MIX_large_841 제외 적용 — train/val/test = "
              f"{[len(getattr(split_recorder, f'MIX_large_{f}_files')) for f in ('train','val','test')]}")

    print(f"[1/2] 원래 경로로 짓는 중 — dataset={a.dataset} flag={a.flag} seed={a.seed}")
    ds_plain, rng_plain = build_dataset(a.dataset, a.flag, a.root_path, a.seed)
    snap_plain = snapshot(ds_plain)

    print(f"[2/2] 캐시 경로로 짓는 중 — tag={a.tag}")
    original, stats = install_cache(a.tag)
    try:
        ds_cached, rng_cached = build_dataset(a.dataset, a.flag, a.root_path, a.seed)
        snap_cached = snapshot(ds_cached)
    finally:
        dl.Dataset_original.read_cell_df = original

    print(f"\n캐시 적중 {stats['hit']} · 비적중 {stats['miss']}")
    print(f"샘플 수: 원래 {len(snap_plain['labels'])} · 캐시 {len(snap_cached['labels'])}")

    bad = 0
    for key in snap_plain:
        p, c = snap_plain[key], snap_cached[key]
        if p.shape != c.shape:
            print(f"  [불일치] {key:14} shape {p.shape} != {c.shape}")
            bad += 1
            continue
        same = np.array_equal(p, c)
        if same:
            print(f"  [일치]   {key:14} {p.shape} {p.dtype}")
        else:
            d = np.abs(p.astype(float) - c.astype(float))
            print(f"  [불일치] {key:14} maxdiff={d.max():.3e} "
                  f"다른 원소 {int((p != c).sum())}/{p.size}")
            bad += 1

    rng_same = rng_plain == rng_cached
    print(f"\n  torch 난수 상태 {'일치' if rng_same else '불일치'} — "
          f"원래 {rng_plain[:4]} · 캐시 {rng_cached[:4]}")
    if not rng_same:
        bad += 1

    print("\n결과: " + ("전부 일치" if bad == 0 else f"불일치 {bad}건"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
