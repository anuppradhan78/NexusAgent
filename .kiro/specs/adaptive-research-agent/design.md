# Design Document

## Overview

The Adaptive Research Agent demonstrates proper Model Context Protocol (MCP) implementation by building custom MCP servers that expose tools for Claude to use autonomously. The system calls Anthropic's Claude API directly for reasoning and synthesis, while providing Claude with access to custom-built MCP servers for Postman API discovery, memory storage, and report generation. This is a focused demonstration of MCP's core capabilities: giving AI assistants access to external tools through a standardized protocol.

**Key Innovations:**
- **Proper MCP Architecture**: Custom MCP servers expose tools that Claude intelligently uses
- **Autonomous Tool Selection**: Claude decides when and how to use available tools
- **Real API Integration**: Demonstrates MCP with real Postman Public API Network
- **Simple but Complete**: Focus on MCP demonstration without unnecessary complexity

---

## ⚠️ CRITICAL: Understanding MCP Architecture

**IMPORTANT NOTE:** Anthropic does NOT provide any MCP servers. This is a common source of confusion.

**What Anthropic Provides:**
- ✅ **Claude API** - The LLM service you call directly
- ✅ **Python SDK** (`anthropic`) - For calling Claude API
- ✅ **JavaScript SDK** (`@anthropic-ai/sdk`) - For calling Claude API  
- ✅ **MCP Documentation** - Explaining how Claude can use MCP tools

**What Anthropic Does NOT Provide:**
- ❌ **`@anthropic-ai/mcp-server-anthropic`** - This package does not exist
- ❌ **Any pre-built MCP servers** - You must build your own
- ❌ **MCP servers for calling Claude** - You call Claude directly via their SDK

**How MCP Actually Works:**
1. **Your application** calls Claude directly using the Anthropic SDK
2. **You build** custom MCP servers that expose tools (we build 3: Postman, Memory, Research Tools)
3. **Claude decides** which of your tools to use based on the query
4. **Your application** routes tool calls to your MCP servers via the MCP SDK
5. **Your MCP servers** execute the tools and return results
6. **Claude synthesizes** the final response from all tool results

**The Correct Flow:**
```
Your App → Claude API (direct call via anthropic SDK)
              ↓
         Claude receives tool definitions
              ↓
         Claude decides: "I need to search APIs"
              ↓
Your App → Your Postman MCP Server → Postman API
              ↓
         Results back to Claude
              ↓
         Claude: "Now I need to call that API"
              ↓
Your App → Your Postman MCP Server → Execute API call
              ↓
         Results back to Claude
              ↓
         Claude synthesizes final answer
```

**Why This Matters:**
- MCP is a **protocol specification** created by Anthropic
- You use the **MCP SDK** (`@modelcontextprotocol/sdk`) to build servers
- Claude is the **consumer** of MCP tools, not the provider
- This architecture enables Claude to use ANY tools you build

---

## Architecture

### High-Level Architecture

```text
USER LAYER:
  [API Clients] [CLI Tools]
           |       |
           +-------+
                |
                v
API LAYER (FastAPI):
    [POST /api/research/query]
    [GET /api/research/history]
    [GET /api/reports]
    [GET /health]
                |
                v
AGENT ORCHESTRATION:
    [Agent Orchestrator]
                |
                v
    [Claude API Client] ──────> [Anthropic Claude API]
    (anthropic Python SDK)           (Direct)
                |
                | Claude decides to use tools
                v
    [MCP Tool Router]
                |
                v
    ┌───────────┴───────────┐
    |           |           |
    v           v           v
[Postman]   [Memory]   [Research]
  MCP         MCP         MCP
 Server      Server      Server
    |           |           |
    v           v           v
[Postman]   [Redis]    [Reports]
  API       Storage    Generator
```

**CUSTOM MCP SERVERS (We Build):**

1. **Postman MCP Server** (Node.js/TypeScript)
   - Tools: search_apis, call_api, get_api_details
   - Connects to: Postman Public API Network

2. **Memory MCP Server** (Node.js/TypeScript)
   - Tools: store_result, get_history
   - Connects to: Redis for simple storage

3. **Research Tools MCP Server** (Node.js/TypeScript)
   - Tools: generate_report
   - Connects to: File system for markdown reports


### Technology Stack

**Core Framework (Python):**
- Python 3.11+
- FastAPI 0.110+ (REST API)
- Pydantic 2.0+ (data validation)
- asyncio (async operations)

**AI Integration:**
- anthropic Python SDK (Direct Claude API access)
- Anthropic Claude (claude-3-5-sonnet-20241022)

**MCP Implementation (Node.js/TypeScript):**
- @modelcontextprotocol/sdk (MCP server framework)
- Node.js 18+ (for MCP servers)
- TypeScript 5+ (type-safe MCP server development)
- Three custom MCP servers we build:
  1. Postman MCP Server
  2. Memory MCP Server  
  3. Research Tools MCP Server

**Memory & Storage:**
- Redis 7.2+ (simple key-value storage)
- redis-py client
- ioredis (Node.js Redis client for MCP servers)

**Observability:**
- Python structlog (structured logging)

**Development:**
- pytest (testing)
- httpx (async HTTP client)
- python-dotenv (configuration)

### Deployment Model

- Backend: FastAPI with uvicorn ASGI server
- Redis: Docker container for simple storage
- MCP Servers: Three custom Node.js servers running locally
- Development: All services running locally
- Configuration: Environment variables + mcp.json for MCP server paths

## Components and Interfaces

### Architecture Overview

The system is split into two main parts:

1. **Python Application** (FastAPI) - Core orchestration and REST API
2. **Node.js MCP Servers** (TypeScript) - Custom tools that Claude can use

**Communication Flow:**
```
User Request → FastAPI → Claude API (with tool definitions)
                              ↓
                    Claude decides to use tools
                              ↓
                    MCP Tool Router → Specific MCP Server
                              ↓
                    Tool executes → Returns result to Claude
                              ↓
                    Claude synthesizes → Response to user
```

**Key Principles:**
- We call Claude directly via the Anthropic Python SDK (NOT through an MCP server)
- Claude autonomously decides which MCP tools to use
- Our custom MCP servers expose tools like `search_apis`, `call_api`, `store_result`, and `generate_report`
- The MCP SDK (`@modelcontextprotocol/sdk`) is used to BUILD our servers, not to call Claude

**Remember:** There is no "Anthropic MCP server" or "Claude MCP server" - those don't exist. You call Claude directly, and Claude uses YOUR MCP servers as tools.

### MCP Servers (Node.js/TypeScript)

We build three custom MCP servers that expose tools for Claude:

#### 1. Postman MCP Server (`mcp-servers/postman/`)

**Purpose**: Expose Postman Public API Network to Claude

**Tools Exposed:**
- `search_apis(query: string)` - Search for relevant APIs
- `call_api(api_id: string, endpoint: string, params: object)` - Execute API request
- `get_api_details(api_id: string)` - Get API documentation

**Implementation**: TypeScript using @modelcontextprotocol/sdk

#### 2. Memory MCP Server (`mcp-servers/memory/`)

**Purpose**: Expose Redis storage to Claude for query history

**Tools Exposed:**
- `store_result(query: string, results: object, timestamp: number)` - Save query results
- `get_history(limit: number)` - Retrieve past queries

**Implementation**: TypeScript using @modelcontextprotocol/sdk + ioredis

#### 3. Research Tools MCP Server (`mcp-servers/research-tools/`)

**Purpose**: Expose report generation to Claude

**Tools Exposed:**
- `generate_report(query: string, data: object, sources: array)` - Create markdown reports

**Implementation**: TypeScript using @modelcontextprotocol/sdk

### Python Application Components

### 1. FastAPI Server (main.py)

**Purpose**: REST API exposing agent capabilities

**Endpoints:**

```python
@app.post("/api/research/query")
async def research_query(request: ResearchRequest) -> ResearchResponse:
    """
    Process research query using Claude with MCP tools
    
    Request:
        {
            "query": "What are the latest trends in AI?",
            "max_sources": 5,
            "include_report": true
        }
    
    Response:
        {
            "query_id": "uuid",
            "synthesized_answer": "...",
            "sources": [...],
            "report_path": "/reports/2025-11-23_12-30-45.md",
            "processing_time_ms": 2500
        }
    """

@app.get("/api/research/history")
async def get_history(
    limit: int = 50,
    offset: int = 0
) -> HistoryResponse:
    """Get past queries with pagination"""

@app.get("/api/reports")
async def list_reports(limit: int = 20) -> ReportsListResponse:
    """List generated reports"""

@app.get("/api/reports/{report_id}")
async def get_report(report_id: str) -> ReportContent:
    """Get specific report content"""

@app.get("/health")
async def health_check() -> HealthResponse:
    """Service health check"""
```


### 2. Agent Orchestrator (agent_orchestrator.py)

**Purpose**: Core agent logic coordinating Claude and MCP tools

**Main Flow:**

```python
class AgentOrchestrator:
    def __init__(
        self,
        claude_client: ClaudeClient,
        mcp_tool_router: MCPToolRouter
    ):
        """Initialize agent with Claude client and MCP tool router"""
    
    async def process_query(
        self,
        query: str,
        max_sources: int = 5,
        include_report: bool = True
    ) -> ResearchResult:
        """
        Main agent processing pipeline using Claude with MCP tools:
        1. Call Claude with query and available MCP tools
        2. Claude decides which tools to use (search_apis, call_api, etc.)
        3. Execute tool calls via MCP servers
        4. Return results to Claude for synthesis
        5. Claude generates final response
        6. Store results and optionally generate report
        """
        
        # Step 1: Prepare tool definitions for Claude
        available_tools = self.mcp_tool_router.get_tool_definitions()
        
        # Step 2: Call Claude with tools
        response = await self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=available_tools,
            messages=[{
                "role": "user",
                "content": f"Research query: {query}. Use available tools to gather information."
            }]
        )
        
        # Step 3: Handle tool calls from Claude
        tool_results = []
        while response.stop_reason == "tool_use":
            for content_block in response.content:
                if content_block.type == "tool_use":
                    # Execute tool via appropriate MCP server
                    result = await self.mcp_tool_router.execute_tool(
                        tool_name=content_block.name,
                        tool_input=content_block.input
                    )
                    tool_results.append({
                        "tool_use_id": content_block.id,
                        "content": result
                    })
            
            # Continue conversation with tool results
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                tools=available_tools,
                messages=[
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": tool_results}
                ]
            )
        
        # Step 4: Extract final synthesis from Claude
        synthesis = self._extract_synthesis(response)
        
        # Step 5: Store in memory (via Memory MCP Server)
        await self.mcp_tool_router.execute_tool(
            "store_result",
            {"query": query, "results": synthesis, "score": 0.5}
        )
        
        return ResearchResult(
            synthesis=synthesis,
            tool_calls_made=len(tool_results),
            claude_response=response
        )
```

### 3. Claude Client (claude_client.py)

**Purpose**: Direct interface with Anthropic Claude API

**Implementation:**

```python
from anthropic import Anthropic

class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    def call_with_tools(
        self,
        messages: list,
        tools: list,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """Call Claude with tool definitions"""
        return self.client.messages.create(
            model=model,
            max_tokens=4096,
            tools=tools,
            messages=messages
        )
```

**Note**: The Anthropic Python SDK provides synchronous methods. We wrap calls in async functions in the orchestrator if needed.

### 4. MCP Tool Router (mcp_tool_router.py)

**Purpose**: Route tool calls from Claude to appropriate MCP servers

**Implementation:**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, Any, List
import asyncio

class MCPToolRouter:
    """Routes tool calls to our custom MCP servers"""
    
    def __init__(self, mcp_config: dict):
        """
        Initialize with MCP server configurations
        
        mcp_config format:
        {
            "postman": {"command": "node", "args": ["mcp-servers/postman/index.js"]},
            "memory": {"command": "node", "args": ["mcp-servers/memory/index.js"]},
            "research": {"command": "node", "args": ["mcp-servers/research-tools/index.js"]}
        }
        """
        self.mcp_config = mcp_config
        self.sessions = {}
        self.tool_registry = {}
    
    async def connect_all(self):
        """Connect to all MCP servers and discover their tools"""
        for server_name, config in self.mcp_config.items():
            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=config.get("env", {})
            )
            
            # Connect to MCP server
            read_stream, write_stream = await stdio_client(server_params).__aenter__()
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            
            self.sessions[server_name] = session
            
            # Discover tools from this server
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                self.tool_registry[tool.name] = server_name
    
    def get_tool_definitions(self) -> List[Dict]:
        """Get all tool definitions for Claude from all connected MCP servers"""
        all_tools = []
        
        for server_name, session in self.sessions.items():
            # Get tools from each MCP server
            # MCP servers expose their tool schemas
            tools_result = asyncio.run(session.list_tools())
            for tool in tools_result.tools:
                all_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
        
        return all_tools
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Any:
        """Execute a tool by routing to appropriate MCP server"""
        server_name = self.tool_registry.get(tool_name)
        if not server_name:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        session = self.sessions[server_name]
        
        # Call tool via MCP protocol
        result = await session.call_tool(tool_name, arguments=tool_input)
        return result.content
    
    async def close_all(self):
        """Close all MCP server connections"""
        for session in self.sessions.values():
            # Properly close MCP sessions
            pass
```


### 5. Memory Store (memory_store.py)

**Purpose**: Simple Redis storage for query history

**Implementation:**

```python
import redis
import json
import time
import uuid
from typing import List, Optional

class MemoryStore:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url, decode_responses=True)
    
    async def store(
        self,
        query: str,
        results: dict,
        sources: List[str]
    ) -> str:
        """Store query and results in Redis"""
        query_id = f"query:{uuid.uuid4()}"
        
        self.client.hset(
            query_id,
            mapping={
                "query_text": query,
                "results_summary": json.dumps(results),
                "timestamp": time.time(),
                "api_sources": json.dumps(sources)
            }
        )
        
        # Set expiration (30 days)
        self.client.expire(query_id, 30 * 24 * 60 * 60)
        
        # Add to sorted set for chronological retrieval
        self.client.zadd("queries:timeline", {query_id: time.time()})
        
        return query_id
    
    async def get_history(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get past queries in chronological order"""
        # Get query IDs from sorted set (most recent first)
        query_ids = self.client.zrevrange(
            "queries:timeline",
            offset,
            offset + limit - 1
        )
        
        queries = []
        for query_id in query_ids:
            data = self.client.hgetall(query_id)
            if data:
                queries.append({
                    "query_id": query_id,
                    "query": data.get("query_text"),
                    "results": json.loads(data.get("results_summary", "{}")),
                    "sources": json.loads(data.get("api_sources", "[]")),
                    "timestamp": float(data.get("timestamp", 0))
                })
        
        return queries
```

**Note**: This is a simplified storage implementation. The Memory MCP Server will expose `store_result` and `get_history` tools that use this store.


### 6. Report Generator (report_generator.py)

**Purpose**: Generate markdown reports (called via Research Tools MCP Server)

**Implementation:**

```python
from pathlib import Path
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        query: str,
        synthesized_answer: str,
        sources: List[dict],
        metadata: dict = None
    ) -> str:
        """Generate markdown research report"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"research_report_{timestamp}.md"
        filepath = self.output_dir / filename
        
        report_content = self._build_report(
            query=query,
            answer=synthesized_answer,
            sources=sources,
            metadata=metadata or {}
        )
        
        filepath.write_text(report_content)
        
        return str(filepath)
    
    def _build_report(
        self,
        query: str,
        answer: str,
        sources: List[dict],
        metadata: dict
    ) -> str:
        """Build markdown report content"""
        
        report = f"""# Research Report: {query}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Query ID:** {metadata.get('query_id', 'N/A')}  
**Processing Time:** {metadata.get('processing_time_ms', 0)}ms

---

## Answer

{answer}

---

## Sources

{self._format_sources(sources)}

---

*Generated by Adaptive Research Agent*
"""
        return report
    
    def _format_sources(self, sources: List[dict]) -> str:
        """Format sources as markdown list"""
        if not sources:
            return "No sources available."
        
        formatted = []
        for i, source in enumerate(sources, 1):
            formatted.append(f"{i}. **{source.get('api_name', 'Unknown')}**")
            formatted.append(f"   - API ID: {source.get('api_id', 'N/A')}")
            formatted.append(f"   - Endpoint: {source.get('endpoint', 'N/A')}")
            formatted.append("")
        
        return "\n".join(formatted)
```

**Note**: This component is used by the Research Tools MCP Server to generate reports when Claude calls the `generate_report` tool.hSynthesis) -> bool:
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
from typing import List, Optional
from datetime import datetime

class ResearchRequest(BaseModel):
    """API request for research query"""
    query: str = Field(..., min_length=10, max_length=500)
    max_sources: int = Field(default=5, ge=1, le=10)
    include_report: bool = True

class APISource(BaseModel):
    """API source information"""
    api_id: str
    api_name: str
    endpoint: str
    verified: bool = False

class ResearchResponse(BaseModel):
    """API response for research query"""
    query_id: str
    synthesized_answer: str
    sources: List[APISource]
    report_path: Optional[str]
    processing_time_ms: int

class HistoryEntry(BaseModel):
    """Query history entry"""
    query_id: str
    query: str
    results: dict
    sources: List[str]
    timestamp: float

class HistoryResponse(BaseModel):
    """Response for history endpoint"""
    queries: List[HistoryEntry]
    total: int
    limit: int
    offset: int

class ReportInfo(BaseModel):
    """Report metadata"""
    report_id: str
    filename: str
    query: str
    timestamp: datetime

class ReportsListResponse(BaseModel):
    """Response for reports list endpoint"""
    reports: List[ReportInfo]
    total: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    redis_connected: bool
    mcp_servers_connected: int
    timestamp: datetime
```

### MCP Tool Models

```python
class ToolDefinition(BaseModel):
    """MCP tool definition for Claude"""
    name: str
    description: str
    input_schema: dict

class ToolCall(BaseModel):
    """Tool call from Claude"""
    tool_use_id: str
    tool_name: str
    tool_input: dict

class ToolResult(BaseModel):
    """Result from tool execution"""
    tool_use_id: str
    content: any
    is_error: bool = False
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
REPORT_OUTPUT_DIR=./reports
LOG_LEVEL=INFO
```

### MCP Server Configuration

Our custom MCP servers are Node.js applications that we build. They are started separately and the Python application connects to them via stdio.

**MCP Server Paths** (configured in Python app):
```python
MCP_CONFIG = {
    "postman": {
        "command": "node",
        "args": ["mcp-servers/postman/index.js"],
        "env": {"POSTMAN_API_KEY": os.getenv("POSTMAN_API_KEY")}
    },
    "memory": {
        "command": "node",
        "args": ["mcp-servers/memory/index.js"],
        "env": {"REDIS_URL": os.getenv("REDIS_URL")}
    },
    "research": {
        "command": "node",
        "args": ["mcp-servers/research-tools/index.js"],
        "env": {"REPORT_OUTPUT_DIR": os.getenv("REPORT_OUTPUT_DIR")}
    }
}
```


## Testing Strategy

### Unit Tests

Focus on testing individual components in isolation:

```python
# test_memory_store.py
async def test_store_and_retrieve():
    """Test storing and retrieving from Redis"""
    memory = MemoryStore("redis://localhost:6379")
    
    query_id = await memory.store(
        query="test query",
        results={"answer": "test"},
        sources=["api1"]
    )
    
    history = await memory.get_history(limit=1)
    assert len(history) == 1
    assert history[0]["query"] == "test query"

# test_report_generator.py
def test_report_generation():
    """Test markdown report generation"""
    generator = ReportGenerator("./test_reports")
    
    report_path = generator.generate(
        query="test query",
        synthesized_answer="test answer",
        sources=[{"api_name": "Test API", "api_id": "123", "endpoint": "/test"}],
        metadata={"query_id": "test-123"}
    )
    
    assert Path(report_path).exists()
    content = Path(report_path).read_text()
    assert "test query" in content
    assert "test answer" in content
```

### Integration Tests

Test the full flow with mocked MCP servers:

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
    assert "report_path" in data

def test_history_endpoint():
    """Test query history retrieval"""
    # First submit a query
    client.post(
        "/api/research/query",
        json={"query": "test query"}
    )
    
    # Then get history
    response = client.get("/api/research/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "queries" in data
    assert len(data["queries"]) > 0
```

### MCP Server Tests

Test each custom MCP server independently:

```python
# test_postman_mcp_server.py
async def test_search_apis_tool():
    """Test Postman MCP server search_apis tool"""
    # Connect to Postman MCP server
    session = await connect_to_mcp_server("postman")
    
    # Call search_apis tool
    result = await session.call_tool(
        "search_apis",
        arguments={"query": "weather", "verified_only": True}
    )
    
    assert result.content is not None
    assert isinstance(result.content, list)

# test_memory_mcp_server.py
async def test_store_result_tool():
    """Test Memory MCP server store_result tool"""
    session = await connect_to_mcp_server("memory")
    
    result = await session.call_tool(
        "store_result",
        arguments={
            "query": "test",
            "results": {"answer": "test"},
            "timestamp": time.time()
        }
    )
    
    assert result.content["success"] == True
```

## Deployment

### Local Development

```bash
# 1. Start Redis
docker run -d -p 6379:6379 redis:latest

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Build MCP servers
cd mcp-servers/postman && npm install && npm run build
cd ../memory && npm install && npm run build
cd ../research-tools && npm install && npm run build

# 4. Configure environment
cp .env.example .env
# Edit .env with API keys

# 5. Run FastAPI application
uvicorn main:app --reload --port 8000
```

**Note**: The Python application will automatically start the MCP servers as subprocesses using the MCP SDK's stdio transport.

### Logging

Simple structured logging with Python's structlog:

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

    query=query,
    sources_used=len(sources),
    processing_time_ms=processing_time,
    mcp_tools_called=tool_count
)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Claude tool calling workflow
*For any* valid research query, Claude should receive tool definitions, make tool calls to MCP servers, and synthesize results into a coherent response
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**

### Property 2: MCP server tool exposure
*For any* custom MCP server (Postman, Memory, Research Tools), it should expose its tools with valid schemas that Claude can discover and call
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

### Property 3: MCP tool routing
*For any* tool call from Claude, the MCP Tool Router should route it to the correct MCP server and return the result to Claude
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

### Property 4: Redis storage round-trip
*For any* query and results stored in Redis, retrieving the history should return the stored data with all fields intact
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

### Property 5: Report generation completeness
*For any* generated report, it should contain the query, synthesized answer, sources, and timestamp in valid markdown format
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6**

### Property 6: API endpoint responses
*For any* API endpoint, it should return appropriate HTTP status codes (200 for success, 4xx for client errors, 5xx for server errors) and structured JSON
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7**

### Property 7: Configuration validation
*For any* required environment variable (ANTHROPIC_API_KEY, POSTMAN_API_KEY, REDIS_URL), if missing, the system should fail to start with a clear error message
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7**

### Property 8: Error handling and logging
*For any* error (Claude API failure, MCP failure, Redis failure), the system should log it with context and handle it gracefully
**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6**

### Property 9: MCP connection resilience
*For any* MCP server connection failure, the system should retry with exponential backoff (3 attempts) and either succeed or gracefully degrade
**Validates: Requirements 8.5**

### Property 10: Memory expiration
*For any* memory entry older than 30 days, it should be automatically removed from Redis
**Validates: Requirements 4.5**
