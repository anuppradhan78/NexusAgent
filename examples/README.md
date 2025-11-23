# Adaptive Research Agent - Example Scripts

This directory contains example scripts demonstrating various features of the Adaptive Research Agent.

## Prerequisites

Before running any examples, ensure:

1. **Redis is running:**
   ```bash
   docker run -d -p 6379:6379 redis/redis-stack:latest
   ```
   Or on Windows:
   ```bash
   start_redis.bat
   ```

2. **Environment variables are configured:**
   ```bash
   # Copy .env.example to .env and fill in your API keys
   cp .env.example .env
   ```

3. **The API server is running:**
   ```bash
   cd backend
   python main.py
   ```
   Or:
   ```bash
   uvicorn main:app --reload
   ```

## Available Examples

### 1. Alert Engine (`example_alert_usage.py`)
Demonstrates alert generation and notification capabilities.

**Features:**
- Triggering alerts based on query content
- Alert deduplication
- Multiple alert channels (console, file, webhook)

**Run:**
```bash
python examples/example_alert_usage.py
```

### 2. History and Reports (`example_history_reports_usage.py`)
Shows how to retrieve query history and access generated reports.

**Features:**
- Querying past research queries
- Listing generated reports
- Retrieving specific report content
- Pagination

**Run:**
```bash
python examples/example_history_reports_usage.py
```

### 3. Comprehensive Logging (`example_logging_usage.py`)
Demonstrates the logging and observability features.

**Features:**
- Querying logs with various filters
- Request ID tracing
- Performance metrics
- Learning decision logs
- Log statistics

**Run:**
```bash
python examples/example_logging_usage.py
```

### 4. Metrics and Self-Improvement (`example_metrics_usage.py`)
Shows how to access and interpret self-improvement metrics.

**Features:**
- Overall system metrics
- Improvement trends
- Source performance analysis
- Confidence threshold tracking

**Run:**
```bash
python examples/example_metrics_usage.py
```

### 5. Report Generation (`example_report_usage.py`)
Demonstrates report generation and retrieval.

**Features:**
- Generating research reports
- Report structure and formatting
- Accessing report metadata
- Report listing

**Run:**
```bash
python examples/example_report_usage.py
```

### 6. Scheduled Queries (`example_scheduler_usage.py`)
Shows how to create and manage scheduled recurring queries.

**Features:**
- Creating scheduled queries with cron expressions
- Listing active schedules
- Updating schedule settings
- Deleting schedules
- Automatic report generation

**Run:**
```bash
python examples/example_scheduler_usage.py
```

### 7. Multi-Turn Conversations (`example_session_usage.py`)
Demonstrates session management for multi-turn conversations.

**Features:**
- Creating conversation sessions
- Maintaining context across queries
- Referencing previous results
- Session history retrieval
- Automatic session creation

**Run:**
```bash
python examples/example_session_usage.py
```

## Running All Examples

To run all examples in sequence:

```bash
# On Unix/Linux/Mac
for script in examples/example_*.py; do
    echo "Running $script..."
    python "$script"
    echo ""
done

# On Windows PowerShell
Get-ChildItem examples/example_*.py | ForEach-Object {
    Write-Host "Running $($_.Name)..."
    python $_.FullName
    Write-Host ""
}
```

## Example Output

Each example script provides detailed output showing:
- ✓ Successful operations
- ✗ Failed operations
- Detailed results and data
- Step-by-step execution flow

## Troubleshooting

### Connection Error
```
ERROR: Could not connect to the API server
```
**Solution:** Ensure the API server is running on `http://localhost:8000`

### Redis Connection Error
```
Redis connection failed
```
**Solution:** Ensure Redis is running on `localhost:6379`

### API Key Error
```
ANTHROPIC_API_KEY not configured
```
**Solution:** Set up your `.env` file with required API keys

## Integration with Tests

These examples complement the test suite:
- **Tests** (`backend/tests/`) - Automated unit and integration tests
- **Examples** (`examples/`) - Interactive demonstrations and usage patterns

## Contributing

When adding new examples:
1. Follow the naming convention: `example_<feature>_usage.py`
2. Include comprehensive docstrings
3. Add error handling for common issues
4. Update this README with the new example
5. Ensure the example works from the `examples/` directory

## Related Documentation

- [Task 18 Summary](../docs/TASK_18_TEST_SUMMARY.md) - Alerts and Reports
- [Task 19 Summary](../docs/TASK_19_SCHEDULER_IMPLEMENTATION.md) - Scheduled Queries
- [Task 20 Summary](../docs/TASK_20_SESSION_MANAGEMENT.md) - Multi-Turn Conversations
- [Task 21 Summary](../docs/TASK_21_COMPREHENSIVE_LOGGING.md) - Comprehensive Logging
- [Main README](../README.md) - Project overview and setup
