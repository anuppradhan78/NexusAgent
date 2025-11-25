#!/bin/bash
# Adaptive Research Agent - Startup Script for WSL Native Deployment
# This script starts all required services in the WSL native filesystem

set -e

echo "================================================================================"
echo "  Adaptive Research Agent - Startup (WSL Native)"
echo "================================================================================"
echo ""

# Navigate to WSL native project directory
cd ~/projects/adaptive-research-agent

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run the deployment script first: deploy_to_linux.bat"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please configure your API keys in .env"
    exit 1
fi

echo "[1/3] Starting Redis..."
echo ""

# Check if Redis is already running on port 6379
if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✓ Redis is already running on port 6379"
    # Check which container is using it
    REDIS_CONTAINER=$(docker ps --filter "publish=6379" --format "{{.Names}}" 2>/dev/null | head -1)
    if [ -n "$REDIS_CONTAINER" ]; then
        echo "  Using container: $REDIS_CONTAINER"
    fi
    
    # Clean up any failed containers
    docker rm -f adaptive-agent-redis >/dev/null 2>&1 || true
else
    # Clean up any existing containers first
    docker rm -f adaptive-agent-redis >/dev/null 2>&1 || true
    
    # Create new container
    echo "Creating new Redis container..."
    docker run -d --name adaptive-agent-redis -p 6379:6379 redis/redis-stack:latest >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Redis started successfully"
        sleep 2
    else
        echo "[ERROR] Failed to start Redis"
        echo "  Port 6379 may be in use by another process"
        exit 1
    fi
fi

echo ""
echo "[2/3] Starting API Server..."
echo ""

# Activate virtual environment and start API server in background
source venv/bin/activate
cd backend
nohup python main.py > ../api_server.log 2>&1 &
API_PID=$!
cd ..

echo "✓ API Server starting (PID: $API_PID)"
echo "  Logs: ~/projects/adaptive-research-agent/api_server.log"
echo "  Waiting for server to initialize..."
sleep 5

echo ""
echo "[3/3] Verifying Services..."
echo ""

# Check if API server is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API Server is running on http://localhost:8000"
    
    # Show health status
    HEALTH=$(curl -s http://localhost:8000/health)
    echo ""
    echo "Health Status:"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "[WARNING] API Server may still be starting..."
    echo "Check api_server.log for any errors: tail -f ~/projects/adaptive-research-agent/api_server.log"
fi

echo ""
echo "================================================================================"
echo "  Startup Complete!"
echo "================================================================================"
echo ""
echo "Services Status:"
echo "  - Redis:      Running on port 6379"
echo "  - API Server: Running on http://localhost:8000 (PID: $API_PID)"
echo ""
echo "Next Steps:"
echo "  1. Check health:   curl http://localhost:8000/health"
echo "  2. View logs:      tail -f ~/projects/adaptive-research-agent/api_server.log"
echo "  3. Add API key:    nano ~/projects/adaptive-research-agent/.env"
echo ""
echo "To stop services:"
echo "  From Windows: wsl bash ~/projects/adaptive-research-agent/shutdown_wsl.sh"
echo "  From WSL:     ~/projects/adaptive-research-agent/shutdown_wsl.sh"
echo ""
