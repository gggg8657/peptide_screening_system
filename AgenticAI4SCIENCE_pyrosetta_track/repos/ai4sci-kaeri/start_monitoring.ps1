param(
    [int]$Iterations = 10,
    [string]$LlmProvider = 'ollama',
    [string]$LlmModel = 'gemma3:1b',
    [string]$LlmBaseUrl = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$backendArgs = @('-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8787')
$frontendCmd = 'npm.cmd'
$frontendArgs = @('run', 'dev', '--', '--host')
$pipelineArgs = @(
    'run_pipeline_live.py',
    '--max-iterations', "$Iterations",
    '--llm-provider', $LlmProvider,
    '--llm-model', $LlmModel
)
if ($LlmBaseUrl -ne '') {
    $pipelineArgs += @('--llm-base-url', $LlmBaseUrl)
}

Write-Host "[launcher] Starting backend API server..." -ForegroundColor Cyan
$backend = Start-Process -FilePath 'python' -ArgumentList $backendArgs -PassThru
Start-Sleep -Seconds 1

Write-Host "[launcher] Starting frontend dev server..." -ForegroundColor Cyan
$frontend = Start-Process -FilePath $frontendCmd -ArgumentList $frontendArgs -WorkingDirectory (Join-Path $root 'frontend') -PassThru
Start-Sleep -Seconds 2

Write-Host "[launcher] Dashboard: http://localhost:5173" -ForegroundColor Green
Write-Host "[launcher] API:       http://localhost:8787/api/status" -ForegroundColor Green
Write-Host "[launcher] Running pipeline (N=$Iterations, model=$LlmModel)" -ForegroundColor Green

try {
    & python @pipelineArgs
}
finally {
    Write-Host "[launcher] Stopping backend/frontend..." -ForegroundColor Yellow
    if ($backend -and -not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
    if ($frontend -and -not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force }
}
