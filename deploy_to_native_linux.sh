#!/bin/bash
# Deploy to Native Linux (WSL Native Filesystem)
# This copies the project from Windows filesystem to WSL native filesystem

set -e

echo "=========================================="
echo "Deploy to Native Linux (WSL)"
echo "=========================================="
echo ""

# Step 1: Copy project to WSL home directory
echo "[1/5] Copying project to WSL native filesystem..."
cd ~
mkdir -p projects
cd projects

# Remove old copy if exists
if [ -d "adaptive-research-agent" ]; then
    echo "Removing old copy..."
    rm -rf adaptive-research-agent
fi

# Copy from Windows mount
echo "Copying files (this may take a minute)..."
cp -r /mnt/c/Users/anupp/Documents/NexusAgent adaptive-research-agent
cd adaptive-research-agent

echo "✓ Project copied to: ~/projects/adaptive-research-agent"

# Step 2: Clean up Windows-specific files
echo ""
echo "[2/5] Cleaning up Windows-specific files..."
rm -rf venv_windows_backup 2>/dev/null || true
rm -rf venv 2>/dev/null || true
echo "✓ Cleaned up"

# Step 3: Create fresh virtual environment
echo ""
echo "[3/5] Creating fresh Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
echo "✓ Virtual environment created"

# Step 4: Verify MCP servers are built
echo ""
echo "[4/5] Verifying MCP servers..."
if [ -f "mcp-servers/postman/dist/index.js" ] && \
   [ -f "mcp-servers/memory/dist/index.js" ] && \
   [ -f "mcp-servers/research-tools/dist/index.js" ]; then
    echo "✓ All MCP servers are built"
else
    echo "Building MCP servers..."
    cd mcp-servers/postman && npm install && npm run build && cd ../..
    cd mcp-servers/memory && npm install && npm run build && cd ../..
    cd mcp-servers/research-tools && npm install && npm run build && cd ../..
    echo "✓ MCP servers built"
fi

# Step 5: Start Redis
echo ""
echo "[5/5] Starting Redis..."
if docker ps | grep -q redis-research-agent; then
    echo "✓ Redis already running"
else
    docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest
    echo "✓ Redis started"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Project location: ~/projects/adaptive-research-agent"
echo ""
echo "To start the server:"
echo "  cd ~/projects/adaptive-research-agent"
echo "  source venv/bin/activate"
echo "  python backend/main.py"
echo ""
echo "To run tests:"
echo "  cd ~/projects/adaptive-research-agent"
echo "  source venv/bin/activate"
echo "  pytest backend/test_e2e_query_flow.py -v"
echo ""
echo "To access from Windows:"
echo "  - Server will be at: http://localhost:8000"
echo "  - Open VS Code: code ~/projects/adaptive-research-agent"
echo ""
