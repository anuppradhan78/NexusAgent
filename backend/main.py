"""
Adaptive Research Agent - Main FastAPI Application
"""
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path
from datetime import datetime

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
    ErrorResponse,
    ScheduleRequest,
    ScheduleResponse
)
from agent_orchestrator import AgentOrchestrator, AgentOrchestratorError
from mcp_client import MCPClient, MCPConnectionError
from memory_store import MemoryStore, MemoryStoreError
from alert_engine import AlertEngine
from report_generator import ReportGenerator
from scheduler import QueryScheduler, SchedulerError
from session_manager import SessionManager, SessionManagerError
from log_manager import LogManager, LogQuery, initialize_log_manager, get_log_manager

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
alert_engine: Optional[AlertEngine] = None
report_generator: Optional[ReportGenerator] = None
agent_orchestrator: Optional[AgentOrchestrator] = None
query_scheduler: Optional[QueryScheduler] = None
session_manager: Optional[SessionManager] = None
log_manager: Optional[LogManager] = None


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    global mcp_client, memory_store, alert_engine, report_generator, agent_orchestrator, query_scheduler, session_manager, log_manager
    
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
        # Initialize log manager first
        # Requirements: 14.1, 14.2 - Comprehensive logging with request ID tracing
        logger.info("initializing_log_manager")
        log_manager = initialize_log_manager(
            redis_url=Config.REDIS_URL,
            redis_password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
            log_retention_days=7
        )
        logger.info("log_manager_initialized")
        
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
        
        # Initialize alert engine
        logger.info("initializing_alert_engine")
        alert_engine = AlertEngine(mcp_client=mcp_client)
        logger.info("alert_engine_initialized")
        
        # Initialize report generator
        logger.info("initializing_report_generator")
        report_generator = ReportGenerator(output_dir=Config.REPORT_OUTPUT_DIR)
        logger.info("report_generator_initialized")
        
        # Initialize session manager (before agent orchestrator)
        logger.info("initializing_session_manager")
        session_manager = SessionManager(
            redis_url=Config.REDIS_URL,
            redis_password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None
        )
        logger.info("session_manager_initialized")
        
        # Initialize agent orchestrator
        logger.info("initializing_agent_orchestrator")
        agent_orchestrator = AgentOrchestrator(
            mcp_client=mcp_client,
            memory_store=memory_store,
            alert_engine=alert_engine,
            report_generator=report_generator,
            session_manager=session_manager
        )
        logger.info("agent_orchestrator_initialized")
        
        # Initialize query scheduler
        logger.info("initializing_query_scheduler")
        query_scheduler = QueryScheduler(
            agent_orchestrator=agent_orchestrator,
            memory_store=memory_store
        )
        await query_scheduler.start()
        logger.info("query_scheduler_initialized")
        
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
    if query_scheduler:
        try:
            await query_scheduler.stop()
        except Exception as e:
            logger.warning("query_scheduler_stop_error", error=str(e))
    
    if session_manager:
        try:
            session_manager.close()
        except Exception as e:
            logger.warning("session_manager_close_error", error=str(e))
    
    if log_manager:
        try:
            log_manager.close()
        except Exception as e:
            logger.warning("log_manager_close_error", error=str(e))
    
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
    - 15.1: Maintain conversation context across multiple queries
    - 15.5: Support session management with unique session IDs
    
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
    
    # Handle session management
    # Requirements: 15.1, 15.5 - Maintain conversation context with session IDs
    session_id = request.session_id
    if session_id and session_manager:
        # Verify session exists, create if not
        session_context = session_manager.get_session(session_id)
        if not session_context:
            logger.info("session_not_found_creating_new", session_id=session_id)
            session_id = session_manager.create_session()
    elif not session_id and session_manager:
        # Create new session if none provided
        session_id = session_manager.create_session()
        logger.info("new_session_created", session_id=session_id)
    
    logger.info(
        "research_query_received",
        query=request.query[:100],
        session_id=session_id,
        max_sources=request.max_sources
    )
    
    try:
        # Process query through agent orchestrator
        # Requirements: 5.1, 6.1, 12.1, 15.1 - Include alerts, reports, and session context
        result = await agent_orchestrator.process_query(
            query=request.query,
            session_id=session_id,
            max_sources=request.max_sources,
            timeout=30,
            include_report=request.include_report,
            alert_enabled=request.alert_enabled
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
        
        # Add query to session history
        # Requirements: 15.1, 15.4 - Store conversation history
        if session_id and session_manager:
            try:
                session_manager.add_query_to_session(
                    session_id=session_id,
                    query_id=result.query_id,
                    query=request.query,
                    synthesized_answer=result.synthesis.summary,
                    sources=[s.api_id for s in api_sources],
                    confidence_score=result.synthesis.confidence_score,
                    memory_id=result.memory_id
                )
                logger.info(
                    "query_added_to_session",
                    session_id=session_id,
                    query_id=result.query_id
                )
            except SessionManagerError as e:
                # Log but don't fail the request
                logger.warning(
                    "failed_to_add_query_to_session",
                    session_id=session_id,
                    error=str(e)
                )
        
        # Build response
        # Requirements: 12.1, 15.5 - Include alert status, report path, and session ID
        response = ResearchResponse(
            query_id=result.query_id,
            session_id=session_id or result.query_id,
            synthesized_answer=result.synthesis.summary,
            detailed_analysis=result.synthesis.detailed_analysis,
            findings=result.synthesis.findings,
            sources=api_sources,
            confidence_score=result.synthesis.confidence_score,
            alert_triggered=result.alert is not None,
            report_path=result.report_path.full_path if result.report_path else None,
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
            session_id=session_id,
            processing_time_ms=result.processing_time_ms,
            confidence_score=result.synthesis.confidence_score,
            sources_count=len(api_sources),
            alert_triggered=result.alert is not None,
            report_generated=result.report_path is not None
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


# Metrics Endpoint
@app.get("/api/metrics", response_model=models.MetricsResponse)
async def get_metrics():
    """
    Get self-improvement metrics.
    
    Requirements:
    - 12.4: GET endpoint returning self-improvement metrics
    - 7.1: Track Self_Improvement_Metric values
    - 7.2: Compute metrics over rolling windows
    - 7.3: Detect improvement trends
    - 7.4: Log metric snapshots
    - 7.5: Expose metrics via /metrics endpoint
    
    Returns:
        MetricsResponse: Self-improvement metrics including:
        - Total queries processed
        - Average relevance and confidence scores
        - Improvement trend (positive = improving)
        - Top performing API sources
        - Current confidence threshold
        - Memory statistics
        - Recent query counts
        
    Raises:
        HTTPException: If metrics calculation fails
    """
    # Check if components are initialized
    if not memory_store:
        logger.error("memory_store_not_initialized_for_metrics")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Memory store not initialized."
        )
    
    logger.info("metrics_requested")
    
    try:
        import time
        current_time = time.time()
        
        # Get all recent memories for analysis
        # Requirement 7.2: Compute metrics over rolling windows
        all_memories = await memory_store.get_recent(limit=1000, min_relevance=0.0)
        
        if not all_memories:
            # No data yet, return default metrics
            logger.info("no_memories_for_metrics", returning_defaults=True)
            return models.MetricsResponse(
                total_queries=0,
                avg_relevance_score=0.0,
                avg_confidence_score=0.0,
                improvement_trend=0.0,
                top_sources=[],
                confidence_threshold=agent_orchestrator.learning_engine.get_confidence_threshold() if agent_orchestrator and agent_orchestrator.learning_engine else 0.5,
                memory_stats={
                    "total_memories": 0,
                    "avg_relevance": 0.0,
                    "high_quality_memories": 0,
                    "memory_size_bytes": 0
                },
                queries_last_hour=0,
                queries_last_day=0
            )
        
        # Requirement 7.1: Calculate total queries, average relevance, average confidence
        total_queries = len(all_memories)
        
        # Calculate average relevance score
        relevance_scores = [m.relevance_score for m in all_memories]
        avg_relevance_score = float(sum(relevance_scores) / len(relevance_scores))
        
        # Calculate average confidence score (using relevance as proxy for confidence)
        # In a full implementation, we'd store actual confidence scores
        avg_confidence_score = avg_relevance_score
        
        # Requirement 7.3: Detect improvement trends
        # Compare recent queries (last 10) vs older queries (10-20)
        improvement_trend = 0.0
        if len(all_memories) >= 20:
            recent_10 = all_memories[:10]
            older_10 = all_memories[10:20]
            
            recent_avg = sum(m.relevance_score for m in recent_10) / len(recent_10)
            older_avg = sum(m.relevance_score for m in older_10) / len(older_10)
            
            # Positive trend = improving
            improvement_trend = float(recent_avg - older_avg)
        elif len(all_memories) >= 10:
            # Not enough data for comparison, but check if recent is above threshold
            recent_avg = sum(m.relevance_score for m in all_memories[:10]) / 10
            improvement_trend = float(recent_avg - 0.5)  # Compare to baseline
        
        # Requirement 7.2: Get top performing API sources
        top_sources = []
        if agent_orchestrator and agent_orchestrator.learning_engine:
            try:
                source_metrics = await agent_orchestrator.learning_engine.analyze_source_performance(
                    lookback_queries=min(100, total_queries)
                )
                
                # Sort by priority score and take top 5
                sorted_sources = sorted(
                    source_metrics.values(),
                    key=lambda m: m.priority_score,
                    reverse=True
                )[:5]
                
                # Convert to response model
                for source in sorted_sources:
                    top_sources.append(models.SourceMetrics(
                        api_id=source.api_id,
                        api_name=source.api_name,
                        total_uses=source.total_uses,
                        success_rate=source.success_rate,
                        avg_relevance=source.avg_relevance,
                        avg_response_time_ms=0.0,  # Not tracked yet
                        priority_score=source.priority_score
                    ))
            except Exception as e:
                logger.warning("source_metrics_calculation_error", error=str(e))
        
        # Get current confidence threshold
        confidence_threshold = 0.5
        if agent_orchestrator and agent_orchestrator.learning_engine:
            confidence_threshold = agent_orchestrator.learning_engine.get_confidence_threshold()
        
        # Get memory statistics
        memory_metrics = await memory_store.get_metrics()
        memory_stats = {
            "total_memories": memory_metrics.total_memories,
            "avg_relevance": memory_metrics.avg_relevance,
            "high_quality_memories": memory_metrics.high_quality_memories,
            "memory_size_bytes": memory_metrics.memory_size_bytes
        }
        
        # Calculate queries in last hour and last day
        one_hour_ago = current_time - 3600
        one_day_ago = current_time - 86400
        
        queries_last_hour = sum(1 for m in all_memories if m.timestamp >= one_hour_ago)
        queries_last_day = sum(1 for m in all_memories if m.timestamp >= one_day_ago)
        
        # Build response
        response = models.MetricsResponse(
            total_queries=total_queries,
            avg_relevance_score=avg_relevance_score,
            avg_confidence_score=avg_confidence_score,
            improvement_trend=improvement_trend,
            top_sources=top_sources,
            confidence_threshold=confidence_threshold,
            memory_stats=memory_stats,
            queries_last_hour=queries_last_hour,
            queries_last_day=queries_last_day
        )
        
        # Requirement 7.4: Log metric snapshots
        logger.info(
            "metrics_calculated",
            total_queries=total_queries,
            avg_relevance_score=avg_relevance_score,
            improvement_trend=improvement_trend,
            confidence_threshold=confidence_threshold,
            queries_last_hour=queries_last_hour,
            queries_last_day=queries_last_day
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(
            "metrics_calculation_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while calculating metrics."
        )


# History Endpoint
@app.get("/api/research/history", response_model=models.HistoryResponse)
async def get_history(
    limit: int = 50,
    offset: int = 0,
    min_relevance: float = 0.0
):
    """
    Get past queries with pagination.
    
    Requirements:
    - 12.3: GET endpoint returning past queries with pagination
    
    Args:
        limit: Maximum number of queries to return (default: 50)
        offset: Number of queries to skip (default: 0)
        min_relevance: Minimum relevance score filter (default: 0.0)
        
    Returns:
        HistoryResponse: List of past queries with pagination info
        
    Raises:
        HTTPException: If history retrieval fails
    """
    # Check if memory store is initialized
    if not memory_store:
        logger.error("memory_store_not_initialized_for_history")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Memory store not initialized."
        )
    
    logger.info(
        "history_requested",
        limit=limit,
        offset=offset,
        min_relevance=min_relevance
    )
    
    try:
        # Get all recent memories (we'll handle pagination manually)
        # Get more than needed to account for offset
        fetch_limit = limit + offset + 100
        all_memories = await memory_store.get_recent(
            limit=fetch_limit,
            min_relevance=min_relevance
        )
        
        # Get total count
        total = len(all_memories)
        
        # Apply pagination
        paginated_memories = all_memories[offset:offset + limit]
        
        # Convert to HistoryEntry models
        history_entries = []
        for mem in paginated_memories:
            # Extract confidence score from results if available
            confidence_score = mem.relevance_score  # Use relevance as proxy
            if isinstance(mem.results, dict):
                confidence_score = mem.results.get("confidence_score", mem.relevance_score)
            
            history_entries.append(models.HistoryEntry(
                query_id=mem.memory_id,
                query=mem.query,
                timestamp=mem.timestamp,
                relevance_score=mem.relevance_score,
                confidence_score=confidence_score,
                sources_count=len(mem.api_sources),
                session_id=mem.session_id
            ))
        
        # Build response
        response = models.HistoryResponse(
            total=total,
            limit=limit,
            offset=offset,
            queries=history_entries
        )
        
        logger.info(
            "history_retrieved",
            total=total,
            returned=len(history_entries),
            limit=limit,
            offset=offset
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(
            "history_retrieval_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving history."
        )


# Reports List Endpoint
@app.get("/api/reports", response_model=models.ReportsListResponse)
async def list_reports(limit: int = 20):
    """
    List generated reports.
    
    Requirements:
    - 12.5: GET endpoint to list generated reports
    
    Args:
        limit: Maximum number of reports to return (default: 20)
        
    Returns:
        ReportsListResponse: List of report metadata
        
    Raises:
        HTTPException: If report listing fails
    """
    logger.info("reports_list_requested", limit=limit)
    
    try:
        # Get reports directory
        reports_dir = Path(Config.REPORT_OUTPUT_DIR)
        
        if not reports_dir.exists():
            logger.warning("reports_directory_not_found", path=str(reports_dir))
            return models.ReportsListResponse(
                total=0,
                reports=[]
            )
        
        # Get all markdown files in reports directory
        all_report_files = list(reports_dir.glob("research_report_*.md"))
        
        # Sort by filename (which contains timestamp) - newest first
        all_report_files = sorted(
            all_report_files,
            key=lambda p: p.name,
            reverse=True
        )
        
        # Limit results
        report_files = all_report_files[:limit]
        
        # Build report metadata list
        reports_metadata = []
        for report_file in report_files:
            try:
                # Extract timestamp from filename
                # Format: research_report_2025-11-22_11-26-48.md
                filename = report_file.name
                timestamp_str = filename.replace("research_report_", "").replace(".md", "")
                
                # Read first few lines to extract query and confidence
                content = report_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Extract query from title (first line)
                query = "Unknown Query"
                if lines and lines[0].startswith("# Research Report:"):
                    query = lines[0].replace("# Research Report:", "").strip()
                
                # Extract confidence score
                confidence_score = 0.5
                for line in lines[:10]:  # Check first 10 lines
                    if "**Confidence Score:**" in line:
                        try:
                            confidence_str = line.split("**Confidence Score:**")[1].strip()
                            confidence_score = float(confidence_str)
                        except (IndexError, ValueError):
                            pass
                        break
                
                # Generate report ID
                report_id = f"report_{timestamp_str}"
                
                # Get file size
                file_size = report_file.stat().st_size
                
                reports_metadata.append(models.ReportMetadata(
                    report_id=report_id,
                    filename=filename,
                    query=query,
                    timestamp=timestamp_str,
                    file_size_bytes=file_size,
                    confidence_score=confidence_score
                ))
                
            except Exception as e:
                logger.warning(
                    "report_metadata_extraction_error",
                    filename=report_file.name,
                    error=str(e)
                )
                continue
        
        # Build response (total is all files, not just returned)
        response = models.ReportsListResponse(
            total=len(all_report_files),
            reports=reports_metadata
        )
        
        logger.info(
            "reports_listed",
            total=len(reports_metadata),
            limit=limit
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "reports_list_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while listing reports."
        )


# Get Specific Report Endpoint
@app.get("/api/reports/{report_id}", response_model=models.ReportContent)
async def get_report(report_id: str):
    """
    Get specific report content.
    
    Requirements:
    - 12.5: GET endpoint to retrieve specific report
    
    Args:
        report_id: Report identifier (format: report_YYYY-MM-DD_HH-MM-SS)
        
    Returns:
        ReportContent: Full report content with metadata
        
    Raises:
        HTTPException: If report not found or retrieval fails
    """
    logger.info("report_requested", report_id=report_id)
    
    try:
        # Extract timestamp from report_id
        # Format: report_2025-11-22_11-26-48
        if not report_id.startswith("report_"):
            raise HTTPException(
                status_code=400,
                detail="Invalid report ID format. Expected: report_YYYY-MM-DD_HH-MM-SS"
            )
        
        timestamp_str = report_id.replace("report_", "")
        filename = f"research_report_{timestamp_str}.md"
        
        # Get reports directory
        reports_dir = Path(Config.REPORT_OUTPUT_DIR)
        report_path = reports_dir / filename
        
        # Check if report exists
        if not report_path.exists():
            logger.warning("report_not_found", report_id=report_id, path=str(report_path))
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {report_id}"
            )
        
        # Read report content
        content = report_path.read_text(encoding='utf-8')
        
        # Extract metadata from content
        lines = content.split('\n')
        
        # Extract query from title
        query = "Unknown Query"
        if lines and lines[0].startswith("# Research Report:"):
            query = lines[0].replace("# Research Report:", "").strip()
        
        # Extract confidence score
        confidence_score = 0.5
        for line in lines[:10]:
            if "**Confidence Score:**" in line:
                try:
                    confidence_str = line.split("**Confidence Score:**")[1].strip()
                    confidence_score = float(confidence_str)
                except (IndexError, ValueError):
                    pass
                break
        
        # Get file size
        file_size = report_path.stat().st_size
        
        # Build metadata
        metadata = models.ReportMetadata(
            report_id=report_id,
            filename=filename,
            query=query,
            timestamp=timestamp_str,
            file_size_bytes=file_size,
            confidence_score=confidence_score
        )
        
        # Build response
        response = models.ReportContent(
            report_id=report_id,
            filename=filename,
            content=content,
            metadata=metadata
        )
        
        logger.info(
            "report_retrieved",
            report_id=report_id,
            size_bytes=file_size
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(
            "report_retrieval_error",
            report_id=report_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving the report."
        )


# Schedule Endpoints
@app.post("/api/schedule", response_model=ScheduleResponse)
async def create_schedule(request: ScheduleRequest):
    """
    Create a scheduled recurring query.
    
    Requirements:
    - 13.1: Accept scheduled queries with cron-like expressions
    - 13.6: Allow users to enable/disable/modify scheduled queries
    
    Args:
        request: ScheduleRequest with query and cron expression
        
    Returns:
        ScheduleResponse: Created schedule information
        
    Raises:
        HTTPException: If schedule creation fails
    """
    # Check if query scheduler is initialized
    if not query_scheduler:
        logger.error("query_scheduler_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Query scheduler not initialized."
        )
    
    logger.info(
        "schedule_creation_requested",
        query=request.query[:100],
        cron_expression=request.cron_expression,
        enabled=request.enabled
    )
    
    try:
        # Create schedule
        schedule = await query_scheduler.create_schedule(
            query=request.query,
            cron_expression=request.cron_expression,
            enabled=request.enabled,
            alert_on_change=request.alert_on_change,
            max_sources=request.max_sources
        )
        
        # Get next run time
        next_run = query_scheduler.get_next_run_time(schedule.schedule_id)
        next_run_str = next_run.isoformat() if next_run else "Not scheduled"
        
        # Build response
        response = ScheduleResponse(
            schedule_id=schedule.schedule_id,
            query=schedule.query,
            cron_expression=schedule.cron_expression,
            next_run=next_run_str,
            enabled=schedule.enabled
        )
        
        logger.info(
            "schedule_created",
            schedule_id=schedule.schedule_id,
            next_run=next_run_str
        )
        
        return response
        
    except SchedulerError as e:
        logger.error(
            "schedule_creation_failed",
            error=str(e),
            query=request.query[:100]
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(
            "schedule_creation_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating schedule."
        )


@app.get("/api/schedule", response_model=models.ScheduleListResponse)
async def list_schedules():
    """
    List all scheduled queries.
    
    Requirements: 13.6 - Allow users to view scheduled queries
    
    Returns:
        ScheduleListResponse: List of all schedules
        
    Raises:
        HTTPException: If listing fails
    """
    # Check if query scheduler is initialized
    if not query_scheduler:
        logger.error("query_scheduler_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Query scheduler not initialized."
        )
    
    logger.info("schedules_list_requested")
    
    try:
        schedules = await query_scheduler.list_schedules()
        
        # Convert to response models
        schedule_items = []
        for schedule in schedules:
            next_run = query_scheduler.get_next_run_time(schedule.schedule_id)
            next_run_str = next_run.isoformat() if next_run else "Not scheduled"
            
            schedule_items.append(models.ScheduleItem(
                schedule_id=schedule.schedule_id,
                query=schedule.query,
                cron_expression=schedule.cron_expression,
                enabled=schedule.enabled,
                alert_on_change=schedule.alert_on_change,
                max_sources=schedule.max_sources,
                created_at=schedule.created_at,
                last_run=schedule.last_run,
                execution_count=schedule.execution_count,
                next_run=next_run_str
            ))
        
        response = models.ScheduleListResponse(
            total=len(schedule_items),
            schedules=schedule_items
        )
        
        logger.info("schedules_listed", count=len(schedule_items))
        
        return response
        
    except Exception as e:
        logger.error(
            "schedules_list_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while listing schedules."
        )


@app.get("/api/schedule/{schedule_id}", response_model=models.ScheduleItem)
async def get_schedule(schedule_id: str):
    """
    Get a specific scheduled query.
    
    Requirements: 13.6 - Allow users to view scheduled queries
    
    Args:
        schedule_id: Schedule identifier
        
    Returns:
        ScheduleItem: Schedule details
        
    Raises:
        HTTPException: If schedule not found
    """
    # Check if query scheduler is initialized
    if not query_scheduler:
        logger.error("query_scheduler_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Query scheduler not initialized."
        )
    
    logger.info("schedule_get_requested", schedule_id=schedule_id)
    
    try:
        schedule = await query_scheduler.get_schedule(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found: {schedule_id}"
            )
        
        next_run = query_scheduler.get_next_run_time(schedule.schedule_id)
        next_run_str = next_run.isoformat() if next_run else "Not scheduled"
        
        response = models.ScheduleItem(
            schedule_id=schedule.schedule_id,
            query=schedule.query,
            cron_expression=schedule.cron_expression,
            enabled=schedule.enabled,
            alert_on_change=schedule.alert_on_change,
            max_sources=schedule.max_sources,
            created_at=schedule.created_at,
            last_run=schedule.last_run,
            execution_count=schedule.execution_count,
            next_run=next_run_str
        )
        
        logger.info("schedule_retrieved", schedule_id=schedule_id)
        
        return response
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(
            "schedule_get_error",
            schedule_id=schedule_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving schedule."
        )


@app.put("/api/schedule/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: str, request: models.ScheduleUpdateRequest):
    """
    Update a scheduled query.
    
    Requirements: 13.6 - Allow users to enable/disable/modify scheduled queries
    
    Args:
        schedule_id: Schedule identifier
        request: ScheduleUpdateRequest with fields to update
        
    Returns:
        ScheduleResponse: Updated schedule information
        
    Raises:
        HTTPException: If update fails
    """
    # Check if query scheduler is initialized
    if not query_scheduler:
        logger.error("query_scheduler_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Query scheduler not initialized."
        )
    
    logger.info("schedule_update_requested", schedule_id=schedule_id)
    
    try:
        # Update schedule
        schedule = await query_scheduler.update_schedule(
            schedule_id=schedule_id,
            enabled=request.enabled,
            cron_expression=request.cron_expression,
            alert_on_change=request.alert_on_change,
            max_sources=request.max_sources
        )
        
        # Get next run time
        next_run = query_scheduler.get_next_run_time(schedule.schedule_id)
        next_run_str = next_run.isoformat() if next_run else "Not scheduled"
        
        # Build response
        response = ScheduleResponse(
            schedule_id=schedule.schedule_id,
            query=schedule.query,
            cron_expression=schedule.cron_expression,
            next_run=next_run_str,
            enabled=schedule.enabled
        )
        
        logger.info(
            "schedule_updated",
            schedule_id=schedule_id,
            enabled=schedule.enabled
        )
        
        return response
        
    except SchedulerError as e:
        logger.error(
            "schedule_update_failed",
            schedule_id=schedule_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=400 if "not found" in str(e).lower() else 400,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(
            "schedule_update_error",
            schedule_id=schedule_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while updating schedule."
        )


@app.delete("/api/schedule/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """
    Delete a scheduled query.
    
    Requirements: 13.6 - Allow users to enable/disable/modify scheduled queries
    
    Args:
        schedule_id: Schedule identifier
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If deletion fails
    """
    # Check if query scheduler is initialized
    if not query_scheduler:
        logger.error("query_scheduler_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Query scheduler not initialized."
        )
    
    logger.info("schedule_deletion_requested", schedule_id=schedule_id)
    
    try:
        success = await query_scheduler.delete_schedule(schedule_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found: {schedule_id}"
            )
        
        logger.info("schedule_deleted", schedule_id=schedule_id)
        
        return {"success": True, "message": "Schedule deleted successfully"}
        
    except HTTPException:
        raise
    
    except SchedulerError as e:
        logger.error(
            "schedule_deletion_failed",
            schedule_id=schedule_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(
            "schedule_deletion_error",
            schedule_id=schedule_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while deleting schedule."
        )


# Session Management Endpoints
@app.post("/api/session")
async def create_session():
    """
    Create a new conversation session.
    
    Requirements: 15.5 - Support session management with unique session IDs
    
    Returns:
        Session information with session_id
        
    Raises:
        HTTPException: If session creation fails
    """
    # Check if session manager is initialized
    if not session_manager:
        logger.error("session_manager_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Session manager not initialized."
        )
    
    logger.info("session_creation_requested")
    
    try:
        session_id = session_manager.create_session()
        
        logger.info("session_created_via_endpoint", session_id=session_id)
        
        return {
            "session_id": session_id,
            "created_at": time.time(),
            "expiration_seconds": session_manager.session_expiration_seconds
        }
        
    except SessionManagerError as e:
        logger.error("session_creation_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@app.get("/api/session/{session_id}/history")
async def get_session_history(session_id: str):
    """
    Get query history for a session.
    
    Requirements:
    - 15.2: Use previous query results as context for follow-up questions
    - 15.3: Allow users to reference previous results
    
    Args:
        session_id: Session identifier
        
    Returns:
        Query history for the session
        
    Raises:
        HTTPException: If session not found or retrieval fails
    """
    # Check if session manager is initialized
    if not session_manager:
        logger.error("session_manager_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Session manager not initialized."
        )
    
    logger.info("session_history_requested", session_id=session_id)
    
    try:
        history = session_manager.get_session_history(session_id)
        
        if history is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        # Convert to dict for JSON response
        history_dicts = [
            {
                "query_id": item.query_id,
                "query": item.query,
                "synthesized_answer": item.synthesized_answer,
                "sources": item.sources,
                "confidence_score": item.confidence_score,
                "timestamp": item.timestamp,
                "memory_id": item.memory_id
            }
            for item in history
        ]
        
        logger.info(
            "session_history_retrieved",
            session_id=session_id,
            query_count=len(history_dicts)
        )
        
        return {
            "session_id": session_id,
            "query_count": len(history_dicts),
            "history": history_dicts
        }
        
    except HTTPException:
        raise
    
    except SessionManagerError as e:
        logger.error("session_history_retrieval_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session history: {str(e)}"
        )


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a conversation session.
    
    Requirements: 15.6 - Session management
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If deletion fails
    """
    # Check if session manager is initialized
    if not session_manager:
        logger.error("session_manager_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Session manager not initialized."
        )
    
    logger.info("session_deletion_requested", session_id=session_id)
    
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        logger.info("session_deleted_via_endpoint", session_id=session_id)
        
        return {"success": True, "message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    
    except SessionManagerError as e:
        logger.error("session_deletion_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


# Logs Endpoint
@app.get("/api/logs")
async def get_logs(
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    level: Optional[str] = None,
    request_id: Optional[str] = None,
    event: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get application logs with filtering.
    
    Requirements:
    - 14.5: Expose logs via /api/logs endpoint with filtering capabilities
    - 14.2: Structured JSON logging with request IDs
    
    Args:
        start_time: Start of time range (Unix timestamp)
        end_time: End of time range (Unix timestamp)
        level: Filter by log level (debug, info, warning, error, critical)
        request_id: Filter by request ID
        event: Filter by event name
        limit: Maximum number of logs to return (default: 100)
        offset: Number of logs to skip (default: 0)
        
    Returns:
        Filtered log entries with pagination info
        
    Raises:
        HTTPException: If log retrieval fails
    """
    # Check if log manager is initialized
    if not log_manager:
        logger.error("log_manager_not_initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Log manager not initialized."
        )
    
    logger.info(
        "logs_requested",
        start_time=start_time,
        end_time=end_time,
        level=level,
        request_id=request_id,
        event=event,
        limit=limit,
        offset=offset
    )
    
    try:
        # Create query
        query = LogQuery(
            start_time=start_time,
            end_time=end_time,
            level=level,
            request_id=request_id,
            event=event,
            limit=limit,
            offset=offset
        )
        
        # Query logs
        logs = log_manager.query_logs(query)
        
        # Convert to dict for JSON response
        log_dicts = []
        for log in logs:
            log_dict = {
                "timestamp": log.timestamp,
                "datetime": datetime.fromtimestamp(log.timestamp).isoformat(),
                "level": log.level,
                "message": log.message,
                "request_id": log.request_id,
                "event": log.event,
                "context": log.context
            }
            log_dicts.append(log_dict)
        
        # Get stats
        stats = log_manager.get_log_stats()
        
        logger.info(
            "logs_retrieved",
            count=len(log_dicts),
            limit=limit,
            offset=offset
        )
        
        return {
            "total": stats.get("memory_logs_count", 0),
            "returned": len(log_dicts),
            "limit": limit,
            "offset": offset,
            "filters": {
                "start_time": start_time,
                "end_time": end_time,
                "level": level,
                "request_id": request_id,
                "event": event
            },
            "logs": log_dicts,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(
            "logs_retrieval_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving logs."
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
