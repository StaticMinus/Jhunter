@echo off
title AI Job Hunter - 24/7 Autonomous Daemon
echo Starting AI Job Hunter Autonomous Daemon...
powershell -ExecutionPolicy Bypass -File "%~dp0start_daemon.ps1"
pause
