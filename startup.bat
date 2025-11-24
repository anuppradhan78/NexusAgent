@echo off
REM Adaptive Research Agent - Startup Script (Windows)
REM This script starts all required services for the agent

echo ================================================================================
echo   Adaptive Research Agent - Startup
echo ================================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r backend\requirements.txt
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and configure your API keys
    pause
    exit /b 1
)

echo [1/3] Starting Redis...
echo.

REM Check if Redis is already running on port 6379
netstat -ano | findstr ":6379" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo Redis is already running on port 6379
) else (
    REM Check if our container exists but is stopped
    docker ps -a --filter "name=redis-research-agent" --format "{{.Names}}" 2>nul | findstr /C:"redis-research-agent" >nul 2>&1
    
    if %errorlevel% equ 0 (
        echo Starting existing Redis container...
        docker start redis-research-agent >nul 2>&1
        if %errorlevel% equ 0 (
            echo Redis started successfully
            timeout /t 2 /nobreak >nul
        ) else (
            echo [ERROR] Failed to start Redis
            echo Please run: start_redis.bat
            exit /b 1
        )
    ) else (
        REM Try to create new container
        echo Starting Redis with Docker...
        docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack-server:latest >nul 2>&1
        if %errorlevel% equ 0 (
            echo Redis started successfully
            timeout /t 2 /nobreak >nul
        ) else (
            echo [ERROR] Failed to start Redis with Docker
            echo Please run: start_redis.bat
            exit /b 1
        )
    )
)

echo.
echo [2/3] Starting API Server...
echo.

REM Start API server in a new window
REM Use the venv Python directly to avoid activation issues
set "SCRIPT_DIR=%~dp0"
start "Adaptive Research Agent - API Server" cmd /k "cd /d "%SCRIPT_DIR%backend" && "%SCRIPT_DIR%venv\Scripts\python.exe" main.py"

echo API Server starting in new window...
echo Waiting for server to initialize...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Verifying Services...
echo.

REM Check if API server is responding
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] API Server is running on http://localhost:8000
) else (
    echo [WARNING] API Server may still be starting...
    echo Check the API Server window for any errors
)

echo.
echo ================================================================================
echo   Startup Complete!
echo ================================================================================
echo.
echo Services Status:
echo   - Redis:      Running on port 6379
echo   - API Server: Running on http://localhost:8000
echo.
echo Next Steps:
echo   1. Run the demo:        python demo.py
echo   2. Check health:        curl http://localhost:8000/health
echo   3. Submit a query:      See GETTING_STARTED.md
echo.
echo To stop all services, run: shutdown.bat
echo.
pause
