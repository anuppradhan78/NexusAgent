# Getting Started with Adaptive Research Agent

This guide will help you set up and start using the Adaptive Research Agent in under 10 minutes.

## Quick Setup (5 minutes)

### Step 1: Install Prerequisites

**Python 3.11+**
```bash
python --version  # Should be 3.11 or higher
```

**Docker (for Redis)**
```bash
docker --version
```

**Node.js (for MCP servers)**
```bash
node --version
```

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd adaptive-research-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: ANTHROPIC_API_KEY
# Optional: POSTMAN_API_KEY
```

Example `.env` file:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
REDIS_URL=redis://localhost:6379
POSTMAN_API_KEY=PMAK-your-key-here
ALERT_CHANNELS=console
REPORT_OUTPUT_DIR=./backend/reports
```

### Step 4: Start Services

**Option A: Quick Start (Recommended)**

Use the startup script to start everything automatically:

```bash
# On Windows
startup.bat

# On Linux/Mac
chmod +x startup.sh shutdown.sh
./startup.sh
```

This will:
- Start Redis with Docker
- Start the API server
- Verify all services are running

**Option B: Manual Start**

**Terminal 1 - Start Redis:**
```bash
# Using Docker
docker run -d -p 6379:6379 redis/redis-stack:latest

# Or on Windows
start_redis.bat
```

**Terminal 2 - Start API Server:**
```bash
cd backend
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Run the Demo

```bash
python demo.py
```

🎉 **That's it!** The demo will showcase all features automatically.

### Step 6: Shutdown (When Done)

```bash
# On Windows
shutdown.bat

# On Linux/Mac
./shutdown.sh
```

## First Query (1 minute)

Try your first research query:

```bash
curl -X POST http://localhost:8000/api/research/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest developments in AI?",
    "max_sources": 3,
    "include_report": true
  }'
```

Or use Python:

```python
import httpx
import asyncio

async def first_query():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/research/query",
            json={
                "query": "What are the latest developments in AI?",
                "max_sources": 3,
                "include_report": True
            }
        )
        result = response.json()
        print(f"Answer: {result['synthesized_answer']}")
        print(f"Confidence: {result['confidence_score']}")

asyncio.run(first_query())
```

## Understanding the Response

A typical response looks like:

```json
{
  "query_id": "uuid-here",
  "session_id": "uuid-here",
  "synthesized_answer": "Based on recent sources...",
  "sources": [
    {
      "api_id": "api-1",
      "api_name": "Tech News API",
      "endpoint": "/latest",
      "verified": true,
      "priority_score": 0.85
    }
  ],
  "confidence_score": 0.87,
  "alert_triggered": false,
  "report_path": "./backend/reports/research_report_2025-11-23_10-30-45.md",
  "processing_time_ms": 2500,
  "similar_past_queries": []
}
```

## Key Concepts

### 1. Query Processing
The agent:
1. Parses your natural language query
2. Discovers relevant APIs from Postman
3. Calls multiple APIs in parallel
4. Synthesizes information using Claude
5. Returns a comprehensive answer with sources

### 2. Learning from Feedback
Provide feedback to improve results:

```bash
curl -X POST http://localhost:8000/api/research/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "your-query-id",
    "relevance_score": 0.9
  }'
```

The agent will:
- Store the feedback in memory
- Adjust confidence thresholds
- Prioritize successful API sources
- Refine similar future queries

### 3. Self-Improvement
Check how the agent is improving:

```bash
curl http://localhost:8000/api/metrics
```

Key metrics:
- **avg_relevance_score**: How useful results are (0.0-1.0)
- **improvement_trend**: Performance change over time
- **confidence_threshold**: Current quality bar
- **top_sources**: Best performing APIs

### 4. Automated Reports
Every query can generate a report:

```bash
# List reports
curl http://localhost:8000/api/reports

# Get specific report
curl http://localhost:8000/api/reports/{report_id}
```

Reports include:
- Executive summary
- Detailed findings
- Source citations
- Confidence assessment
- Metadata

### 5. Scheduled Queries
Set up recurring research:

```bash
curl -X POST http://localhost:8000/api/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Daily tech news summary",
    "schedule": "0 9 * * *",
    "max_sources": 5
  }'
```

Cron expressions:
- `0 9 * * *` - Daily at 9 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Every Monday at midnight

### 6. Multi-Turn Conversations
Have context-aware conversations:

```python
# First query
response1 = await client.post("/api/research/query", json={
    "query": "What is quantum computing?",
    "session_id": "my-session"
})

# Follow-up (uses context from first query)
response2 = await client.post("/api/research/query", json={
    "query": "How does it compare to classical computing?",
    "session_id": "my-session"
})
```

## Common Use Cases

### Research Assistant
```python
# Daily research on a topic
query = "Latest developments in renewable energy"
response = await client.post("/api/research/query", json={
    "query": query,
    "max_sources": 5,
    "include_report": True
})
```

### Monitoring & Alerts
```python
# Monitor for critical updates
response = await client.post("/api/research/query", json={
    "query": "Critical security vulnerabilities",
    "alert_enabled": True,
    "max_sources": 3
})

if response.json()["alert_triggered"]:
    print("⚠️ Critical information detected!")
```

### Scheduled Intelligence
```python
# Weekly market analysis
await client.post("/api/schedule", json={
    "query": "Weekly market trends analysis",
    "schedule": "0 9 * * 1",  # Every Monday at 9 AM
    "max_sources": 5,
    "alert_enabled": True
})
```

### Learning System
```python
# Submit query
result = await client.post("/api/research/query", json={
    "query": "AI trends"
})

# Provide feedback
await client.post("/api/research/feedback", json={
    "query_id": result.json()["query_id"],
    "relevance_score": 0.9
})

# Check improvement
metrics = await client.get("/api/metrics")
print(f"Improvement: {metrics.json()['improvement_trend']}")
```

## Troubleshooting

### "Cannot connect to API server"
**Solution:**
```bash
cd backend
python main.py
```
Ensure server is running on port 8000.

### "Redis connection failed"
**Solution:**
```bash
docker run -d -p 6379:6379 redis/redis-stack:latest
```
Ensure Redis is running with RediSearch module.

### "ANTHROPIC_API_KEY not configured"
**Solution:**
1. Get API key from https://console.anthropic.com/
2. Add to `.env` file:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

### "MCP server connection failed"
**Solution:**
1. Ensure Node.js is installed
2. Check `mcp.json` configuration
3. Verify API keys in `.env`

### Slow query processing
**Solution:**
- Reduce `max_sources` (try 2-3 instead of 5)
- Check network connectivity
- Verify MCP servers are responding

## Next Steps

### 1. Explore Examples
```bash
# Run individual feature examples
python examples/example_metrics_usage.py
python examples/example_scheduler_usage.py
python examples/example_session_usage.py
```

### 2. Read Documentation
- [README.md](README.md) - Full project documentation
- [Demo Guide](docs/DEMO_GUIDE.md) - Detailed demo explanation
- [Examples README](examples/README.md) - Usage examples
- [Design Document](.kiro/specs/adaptive-research-agent/design.md) - Architecture

### 3. Customize Configuration
Edit `.env` to customize:
- Alert channels (console, file, webhook)
- Report output directory
- Learning rate
- Confidence threshold
- Memory settings

### 4. Integrate into Your Application
```python
import httpx

class ResearchClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def research(self, query: str):
        response = await self.client.post(
            f"{self.base_url}/api/research/query",
            json={"query": query}
        )
        return response.json()
    
    async def feedback(self, query_id: str, score: float):
        await self.client.post(
            f"{self.base_url}/api/research/feedback",
            json={"query_id": query_id, "relevance_score": score}
        )

# Usage
client = ResearchClient()
result = await client.research("What is machine learning?")
await client.feedback(result["query_id"], 0.9)
```

### 5. Monitor Performance
```bash
# Watch metrics in real-time
watch -n 5 'curl -s http://localhost:8000/api/metrics | python -m json.tool'

# View logs
curl "http://localhost:8000/api/logs?limit=50" | python -m json.tool

# Check query history
curl "http://localhost:8000/api/research/history?limit=10" | python -m json.tool
```

## Best Practices

### 1. Provide Feedback
Always provide feedback to help the agent learn:
```python
# Good: Provide feedback
result = await research(query)
await feedback(result["query_id"], 0.85)

# Bad: No feedback (agent can't learn)
result = await research(query)
```

### 2. Use Sessions for Conversations
```python
# Good: Use session for related queries
session_id = "my-conversation"
await research("What is AI?", session_id=session_id)
await research("How does it work?", session_id=session_id)

# Bad: No session (loses context)
await research("What is AI?")
await research("How does it work?")  # No context
```

### 3. Enable Reports for Important Queries
```python
# Good: Generate report for important research
await research(query, include_report=True)

# OK: Skip reports for quick queries
await research(query, include_report=False)
```

### 4. Monitor Improvement Trends
```python
# Check metrics regularly
metrics = await get_metrics()
if metrics["improvement_trend"] < 0:
    print("⚠️ Agent needs more feedback!")
```

## Support & Resources

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Issues**: Check server logs and Redis connection
- **API Reference**: See [README.md](README.md#-api-endpoints)

## Quick Reference

```bash
# Start services
docker run -d -p 6379:6379 redis/redis-stack:latest
cd backend && python main.py

# Run demo
python demo.py

# Submit query
curl -X POST http://localhost:8000/api/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question"}'

# Provide feedback
curl -X POST http://localhost:8000/api/research/feedback \
  -H "Content-Type: application/json" \
  -d '{"query_id": "id", "relevance_score": 0.9}'

# Check metrics
curl http://localhost:8000/api/metrics

# View history
curl http://localhost:8000/api/research/history

# List reports
curl http://localhost:8000/api/reports
```

---

**Ready to start?** Run `python demo.py` and watch the agent in action! 🚀
