# WSL Migration Guide for Adaptive Research Agent

## Overview
This guide helps you migrate the Adaptive Research Agent from Windows to Windows Subsystem for Linux (WSL) to resolve MCP compatibility issues.

## Prerequisites

### 1. Install WSL
```powershell
# Run in PowerShell as Administrator
wsl --install
```

This installs Ubuntu by default. Restart your computer when prompted.

### 2. Verify WSL Installation
```bash
wsl --list --verbose
```

## Migration Steps

### Step 1: Access WSL
Open WSL terminal:
```powershell
wsl
```

### Step 2: Install Required Dependencies in WSL

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js (required for MCP servers)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker (for Redis)
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install curl and other utilities
sudo apt install -y curl git
```

### Step 3: Copy Project to WSL

Option A: Access Windows files from WSL
```bash
# Windows drives are mounted at /mnt/
cd /mnt/c/Users/YourUsername/path/to/adaptive-research-agent
```

Option B: Clone fresh copy in WSL
```bash
# Create workspace in WSL home directory
cd ~
mkdir -p projects
cd projects
# Copy files or clone repository
```

### Step 4: Set Up Python Environment

```bash
# Navigate to project directory
cd ~/projects/adaptive-research-agent  # or your path

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 5: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env  # or use: code .env if VS Code is installed
```

Add your keys:
```env
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://localhost:6379
POSTMAN_API_KEY=PMAK-...
```

### Step 6: Start Redis in WSL

```bash
# Start Docker service if not running
sudo service docker start

# Start Redis container
docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest

# Verify Redis is running
docker ps
```

### Step 7: Test MCP Servers

```bash
# Test Anthropic MCP server
npx -y @anthropic-ai/mcp-server-anthropic

# Test Postman MCP server (if you have API key)
npx -y @postman/mcp-server
```

### Step 8: Start the Application

```bash
# Make startup script executable
chmod +x startup.sh shutdown.sh

# Start all services
./startup.sh
```

### Step 9: Verify Everything Works

```bash
# Check health endpoint
curl http://localhost:8000/health

# Run the demo
python demo.py

# Run tests
cd backend
pytest -v
```

## Common Issues and Solutions

### Issue: Docker Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### Issue: Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :6379

# Kill process
sudo kill -9 <PID>
```

### Issue: Python Version
```bash
# Check Python version
python3 --version

# If not 3.11+, install it
sudo apt install -y python3.11 python3.11-venv
```

### Issue: Node.js Not Found
```bash
# Verify Node.js installation
node --version
npm --version

# If missing, reinstall
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

## Accessing WSL from Windows

### VS Code Integration
1. Install "Remote - WSL" extension in VS Code
2. Open WSL terminal: `wsl`
3. Navigate to project: `cd ~/projects/adaptive-research-agent`
4. Open in VS Code: `code .`

### File Access
- Access WSL files from Windows: `\\wsl$\Ubuntu\home\username\projects\`
- Access Windows files from WSL: `/mnt/c/Users/YourUsername/`

## Performance Tips

1. **Keep project files in WSL filesystem** (not /mnt/c/) for better performance
2. **Use WSL 2** (not WSL 1) for Docker compatibility
3. **Allocate more memory** to WSL if needed:
   - Create/edit `%USERPROFILE%\.wslconfig`
   ```ini
   [wsl2]
   memory=4GB
   processors=2
   ```

## Next Steps

After successful migration:

1. ✅ Verify all services start correctly
2. ✅ Run the test suite
3. ✅ Test MCP server connections
4. ✅ Run demo.py to verify full functionality
5. ✅ Update any documentation with WSL-specific instructions

## Rollback Plan

If you need to return to Windows:
1. Keep your Windows installation intact
2. Export WSL environment: `wsl --export Ubuntu backup.tar`
3. Can switch back anytime using Windows scripts

## Benefits of WSL

- ✅ Better MCP server compatibility
- ✅ Native Unix tools and scripts
- ✅ Improved Docker performance
- ✅ Consistent with production Linux environments
- ✅ Access to both Windows and Linux ecosystems

## Support

If you encounter issues:
1. Check WSL logs: `dmesg | tail`
2. Check Docker logs: `docker logs redis-research-agent`
3. Check application logs: `tail -f api_server.log`
4. Verify MCP configuration: `cat mcp.json`
