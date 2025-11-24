"""
Memory Store - Simple Redis storage for query history
"""
import redis
import json
import time
import uuid
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class MemoryStore:
    """Simple Redis storage for query history"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis", url=redis_url)
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def store(
        self,
        query: str,
        results: Dict[str, Any],
        sources: List[str]
    ) -> str:
        """Store query and results in Redis"""
        try:
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
            
            logger.info("Query stored in Redis", query_id=query_id)
            return query_id
            
        except Exception as e:
            logger.error("Failed to store query in Redis", error=str(e))
            raise
    
    async def get_history(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get past queries in chronological order"""
        try:
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
            
            logger.info(f"Retrieved {len(queries)} queries from history")
            return queries
            
        except Exception as e:
            logger.error("Failed to get history from Redis", error=str(e))
            return []
