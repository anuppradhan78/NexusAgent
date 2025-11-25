# Scripts Fixed for WSL Native Deployment ✅

## Problem Identified

The original scripts (`startup.bat`, `startup.sh`, `shutdown.bat`, `shutdown.sh`, `demo.py`) were designed for the Windows filesystem and are **incompatible** with the WSL native deployment at `~/projects/adaptive-research-agent`.

## Issues with Old Scripts

1. **Wrong Paths** - Point to `/mnt/c/Users/.../NexusAgent` instead of `~/projects/adaptive-research-agent`
2. **Wrong Virtual Environment** - Use Windows venv instead of WSL venv
3. **MCP Compatibility** - Don't work with MCP servers due to stdio issues on Windows filesystem
4. **Performance** - Slower due to Windows/WSL filesystem translation layer

## New Scripts Created

### ✅ For Windows Users

| Script | Purpose | Usage |
|--------|---------|-------|
| `startup_wsl.bat` | Start all services | Double-click or `startup_wsl.bat` |
| `shutdown_wsl.bat` | Stop all services | Double-click or `shutdown_wsl.bat` |

### ✅ For WSL Users

| Script | Purpose | Usage |
|--------|---------|-------|
| `startup_wsl.sh` | Start all services | `~/projects/adaptive-research-agent/startup_wsl.sh` |
| `shutdown_wsl.sh` | Stop all services | `~/projects/adaptive-research-agent/shutdown_wsl.sh` |

## What the New Scripts Do

### startup_wsl.sh / startup_wsl.bat

1. ✅ Navigate to `~/projects/adaptive-research-agent` (WSL native)
2. ✅ Check for virtual environment
3. ✅ Check for .env configuration
4. ✅ Start Redis in Docker
5. ✅ Start API server in background
6. ✅ Verify services are running
7. ✅ Display health status

### shutdown_wsl.sh / shutdown_wsl.bat

1. ✅ Stop API server (port 8000)
2. ✅ Stop Redis Docker container
3. ✅ Clean up log files
4. ✅ Confirm shutdown

## Quick Start

### From Windows

```cmd
REM Start services
startup_wsl.bat

REM Stop services
shutdown_wsl.bat
```

### From WSL

```bash
# Start services
wsl
cd ~/projects/adaptive-research-agent
./startup_wsl.sh

# Stop services
~/projects/adaptive-research-agent/shutdown_wsl.sh
```

## Verification

After starting, verify everything works:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "mcp_servers_connected": 6
}
```

## Files Updated

### Created
- ✅ `startup_wsl.sh` - WSL startup script
- ✅ `shutdown_wsl.sh` - WSL shutdown script
- ✅ `startup_wsl.bat` - Windows wrapper for startup
- ✅ `shutdown_wsl.bat` - Windows wrapper for shutdown
- ✅ `QUICK_START_WSL.md` - Complete usage guide
- ✅ `DEPRECATED_SCRIPTS.md` - List of old scripts
- ✅ `SCRIPTS_FIXED.md` - This document

### Deprecated (Do Not Use)
- ❌ `startup.bat`
- ❌ `startup.sh`
- ❌ `shutdown.bat`
- ❌ `shutdown.sh`
- ❌ `setup_scripts.sh`
- ❌ `start_redis.bat`
- ❌ `demo.py` (needs updating)

## Demo Script Status

The `demo.py` script also needs updating because it:
1. Assumes API endpoints that may not exist yet
2. Uses features not implemented in current version
3. Needs to be run from WSL with correct paths

**Recommendation:** Create a simpler demo script or update demo.py to match actual API implementation.

## Documentation

See these files for more information:
- `QUICK_START_WSL.md` - How to use the new scripts
- `DEPRECATED_SCRIPTS.md` - Why old scripts don't work
- `PROJECT_STATUS.md` - Overall project status
- `docs/MCP_FIX_COMPLETE.md` - MCP connection fix details

## Summary

✅ **All scripts are now correct for WSL native deployment**
✅ **Use `startup_wsl.bat` / `shutdown_wsl.bat` from Windows**
✅ **Application runs at `~/projects/adaptive-research-agent`**
✅ **6 MCP tools working correctly**
✅ **No more stdio communication issues**

The Adaptive Research Agent is ready to use!
