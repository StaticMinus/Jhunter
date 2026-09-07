# AI Job Hunter — 24/7 Autonomous Daemon Persistent Supervisor
# Automatically restarts the daemon if any unhandled error or network failure occurs.

$ErrorActionPreference = "Continue"
$RootPath = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RootPath

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 🚀 AI JOB HUNTER — 24/7 AUTONOMOUS PUMP SUPERVISOR" -ForegroundColor Green
Write-Host " Workspace: $RootPath" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

$VenvPython = "$RootPath\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $VenvPython = "python"
}

$RestartCount = 0

while ($true) {
    $Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "`n[$Timestamp] [Supervisor] Starting Autonomous Daemon (Run #$($RestartCount + 1))..." -ForegroundColor Yellow
    
    try {
        & $VenvPython "workers\autonomous_daemon.py"
    } catch {
        Write-Host "[$Timestamp] [Supervisor] Process threw terminating error: $_" -ForegroundColor Red
    }

    $ExitCode = $LASTEXITCODE
    $RestartCount++
    $Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "[$Timestamp] [Supervisor] Autonomous Daemon exited with code $ExitCode. Restarting in 15 seconds (Restart count: $RestartCount)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
}
