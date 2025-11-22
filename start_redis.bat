@echo off
REM Start Redis with RediSearch module using Docker
REM This script starts Redis Stack Server which includes RediSearch

echo Starting Redis with RediSearch module...
echo.

docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack-server:latest

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Redis started successfully!
    echo.
    echo Redis is now running on localhost:6379
    echo.
    echo To stop Redis: docker stop redis-research-agent
    echo To remove Redis: docker rm redis-research-agent
    echo To view logs: docker logs redis-research-agent
) else (
    echo.
    echo ✗ Failed to start Redis
    echo.
    echo Make sure Docker is installed and running
    echo Install Docker from: https://www.docker.com/products/docker-desktop
)

pause
