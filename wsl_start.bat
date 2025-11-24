@echo off
REM Start Adaptive Research Agent in WSL

echo ================================================================================
echo   Starting Adaptive Research Agent in WSL
echo ================================================================================
echo.

set "WSL_PATH=/mnt/c/Users/anupp/Documents/NexusAgent"

echo [1/3] Starting Redis...
wsl bash -c "docker ps -q -f name=redis-research-agent | grep -q . && echo 'Redis already running' || docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest"

echo.
echo [2/3] Starting API Server...
echo Opening new WSL terminal for API server...

REM Start API server in new Windows Terminal tab (if available) or new window
wt -w 0 nt wsl bash -c "cd '%WSL_PATH%' && source venv/bin/activate && python backend/main.py"

if %errorlevel% neq 0 (
    REM Fallback: start in new command window
    start "Adaptive Research Agent - API Server" wsl bash -c "cd '%WSL_PATH%' && source venv/bin/activate && python backend/main.py"
)

echo.
echo [3/3] Waiting for server to start...
timeout /t 5 /nobreak >nul

echo.
echo ================================================================================
echo   Startup Complete!
echo ================================================================================
echo.
echo Services:
echo   - Redis:      Running on port 6379
echo   - API Server: Running on http://localhost:8000
echo.
echo To test:
echo   curl http://localhost:8000/health
echo.
echo To run tests:
echo   wsl bash -c "cd '%WSL_PATH%' && source venv/bin/activate && pytest backend/test_e2e_query_flow.py -v"
echo.
echo To stop:
echo   wsl_stop.bat
echo.

pause
