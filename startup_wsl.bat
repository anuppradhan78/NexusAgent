@echo off
REM Adaptive Research Agent - Startup Script for WSL (Windows wrapper)
REM This script calls the WSL startup script from Windows

echo ================================================================================
echo   Adaptive Research Agent - Startup (WSL Native)
echo ================================================================================
echo.

echo Starting services in WSL native filesystem...
echo.

wsl bash ~/projects/adaptive-research-agent/startup_wsl.sh

if %errorlevel% equ 0 (
    echo.
    echo ================================================================================
    echo   Services Started Successfully!
    echo ================================================================================
    echo.
    echo Access from Windows:
    echo   - API Server: http://localhost:8000
    echo   - Health:     curl http://localhost:8000/health
    echo.
    echo To stop services, run: shutdown_wsl.bat
    echo.
) else (
    echo.
    echo [ERROR] Failed to start services
    echo Check the output above for errors
    echo.
)

pause
