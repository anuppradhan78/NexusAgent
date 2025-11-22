# Adaptive Research Agent - Backend

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp ../.env.example .env
```

Required environment variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `POSTMAN_API_KEY`: Your Postman API key
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379)

### 3. Start Redis

The agent requires Redis with RediSearch module:

```bash
docker run -d -p 6379:6379 redis/redis-stack:latest
```

### 4. Run the Server

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Health

```bash
curl http://localhost:8000/health
```

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── mcp_client.py       # MCP client for Anthropic and Postman
├── memory_store.py     # Redis vector memory store
├── agent_orchestrator.py # Core agent logic
├── learning_engine.py  # Self-improvement engine
├── alert_engine.py     # Alert generation
├── report_generator.py # Report generation
└── models.py           # Pydantic data models
```

## MCP Configuration

MCP servers are configured in `../mcp.json`:
- Anthropic MCP: Claude access for reasoning and synthesis
- Postman MCP: Public API Network access for data gathering

## Development

Run tests:
```bash
pytest
```

Run with auto-reload:
```bash
uvicorn main:app --reload
```
