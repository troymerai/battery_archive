"""
data/extracted/ 의 **모든 셀 pkl 을 하나도 빠뜨리지 않고** 열어 셀 단위
메타데이터를 뽑고, **같은 실행 · 같은 메모리 상의 행 목록**에서 데이터셋 단위
요약표와 보고서용 표 조각까지 파생시킨다.

2026-08-13 개정 (2판)
---------------------
1판은 셀 census 만 만들고, 보고서 본문 표는 저장소에 없는 일회성 스크립트로
따로 계산했습니다. 그 스크립트가 중앙값을 `sorted[n//2]`(상위 중앙값)로
잡았고 이 스크립트는 `np.median`(짝수면 두 가운데 값의 평균)을 써서, 셀 수가
짝수인 서브셋 7곳에서 두 산출물의 숫자가 갈렸습니다. **원인은 두 번 실행한
것이 아니라 같은 자료를 두 코드가 다르게 접은 것입니다.**

그래서 2판은 세 산출물을 **한 함수 호출 사슬 안에서** 만듭니다. 중앙값 규약은
`np.median` 하나로 통일하고, 상위 중앙값이 필요하면 별도 열로 둡니다.

전수성
------
- 루프 전에 대상 파일 수를 세고, 루프 뒤 기록된 행 수와 대조합니다.
  어긋나면 종료 코드 1 입니다.
- 셀 하나를 열고 → 스칼라만 뽑고 → 무거운 배열 참조를 버리고 → 행 1개를
  append + flush 합니다. 원시 배열은 누적하지 않습니다. 최대 상주량은
  가장 큰 pkl 1개(ISU-ILCC_G6C3.pkl, 452 MB)입니다.
- 셀 단위 try/except 이고 실패해도 멈추지 않습니다. **건너뛰지 않습니다.**
- 처리 순서는 sorted() 로 고정되어 있어 중단돼도 어디까지 갔는지 보입니다.

중복 셀 처리 — 두 곳을 같은 논리로 다룹니다
--------------------------------------------
- `total_MICH/` 58개: `data_loader.py:391-393` 의 `merge_MICH()` 가 만든 파생
  디렉터리. **디렉터리째 제외**합니다.
- `Stanford` ∩ `Stanford_2` 동명 38개: `analysis/stanford_overlap_check.py` 가
  38쌍 전부 **바이트 동일**임을 확인했습니다. 행은 남기되 `duplicate_of` 를
  채워 **고유 셀 집계에서 뺍니다.** 정본은 `Stanford/` 쪽입니다 —
  `data_loader.py:404-405` 가 접두사 `Stanford` 를 그 디렉터리로 보냅니다.

사용법:
    .venv-blife/Scripts/python.exe analysis/dataset_metadata_survey.py

산출:
    analysis/out/dataset_cell_census.csv     셀 1행 (전수)
    docs/reports/datasets_metadata.csv       데이터셋 1행 (요약)
    analysis/out/survey_tables.md            보고서용 표 조각
두 CSV 의 첫 줄은 `#` 로 시작하는 실행 식별자 주석입니다. 읽을 때는
`read_csv_with_run_header()` 를 쓰거나 pandas 의 `comment='#'` 를 주십시오.
"""
import csv
import json
import os
import pickle
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACTED = os.path.join(ROOT, "data", "extracted")
CENSUS = os.path.join(ROOT, "analysis", "out", "dataset_cell_census.csv")
SUMMARY = os.path.join(ROOT, "docs", "reports", "datasets_metadata.csv")
TABLES = os.path.join(ROOT, "analysis", "out", "survey_tables.md")
OVERLAP = os.path.join(ROOT, "analysis", "out", "stanford_overlap.csv")

NON_CELL_DIRS = {"Life labels", "READMEs", "seen_unseen_labels"}
DERIVED_DIRS = {"total_MICH"}

# 중복 쌍에서 정본으로 남길 쪽. 나머지 쪽 행이 duplicate_of 를 갖습니다.
DUP_CANONICAL, DUP_SHADOW = "Stanford", "Stanford_2"

LABEL_FILE = {
    "UL_PUR": "UL-PUR",
    "ISU_ILCC": "ISU-ILCC",
    "MICH": "total_MICH",
    "MICH_EXP": "total_MICH",
}

FIELDS = [
    "subset", "file", "cell_id", "duplicate_of",
    "form_factor", "anode_material", "cathode_material", "electrolyte_material",
    "nominal_capacity_in_Ah", "depth_of_charge", "depth_of_discharge",
    "max_voltage_limit_in_V", "min_voltage_limit_in_V",
    "max_current_limit_in_A", "min_current_limit_in_A",
    "already_spent_cycles", "reference", "description",
    "soc_lo", "soc_hi", "soc_span",
    # 정규화 (작업 4)
    "cathode_normalized", "anode_normalized", "cathode_subtype", "polarity_swapped",
    # 부문 (작업 5)
    "sector", "sector_reason",
    "charge_protocol_n", "charge_rate_C_first", "charge_rate_C_uniq",
    "discharge_protocol_n", "discharge_rate_C_first", "discharge_rate_C_uniq",
    # 사이클 축 — 두 정의를 분리합니다 (작업 1-2)
    "n_cycle_records", "cycle_number_first", "cycle_number_last", "cycle_number_max",
    "cycle_number_gaps", "points_per_cycle_median",
    "Qd_first_max_Ah", "Qd_last_max_Ah", "Qc_first_max_Ah",
    "soh_first", "soh_last", "soh_min",
    "eol_repro", "eol_repro_branch", "label_deployed", "label_key", "label_found",
    "has_temperature", "temp_finite", "temp_median_C", "temp_p05_C", "temp_p95_C",
    "has_internal_resistance", "has_Qdlin", "cycle_keys", "file_bytes",
    "error",
]

# ---------------------------------------------------------------------------
# 작업 4 — 화학 정규화. 규칙 전체를 여기 두고 보고서가 이 표를 그대로 싣습니다.
# 키는 pkl 의 원본 문자열 그대로입니다 (2026-08-13 census 에서 전수로 뽑은 16종).
# ---------------------------------------------------------------------------
CATHODE_MAP = {
    "LFP": ("LFP", ""),
    "LiFePO4": ("LFP", ""),
    "LiCoO2": ("LCO", ""),
    "LiCoO2+LiNi0.4Co0.4Mn0.2O2": ("블렌드", "LCO+NMC442"),
    "NMC": ("NMC", ""),
    "NMC111": ("NMC", "NMC111"),
    "NMC_532": ("NMC", "NMC532"),
    "LiNi0.5Co0.2Mn0.3O2": ("NMC", "NMC523"),
    "LiNi0.5Mn0.3Co0.2O2": ("NMC", "NMC532"),
    "NCA": ("NCA", ""),
    "LiNi0.8Co0.15Al0.05O2": ("NCA", "NCA801505"),
    "Li0.86Ni0.86Co0.11Al0.03 O2 (NCA)": ("NCA", "NCA861103"),
    "Li0.84(Ni0.83Co0.11Mn 0.07)O2 (NCM)": ("NMC", "NMC831107"),
    "42 wt.% Li(NiCoMn)O2 blended with 58 wt.% Li(NiCoAl)O2 (NCM+NCA)":
        ("블렌드", "NMC+NCA"),
    "Unknown": ("미상", ""),
    # ZN-coin 은 역할이 뒤바뀌어 기록돼 있습니다 — 아래 극성 검사에서 처리합니다.
    "Zinc": ("__음극물질__", ""),
}
ANODE_MAP = {
    "graphite": ("graphite", ""),
    "Graphite": ("graphite", ""),
    "Graphite/Si": ("graphite-Si", ""),
    "Unknown": ("미상", ""),
    "MnO2": ("__양극물질__", ""),
}
# 역할 판정용 — 지시 §3-1 의 두 목록.
ANODE_ROLE = {"graphite", "graphite-Si", "carbon", "hard carbon", "Li metal", "Zn"}
CATHODE_ROLE = {"LFP", "LCO", "NMC", "NCA", "블렌드", "MnO2"}


def normalize_composition(cathode_raw, anode_raw):
    """(cathode_norm, anode_norm, subtype, swapped) 를 돌려준다.

    pkl 의 두 필드가 화학적으로 반대 자리에 들어 있으면 바로잡고 swapped=1 로
    표시합니다. 원본 문자열 열은 손대지 않습니다.
    """
    c_norm, c_sub = CATHODE_MAP.get(cathode_raw, ("미상", ""))
    a_norm, a_sub = ANODE_MAP.get(anode_raw, ("미상", ""))
    swapped = 0
    # 양극 자리에 음극 물질이, 음극 자리에 양극 물질이 들어 있는 경우
    if c_norm == "__음극물질__" and a_norm == "__양극물질__":
        c_norm, c_sub = "MnO2", ""
        a_norm = "Zn"
        swapped = 1
    else:
        if c_norm == "__음극물질__":
            c_norm, swapped = "미상", 1
        if a_norm == "__양극물질__":
            a_norm, swapped = "미상", 1
    return c_norm, a_norm, c_sub or a_sub, swapped


# ---------------------------------------------------------------------------
# 작업 5 — 셀 단위 부문 분류. 판단 축은 정격용량 + 폼팩터 + 화학 + 프로토콜.
# 순서가 규칙입니다. 위에서부터 처음 걸리는 것을 씁니다.
# 결과는 원칙적으로 [추론] 이고, SDU 만 원논문이 용도를 명시해 [확인] 입니다.
# ---------------------------------------------------------------------------
def classify_sector(subset, form, cap, cath, soc_span):
    f = (form or "").strip().lower()
    try:
        ah = float(cap)
    except (TypeError, ValueError):
        ah = None
    span = None
    try:
        span = float(soc_span)
    except (TypeError, ValueError):
        pass

    if "coin" in f:
        return "실험실 연구 전용", "코인셀 — 상용 제품 대응 없음"
    if cath == "미상":
        return "실험실 연구 전용", "전극 조성이 문서·pkl 모두 미상"
    if "pouch" in f and ah is not None and ah <= 0.5:
        return "실험실 연구 전용", f"{ah:g} Ah 파우치 — 상용 제품 대응 불명확"
    if "502030" in f:
        return "소형 IT기기", "502030 소형 각형 폴리머 — 웨어러블·소형기기 규격"
    if ah is not None and ah >= 20:
        return "전기차 / ESS", f"{ah:g} Ah 대형 셀"
    if subset == "SDU":
        return "ESS (2차 활용)", "원논문이 재사용 배터리 선별을 명시 [확인]"
    if "pouch" in f and ah is not None and ah >= 4.0:
        return "전기차", f"{ah:g} Ah 대형 파우치"
    if cath == "LFP" and ah is not None and ah <= 1.5:
        return "전동공구 / 경형", f"고출력 LFP {ah:g} Ah 소형 셀"
    if cath in ("LCO", "블렌드") and ah is not None and ah < 3.0 and cath == "LCO":
        return "소형 IT기기", f"LCO {ah:g} Ah — 휴대기기 셀 규격"
    if cath == "블렌드" and ah is not None and ah < 2.0:
        return "소형 IT기기", f"LCO 계열 블렌드 {ah:g} Ah"
    if cath == "블렌드" and ah is not None and 2.0 <= ah < 3.0 and subset == "HNEI":
        return "소형 IT기기", f"LCO+NMC442 {ah:g} Ah 18650 — 노트북 팩 셀"
    if cath == "NMC" and span is not None and span < 0.9 and ah is not None and ah < 2.5:
        return "경형 이동수단", f"NMC {ah:g} Ah · SOC 부분 순환(span {span:g})"
    if cath in ("NCA", "블렌드") and ah is not None and ah >= 2.5:
        return "전기차", f"{cath} {ah:g} Ah — EV 팩 셀 규격"
    if cath == "NMC" and ah is not None and ah >= 3.0:
        return "전기차", f"NMC {ah:g} Ah — EV 팩 셀 규격"
    if cath == "NMC" and ah is not None and 1.5 <= ah < 3.0:
        return "소형 IT기기", f"NMC {ah:g} Ah — 범용 소형 팩 규격"
    return "미분류", f"규칙에 걸리지 않음 (cath={cath}, Ah={cap}, form={form})"


# ---------------------------------------------------------------------------
def run_identifier():
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=15).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                               capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception:
        sha, dirty = "미상", ""
    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "git_commit": (sha or "미상")[:40],
        "git_dirty": bool(dirty),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "script": "analysis/dataset_metadata_survey.py",
    }


def run_header_line(run):
    return "# " + json.dumps(run, ensure_ascii=False, sort_keys=True)


def read_csv_with_run_header(path):
    """첫 줄의 `#` 실행 식별자를 건너뛰고 (run, rows) 를 돌려준다."""
    with open(path, encoding="utf-8", newline="") as fh:
        first = fh.readline()
        if first.startswith("#"):
            run = json.loads(first[1:].strip())
        else:
            run, fh = None, open(path, encoding="utf-8", newline="")
        return run, list(csv.DictReader(fh))


def _maxf(seq):
    if seq is None:
        return None
    a = np.asarray(seq, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.max()) if a.size else None


def _prot(p):
    if not isinstance(p, list) or not p:
        return 0, None, ""
    rates = [s.get("rate_in_C") for s in p if isinstance(s, dict)]
    first = rates[0] if rates else None

    def fmt(r):
        return f"{r:g}" if isinstance(r, (int, float)) else str(r)

    uniq = sorted({fmt(r) for r in rates if r is not None and r != ""})
    return len(p), first, "|".join(uniq)


def load_labels():
    out = {}
    d = os.path.join(EXTRACTED, "Life labels")
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if fn.endswith("_labels.json"):
            with open(os.path.join(d, fn), encoding="utf-8") as fh:
                out[fn[: -len("_labels.json")]] = json.load(fh)
    return out


def load_duplicates():
    """stanford_overlap_check.py 결과에서 바이트 동일 쌍의 파일명을 읽는다."""
    dup = {}
    if not os.path.exists(OVERLAP):
        print(f"[census] 경고: {OVERLAP} 없음 — 중복 표시를 채우지 못합니다.",
              file=sys.stderr)
        return dup
    with open(OVERLAP, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("bytes_equal") == "1":
                dup[r["file"]] = f"{DUP_CANONICAL}/{r['file']}"
    return dup


def label_lookup(labels, subset, file_name):
    name = LABEL_FILE.get(subset, subset)
    table = labels.get(name)
    key = file_name.replace("--", "-#") if subset == "Tongji" else file_name
    if table is None:
        return key, None, False
    return (key, table[key], True) if key in table else (key, None, False)


def scan_cell(path, subset, file_name, labels, dup):
    row = {k: "" for k in FIELDS}
    row["subset"], row["file"] = subset, file_name
    row["file_bytes"] = os.path.getsize(path)
    if subset == DUP_SHADOW and file_name in dup:
        row["duplicate_of"] = dup[file_name]

    with open(path, "rb") as fh:
        d = pickle.load(fh)

    row["cell_id"] = d.get("cell_id")
    for k in ("form_factor", "anode_material", "cathode_material",
              "electrolyte_material", "nominal_capacity_in_Ah",
              "depth_of_charge", "depth_of_discharge",
              "max_voltage_limit_in_V", "min_voltage_limit_in_V",
              "max_current_limit_in_A", "min_current_limit_in_A",
              "already_spent_cycles", "reference", "description"):
        row[k] = d.get(k)

    soc = d.get("SOC_interval") or [None, None]
    row["soc_lo"], row["soc_hi"] = soc[0], soc[1]
    span = (soc[1] - soc[0]) if (soc[0] is not None and soc[1] is not None) else None
    row["soc_span"] = span

    (row["cathode_normalized"], row["anode_normalized"],
     row["cathode_subtype"], row["polarity_swapped"]) = normalize_composition(
        d.get("cathode_material"), d.get("anode_material"))
    row["sector"], row["sector_reason"] = classify_sector(
        subset, d.get("form_factor"), d.get("nominal_capacity_in_Ah"),
        row["cathode_normalized"], span)

    (row["charge_protocol_n"], row["charge_rate_C_first"],
     row["charge_rate_C_uniq"]) = _prot(d.get("charge_protocol"))
    (row["discharge_protocol_n"], row["discharge_rate_C_first"],
     row["discharge_rate_C_uniq"]) = _prot(d.get("discharge_protocol"))

    cyc = d.get("cycle_data") or []
    row["n_cycle_records"] = len(cyc)
    if not cyc:
        key, val, found = label_lookup(labels, subset, file_name)
        row["label_key"], row["label_deployed"], row["label_found"] = key, val, int(found)
        return row

    row["cycle_keys"] = "|".join(sorted(cyc[0].keys()))
    nums, lens, temps = [], [], []
    has_temp = has_ir = has_qdlin = False

    nominal = d.get("nominal_capacity_in_Ah")
    if file_name.startswith("RWTH"):
        nominal = 1.85
    elif file_name.startswith("SNL_18650_NCA_25C_20-80"):
        nominal = 3.2
    denom = (nominal * (span if span else 1)) if nominal else None

    sohs = []
    for i, c in enumerate(cyc):
        if not isinstance(c, dict):
            continue
        n = c.get("cycle_number")
        if n is not None:
            nums.append(n)
        v = c.get("voltage_in_V")
        if v is not None:
            lens.append(len(v))
        t = c.get("temperature_in_C")
        if t is not None:
            has_temp = True
            a = np.asarray(t, dtype=float)
            a = a[np.isfinite(a)]
            if a.size:
                temps.append(float(np.median(a)))
        if c.get("internal_resistance_in_ohm") is not None:
            has_ir = True
        if c.get("Qdlin") is not None:
            has_qdlin = True

        qd = _maxf(c.get("discharge_capacity_in_Ah"))
        if i == 0:
            row["Qd_first_max_Ah"] = qd
            row["Qc_first_max_Ah"] = _maxf(c.get("charge_capacity_in_Ah"))
        if i == len(cyc) - 1:
            row["Qd_last_max_Ah"] = qd
        sohs.append(qd / denom if (qd is not None and denom) else np.nan)

    del cyc, d

    if nums:
        row["cycle_number_first"] = nums[0]
        row["cycle_number_last"] = nums[-1]
        try:
            ints = [int(x) for x in nums]
            lo, hi = min(ints), max(ints)
            row["cycle_number_max"] = hi
            row["cycle_number_gaps"] = (hi - lo + 1) - len(set(ints))
        except (TypeError, ValueError):
            row["cycle_number_max"] = ""
            row["cycle_number_gaps"] = ""
    if lens:
        row["points_per_cycle_median"] = float(np.median(lens))
    row["has_temperature"] = int(has_temp)
    row["temp_finite"] = int(bool(temps))
    if temps:
        ta = np.asarray(temps)
        row["temp_median_C"] = float(np.median(ta))
        row["temp_p05_C"] = float(np.percentile(ta, 5))
        row["temp_p95_C"] = float(np.percentile(ta, 95))
    row["has_internal_resistance"] = int(has_ir)
    row["has_Qdlin"] = int(has_qdlin)

    sa = np.asarray(sohs, dtype=float)
    fin = sa[np.isfinite(sa)]
    if fin.size:
        row["soh_first"] = float(sa[0]) if np.isfinite(sa[0]) else ""
        row["soh_last"] = float(sa[-1]) if np.isfinite(sa[-1]) else ""
        row["soh_min"] = float(fin.min())
        last = sa[-1]
        if subset == "CALB":
            row["eol_repro_branch"] = "CALB_external_excel"
        elif not np.isfinite(last):
            row["eol_repro_branch"] = "soh_last_not_finite"
        elif last >= 0.825:
            row["eol_repro_branch"] = "abandoned"
        elif last > 0.8:
            row["eol_repro_branch"] = "extrapolated"
        else:
            row["eol_repro_branch"] = "first_crossing"
            hit = np.where(sa <= 0.80)[0]
            if hit.size:
                row["eol_repro"] = int(hit[0]) + 1

    key, val, found = label_lookup(labels, subset, file_name)
    row["label_key"], row["label_deployed"], row["label_found"] = key, val, int(found)
    return row


def main():
    run = run_identifier()
    labels, dup = load_labels(), load_duplicates()

    subsets = sorted(
        n for n in os.listdir(EXTRACTED)
        if os.path.isdir(os.path.join(EXTRACTED, n))
        and n not in NON_CELL_DIRS and n not in DERIVED_DIRS
    )
    targets = []
    for sub in subsets:
        for fn in sorted(os.listdir(os.path.join(EXTRACTED, sub))):
            if fn.endswith(".pkl"):
                targets.append((sub, fn))
    expected = len(targets)
    t0 = time.monotonic()
    print(f"[census] 대상 셀 {expected}개 · 서브셋 {len(subsets)}개", file=sys.stderr, flush=True)
    print(f"[census] 중복(바이트 동일) 표시 대상 {len(dup)}개", file=sys.stderr, flush=True)

    os.makedirs(os.path.dirname(CENSUS), exist_ok=True)
    rows, failed, written = [], [], 0
    with open(CENSUS, "w", newline="", encoding="utf-8") as fh:
        fh.write(run_header_line(run) + "\n")
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for i, (sub, fn) in enumerate(targets):
            path = os.path.join(EXTRACTED, sub, fn)
            try:
                row = scan_cell(path, sub, fn, labels, dup)
            except Exception as e:
                row = {k: "" for k in FIELDS}
                row["subset"], row["file"] = sub, fn
                row["error"] = f"{type(e).__name__}: {e}"[:300]
                failed.append(f"{sub}/{fn}: {row['error']}")
            w.writerow(row)
            fh.flush()
            rows.append(row)          # 요약표는 이 목록에서만 파생시킵니다
            written += 1
            if i % 50 == 0:
                print(f"  {i}/{expected} {sub}", file=sys.stderr, flush=True)

    elapsed = time.monotonic() - t0
    print(f"[census] 기록 {written}행 / 대상 {expected}개", file=sys.stderr)
    print(f"[census] 소요 {elapsed / 60:.1f}분", file=sys.stderr)
    print(f"[census] 읽기 실패 {len(failed)}건", file=sys.stderr)
    for f in failed:
        print(f"   ! {f}", file=sys.stderr)

    rollup(rows, run)
    write_tables(rows, run, elapsed, expected, written, failed)

    if written != expected:
        print("[census] 대조 불일치 — 보고서를 완료로 두지 마십시오.", file=sys.stderr)
        return 1
    print("[census] 대조 일치.", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _nums(rs, col):
    a = [_f(r[col]) for r in rs]
    a = np.asarray([x for x in a if x is not None], dtype=float)
    return a[np.isfinite(a)]


def _uniq(vals, cap=6):
    s = sorted({str(v) for v in vals if v not in ("", None, "None")})
    return f"<{len(s)}종>" if len(s) > cap else "|".join(s)


def unique_rows(rows):
    """고유 셀만 — 바이트 동일 중복본을 뺀다."""
    return [r for r in rows if not r["duplicate_of"]]


def rollup(rows, run):
    by = {}
    for r in rows:
        by.setdefault(r["subset"], []).append(r)

    cols = ["subset", "n_files", "n_unique_cells", "n_duplicate_files",
            "n_read_ok", "n_read_fail", "total_bytes", "total_GB_decimal",
            "form_factor", "anode_material", "cathode_material",
            "cathode_normalized", "anode_normalized", "cathode_subtype",
            "polarity_swapped_cells", "sector",
            "nominal_capacity_in_Ah", "max_voltage_limit_in_V", "min_voltage_limit_in_V",
            "soc_interval", "charge_rate_C", "discharge_rate_C",
            "charge_protocol_multi_step_cells",
            "n_cycle_records_min", "n_cycle_records_median", "n_cycle_records_median_upper",
            "n_cycle_records_max", "n_cycle_records_sum",
            "cycle_number_max_median", "cells_records_ne_cyclemax",
            "cycle_number_first", "cells_with_gaps",
            "soh_first_min", "soh_first_max", "soh_last_min", "soh_last_max",
            "eol_branch_counts", "labels_deployed", "cells_without_label",
            "temp_array_cells", "temp_finite_cells",
            "has_internal_resistance_cells", "has_Qdlin_cells",
            "points_per_cycle_median"]

    os.makedirs(os.path.dirname(SUMMARY), exist_ok=True)
    with open(SUMMARY, "w", newline="", encoding="utf-8") as fh:
        fh.write(run_header_line(run) + "\n")
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for sub in sorted(by):
            rs = by[sub]
            ok = [r for r in rs if not r["error"]]
            uq = [r for r in ok if not r["duplicate_of"]]
            o = {c: "" for c in cols}
            o["subset"] = sub
            o["n_files"] = len(rs)
            o["n_unique_cells"] = len(unique_rows(rs))
            o["n_duplicate_files"] = sum(1 for r in rs if r["duplicate_of"])
            o["n_read_ok"], o["n_read_fail"] = len(ok), len(rs) - len(ok)
            tb = int(sum(_f(r["file_bytes"]) or 0 for r in rs))
            o["total_bytes"] = tb
            o["total_GB_decimal"] = round(tb / 1e9, 2)
            for c in ("form_factor", "anode_material", "cathode_material",
                      "cathode_normalized", "anode_normalized", "cathode_subtype",
                      "sector", "nominal_capacity_in_Ah", "max_voltage_limit_in_V",
                      "min_voltage_limit_in_V", "cycle_number_first"):
                o[c] = _uniq(r[c] for r in ok)
            o["polarity_swapped_cells"] = sum(1 for r in ok if r["polarity_swapped"] == 1
                                              or r["polarity_swapped"] == "1")
            o["soc_interval"] = _uniq(f"[{r['soc_lo']},{r['soc_hi']}]" for r in ok)
            o["charge_rate_C"] = _uniq(r["charge_rate_C_uniq"] for r in ok)
            o["discharge_rate_C"] = _uniq(r["discharge_rate_C_uniq"] for r in ok)
            o["charge_protocol_multi_step_cells"] = sum(
                1 for r in ok if str(r["charge_protocol_n"]) not in ("", "0", "1"))
            n = _nums(uq, "n_cycle_records")
            if n.size:
                sn = np.sort(n)
                o["n_cycle_records_min"] = int(sn.min())
                o["n_cycle_records_median"] = float(np.median(sn))
                o["n_cycle_records_median_upper"] = int(sn[len(sn) // 2])
                o["n_cycle_records_max"] = int(sn.max())
                o["n_cycle_records_sum"] = int(sn.sum())
            cm = _nums(uq, "cycle_number_max")
            if cm.size:
                o["cycle_number_max_median"] = float(np.median(cm))
            o["cells_records_ne_cyclemax"] = sum(
                1 for r in uq if r["cycle_number_max"] not in ("", None)
                and _f(r["n_cycle_records"]) != _f(r["cycle_number_max"]))
            o["cells_with_gaps"] = sum(1 for r in uq
                                       if str(r["cycle_number_gaps"]) not in ("", "0"))
            for src, lo, hi in (("soh_first", "soh_first_min", "soh_first_max"),
                                ("soh_last", "soh_last_min", "soh_last_max")):
                a = _nums(ok, src)
                if a.size:
                    o[lo], o[hi] = round(float(a.min()), 4), round(float(a.max()), 4)
            br = {}
            for r in ok:
                br[r["eol_repro_branch"]] = br.get(r["eol_repro_branch"], 0) + 1
            o["eol_branch_counts"] = "|".join(f"{k}={v}" for k, v in sorted(br.items()))
            o["labels_deployed"] = sum(1 for r in ok if str(r["label_found"]) == "1")
            o["cells_without_label"] = sum(1 for r in ok if str(r["label_found"]) != "1")
            o["temp_array_cells"] = sum(1 for r in ok if str(r["has_temperature"]) == "1")
            o["temp_finite_cells"] = sum(1 for r in ok if str(r["temp_finite"]) == "1")
            o["has_internal_resistance_cells"] = sum(
                1 for r in ok if str(r["has_internal_resistance"]) == "1")
            o["has_Qdlin_cells"] = sum(1 for r in ok if str(r["has_Qdlin"]) == "1")
            p = _nums(ok, "points_per_cycle_median")
            if p.size:
                o["points_per_cycle_median"] = float(np.median(p))
            w.writerow(o)
    print(f"[census] 요약표 {SUMMARY}", file=sys.stderr)


def write_tables(rows, run, elapsed, expected, written, failed):
    """보고서 본문에 그대로 실을 표 조각. **census 와 같은 행 목록에서 만듭니다.**"""
    import collections
    by = collections.defaultdict(list)
    for r in rows:
        by[r["subset"]].append(r)
    uq = unique_rows(rows)
    out = []
    A = out.append

    A(f"<!-- {run_header_line(run)} -->")
    A(f"실행 소요 {elapsed / 60:.1f}분 · 대상 {expected} · 기록 {written} · 실패 {len(failed)}\n")

    A("## T0. 전수 대조\n")
    A("| 항목 | 값 |")
    A("|---|---:|")
    A(f"| 대상 파일(pkl) | {expected} |")
    A(f"| 기록 행 | {written} |")
    A(f"| 읽기 실패 | {len(failed)} |")
    A(f"| 바이트 동일 중복본 | {sum(1 for r in rows if r['duplicate_of'])} |")
    A(f"| **고유 셀** | **{len(uq)}** |")
    A(f"| 소요(분) | {elapsed / 60:.1f} |\n")

    A("## T1. 사양\n")
    A("| subset | 파일 | 고유셀 | form_factor | anode | cathode | 정격 Ah | Vmax | Vmin | SOC구간 |")
    A("|---|---:|---:|---|---|---|---|---|---|---|")
    for s in sorted(by):
        rs = [r for r in by[s] if not r["error"]]
        u = unique_rows(rs)
        A(f"| {s} | {len(by[s])} | {len(u)} | {_uniq(r['form_factor'] for r in rs)} "
          f"| {_uniq(r['anode_material'] for r in rs)} | {_uniq(r['cathode_material'] for r in rs)} "
          f"| {_uniq(r['nominal_capacity_in_Ah'] for r in rs)} "
          f"| {_uniq(r['max_voltage_limit_in_V'] for r in rs)} "
          f"| {_uniq(r['min_voltage_limit_in_V'] for r in rs)} "
          f"| {_uniq('[' + str(r['soc_lo']) + ',' + str(r['soc_hi']) + ']' for r in rs)} |")

    A("\n## T2. 사이클 축 — 두 정의\n")
    A("| subset | 고유셀 | n_cycle_records min/중앙/max | 중앙(상위) | cycle_number_max 중앙 | 두 값 다른 셀 | 첫 번호 | 결번 셀 |")
    A("|---|---:|---|---:|---:|---:|---|---:|")
    for s in sorted(by):
        u = unique_rows([r for r in by[s] if not r["error"]])
        n = np.sort(_nums(u, "n_cycle_records"))
        cm = _nums(u, "cycle_number_max")
        ne = sum(1 for r in u if r["cycle_number_max"] not in ("", None)
                 and _f(r["n_cycle_records"]) != _f(r["cycle_number_max"]))
        gaps = sum(1 for r in u if str(r["cycle_number_gaps"]) not in ("", "0"))
        A(f"| {s} | {len(u)} | {int(n.min())} / {np.median(n):g} / {int(n.max())} "
          f"| {int(n[len(n) // 2])} | {np.median(cm):g} | {ne} "
          f"| {_uniq(r['cycle_number_first'] for r in u)} | {gaps} |")

    A("\n## T3. 온도 3단계\n")
    A("| subset | 고유셀 | 배열 있음 | 유한값 있음 | 전부 None |")
    A("|---|---:|---:|---:|---:|")
    ta = tf = 0
    for s in sorted(by):
        u = unique_rows([r for r in by[s] if not r["error"]])
        a = sum(1 for r in u if str(r["has_temperature"]) == "1")
        f2 = sum(1 for r in u if str(r["temp_finite"]) == "1")
        ta += a
        tf += f2
        A(f"| {s} | {len(u)} | {a} | {f2} | {len(u) - a} |")
    A(f"| **합** | **{len(uq)}** | **{ta}** | **{tf}** | **{len(uq) - ta}** |")

    A("\n## T4. 화학 정규화 결과 (고유 셀)\n")
    A("| cathode_normalized | subtype | 셀 수 | 서브셋 |")
    A("|---|---|---:|---|")
    agg = collections.defaultdict(list)
    for r in uq:
        if not r["error"]:
            agg[(r["cathode_normalized"], r["cathode_subtype"])].append(r["subset"])
    for k in sorted(agg):
        c = collections.Counter(agg[k])
        A(f"| {k[0]} | {k[1] or '—'} | {len(agg[k])} | "
          f"{' '.join(f'{a}:{b}' for a, b in sorted(c.items()))} |")

    A("\n## T5. 부문 — 셀 단위 (고유 셀)\n")
    A("| 부문 | 셀 수 | 서브셋 분포 |")
    A("|---|---:|---|")
    sec = collections.defaultdict(list)
    for r in uq:
        if not r["error"]:
            sec[r["sector"]].append(r["subset"])
    for k in sorted(sec):
        c = collections.Counter(sec[k])
        A(f"| {k} | {len(sec[k])} | {' '.join(f'{a}:{b}' for a, b in sorted(c.items()))} |")

    A("\n## T6. 서브셋 안에서 부문이 갈리는 곳\n")
    A("| subset | 부문 분포 |")
    A("|---|---|")
    for s in sorted(by):
        u = [r for r in unique_rows(by[s]) if not r["error"]]
        c = collections.Counter(r["sector"] for r in u)
        if len(c) > 1:
            A(f"| {s} | {' · '.join(f'{a} {b}셀' for a, b in sorted(c.items()))} |")

    A("\n## T7. 화학 × 부문 교차표 (고유 셀)\n")
    chems = sorted({r["cathode_normalized"] for r in uq if not r["error"]})
    secs = sorted({r["sector"] for r in uq if not r["error"]})
    A("| 화학 \\ 부문 | " + " | ".join(secs) + " | 합 |")
    A("|---|" + "---:|" * (len(secs) + 1))
    for ch in chems:
        cells = [r for r in uq if not r["error"] and r["cathode_normalized"] == ch]
        counts = [sum(1 for r in cells if r["sector"] == sc) for sc in secs]
        A(f"| {ch} | " + " | ".join(str(x) for x in counts) + f" | {len(cells)} |")

    A("\n## T8. 용량 — 단위 통일 (십진 GB)\n")
    A("| 대상 | 파일 수 | 바이트 | GB(십진) |")
    A("|---|---:|---:|---:|")
    tot = int(sum(_f(r["file_bytes"]) or 0 for r in rows))
    utot = int(sum(_f(r["file_bytes"]) or 0 for r in uq))
    A(f"| 18개 서브셋 전 파일 | {len(rows)} | {tot} | {tot / 1e9:.2f} |")
    A(f"| 그중 고유 셀 | {len(uq)} | {utot} | {utot / 1e9:.2f} |")

    os.makedirs(os.path.dirname(TABLES), exist_ok=True)
    with open(TABLES, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"[census] 표 조각 {TABLES}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
