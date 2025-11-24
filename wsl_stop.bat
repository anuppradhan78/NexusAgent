@echo off
REM Stop Adaptive Research Agent in WSL

echo ================================================================================
echo   Stopping Adaptive Research Agent in WSL
echo ================================================================================
echo.

set "WSL_PATH=/mnt/c/Users/anupp/Documents/NexusAgent"

echo [1/2] Stopping API Server...
wsl bash -c "pkill -f 'python backend/main.py' || echo 'No API server running'"

echo.
echo [2/2] Stopping Redis...
wsl bash -c "docker stop redis-research-agent 2>/dev/null || echo 'Redis not running'"

echo.
echo ================================================================================
echo   Shutdown Complete!
echo ================================================================================
echo.

pause
