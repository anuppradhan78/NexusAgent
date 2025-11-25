# Deprecated Scripts

The following scripts are **DEPRECATED** and should NOT be used with the WSL native deployment:

## ❌ Deprecated Files

- `startup.bat` - Designed for Windows filesystem, not WSL native
- `startup.sh` - Designed for Windows filesystem, not WSL native
- `shutdown.bat` - Designed for Windows filesystem, not WSL native
- `shutdown.sh` - Designed for Windows filesystem, not WSL native
- `setup_scripts.sh` - Not needed for WSL deployment
- `start_redis.bat` - Use Docker commands directly or startup scripts
- `demo.py` - Needs updating for WSL paths

## ✅ Use Instead

### For WSL Native Deployment

**From Windows:**
- Start: `startup_wsl.bat`
- Stop: `shutdown_wsl.bat`

**From WSL:**
- Start: `~/projects/adaptive-research-agent/startup_wsl.sh`
- Stop: `~/projects/adaptive-research-agent/shutdown_wsl.sh`

## Why These Scripts Are Deprecated

The application now runs in the **WSL native filesystem** at `~/projects/adaptive-research-agent` instead of the Windows filesystem at `/mnt/c/Users/.../NexusAgent`.

The old scripts:
1. Point to wrong file paths (Windows filesystem)
2. Use wrong Python virtual environment
3. Don't work with MCP servers (stdio issues)
4. Have slower performance

## Migration

If you were using the old scripts, switch to the new ones:

**Old:**
```cmd
startup.bat
```

**New:**
```cmd
startup_wsl.bat
```

See `QUICK_START_WSL.md` for complete instructions.
