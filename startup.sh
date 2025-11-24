#!/bin/bash
# Adaptive Research Agent - Startup Script (Unix/Linux/Mac)
# This script starts all required services for the agent
#
# First time setup: Make this script executable
#   chmod +x startup.sh shutdown.sh
#
# Then run: ./startup.sh

set -e

echo "================================================================================"
echo "  Adaptive Research Agent - Startup"
echo "================================================================================"
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then run: source venv/bin/activate"
    echo "Then run: pip install -r backend/requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys"
    exit 1
fi

echo "[1/3] Starting Redis..."
echo ""

# Check if Redis is already running
if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Redis is already running on port 6379"
else
    # Try to start Redis using Docker
    if command -v docker &> /dev/null; then
        echo "Starting Redis with Docker..."
        docker run -d --name adaptive-agent-redis -p 6379:6379 redis/redis-stack:latest
        if [ $? -eq 0 ]; then
            echo "Redis started successfully"
            sleep 3
        else
            echo "[ERROR] Failed to start Redis with Docker"
            echo "Please start Redis manually"
            exit 1
        fi
    else
        echo "[ERROR] Docker not available"
        echo "Please install Docker or start Redis manually"
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

echo "API Server starting (PID: $API_PID)..."
echo "Logs: api_server.log"
echo "Waiting for server to initialize..."
sleep 5

echo ""
echo "[3/3] Verifying Services..."
echo ""

# Check if API server is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "[SUCCESS] API Server is running on http://localhost:8000"
else
    echo "[WARNING] API Server may still be starting..."
    echo "Check api_server.log for any errors"
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
echo "  1. Run the demo:        python demo.py"
echo "  2. Check health:        curl http://localhost:8000/health"
echo "  3. Submit a query:      See GETTING_STARTED.md"
echo "  4. View logs:           tail -f api_server.log"
echo ""
echo "To stop all services, run: ./shutdown.sh"
echo ""
