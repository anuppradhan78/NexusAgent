"""
Adaptive Research Agent - Main FastAPI Application
"""
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from dotenv import load_dotenv

# Import models and components
import models
from models import (
    ResearchRequest,
    ResearchResponse,
    APISource,
    MemoryEntry,
    ErrorResponse
)
from agent_orchestrator import AgentOrchestrator, AgentOrchestratorError
from mcp_client import MCPClient, MCPConnectionError
from memory_store import MemoryStore, MemoryStoreError

# Load environment variables
load_dotenv()

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


# Configuration class
class Config:
    """Application configuration loaded from environment variables"""
    
    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    POSTMAN_API_KEY: str = os.getenv("POSTMAN_API_KEY", "")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # MCP Server Configuration
    MCP_SERVER_CONFIG: str = os.getenv("MCP_SERVER_CONFIG", "{}")
    
    # Alert Configuration
    ALERT_CHANNELS: str = os.getenv("ALERT_CHANNELS", "console")
    
    # Report Configuration
    REPORT_OUTPUT_DIR: str = os.getenv("REPORT_OUTPUT_DIR", "./reports")
    
    # Learning Configuration
    LEARNING_RATE: float = float(os.getenv("LEARNING_RATE", "0.1"))
    CONFIDENCE_THRESHOLD_INITIAL: float = float(os.getenv("CONFIDENCE_THRESHOLD_INITIAL", "0.5"))
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration and return list of missing variables"""
        missing = []
        
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        
        # Note: POSTMAN_API_KEY is optional for basic functionality
        # REDIS_PASSWORD is optional for local development
        
        return missing


# Global instances (initialized during startup)
mcp_client: Optional[MCPClient] = None
memory_store: Optional[MemoryStore] = None
agent_orchestrator: Optional[AgentOrchestrator] = None


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    global mcp_client, memory_store, agent_orchestrator
    
    # Startup
    logger.info(
        "application_starting",
        host=Config.HOST,
        port=Config.PORT,
        log_level=Config.LOG_LEVEL
    )
    
    # Validate configuration
    missing_vars = Config.validate()
    if missing_vars:
        logger.warning(
            "missing_environment_variables",
            missing=missing_vars,
            message="Some features may not work without these variables"
        )
    
    # Create reports directory if it doesn't exist
    os.makedirs(Config.REPORT_OUTPUT_DIR, exist_ok=True)
    logger.info("reports_directory_ready", path=Config.REPORT_OUTPUT_DIR)
    
    # Initialize components
    try:
        # Initialize MCP client
        logger.info("initializing_mcp_client")
        mcp_client = MCPClient()
        await mcp_client.initialize()
        logger.info("mcp_client_initialized")
        
        # Initialize memory store
        logger.info("initializing_memory_store")
        memory_store = MemoryStore(
            redis_url=Config.REDIS_URL,
            redis_password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None
        )
        logger.info("memory_store_initialized")
        
        # Initialize agent orchestrator
        logger.info("initializing_agent_orchestrator")
        agent_orchestrator = AgentOrchestrator(
            mcp_client=mcp_client,
            memory_store=memory_store
        )
        logger.info("agent_orchestrator_initialized")
        
    except Exception as e:
        logger.error(
            "initialization_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        # Continue startup but log warning
        logger.warning("application_starting_in_degraded_mode")
    
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    
    # Cleanup
    if mcp_client:
        try:
            await mcp_client.close()
        except Exception as e:
            logger.warning("mcp_client_close_error", error=str(e))
    
    if memory_store:
        try:
            memory_store.close()
        except Exception as e:
            logger.warning("memory_store_close_error", error=str(e))
    
    logger.info("application_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title="Adaptive Research Agent",
    description="Autonomous, self-improving AI research system",
    version="1.0.0",
    lifespan=lifespan
)


# Middleware to add request ID to all requests
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request for tracing"""
    request_id = str(uuid.uuid4())
    
    # Add request ID to structured logging context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )
    
    # Log incoming request
    logger.info(
        "request_received",
        client_host=request.client.host if request.client else None
    )
    
    # Process request
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Log response
    logger.info(
        "request_completed",
        status_code=response.status_code
    )
    
    return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Research Query Endpoint
@app.post("/api/research/query", response_model=ResearchResponse)
async def research_query(request: ResearchRequest):
    """
    Process research query and return synthesized results.
    
    Requirements:
    - 12.1: POST endpoint accepting natural language queries
    - 12.7: Handle errors gracefully with appropriate status codes
    - 1.1: Parse intent and identify relevant API sources
    - 1.3: Synthesize information from multiple sources
    - 1.4: Include source citations with confidence scores
    - 1.5: Handle API failures gracefully
    
    Args:
        request: ResearchRequest with query and options
        
    Returns:
        ResearchResponse: Synthesized answer with sources and metadata
        
    Raises:
        HTTPException: If processing fails
    """
    # Check if agent orchestrator is initialized
    if not agent_orchestrator:
        logger.error("agent_orchestrator_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Agent orchestrator not initialized."
        )
    
    logger.info(
        "research_query_received",
        query=request.query[:100],
        session_id=request.session_id,
        max_sources=request.max_sources
    )
    
    try:
        # Process query through agent orchestrator
        result = await agent_orchestrator.process_query(
            query=request.query,
            session_id=request.session_id,
            max_sources=request.max_sources,
            timeout=30
        )
        
        # Convert APIEndpoint objects to APISource models
        api_sources = []
        for source_detail in result.synthesis.source_details:
            # Find corresponding API result for response time
            response_time = None
            for api_result in result.api_results:
                if api_result.api_id == source_detail.api_id:
                    response_time = api_result.response_time_ms
                    break
            
            api_sources.append(APISource(
                api_id=source_detail.api_id,
                api_name=source_detail.api_name,
                endpoint=source_detail.endpoint,
                method=source_detail.method,
                verified=source_detail.verified,
                priority_score=source_detail.priority_score,
                response_time_ms=response_time
            ))
        
        # Convert MemoryEntry dataclasses to Pydantic models
        memory_entries = []
        for mem in result.similar_queries:
            memory_entries.append(MemoryEntry(
                memory_id=mem.memory_id,
                query=mem.query,
                results=mem.results,
                relevance_score=mem.relevance_score,
                api_sources=mem.api_sources,
                similarity_score=mem.similarity_score,
                timestamp=mem.timestamp,
                session_id=mem.session_id
            ))
        
        # Build response
        response = ResearchResponse(
            query_id=result.query_id,
            session_id=request.session_id or result.query_id,
            synthesized_answer=result.synthesis.summary,
            detailed_analysis=result.synthesis.detailed_analysis,
            findings=result.synthesis.findings,
            sources=api_sources,
            confidence_score=result.synthesis.confidence_score,
            alert_triggered=False,  # TODO: Implement alert engine in Phase 4
            report_path=None,  # TODO: Implement report generator in Phase 4
            processing_time_ms=result.processing_time_ms,
            similar_past_queries=memory_entries,
            memory_id=result.memory_id,
            refinement_applied=result.refined_query is not None and len(result.refined_query.refinements) > 0,
            refinements=result.refined_query.refinements if result.refined_query else [],
            refinement_confidence=result.refined_query.confidence if result.refined_query else 0.5
        )
        
        logger.info(
            "research_query_completed",
            query_id=result.query_id,
            processing_time_ms=result.processing_time_ms,
            confidence_score=result.synthesis.confidence_score,
            sources_count=len(api_sources)
        )
        
        return response
        
    except AgentOrchestratorError as e:
        logger.error(
            "agent_orchestrator_error",
            error=str(e),
            query=request.query[:100]
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )
    
    except MCPConnectionError as e:
        logger.error(
            "mcp_connection_error",
            error=str(e),
            query=request.query[:100]
        )
        raise HTTPException(
            status_code=503,
            detail="MCP service unavailable. Please try again later."
        )
    
    except MemoryStoreError as e:
        logger.warning(
            "memory_store_error",
            error=str(e),
            query=request.query[:100]
        )
        # Continue without memory - graceful degradation
        # This should be handled by the orchestrator, but catch here as backup
        raise HTTPException(
            status_code=500,
            detail=f"Memory store error: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
            query=request.query[:100]
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your query."
        )


# Feedback Endpoint
@app.post("/api/research/feedback", response_model=models.FeedbackResponse)
async def submit_feedback(feedback: models.FeedbackRequest):
    """
    Submit relevance feedback for learning.
    
    Requirements:
    - 12.2: POST endpoint accepting relevance scores
    - 3.1: Accept relevance feedback and update memory
    - 3.2: Update Relevance_Score for corresponding memory entry
    - 3.6: Log feedback for analysis
    
    Args:
        feedback: FeedbackRequest with query_id, memory_id, and relevance_score
        
    Returns:
        FeedbackResponse: Confirmation of feedback submission
        
    Raises:
        HTTPException: If feedback submission fails
    """
    # Check if memory store is initialized
    if not memory_store:
        logger.error("memory_store_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Memory store not initialized."
        )
    
    logger.info(
        "feedback_received",
        query_id=feedback.query_id,
        memory_id=feedback.memory_id,
        relevance_score=feedback.relevance_score,
        has_notes=bool(feedback.feedback_notes)
    )
    
    try:
        # Update memory entry with new relevance score
        # Requirement 3.1, 3.2: Update memory with feedback
        success = await memory_store.update_relevance(
            memory_id=feedback.memory_id,
            new_score=feedback.relevance_score
        )
        
        if not success:
            logger.warning(
                "memory_not_found_for_feedback",
                memory_id=feedback.memory_id,
                query_id=feedback.query_id
            )
            raise HTTPException(
                status_code=404,
                detail=f"Memory entry not found: {feedback.memory_id}"
            )
        
        # Trigger learning engine to adjust thresholds
        # Requirement 3.3: Adjust confidence thresholds based on feedback
        if agent_orchestrator and agent_orchestrator.learning_engine:
            try:
                # Get recent feedback for threshold adjustment
                recent_memories = await memory_store.get_recent(limit=50)
                
                # Convert to FeedbackEntry format for learning engine
                from learning_engine import FeedbackEntry
                recent_feedback = []
                for mem in recent_memories:
                    # Estimate confidence from relevance (simplified)
                    # In production, we'd store actual confidence scores
                    estimated_confidence = mem.relevance_score
                    recent_feedback.append(FeedbackEntry(
                        query_id=mem.memory_id,
                        confidence=estimated_confidence,
                        relevance_score=mem.relevance_score,
                        timestamp=mem.timestamp
                    ))
                
                # Adjust threshold based on feedback patterns
                new_threshold = await agent_orchestrator.learning_engine.adjust_confidence_threshold(
                    recent_feedback=recent_feedback
                )
                
                logger.info(
                    "confidence_threshold_updated",
                    new_threshold=new_threshold,
                    feedback_count=len(recent_feedback)
                )
            except Exception as e:
                # Log but don't fail the request if threshold adjustment fails
                logger.warning(
                    "threshold_adjustment_failed",
                    error=str(e),
                    memory_id=feedback.memory_id
                )
        
        # Log feedback for analysis (Requirement 3.6)
        logger.info(
            "feedback_processed",
            query_id=feedback.query_id,
            memory_id=feedback.memory_id,
            relevance_score=feedback.relevance_score,
            feedback_notes=feedback.feedback_notes[:100] if feedback.feedback_notes else None
        )
        
        # Build response
        response = models.FeedbackResponse(
            success=True,
            message="Feedback recorded successfully",
            memory_id=feedback.memory_id,
            new_relevance_score=feedback.relevance_score
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except MemoryStoreError as e:
        logger.error(
            "memory_store_error_feedback",
            error=str(e),
            memory_id=feedback.memory_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update memory: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "feedback_submission_error",
            error=str(e),
            error_type=type(e).__name__,
            memory_id=feedback.memory_id
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing feedback."
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns service status and configuration validation.
    Requirements: 12.6, 14.1, 14.2
    """
    missing_vars = Config.validate()
    
    health_status = {
        "status": "healthy" if not missing_vars else "degraded",
        "service": "adaptive-research-agent",
        "version": "1.0.0",
        "configuration": {
            "redis_configured": bool(Config.REDIS_URL),
            "anthropic_configured": bool(Config.ANTHROPIC_API_KEY),
            "postman_configured": bool(Config.POSTMAN_API_KEY),
            "reports_directory": Config.REPORT_OUTPUT_DIR
        }
    }
    
    if missing_vars:
        health_status["warnings"] = {
            "missing_environment_variables": missing_vars
        }
    
    logger.info("health_check_performed", status=health_status["status"])
    
    return health_status


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions with structured logging"""
    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": structlog.contextvars.get_contextvars().get("request_id")
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Validate configuration before starting
    missing_vars = Config.validate()
    if missing_vars:
        logger.warning(
            "starting_with_missing_config",
            missing=missing_vars
        )
    
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level=Config.LOG_LEVEL.lower()
    )
