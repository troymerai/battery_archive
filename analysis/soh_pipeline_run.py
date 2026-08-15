"""SOH 궤적 생성 — upstream/BatteryMFormer 파이프라인을 고치지 않고 그대로 부른다.

무엇을 하는가
--------------
`upstream/BatteryMFormer/process_scripts/run_soh_pipeline.sh` 의 Step 1·2·3·5 를
파이썬에서 순서대로 부르고, 각 단계의 표준출력을 그대로 남기면서 셀 단위
제외 사유를 표로 뽑는다.

**Step 4(time_normalization.py)는 부르지 않는다.** 그 스크립트는
`cleaned_data` 를 제자리에서 덮어쓴다(`time_normalization.py:367,418`).
이 저장소에서 `data/extracted/` 는 읽기 전용이고, BatteryLife v11 은 이미
시간 정규화가 적용된 판이다(`assets/Version10_Update_Details.md` 4항).

산출
-----
    data/soh_v11/SOH/<subset>/*.pkl            Step 1 산출 (외삽 꼬리 포함, 평활 전)
    data/soh_v11/CALB_from_pkl/*.pkl           Step 1 의 CALB(pkl 경로) 사본.
                                               Step 1b 가 엑셀 경로로 덮어쓰기 전 보존
    data/soh_v11/processed_SOH/<subset>/*.pkl  Step 2·3·5 산출 (PCHIP 평활 포함)
    data/soh_v11/logs/<step>.log               각 호출의 표준출력·표준오류 원문
    data/soh_v11/soh_generation_log.csv        서브셋별 소요·입출력 셀 수
    data/soh_v11/soh_skipped_cells.csv         제외된 셀과 사유(원문 + 분류)

실행
-----
    저장소 루트에서
    .venv-blife/Scripts/python.exe analysis/soh_pipeline_run.py
"""

import csv
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BMF = ROOT / 'upstream' / 'BatteryMFormer'
SCRIPTS = BMF / 'process_scripts'
CLEANED = ROOT / 'data' / 'extracted'

OUT_ROOT = ROOT / 'data' / 'soh_v11'
SOH_DIR = OUT_ROOT / 'SOH'
PROC_DIR = OUT_ROOT / 'processed_SOH'
CALB_SNAPSHOT = OUT_ROOT / 'CALB_from_pkl'
LOG_DIR = OUT_ROOT / 'logs'

# generate_soh.py 의 기본 목록 17개. 저장소의 배포 서브셋은 18개이고
# SDU 하나가 상위 기본 목록 밖에 있다 — 뒤에 따로 붙여 별도로 표시한다.
UPSTREAM_DEFAULT = [
    'CALCE', 'HNEI', 'MATR', 'UL_PUR', 'SNL', 'MICH_EXP', 'MICH',
    'RWTH', 'HUST', 'Tongji', 'Stanford', 'XJTU', 'ISU_ILCC',
    'NA-ion', 'CALB', 'ZN-coin', 'Stanford_2',
]
EXTRA = ['SDU']

# 제외 사유 원문 -> 분류. generate_soh.py 의 return 문 5개와 1:1 대응한다.
REASON_RULES = [
    (re.compile(r'^In EXCLUDED_CELLS list$'), 'EXCLUDED_CELLS'),
    (re.compile(r'^No SOH data generated'), 'EMPTY_CYCLE_DATA'),
    (re.compile(r'^Final SOH .* > threshold'), 'FILTER_THRESHOLD'),
    (re.compile(r'^Slope is non-negative'), 'SLOPE_NON_NEGATIVE'),
    (re.compile(r'^Slope too small'), 'SLOPE_BELOW_MIN'),
]


def classify(reason):
    for pat, name in REASON_RULES:
        if pat.search(reason):
            return name
    return 'UNCLASSIFIED'


def run(tag, argv, cwd=BMF):
    """자식 프로세스를 부르고 stdout+stderr 를 로그로 남긴 뒤 stdout 을 돌려준다."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run(
        argv, cwd=str(cwd), capture_output=True,
        encoding='utf-8', errors='replace',
    )
    elapsed = time.time() - t0
    (LOG_DIR / f'{tag}.log').write_text(
        f'# argv: {argv}\n# cwd: {cwd}\n# returncode: {proc.returncode}\n'
        f'# elapsed_s: {elapsed:.1f}\n\n===== STDOUT =====\n{proc.stdout}\n'
        f'===== STDERR =====\n{proc.stderr}\n',
        encoding='utf-8',
    )
    print(f'  [{tag}] rc={proc.returncode} {elapsed:.1f}s', flush=True)
    return proc, elapsed


def parse_skipped(stdout, dataset):
    """generate_soh.py 의 SKIPPED CELLS REPORT 블록에서 (셀, 사유) 를 뽑는다."""
    rows = []
    lines = stdout.splitlines()
    inside = False
    for line in lines:
        if 'SKIPPED CELLS REPORT:' in line:
            inside = True
            continue
        if inside:
            if line.startswith('====') or line.startswith('----'):
                if line.startswith('===='):
                    inside = False
                continue
            if line.startswith('Cell Name'):
                continue
            if '|' not in line:
                continue
            name, _, reason = line.partition('|')
            name, reason = name.strip(), reason.strip()
            if not name:
                continue
            rows.append({'subset': dataset, 'cell': name, 'reason': reason,
                         'reason_class': classify(reason)})
    return rows


def count_pkl(path):
    p = Path(path)
    return len(list(p.glob('*.pkl'))) if p.is_dir() else 0


def main():
    if not CLEANED.is_dir():
        sys.exit(f'cleaned_data 없음: {CLEANED}')
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    SOH_DIR.mkdir(parents=True, exist_ok=True)

    gen_log = []
    skipped = []

    # ---------------- Step 1: generate_soh.py --------------------------------
    print('[Step 1] generate_soh.py')
    for ds in UPSTREAM_DEFAULT + EXTRA:
        src = CLEANED / ds
        if not src.is_dir():
            gen_log.append({'step': 'step1', 'subset': ds, 'in_scope_of_upstream_default': ds in UPSTREAM_DEFAULT,
                            'input_cells': 0, 'output_cells': 0, 'skipped': 0,
                            'elapsed_s': 0.0, 'returncode': '', 'status': 'INPUT_DIR_MISSING'})
            continue
        n_in = count_pkl(src)
        proc, elapsed = run(
            f'step1_{ds}',
            [sys.executable, str(SCRIPTS / 'generate_soh.py'),
             '--cleaned_data_root', str(CLEANED),
             '--output_root', str(SOH_DIR),
             '--datasets', ds,
             '--num_workers', '1'],
        )
        rows = parse_skipped(proc.stdout, ds)
        skipped.extend(rows)
        gen_log.append({
            'step': 'step1', 'subset': ds,
            'in_scope_of_upstream_default': ds in UPSTREAM_DEFAULT,
            'input_cells': n_in, 'output_cells': count_pkl(SOH_DIR / ds),
            'skipped': len(rows), 'elapsed_s': round(elapsed, 1),
            'returncode': proc.returncode,
            'status': 'OK' if proc.returncode == 0 else 'FAILED',
        })

    # ------- Step 1b: CALB 엑셀 경로. 덮어쓰기 전에 pkl 경로 산출을 보존한다 ----
    print('[Step 1b] generate_CALB_soh.py')
    if (SOH_DIR / 'CALB').is_dir():
        if CALB_SNAPSHOT.exists():
            shutil.rmtree(CALB_SNAPSHOT)
        shutil.copytree(SOH_DIR / 'CALB', CALB_SNAPSHOT)
    n_before = count_pkl(SOH_DIR / 'CALB')
    proc, elapsed = run(
        'step1b_CALB_excel',
        [sys.executable, str(SCRIPTS / 'generate_CALB_soh.py'),
         '--raw_data_file_path', str(SCRIPTS / 'overall_CALB_cycling_data.xlsx'),
         '--output_path', str(SOH_DIR)],
    )
    gen_log.append({
        'step': 'step1b', 'subset': 'CALB(excel)', 'in_scope_of_upstream_default': True,
        'input_cells': n_before, 'output_cells': count_pkl(SOH_DIR / 'CALB'),
        'skipped': '', 'elapsed_s': round(elapsed, 1), 'returncode': proc.returncode,
        'status': 'OK' if proc.returncode == 0 else 'FAILED',
    })

    # ---------------- Step 2: 서브셋별 preprocess + 일반 preprocess -----------
    print('[Step 2] preprocess')
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    specific = [
        ('HNEI', 'preprocess_HNEI.py'), ('MICH', 'preprocess_MICH.py'),
        ('MICH_EXP', 'preprocess_MICH_EXP.py'), ('RWTH', 'preprocess_RWTH.py'),
        ('SNL', 'preprocess_SNL.py'), ('Tongji', 'preprocess_Tongji.py'),
    ]
    for ds, script in specific:
        proc, elapsed = run(
            f'step2_{ds}',
            [sys.executable, str(SCRIPTS / script),
             '--input', str(SOH_DIR / ds), '--output', str(PROC_DIR / ds)],
        )
        gen_log.append({'step': 'step2', 'subset': ds, 'in_scope_of_upstream_default': True,
                        'input_cells': count_pkl(SOH_DIR / ds),
                        'output_cells': count_pkl(PROC_DIR / ds), 'skipped': '',
                        'elapsed_s': round(elapsed, 1), 'returncode': proc.returncode,
                        'status': 'OK' if proc.returncode == 0 else 'FAILED'})

    proc, elapsed = run(
        'step2_ISU_ILCC',
        [sys.executable, str(SCRIPTS / 'preprocess_ISU_ILCC.py'),
         '--input', str(SOH_DIR / 'ISU_ILCC'), '--output', str(PROC_DIR / 'ISU_ILCC'),
         '--rpt_json', str(SCRIPTS / 'all_rpt_positions.json'), '--workers', '1'],
    )
    gen_log.append({'step': 'step2', 'subset': 'ISU_ILCC', 'in_scope_of_upstream_default': True,
                    'input_cells': count_pkl(SOH_DIR / 'ISU_ILCC'),
                    'output_cells': count_pkl(PROC_DIR / 'ISU_ILCC'), 'skipped': '',
                    'elapsed_s': round(elapsed, 1), 'returncode': proc.returncode,
                    'status': 'OK' if proc.returncode == 0 else 'FAILED'})

    proc, elapsed = run(
        'step2_general',
        [sys.executable, str(SCRIPTS / 'preprocess.py'),
         '--base_input', str(SOH_DIR), '--base_output', str(PROC_DIR)],
    )
    gen_log.append({'step': 'step2', 'subset': '(general preprocess.py)',
                    'in_scope_of_upstream_default': True, 'input_cells': '',
                    'output_cells': '', 'skipped': '', 'elapsed_s': round(elapsed, 1),
                    'returncode': proc.returncode,
                    'status': 'OK' if proc.returncode == 0 else 'FAILED'})

    # ---------------- Step 3: total_MICH 병합 --------------------------------
    print('[Step 3] merge total_MICH')
    target = PROC_DIR / 'total_MICH'
    target.mkdir(parents=True, exist_ok=True)
    for ds in ('MICH', 'MICH_EXP'):
        src = PROC_DIR / ds
        if src.is_dir():
            for f in src.glob('*.pkl'):
                shutil.copy2(f, target / f.name)
    gen_log.append({'step': 'step3', 'subset': 'total_MICH', 'in_scope_of_upstream_default': True,
                    'input_cells': count_pkl(PROC_DIR / 'MICH') + count_pkl(PROC_DIR / 'MICH_EXP'),
                    'output_cells': count_pkl(target), 'skipped': '', 'elapsed_s': 0.0,
                    'returncode': 0, 'status': 'OK'})

    # ---------------- Step 4: 건너뜀 (원시 데이터 제자리 수정) ----------------
    gen_log.append({'step': 'step4', 'subset': '(time_normalization.py)',
                    'in_scope_of_upstream_default': True, 'input_cells': '', 'output_cells': '',
                    'skipped': '', 'elapsed_s': 0.0, 'returncode': '',
                    'status': 'SKIPPED_WOULD_MODIFY_RAW_DATA'})

    # ---------------- Step 5: Tongji 파일명 정리 -----------------------------
    print('[Step 5] rename Tongji')
    proc, elapsed = run(
        'step5_rename_Tongji',
        [sys.executable, str(SCRIPTS / 'rename_Tongji_cells.py'),
         '--output_dir', str(PROC_DIR)],
    )
    gen_log.append({'step': 'step5', 'subset': 'Tongji', 'in_scope_of_upstream_default': True,
                    'input_cells': '', 'output_cells': count_pkl(PROC_DIR / 'Tongji'),
                    'skipped': '', 'elapsed_s': round(elapsed, 1),
                    'returncode': proc.returncode,
                    'status': 'OK' if proc.returncode == 0 else 'FAILED'})

    # ---------------- 표 두 개 기록 ------------------------------------------
    with open(OUT_ROOT / 'soh_generation_log.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(gen_log[0].keys()))
        w.writeheader()
        w.writerows(gen_log)

    with open(OUT_ROOT / 'soh_skipped_cells.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['subset', 'cell', 'reason', 'reason_class'])
        w.writeheader()
        w.writerows(skipped)

    print(f'\n제외 셀 {len(skipped)}개 · 로그 {OUT_ROOT}')
    failed = [r for r in gen_log if r['status'] not in ('OK', 'SKIPPED_WOULD_MODIFY_RAW_DATA')]
    if failed:
        print('실패한 단계:')
        for r in failed:
            print('  ', r['step'], r['subset'], r['status'])
        sys.exit(1)


if __name__ == '__main__':
    main()
