"""
FastAPI Server - Main application entry point
"""
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from dotenv import load_dotenv

from models import (
    ResearchRequest,
    ResearchResponse,
    HistoryResponse,
    ReportsListResponse,
    HealthResponse
)
from claude_client import ClaudeClient
from mcp_tool_router import MCPToolRouter
from memory_store import MemoryStore
from report_generator import ReportGenerator
from agent_orchestrator import AgentOrchestrator

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Global components
claude_client = None
mcp_tool_router = None
memory_store = None
report_generator = None
agent_orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global claude_client, mcp_tool_router, memory_store, report_generator, agent_orchestrator
    
    logger.info("Starting Adaptive Research Agent...")
    
    # Validate required environment variables
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.error("ANTHROPIC_API_KEY is required")
        sys.exit(1)
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    report_dir = os.getenv("REPORT_OUTPUT_DIR", "./reports")
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        
        # Claude Client
        claude_client = ClaudeClient(anthropic_key)
        logger.info("Claude client initialized")
        
        # MCP Tool Router
        mcp_tool_router = MCPToolRouter()
        await mcp_tool_router.connect_all()
        logger.info("MCP Tool Router initialized")
        
        # Memory Store
        try:
            memory_store = MemoryStore(redis_url)
            logger.info("Memory store initialized")
        except Exception as e:
            logger.warning("Redis unavailable, running in degraded mode", error=str(e))
            memory_store = None
        
        # Report Generator
        report_generator = ReportGenerator(report_dir)
        logger.info("Report generator initialized")
        
        # Agent Orchestrator
        agent_orchestrator = AgentOrchestrator(claude_client, mcp_tool_router)
        logger.info("Agent orchestrator initialized")
        
        logger.info("Adaptive Research Agent started successfully")
        
        yield
        
        # Shutdown
        logger.info("Shutting down...")
        if mcp_tool_router:
            await mcp_tool_router.close_all()
        logger.info("Shutdown complete")
        
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        sys.exit(1)


# Create FastAPI app
app = FastAPI(
    title="Adaptive Research Agent",
    description="MCP-powered research agent with Claude",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests"""
    import uuid
    request_id = str(uuid.uuid4())
    
    # Add to structlog context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.post("/api/research/query", response_model=ResearchResponse)
async def research_query(request: ResearchRequest):
    """
    Process research query using Claude with MCP tools
    """
    try:
        logger.info("Received research query", query=request.query)
        
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        result = await agent_orchestrator.process_query(
            query=request.query,
            max_sources=request.max_sources,
            include_report=request.include_report
        )
        
        return ResearchResponse(**result)
        
    except Exception as e:
        logger.error("Query processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.get("/api/research/history", response_model=HistoryResponse)
async def get_history(limit: int = 50, offset: int = 0):
    """
    Get past queries with pagination
    """
    try:
        if not memory_store:
            return HistoryResponse(queries=[], total=0, limit=limit, offset=offset)
        
        queries = await memory_store.get_history(limit=limit, offset=offset)
        
        return HistoryResponse(
            queries=queries,
            total=len(queries),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error("Failed to get history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@app.get("/api/reports", response_model=ReportsListResponse)
async def list_reports(limit: int = 20):
    """
    List all generated reports
    """
    try:
        if not report_generator:
            raise HTTPException(status_code=503, detail="Report generator not initialized")
        
        reports = report_generator.list_reports(limit=limit)
        
        return ReportsListResponse(
            reports=reports,
            total=len(reports)
        )
        
    except Exception as e:
        logger.error("Failed to list reports", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """
    Get specific report content
    """
    try:
        if not report_generator:
            raise HTTPException(status_code=503, detail="Report generator not initialized")
        
        content = report_generator.get_report(report_id)
        
        return JSONResponse(content={"report_id": report_id, "content": content})
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")
    except Exception as e:
        logger.error("Failed to get report", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Service health check
    """
    redis_connected = False
    if memory_store:
        try:
            memory_store.client.ping()
            redis_connected = True
        except:
            pass
    
    mcp_servers_connected = len(mcp_tool_router.tool_registry) if mcp_tool_router else 0
    
    status = "healthy" if redis_connected and mcp_servers_connected > 0 else "degraded"
    
    return HealthResponse(
        status=status,
        redis_connected=redis_connected,
        mcp_servers_connected=mcp_servers_connected,
        timestamp=datetime.now()
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
