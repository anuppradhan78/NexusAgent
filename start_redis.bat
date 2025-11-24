@echo off
REM Start Redis with RediSearch module using Docker
REM This script starts Redis Stack Server which includes RediSearch
REM
REM Useful commands:
REM   Check status: docker ps -a --filter "name=redis-research-agent"
REM   Stop Redis:   docker stop redis-research-agent
REM   Remove Redis: docker rm redis-research-agent
REM   View logs:    docker logs redis-research-agent
REM   Clean start:  docker stop redis-research-agent && docker rm redis-research-agent

echo Starting Redis with RediSearch module...
echo.

REM Check if anything is already running on port 6379
netstat -ano | findstr ":6379" | findstr "LISTENING" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Redis is already running on localhost:6379
    echo.
    echo If you need to restart it:
    echo   docker stop redis-research-agent
    echo   docker rm redis-research-agent
    echo   Then run this script again
    goto :end
)

REM Check if our container exists but is stopped
docker ps -a --filter "name=redis-research-agent" --format "{{.Names}}" 2>nul | findstr /C:"redis-research-agent" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Found existing container, starting it...
    docker start redis-research-agent
    if %ERRORLEVEL% EQU 0 (
        echo ✓ Redis started successfully!
        goto :end
    ) else (
        echo ✗ Failed to start existing container, removing it...
        docker rm -f redis-research-agent >nul 2>&1
    )
)

REM Create new container
echo Creating new Redis container...
docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack-server:latest

if %ERRORLEVEL% EQU 0 (
    echo ✓ Redis started successfully!
) else (
    echo ✗ Failed to start Redis
    echo.
    echo Possible issues:
    echo   - Docker is not installed or not running
    echo   - Port 6379 is already in use
    echo   - Container name conflict
    echo.
    echo Install Docker from: https://www.docker.com/products/docker-desktop
    goto :error
)

:end
echo.
echo Redis is now running on localhost:6379
echo.
echo Useful commands:
echo   Stop:   docker stop redis-research-agent
echo   Remove: docker rm redis-research-agent
echo   Logs:   docker logs redis-research-agent
echo.
exit /b 0

:error
echo.
exit /b 1
