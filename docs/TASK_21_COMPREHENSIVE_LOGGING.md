# Comprehensive Logging Implementation Summary

## Overview

This document summarizes the implementation of comprehensive logging capabilities for the Adaptive Research Agent, providing structured JSON logging with request ID tracing, log storage and retrieval, and performance metrics logging.

## Requirements Implemented

### Requirement 14.1: Log all queries, API calls, memory operations, learning decisions
✅ **Implemented**
- `LogManager` class stores all application events
- Logs include queries, API calls, memory operations, and learning decisions
- Each log entry contains structured data with context
- All major operations are logged throughout the application

### Requirement 14.2: Use structured JSON logging with request IDs
✅ **Implemented**
- Structlog configured for JSON output with ISO timestamps
- Request ID middleware adds unique ID to each request
- Request IDs are propagated through all log entries
- Context variables merge request IDs automatically
- Log entries include: timestamp, level, message, request_id, event, context

### Requirement 14.3: Log performance metrics (latency, token usage, memory operations)
✅ **Implemented**
- Processing time logged for all queries
- API response times tracked
- Memory operation metrics logged
- Confidence scores and source counts tracked
- `get_log_stats()` provides aggregated metrics
- Level counts and time ranges available

### Requirement 14.4: Log learning loop decisions with reasoning
✅ **Implemented**
- Query refinement decisions logged with reasoning
- Confidence threshold adjustments logged
- Source prioritization changes logged
- Feedback processing logged with context
- All learning decisions include explanatory context

### Requirement 14.5: Expose logs via /api/logs endpoint with filtering
✅ **Implemented**
- `GET /api/logs` endpoint with comprehensive filtering
- Filter by: level, request_id, event, time range
- Pagination support (limit, offset)
- Returns logs with statistics
- Combined filters supported

### Requirement 14.6: Integrate with standard logging frameworks
✅ **Implemented**
- Uses structlog for structured logging
- Compatible with Python's standard logging
- JSON output format for log aggregation tools
- Request ID tracing throughout the stack
- Graceful degradation if Redis unavailable

## Components Created

### 1. LogManager (`backend/log_manager.py`)
Main class for managing application logs:
- `log()` - Log an event with structured data
- `query_logs()` - Query logs with filtering
- `get_log_stats()` - Get log statistics
- `cleanup_old_logs()` - Manual cleanup (Redis handles automatically)

### 2. Data Models
- `LogEntry` - Single log entry with timestamp, level, message, request_id, event, context
- `LogQuery` - Query parameters for filtering logs

### 3. API Endpoint (in `backend/main.py`)
- `GET /api/logs` - Query logs with filtering parameters:
  - `start_time` - Start of time range (Unix timestamp)
  - `end_time` - End of time range (Unix timestamp)
  - `level` - Filter by log level
  - `request_id` - Filter by request ID
  - `event` - Filter by event name
  - `limit` - Maximum logs to return (default: 100)
  - `offset` - Pagination offset (default: 0)

### 4. Integration
- Log manager initialized in application startup
- Request ID middleware adds unique ID to each request
- Structlog configured with JSON renderer
- All components use structured logging

## Storage Architecture

### Dual Storage System
1. **In-Memory Buffer**
   - Fast access to recent logs
   - Configurable size (default: 1000 logs)
   - Deque with automatic eviction of oldest logs

2. **Redis Persistence**
   - Long-term storage with TTL
   - Configurable retention (default: 7 days)
   - Automatic expiration via Redis TTL
   - Survives application restarts

### Log Entry Structure
```json
{
  "timestamp": 1763936887.024428,
  "datetime": "2025-11-23T14:28:07.024428",
  "level": "info",
  "message": "Query processed successfully",
  "request_id": "req_123",
  "event": "query_processed",
  "context": {
    "query": "What is AI?",
    "processing_time_ms": 1500,
    "confidence_score": 0.85,
    "sources_used": ["api_1", "api_2"],
    "refinement_applied": true,
    "reasoning": "High confidence due to multiple consistent sources"
  }
}
```

## Testing

### Unit Tests (`backend/tests/test_log_manager.py`)
✅ All 14 tests passing:
- `test_log_creation` - Log entry creation
- `test_multiple_logs` - Multiple log entries
- `test_query_logs_no_filters` - Query without filters
- `test_query_logs_by_level` - Filter by log level
- `test_query_logs_by_request_id` - Filter by request ID
- `test_query_logs_by_event` - Filter by event name
- `test_query_logs_by_time_range` - Filter by time range
- `test_query_logs_pagination` - Pagination
- `test_log_stats` - Statistics
- `test_log_context_data` - Context data storage
- `test_log_levels` - Different log levels
- `test_memory_buffer_limit` - Buffer size limits
- `test_log_without_request_id` - Optional request ID
- `test_combined_filters` - Multiple filters

## Usage Examples

### Example 1: Query All Recent Logs
```python
response = await client.get("/api/logs?limit=10")
data = response.json()

for log in data['logs']:
    print(f"[{log['datetime']}] {log['level']}: {log['message']}")
```

### Example 2: Filter by Log Level
```python
response = await client.get("/api/logs?level=error&limit=10")
data = response.json()

print(f"Found {len(data['logs'])} error logs")
```

### Example 3: Trace a Specific Request
```python
# Get request ID from response
request_id = response.headers.get("X-Request-ID")

# Query logs for this request
response = await client.get(f"/api/logs?request_id={request_id}&limit=50")
data = response.json()

print(f"Request trace ({len(data['logs'])} events):")
for log in data['logs']:
    print(f"  {log['event']}: {log['message']}")
```

### Example 4: Filter by Time Range
```python
five_minutes_ago = (datetime.now() - timedelta(minutes=5)).timestamp()
response = await client.get(f"/api/logs?start_time={five_minutes_ago}&limit=10")
```

### Example 5: Filter by Event Type
```python
response = await client.get("/api/logs?event=query_processed&limit=10")
data = response.json()

for log in data['logs']:
    if 'query' in log['context']:
        print(f"Query: {log['context']['query']}")
```

### Example 6: Combined Filters
```python
response = await client.get(
    "/api/logs?level=info&event=query_processed&request_id=req_123&limit=10"
)
```

## Log Events

### Query Processing Events
- `query_received` - Query submitted
- `intent_parsed` - Query intent extracted
- `similar_queries_found` - Similar past queries retrieved
- `query_refined` - Query refinement applied
- `apis_discovered` - APIs discovered from Postman
- `api_call_complete` - Individual API call completed
- `synthesis_complete` - Results synthesized
- `query_processed_successfully` - Query completed

### Memory Events
- `memory_stored` - Entry stored in memory
- `similar_memories_found` - Similar memories retrieved
- `relevance_updated` - Relevance score updated
- `memory_metrics_calculated` - Metrics computed

### Learning Events
- `query_refined` - Query refinement with reasoning
- `confidence_threshold_adjusted` - Threshold changed
- `source_metrics_calculated` - Source performance analyzed
- `feedback_processed` - User feedback processed

### Alert Events
- `alert_triggered` - Alert generated
- `alert_suppressed_duplicate` - Duplicate alert prevented

### Report Events
- `report_generated` - Report created
- `report_retrieved` - Report accessed

### Session Events
- `session_created` - New session started
- `session_retrieved` - Session accessed
- `query_added_to_session` - Query added to history
- `session_deleted` - Session removed

## Performance Considerations

### Memory Management
- In-memory buffer limited to configurable size (default: 1000)
- Oldest logs automatically evicted when buffer full
- Redis provides long-term storage without memory growth

### Query Performance
- Memory logs queried first (fast)
- Redis queried only if needed
- Filters applied efficiently
- Pagination prevents large result sets

### Storage Efficiency
- Logs expire automatically after retention period
- Redis TTL handles cleanup
- No manual cleanup required in normal operation

## Configuration

### Environment Variables
```bash
# Redis configuration (shared with other components)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# Log retention (optional, default: 7 days)
LOG_RETENTION_DAYS=7

# Memory buffer size (optional, default: 1000)
MAX_MEMORY_LOGS=1000
```

### Structlog Configuration
```python
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # Merge context vars (request ID)
        structlog.processors.TimeStamper(fmt="iso"),  # ISO timestamps
        structlog.processors.add_log_level,  # Add log level
        structlog.processors.JSONRenderer()  # JSON output
    ]
)
```

## Integration with Existing Components

### Request ID Middleware
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### Logging in Components
```python
# All components use structlog
logger = structlog.get_logger()

# Log with context
logger.info(
    "query_processed",
    query_id=query_id,
    processing_time_ms=processing_time,
    confidence_score=confidence_score,
    sources_used=len(sources),
    refinement_applied=True,
    reasoning="High confidence due to multiple consistent sources"
)
```

## Observability Benefits

### Request Tracing
- Every request has unique ID
- All logs for a request can be traced
- End-to-end visibility of request flow

### Performance Monitoring
- Processing times logged
- API response times tracked
- Memory operation metrics available
- Trends visible over time

### Debugging
- Structured logs easy to parse
- Context data provides details
- Filtering enables quick issue location
- Request traces show complete flow

### Learning Insights
- Learning decisions logged with reasoning
- Query refinements tracked
- Source performance visible
- Feedback patterns analyzable

## Future Enhancements

Potential improvements for future iterations:
1. Log aggregation to external services (Elasticsearch, Splunk)
2. Real-time log streaming via WebSocket
3. Log-based alerting rules
4. Advanced analytics and visualization
5. Log compression for long-term storage
6. Distributed tracing integration (OpenTelemetry)

## Files Created/Modified

**New Files:**
1. `backend/log_manager.py` - Log manager implementation (600+ lines)
2. `backend/tests/test_log_manager.py` - Unit tests (14 tests, all passing)
3. `backend/example_logging_usage.py` - Usage examples and documentation
4. `docs/TASK_21_COMPREHENSIVE_LOGGING.md` - This implementation summary

**Modified Files:**
1. `backend/main.py` - Added log manager initialization and /api/logs endpoint

## Conclusion

The comprehensive logging implementation successfully provides structured JSON logging with request ID tracing, log storage and retrieval, performance metrics logging, and learning decision logging. All requirements (14.1-14.6) have been implemented and tested. The system provides excellent observability for debugging, monitoring, and understanding agent behavior.
