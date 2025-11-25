# Quick Start Guide - WSL Native Deployment

## Overview

The Adaptive Research Agent now runs in the **WSL native filesystem** at:
```
~/projects/adaptive-research-agent
```

This resolves all MCP stdio communication issues and provides better performance.

## Starting the Application

### From Windows (Recommended)

```cmd
startup_wsl.bat
```

This will:
1. Start Redis in Docker
2. Start the API server in WSL
3. Show health status

### From WSL

```bash
wsl
cd ~/projects/adaptive-research-agent
./startup_wsl.sh
```

## Stopping the Application

### From Windows

```cmd
shutdown_wsl.bat
```

### From WSL

```bash
wsl
~/projects/adaptive-research-agent/shutdown_wsl.sh
```

## Configuration

### Add API Keys

**From Windows:**
```cmd
wsl nano ~/projects/adaptive-research-agent/.env
```

**From WSL:**
```bash
nano ~/projects/adaptive-research-agent/.env
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Accessing the Application

The API server is accessible from both Windows and WSL:

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "redis_connected": true,
  "mcp_servers_connected": 6
}
```

## Viewing Logs

**From Windows:**
```cmd
wsl tail -f ~/projects/adaptive-research-agent/api_server.log
```

**From WSL:**
```bash
tail -f ~/projects/adaptive-research-agent/api_server.log
```

## File Locations

| Component | Location |
|-----------|----------|
| Project Root | `~/projects/adaptive-research-agent` |
| Backend Code | `~/projects/adaptive-research-agent/backend/` |
| MCP Servers | `~/projects/adaptive-research-agent/mcp-servers/` |
| Logs | `~/projects/adaptive-research-agent/api_server.log` |
| Config | `~/projects/adaptive-research-agent/.env` |

## Editing Files

### From Windows with VS Code

```cmd
code ~/projects/adaptive-research-agent
```

Or open WSL in VS Code:
```cmd
wsl code ~/projects/adaptive-research-agent
```

### From WSL

```bash
cd ~/projects/adaptive-research-agent
nano backend/main.py
```

## Troubleshooting

### Server Won't Start

1. Check if Redis is running:
   ```bash
   docker ps | grep redis
   ```

2. Check logs:
   ```bash
   wsl tail -f ~/projects/adaptive-research-agent/api_server.log
   ```

3. Verify .env file exists:
   ```bash
   wsl cat ~/projects/adaptive-research-agent/.env
   ```

### Port Already in Use

Stop existing processes:
```bash
wsl bash ~/projects/adaptive-research-agent/shutdown_wsl.sh
```

### MCP Tools Not Loading

Check health endpoint:
```bash
curl http://localhost:8000/health
```

Should show `mcp_servers_connected: 6`

## Old Scripts (Deprecated)

The following scripts are **deprecated** and should NOT be used:
- ❌ `startup.bat` - Points to Windows filesystem
- ❌ `startup.sh` - Points to Windows filesystem  
- ❌ `shutdown.bat` - Points to Windows filesystem
- ❌ `shutdown.sh` - Points to Windows filesystem

**Use the new WSL scripts instead:**
- ✅ `startup_wsl.bat` (from Windows)
- ✅ `shutdown_wsl.bat` (from Windows)
- ✅ `startup_wsl.sh` (from WSL)
- ✅ `shutdown_wsl.sh` (from WSL)

## Testing

Once the server is running with API keys configured:

```bash
# From Windows
wsl bash -c "cd ~/projects/adaptive-research-agent && source venv/bin/activate && pytest backend/test_e2e_query_flow.py -v"
```

## Summary

**✅ DO:**
- Use `startup_wsl.bat` / `shutdown_wsl.bat` from Windows
- Edit files in `~/projects/adaptive-research-agent` (WSL native)
- Access API at `http://localhost:8000` from Windows or WSL

**❌ DON'T:**
- Use old `startup.bat` / `shutdown.bat` scripts
- Edit files in `/mnt/c/Users/.../NexusAgent` (Windows filesystem)
- Try to run MCP servers from Windows filesystem

The application now runs entirely in WSL native filesystem for optimal performance and compatibility!
