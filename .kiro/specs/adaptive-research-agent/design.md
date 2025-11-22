# Design Document

## Overview

The Adaptive Research Agent is an autonomous, self-improving AI system built for the Context Engineering Challenge. It demonstrates agents that don't just think, but act - continuously learning and improving as they operate. The system uses Anthropic's Claude via MCP for reasoning, Postman's Public API Network for real-time data access, and Redis vector storage for semantic memory. The architecture emphasizes autonomous operation, continuous learning loops, and adaptive behavior that improves over time without human intervention.

**Key Innovations:**
- Self-improving query refinement based on relevance feedback
- Vector-based semantic memory for pattern recognition
- Adaptive confidence thresholds that adjust based on success rates
- Autonomous alert generation and report creation
- Multi-source API orchestration with intelligent prioritization

## Architecture

### High-Level Architecture

```text
USER LAYER:
  [Web UI] [CLI] [API Clients] [Scheduled Jobs]
           |       |       |           |
           +-------+-------+-----------+
                        |
                        v
API LAYER (FastAPI):
         [Research Endpoint] [Feedback Endpoint]
         [Metrics Endpoint]  [Reports Endpoint]
                        |
                        v
AGENT ORCHESTRATION:
              [Query Parser]
                    |
              [Memory Retrieval] <---> [Redis Vector Store]
                    |                         |
              [Query Refiner]            [Embeddings]
                    |                    [Past Patterns]
              [API Orchestrator]         [Relevance Scores]
                    |
         +----------+----------+
         |          |          |
    [Postman    [Other     [Future
     MCP]        APIs]      Sources]
         |          |          |
         +----------+----------+
                    |
              [Information Synthesizer] <---> [Anthropic Claude MCP]
                    |
         +----------+----------+
         |                    |
    [Alert Engine]      [Report Generator]
         |                    |
    [Notifications]      [Markdown Reports]
                    |
              [Learning Loop]
                    |
         +----------+----------+
         |          |          |
    [Feedback   [Pattern    [Threshold
     Analysis]   Learning]   Adjustment]
         |          |          |
         +----------+----------+
                    |
              [Memory Update] ---> [Redis Vector Store]
```


### Technology Stack

**Core Framework:**
- Python 3.11+
- FastAPI 0.110+ (REST API)
- Pydantic 2.0+ (data validation)
- asyncio (async operations)

**AI & MCP:**
- Anthropic Claude (claude-3-5-sonnet-20241022) via MCP
- MCP Python SDK (model-context-protocol)
- Postman MCP Server (verified publisher APIs)

**Memory & Storage:**
- Redis 7.2+ with RediSearch module (vector storage)
- redis-py client with vector search support
- Sentence Transformers or Anthropic embeddings

**Observability:**
- Python structlog (structured logging)
- Prometheus client (metrics)
- APScheduler (scheduled queries)

**Development:**
- pytest (testing)
- httpx (async HTTP client)
- python-dotenv (configuration)

### Deployment Model

- Backend: FastAPI with uvicorn ASGI server
- Redis: Docker container with RediSearch module
- MCP Servers: Configured via mcp.json
- Development: All services running locally
- Production: Docker Compose for orchestration

## Components and Interfaces

### 1. FastAPI Server (main.py)

**Purpose**: REST API exposing agent capabilities

**Endpoints:**

```python
@app.post("/api/research/query")
async def research_query(request: ResearchRequest) -> ResearchResponse:
    """
    Process research query and return synthesized results
    
    Request:
        {
            "query": "What are the latest trends in AI?",
            "session_id": "optional-uuid",
            "max_sources": 5,
            "include_report": true
        }
    
    Response:
        {
            "query_id": "uuid",
            "session_id": "uuid",
            "synthesized_answer": "...",
            "sources": [...],
            "confidence_score": 0.85,
            "alert_triggered": false,
            "report_path": "/reports/2025-11-21_12-30-45.md",
            "processing_time_ms": 2500,
            "similar_past_queries": [...]
        }
    """

@app.post("/api/research/feedback")
async def submit_feedback(feedback: FeedbackRequest) -> FeedbackResponse:
    """
    Submit relevance feedback for learning
    
    Request:
        {
            "query_id": "uuid",
            "relevance_score": 0.9,
            "feedback_notes": "Very helpful information"
        }
    """

@app.get("/api/research/history")
async def get_history(
    limit: int = 50,
    offset: int = 0,
    min_relevance: float = 0.0
) -> HistoryResponse:
    """Get past queries with pagination"""

@app.get("/api/metrics")
async def get_metrics() -> MetricsResponse:
    """Get self-improvement metrics"""

@app.get("/api/reports")
async def list_reports(limit: int = 20) -> ReportsListResponse:
    """List generated reports"""

@app.get("/api/reports/{report_id}")
async def get_report(report_id: str) -> ReportContent:
    """Get specific report content"""

@app.post("/api/schedule")
async def create_schedule(schedule: ScheduleRequest) -> ScheduleResponse:
    """Create scheduled recurring query"""

@app.get("/health")
async def health_check() -> HealthResponse:
    """Service health check"""
```


### 2. Agent Orchestrator (agent_orchestrator.py)

**Purpose**: Core agent logic coordinating all operations

**Main Flow:**

```python
class AgentOrchestrator:
    def __init__(
        self,
        mcp_client: MCPClient,
        memory_store: MemoryStore,
        learning_engine: LearningEngine
    ):
        """Initialize agent with dependencies"""
    
    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_sources: int = 5
    ) -> ResearchResult:
        """
        Main agent processing pipeline:
        1. Parse query intent
        2. Retrieve similar past queries from memory
        3. Refine query based on learned patterns
        4. Orchestrate API calls to multiple sources
        5. Synthesize information using Claude
        6. Evaluate for alerts
        7. Generate report if requested
        8. Store in memory for learning
        """
        
        # Step 1: Parse intent using Claude
        intent = await self._parse_intent(query)
        
        # Step 2: Semantic search in memory
        similar_queries = await self.memory_store.find_similar(
            query_embedding=await self._get_embedding(query),
            top_k=5
        )
        
        # Step 3: Refine query based on patterns
        refined_query = await self.learning_engine.refine_query(
            original_query=query,
            similar_patterns=similar_queries
        )
        
        # Step 4: Discover and call APIs
        api_sources = await self._discover_apis(intent, refined_query)
        results = await self._gather_information(api_sources)
        
        # Step 5: Synthesize with Claude
        synthesis = await self._synthesize_results(
            query=query,
            results=results,
            context=similar_queries
        )
        
        # Step 6: Check alert conditions
        alert = await self._evaluate_alert(synthesis)
        
        # Step 7: Generate report
        report = await self._generate_report(synthesis)
        
        # Step 8: Store in memory
        await self.memory_store.store(
            query=query,
            results=synthesis,
            sources=api_sources,
            timestamp=datetime.now()
        )
        
        return ResearchResult(
            synthesis=synthesis,
            alert=alert,
            report=report,
            similar_queries=similar_queries
        )
```

### 3. MCP Client (mcp_client.py)

**Purpose**: Interface with Anthropic Claude and Postman via MCP

**Implementation:**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self):
        self.claude_session: Optional[ClientSession] = None
        self.postman_session: Optional[ClientSession] = None
    
    async def initialize(self):
        """Initialize MCP connections"""
        # Connect to Anthropic MCP
        self.claude_session = await self._connect_claude()
        
        # Connect to Postman MCP
        self.postman_session = await self._connect_postman()
    
    async def _connect_claude(self) -> ClientSession:
        """Connect to Anthropic Claude via MCP"""
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@anthropic-ai/mcp-server-anthropic"],
            env={"ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")}
        )
        
        return await stdio_client(server_params)
    
    async def _connect_postman(self) -> ClientSession:
        """Connect to Postman MCP server"""
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@postman/mcp-server"],
            env={"POSTMAN_API_KEY": os.getenv("POSTMAN_API_KEY")}
        )
        
        return await stdio_client(server_params)
    
    async def call_claude(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7
    ) -> str:
        """Call Claude via MCP for reasoning"""
        response = await self.claude_session.call_tool(
            "claude_chat",
            arguments={
                "prompt": prompt,
                "system": system,
                "temperature": temperature,
                "model": "claude-3-5-sonnet-20241022"
            }
        )
        return response.content
    
    async def discover_apis(self, query: str) -> List[APIEndpoint]:
        """Discover relevant APIs from Postman"""
        response = await self.postman_session.call_tool(
            "search_apis",
            arguments={"query": query, "verified_only": True}
        )
        return self._parse_api_results(response)
    
    async def call_api(
        self,
        api_id: str,
        endpoint: str,
        params: dict
    ) -> dict:
        """Call specific API via Postman MCP"""
        response = await self.postman_session.call_tool(
            "execute_request",
            arguments={
                "api_id": api_id,
                "endpoint": endpoint,
                "params": params
            }
        )
        return response.content
```


### 4. Memory Store (memory_store.py)

**Purpose**: Redis-based vector storage for agent memory

**Implementation:**

```python
import redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

class MemoryStore:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.index_name = "agent_memory_idx"
        self._create_index()
    
    def _create_index(self):
        """Create Redis vector search index"""
        try:
            schema = (
                VectorField(
                    "query_embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": 1024,  # Anthropic embedding dimension
                        "DISTANCE_METRIC": "COSINE"
                    }
                ),
                TextField("query_text"),
                TextField("results_summary"),
                NumericField("relevance_score"),
                NumericField("timestamp"),
                TextField("api_sources"),
                TextField("session_id")
            )
            
            definition = IndexDefinition(
                prefix=["memory:"],
                index_type=IndexType.HASH
            )
            
            self.client.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
        except redis.ResponseError as e:
            if "Index already exists" not in str(e):
                raise
    
    async def store(
        self,
        query: str,
        query_embedding: List[float],
        results: dict,
        sources: List[str],
        relevance_score: float = 0.5,
        session_id: Optional[str] = None
    ) -> str:
        """Store query and results in memory"""
        memory_id = f"memory:{uuid.uuid4()}"
        
        self.client.hset(
            memory_id,
            mapping={
                "query_text": query,
                "query_embedding": np.array(query_embedding, dtype=np.float32).tobytes(),
                "results_summary": json.dumps(results),
                "relevance_score": relevance_score,
                "timestamp": time.time(),
                "api_sources": json.dumps(sources),
                "session_id": session_id or ""
            }
        )
        
        # Set expiration (30 days)
        self.client.expire(memory_id, 30 * 24 * 60 * 60)
        
        return memory_id
    
    async def find_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_relevance: float = 0.0
    ) -> List[MemoryEntry]:
        """Find similar past queries using vector search"""
        query_vector = np.array(query_embedding, dtype=np.float32).tobytes()
        
        query = (
            Query(f"*=>[KNN {top_k} @query_embedding $vec AS score]")
            .sort_by("score")
            .return_fields("query_text", "results_summary", "relevance_score", "api_sources", "score")
            .dialect(2)
        )
        
        results = self.client.ft(self.index_name).search(
            query,
            query_params={"vec": query_vector}
        )
        
        memories = []
        for doc in results.docs:
            if float(doc.relevance_score) >= min_relevance:
                memories.append(MemoryEntry(
                    query=doc.query_text,
                    results=json.loads(doc.results_summary),
                    relevance_score=float(doc.relevance_score),
                    api_sources=json.loads(doc.api_sources),
                    similarity_score=1 - float(doc.score)  # Convert distance to similarity
                ))
        
        return memories
    
    async def update_relevance(self, memory_id: str, new_score: float):
        """Update relevance score based on feedback"""
        self.client.hset(memory_id, "relevance_score", new_score)
    
    async def get_metrics(self) -> MemoryMetrics:
        """Get memory statistics"""
        total_memories = self.client.dbsize()
        
        # Get average relevance score
        all_scores = []
        for key in self.client.scan_iter("memory:*"):
            score = self.client.hget(key, "relevance_score")
            if score:
                all_scores.append(float(score))
        
        return MemoryMetrics(
            total_memories=total_memories,
            avg_relevance=np.mean(all_scores) if all_scores else 0.0,
            high_quality_memories=sum(1 for s in all_scores if s >= 0.7)
        )
```


### 5. Learning Engine (learning_engine.py)

**Purpose**: Continuous improvement through pattern analysis

**Implementation:**

```python
class LearningEngine:
    def __init__(self, memory_store: MemoryStore, mcp_client: MCPClient):
        self.memory_store = memory_store
        self.mcp_client = mcp_client
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD_INITIAL", "0.5"))
        self.learning_rate = float(os.getenv("LEARNING_RATE", "0.1"))
    
    async def refine_query(
        self,
        original_query: str,
        similar_patterns: List[MemoryEntry]
    ) -> RefinedQuery:
        """Refine query based on successful past patterns"""
        
        # Filter for high-quality patterns
        successful_patterns = [
            p for p in similar_patterns
            if p.relevance_score >= 0.7
        ]
        
        if not successful_patterns:
            return RefinedQuery(
                query=original_query,
                refinements=[],
                confidence=0.5
            )
        
        # Analyze patterns using Claude
        pattern_analysis = await self.mcp_client.call_claude(
            prompt=f"""Analyze these successful past queries and suggest refinements for the current query.
            
Current query: {original_query}

Successful past patterns:
{self._format_patterns(successful_patterns)}

Suggest:
1. Additional search terms to include
2. API sources to prioritize
3. Query parameters that worked well
4. Information types that were most relevant
""",
            system="You are a query optimization expert. Suggest concrete, actionable refinements."
        )
        
        refinements = self._parse_refinements(pattern_analysis)
        
        return RefinedQuery(
            query=original_query,
            refinements=refinements,
            confidence=self._calculate_confidence(successful_patterns),
            prioritized_sources=self._extract_top_sources(successful_patterns)
        )
    
    async def adjust_confidence_threshold(self, recent_feedback: List[FeedbackEntry]):
        """Dynamically adjust confidence threshold based on feedback"""
        
        if len(recent_feedback) < 10:
            return  # Need minimum data
        
        # Calculate false positive rate (low relevance despite high confidence)
        false_positives = sum(
            1 for f in recent_feedback
            if f.confidence > self.confidence_threshold and f.relevance_score < 0.5
        )
        
        fp_rate = false_positives / len(recent_feedback)
        
        # Adjust threshold
        if fp_rate > 0.2:  # Too many false positives
            self.confidence_threshold += self.learning_rate
        elif fp_rate < 0.05:  # Very few false positives, can be more aggressive
            self.confidence_threshold -= self.learning_rate
        
        # Clamp between 0.3 and 0.9
        self.confidence_threshold = max(0.3, min(0.9, self.confidence_threshold))
        
        logger.info(
            "confidence_threshold_adjusted",
            new_threshold=self.confidence_threshold,
            fp_rate=fp_rate,
            sample_size=len(recent_feedback)
        )
    
    async def analyze_source_performance(
        self,
        lookback_queries: int = 50
    ) -> Dict[str, SourceMetrics]:
        """Analyze which API sources perform best"""
        
        # Get recent memories
        recent = await self.memory_store.get_recent(limit=lookback_queries)
        
        source_stats = defaultdict(lambda: {"total": 0, "high_relevance": 0, "avg_score": []})
        
        for memory in recent:
            for source in memory.api_sources:
                source_stats[source]["total"] += 1
                source_stats[source]["avg_score"].append(memory.relevance_score)
                if memory.relevance_score >= 0.7:
                    source_stats[source]["high_relevance"] += 1
        
        # Calculate metrics
        metrics = {}
        for source, stats in source_stats.items():
            metrics[source] = SourceMetrics(
                total_uses=stats["total"],
                success_rate=stats["high_relevance"] / stats["total"],
                avg_relevance=np.mean(stats["avg_score"]),
                priority_score=self._calculate_priority(stats)
            )
        
        return metrics
    
    def _calculate_priority(self, stats: dict) -> float:
        """Calculate priority score for API source"""
        success_rate = stats["high_relevance"] / stats["total"]
        avg_score = np.mean(stats["avg_score"])
        usage_weight = min(stats["total"] / 10, 1.0)  # More usage = more confidence
        
        return (success_rate * 0.5 + avg_score * 0.3 + usage_weight * 0.2)
```


### 6. Alert Engine (alert_engine.py)

**Purpose**: Detect critical information and send notifications

**Implementation:**

```python
class AlertEngine:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.alert_channels = self._parse_channels(os.getenv("ALERT_CHANNELS", "console"))
        self.alert_history = []
    
    async def evaluate(
        self,
        query: str,
        synthesis: ResearchSynthesis
    ) -> Optional[Alert]:
        """Evaluate if information warrants an alert"""
        
        # Use Claude to assess urgency
        assessment = await self.mcp_client.call_claude(
            prompt=f"""Analyze this research result for urgency and importance.
            
Query: {query}

Findings:
{synthesis.summary}

Sources: {', '.join(synthesis.sources)}

Assess:
1. Is this time-sensitive or breaking information?
2. Does this contain critical updates or anomalies?
3. What is the severity level (low/medium/high/critical)?
4. Should an alert be triggered?

Respond in JSON format:
{{
    "should_alert": true/false,
    "severity": "low|medium|high|critical",
    "reasoning": "explanation",
    "key_points": ["point1", "point2"]
}}
""",
            system="You are an information triage specialist. Be conservative with alerts to avoid fatigue."
        )
        
        alert_decision = json.loads(assessment)
        
        if not alert_decision["should_alert"]:
            return None
        
        # Check for duplicates
        if self._is_duplicate(query, synthesis):
            logger.info("alert_suppressed_duplicate", query=query)
            return None
        
        alert = Alert(
            severity=alert_decision["severity"],
            title=f"Research Alert: {query[:50]}...",
            message=alert_decision["reasoning"],
            key_points=alert_decision["key_points"],
            sources=synthesis.sources,
            timestamp=datetime.now()
        )
        
        await self._send_alert(alert)
        self.alert_history.append(alert)
        
        return alert
    
    async def _send_alert(self, alert: Alert):
        """Send alert via configured channels"""
        for channel in self.alert_channels:
            if channel == "console":
                self._send_console(alert)
            elif channel.startswith("file:"):
                await self._send_file(alert, channel.split(":")[1])
            elif channel.startswith("webhook:"):
                await self._send_webhook(alert, channel.split(":")[1])
    
    def _send_console(self, alert: Alert):
        """Print alert to console"""
        print(f"\n{'='*60}")
        print(f"🚨 ALERT [{alert.severity.upper()}] 🚨")
        print(f"{'='*60}")
        print(f"Title: {alert.title}")
        print(f"Message: {alert.message}")
        print(f"\nKey Points:")
        for point in alert.key_points:
            print(f"  • {point}")
        print(f"\nSources: {', '.join(alert.sources)}")
        print(f"{'='*60}\n")
    
    def _is_duplicate(self, query: str, synthesis: ResearchSynthesis) -> bool:
        """Check if similar alert was recently sent"""
        recent_alerts = [a for a in self.alert_history if 
                        (datetime.now() - a.timestamp).seconds < 3600]
        
        for past_alert in recent_alerts:
            # Simple similarity check (could use embeddings for better accuracy)
            if self._text_similarity(past_alert.title, query) > 0.8:
                return True
        
        return False

### 7. Report Generator (report_generator.py)

**Purpose**: Create comprehensive markdown reports

**Implementation:**

```python
class ReportGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(
        self,
        query: str,
        synthesis: ResearchSynthesis,
        similar_queries: List[MemoryEntry],
        metadata: dict
    ) -> ReportPath:
        """Generate comprehensive research report"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"research_report_{timestamp}.md"
        filepath = self.output_dir / filename
        
        report_content = self._build_report(
            query=query,
            synthesis=synthesis,
            similar_queries=similar_queries,
            metadata=metadata
        )
        
        filepath.write_text(report_content)
        
        logger.info("report_generated", path=str(filepath), query=query)
        
        return ReportPath(
            filename=filename,
            full_path=str(filepath),
            timestamp=timestamp
        )
    
    def _build_report(
        self,
        query: str,
        synthesis: ResearchSynthesis,
        similar_queries: List[MemoryEntry],
        metadata: dict
    ) -> str:
        """Build markdown report content"""
        
        report = f"""# Research Report: {query}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Query ID:** {metadata.get('query_id', 'N/A')}  
**Confidence Score:** {synthesis.confidence_score:.2f}  
**Processing Time:** {metadata.get('processing_time_ms', 0)}ms

---

## Executive Summary

{synthesis.summary}

---

## Key Findings

{self._format_findings(synthesis.findings)}

---

## Detailed Analysis

{synthesis.detailed_analysis}

---

## Sources

{self._format_sources(synthesis.sources, synthesis.source_details)}

---

## Related Research

{self._format_related(similar_queries)}

---

## Confidence Assessment

**Overall Confidence:** {synthesis.confidence_score:.2f}

{self._format_confidence_breakdown(synthesis.confidence_breakdown)}

---

## Metadata

- **API Sources Used:** {', '.join(metadata.get('api_sources', []))}
- **Query Refinements Applied:** {len(metadata.get('refinements', []))}
- **Similar Past Queries Found:** {len(similar_queries)}
- **Alert Triggered:** {'Yes' if metadata.get('alert_triggered') else 'No'}

---

*Generated by Adaptive Research Agent*
"""
        return report
```


## Data Models

### Core Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class ResearchRequest(BaseModel):
    """API request for research query"""
    query: str = Field(..., min_length=10, max_length=500)
    session_id: Optional[str] = None
    max_sources: int = Field(default=5, ge=1, le=10)
    include_report: bool = True
    alert_enabled: bool = True

class APISource(BaseModel):
    """API source information"""
    api_id: str
    api_name: str
    endpoint: str
    verified: bool
    priority_score: float = 0.5

class ResearchSynthesis(BaseModel):
    """Synthesized research results"""
    summary: str
    detailed_analysis: str
    findings: List[str]
    sources: List[str]
    source_details: List[APISource]
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_breakdown: Dict[str, float]

class Alert(BaseModel):
    """Alert notification"""
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    title: str
    message: str
    key_points: List[str]
    sources: List[str]
    timestamp: datetime

class MemoryEntry(BaseModel):
    """Memory store entry"""
    query: str
    results: dict
    relevance_score: float
    api_sources: List[str]
    similarity_score: float
    timestamp: float

class FeedbackRequest(BaseModel):
    """Feedback submission"""
    query_id: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    feedback_notes: Optional[str] = None

class RefinedQuery(BaseModel):
    """Query refinement result"""
    query: str
    refinements: List[str]
    confidence: float
    prioritized_sources: List[str]

class MetricsResponse(BaseModel):
    """Self-improvement metrics"""
    total_queries: int
    avg_relevance_score: float
    avg_confidence_score: float
    improvement_trend: float  # Positive = improving
    top_sources: List[Dict[str, float]]
    confidence_threshold: float
    memory_stats: Dict[str, int]

class ResearchResponse(BaseModel):
    """API response for research query"""
    query_id: str
    session_id: str
    synthesized_answer: str
    sources: List[APISource]
    confidence_score: float
    alert_triggered: bool
    report_path: Optional[str]
    processing_time_ms: int
    similar_past_queries: List[MemoryEntry]
```

## Error Handling

### Error Categories

```python
class AgentError(Exception):
    """Base exception for agent errors"""
    pass

class MCPConnectionError(AgentError):
    """MCP server connection failed"""
    pass

class MemoryStoreError(AgentError):
    """Redis memory operation failed"""
    pass

class APIDiscoveryError(AgentError):
    """Failed to discover or call APIs"""
    pass

class SynthesisError(AgentError):
    """Failed to synthesize information"""
    pass
```

### Error Handling Strategy

1. **MCP Failures**: Retry with exponential backoff (3 attempts), fallback to degraded mode
2. **Redis Failures**: Operate without memory (no learning), log warning
3. **API Failures**: Continue with available sources, note in confidence score
4. **Synthesis Failures**: Return raw results with error note
5. **All Errors**: Structured logging with request ID for tracing

## Configuration Management

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://localhost:6379
POSTMAN_API_KEY=PMAK-...

# Optional
REDIS_PASSWORD=
MCP_SERVER_CONFIG=./mcp.json
ALERT_CHANNELS=console,file:/tmp/alerts.log
REPORT_OUTPUT_DIR=./reports
LEARNING_RATE=0.1
CONFIDENCE_THRESHOLD_INITIAL=0.5
MAX_MEMORY_ENTRIES=1000
LOG_LEVEL=INFO
```

### MCP Configuration (mcp.json)

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


## Testing Strategy

### Unit Tests

```python
# test_memory_store.py
async def test_store_and_retrieve():
    """Test storing and retrieving from memory"""
    memory = MemoryStore("redis://localhost:6379")
    
    query_embedding = [0.1] * 1024
    memory_id = await memory.store(
        query="test query",
        query_embedding=query_embedding,
        results={"answer": "test"},
        sources=["api1"]
    )
    
    similar = await memory.find_similar(query_embedding, top_k=1)
    assert len(similar) == 1
    assert similar[0].query == "test query"

# test_learning_engine.py
async def test_query_refinement():
    """Test query refinement based on patterns"""
    engine = LearningEngine(memory_store, mcp_client)
    
    patterns = [
        MemoryEntry(
            query="AI trends",
            results={},
            relevance_score=0.9,
            api_sources=["tech_api"],
            similarity_score=0.8
        )
    ]
    
    refined = await engine.refine_query("AI developments", patterns)
    assert len(refined.refinements) > 0
    assert "tech_api" in refined.prioritized_sources

# test_alert_engine.py
async def test_alert_deduplication():
    """Test alert deduplication"""
    engine = AlertEngine(mcp_client)
    
    synthesis = ResearchSynthesis(
        summary="Breaking news",
        detailed_analysis="Details",
        findings=["finding1"],
        sources=["source1"],
        source_details=[],
        confidence_score=0.9,
        confidence_breakdown={}
    )
    
    alert1 = await engine.evaluate("breaking news", synthesis)
    alert2 = await engine.evaluate("breaking news", synthesis)
    
    assert alert1 is not None
    assert alert2 is None  # Duplicate suppressed
```

### Integration Tests

```python
# test_api.py
from fastapi.testclient import TestClient

client = TestClient(app)

def test_research_query_endpoint():
    """Test full research query flow"""
    response = client.post(
        "/api/research/query",
        json={
            "query": "What are the latest AI developments?",
            "max_sources": 3,
            "include_report": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "synthesized_answer" in data
    assert "sources" in data
    assert data["confidence_score"] > 0
    assert "report_path" in data

def test_feedback_loop():
    """Test feedback submission and learning"""
    # Submit query
    query_response = client.post(
        "/api/research/query",
        json={"query": "test query"}
    )
    query_id = query_response.json()["query_id"]
    
    # Submit feedback
    feedback_response = client.post(
        "/api/research/feedback",
        json={
            "query_id": query_id,
            "relevance_score": 0.9
        }
    )
    
    assert feedback_response.status_code == 200
    
    # Check metrics updated
    metrics = client.get("/api/metrics").json()
    assert metrics["total_queries"] > 0
```

### End-to-End Tests

```python
async def test_self_improvement_loop():
    """Test that agent improves over time"""
    agent = AgentOrchestrator(mcp_client, memory_store, learning_engine)
    
    # Submit same query multiple times with feedback
    query = "AI research trends"
    
    results = []
    for i in range(5):
        result = await agent.process_query(query)
        results.append(result)
        
        # Provide positive feedback
        await agent.submit_feedback(
            query_id=result.query_id,
            relevance_score=0.8 + (i * 0.04)  # Gradually improving
        )
    
    # Verify improvement
    initial_confidence = results[0].confidence_score
    final_confidence = results[-1].confidence_score
    
    assert final_confidence >= initial_confidence
    assert len(results[-1].similar_past_queries) > 0
```

## Deployment Architecture

### Local Development

```bash
# Start Redis with RediSearch
docker run -d -p 6379:6379 redis/redis-stack:latest

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Run agent
uvicorn main:app --reload --port 8000
```

### Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - POSTMAN_API_KEY=${POSTMAN_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./reports:/app/reports
      - ./mcp.json:/app/mcp.json

volumes:
  redis_data:
```

## Performance Targets

- **Query Processing**: < 5 seconds for 3 API sources
- **Memory Search**: < 100ms for top-5 similar queries
- **Report Generation**: < 2 seconds
- **Learning Loop**: Process feedback in < 500ms
- **Throughput**: 10 concurrent queries

## Observability

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "query_processed",
    query_id=query_id,
    query=query,
    sources_used=len(sources),
    confidence=confidence_score,
    processing_time_ms=processing_time,
    similar_queries_found=len(similar),
    alert_triggered=alert is not None
)
```

### Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

queries_total = Counter("queries_total", "Total queries processed")
query_duration = Histogram("query_duration_seconds", "Query processing time")
relevance_score = Histogram("relevance_score", "Relevance scores")
confidence_threshold = Gauge("confidence_threshold", "Current confidence threshold")
memory_size = Gauge("memory_size", "Number of entries in memory")
```

## Future Enhancements

1. **Multi-modal Input**: Support image and voice queries
2. **Collaborative Learning**: Share patterns across agent instances
3. **Advanced Scheduling**: Complex cron expressions, conditional triggers
4. **Custom API Integration**: Allow users to add private APIs
5. **Explainability Dashboard**: Visualize learning and decision-making
6. **A/B Testing**: Compare different learning strategies


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Query processing completeness
*For any* valid research query, the agent should return a response containing synthesized answer, sources with citations, and a confidence score between 0.0 and 1.0
**Validates: Requirements 1.1, 1.3, 1.4**

### Property 2: Memory persistence round-trip
*For any* processed query, storing it in memory and then retrieving similar queries should return the stored query with all original fields intact
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Feedback updates memory
*For any* query ID and relevance score, submitting feedback should update the corresponding memory entry's relevance score to the new value
**Validates: Requirements 3.1, 3.2**

### Property 4: Confidence threshold adaptation
*For any* sequence of feedback with high false positive rate (>20%), the confidence threshold should increase to reduce false positives
**Validates: Requirements 3.3, 7.1**

### Property 5: Source prioritization learning
*For any* API source that consistently receives high relevance scores (>=0.7) across multiple queries, its priority score should increase over time
**Validates: Requirements 3.5, 4.2**

### Property 6: Query refinement improves results
*For any* query with similar past successful queries in memory, the refined query should incorporate successful patterns from history
**Validates: Requirements 4.1, 4.2, 4.3**

### Property 7: Alert deduplication
*For any* two similar queries processed within 1 hour, if the first triggers an alert, the second should not trigger a duplicate alert
**Validates: Requirements 5.4**

### Property 8: Report structure completeness
*For any* generated report, it should contain all required sections: executive summary, key findings, detailed analysis, sources, and metadata
**Validates: Requirements 6.1, 6.2, 6.3, 6.5**

### Property 9: Metrics trend detection
*For any* sequence of queries with increasing average relevance scores, the improvement trend metric should be positive
**Validates: Requirements 7.3, 7.4**

### Property 10: MCP connection resilience
*For any* MCP connection failure, the agent should retry with exponential backoff and either succeed or gracefully degrade
**Validates: Requirements 8.5**

### Property 11: Parallel API execution
*For any* query requiring multiple API sources, all API calls should execute concurrently and complete within the timeout period
**Validates: Requirements 1.2, 1.6**

### Property 12: Memory expiration
*For any* memory entry older than 30 days, it should be automatically removed from Redis
**Validates: Requirements 2.6**

### Property 13: Session context preservation
*For any* multi-turn conversation, follow-up queries should have access to previous query results within the same session
**Validates: Requirements 15.1, 15.2, 15.3**

### Property 14: API endpoint validation
*For any* API request, all required endpoints should return appropriate HTTP status codes (200 for success, 4xx for client errors, 5xx for server errors)
**Validates: Requirements 12.7**

### Property 15: Scheduled query execution
*For any* scheduled query with a cron expression, it should execute at the specified intervals and generate reports automatically
**Validates: Requirements 13.1, 13.2, 13.5**
