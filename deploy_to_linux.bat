@echo off
REM Deploy to Native Linux (WSL Native Filesystem)

echo ================================================================================
echo   Deploy to Native Linux (WSL)
echo ================================================================================
echo.
echo This will:
echo   1. Copy project to WSL native filesystem (~~/projects/)
echo   2. Create fresh Python virtual environment
echo   3. Install all dependencies
echo   4. Start Redis
echo.
echo Time: ~5 minutes
echo.
pause

wsl bash -c "cd /mnt/c/Users/anupp/Documents/NexusAgent && chmod +x deploy_to_native_linux.sh && ./deploy_to_native_linux.sh"

if %errorlevel% equ 0 (
    echo.
    echo ================================================================================
    echo   ✅ Deployment Successful!
    echo ================================================================================
    echo.
    echo Your project is now in native Linux at: ~/projects/adaptive-research-agent
    echo.
    echo To start the server, run:
    echo   wsl
    echo   cd ~/projects/adaptive-research-agent
    echo   source venv/bin/activate
    echo   python backend/main.py
    echo.
    echo Or use the quick start script:
    echo   wsl bash -c "cd ~/projects/adaptive-research-agent && source venv/bin/activate && python backend/main.py"
    echo.
) else (
    echo.
    echo ================================================================================
    echo   ❌ Deployment Failed
    echo ================================================================================
    echo.
    echo Please check the output above for errors.
    echo.
)

pause
