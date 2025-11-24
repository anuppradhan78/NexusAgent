# Available Scripts

This document lists all available scripts for managing the Adaptive Research Agent.

## Startup & Shutdown

### startup.bat / startup.sh
**Purpose:** Start all required services (Redis + API Server)

**Usage:**
```bash
# Windows (automatically executable)
startup.bat

# Linux/Mac (first time only - make executable)
chmod +x startup.sh shutdown.sh
# Or run: bash setup_scripts.sh

# Then run:
./startup.sh
```

**What it does:**
1. Checks for virtual environment and .env file
2. Starts Redis using Docker
3. Starts the API server in a new window/background
4. Verifies all services are running

### shutdown.bat / shutdown.sh
**Purpose:** Stop all running services

**Usage:**
```bash
# Windows
shutdown.bat

# Linux/Mac
chmod +x shutdown.sh
./shutdown.sh
```

**What it does:**
1. Stops the API server (port 8000)
2. Stops Redis (port 6379 or Docker container)
3. Cleans up log files

### start_redis.bat
**Purpose:** Start only Redis (Windows only)

**Usage:**
```bash
start_redis.bat
```

**What it does:**
- Starts Redis using Docker on Windows
- Alternative to starting Redis manually

## Demo & Examples

### demo.py
**Purpose:** Comprehensive demonstration of all features

**Usage:**
```bash
python demo.py
```

**What it demonstrates:**
1. Autonomous query processing
2. Learning from feedback
3. Alert generation
4. Report generation
5. Self-improvement metrics
6. Scheduled queries
7. Multi-turn conversations
8. Query history

**Prerequisites:**
- Redis running on port 6379
- API server running on port 8000
- Environment variables configured

### Example Scripts (examples/)

Individual feature demonstrations:

```bash
# Alert engine
python examples/example_alert_usage.py

# History and reports
python examples/example_history_reports_usage.py

# Logging
python examples/example_logging_usage.py

# Metrics
python examples/example_metrics_usage.py

# Report generation
python examples/example_report_usage.py

# Scheduled queries
python examples/example_scheduler_usage.py

# Multi-turn conversations
python examples/example_session_usage.py
```

## Verification Scripts (backend/)

### verify_setup.py
**Purpose:** Verify installation and configuration

**Usage:**
```bash
cd backend
python verify_setup.py
```

**What it checks:**
- Python version
- Required packages installed
- Environment variables configured
- Redis connection
- MCP configuration

### verify_mcp.py
**Purpose:** Verify MCP server connections

**Usage:**
```bash
cd backend
python verify_mcp.py
```

**What it checks:**
- Anthropic MCP server connection
- Postman MCP server connection
- API key validity
- MCP tool availability

## Quick Reference

### First Time Setup
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Make scripts executable (Linux/Mac only)
chmod +x startup.sh shutdown.sh
# Or run: bash setup_scripts.sh

# 6. Start services
# Windows:
startup.bat
# Linux/Mac:
./startup.sh

# 7. Run demo
python demo.py
```

### Daily Usage
```bash
# Start services
startup.bat  # or ./startup.sh

# Run demo or examples
python demo.py

# Stop services when done
shutdown.bat  # or ./shutdown.sh
```

### Development Workflow
```bash
# Start services
startup.bat  # or ./startup.sh

# Run tests
cd backend
pytest -v

# Check specific functionality
python examples/example_metrics_usage.py

# View logs
# Windows: Check API Server window
# Linux/Mac: tail -f api_server.log

# Stop services
shutdown.bat  # or ./shutdown.sh
```

## Troubleshooting Scripts

### Check if services are running
```bash
# Check Redis
# Windows:
netstat -ano | findstr ":6379"
# Linux/Mac:
lsof -i :6379

# Check API Server
# Windows:
netstat -ano | findstr ":8000"
# Linux/Mac:
lsof -i :8000

# Or use curl
curl http://localhost:8000/health
```

### Manual cleanup
```bash
# Kill process on port 8000
# Windows:
for /f "tokens=5" %a in ('netstat -ano ^| findstr ":8000"') do taskkill /PID %a /F
# Linux/Mac:
kill -9 $(lsof -ti:8000)

# Kill process on port 6379
# Windows:
for /f "tokens=5" %a in ('netstat -ano ^| findstr ":6379"') do taskkill /PID %a /F
# Linux/Mac:
kill -9 $(lsof -ti:6379)

# Stop Docker containers
docker stop adaptive-agent-redis
docker rm adaptive-agent-redis
```

## Script Locations

```
.
├── startup.bat              # Windows startup script
├── startup.sh               # Unix/Linux/Mac startup script
├── shutdown.bat             # Windows shutdown script
├── shutdown.sh              # Unix/Linux/Mac shutdown script
├── start_redis.bat          # Windows Redis startup
├── demo.py                  # Comprehensive demo
├── backend/
│   ├── verify_setup.py      # Setup verification
│   └── verify_mcp.py        # MCP verification
└── examples/
    ├── example_alert_usage.py
    ├── example_history_reports_usage.py
    ├── example_logging_usage.py
    ├── example_metrics_usage.py
    ├── example_report_usage.py
    ├── example_scheduler_usage.py
    └── example_session_usage.py
```

## Related Documentation

- [README.md](README.md) - Main project documentation
- [GETTING_STARTED.md](GETTING_STARTED.md) - Setup guide
- [DEMO_GUIDE.md](DEMO_GUIDE.md) - Demo explanation
- [examples/README.md](examples/README.md) - Examples documentation

---

**Tip:** Always use the startup/shutdown scripts for the smoothest experience!
