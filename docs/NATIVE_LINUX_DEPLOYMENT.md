# Native Linux Deployment Guide

## Why Native Linux?

**Current Issue**: Project is on Windows filesystem (`/mnt/c/`), accessed by WSL. This causes MCP stdio communication to fail.

**Solution**: Copy project to WSL's native Linux filesystem. This gives true native Linux performance and fixes MCP issues.

## What You Need

✅ You already have:
- WSL 2 with Ubuntu installed
- All dependencies installed in WSL
- MCP servers built

## Deployment Options

### Option 1: Automated Deployment (Recommended)

**Time**: ~5 minutes

Simply run:
```cmd
deploy_to_linux.bat
```

This will:
1. Copy project to `~/projects/adaptive-research-agent` in WSL
2. Create fresh Python virtual environment
3. Install all dependencies
4. Verify MCP servers
5. Start Redis

### Option 2: Manual Deployment

If you prefer to do it manually:

```bash
# 1. Open WSL
wsl

# 2. Copy project to native filesystem
cd ~
mkdir -p projects
cp -r /mnt/c/Users/anupp/Documents/NexusAgent projects/adaptive-research-agent
cd projects/adaptive-research-agent

# 3. Create fresh virtual environment
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 4. Start Redis
docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest

# 5. Start server
python backend/main.py
```

## After Deployment

### Starting the Server

**From Windows Command Prompt:**
```cmd
wsl bash -c "cd ~/projects/adaptive-research-agent && source venv/bin/activate && python backend/main.py"
```

**From WSL Terminal:**
```bash
cd ~/projects/adaptive-research-agent
source venv/bin/activate
python backend/main.py
```

### Running Tests

```bash
cd ~/projects/adaptive-research-agent
source venv/bin/activate
pytest backend/test_e2e_query_flow.py -v
```

### Accessing from Windows

- **API Server**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **VS Code**: `code ~/projects/adaptive-research-agent` (from WSL)

## What This Fixes

| Issue | Before (Windows FS) | After (Native Linux) |
|-------|---------------------|----------------------|
| MCP stdio | ❌ Doesn't work | ✅ Works perfectly |
| File I/O | ⚠️ Slow | ✅ Fast |
| Process spawning | ❌ Unreliable | ✅ Reliable |
| Node.js pipes | ❌ Broken | ✅ Works |

## Expected Results

After deployment, health check should show:

```json
{
  "status": "healthy",
  "redis_connected": true,
  "mcp_servers_connected": 3,  // ← This should be 3, not 0!
  "timestamp": "2025-11-23T..."
}
```

## File Locations

| Location | Path | Purpose |
|----------|------|---------|
| **Windows** | `C:\Users\anupp\Documents\NexusAgent` | Original (keep as backup) |
| **WSL Native** | `~/projects/adaptive-research-agent` | Active development |
| **From Windows** | `\\wsl$\Ubuntu\home\<user>\projects\adaptive-research-agent` | Access from Explorer |

## Development Workflow

### Editing Files

**Option A: VS Code Remote WSL**
1. Install "Remote - WSL" extension in VS Code
2. In WSL: `code ~/projects/adaptive-research-agent`
3. Edit files directly in native Linux

**Option B: Windows Explorer**
1. Open: `\\wsl$\Ubuntu\home\<username>\projects\adaptive-research-agent`
2. Edit with any Windows editor
3. Changes are instant

### Running Commands

Always run from WSL for best performance:
```bash
wsl
cd ~/projects/adaptive-research-agent
source venv/bin/activate
# Your commands here
```

## Advantages

1. ✅ **MCP servers work** - stdio communication works perfectly
2. ✅ **Better performance** - No Windows/Linux translation layer
3. ✅ **True Linux environment** - Matches production
4. ✅ **Still accessible from Windows** - Via network and file sharing
5. ✅ **VS Code integration** - Remote WSL extension works great

## Disadvantages

1. ⚠️ **Two copies** - Original in Windows, working copy in WSL
2. ⚠️ **Manual sync** - Need to copy changes if you want to update Windows copy
3. ⚠️ **Disk space** - Uses space in both filesystems

## Backup Strategy

Keep Windows copy as backup:
- Original: `C:\Users\anupp\Documents\NexusAgent`
- Working: `~/projects/adaptive-research-agent` (in WSL)

To sync changes back to Windows:
```bash
cp -r ~/projects/adaptive-research-agent /mnt/c/Users/anupp/Documents/NexusAgent-updated
```

## Troubleshooting

### "Permission denied" errors
```bash
chmod +x deploy_to_native_linux.sh
chmod +x startup.sh
```

### Docker not working
```bash
sudo service docker start
```

### Port already in use
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Python not found
```bash
python3.12 --version
# If missing: sudo apt install python3.12 python3.12-venv
```

## Next Steps After Deployment

1. ✅ Run deployment script
2. ✅ Start server in WSL
3. ✅ Check health endpoint (should show 3 MCP servers)
4. ✅ Run Phase 4 tests
5. ✅ Verify all functionality works

## Quick Reference

```bash
# Deploy (from Windows)
deploy_to_linux.bat

# Start server (from WSL)
cd ~/projects/adaptive-research-agent
source venv/bin/activate
python backend/main.py

# Run tests (from WSL)
cd ~/projects/adaptive-research-agent
source venv/bin/activate
pytest backend/test_e2e_query_flow.py -v

# Check health (from anywhere)
curl http://localhost:8000/health
```

## Time Estimate

- **Deployment**: 5 minutes
- **First startup**: 30 seconds
- **Running tests**: 2-3 minutes
- **Total**: ~10 minutes to fully working system

## Ready?

Run this command to deploy:
```cmd
deploy_to_linux.bat
```

Or if you prefer manual control, follow the manual deployment steps above.
