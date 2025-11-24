#!/bin/bash
# WSL Setup Script for Adaptive Research Agent
# This script sets up the project in WSL

set -e

echo "=========================================="
echo "WSL Setup - Adaptive Research Agent"
echo "=========================================="
echo ""

# Step 1: Update system packages
echo "[1/8] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Python 3.12 (Ubuntu 24.04 default) or 3.11
echo ""
echo "[2/8] Installing Python..."
# Check if python3.12 is available (Ubuntu 24.04)
if apt-cache show python3.12 &> /dev/null; then
    echo "Installing Python 3.12 (Ubuntu 24.04 default)..."
    sudo apt install -y python3.12 python3.12-venv python3-pip
    PYTHON_CMD="python3.12"
else
    # Fallback to python3.11 with deadsnakes PPA
    echo "Adding deadsnakes PPA for Python 3.11..."
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3-pip
    PYTHON_CMD="python3.11"
fi

echo "Python installed: $($PYTHON_CMD --version)"

# Step 3: Install Node.js 20
echo ""
echo "[3/8] Installing Node.js 20..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo "Node.js already installed: $(node --version)"
fi

# Step 4: Check Docker
echo ""
echo "[4/8] Checking Docker..."
if command -v docker &> /dev/null; then
    echo "Docker is available: $(docker --version)"
    echo "Note: Using Docker Desktop for Windows (accessed from WSL)"
else
    echo "Warning: Docker not found"
    echo "Please ensure Docker Desktop for Windows is installed and WSL integration is enabled"
    echo "You can continue - Docker will be needed later for Redis"
fi

# Step 5: Install utilities
echo ""
echo "[5/8] Installing utilities..."
sudo apt install -y curl git

# Step 6: Create Python virtual environment
echo ""
echo "[6/8] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "Virtual environment created with $PYTHON_CMD"
else
    echo "Virtual environment already exists"
fi

# Step 7: Install Python dependencies
echo ""
echo "[7/8] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Step 8: Build MCP servers
echo ""
echo "[8/8] Building MCP servers..."

# Build Postman MCP server
if [ -d "mcp-servers/postman" ]; then
    echo "Building Postman MCP server..."
    cd mcp-servers/postman
    npm install
    npm run build
    cd ../..
fi

# Build Memory MCP server
if [ -d "mcp-servers/memory" ]; then
    echo "Building Memory MCP server..."
    cd mcp-servers/memory
    npm install
    npm run build
    cd ../..
fi

# Build Research Tools MCP server
if [ -d "mcp-servers/research-tools" ]; then
    echo "Building Research Tools MCP server..."
    cd mcp-servers/research-tools
    npm install
    npm run build
    cd ../..
fi

echo ""
echo "=========================================="
echo "✅ WSL Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start Redis: docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Start server: python backend/main.py"
echo "4. Run tests: pytest backend/test_e2e_query_flow.py -v"
echo ""
echo "Or use the startup script: ./startup.sh"
echo ""
