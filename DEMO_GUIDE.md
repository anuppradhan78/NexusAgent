# Demo Guide - Adaptive Research Agent

This guide explains how to run the demo script for the Adaptive Research Agent.

## Overview

The `demo.py` script demonstrates the core features of the Adaptive Research Agent:
- Query processing with Claude AI
- Autonomous MCP tool usage
- Answer synthesis
- Report generation
- Query history tracking

## Prerequisites

**System must be running:**
```cmd
startup_wsl.bat
```

This starts:
- Redis (port 6379)
- API Server (port 8000)
- 6 MCP tools

## Running the Demo

Simply run:
```cmd
python demo.py
```

## What the Demo Does

### 1. Health Check ✅
Verifies the system is running:
- API server status
- Redis connection
- MCP servers connected (should show 6)

### 2. Research Query Demo
Submits two research queries:
1. "What is the Model Context Protocol?"
2. "Explain how REST APIs work"

**What you'll see:**
- Query processing time
- Query ID
- Synthesized answer from Claude
- Number of sources used
- Report generation (if enabled)

### 3. Query History
Retrieves past queries from the system.

### 4. Generated Reports
Lists all markdown reports that were generated.

## Understanding the Output

### Success Indicators
- ✓ Green checkmarks = successful operations
- ℹ Blue info messages = status updates
- ✗ Red X marks = errors (if any)

### Example Output
```
✓ API server is healthy
  Status: healthy
  Redis connected: True
  MCP servers connected: 6

✓ Query completed in 7.7 seconds
  Query ID: 0f469e48-ea73-4905-9489-7b0d05dee35d
  Processing time: 5679ms

✓ Found 2 reports
  - research_report_2025-11-25T04-36-29.md (1438 bytes)
```

## What Claude Does

When you submit a query, Claude:
1. Receives your question
2. Decides which MCP tools to use
3. Calls tools like:
   - `fetch_url` - Get web content
   - `send_api_request` - Make API calls
   - `generate_report` - Create markdown reports
4. Synthesizes a comprehensive answer
5. Returns results with sources

## Customizing the Demo

Edit `demo.py` to change queries:

```python
demo_query(
    query="Your custom question here",
    max_sources=2,
    include_report=True
)
```

## Troubleshooting

### "Cannot connect to API server"
**Solution:** Start the system first:
```cmd
startup_wsl.bat
```

### "Query timed out"
**Solution:** This is normal for complex queries. The system is working, just taking time to gather information.

### No reports found
**Solution:** Set `include_report=True` in queries to generate reports.

## Manual Testing

You can also test the API directly:

**Health Check:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

**Submit Query:**
```powershell
$body = @{
    query = "What is machine learning?"
    max_sources = 2
    include_report = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/research/query" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing
```

**List Reports:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/reports" -UseBasicParsing
```

## Viewing Generated Reports

Reports are saved in the `reports/` directory:

```cmd
wsl ls -la ~/projects/adaptive-research-agent/reports/
wsl cat ~/projects/adaptive-research-agent/reports/research_report_*.md
```

## System Architecture

```
Demo Script (demo.py)
    ↓
API Server (FastAPI)
    ↓
Agent Orchestrator
    ↓
Claude AI + MCP Tools
    ↓
Results + Reports
```

## Next Steps

After running the demo:

1. **View logs:**
   ```cmd
   wsl tail -f ~/projects/adaptive-research-agent/api_server.log
   ```

2. **Check reports:**
   ```cmd
   wsl ls ~/projects/adaptive-research-agent/reports/
   ```

3. **Try your own queries:**
   Edit `demo.py` and add your questions

4. **Stop the system:**
   ```cmd
   shutdown_wsl.bat
   ```

## Related Documentation

- [README.md](README.md) - Project overview
- [GETTING_STARTED.md](GETTING_STARTED.md) - Setup guide
- [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md) - Completion summary
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

---

**Tip:** The demo takes 10-100 seconds per query depending on complexity. This is normal as Claude is gathering information from multiple sources!
