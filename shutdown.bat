@echo off
REM Adaptive Research Agent - Shutdown Script (Windows)
REM This script stops all running services

echo ================================================================================
echo   Adaptive Research Agent - Shutdown
echo ================================================================================
echo.

echo [1/2] Stopping API Server...
echo.

REM Find and kill Python processes running main.py
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Stopping process on port 8000 (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)

REM Also try to kill by process name
tasklist | findstr "python.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo Stopping Python processes...
    REM Only kill if running from backend directory
    wmic process where "commandline like '%%main.py%%'" delete >nul 2>&1
)

echo API Server stopped

echo.
echo [2/2] Stopping Redis...
echo.

REM Stop Redis Docker container
docker ps | findstr "redis-research-agent" >nul 2>&1
if %errorlevel% equ 0 (
    echo Stopping Redis container...
    docker stop redis-research-agent >nul 2>&1
    echo Redis stopped
) else (
    echo Redis container not running
)

echo.
echo ================================================================================
echo   Shutdown Complete!
echo ================================================================================
echo.
echo All services have been stopped.
echo.
echo To start services again, run: startup.bat
echo.
pause
