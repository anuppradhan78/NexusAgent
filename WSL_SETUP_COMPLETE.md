# WSL Setup - Ready to Run

## 🎯 Quick Start

I've created everything you need to migrate to WSL with a single command!

### Step 1: Run Migration (One Time Setup)

Double-click or run:
```
migrate_to_wsl.bat
```

This will:
- ✅ Install Python 3.11 in WSL
- ✅ Install Node.js 20 in WSL
- ✅ Set up Docker in WSL
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Build all 3 MCP servers (Postman, Memory, Research Tools)

**Time:** 5-10 minutes

### Step 2: Start the Application

After migration completes, run:
```
wsl_start.bat
```

This will:
- ✅ Start Redis in Docker
- ✅ Start the API server in a new terminal
- ✅ Verify services are running

### Step 3: Run Tests

To run Phase 4 tests:
```
wsl_test.bat
```

### Step 4: Stop Everything

When done:
```
wsl_stop.bat
```

## 📁 Files Created

| File | Purpose |
|------|---------|
| `migrate_to_wsl.bat` | One-time setup - installs everything in WSL |
| `wsl_start.bat` | Start Redis and API server |
| `wsl_stop.bat` | Stop all services |
| `wsl_test.bat` | Run Phase 4 tests |
| `setup_wsl.sh` | WSL setup script (called by migrate_to_wsl.bat) |

## 🔧 Manual Commands (if needed)

If you prefer to run commands manually in WSL:

### Open WSL
```powershell
wsl
```

### Navigate to Project
```bash
cd /mnt/c/Users/anupp/Documents/NexusAgent
```

### Start Redis
```bash
docker run -d --name redis-research-agent -p 6379:6379 redis/redis-stack:latest
```

### Start API Server
```bash
source venv/bin/activate
python backend/main.py
```

### Run Tests
```bash
source venv/bin/activate
pytest backend/test_e2e_query_flow.py -v
```

### Check Health
```bash
curl http://localhost:8000/health
```

## ✅ What Gets Fixed in WSL

Moving to WSL solves the Windows/MCP compatibility issues:

| Issue | Windows | WSL |
|-------|---------|-----|
| MCP stdio communication | ❌ Hangs | ✅ Works |
| Node.js subprocess spawning | ❌ Unreliable | ✅ Reliable |
| Docker performance | ⚠️ Slower | ✅ Fast |
| Unix scripts | ❌ Need conversion | ✅ Native |

## 🎯 Phase 4 Testing Plan

Once WSL setup is complete, we'll continue with Phase 4:

- [ ] **Task 11.1**: Test complete query flow ✅ (test file ready)
- [ ] **Task 11.2**: Test history retrieval
- [ ] **Task 11.3**: Test report listing and retrieval
- [ ] **Task 11.4**: Test error handling
- [ ] **Task 11.5**: Test health endpoint
- [ ] **Task 12.1**: Update README.md
- [ ] **Task 12.2**: Update demo script
- [ ] **Task 12.3**: Verify .env.example

## 🐛 Troubleshooting

### "Docker permission denied"
```bash
wsl
sudo usermod -aG docker $USER
newgrp docker
```

### "Port 8000 already in use"
```bash
wsl
sudo lsof -i :8000
sudo kill -9 <PID>
```

### "Python not found"
```bash
wsl
python3.11 --version
# If missing, run: sudo apt install python3.11
```

### "Node not found"
```bash
wsl
node --version
# If missing, run setup again: ./setup_wsl.sh
```

## 📊 Expected Output

After running `wsl_start.bat`, you should see:

```
[1/3] Starting Redis...
Redis started successfully

[2/3] Starting API Server...
Opening new WSL terminal for API server...

[3/3] Waiting for server to start...

================================================================================
  Startup Complete!
================================================================================

Services:
  - Redis:      Running on port 6379
  - API Server: Running on http://localhost:8000
```

Then in the API server terminal:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
{"event": "Starting Adaptive Research Agent...", "timestamp": "...", "level": "info"}
{"event": "Claude client initialized", "timestamp": "...", "level": "info"}
{"event": "Connecting to MCP servers...", "timestamp": "...", "level": "info"}
{"event": "Connected to postman MCP server", "timestamp": "...", "level": "info"}
{"event": "Connected to memory MCP server", "timestamp": "...", "level": "info"}
{"event": "Connected to research MCP server", "timestamp": "...", "level": "info"}
{"event": "MCP Tool Router initialized with 6 tools", "timestamp": "...", "level": "info"}
{"event": "Adaptive Research Agent started successfully", "timestamp": "...", "level": "info"}
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🚀 Ready to Go!

Everything is set up. Just run:

1. `migrate_to_wsl.bat` (one time)
2. `wsl_start.bat` (to start)
3. `wsl_test.bat` (to test)
4. `wsl_stop.bat` (to stop)

**Let me know when you're ready to run the migration!**
