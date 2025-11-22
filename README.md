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

1. **Start the FastAPI server**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Check health endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Process a research query** (coming in Phase 2)
   ```bash
   curl -X POST http://localhost:8000/api/research/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the latest AI trends?", "max_sources": 5}'
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

### 🚧 Phase 3: Learning & Improvement (In Progress)
- [ ] Learning engine for query refinement
- [ ] Feedback system for relevance scoring
- [ ] Confidence threshold adaptation
- [ ] Source prioritization based on performance

### 📅 Phase 4: Actions & Observability
- [ ] Alert engine for critical information
- [ ] Report generator for markdown reports
- [ ] Metrics endpoint for self-improvement tracking
- [ ] History and reports API endpoints

### 📅 Phase 5: Advanced Features
- [ ] Scheduled recurring queries
- [ ] Multi-turn conversation support
- [ ] Comprehensive logging and tracing
- [ ] Demo script and documentation

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

### Research Query (Phase 2+)
```
POST /api/research/query
{
  "query": "What are the latest AI trends?",
  "session_id": "optional-uuid",
  "max_sources": 5,
  "include_report": true
}
```

### Feedback Submission (Phase 3+)
```
POST /api/research/feedback
{
  "query_id": "uuid",
  "relevance_score": 0.9,
  "feedback_notes": "Very helpful"
}
```

### Metrics (Phase 4+)
```
GET /api/metrics
```
Returns self-improvement metrics and learning statistics.

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

**Status**: Phase 2 Complete - Agent Orchestrator Implemented ✅


