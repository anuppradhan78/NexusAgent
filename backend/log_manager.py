"""
Log Manager for Adaptive Research Agent

This module provides comprehensive logging capabilities including:
- Structured JSON logging with request ID tracing
- Log storage and retrieval
- Performance metrics logging
- Log filtering and querying

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6
"""
import os
import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import structlog

try:
    import redis
except ImportError:
    raise ImportError(
        "Redis package not found. Install with: pip install redis[hiredis]==5.0.1"
    )

logger = structlog.get_logger()


@dataclass
class LogEntry:
    """
    Represents a single log entry.
    
    Attributes:
        timestamp: Unix timestamp when log was created
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        request_id: Request ID for tracing
        event: Event name/type
        context: Additional context data
    """
    timestamp: float
    level: str
    message: str
    request_id: Optional[str]
    event: str
    context: Dict[str, Any]


@dataclass
class LogQuery:
    """
    Query parameters for log filtering.
    
    Attributes:
        start_time: Start of time range (Unix timestamp)
        end_time: End of time range (Unix timestamp)
        level: Filter by log level
        request_id: Filter by request ID
        event: Filter by event name
        limit: Maximum number of logs to return
        offset: Number of logs to skip
    """
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    level: Optional[str] = None
    request_id: Optional[str] = None
    event: Optional[str] = None
    limit: int = 100
    offset: int = 0


class LogManagerError(Exception):
    """Raised when log management operations fail"""
    pass


class LogManager:
    """
    Manages application logs with storage, retrieval, and filtering.
    
    Stores logs in Redis with automatic expiration and provides
    querying capabilities for observability.
    
    Requirements:
    - 14.1: Log all queries, API calls, memory operations, learning decisions
    - 14.2: Use structured JSON logging with request IDs
    - 14.3: Log performance metrics (latency, token usage, memory operations)
    - 14.4: Log learning loop decisions with reasoning
    - 14.5: Expose logs via /api/logs endpoint with filtering
    - 14.6: Integrate with standard logging frameworks
    """
    
    def __init__(
        self,
        redis_url: str = None,
        redis_password: str = None,
        log_retention_days: int = 7,
        max_memory_logs: int = 1000
    ):
        """
        Initialize log manager with Redis connection.
        
        Requirements: 14.2 - Structured JSON logging with request IDs
        
        Args:
            redis_url: Redis connection URL (default from REDIS_URL env var)
            redis_password: Redis password (default from REDIS_PASSWORD env var)
            log_retention_days: Number of days to retain logs (default 7)
            max_memory_logs: Maximum logs to keep in memory (default 1000)
        """
        # Get configuration from environment if not provided
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.log_retention_days = log_retention_days
        self.log_retention_seconds = log_retention_days * 24 * 60 * 60
        self.log_prefix = "log:"
        
        # In-memory log buffer for fast access
        self.memory_logs = deque(maxlen=max_memory_logs)
        
        # Initialize Redis client
        self.client = None
        self._connect()
        
        logger.info(
            "log_manager_initialized",
            redis_url=self.redis_url,
            retention_days=self.log_retention_days,
            max_memory_logs=max_memory_logs
        )
    
    def _connect(self) -> None:
        """
        Connect to Redis with error handling.
        """
        try:
            connection_params = {
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "retry_on_timeout": True
            }
            
            if self.redis_password:
                connection_params["password"] = self.redis_password
            
            self.client = redis.from_url(
                self.redis_url,
                **connection_params
            )
            
            # Test connection
            self.client.ping()
            
            logger.info("log_manager_redis_connected", url=self.redis_url)
            
        except redis.ConnectionError as e:
            logger.error("log_manager_redis_connection_failed", error=str(e), url=self.redis_url)
            # Continue without Redis - logs will only be in memory
            logger.warning("log_manager_operating_without_redis")
        except Exception as e:
            logger.error("log_manager_redis_connection_error", error=str(e))
            logger.warning("log_manager_operating_without_redis")
    
    def log(
        self,
        level: str,
        message: str,
        event: str,
        request_id: Optional[str] = None,
        **context
    ) -> None:
        """
        Log an event with structured data.
        
        Requirements:
        - 14.1: Log all operations
        - 14.2: Structured JSON logging with request IDs
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            event: Event name/type
            request_id: Optional request ID for tracing
            **context: Additional context data
        """
        try:
            timestamp = time.time()
            
            # Create log entry
            log_entry = LogEntry(
                timestamp=timestamp,
                level=level.lower(),
                message=message,
                request_id=request_id,
                event=event,
                context=context
            )
            
            # Add to memory buffer
            self.memory_logs.append(log_entry)
            
            # Store in Redis if available
            if self.client:
                try:
                    log_key = f"{self.log_prefix}{int(timestamp * 1000000)}"
                    log_data = json.dumps(asdict(log_entry))
                    
                    self.client.set(log_key, log_data)
                    self.client.expire(log_key, self.log_retention_seconds)
                except redis.RedisError as e:
                    # Log to structlog but don't fail
                    logger.warning("log_storage_failed", error=str(e))
            
        except Exception as e:
            # Never fail on logging
            logger.error("log_manager_error", error=str(e))
    
    def query_logs(self, query: LogQuery) -> List[LogEntry]:
        """
        Query logs with filtering.
        
        Requirements: 14.5 - Expose logs via endpoint with filtering
        
        Args:
            query: LogQuery with filter parameters
            
        Returns:
            List[LogEntry]: Filtered log entries
        """
        try:
            # Start with memory logs for fast access
            filtered_logs = list(self.memory_logs)
            
            # Try to get additional logs from Redis if available
            if self.client:
                try:
                    redis_logs = self._query_redis_logs(query)
                    # Merge with memory logs (deduplicate by timestamp)
                    existing_timestamps = {log.timestamp for log in filtered_logs}
                    for log in redis_logs:
                        if log.timestamp not in existing_timestamps:
                            filtered_logs.append(log)
                except redis.RedisError as e:
                    logger.warning("redis_log_query_failed", error=str(e))
            
            # Apply filters
            if query.start_time is not None:
                filtered_logs = [log for log in filtered_logs if log.timestamp >= query.start_time]
            
            if query.end_time is not None:
                filtered_logs = [log for log in filtered_logs if log.timestamp <= query.end_time]
            
            if query.level:
                filtered_logs = [log for log in filtered_logs if log.level == query.level.lower()]
            
            if query.request_id:
                filtered_logs = [log for log in filtered_logs if log.request_id == query.request_id]
            
            if query.event:
                filtered_logs = [log for log in filtered_logs if log.event == query.event]
            
            # Sort by timestamp (newest first)
            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            start_idx = query.offset
            end_idx = query.offset + query.limit
            paginated_logs = filtered_logs[start_idx:end_idx]
            
            logger.info(
                "logs_queried",
                total_found=len(filtered_logs),
                returned=len(paginated_logs),
                filters_applied={
                    "start_time": query.start_time,
                    "end_time": query.end_time,
                    "level": query.level,
                    "request_id": query.request_id,
                    "event": query.event
                }
            )
            
            return paginated_logs
            
        except Exception as e:
            logger.error("log_query_error", error=str(e))
            return []
    
    def _query_redis_logs(self, query: LogQuery) -> List[LogEntry]:
        """
        Query logs from Redis.
        
        Args:
            query: LogQuery with filter parameters
            
        Returns:
            List[LogEntry]: Logs from Redis
        """
        logs = []
        
        try:
            # Scan for log keys
            for key in self.client.scan_iter(f"{self.log_prefix}*"):
                try:
                    log_data = self.client.get(key)
                    if log_data:
                        log_dict = json.loads(log_data)
                        log_entry = LogEntry(**log_dict)
                        logs.append(log_entry)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning("invalid_log_entry", key=key, error=str(e))
                    continue
        except Exception as e:
            logger.error("redis_log_scan_error", error=str(e))
        
        return logs
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored logs.
        
        Requirements: 14.3 - Log performance metrics
        
        Returns:
            Dict with log statistics
        """
        try:
            stats = {
                "memory_logs_count": len(self.memory_logs),
                "redis_connected": self.client is not None,
                "retention_days": self.log_retention_days
            }
            
            # Count logs by level in memory
            level_counts = {}
            for log in self.memory_logs:
                level_counts[log.level] = level_counts.get(log.level, 0) + 1
            
            stats["level_counts"] = level_counts
            
            # Get time range
            if self.memory_logs:
                stats["oldest_log"] = min(log.timestamp for log in self.memory_logs)
                stats["newest_log"] = max(log.timestamp for log in self.memory_logs)
            
            # Try to get Redis stats
            if self.client:
                try:
                    redis_log_count = 0
                    for _ in self.client.scan_iter(f"{self.log_prefix}*"):
                        redis_log_count += 1
                    stats["redis_logs_count"] = redis_log_count
                except redis.RedisError as e:
                    logger.warning("redis_stats_failed", error=str(e))
            
            return stats
            
        except Exception as e:
            logger.error("log_stats_error", error=str(e))
            return {"error": str(e)}
    
    def cleanup_old_logs(self) -> int:
        """
        Manually cleanup old logs (Redis handles this automatically via TTL).
        
        Returns:
            int: Number of logs cleaned up
        """
        try:
            cleaned = 0
            current_time = time.time()
            expiration_threshold = current_time - self.log_retention_seconds
            
            if self.client:
                # Scan for old logs
                for key in self.client.scan_iter(f"{self.log_prefix}*"):
                    try:
                        log_data = self.client.get(key)
                        if log_data:
                            log_dict = json.loads(log_data)
                            if log_dict.get("timestamp", 0) < expiration_threshold:
                                self.client.delete(key)
                                cleaned += 1
                    except Exception as e:
                        logger.warning("log_cleanup_item_error", key=key, error=str(e))
                        continue
            
            if cleaned > 0:
                logger.info("old_logs_cleaned", count=cleaned)
            
            return cleaned
            
        except Exception as e:
            logger.error("log_cleanup_error", error=str(e))
            return 0
    
    def close(self) -> None:
        """
        Close Redis connection.
        """
        if self.client:
            try:
                self.client.close()
                logger.info("log_manager_closed")
            except Exception as e:
                logger.warning("log_manager_close_error", error=str(e))


# Global log manager instance
_log_manager: Optional[LogManager] = None


def get_log_manager() -> Optional[LogManager]:
    """Get the global log manager instance"""
    return _log_manager


def initialize_log_manager(
    redis_url: str = None,
    redis_password: str = None,
    log_retention_days: int = 7
) -> LogManager:
    """
    Initialize the global log manager.
    
    Args:
        redis_url: Redis connection URL
        redis_password: Redis password
        log_retention_days: Number of days to retain logs
        
    Returns:
        LogManager: Initialized log manager
    """
    global _log_manager
    _log_manager = LogManager(
        redis_url=redis_url,
        redis_password=redis_password,
        log_retention_days=log_retention_days
    )
    return _log_manager
