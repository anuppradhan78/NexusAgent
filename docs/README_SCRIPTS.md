# How to Start/Stop the Application

## ⚠️ Important: WSL Native Deployment

This application runs in the **WSL native filesystem** at:
```
~/projects/adaptive-research-agent
```

## Quick Start

### From Windows (Easiest)

**Start:**
```cmd
startup_wsl.bat
```

**Stop:**
```cmd
shutdown_wsl.bat
```

### From WSL

**Start:**
```bash
wsl
cd ~/projects/adaptive-research-agent
./startup_wsl.sh
```

**Stop:**
```bash
wsl
~/projects/adaptive-research-agent/shutdown_wsl.sh
```

## First Time Setup

1. **Deploy to WSL** (if not done already):
   ```cmd
   deploy_to_linux.bat
   ```

2. **Configure API Keys**:
   ```cmd
   wsl nano ~/projects/adaptive-research-agent/.env
   ```
   
   Add:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. **Start Services**:
   ```cmd
   startup_wsl.bat
   ```

4. **Verify**:
   ```bash
   curl http://localhost:8000/health
   ```

## What Gets Started

1. **Redis** - Docker container on port 6379
2. **API Server** - FastAPI on port 8000
3. **MCP Servers** - 6 tools from 3 servers

## Health Check

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "mcp_servers_connected": 6
}
```

## Logs

View logs:
```cmd
wsl tail -f ~/projects/adaptive-research-agent/api_server.log
```

## ✅ Clean Setup

Old deprecated scripts have been removed. Only use the WSL scripts listed above.

## Documentation

- `docs/QUICK_START_WSL.md` - Detailed guide
- `docs/SCRIPTS_FIXED.md` - What was fixed
- `docs/DEPRECATED_SCRIPTS.md` - Why old scripts don't work
- `PROJECT_STATUS.md` - Project overview

## Troubleshooting

**Server won't start?**
```bash
wsl tail -f ~/projects/adaptive-research-agent/api_server.log
```

**Port in use?**
```cmd
shutdown_wsl.bat
startup_wsl.bat
```

**MCP tools not loading?**
Check health endpoint shows `mcp_servers_connected: 6`

---

**✅ Use `startup_wsl.bat` and `shutdown_wsl.bat` for correct operation!**
