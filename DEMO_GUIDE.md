# Demo Guide - Adaptive Research Agent

This guide explains how to run and understand the comprehensive demo of the Adaptive Research Agent.

## Overview

The `demo.py` script provides a complete walkthrough of all major features of the Adaptive Research Agent, demonstrating how it autonomously gathers information, learns from feedback, and improves over time.

## Prerequisites

Before running the demo, ensure:

1. **Redis is running:**
   ```bash
   docker run -d -p 6379:6379 redis/redis-stack:latest
   ```
   Or on Windows:
   ```bash
   start_redis.bat
   ```

2. **Environment variables are configured:**
   - Copy `.env.example` to `.env`
   - Add your `ANTHROPIC_API_KEY`
   - Optionally add `POSTMAN_API_KEY`

3. **API server is running:**
   ```bash
   cd backend
   python main.py
   ```

## Running the Demo

Simply run:
```bash
python demo.py
```

The demo will automatically execute all scenarios and display results.

## Demo Scenarios

### 1. Autonomous Query Processing
**What it demonstrates:**
- Natural language query understanding
- Automatic API discovery from Postman
- Parallel information gathering from multiple sources
- Intelligent synthesis using Claude
- Source citations with confidence scores

**What you'll see:**
- Three different research queries being processed
- Processing time and confidence scores
- Number of API sources used
- Synthesized answers with citations
- Similar past queries (if any exist)

### 2. Learning from Feedback
**What it demonstrates:**
- Feedback submission with relevance scores
- Pattern recognition from past queries
- Query refinement based on learned patterns
- Improved results for similar queries

**What you'll see:**
- Feedback being submitted for previous queries
- A similar query being processed with learned patterns
- Agent using historical data to improve results
- Previous relevance scores being applied

### 3. Alert Generation
**What it demonstrates:**
- Automatic detection of critical information
- Alert triggering based on content analysis
- Alert deduplication to prevent fatigue
- Multi-channel notification support

**What you'll see:**
- Queries about breaking news or critical topics
- Alerts being triggered (or not) based on urgency
- Alert status in query responses

### 4. Automated Report Generation
**What it demonstrates:**
- Comprehensive markdown report creation
- Structured sections with executive summary
- Source citations and metadata
- Report storage and retrieval

**What you'll see:**
- List of generated reports
- Report metadata (ID, query, timestamp, path)
- Sample report content structure
- Report retrieval by ID

### 5. Self-Improvement Metrics
**What it demonstrates:**
- Performance tracking over time
- Average relevance and confidence scores
- Improvement trend detection
- Source performance analysis
- Memory statistics

**What you'll see:**
- Total queries processed
- Average relevance and confidence scores
- Improvement trend (positive = getting better)
- Top performing API sources
- Current confidence threshold
- Memory statistics

### 6. Scheduled Recurring Queries
**What it demonstrates:**
- Cron-based query scheduling
- Background query execution
- Automatic report generation
- Schedule management (create, list, update, delete)

**What you'll see:**
- Scheduled query creation with cron expression
- Schedule ID and next run time
- List of all active schedules
- Schedule configuration details

### 7. Multi-Turn Conversations
**What it demonstrates:**
- Session-based conversation management
- Context preservation across queries
- Follow-up question handling
- Conversation history retrieval

**What you'll see:**
- Session creation
- Multiple related queries in sequence
- Context-aware responses
- Conversation history summary

### 8. Query History (Bonus)
**What it demonstrates:**
- Historical query retrieval
- Pagination support
- Relevance score tracking
- Timestamp information

**What you'll see:**
- Recent queries with metadata
- Query IDs, text, relevance scores
- Timestamps for each query

## Understanding the Output

### Success Indicators
- ✓ Green checkmarks indicate successful operations
- Processing times show performance
- Confidence scores indicate result quality
- Improvement trends show learning progress

### What to Look For

1. **First Run:**
   - No similar past queries found
   - Baseline confidence scores
   - Initial performance metrics

2. **After Feedback:**
   - Similar queries being recognized
   - Learned patterns being applied
   - Improved confidence scores
   - Positive improvement trend

3. **Over Time:**
   - Increasing average relevance scores
   - More efficient query processing
   - Better source prioritization
   - Growing memory of successful patterns

## Customizing the Demo

You can modify `demo.py` to:

1. **Change queries:**
   ```python
   queries = [
       "Your custom query here",
       "Another query",
   ]
   ```

2. **Adjust feedback scores:**
   ```python
   feedback_scores = [0.9, 0.85, 0.75]  # Modify these
   ```

3. **Configure API sources:**
   ```python
   "max_sources": 5,  # Increase or decrease
   ```

4. **Enable/disable features:**
   ```python
   "include_report": True,
   "alert_enabled": True,
   ```

## Troubleshooting

### Demo Fails to Start
**Error:** "Cannot connect to API server"
**Solution:** Ensure the API server is running on `http://localhost:8000`

### No Results Returned
**Error:** "Query failed with status 500"
**Solution:** 
- Check Redis is running
- Verify API keys in `.env`
- Check server logs for errors

### Slow Performance
**Issue:** Queries taking > 30 seconds
**Solution:**
- Reduce `max_sources` parameter
- Check network connectivity
- Verify MCP servers are responding

### No Improvement Trend
**Issue:** Improvement trend is 0 or negative
**Solution:**
- Submit more queries (need at least 10)
- Provide varied feedback scores
- Wait for learning to accumulate data

## Next Steps

After running the demo:

1. **Explore the API directly:**
   ```bash
   curl -X POST http://localhost:8000/api/research/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Your question here"}'
   ```

2. **Run individual examples:**
   ```bash
   python examples/example_metrics_usage.py
   python examples/example_scheduler_usage.py
   ```

3. **Check generated reports:**
   ```bash
   ls backend/reports/
   cat backend/reports/research_report_*.md
   ```

4. **Monitor metrics:**
   ```bash
   curl http://localhost:8000/api/metrics | python -m json.tool
   ```

5. **Review logs:**
   ```bash
   curl "http://localhost:8000/api/logs?limit=50" | python -m json.tool
   ```

## Understanding Self-Improvement

The agent improves through:

1. **Memory Storage:** Every query is stored with embeddings
2. **Similarity Search:** New queries find similar past queries
3. **Pattern Learning:** Successful patterns are identified
4. **Query Refinement:** New queries are improved using patterns
5. **Source Prioritization:** Better sources get higher priority
6. **Threshold Adjustment:** Confidence thresholds adapt to feedback

**Key Metric:** Watch the "improvement_trend" in metrics. A positive value means the agent is getting better!

## Demo Architecture

```
Demo Script
    ↓
Health Check → Verify API Server
    ↓
Query Processing → Submit 3 queries
    ↓
Feedback Loop → Provide relevance scores
    ↓
Learning Demo → Show pattern recognition
    ↓
Alert Demo → Trigger critical alerts
    ↓
Report Demo → Generate & retrieve reports
    ↓
Metrics Demo → Show improvement trends
    ↓
Scheduler Demo → Create scheduled queries
    ↓
Conversation Demo → Multi-turn interaction
    ↓
History Demo → Review past queries
    ↓
Summary → Display all features demonstrated
```

## Related Documentation

- [Main README](README.md) - Project overview
- [Getting Started](GETTING_STARTED.md) - Quick setup guide
- [Examples README](examples/README.md) - Individual feature examples
- [Requirements](.kiro/specs/adaptive-research-agent/requirements.md) - Feature requirements
- [Design](.kiro/specs/adaptive-research-agent/design.md) - System architecture

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review server logs in the terminal
3. Verify all prerequisites are met
4. Check the examples directory for working code

---

**Tip:** Run the demo multiple times to see the learning effect. The agent gets better with more data!
