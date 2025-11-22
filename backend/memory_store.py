"""
Redis Vector Memory Store for Adaptive Research Agent

This module provides the MemoryStore class that manages agent memory using Redis
with RediSearch for vector-based semantic search.

Stores:
- Query text and embeddings
- API sources used
- Results obtained
- Relevance scores
- Timestamps

Provides:
- Semantic search for similar past queries
- Relevance score updates based on feedback
- Automatic memory cleanup (30-day expiration)

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 2.1, 2.2, 2.6
"""
import os
import json
import time
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np
import structlog

try:
    import redis
    from redis.commands.search.field import VectorField, TextField, NumericField, TagField
    from redis.commands.search.indexDefinition import IndexDefinition, IndexType
    from redis.commands.search.query import Query
except ImportError:
    raise ImportError(
        "Redis package not found. Install with: pip install redis[hiredis]==5.0.1"
    )

logger = structlog.get_logger()


@dataclass
class MemoryEntry:
    """
    Represents a single memory entry from the agent's past interactions.
    
    Attributes:
        memory_id: Unique identifier for this memory
        query: Original query text
        results: Synthesized results/answer
        relevance_score: User feedback score (0.0-1.0)
        api_sources: List of API sources used
        similarity_score: Cosine similarity to search query (for retrieved memories)
        timestamp: Unix timestamp when memory was created
        session_id: Optional session identifier for multi-turn conversations
    """
    memory_id: str
    query: str
    results: Dict[str, Any]
    relevance_score: float
    api_sources: List[str]
    similarity_score: float
    timestamp: float
    session_id: Optional[str] = None


@dataclass
class MemoryMetrics:
    """
    Statistics about the memory store.
    
    Attributes:
        total_memories: Total number of memories stored
        avg_relevance: Average relevance score across all memories
        high_quality_memories: Count of memories with relevance >= 0.7
        memory_size_bytes: Approximate size of memory in bytes
    """
    total_memories: int
    avg_relevance: float
    high_quality_memories: int
    memory_size_bytes: int


class MemoryStoreError(Exception):
    """Raised when memory store operations fail"""
    pass


class MemoryStore:
    """
    Redis-based vector storage for agent memory with semantic search capabilities.
    
    Uses RediSearch module for vector similarity search with cosine distance.
    Stores query embeddings (1024-dimensional) along with metadata for learning.
    
    Requirements:
    - 10.1: Connect to Redis with RediSearch module
    - 10.2: Generate embeddings using Anthropic's embedding model
    - 10.3: Store vectors with metadata in Redis
    - 10.4: Perform k-nearest neighbor search
    - 10.5: Handle Redis connection failures gracefully
    - 10.6: Implement memory cleanup
    - 2.1: Store query, embedding, results, sources
    - 2.2: Store relevance scores
    - 2.6: 30-day expiration for stale entries
    """
    
    def __init__(
        self,
        redis_url: str = None,
        redis_password: str = None,
        embedding_dim: int = 1024,
        index_name: str = "agent_memory_idx"
    ):
        """
        Initialize memory store with Redis connection.
        
        Requirements: 10.1 - Connect to Redis with RediSearch module
        
        Args:
            redis_url: Redis connection URL (default from REDIS_URL env var)
            redis_password: Redis password (default from REDIS_PASSWORD env var)
            embedding_dim: Dimension of embedding vectors (default 1024 for Anthropic)
            index_name: Name of the Redis search index
        """
        # Get configuration from environment if not provided
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.embedding_dim = embedding_dim
        self.index_name = index_name
        self.memory_prefix = "memory:"
        
        # Memory expiration (30 days in seconds)
        self.expiration_seconds = 30 * 24 * 60 * 60  # Requirement 2.6
        
        # Initialize Redis client
        self.client = None
        self._connect()
        
        # Create search index
        self._create_index()
        
        logger.info(
            "memory_store_initialized",
            redis_url=self.redis_url,
            embedding_dim=self.embedding_dim,
            index_name=self.index_name
        )
    
    def _connect(self) -> None:
        """
        Connect to Redis with error handling.
        
        Requirements: 10.5 - Handle Redis connection failures gracefully
        """
        try:
            connection_params = {
                "decode_responses": False,  # We need bytes for vector storage
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
            
            logger.info("redis_connected", url=self.redis_url)
            
        except redis.ConnectionError as e:
            logger.error("redis_connection_failed", error=str(e), url=self.redis_url)
            raise MemoryStoreError(f"Failed to connect to Redis: {e}")
        except Exception as e:
            logger.error("redis_connection_error", error=str(e))
            raise MemoryStoreError(f"Redis connection error: {e}")

    def _create_index(self) -> None:
        """
        Create Redis vector search index for semantic similarity search.
        
        Requirements: 10.3 - Store vectors with metadata in Redis
        
        Creates index with:
        - Vector field for embeddings (1024-dim, COSINE distance)
        - Text fields for query and results
        - Numeric fields for scores and timestamps
        - Tag field for API sources
        """
        try:
            # Check if index already exists
            try:
                self.client.ft(self.index_name).info()
                logger.info("redis_index_exists", index_name=self.index_name)
                return
            except redis.ResponseError:
                # Index doesn't exist, create it
                pass
            
            # Define schema
            schema = (
                VectorField(
                    "query_embedding",
                    "FLAT",  # Use FLAT algorithm for exact k-NN
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.embedding_dim,
                        "DISTANCE_METRIC": "COSINE"
                    }
                ),
                TextField("query_text", weight=2.0),
                TextField("results_summary"),
                NumericField("relevance_score", sortable=True),
                NumericField("timestamp", sortable=True),
                TagField("api_sources"),
                TextField("session_id")
            )
            
            # Define index on hash documents with memory: prefix
            definition = IndexDefinition(
                prefix=[self.memory_prefix],
                index_type=IndexType.HASH
            )
            
            # Create index
            self.client.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
            
            logger.info(
                "redis_index_created",
                index_name=self.index_name,
                embedding_dim=self.embedding_dim
            )
            
        except redis.ResponseError as e:
            if "Index already exists" in str(e):
                logger.info("redis_index_already_exists", index_name=self.index_name)
            else:
                logger.error("redis_index_creation_failed", error=str(e))
                raise MemoryStoreError(f"Failed to create Redis index: {e}")
        except Exception as e:
            logger.error("redis_index_error", error=str(e))
            raise MemoryStoreError(f"Redis index error: {e}")
    
    async def store(
        self,
        query: str,
        query_embedding: List[float],
        results: Dict[str, Any],
        sources: List[str],
        relevance_score: float = 0.5,
        session_id: Optional[str] = None
    ) -> str:
        """
        Store query and results in memory with vector embedding.
        
        Requirements:
        - 2.1: Store query text, API sources used, results obtained, and Relevance_Score
        - 2.2: Store query, results, and relevance score
        - 2.6: Set 30-day expiration
        
        Args:
            query: Original query text
            query_embedding: 1024-dimensional embedding vector
            results: Synthesized results/answer dictionary
            sources: List of API source identifiers used
            relevance_score: Initial relevance score (0.0-1.0)
            session_id: Optional session identifier
            
        Returns:
            str: Unique memory ID
            
        Raises:
            MemoryStoreError: If storage fails
        """
        try:
            # Generate unique memory ID
            memory_id = f"{self.memory_prefix}{uuid.uuid4()}"
            
            # Validate embedding dimension
            if len(query_embedding) != self.embedding_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.embedding_dim}, "
                    f"got {len(query_embedding)}"
                )
            
            # Convert embedding to bytes (FLOAT32)
            embedding_bytes = np.array(query_embedding, dtype=np.float32).tobytes()
            
            # Prepare results summary (truncate if too long)
            results_summary = json.dumps(results)
            if len(results_summary) > 10000:
                results_summary = results_summary[:10000] + "..."
            
            # Prepare data for storage
            memory_data = {
                "query_text": query,
                "query_embedding": embedding_bytes,
                "results_summary": results_summary,
                "relevance_score": relevance_score,
                "timestamp": time.time(),
                "api_sources": ",".join(sources),  # Tag field uses comma-separated values
                "session_id": session_id or ""
            }
            
            # Store in Redis as hash
            self.client.hset(
                memory_id,
                mapping=memory_data
            )
            
            # Set expiration (30 days) - Requirement 2.6
            self.client.expire(memory_id, self.expiration_seconds)
            
            logger.info(
                "memory_stored",
                memory_id=memory_id,
                query_length=len(query),
                sources_count=len(sources),
                relevance_score=relevance_score
            )
            
            return memory_id
            
        except redis.RedisError as e:
            logger.error("memory_storage_failed", error=str(e), query=query[:100])
            raise MemoryStoreError(f"Failed to store memory: {e}")
        except Exception as e:
            logger.error("memory_storage_error", error=str(e))
            raise MemoryStoreError(f"Memory storage error: {e}")
    
    async def find_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_relevance: float = 0.0,
        session_id: Optional[str] = None
    ) -> List[MemoryEntry]:
        """
        Find similar past queries using k-NN vector search.
        
        Requirements:
        - 10.4: Perform k-nearest neighbor search to find similar past queries
        - 2.3: Perform semantic search on Agent_Memory before processing new queries
        
        Args:
            query_embedding: 1024-dimensional query embedding
            top_k: Number of similar memories to return
            min_relevance: Minimum relevance score filter
            session_id: Optional filter by session
            
        Returns:
            List[MemoryEntry]: Similar past queries sorted by similarity
            
        Raises:
            MemoryStoreError: If search fails
        """
        try:
            # Validate embedding dimension
            if len(query_embedding) != self.embedding_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.embedding_dim}, "
                    f"got {len(query_embedding)}"
                )
            
            # Convert embedding to bytes
            query_vector = np.array(query_embedding, dtype=np.float32).tobytes()
            
            # Build search query with k-NN
            # KNN search returns distance, we convert to similarity later
            base_query = f"*=>[KNN {top_k} @query_embedding $vec AS distance]"
            
            # Add relevance filter if specified
            if min_relevance > 0.0:
                base_query = f"@relevance_score:[{min_relevance} inf]=>[KNN {top_k} @query_embedding $vec AS distance]"
            
            # Add session filter if specified
            if session_id:
                base_query = f"@session_id:{{{session_id}}}=>[KNN {top_k} @query_embedding $vec AS distance]"
            
            query = (
                Query(base_query)
                .sort_by("distance")  # Sort by distance (lower = more similar)
                .return_fields(
                    "query_text",
                    "results_summary",
                    "relevance_score",
                    "api_sources",
                    "timestamp",
                    "session_id",
                    "distance"
                )
                .dialect(2)  # Use dialect 2 for vector search
            )
            
            # Execute search
            results = self.client.ft(self.index_name).search(
                query,
                query_params={"vec": query_vector}
            )
            
            # Parse results into MemoryEntry objects
            memories = []
            for doc in results.docs:
                try:
                    # Convert distance to similarity (1 - distance for cosine)
                    distance = float(doc.distance) if hasattr(doc, 'distance') else 1.0
                    similarity_score = 1.0 - distance
                    
                    # Parse results JSON
                    results_dict = {}
                    if hasattr(doc, 'results_summary'):
                        try:
                            results_dict = json.loads(doc.results_summary)
                        except json.JSONDecodeError:
                            results_dict = {"summary": doc.results_summary}
                    
                    # Parse API sources
                    api_sources = []
                    if hasattr(doc, 'api_sources'):
                        api_sources = doc.api_sources.split(',') if doc.api_sources else []
                    
                    # Create memory entry
                    memory = MemoryEntry(
                        memory_id=doc.id,
                        query=doc.query_text if hasattr(doc, 'query_text') else "",
                        results=results_dict,
                        relevance_score=float(doc.relevance_score) if hasattr(doc, 'relevance_score') else 0.5,
                        api_sources=api_sources,
                        similarity_score=similarity_score,
                        timestamp=float(doc.timestamp) if hasattr(doc, 'timestamp') else time.time(),
                        session_id=doc.session_id if hasattr(doc, 'session_id') and doc.session_id else None
                    )
                    
                    memories.append(memory)
                    
                except Exception as e:
                    logger.warning("memory_parsing_error", error=str(e), doc_id=doc.id)
                    continue
            
            logger.info(
                "similar_memories_found",
                count=len(memories),
                top_k=top_k,
                min_relevance=min_relevance
            )
            
            return memories
            
        except redis.RedisError as e:
            logger.error("memory_search_failed", error=str(e))
            # Return empty list for graceful degradation (Requirement 10.5)
            logger.warning("memory_search_degraded", returning_empty=True)
            return []
        except Exception as e:
            logger.error("memory_search_error", error=str(e))
            return []

    async def update_relevance(
        self,
        memory_id: str,
        new_score: float
    ) -> bool:
        """
        Update relevance score based on user feedback.
        
        Requirements:
        - 3.1: Accept relevance feedback and update memory
        - 3.2: Update Relevance_Score for corresponding memory entry
        
        Args:
            memory_id: Unique memory identifier
            new_score: New relevance score (0.0-1.0)
            
        Returns:
            bool: True if update successful, False otherwise
            
        Raises:
            MemoryStoreError: If update fails
        """
        try:
            # Validate score range
            if not 0.0 <= new_score <= 1.0:
                raise ValueError(f"Relevance score must be between 0.0 and 1.0, got {new_score}")
            
            # Check if memory exists
            if not self.client.exists(memory_id):
                logger.warning("memory_not_found", memory_id=memory_id)
                return False
            
            # Update relevance score
            self.client.hset(memory_id, "relevance_score", new_score)
            
            # Refresh expiration (reset 30-day timer)
            self.client.expire(memory_id, self.expiration_seconds)
            
            logger.info(
                "relevance_updated",
                memory_id=memory_id,
                new_score=new_score
            )
            
            return True
            
        except redis.RedisError as e:
            logger.error("relevance_update_failed", error=str(e), memory_id=memory_id)
            raise MemoryStoreError(f"Failed to update relevance: {e}")
        except Exception as e:
            logger.error("relevance_update_error", error=str(e))
            raise MemoryStoreError(f"Relevance update error: {e}")
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: Unique memory identifier
            
        Returns:
            MemoryEntry if found, None otherwise
        """
        try:
            # Get memory data
            memory_data = self.client.hgetall(memory_id)
            
            if not memory_data:
                return None
            
            # Parse data
            query_text = memory_data.get(b'query_text', b'').decode('utf-8')
            results_summary = memory_data.get(b'results_summary', b'{}').decode('utf-8')
            relevance_score = float(memory_data.get(b'relevance_score', b'0.5'))
            timestamp = float(memory_data.get(b'timestamp', b'0'))
            api_sources_str = memory_data.get(b'api_sources', b'').decode('utf-8')
            session_id = memory_data.get(b'session_id', b'').decode('utf-8')
            
            # Parse JSON results
            try:
                results_dict = json.loads(results_summary)
            except json.JSONDecodeError:
                results_dict = {"summary": results_summary}
            
            # Parse API sources
            api_sources = api_sources_str.split(',') if api_sources_str else []
            
            return MemoryEntry(
                memory_id=memory_id,
                query=query_text,
                results=results_dict,
                relevance_score=relevance_score,
                api_sources=api_sources,
                similarity_score=1.0,  # Exact match
                timestamp=timestamp,
                session_id=session_id if session_id else None
            )
            
        except Exception as e:
            logger.error("get_memory_error", error=str(e), memory_id=memory_id)
            return None
    
    async def get_recent(
        self,
        limit: int = 50,
        min_relevance: float = 0.0
    ) -> List[MemoryEntry]:
        """
        Get recent memories sorted by timestamp.
        
        Args:
            limit: Maximum number of memories to return
            min_relevance: Minimum relevance score filter
            
        Returns:
            List[MemoryEntry]: Recent memories sorted by timestamp (newest first)
        """
        try:
            # Build query for recent memories
            if min_relevance > 0.0:
                query_str = f"@relevance_score:[{min_relevance} inf]"
            else:
                query_str = "*"
            
            query = (
                Query(query_str)
                .sort_by("timestamp", asc=False)  # Newest first
                .paging(0, limit)
                .return_fields(
                    "query_text",
                    "results_summary",
                    "relevance_score",
                    "api_sources",
                    "timestamp",
                    "session_id"
                )
            )
            
            # Execute search
            results = self.client.ft(self.index_name).search(query)
            
            # Parse results
            memories = []
            for doc in results.docs:
                try:
                    results_dict = {}
                    if hasattr(doc, 'results_summary'):
                        try:
                            results_dict = json.loads(doc.results_summary)
                        except json.JSONDecodeError:
                            results_dict = {"summary": doc.results_summary}
                    
                    api_sources = []
                    if hasattr(doc, 'api_sources'):
                        api_sources = doc.api_sources.split(',') if doc.api_sources else []
                    
                    memory = MemoryEntry(
                        memory_id=doc.id,
                        query=doc.query_text if hasattr(doc, 'query_text') else "",
                        results=results_dict,
                        relevance_score=float(doc.relevance_score) if hasattr(doc, 'relevance_score') else 0.5,
                        api_sources=api_sources,
                        similarity_score=1.0,
                        timestamp=float(doc.timestamp) if hasattr(doc, 'timestamp') else time.time(),
                        session_id=doc.session_id if hasattr(doc, 'session_id') and doc.session_id else None
                    )
                    
                    memories.append(memory)
                    
                except Exception as e:
                    logger.warning("memory_parsing_error", error=str(e), doc_id=doc.id)
                    continue
            
            logger.info("recent_memories_retrieved", count=len(memories), limit=limit)
            
            return memories
            
        except Exception as e:
            logger.error("get_recent_error", error=str(e))
            return []
    
    async def get_metrics(self) -> MemoryMetrics:
        """
        Get memory store statistics.
        
        Requirements: 7.5 - Expose metrics for monitoring
        
        Returns:
            MemoryMetrics: Statistics about stored memories
        """
        try:
            # Count total memories with prefix
            total_memories = 0
            memory_size_bytes = 0
            all_scores = []
            
            # Scan for all memory keys
            for key in self.client.scan_iter(f"{self.memory_prefix}*"):
                total_memories += 1
                
                # Get memory size
                try:
                    memory_size_bytes += self.client.memory_usage(key) or 0
                except:
                    pass  # memory_usage not available in all Redis versions
                
                # Get relevance score
                score = self.client.hget(key, "relevance_score")
                if score:
                    try:
                        all_scores.append(float(score))
                    except (ValueError, TypeError):
                        pass
            
            # Calculate metrics
            avg_relevance = np.mean(all_scores) if all_scores else 0.0
            high_quality_memories = sum(1 for s in all_scores if s >= 0.7)
            
            metrics = MemoryMetrics(
                total_memories=total_memories,
                avg_relevance=float(avg_relevance),
                high_quality_memories=high_quality_memories,
                memory_size_bytes=memory_size_bytes
            )
            
            logger.info(
                "memory_metrics_calculated",
                total=total_memories,
                avg_relevance=avg_relevance,
                high_quality=high_quality_memories
            )
            
            return metrics
            
        except Exception as e:
            logger.error("get_metrics_error", error=str(e))
            return MemoryMetrics(
                total_memories=0,
                avg_relevance=0.0,
                high_quality_memories=0,
                memory_size_bytes=0
            )
    
    async def cleanup_expired(self) -> int:
        """
        Manually cleanup expired memories (Redis handles this automatically).
        
        Requirements: 10.6 - Implement memory cleanup
        
        This is mainly for testing/maintenance as Redis automatically
        removes expired keys.
        
        Returns:
            int: Number of memories cleaned up
        """
        try:
            cleaned = 0
            current_time = time.time()
            expiration_threshold = current_time - self.expiration_seconds
            
            # Scan for old memories
            for key in self.client.scan_iter(f"{self.memory_prefix}*"):
                timestamp = self.client.hget(key, "timestamp")
                if timestamp:
                    try:
                        ts = float(timestamp)
                        if ts < expiration_threshold:
                            self.client.delete(key)
                            cleaned += 1
                    except (ValueError, TypeError):
                        pass
            
            if cleaned > 0:
                logger.info("expired_memories_cleaned", count=cleaned)
            
            return cleaned
            
        except Exception as e:
            logger.error("cleanup_error", error=str(e))
            return 0
    
    def close(self) -> None:
        """
        Close Redis connection.
        """
        if self.client:
            try:
                self.client.close()
                logger.info("memory_store_closed")
            except Exception as e:
                logger.warning("memory_store_close_error", error=str(e))
    
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
