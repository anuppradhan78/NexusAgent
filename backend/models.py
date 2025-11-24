"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ResearchRequest(BaseModel):
    """API request for research query"""
    query: str = Field(..., min_length=10, max_length=500)
    max_sources: int = Field(default=5, ge=1, le=10)
    include_report: bool = True


class APISource(BaseModel):
    """API source information"""
    tool: str
    input: Dict[str, Any]


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
    results: Dict[str, Any]
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
    path: str
    size: int
    created: float


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
