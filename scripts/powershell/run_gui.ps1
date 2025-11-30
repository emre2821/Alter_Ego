# scripts/powershell/run_gui.ps1 - Launcher for Alter/Ego GUI
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Change to repository root (two levels up from scripts/powershell/)
$RepoRoot = Join-Path $PSScriptRoot "..\..\"
Set-Location -LiteralPath $RepoRoot

# Logs
$null = New-Item -ItemType Directory -Force -Path "$RepoRoot\logs"
$ts  = (Get-Date).ToString('yyyyMMdd_HHmmss')
$log = Join-Path $RepoRoot "logs\run_$ts.log"

# Keep GPT4All on CPU; make output UTF-8
$env:GPT4ALL_NO_CUDA = '1'
$env:PYTHONUTF8      = '1'

Write-Host "== Alter/Ego starting =="
Write-Host "  Folder: $RepoRoot"
Write-Host "  Log:    $log"
Write-Host ""

# Ensure uv exists
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host "[fatal] 'uv' not found on PATH. Add %USERPROFILE%\.local\bin to PATH or reinstall uv." -ForegroundColor Red
  Pause
  exit 1
}

# Ensure Typer (prevents earlier import error)
uv run python - <<'PY'
import importlib, sys
sys.exit(0 if importlib.util.find_spec('typer') else 1)
PY
if ($LASTEXITCODE -ne 0) {
  Write-Host "[setup] Installing Typer..."
  uv pip install "typer>=0.12,<0.13"
}

# Launch + tee to file
Write-Host "[run] Launching Alter/Ego GUI..."
$launchArgs = @('src\alter_ego\alter_ego_computer.py', 'launch')
if ($env:PERSONA_ROOT) {
  $launchArgs += @('--persona-root', $env:PERSONA_ROOT)
}
if ($env:ALTER_EGO_DUMMY_ONLY -and $env:ALTER_EGO_DUMMY_ONLY.ToLower() -eq 'on') {
  $launchArgs += '--dummy-only'
}
if ($env:GPT4ALL_MODEL) {
  $launchArgs += @('--gpt4all-model', $env:GPT4ALL_MODEL)
}
if ($env:ALTER_EGO_THEME) {
  $launchArgs += @('--theme', $env:ALTER_EGO_THEME)
}
if ($env:ENABLE_TTS) {
  $launchArgs += @('--enable-tts', ($env:ENABLE_TTS -ne '0'))
}
uv run python @launchArgs *>&1 | Tee-Object -FilePath $log

Write-Host ""
Write-Host "== Alter/Ego exited =="
Write-Host "Log saved to: $log"
Pause
