# Project Organization

This document describes the organization and structure of the Adaptive Research Agent project.

## Directory Structure

```
NexusAgent/
├── .kiro/                          # Kiro IDE configuration
│   └── specs/                      # Feature specifications
│       └── adaptive-research-agent/
│           ├── requirements.md     # Requirements document
│           ├── design.md          # Design document
│           └── tasks.md           # Implementation tasks
│
├── backend/                        # Backend application
│   ├── *.py                       # Core application modules
│   ├── tests/                     # Test suite
│   │   ├── test_*.py             # Unit and integration tests
│   │   └── __init__.py
│   ├── reports/                   # Generated research reports
│   ├── requirements.txt           # Python dependencies
│   └── __pycache__/              # Python cache
│
├── docs/                          # Documentation
│   ├── README.md                  # Documentation index
│   ├── TASK_*_*.md               # Task implementation summaries
│   ├── *_IMPLEMENTATION.md       # Component implementation docs
│   └── *_SUMMARY.md              # Feature summaries
│
├── examples/                      # Example scripts
│   ├── README.md                  # Examples documentation
│   └── example_*.py              # Usage examples
│
├── reports/                       # Additional reports directory
├── venv/                         # Python virtual environment
├── .env                          # Environment variables (not in git)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── mcp.json                      # MCP server configuration
├── README.md                     # Project README
└── start_redis.bat              # Redis startup script (Windows)
```

## Core Modules (`backend/`)

### Main Application
- `main.py` - FastAPI application with all endpoints
- `models.py` - Pydantic data models

### Agent Components
- `agent_orchestrator.py` - Main agent orchestration logic
- `mcp_client.py` - MCP client for Anthropic and Postman
- `memory_store.py` - Redis vector memory storage
- `learning_engine.py` - Self-improvement and learning logic
- `alert_engine.py` - Alert generation and notification
- `report_generator.py` - Research report generation
- `scheduler.py` - Scheduled query management
- `session_manager.py` - Multi-turn conversation sessions
- `log_manager.py` - Comprehensive logging system

### Verification Scripts
- `verify_mcp.py` - MCP connection verification
- `verify_setup.py` - Setup verification

## Test Suite (`backend/tests/`)

### Unit Tests
- `test_agent_orchestrator.py` - Agent orchestration tests
- `test_alert_engine.py` - Alert engine tests
- `test_learning_engine.py` - Learning engine tests
- `test_mcp_client.py` - MCP client tests
- `test_memory_store.py` - Memory store tests
- `test_report_generator.py` - Report generator tests
- `test_scheduler.py` - Scheduler tests
- `test_session_manager.py` - Session manager tests
- `test_log_manager.py` - Log manager tests

### Integration Tests
- `test_api_integration_task15.py` - API integration tests
- `test_e2e_query_flow.py` - End-to-end query flow
- `test_feedback_endpoint.py` - Feedback endpoint tests
- `test_history_reports_endpoints.py` - History/reports endpoints
- `test_history_reports_integration.py` - History/reports integration
- `test_learning_integration.py` - Learning integration tests
- `test_learning_loop.py` - Learning loop tests
- `test_metrics_endpoint.py` - Metrics endpoint tests
- `test_metrics_integration.py` - Metrics integration tests
- `test_research_endpoint.py` - Research endpoint tests
- `test_scheduler_integration.py` - Scheduler integration tests
- `test_session_integration.py` - Session integration tests
- `test_task18_alerts_reports_integration.py` - Alerts/reports integration
- `test_infrastructure.py` - Infrastructure tests
- `test_main.py` - Main application tests
- `test_phase1.py` - Phase 1 tests

## Documentation (`docs/`)

### Implementation Summaries
- `TASK_5_COMPLETION_SUMMARY.md` - Phase 1 completion
- `TASK_11_COMPLETION_SUMMARY.md` - Learning loop completion
- `TASK_15_IMPLEMENTATION_SUMMARY.md` - Alerts and reports (Phase 4)
- `TASK_16_IMPLEMENTATION_SUMMARY.md` - Metrics endpoint
- `TASK_17_IMPLEMENTATION_SUMMARY.md` - History and reports endpoints
- `TASK_18_TEST_SUMMARY.md` - Alerts and reports testing
- `TASK_19_SCHEDULER_IMPLEMENTATION.md` - Scheduled queries
- `TASK_20_SESSION_MANAGEMENT.md` - Multi-turn conversations
- `TASK_21_COMPREHENSIVE_LOGGING.md` - Comprehensive logging

### Component Documentation
- `ALERT_ENGINE_IMPLEMENTATION.md` - Alert engine details
- `FEEDBACK_IMPLEMENTATION_SUMMARY.md` - Feedback system
- `MEMORY_STORE_README.md` - Memory store details
- `MCP_FIX_SUMMARY.md` - MCP fixes
- `MCPFIX_EXPLANATION.md` - MCP fix explanation
- `INFRASTRUCTURE_TEST_RESULTS.md` - Infrastructure test results
- `README.md` - Documentation index

## Examples (`examples/`)

### Usage Examples
- `example_alert_usage.py` - Alert engine demonstration
- `example_history_reports_usage.py` - History and reports
- `example_logging_usage.py` - Logging and observability
- `example_metrics_usage.py` - Metrics and self-improvement
- `example_report_usage.py` - Report generation
- `example_scheduler_usage.py` - Scheduled queries
- `example_session_usage.py` - Multi-turn conversations
- `README.md` - Examples documentation

## Configuration Files

### Environment Configuration
- `.env` - Environment variables (not in git)
- `.env.example` - Environment template with all required variables

### MCP Configuration
- `mcp.json` - MCP server configuration for Anthropic and Postman

### Python Configuration
- `requirements.txt` - Python package dependencies
- `.gitignore` - Git ignore rules

## Generated Content

### Reports
- `backend/reports/` - Research reports generated by queries
- `reports/` - Additional reports directory

### Logs
- Logs stored in Redis (in-memory and persistent)
- Accessible via `/api/logs` endpoint

### Cache
- `__pycache__/` - Python bytecode cache (not in git)
- `.pytest_cache/` - Pytest cache (not in git)

## Development Workflow

### 1. Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services
```bash
# Start Redis
docker run -d -p 6379:6379 redis/redis-stack:latest
# or on Windows: start_redis.bat

# Start API server
cd backend
python main.py
# or: uvicorn main:app --reload
```

### 3. Run Tests
```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_agent_orchestrator.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

### 4. Run Examples
```bash
# Run specific example
python examples/example_logging_usage.py

# Run all examples (Unix/Linux/Mac)
for script in examples/example_*.py; do python "$script"; done

# Run all examples (Windows PowerShell)
Get-ChildItem examples/example_*.py | ForEach-Object { python $_.FullName }
```

## API Endpoints

### Research
- `POST /api/research/query` - Submit research query
- `POST /api/research/feedback` - Submit feedback
- `GET /api/research/history` - Get query history

### Metrics and Monitoring
- `GET /api/metrics` - Get self-improvement metrics
- `GET /api/logs` - Query application logs

### Reports
- `GET /api/reports` - List generated reports
- `GET /api/reports/{report_id}` - Get specific report

### Scheduling
- `POST /api/schedule` - Create scheduled query
- `GET /api/schedule` - List schedules
- `GET /api/schedule/{schedule_id}` - Get schedule details
- `PUT /api/schedule/{schedule_id}` - Update schedule
- `DELETE /api/schedule/{schedule_id}` - Delete schedule

### Sessions
- `POST /api/session` - Create new session
- `GET /api/session/{session_id}/history` - Get session history
- `DELETE /api/session/{session_id}` - Delete session

### Health
- `GET /health` - Health check

## Best Practices

### Code Organization
1. Keep core logic in `backend/` modules
2. Write tests in `backend/tests/`
3. Document implementations in `docs/`
4. Provide examples in `examples/`

### Testing
1. Write unit tests for individual components
2. Write integration tests for component interactions
3. Write end-to-end tests for complete workflows
4. Maintain test coverage above 80%

### Documentation
1. Update task summaries when completing tasks
2. Document new features in `docs/`
3. Provide usage examples in `examples/`
4. Keep README files up to date

### Version Control
1. Don't commit `.env` files
2. Don't commit `__pycache__/` directories
3. Don't commit generated reports
4. Keep `.gitignore` updated

## Related Documentation

- [Main README](../README.md) - Project overview and setup
- [Requirements](../.kiro/specs/adaptive-research-agent/requirements.md) - Feature requirements
- [Design](../.kiro/specs/adaptive-research-agent/design.md) - System design
- [Tasks](../.kiro/specs/adaptive-research-agent/tasks.md) - Implementation tasks
- [Examples README](../examples/README.md) - Usage examples
