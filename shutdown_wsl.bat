@echo off
REM Adaptive Research Agent - Shutdown Script for WSL (Windows wrapper)
REM This script calls the WSL shutdown script from Windows

echo ================================================================================
echo   Adaptive Research Agent - Shutdown (WSL Native)
echo ================================================================================
echo.

echo Stopping services in WSL native filesystem...
echo.

wsl bash ~/projects/adaptive-research-agent/shutdown_wsl.sh

if %errorlevel% equ 0 (
    echo.
    echo ================================================================================
    echo   Services Stopped Successfully!
    echo ================================================================================
    echo.
    echo To start services again, run: startup_wsl.bat
    echo.
) else (
    echo.
    echo [ERROR] Failed to stop services
    echo Check the output above for errors
    echo.
)

pause
