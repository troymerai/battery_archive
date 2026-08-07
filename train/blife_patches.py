"""상위 로더에 거는 패치 — **학습 경로와 추론 경로가 같은 코드를 쓰게 한다.**

왜 이 파일이 있는가
-------------------
텐서 캐시 패치가 `train/templates/entrypoint.py`(학습)와
`train/infer_cell_preds.py`(추론)에 **복제되어 있었다**
(`docs/reports/2026-08-07_cell_predictions.md` §10-1). A/B 실험에서 80회를
돌릴 예정이라 둘이 어긋나면 조용히 다른 조건으로 도는 사고가 난다.
한 군데로 모은다.

`upstream/` 을 고치지 않는다. 전부 실행 시점 monkeypatch 다.

여기 있는 것
------------
* `apply_mix841` — 라벨 미배포 6셀을 뺀 `MIX_large_841` 분할
* `install_tensor_cache` — 리샘플링된 입력 텐서 캐시
* `install_label_source` — A/B 라벨 교체

세 함수 모두 **되돌리는 함수를 돌려준다.** 한 프로세스에서 여러 조합을 돌 때
앞 조합의 패치가 남지 않게 하기 위해서다.
"""

from __future__ import annotations

import json
from pathlib import Path

# `.build` 진입점 패치 2 의 목록과 같아야 한다.
MIX_841_EXCLUDED = [
    "MICH_13R_pouch_NMC_25C_50-100_0.2-0.2C.pkl",
    "MICH_14C_pouch_NMC_-5C_50-100_0.2-0.2C.pkl",
    "MICH_15H_pouch_NMC_45C_50-100_0.2-0.2C.pkl",
    "MICH_17C_pouch_NMC_-5C_50-100_0.2-1.5C.pkl",
    "MICH_18H_pouch_NMC_45C_50-100_0.2-1.5C.pkl",
    "MICH_16R_pouch_NMC_25C_50-100_0.2-1.5C.pkl",
]

MIX_841_EXPECT = {"train": 510, "val": 165, "test": 162}

# 도메인 -> 텐서 캐시 태그
CACHE_TAG = {"Li-ion": "liion", "Zn-ion": "znion", "Na-ion": "naion", "CALB": "calb"}


class LabelMissing(RuntimeError):
    """지정한 라벨 원본에서 어떤 셀의 수명을 찾지 못했다.

    상위는 이 상황에서 **터진다** — `read_cell_df` 가 eol 이 없을 때 5-튜플을
    돌려주는데(`data_loader.py:443`) `read_samples_from_one_cell:487` 이 6개를
    푼다. 잠복 결함이고, 라벨 A 에서는 `.build` 진입점이 문제 셀 6개를 미리
    빼기 때문에 드러나지 않았다 (TRN-010).

    조용히 그 셀을 건너뛰면 **표본이 바뀐다.** 그래서 건너뛰지 않고, 어느
    셀인지 짚어 멈춘다. 어차피 상위도 멈추므로 치명도는 같고 메시지만 낫다.
    """

    def __init__(self, file_name: str, labels_dir):
        self.file_name = file_name
        self.labels_dir = labels_dir
        super().__init__(
            f"'{file_name}' 의 수명 라벨을 {labels_dir} 에서 찾지 못했습니다.\n"
            f"  상위 read_samples_from_one_cell(data_loader.py:487) 이 5-튜플을 "
            f"6개로 풀려다 ValueError 로 죽는 자리입니다.\n"
            f"  건너뛰면 표본이 바뀝니다 — 조용히 넘기지 않습니다.\n"
            f"  docs/reports/2026-08-07_label_ab_manifest.md 를 보십시오.")


# ------------------------------------------------------------------ 분할

def apply_mix841(split_recorder, die=None):
    """`MIX_large_*_files` 를 841 판으로 바꾸고 되돌리는 함수를 돌려준다.

    `MICH_EXP_*_files` 는 건드리지 않는다 — 거기서 빼면 `--dataset MICH_EXP`
    단독 분기까지 오염된다.
    """
    before = {}
    for flag in ("train", "val", "test"):
        name = f"MIX_large_{flag}_files"
        original = list(getattr(split_recorder, name))
        before[name] = original
        kept = [f for f in original if f not in MIX_841_EXCLUDED]
        setattr(split_recorder, name, kept)
        setattr(split_recorder, f"MIX_large_841_{flag}_files", kept)
        if die is not None and len(kept) != MIX_841_EXPECT[flag]:
            die(f"{flag} 이 {len(kept)}셀입니다. {MIX_841_EXPECT[flag]} 이어야 "
                f"합니다 (원본 {len(original)}). 상위 분할이 바뀌었습니다.")

    def restore():
        for name, original in before.items():
            setattr(split_recorder, name, original)
    return restore


# ------------------------------------------------------------ 텐서 캐시

def install_tensor_cache(data_loader_module, cache_dir: Path, tag: str, die=None,
                         eol_lookup=None):
    """`Dataset_original.read_cell_df` 를 감싸 pkl 적재+리샘플링을 건너뛴다.

    `batch_aug` 는 **건너뛰지 않는다.** `utils/augmentation.py:25` 의
    `m.uniform_(0, 1)` 이 torch 난수를 뽑으므로, 건너뛰면 난수열이 밀려 학습
    로더의 셔플 순서가 달라진다. 0.008초/셀이라 아껴도 의미가 없다.

    ``eol_lookup`` — **A/B 라벨 실험에서 반드시 줘야 한다.**

    캐시 색인은 만들 때의 수명 라벨(`eol`)을 **함께 담고 있다.** 그래서 캐시를
    켠 채 라벨만 갈아 끼우면 `read_cell_df` 가 통째로 대체되어
    `read_cell_data_according_to_prefix` 를 부르지 않고, **라벨 교체가 조용히
    무시된다.** 캐시를 만든 시점의 라벨이 그대로 쓰인다.

    이 인자를 주면 `eol` 만 그쪽에서 받아 온다. 입력 텐서와
    `valid_cycle_number` 는 라벨과 무관하므로 캐시 값을 그대로 쓴다 — A/B 가
    입력을 공유한다는 캐시의 취지가 유지된다. `None` 을 돌려주면 그 셀은
    라벨없음으로 버려진다 (상위와 같은 처리).

    돌려주는 값: (되돌리는 함수, 통계 dict, 설명 문자열)
    """
    import numpy as np

    cache_dir = Path(cache_dir)
    npy_path = cache_dir / f"{tag}_curves.npy"
    idx_path = cache_dir / f"{tag}_index.json"
    if not npy_path.exists() or not idx_path.exists():
        msg = (f"텐서 캐시가 없습니다.\n  {npy_path}\n  {idx_path}\n"
               f"  먼저 `python train/build_tensor_cache.py --domain <도메인>` 을 돌리십시오.")
        if die is not None:
            die(msg)
        return None, {"hit": 0, "miss": 0, "off": True}, msg

    index = json.loads(idx_path.read_text(encoding="utf-8"))
    cfg = index["config"]
    rows = {n: i for i, n in enumerate(index["cells"])}
    meta = index["meta"]
    curves = np.load(npy_path, mmap_mode="r")
    if len(curves) != len(index["cells"]):
        msg = f"캐시 행 수 {len(curves)} 와 셀 목록 {len(index['cells'])} 가 다릅니다."
        if die is not None:
            die(msg)
        raise SystemExit(msg)

    original = data_loader_module.Dataset_original.read_cell_df
    stats = {"hit": 0, "miss": 0, "off": False}

    def read_cell_df_cached(self, file_name):
        row = rows.get(file_name)
        # 캐시를 만든 조건과 다르면 손대지 않는다. 조용히 다른 텐서를 먹이는 것이
        # 가장 나쁘다.
        same_cfg = (self.charge_discharge_len == cfg["charge_discharge_length"]
                    and self.early_cycle_threshold == cfg["early_cycle_threshold"]
                    and self.seq_len == cfg["seq_len"])
        if row is None or not same_cfg:
            stats["miss"] += 1
            return original(self, file_name)
        stats["hit"] += 1
        m = meta[file_name]
        # 라벨은 캐시가 아니라 지정된 원본에서 받는다 (A/B 실험).
        eol = m["eol"] if eol_lookup is None else eol_lookup(file_name)
        if eol is None:
            stats["no_label"] = stats.get("no_label", 0) + 1
            raise LabelMissing(file_name, getattr(eol_lookup, "labels_dir", "(라벨 원본)"))
        # mmap 뷰가 아니라 사본을 준다. 상위는 이 객체를 batch_aug 에 넘기고
        # 같은 객체를 돌려주므로 그 흐름을 그대로 흉내 낸다.
        arr = np.array(curves[row], dtype=np.float64)
        cj_aug, _fm_aug = self.aug_helper.batch_aug(arr)
        # 상위 반환 순서: df, curves, eol, nominal_capacity, cj_aug, valid_cycle_number
        # df 는 `is None` 검사에만, nominal_capacity 는 아무 데도 쓰이지 않는다
        # (data_loader.py:487-489 이 유일한 호출부).
        return True, arr, eol, None, cj_aug, m["valid_cycle_number"]

    data_loader_module.Dataset_original.read_cell_df = read_cell_df_cached

    def restore():
        data_loader_module.Dataset_original.read_cell_df = original

    desc = (f"{npy_path.name} ({len(index['cells'])}셀, "
            f"{tuple(index['shape'])} {index['dtype']})")
    return restore, stats, desc


# -------------------------------------------------------- 셀 경계 관측

def install_cell_recorder(data_loader_module):
    """`read_samples_from_one_cell` 을 감싸 셀마다 몇 샘플이 나왔는지 **관측**한다.

    셀 경계를 미리 계산해 둔 표에서 읽어 오면 라벨이 바뀌었을 때 틀린다
    (`experiments/results/cell_sample_counts.json` 은 A 라벨 기준이다).
    실제로 만들어지는 것을 그 자리에서 세면 A 든 B 든 항상 맞는다.

    돌려주는 값: (되돌리는 함수, [(셀 이름, 샘플 수, eol), ...])
    """
    original = data_loader_module.Dataset_original.read_samples_from_one_cell
    records: list[tuple] = []

    def patched(self, file_name):
        out = original(self, file_name)
        curves, _masks, labels, eol, _cj = out
        # eol 이 None 이면 상위가 이 셀을 통째로 버린다 (data_loader.py:342-344)
        n = 0 if (labels is None or eol is None) else len(labels)
        records.append((file_name, n, eol))
        return out

    data_loader_module.Dataset_original.read_samples_from_one_cell = patched

    def restore():
        data_loader_module.Dataset_original.read_samples_from_one_cell = original
    return restore, records


# ------------------------------------------------------------ 라벨 A/B

def make_eol_lookup(labels_dir: Path, stats: dict | None = None):
    """수명 라벨을 디렉터리에서 찾아 주는 함수를 만든다.

    조회 규칙은 상위와 **같게** 둔다 (`data_loader.py:417-431`) — 접두사로
    파일을 고르고, Tongji 는 `--` 를 `-#` 로 바꾼다. 라벨 B 가 그 규칙을
    따르지 않으면 조회가 실패하고 그 셀은 버려진다. **조용히 고치지 않는다** —
    실패는 실패로 드러나야 한다.
    """
    labels_dir = Path(labels_dir)
    st = stats if stats is not None else {}
    st.setdefault("found", 0)
    st.setdefault("missing", 0)
    st.setdefault("no_file", 0)
    cache: dict[str, dict | None] = {}

    def lookup(file_name: str):
        prefix = file_name.split("_")[0]
        if prefix == "MICH":
            fname, key = "total_MICH_labels.json", file_name
        elif prefix.startswith("Tongji"):
            fname, key = "Tongji_labels.json", file_name.replace("--", "-#")
        else:
            fname, key = f"{prefix}_labels.json", file_name
        if fname not in cache:
            p = labels_dir / fname
            cache[fname] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        table = cache[fname]
        if table is None:
            st["no_file"] += 1
            return None
        if key in table:
            st["found"] += 1
            return table[key]
        st["missing"] += 1
        return None

    lookup.labels_dir = labels_dir
    return lookup, st


def install_label_source(data_loader_module, labels_dir: Path):
    """수명 라벨을 다른 디렉터리에서 읽게 한다 (A/B 실험용).

    상위는 `read_cell_data_according_to_prefix` 안에서
    `{root_path}/Life labels/{prefix}_labels.json` 을 직접 엽니다
    (`data_loader.py:417-431`). 그 조회부만 감싼다 — pkl 적재는 그대로 둔다.

    **키 규칙도 상위와 같게 유지한다** (Tongji 는 `--` -> `-#`). B 라벨이 그
    규칙을 따르지 않으면 조회가 실패하고, 그 셀은 라벨없음으로 버려진다.
    그것을 조용히 고치지 않는다 — 실패는 실패로 드러나야 한다.

    돌려주는 값: (되돌리는 함수, 통계 dict)
    """
    labels_dir = Path(labels_dir)
    original = data_loader_module.Dataset_original.read_cell_data_according_to_prefix
    stats = {"found": 0, "missing": 0, "no_file": 0}
    cache: dict[str, dict] = {}

    def patched(self, file_name):
        data, _eol = original(self, file_name)
        prefix = file_name.split("_")[0]
        if prefix == "MICH":
            fname, key = "total_MICH_labels.json", file_name
        elif prefix.startswith("Tongji"):
            fname, key = "Tongji_labels.json", file_name.replace("--", "-#")
        else:
            fname, key = f"{prefix}_labels.json", file_name
        if fname not in cache:
            p = labels_dir / fname
            cache[fname] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        table = cache[fname]
        if table is None:
            stats["no_file"] += 1
            return data, None
        if key in table:
            stats["found"] += 1
            return data, table[key]
        stats["missing"] += 1
        return data, None

    data_loader_module.Dataset_original.read_cell_data_according_to_prefix = patched

    def restore():
        data_loader_module.Dataset_original.read_cell_data_according_to_prefix = original
    return restore, stats
