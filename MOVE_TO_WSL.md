# Moving to WSL - Quick Guide

## Current Status
✅ WSL 2 with Ubuntu is installed and running
✅ Project files are in Windows: `C:\Users\anupp\Documents\NexusAgent`

## Quick Migration Steps

### Option A: Access Windows Files from WSL (Easiest)

1. **Open WSL terminal:**
   ```powershell
   wsl
   ```

2. **Navigate to your project:**
   ```bash
   cd /mnt/c/Users/anupp/Documents/NexusAgent
   ```

3. **Run the setup script:**
   ```bash
   chmod +x setup_wsl.sh
   ./setup_wsl.sh
   ```

4. **Start Redis:**
   ```bash
   docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest
   ```

5. **Start the server:**
   ```bash
   source venv/bin/activate
   python backend/main.py
   ```

### Option B: Copy Project to WSL Filesystem (Better Performance)

1. **Open WSL terminal:**
   ```powershell
   wsl
   ```

2. **Create project directory in WSL:**
   ```bash
   mkdir -p ~/projects
   cd ~/projects
   ```

3. **Copy project from Windows:**
   ```bash
   cp -r /mnt/c/Users/anupp/Documents/NexusAgent ./adaptive-research-agent
   cd adaptive-research-agent
   ```

4. **Run the setup script:**
   ```bash
   chmod +x setup_wsl.sh
   ./setup_wsl.sh
   ```

5. **Start Redis:**
   ```bash
   docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest
   ```

6. **Start the server:**
   ```bash
   source venv/bin/activate
   python backend/main.py
   ```

## What the Setup Script Does

The `setup_wsl.sh` script will:
1. ✅ Update system packages
2. ✅ Install Python 3.11
3. ✅ Install Node.js 20
4. ✅ Install Docker
5. ✅ Install utilities (curl, git)
6. ✅ Create Python virtual environment
7. ✅ Install Python dependencies
8. ✅ Build all 3 MCP servers

## After Setup

Once setup is complete, you can:

1. **Start all services:**
   ```bash
   ./startup.sh
   ```

2. **Run tests:**
   ```bash
   source venv/bin/activate
   pytest backend/test_e2e_query_flow.py -v
   ```

3. **Check health:**
   ```bash
   curl http://localhost:8000/health
   ```

## Accessing WSL from VS Code

If you use VS Code:
1. Install "Remote - WSL" extension
2. Open WSL terminal: `wsl`
3. Navigate to project: `cd ~/projects/adaptive-research-agent`
4. Open in VS Code: `code .`

## Troubleshooting

### Docker Permission Denied
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Port Already in Use
```bash
# Find process
sudo lsof -i :8000
# Kill process
sudo kill -9 <PID>
```

### Node.js Not Found
```bash
# Verify installation
node --version
npm --version

# If missing, reinstall
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

## Benefits of WSL

✅ Better MCP server compatibility
✅ Native Unix tools and scripts
✅ Improved Docker performance
✅ Consistent with production Linux environments
✅ Access to both Windows and Linux ecosystems

## Next Steps

After migration is complete, continue with Phase 4 testing:
- Task 11.1: Test complete query flow ✅ (test file created)
- Task 11.2: Test history retrieval
- Task 11.3: Test report listing and retrieval
- Task 11.4: Test error handling
- Task 11.5: Test health endpoint
