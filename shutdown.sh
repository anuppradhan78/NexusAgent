#!/bin/bash
# Adaptive Research Agent - Shutdown Script (Unix/Linux/Mac)
# This script stops all running services
#
# First time setup: Make this script executable
#   chmod +x startup.sh shutdown.sh
#
# Then run: ./shutdown.sh

echo "================================================================================"
echo "  Adaptive Research Agent - Shutdown"
echo "================================================================================"
echo ""

echo "[1/2] Stopping API Server..."
echo ""

# Find and kill processes on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo "Stopping process on port 8000 (PID: $PID)"
    kill -9 $PID 2>/dev/null || true
    echo "API Server stopped"
else
    echo "No process found on port 8000"
fi

# Also try to kill by process name
pkill -f "python.*main.py" 2>/dev/null || true

echo ""
echo "[2/2] Stopping Redis..."
echo ""

# Stop Redis Docker container
if docker ps | grep -q "adaptive-agent-redis"; then
    echo "Stopping Redis container..."
    docker stop adaptive-agent-redis >/dev/null 2>&1 || true
    docker rm adaptive-agent-redis >/dev/null 2>&1 || true
    echo "Redis stopped"
else
    # Try to stop Redis on port 6379
    if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -Pi :6379 -sTCP:LISTEN -t)
        echo "Stopping process on port 6379 (PID: $PID)"
        kill -9 $PID 2>/dev/null || true
        echo "Redis stopped"
    else
        echo "No Redis process found on port 6379"
    fi
fi

# Clean up log file
if [ -f "api_server.log" ]; then
    echo ""
    echo "Cleaning up log file..."
    rm api_server.log
fi

echo ""
echo "================================================================================"
echo "  Shutdown Complete!"
echo "================================================================================"
echo ""
echo "All services have been stopped."
echo ""
echo "To start services again, run: ./startup.sh"
echo ""
