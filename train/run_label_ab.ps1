<#
.SYNOPSIS
    A/B 라벨 교체 본 실험 — 40회를 밤새 돌린다.

.DESCRIPTION
    CPMLP · CPTransformer  ×  AA/AB/BA/BB  ×  seed 42·2021·2024·7·1234 = 40회.
    CPGRU · CPLSTM · MLP 는 이번 범위가 아니다.

    조건 이름의 앞 글자가 **학습** 라벨, 뒷 글자가 **시험** 라벨이다.
    val 은 train 을 따른다 (검증은 학습 절차의 일부).

    시드 하나에 2모델 × 4조건 = 8회를 끝내고 다음 시드로 간다. 밤중에
    멈추더라도 시드 단위로는 결과가 온전하다.

    이미 결과 파일이 있는 조합은 건너뛴다 — 그대로 다시 돌리면 재개된다.

.PARAMETER DryRun
    학습을 돌리지 않고 40개 조합의 명령만 찍는다.

.PARAMETER Seeds
    돌릴 시드. 기본은 다섯 개 전부.

.EXAMPLE
    .\.venv-blife\Scripts\Activate.ps1
    python train\run_label_ab.ps1        # <- 아니다. 아래처럼 부른다
    powershell -ExecutionPolicy Bypass -File train\run_label_ab.ps1
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [int[]]$Seeds = @(42, 2021, 2024, 7, 1234),
    [string[]]$Models = @('CPMLP', 'CPTransformer'),
    [string[]]$Conditions = @('AA', 'AB', 'BA', 'BB'),
    [int]$MinFreeGB = 20,
    [int]$BasePort = 29000
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

$OutRoot = Join-Path $Repo 'experiments\results\label_ab'
$FailDir = Join-Path $OutRoot '_failures'
$LogDir = Join-Path $Repo 'runs\label_ab'
$ProgressLog = Join-Path $LogDir '_progress.log'
$VenvPy = Join-Path $Repo '.venv-blife\Scripts\python.exe'

New-Item -ItemType Directory -Force -Path $OutRoot, $FailDir, $LogDir | Out-Null

function Write-Both {
    param([string]$Message)
    $stamp = (Get-Date).ToString('HH:mm:ss')
    $line = "[$stamp] $Message"
    Write-Host $line
    Add-Content -Path $ProgressLog -Value $line -Encoding utf8
}

# --------------------------------------------------------------------------
# 사전 점검 — 하나라도 어긋나면 시작하지 않는다
# --------------------------------------------------------------------------

Write-Both "=== A/B 본 실험 러너 시작 ==="

# (1) .venv-blife 확인. 활성화되어 있지 않으면 **즉시 멈춘다.**
if (-not (Test-Path $VenvPy)) {
    throw ".venv-blife 를 찾지 못했습니다: $VenvPy"
}
$pyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pyExe) { throw "python 이 PATH 에 없습니다. .venv-blife\Scripts\Activate.ps1 을 먼저 부르십시오." }
$resolvedVenv = (Resolve-Path $VenvPy).Path
if ($pyExe -ne $resolvedVenv) {
    throw @"
.venv-blife 가 활성화되지 않았습니다. 즉시 멈춥니다.
  지금 python : $pyExe
  필요한 python: $resolvedVenv
  먼저: .\.venv-blife\Scripts\Activate.ps1
"@
}
$torchOk = & python -c "import torch,sys; sys.stdout.write(torch.__version__ + '|' + str(torch.cuda.is_available()))" 2>$null
if ($LASTEXITCODE -ne 0) { throw "torch 를 불러오지 못했습니다. 환경을 확인하십시오." }
Write-Both "환경 OK — python=$pyExe  torch=$torchOk"

# (2) 진입점과 텐서 캐시
$entry = Join-Path $Repo '.build\batterylife\run_main_nodeepspeed.py'
if (-not (Test-Path $entry)) { throw ".build 진입점이 없습니다: $entry  (train/make_scripts.py 로 재생성하십시오)" }
$cache = Join-Path $Repo 'data\tensor_cache\liion_curves.npy'
if (-not (Test-Path $cache)) { throw "Li-ion 텐서 캐시가 없습니다: $cache  (train/build_tensor_cache.py --domain Li-ion)" }

# (3) 디스크 여유. 페이지 파일 설정은 건드리지 않는다.
$drive = (Get-Item $Repo).PSDrive
$freeGB = [math]::Round($drive.Free / 1GB, 1)
if ($freeGB -lt $MinFreeGB) {
    throw "디스크 여유가 $freeGB GB 입니다. 최소 $MinFreeGB GB 가 필요합니다."
}
Write-Both "디스크 OK — $($drive.Name): 여유 $freeGB GB (체크포인트 40회분 약 0.7 GB 예상)"

# (4) 기존 체크포인트를 건드리지 않는지 확인
$oldCkpt = Join-Path $Repo 'data\checkpoints'
$newCkpt = Join-Path $Repo 'data\checkpoints_label_ab'
if ($newCkpt.StartsWith($oldCkpt + [IO.Path]::DirectorySeparatorChar)) {
    throw "체크포인트 경로가 기존 트리 안입니다. 갈라야 합니다: $newCkpt"
}
$oldSize = 0
if (Test-Path $oldCkpt) {
    $oldSize = (Get-ChildItem $oldCkpt -Recurse -File | Measure-Object -Property Length -Sum).Sum
    Write-Both ("기존 체크포인트 {0:N0} MB — 이 러너는 {1} 만 씁니다" -f ($oldSize / 1MB), (Split-Path $newCkpt -Leaf))
}

# --------------------------------------------------------------------------
# 조합 목록 — 시드 단위로 묶는다
# --------------------------------------------------------------------------

$combos = @()
foreach ($seed in $Seeds) {
    foreach ($model in $Models) {
        foreach ($cond in $Conditions) {
            $combos += [pscustomobject]@{
                Seed = $seed; Model = $model; Condition = $cond
                Result = Join-Path $OutRoot "$cond\$($model)_s$seed.json"
                Timeout = if ($model -eq 'CPMLP') { 24 * 60 } else { 61 * 60 }
            }
        }
    }
}
$total = $combos.Count
Write-Both "조합 $total 개 (시드 $($Seeds.Count) × 모델 $($Models.Count) × 조건 $($Conditions.Count))"

if ($DryRun) {
    Write-Both "--- DRY RUN — 학습을 돌리지 않습니다 ---"
    $i = 0
    foreach ($c in $combos) {
        $i++
        $port = $BasePort + $i
        Write-Host ("--- [{0}/{1}] {2} / {3} / seed {4}" -f $i, $total, $c.Condition, $c.Model, $c.Seed)
        & python (Join-Path $Repo 'train\run_label_ab_one.py') `
            --condition $c.Condition --model $c.Model --seed $c.Seed `
            --port $port --timeout $c.Timeout --dry-run
        if ($LASTEXITCODE -ne 0) { throw "dry-run 실패: $($c.Condition)/$($c.Model)/s$($c.Seed)" }
    }
    Write-Both "--- DRY RUN 끝. $total 개 명령 생성 확인 ---"
    exit 0
}

# --------------------------------------------------------------------------
# 실행
# --------------------------------------------------------------------------

$done = 0; $skipped = 0; $failed = 0; $ran = 0
$startedAt = Get-Date
$durations = @()
$i = 0

foreach ($c in $combos) {
    $i++
    $tag = "$($c.Condition)/$($c.Model)/s$($c.Seed)"

    if (Test-Path $c.Result) {
        $skipped++; $done++
        Write-Both "[$i/$total] $tag  건너뜀 (결과 있음)"
        continue
    }

    # 남은 예상: 지금까지 실제로 돈 것들의 평균 × 남은 개수
    $remainText = ''
    if ($durations.Count -gt 0) {
        $avg = ($durations | Measure-Object -Average).Average
        $remain = ($total - $done) * $avg
        $remainText = "  남은 예상 {0:N1}h" -f ($remain / 3600)
    }
    Write-Both "[$i/$total] $tag  시작 (완료 $done/$total, 경과 $([math]::Round(((Get-Date) - $startedAt).TotalMinutes,1))분$remainText)"

    $t0 = Get-Date
    & python (Join-Path $Repo 'train\run_label_ab_one.py') `
        --condition $c.Condition --model $c.Model --seed $c.Seed `
        --port ($BasePort + $i) --timeout $c.Timeout
    $rc = $LASTEXITCODE
    $elapsed = ((Get-Date) - $t0).TotalSeconds

    if ($rc -eq 0) {
        $ran++; $done++; $durations += $elapsed
        Write-Both "[$i/$total] $tag  완료 ($([math]::Round($elapsed,0))s)"
    }
    else {
        # 한 조합이 실패해도 다음으로 간다. traceback 은 _failures/ 에 있다.
        $failed++
        Write-Both "[$i/$total] $tag  [실패] rc=$rc ($([math]::Round($elapsed,0))s) — $FailDir 를 보십시오"
    }
}

$wall = ((Get-Date) - $startedAt).TotalHours
Write-Both "=== 끝 === 완료 $done/$total (새로 돔 $ran · 건너뜀 $skipped · 실패 $failed) · 총 $([math]::Round($wall,2))시간"
if ($failed -gt 0) {
    Write-Both "실패 목록:"
    Get-ChildItem $FailDir -Filter *.txt | ForEach-Object { Write-Both "  $($_.Name)" }
}
exit ([int]($failed -gt 0))
