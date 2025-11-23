"""
Session Manager for Multi-Turn Conversations

This module provides the SessionManager class that manages conversation sessions
for multi-turn interactions with the Adaptive Research Agent.

Features:
- Store conversation context in Redis by session_id
- Maintain query history within sessions
- Allow referencing previous results
- Expire inactive sessions after 1 hour

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6
"""
import os
import json
import time
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import structlog

try:
    import redis
except ImportError:
    raise ImportError(
        "Redis package not found. Install with: pip install redis[hiredis]==5.0.1"
    )

logger = structlog.get_logger()


@dataclass
class QueryHistoryItem:
    """
    Represents a single query in a conversation session.
    
    Attributes:
        query_id: Unique identifier for this query
        query: Original query text
        synthesized_answer: Synthesized answer from the agent
        sources: List of API sources used
        confidence_score: Confidence score for the answer
        timestamp: Unix timestamp when query was processed
        memory_id: ID of the memory entry for this query
    """
    query_id: str
    query: str
    synthesized_answer: str
    sources: List[str]
    confidence_score: float
    timestamp: float
    memory_id: str


@dataclass
class SessionContext:
    """
    Represents a conversation session context.
    
    Attributes:
        session_id: Unique session identifier
        query_history: List of queries in this session
        created_at: Unix timestamp when session was created
        last_activity: Unix timestamp of last activity
        metadata: Additional session metadata
    """
    session_id: str
    query_history: List[QueryHistoryItem]
    created_at: float
    last_activity: float
    metadata: Dict[str, Any]


class SessionManagerError(Exception):
    """Raised when session management operations fail"""
    pass


class SessionManager:
    """
    Manages conversation sessions for multi-turn interactions.
    
    Stores session context in Redis with automatic expiration after 1 hour
    of inactivity. Maintains query history within sessions and allows
    referencing previous results.
    
    Requirements:
    - 15.1: Maintain conversation context across multiple queries
    - 15.2: Use previous query results as context for follow-up questions
    - 15.3: Allow users to reference previous results
    - 15.4: Store conversation history in Agent_Memory
    - 15.5: Support session management with unique session IDs
    - 15.6: Expire inactive sessions after 1 hour
    """
    
    def __init__(
        self,
        redis_url: str = None,
        redis_password: str = None,
        session_expiration_seconds: int = 3600  # 1 hour
    ):
        """
        Initialize session manager with Redis connection.
        
        Requirements: 15.5 - Support session management with unique session IDs
        
        Args:
            redis_url: Redis connection URL (default from REDIS_URL env var)
            redis_password: Redis password (default from REDIS_PASSWORD env var)
            session_expiration_seconds: Session expiration time (default 3600 = 1 hour)
        """
        # Get configuration from environment if not provided
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.session_expiration_seconds = session_expiration_seconds
        self.session_prefix = "session:"
        
        # Initialize Redis client
        self.client = None
        self._connect()
        
        logger.info(
            "session_manager_initialized",
            redis_url=self.redis_url,
            expiration_seconds=self.session_expiration_seconds
        )
    
    def _connect(self) -> None:
        """
        Connect to Redis with error handling.
        """
        try:
            connection_params = {
                "decode_responses": True,  # We want strings for session data
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
            
            logger.info("session_manager_redis_connected", url=self.redis_url)
            
        except redis.ConnectionError as e:
            logger.error("session_manager_redis_connection_failed", error=str(e), url=self.redis_url)
            raise SessionManagerError(f"Failed to connect to Redis: {e}")
        except Exception as e:
            logger.error("session_manager_redis_connection_error", error=str(e))
            raise SessionManagerError(f"Redis connection error: {e}")
    
    def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new conversation session.
        
        Requirements: 15.5 - Support session management with unique session IDs
        
        Args:
            metadata: Optional metadata for the session
            
        Returns:
            str: Unique session ID
            
        Raises:
            SessionManagerError: If session creation fails
        """
        try:
            # Generate unique session ID
            session_id = f"session_{uuid.uuid4()}"
            
            # Create session context
            current_time = time.time()
            session_context = SessionContext(
                session_id=session_id,
                query_history=[],
                created_at=current_time,
                last_activity=current_time,
                metadata=metadata or {}
            )
            
            # Store in Redis
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self._serialize_session(session_context)
            
            self.client.set(session_key, session_data)
            
            # Set expiration (Requirement 15.6)
            self.client.expire(session_key, self.session_expiration_seconds)
            
            logger.info(
                "session_created",
                session_id=session_id,
                expiration_seconds=self.session_expiration_seconds
            )
            
            return session_id
            
        except redis.RedisError as e:
            logger.error("session_creation_failed", error=str(e))
            raise SessionManagerError(f"Failed to create session: {e}")
        except Exception as e:
            logger.error("session_creation_error", error=str(e))
            raise SessionManagerError(f"Session creation error: {e}")
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        Retrieve a session context.
        
        Requirements:
        - 15.1: Maintain conversation context across multiple queries
        - 15.2: Use previous query results as context
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionContext if found, None otherwise
            
        Raises:
            SessionManagerError: If retrieval fails
        """
        try:
            session_key = f"{self.session_prefix}{session_id}"
            
            # Get session data
            session_data = self.client.get(session_key)
            
            if not session_data:
                logger.info("session_not_found", session_id=session_id)
                return None
            
            # Deserialize session
            session_context = self._deserialize_session(session_data)
            
            # Update last activity and refresh expiration
            session_context.last_activity = time.time()
            self._update_session(session_context)
            
            logger.info(
                "session_retrieved",
                session_id=session_id,
                query_count=len(session_context.query_history)
            )
            
            return session_context
            
        except redis.RedisError as e:
            logger.error("session_retrieval_failed", error=str(e), session_id=session_id)
            raise SessionManagerError(f"Failed to retrieve session: {e}")
        except Exception as e:
            logger.error("session_retrieval_error", error=str(e), session_id=session_id)
            raise SessionManagerError(f"Session retrieval error: {e}")
    
    def add_query_to_session(
        self,
        session_id: str,
        query_id: str,
        query: str,
        synthesized_answer: str,
        sources: List[str],
        confidence_score: float,
        memory_id: str
    ) -> bool:
        """
        Add a query to a session's history.
        
        Requirements:
        - 15.1: Maintain conversation context across multiple queries
        - 15.4: Store conversation history in Agent_Memory
        
        Args:
            session_id: Session identifier
            query_id: Unique query identifier
            query: Original query text
            synthesized_answer: Synthesized answer from the agent
            sources: List of API sources used
            confidence_score: Confidence score for the answer
            memory_id: ID of the memory entry
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            SessionManagerError: If operation fails
        """
        try:
            # Get session
            session_context = self.get_session(session_id)
            
            if not session_context:
                logger.warning("session_not_found_for_query", session_id=session_id)
                return False
            
            # Create query history item
            query_item = QueryHistoryItem(
                query_id=query_id,
                query=query,
                synthesized_answer=synthesized_answer,
                sources=sources,
                confidence_score=confidence_score,
                timestamp=time.time(),
                memory_id=memory_id
            )
            
            # Add to history
            session_context.query_history.append(query_item)
            session_context.last_activity = time.time()
            
            # Update session in Redis
            self._update_session(session_context)
            
            logger.info(
                "query_added_to_session",
                session_id=session_id,
                query_id=query_id,
                total_queries=len(session_context.query_history)
            )
            
            return True
            
        except redis.RedisError as e:
            logger.error("add_query_to_session_failed", error=str(e), session_id=session_id)
            raise SessionManagerError(f"Failed to add query to session: {e}")
        except Exception as e:
            logger.error("add_query_to_session_error", error=str(e), session_id=session_id)
            raise SessionManagerError(f"Add query to session error: {e}")
    
    def get_session_history(self, session_id: str) -> List[QueryHistoryItem]:
        """
        Get query history for a session.
        
        Requirements:
        - 15.2: Use previous query results as context for follow-up questions
        - 15.3: Allow users to reference previous results
        
        Args:
            session_id: Session identifier
            
        Returns:
            List[QueryHistoryItem]: Query history for the session
            
        Raises:
            SessionManagerError: If retrieval fails
        """
        try:
            session_context = self.get_session(session_id)
            
            if not session_context:
                logger.info("session_not_found_for_history", session_id=session_id)
                return []
            
            logger.info(
                "session_history_retrieved",
                session_id=session_id,
                query_count=len(session_context.query_history)
            )
            
            return session_context.query_history
            
        except Exception as e:
            logger.error("get_session_history_error", error=str(e), session_id=session_id)
            raise SessionManagerError(f"Get session history error: {e}")
    
    def get_previous_query(self, session_id: str, index: int = -1) -> Optional[QueryHistoryItem]:
        """
        Get a specific previous query from session history.
        
        Requirements: 15.3 - Allow users to reference previous results
        
        Args:
            session_id: Session identifier
            index: Index of query to retrieve (default -1 for most recent)
            
        Returns:
            QueryHistoryItem if found, None otherwise
        """
        try:
            history = self.get_session_history(session_id)
            
            if not history:
                return None
            
            # Handle negative indices (from end)
            if index < 0:
                index = len(history) + index
            
            # Check bounds
            if 0 <= index < len(history):
                return history[index]
            
            return None
            
        except Exception as e:
            logger.error("get_previous_query_error", error=str(e), session_id=session_id)
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            SessionManagerError: If deletion fails
        """
        try:
            session_key = f"{self.session_prefix}{session_id}"
            
            # Delete from Redis
            deleted = self.client.delete(session_key)
            
            if deleted:
                logger.info("session_deleted", session_id=session_id)
            else:
                logger.info("session_not_found_for_deletion", session_id=session_id)
            
            return bool(deleted)
            
        except redis.RedisError as e:
            logger.error("session_deletion_failed", error=str(e), session_id=session_id)
            raise SessionManagerError(f"Failed to delete session: {e}")
        except Exception as e:
            logger.error("session_deletion_error", error=str(e), session_id=session_id)
            raise SessionManagerError(f"Session deletion error: {e}")
    
    def cleanup_expired_sessions(self) -> int:
        """
        Manually cleanup expired sessions (Redis handles this automatically).
        
        Requirements: 15.6 - Expire inactive sessions after 1 hour
        
        This is mainly for testing/maintenance as Redis automatically
        removes expired keys.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            cleaned = 0
            current_time = time.time()
            expiration_threshold = current_time - self.session_expiration_seconds
            
            # Scan for old sessions
            for key in self.client.scan_iter(f"{self.session_prefix}*"):
                try:
                    session_data = self.client.get(key)
                    if session_data:
                        session_context = self._deserialize_session(session_data)
                        if session_context.last_activity < expiration_threshold:
                            self.client.delete(key)
                            cleaned += 1
                except Exception as e:
                    logger.warning("session_cleanup_item_error", key=key, error=str(e))
                    continue
            
            if cleaned > 0:
                logger.info("expired_sessions_cleaned", count=cleaned)
            
            return cleaned
            
        except Exception as e:
            logger.error("cleanup_expired_sessions_error", error=str(e))
            return 0
    
    def _update_session(self, session_context: SessionContext) -> None:
        """
        Update session in Redis and refresh expiration.
        
        Args:
            session_context: Session context to update
        """
        try:
            session_key = f"{self.session_prefix}{session_context.session_id}"
            session_data = self._serialize_session(session_context)
            
            self.client.set(session_key, session_data)
            
            # Refresh expiration (Requirement 15.6)
            self.client.expire(session_key, self.session_expiration_seconds)
            
        except Exception as e:
            logger.error("session_update_error", error=str(e), session_id=session_context.session_id)
            raise SessionManagerError(f"Failed to update session: {e}")
    
    def _serialize_session(self, session_context: SessionContext) -> str:
        """
        Serialize session context to JSON string.
        
        Args:
            session_context: Session context to serialize
            
        Returns:
            str: JSON string
        """
        # Convert dataclass to dict
        session_dict = {
            "session_id": session_context.session_id,
            "query_history": [asdict(item) for item in session_context.query_history],
            "created_at": session_context.created_at,
            "last_activity": session_context.last_activity,
            "metadata": session_context.metadata
        }
        
        return json.dumps(session_dict)
    
    def _deserialize_session(self, session_data: str) -> SessionContext:
        """
        Deserialize session context from JSON string.
        
        Args:
            session_data: JSON string
            
        Returns:
            SessionContext: Deserialized session context
        """
        session_dict = json.loads(session_data)
        
        # Convert query history items
        query_history = [
            QueryHistoryItem(**item) for item in session_dict.get("query_history", [])
        ]
        
        return SessionContext(
            session_id=session_dict["session_id"],
            query_history=query_history,
            created_at=session_dict["created_at"],
            last_activity=session_dict["last_activity"],
            metadata=session_dict.get("metadata", {})
        )
    
    def close(self) -> None:
        """
        Close Redis connection.
        """
        if self.client:
            try:
                self.client.close()
                logger.info("session_manager_closed")
            except Exception as e:
                logger.warning("session_manager_close_error", error=str(e))
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.close()
