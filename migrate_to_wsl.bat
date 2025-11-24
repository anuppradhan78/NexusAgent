@echo off
REM Migrate Adaptive Research Agent to WSL
REM This script launches WSL and runs the setup

echo ================================================================================
echo   Migrating Adaptive Research Agent to WSL
echo ================================================================================
echo.

REM Get current directory in Windows format
set "WIN_DIR=%CD%"

REM Convert to WSL path format
set "WSL_PATH=/mnt/c/Users/anupp/Documents/NexusAgent"

echo Current Windows directory: %WIN_DIR%
echo WSL path: %WSL_PATH%
echo.

echo Starting WSL setup...
echo This will take 5-10 minutes.
echo.

REM Launch WSL and run setup script
wsl bash -c "cd '%WSL_PATH%' && chmod +x setup_wsl.sh && ./setup_wsl.sh"

if %errorlevel% equ 0 (
    echo.
    echo ================================================================================
    echo   Migration Complete!
    echo ================================================================================
    echo.
    echo Next steps:
    echo   1. Open WSL: wsl
    echo   2. Navigate: cd /mnt/c/Users/anupp/Documents/NexusAgent
    echo   3. Start Redis: docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest
    echo   4. Start server: source venv/bin/activate ^&^& python backend/main.py
    echo.
    echo Or simply run: wsl_start.bat
    echo.
) else (
    echo.
    echo ================================================================================
    echo   Setup encountered an error
    echo ================================================================================
    echo.
    echo Please check the output above for details.
    echo You may need to run the setup manually in WSL.
    echo.
)

pause
