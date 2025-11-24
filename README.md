# Adaptive Research Agent

An autonomous, self-improving AI research system that gathers information from real-time data sources via APIs, learns what's relevant over time, and takes meaningful action without human intervention.

## 🌟 Key Features

- **Autonomous Operation**: Self-improving loops that continuously enhance performance
- **Context-Aware Learning**: Redis vector-based memory for semantic search and pattern recognition
- **Adaptive Query Refinement**: Learns from feedback to improve future queries
- **Real-Time API Monitoring**: Intelligent data synthesis from multiple sources
- **Proactive Alerting**: Automatic detection and notification of critical information
- **Automated Report Generation**: Comprehensive markdown reports with citations

## 🏗️ Architecture

### Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **AI Integration**: Anthropic Claude via Model Context Protocol (MCP)
- **API Discovery**: Postman Public API Network via MCP
- **Memory Store**: Redis with RediSearch for vector similarity search
- **Async Processing**: asyncio for parallel API execution
- **Logging**: Structured logging with structlog

### Core Components

1. **Agent Orchestrator** (`agent_orchestrator.py`)
   - Main processing pipeline coordinating all operations
   - Query intent parsing using Claude
   - Parallel API discovery and execution
   - Information synthesis with source citations

2. **MCP Client** (`mcp_client.py`)
   - Connection to Anthropic Claude for reasoning
   - Integration with Postman API Network
   - Retry logic with exponential backoff

3. **Memory Store** (`memory_store.py`)
   - Redis vector storage with 1024-dimensional embeddings
   - Semantic search for similar past queries
   - Automatic 30-day expiration for stale entries

4. **FastAPI Server** (`main.py`)
   - REST API endpoints for query processing
   - Health checks and monitoring
   - Structured logging with request IDs

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Redis with RediSearch module
- Node.js (for MCP servers)
- Anthropic API key
- Postman API key (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/adaptive-research-agent.git
   cd adaptive-research-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Start Redis with RediSearch**
   ```bash
   docker run -d -p 6379:6379 redis/redis-stack:latest
   ```
   
   Or on Windows, use the provided batch file:
   ```bash
   start_redis.bat
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

   Required variables:
   ```env
   ANTHROPIC_API_KEY=sk-ant-...
   REDIS_URL=redis://localhost:6379
   POSTMAN_API_KEY=PMAK-...  # Optional
   ```

### Running the Agent

**Quick Start (Recommended):**

Use the startup scripts to start all services automatically:

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

**Manual Start:**

1. **Start Redis**
   ```bash
   docker run -d -p 6379:6379 redis/redis-stack:latest
   # Or on Windows: start_redis.bat
   ```

2. **Start the API server**
   ```bash
   cd backend
   python main.py
   ```

3. **Check health endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

**Run the Demo:**

```bash
python demo.py
```

This will demonstrate all key features:
- Autonomous query processing
- Learning from feedback
- Alert generation
- Report creation
- Self-improvement metrics
- Scheduled queries
- Multi-turn conversations

**Process a Research Query:**

```bash
curl -X POST http://localhost:8000/api/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest AI trends?", "max_sources": 5}'
```

**Shutdown:**

```bash
# On Windows
shutdown.bat

# On Linux/Mac
./shutdown.sh
```

## 🧪 Testing

Run the test suite:

```bash
cd backend
pytest -v
```

Run specific test files:
```bash
pytest test_agent_orchestrator.py -v
pytest test_mcp_client.py -v
pytest test_memory_store.py -v
```

## 📋 Development Roadmap

### ✅ Phase 1: Foundation (Complete)
- [x] MCP client for Anthropic and Postman
- [x] Redis vector memory store
- [x] FastAPI server with health endpoint
- [x] Basic infrastructure testing

### ✅ Phase 2: Core Agent Logic (Complete)
- [x] Agent orchestrator with query processing pipeline
- [x] Intent parsing using Claude
- [x] API discovery from Postman
- [x] Parallel information gathering
- [x] Result synthesis with citations

### ✅ Phase 3: Learning & Improvement (Complete)
- [x] Learning engine for query refinement
- [x] Feedback system for relevance scoring
- [x] Confidence threshold adaptation
- [x] Source prioritization based on performance

### ✅ Phase 4: Actions & Observability (Complete)
- [x] Alert engine for critical information
- [x] Report generator for markdown reports
- [x] Metrics endpoint for self-improvement tracking
- [x] History and reports API endpoints

### ✅ Phase 5: Advanced Features (Complete)
- [x] Scheduled recurring queries
- [x] Multi-turn conversation support
- [x] Comprehensive logging and tracing
- [x] Demo script and documentation

## 🏛️ Architecture Principles

### Spec-Driven Development

This project follows a rigorous spec-driven development methodology:

1. **Requirements**: EARS-compliant acceptance criteria with INCOSE quality rules
2. **Design**: Comprehensive architecture with correctness properties
3. **Implementation**: Task-based development with property-based testing
4. **Verification**: Continuous validation against specifications

### Correctness Properties

The system is built around formal correctness properties that ensure:

- **Query Processing Completeness**: All queries return synthesized answers with sources
- **Memory Persistence**: Round-trip consistency for stored queries
- **Parallel Execution**: Concurrent API calls within timeout constraints
- **Graceful Degradation**: Continued operation despite partial failures

## 📊 API Endpoints

### Health Check
```
GET /health
```
Returns service status and configuration validation.

### Research Query
```
POST /api/research/query
{
  "query": "What are the latest AI trends?",
  "session_id": "optional-uuid",
  "max_sources": 5,
  "include_report": true,
  "alert_enabled": true
}
```
Returns synthesized answer with sources, confidence score, and optional report.

### Feedback Submission
```
POST /api/research/feedback
{
  "query_id": "uuid",
  "relevance_score": 0.9,
  "feedback_notes": "Very helpful"
}
```
Submit feedback to improve future queries through learning.

### Query History
```
GET /api/research/history?limit=50&offset=0&min_relevance=0.0
```
Retrieve past queries with pagination and filtering.

### Metrics
```
GET /api/metrics
```
Returns self-improvement metrics, learning statistics, and performance trends.

### Reports
```
GET /api/reports
GET /api/reports/{report_id}
```
List and retrieve generated research reports.

### Scheduled Queries
```
POST /api/schedule
GET /api/schedule
GET /api/schedule/{schedule_id}
PUT /api/schedule/{schedule_id}
DELETE /api/schedule/{schedule_id}
```
Create and manage recurring scheduled queries.

### Sessions (Multi-Turn Conversations)
```
POST /api/session
GET /api/session/{session_id}/history
DELETE /api/session/{session_id}
```
Manage conversation sessions for context-aware interactions.

### Logs
```
GET /api/logs?level=INFO&limit=100&request_id=xxx
```
Query structured application logs with filtering.

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic API key for Claude |
| `REDIS_URL` | Yes | `redis://localhost:6379` | Redis connection URL |
| `REDIS_PASSWORD` | No | - | Redis password if required |
| `POSTMAN_API_KEY` | No | - | Postman API key for API discovery |
| `ALERT_CHANNELS` | No | `console` | Alert delivery channels |
| `REPORT_OUTPUT_DIR` | No | `./reports` | Directory for generated reports |
| `LEARNING_RATE` | No | `0.1` | Learning rate for threshold adjustment |
| `CONFIDENCE_THRESHOLD_INITIAL` | No | `0.5` | Initial confidence threshold |

### MCP Configuration

MCP servers are configured in `mcp.json`:

```json
{
  "mcpServers": {
    "anthropic": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-anthropic"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      }
    },
    "postman": {
      "command": "npx",
      "args": ["-y", "@postman/mcp-server"],
      "env": {
        "POSTMAN_API_KEY": "${POSTMAN_API_KEY}"
      }
    }
  }
}
```


## 💡 Usage Examples

### Quick Start Demo

Run the comprehensive demo to see all features in action:

```bash
python demo.py
```

This demonstrates:
1. **Autonomous Query Processing** - Submit natural language queries
2. **Learning from Feedback** - Provide relevance scores to improve results
3. **Alert Generation** - Automatic detection of critical information
4. **Report Generation** - Comprehensive markdown reports with citations
5. **Self-Improvement Metrics** - Track performance improvements over time
6. **Scheduled Queries** - Set up recurring research tasks
7. **Multi-Turn Conversations** - Context-aware follow-up questions

### Python Client Example

```python
import httpx
import asyncio

async def research_query():
    async with httpx.AsyncClient() as client:
        # Submit a research query
        response = await client.post(
            "http://localhost:8000/api/research/query",
            json={
                "query": "What are the latest developments in quantum computing?",
                "max_sources": 5,
                "include_report": True
            }
        )
        
        result = response.json()
        print(f"Answer: {result['synthesized_answer']}")
        print(f"Confidence: {result['confidence_score']}")
        print(f"Sources: {len(result['sources'])}")
        
        # Provide feedback
        await client.post(
            "http://localhost:8000/api/research/feedback",
            json={
                "query_id": result['query_id'],
                "relevance_score": 0.9
            }
        )

asyncio.run(research_query())
```

### Command Line Examples

```bash
# Submit a research query
curl -X POST http://localhost:8000/api/research/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest AI breakthroughs?",
    "max_sources": 3,
    "include_report": true
  }'

# Provide feedback
curl -X POST http://localhost:8000/api/research/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "your-query-id",
    "relevance_score": 0.85
  }'

# Get metrics
curl http://localhost:8000/api/metrics

# View query history
curl "http://localhost:8000/api/research/history?limit=10"

# Create scheduled query
curl -X POST http://localhost:8000/api/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Daily tech news summary",
    "schedule": "0 9 * * *",
    "max_sources": 5
  }'
```

### Example Scripts

The `examples/` directory contains detailed usage examples:

- `example_alert_usage.py` - Alert generation and notification
- `example_history_reports_usage.py` - Query history and reports
- `example_logging_usage.py` - Logging and observability
- `example_metrics_usage.py` - Metrics and self-improvement
- `example_report_usage.py` - Report generation
- `example_scheduler_usage.py` - Scheduled queries
- `example_session_usage.py` - Multi-turn conversations

Run any example:
```bash
python examples/example_metrics_usage.py
```

## 🔍 How It Works

### 1. Query Processing Pipeline

```
User Query → Intent Parsing (Claude) → Memory Search (Redis) 
→ Query Refinement (Learning Engine) → API Discovery (Postman)
→ Parallel API Calls → Information Synthesis (Claude)
→ Alert Evaluation → Report Generation → Memory Storage
```

### 2. Learning Loop

```
Query Results → User Feedback → Relevance Score Update
→ Pattern Analysis → Confidence Threshold Adjustment
→ Source Prioritization → Query Refinement Rules
→ Improved Future Queries
```

### 3. Self-Improvement Metrics

The agent tracks:
- **Average Relevance Score**: How useful results are to users
- **Confidence Score**: Agent's certainty in its answers
- **Improvement Trend**: Performance change over time
- **Source Performance**: Which APIs provide best results
- **Query Efficiency**: Processing time and resource usage

## 🧪 Testing

### Run All Tests
```bash
cd backend
pytest -v
```

### Run Specific Test Categories
```bash
# Unit tests
pytest tests/test_agent_orchestrator.py -v
pytest tests/test_learning_engine.py -v
pytest tests/test_memory_store.py -v

# Integration tests
pytest tests/test_learning_integration.py -v
pytest tests/test_e2e_query_flow.py -v

# End-to-end tests
pytest tests/test_task18_alerts_reports_integration.py -v
```

### Test Coverage
```bash
pytest --cov=backend --cov-report=html
```

## 🐛 Troubleshooting

### Redis Connection Issues
```
Error: Could not connect to Redis
```
**Solution**: Ensure Redis is running with RediSearch module:
```bash
docker run -d -p 6379:6379 redis/redis-stack:latest
```

### MCP Connection Issues
```
Error: MCP server connection failed
```
**Solution**: 
1. Check that Node.js is installed
2. Verify API keys in `.env` file
3. Check `mcp.json` configuration
4. Try running: `npx -y @anthropic-ai/mcp-server-anthropic`

### API Server Not Starting
```
Error: Address already in use
```
**Solution**: Kill existing process on port 8000:
```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Missing Dependencies
```
ModuleNotFoundError: No module named 'xxx'
```
**Solution**: Reinstall dependencies:
```bash
pip install -r backend/requirements.txt
```

## 📚 Documentation

- [Requirements Document](.kiro/specs/adaptive-research-agent/requirements.md) - Detailed requirements
- [Design Document](.kiro/specs/adaptive-research-agent/design.md) - System architecture
- [Implementation Tasks](.kiro/specs/adaptive-research-agent/tasks.md) - Development roadmap
- [Examples README](examples/README.md) - Usage examples
- [Project Organization](docs/PROJECT_ORGANIZATION.md) - Code structure

## 🙏 Acknowledgments

- Built for the Context Engineering Challenge
- Uses Anthropic's Claude via Model Context Protocol
- Integrates with Postman's Public API Network
- Inspired by autonomous agent research and self-improving systems

## 📧 Contact

Anup Pradhan
Chief Architect
AImitari Medtech Pte. Ltd.  


---

**Status**: All Phases Complete - Fully Functional Autonomous Research Agent ✅


