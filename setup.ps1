# setup.ps1 — Install dependencies, configure hooks, create state directories
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateDir = Join-Path $env:USERPROFILE ".claude-helper"
$VenvDir = Join-Path $StateDir "venv"
$ClaudeSettings = Join-Path $env:USERPROFILE ".claude\settings.json"

Write-Host "=== Claude Helper Setup ===" -ForegroundColor Cyan

# Find Python executable (try python, then py -3)
$PythonExe = $null
try {
    $ver = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) { $PythonExe = "python" }
} catch {}
if (-not $PythonExe) {
    try {
        $ver = & py -3 --version 2>&1
        if ($LASTEXITCODE -eq 0) { $PythonExe = "py -3" }
    } catch {}
}
if (-not $PythonExe) {
    Write-Host "ERROR: Python 3 not found. Install Python from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "  Using: $PythonExe ($ver)" -ForegroundColor Gray

# 1. Create virtual environment and install dependencies
Write-Host ""
Write-Host "[1/3] Setting up Python virtual environment..." -ForegroundColor Yellow
Invoke-Expression "$PythonExe -m venv `"$VenvDir`""
& "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip -q
& "$VenvDir\Scripts\python.exe" -m pip install -r "$ScriptDir\requirements.txt" -q
Write-Host "  + venv created at $VenvDir" -ForegroundColor Green
Write-Host "  + dependencies installed (pystray, Pillow, psutil)" -ForegroundColor Green

# 2. Create state directories
Write-Host ""
Write-Host "[2/3] Creating state directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path (Join-Path $StateDir "sessions") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $StateDir "responses") | Out-Null
Write-Host "  + $StateDir\sessions" -ForegroundColor Green
Write-Host "  + $StateDir\responses" -ForegroundColor Green

# 3. Merge hook configuration into Claude settings
Write-Host ""
Write-Host "[3/3] Configuring Claude Code hooks..." -ForegroundColor Yellow

# Ensure settings directory and file exist
$ClaudeDir = Split-Path -Parent $ClaudeSettings
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
}
if (-not (Test-Path $ClaudeSettings)) {
    Set-Content -Path $ClaudeSettings -Value "{}"
}

$HooksDir = Join-Path $ScriptDir "hooks"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$MergeScript = Join-Path $ScriptDir "merge_hooks.py"

& $VenvPython $MergeScript $ClaudeSettings $HooksDir $VenvPython

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the system tray app:" -ForegroundColor White
Write-Host "  & `"$VenvPython`" `"$ScriptDir\claude_helper.py`"" -ForegroundColor Gray
Write-Host ""
Write-Host "To enable auto-start on login:" -ForegroundColor White
Write-Host "  Click 'Auto-start: Off' in the system tray dropdown" -ForegroundColor Gray
Write-Host ""
Write-Host "To verify:" -ForegroundColor White
Write-Host "  1. Start a Claude Code session" -ForegroundColor Gray
Write-Host "  2. Ask Claude to run a bash command" -ForegroundColor Gray
Write-Host "  3. Check the system tray for the Claude Helper icon" -ForegroundColor Gray
