"""
Pydantic Models for Adaptive Research Agent API

This module defines all request/response models for the FastAPI endpoints.

Requirements: 1.4, 12.1
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ResearchRequest(BaseModel):
    """
    API request for research query.
    
    Requirements: 12.1 - POST /api/research/query request model
    """
    query: str = Field(..., min_length=10, max_length=500, description="Natural language research query")
    session_id: Optional[str] = Field(None, description="Optional session ID for multi-turn conversations")
    max_sources: int = Field(default=5, ge=1, le=10, description="Maximum number of API sources to use")
    include_report: bool = Field(default=True, description="Whether to generate a report")
    alert_enabled: bool = Field(default=True, description="Whether to enable alert evaluation")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class APISource(BaseModel):
    """
    API source information.
    
    Requirements: 1.4 - Include source citations
    """
    api_id: str = Field(..., description="Unique API identifier")
    api_name: str = Field(..., description="Human-readable API name")
    endpoint: str = Field(..., description="API endpoint URL")
    method: str = Field(default="GET", description="HTTP method")
    verified: bool = Field(default=False, description="Whether API is verified by Postman")
    priority_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Priority score for this source")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")


class ResearchSynthesis(BaseModel):
    """
    Synthesized research results.
    
    Requirements: 1.3, 1.4 - Synthesized information with confidence scores
    """
    summary: str = Field(..., description="Executive summary of findings")
    detailed_analysis: str = Field(..., description="Detailed analysis combining all sources")
    findings: List[str] = Field(default_factory=list, description="List of key findings")
    sources: List[str] = Field(default_factory=list, description="List of source identifiers")
    source_details: List[APISource] = Field(default_factory=list, description="Detailed source information")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in results")
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict, description="Confidence by source")


class MemoryEntry(BaseModel):
    """
    Memory store entry from past interactions.
    
    Requirements: 2.1, 2.2 - Memory storage structure
    """
    memory_id: str = Field(..., description="Unique memory identifier")
    query: str = Field(..., description="Original query text")
    results: Dict[str, Any] = Field(default_factory=dict, description="Synthesized results")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="User feedback relevance score")
    api_sources: List[str] = Field(default_factory=list, description="API sources used")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity to current query")
    timestamp: float = Field(..., description="Unix timestamp when memory was created")
    session_id: Optional[str] = Field(None, description="Session identifier")


class ResearchResponse(BaseModel):
    """
    API response for research query.
    
    Requirements: 12.1 - POST /api/research/query response model
    """
    query_id: str = Field(..., description="Unique identifier for this query")
    session_id: str = Field(..., description="Session identifier")
    synthesized_answer: str = Field(..., description="Synthesized answer from multiple sources")
    detailed_analysis: str = Field(..., description="Detailed analysis")
    findings: List[str] = Field(default_factory=list, description="Key findings")
    sources: List[APISource] = Field(default_factory=list, description="API sources used with details")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    alert_triggered: bool = Field(default=False, description="Whether an alert was triggered")
    report_path: Optional[str] = Field(None, description="Path to generated report if requested")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    similar_past_queries: List[MemoryEntry] = Field(default_factory=list, description="Similar past queries from memory")
    memory_id: str = Field(..., description="ID of stored memory entry")
    refinement_applied: bool = Field(default=False, description="Whether query refinement was applied")
    refinements: List[str] = Field(default_factory=list, description="List of refinements applied")
    refinement_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in refinement quality")


class FeedbackRequest(BaseModel):
    """
    Feedback submission for learning.
    
    Requirements: 12.2 - POST /api/research/feedback request model
    """
    query_id: str = Field(..., description="Query identifier to provide feedback for")
    memory_id: str = Field(..., description="Memory entry identifier")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0 = not relevant, 1.0 = highly relevant)")
    feedback_notes: Optional[str] = Field(None, max_length=1000, description="Optional feedback notes")
    
    @field_validator('relevance_score')
    @classmethod
    def validate_relevance_score(cls, v: float) -> float:
        """Validate relevance score is in valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0")
        return v


class FeedbackResponse(BaseModel):
    """
    Response for feedback submission.
    
    Requirements: 12.2 - POST /api/research/feedback response model
    """
    success: bool = Field(..., description="Whether feedback was successfully recorded")
    message: str = Field(..., description="Status message")
    memory_id: str = Field(..., description="Updated memory entry ID")
    new_relevance_score: float = Field(..., description="New relevance score")


class HistoryEntry(BaseModel):
    """
    Single entry in query history.
    
    Requirements: 12.3 - GET /api/research/history response model
    """
    query_id: str = Field(..., description="Query identifier")
    query: str = Field(..., description="Original query text")
    timestamp: float = Field(..., description="Unix timestamp")
    relevance_score: float = Field(..., description="Relevance score")
    confidence_score: float = Field(..., description="Confidence score")
    sources_count: int = Field(..., description="Number of sources used")
    session_id: Optional[str] = Field(None, description="Session identifier")


class HistoryResponse(BaseModel):
    """
    Response for query history.
    
    Requirements: 12.3 - GET /api/research/history response model
    """
    total: int = Field(..., description="Total number of queries")
    limit: int = Field(..., description="Limit per page")
    offset: int = Field(..., description="Current offset")
    queries: List[HistoryEntry] = Field(default_factory=list, description="List of past queries")


class SourceMetrics(BaseModel):
    """
    Metrics for a specific API source.
    
    Requirements: 7.2, 7.5 - Source performance metrics
    """
    api_id: str = Field(..., description="API identifier")
    api_name: str = Field(..., description="API name")
    total_uses: int = Field(..., description="Total times this source was used")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    avg_relevance: float = Field(..., ge=0.0, le=1.0, description="Average relevance score")
    avg_response_time_ms: float = Field(..., description="Average response time")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Current priority score")


class MetricsResponse(BaseModel):
    """
    Self-improvement metrics response.
    
    Requirements: 12.4, 7.1, 7.2, 7.3, 7.4, 7.5 - GET /api/metrics response model
    """
    total_queries: int = Field(..., description="Total queries processed")
    avg_relevance_score: float = Field(..., ge=0.0, le=1.0, description="Average relevance score")
    avg_confidence_score: float = Field(..., ge=0.0, le=1.0, description="Average confidence score")
    improvement_trend: float = Field(..., description="Improvement trend (positive = improving)")
    top_sources: List[SourceMetrics] = Field(default_factory=list, description="Top performing API sources")
    confidence_threshold: float = Field(..., ge=0.0, le=1.0, description="Current confidence threshold")
    memory_stats: Dict[str, Any] = Field(default_factory=dict, description="Memory store statistics")
    queries_last_hour: int = Field(default=0, description="Queries in last hour")
    queries_last_day: int = Field(default=0, description="Queries in last day")


class ReportMetadata(BaseModel):
    """
    Metadata for a generated report.
    
    Requirements: 12.5 - GET /api/reports response model
    """
    report_id: str = Field(..., description="Unique report identifier")
    filename: str = Field(..., description="Report filename")
    query: str = Field(..., description="Original query")
    timestamp: str = Field(..., description="Generation timestamp")
    file_size_bytes: int = Field(..., description="File size in bytes")
    confidence_score: float = Field(..., description="Confidence score")


class ReportsListResponse(BaseModel):
    """
    Response for listing generated reports.
    
    Requirements: 12.5 - GET /api/reports response model
    """
    total: int = Field(..., description="Total number of reports")
    reports: List[ReportMetadata] = Field(default_factory=list, description="List of reports")


class ReportContent(BaseModel):
    """
    Full report content.
    
    Requirements: 12.5 - GET /api/reports/{report_id} response model
    """
    report_id: str = Field(..., description="Report identifier")
    filename: str = Field(..., description="Report filename")
    content: str = Field(..., description="Full markdown content")
    metadata: ReportMetadata = Field(..., description="Report metadata")


class ScheduleRequest(BaseModel):
    """
    Request to create a scheduled query.
    
    Requirements: 13.1 - POST /api/schedule request model
    """
    query: str = Field(..., min_length=10, max_length=500, description="Query to schedule")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")
    alert_on_change: bool = Field(default=True, description="Alert when results change significantly")
    max_sources: int = Field(default=5, ge=1, le=10, description="Maximum API sources")


class ScheduleResponse(BaseModel):
    """
    Response for schedule creation.
    
    Requirements: 13.1 - POST /api/schedule response model
    """
    schedule_id: str = Field(..., description="Unique schedule identifier")
    query: str = Field(..., description="Scheduled query")
    cron_expression: str = Field(..., description="Cron expression")
    next_run: str = Field(..., description="Next scheduled run time")
    enabled: bool = Field(..., description="Whether schedule is enabled")


class HealthResponse(BaseModel):
    """
    Health check response.
    
    Requirements: 12.6 - GET /health response model
    """
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    configuration: Dict[str, bool] = Field(default_factory=dict, description="Configuration status")
    warnings: Optional[Dict[str, List[str]]] = Field(None, description="Configuration warnings")


class ErrorResponse(BaseModel):
    """
    Standard error response.
    
    Requirements: 12.7 - Error handling with appropriate status codes
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
