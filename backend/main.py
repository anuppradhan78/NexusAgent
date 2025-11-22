"""
Adaptive Research Agent - Main FastAPI Application
"""
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from dotenv import load_dotenv

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


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
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
    
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


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
