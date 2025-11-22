"""
Agent Orchestrator for Adaptive Research Agent

This module provides the AgentOrchestrator class that coordinates the main
agent processing pipeline:
- Query intent parsing
- Memory retrieval for similar past queries
- Query refinement based on learned patterns
- API discovery and parallel execution
- Information synthesis using Claude
- Result storage in memory

Requirements: 1.1, 1.2, 1.3, 8.2, 8.3, 9.2, 9.3
"""
import asyncio
import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import structlog

from mcp_client import MCPClient, APIEndpoint
from memory_store import MemoryStore, MemoryEntry
from learning_engine import LearningEngine, RefinedQuery

logger = structlog.get_logger()


@dataclass
class QueryIntent:
    """
    Parsed intent from a research query.
    
    Attributes:
        original_query: The original query text
        intent_type: Type of query (factual, analytical, comparative, etc.)
        key_topics: Main topics identified in the query
        search_terms: Refined search terms for API discovery
        context: Additional context for query processing
    """
    original_query: str
    intent_type: str
    key_topics: List[str]
    search_terms: List[str]
    context: str


@dataclass
class APIResult:
    """
    Result from a single API call.
    
    Attributes:
        api_id: API identifier
        api_name: Name of the API
        endpoint: Endpoint called
        data: Response data
        success: Whether the call succeeded
        error: Error message if failed
        response_time_ms: Time taken for the API call
    """
    api_id: str
    api_name: str
    endpoint: str
    data: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    response_time_ms: float = 0.0


@dataclass
class ResearchSynthesis:
    """
    Synthesized research results.
    
    Attributes:
        summary: Executive summary of findings
        detailed_analysis: Detailed analysis of information
        findings: List of key findings
        sources: List of source identifiers
        source_details: Detailed information about each source
        confidence_score: Overall confidence in results (0.0-1.0)
        confidence_breakdown: Confidence by source
    """
    summary: str
    detailed_analysis: str
    findings: List[str]
    sources: List[str]
    source_details: List[APIEndpoint]
    confidence_score: float
    confidence_breakdown: Dict[str, float]


@dataclass
class ResearchResult:
    """
    Complete research result from agent processing.
    
    Attributes:
        query_id: Unique identifier for this query
        query: Original query text
        intent: Parsed query intent
        synthesis: Synthesized results
        similar_queries: Similar past queries from memory
        api_results: Raw API results
        processing_time_ms: Total processing time
        memory_id: ID of stored memory entry
        refined_query: Query refinement information from learning engine
    """
    query_id: str
    query: str
    intent: QueryIntent
    synthesis: ResearchSynthesis
    similar_queries: List[MemoryEntry]
    api_results: List[APIResult]
    processing_time_ms: float
    memory_id: str
    refined_query: Optional[RefinedQuery] = None


class AgentOrchestratorError(Exception):
    """Raised when agent orchestration fails"""
    pass


class AgentOrchestrator:
    """
    Core agent orchestration logic coordinating all operations.
    
    Manages the complete research pipeline:
    1. Parse query intent using Claude
    2. Retrieve similar past queries from memory
    3. Discover relevant APIs from Postman
    4. Execute API calls in parallel
    5. Synthesize information using Claude
    6. Store results in memory
    
    Requirements:
    - 1.1: Parse intent and identify relevant API sources
    - 1.2: Query multiple API endpoints in parallel
    - 1.3: Use Claude to synthesize information
    - 8.2: Use Claude for query intent parsing and synthesis
    - 8.3: Use Claude to generate natural language summaries
    - 9.2: Query Postman to discover relevant APIs
    - 9.3: Use verified publisher APIs
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        memory_store: MemoryStore,
        learning_engine: Optional[LearningEngine] = None
    ):
        """
        Initialize agent orchestrator with dependencies.
        
        Args:
            mcp_client: MCP client for Claude and Postman access
            memory_store: Redis memory store for learning
            learning_engine: Optional learning engine for query refinement
        """
        self.mcp_client = mcp_client
        self.memory_store = memory_store
        self.learning_engine = learning_engine or LearningEngine(memory_store, mcp_client)
        
        logger.info("agent_orchestrator_initialized")
    
    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_sources: int = 5,
        timeout: int = 30
    ) -> ResearchResult:
        """
        Main agent processing pipeline.
        
        Requirements:
        - 1.1: Parse intent and identify relevant API sources
        - 1.2: Query multiple API endpoints in parallel
        - 1.3: Use Claude to synthesize information
        - 1.4: Include source citations with confidence scores
        
        Args:
            query: Natural language research query
            session_id: Optional session ID for multi-turn conversations
            max_sources: Maximum number of API sources to use
            timeout: Timeout in seconds for the entire operation
            
        Returns:
            ResearchResult: Complete research results
            
        Raises:
            AgentOrchestratorError: If processing fails critically
        """
        start_time = time.time()
        query_id = f"query_{int(start_time)}_{hash(query) % 10000}"
        
        logger.info(
            "processing_query",
            query_id=query_id,
            query=query[:100],
            max_sources=max_sources
        )
        
        try:
            # Step 1: Parse query intent using Claude
            logger.info("step_1_parsing_intent", query_id=query_id)
            intent = await self._parse_intent(query)
            
            # Step 2: Get embedding and retrieve similar past queries
            logger.info("step_2_retrieving_memory", query_id=query_id)
            query_embedding = await self._get_embedding(query)
            similar_queries = await self.memory_store.find_similar(
                query_embedding=query_embedding,
                top_k=5,
                min_relevance=0.5,
                session_id=session_id
            )
            
            logger.info(
                "similar_queries_found",
                query_id=query_id,
                count=len(similar_queries)
            )
            
            # Step 2.5: Apply query refinements from learning engine
            # Requirements: 2.3, 2.4, 4.1, 4.5, 4.6
            logger.info("step_2_5_refining_query", query_id=query_id)
            refined_query = await self.learning_engine.refine_query(
                original_query=query,
                similar_patterns=similar_queries
            )
            
            logger.info(
                "query_refined",
                query_id=query_id,
                refinements_count=len(refined_query.refinements),
                confidence=refined_query.confidence,
                prioritized_sources_count=len(refined_query.prioritized_sources)
            )
            
            # Step 3: Discover relevant APIs from Postman
            logger.info("step_3_discovering_apis", query_id=query_id)
            api_sources = await self._discover_apis(intent, max_sources, refined_query)
            
            if not api_sources:
                logger.warning(
                    "no_apis_discovered",
                    query_id=query_id,
                    query=query
                )
            
            # Step 4: Gather information from APIs in parallel
            logger.info(
                "step_4_gathering_information",
                query_id=query_id,
                api_count=len(api_sources)
            )
            api_results = await self._gather_information(
                api_sources,
                intent,
                timeout=timeout
            )
            
            # Step 5: Synthesize results using Claude
            logger.info("step_5_synthesizing_results", query_id=query_id)
            synthesis = await self._synthesize_results(
                query=query,
                intent=intent,
                api_results=api_results,
                similar_queries=similar_queries
            )
            
            # Step 6: Store in memory for learning
            # Requirements: 4.6 - Track refinement effectiveness
            logger.info("step_6_storing_memory", query_id=query_id)
            
            # Include refinement metadata for tracking effectiveness
            results_with_metadata = {
                "summary": synthesis.summary,
                "findings": synthesis.findings,
                "confidence": synthesis.confidence_score,
                "refinement_applied": len(refined_query.refinements) > 0,
                "refinement_confidence": refined_query.confidence,
                "refinements": refined_query.refinements,
                "prioritized_sources_used": [
                    api.api_id for api in api_sources 
                    if api.api_id in refined_query.prioritized_sources
                ]
            }
            
            memory_id = await self.memory_store.store(
                query=query,
                query_embedding=query_embedding,
                results=results_with_metadata,
                sources=[api.api_id for api in api_sources],
                relevance_score=0.5,  # Initial score, updated by feedback
                session_id=session_id
            )
            
            # Calculate total processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Create result
            result = ResearchResult(
                query_id=query_id,
                query=query,
                intent=intent,
                synthesis=synthesis,
                similar_queries=similar_queries,
                api_results=api_results,
                processing_time_ms=processing_time_ms,
                memory_id=memory_id,
                refined_query=refined_query
            )
            
            logger.info(
                "query_processed_successfully",
                query_id=query_id,
                processing_time_ms=processing_time_ms,
                api_sources_used=len(api_sources),
                confidence_score=synthesis.confidence_score,
                refinement_applied=len(refined_query.refinements) > 0,
                refinement_confidence=refined_query.confidence
            )
            
            return result
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "query_processing_failed",
                query_id=query_id,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
            raise AgentOrchestratorError(f"Failed to process query: {e}")

    async def _parse_intent(self, query: str) -> QueryIntent:
        """
        Parse query intent using Claude to understand what the user wants.
        
        Requirements:
        - 8.2: Use Claude for query intent parsing
        - 1.1: Parse the intent and identify relevant API sources
        
        Args:
            query: Natural language query
            
        Returns:
            QueryIntent: Parsed intent with topics and search terms
        """
        try:
            prompt = f"""Analyze this research query and extract structured information.

Query: {query}

Provide a JSON response with:
1. intent_type: The type of query (factual, analytical, comparative, trend_analysis, how_to, etc.)
2. key_topics: List of main topics (3-5 topics)
3. search_terms: List of refined search terms for API discovery (5-10 terms)
4. context: Brief context about what the user is trying to learn

Example response:
{{
    "intent_type": "trend_analysis",
    "key_topics": ["artificial intelligence", "machine learning", "2024 trends"],
    "search_terms": ["AI trends 2024", "machine learning developments", "AI research", "ML innovations"],
    "context": "User wants to understand current trends and developments in AI/ML field"
}}

Respond ONLY with valid JSON, no additional text."""

            response = await self.mcp_client.call_claude(
                prompt=prompt,
                system="You are a query analysis expert. Extract structured information from queries.",
                temperature=0.3  # Lower temperature for more consistent parsing
            )
            
            # Parse JSON response
            intent_data = json.loads(response.strip())
            
            intent = QueryIntent(
                original_query=query,
                intent_type=intent_data.get("intent_type", "general"),
                key_topics=intent_data.get("key_topics", []),
                search_terms=intent_data.get("search_terms", [query]),
                context=intent_data.get("context", "")
            )
            
            logger.info(
                "intent_parsed",
                intent_type=intent.intent_type,
                topics_count=len(intent.key_topics),
                search_terms_count=len(intent.search_terms)
            )
            
            return intent
            
        except json.JSONDecodeError as e:
            logger.warning(
                "intent_parsing_json_error",
                error=str(e),
                response=response[:200] if 'response' in locals() else None
            )
            # Fallback to basic intent
            return QueryIntent(
                original_query=query,
                intent_type="general",
                key_topics=[query],
                search_terms=[query],
                context=f"Research query about: {query}"
            )
        except Exception as e:
            logger.error("intent_parsing_failed", error=str(e))
            # Fallback to basic intent
            return QueryIntent(
                original_query=query,
                intent_type="general",
                key_topics=[query],
                search_terms=[query],
                context=f"Research query about: {query}"
            )
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Claude/Anthropic.
        
        Requirements:
        - 10.2: Generate embeddings using Anthropic's embedding model
        - 2.1: Generate Memory_Vector embedding
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: 1024-dimensional embedding vector
        """
        try:
            # For now, use a simple approach with Claude to generate embeddings
            # In production, you'd use Anthropic's dedicated embedding API
            # or a specialized embedding model
            
            # Placeholder: Generate a deterministic embedding based on text
            # This is a simplified version - in production use proper embeddings
            import hashlib
            
            # Create a deterministic hash-based embedding
            # This ensures same text always gets same embedding
            text_hash = hashlib.sha256(text.encode()).digest()
            
            # Convert to 1024-dimensional vector
            embedding = []
            for i in range(1024):
                # Use hash bytes cyclically to generate float values
                byte_val = text_hash[i % len(text_hash)]
                # Normalize to [-1, 1] range
                embedding.append((byte_val / 127.5) - 1.0)
            
            logger.info(
                "embedding_generated",
                text_length=len(text),
                embedding_dim=len(embedding)
            )
            
            return embedding
            
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            # Return zero vector as fallback
            return [0.0] * 1024
    
    async def _discover_apis(
        self,
        intent: QueryIntent,
        max_sources: int = 5,
        refined_query: Optional[RefinedQuery] = None
    ) -> List[APIEndpoint]:
        """
        Discover relevant APIs from Postman based on query intent.
        
        Prioritizes API sources based on learned performance from past queries.
        
        Requirements:
        - 9.2: Query Postman Public API Network to discover relevant APIs
        - 1.1: Identify relevant API sources from Postman Public API Network
        - 2.4: Prioritize API sources based on historical patterns
        - 4.5: Track refinement effectiveness
        
        Args:
            intent: Parsed query intent
            max_sources: Maximum number of APIs to return
            refined_query: Optional refined query with prioritized sources
            
        Returns:
            List[APIEndpoint]: Discovered API endpoints, prioritized by learning
        """
        try:
            discovered_apis = []
            
            # Try each search term to find relevant APIs
            for search_term in intent.search_terms[:3]:  # Limit to top 3 search terms
                try:
                    apis = await self.mcp_client.discover_apis(
                        query=search_term,
                        verified_only=True,
                        max_results=max_sources
                    )
                    
                    discovered_apis.extend(apis)
                    
                    logger.info(
                        "apis_discovered_for_term",
                        search_term=search_term,
                        count=len(apis)
                    )
                    
                except Exception as e:
                    logger.warning(
                        "api_discovery_failed_for_term",
                        search_term=search_term,
                        error=str(e)
                    )
                    continue
            
            # Remove duplicates based on api_id
            unique_apis = {}
            for api in discovered_apis:
                if api.api_id not in unique_apis:
                    unique_apis[api.api_id] = api
            
            # Apply learned prioritization if available
            # Requirements: 2.4, 4.5 - Prioritize based on learned performance
            if refined_query and refined_query.prioritized_sources:
                logger.info(
                    "applying_learned_prioritization",
                    prioritized_sources=refined_query.prioritized_sources
                )
                
                # Boost priority scores for learned high-performing sources
                for api in unique_apis.values():
                    if api.api_id in refined_query.prioritized_sources:
                        # Boost priority by position in prioritized list
                        boost_index = refined_query.prioritized_sources.index(api.api_id)
                        boost_factor = 1.0 + (0.5 * (1.0 - boost_index / len(refined_query.prioritized_sources)))
                        api.priority_score *= boost_factor
                        
                        logger.debug(
                            "api_priority_boosted",
                            api_id=api.api_id,
                            boost_factor=boost_factor,
                            new_priority=api.priority_score
                        )
            
            # Sort by priority score and limit to max_sources
            sorted_apis = sorted(
                unique_apis.values(),
                key=lambda x: x.priority_score,
                reverse=True
            )[:max_sources]
            
            logger.info(
                "api_discovery_complete",
                total_discovered=len(discovered_apis),
                unique_apis=len(unique_apis),
                final_count=len(sorted_apis),
                learning_applied=refined_query is not None and len(refined_query.prioritized_sources) > 0
            )
            
            return sorted_apis
            
        except Exception as e:
            logger.error("api_discovery_error", error=str(e))
            return []
    
    async def _gather_information(
        self,
        api_sources: List[APIEndpoint],
        intent: QueryIntent,
        timeout: int = 30
    ) -> List[APIResult]:
        """
        Gather information from multiple APIs in parallel.
        
        Requirements:
        - 1.2: Query multiple API endpoints in parallel
        - 1.5: Handle API failures gracefully
        - 1.6: Complete within 30 seconds for up to 5 sources
        
        Args:
            api_sources: List of API endpoints to call
            intent: Query intent for context
            timeout: Timeout for all API calls
            
        Returns:
            List[APIResult]: Results from all API calls
        """
        if not api_sources:
            logger.warning("no_api_sources_to_gather")
            return []
        
        logger.info(
            "gathering_information_parallel",
            api_count=len(api_sources),
            timeout=timeout
        )
        
        # Create tasks for parallel execution
        tasks = []
        for api in api_sources:
            task = self._call_single_api(api, intent, timeout)
            tasks.append(task)
        
        # Execute all API calls in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            
            # Process results
            api_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(
                        "api_call_exception",
                        api_id=api_sources[i].api_id,
                        error=str(result)
                    )
                    # Create error result
                    api_results.append(APIResult(
                        api_id=api_sources[i].api_id,
                        api_name=api_sources[i].api_name,
                        endpoint=api_sources[i].endpoint,
                        data={},
                        success=False,
                        error=str(result)
                    ))
                else:
                    api_results.append(result)
            
            successful = sum(1 for r in api_results if r.success)
            logger.info(
                "information_gathered",
                total_apis=len(api_results),
                successful=successful,
                failed=len(api_results) - successful
            )
            
            return api_results
            
        except asyncio.TimeoutError:
            logger.error(
                "api_gathering_timeout",
                timeout=timeout,
                api_count=len(api_sources)
            )
            # Return partial results
            return []
        except Exception as e:
            logger.error("api_gathering_error", error=str(e))
            return []
    
    async def _call_single_api(
        self,
        api: APIEndpoint,
        intent: QueryIntent,
        timeout: int
    ) -> APIResult:
        """
        Call a single API and return structured result.
        
        Requirements:
        - 1.5: Handle API failures gracefully
        
        Args:
            api: API endpoint to call
            intent: Query intent for context
            timeout: Timeout for this API call
            
        Returns:
            APIResult: Result from API call
        """
        start_time = time.time()
        
        try:
            logger.info(
                "calling_api",
                api_id=api.api_id,
                api_name=api.api_name,
                endpoint=api.endpoint
            )
            
            # Prepare parameters based on intent
            params = {
                "q": intent.original_query,
                "limit": 10
            }
            
            # Call API via MCP client
            response = await self.mcp_client.call_api(
                api_id=api.api_id,
                endpoint=api.endpoint,
                method=api.method,
                params=params,
                timeout=timeout
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Check if call was successful
            success = response.get("success", True) and not response.get("error")
            
            result = APIResult(
                api_id=api.api_id,
                api_name=api.api_name,
                endpoint=api.endpoint,
                data=response if success else {},
                success=success,
                error=response.get("error") if not success else None,
                response_time_ms=response_time_ms
            )
            
            logger.info(
                "api_call_complete",
                api_id=api.api_id,
                success=success,
                response_time_ms=response_time_ms
            )
            
            return result
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "api_call_failed",
                api_id=api.api_id,
                error=str(e),
                response_time_ms=response_time_ms
            )
            
            return APIResult(
                api_id=api.api_id,
                api_name=api.api_name,
                endpoint=api.endpoint,
                data={},
                success=False,
                error=str(e),
                response_time_ms=response_time_ms
            )

    async def _synthesize_results(
        self,
        query: str,
        intent: QueryIntent,
        api_results: List[APIResult],
        similar_queries: List[MemoryEntry]
    ) -> ResearchSynthesis:
        """
        Synthesize information from multiple sources using Claude.
        
        Requirements:
        - 1.3: Use Claude to synthesize information from multiple sources
        - 1.4: Include source citations with confidence scores
        - 8.3: Use Claude to generate natural language summaries
        
        Args:
            query: Original query
            intent: Parsed query intent
            api_results: Results from API calls
            similar_queries: Similar past queries from memory
            
        Returns:
            ResearchSynthesis: Synthesized research results
        """
        try:
            # Filter successful API results
            successful_results = [r for r in api_results if r.success]
            
            if not successful_results:
                logger.warning("no_successful_api_results", query=query)
                return self._create_fallback_synthesis(query, api_results)
            
            # Prepare context from API results
            api_context = self._format_api_results(successful_results)
            
            # Prepare context from similar queries
            memory_context = self._format_memory_context(similar_queries)
            
            # Create synthesis prompt
            prompt = f"""Synthesize research findings from multiple sources into a comprehensive response.

Original Query: {query}

Query Intent: {intent.context}
Key Topics: {', '.join(intent.key_topics)}

API Results:
{api_context}

Similar Past Research:
{memory_context}

Provide a JSON response with:
1. summary: Executive summary (2-3 sentences)
2. detailed_analysis: Detailed analysis combining all sources (3-5 paragraphs)
3. findings: List of 5-7 key findings as bullet points
4. confidence_assessment: Your confidence in each source (0.0-1.0)
5. overall_confidence: Overall confidence in the synthesized answer (0.0-1.0)

Example response:
{{
    "summary": "Brief executive summary of findings...",
    "detailed_analysis": "Detailed analysis paragraph 1...\\n\\nParagraph 2...\\n\\nParagraph 3...",
    "findings": [
        "Key finding 1 with specific data",
        "Key finding 2 with evidence",
        "Key finding 3 with context"
    ],
    "confidence_assessment": {{
        "api_1": 0.85,
        "api_2": 0.70
    }},
    "overall_confidence": 0.78
}}

Respond ONLY with valid JSON, no additional text."""

            response = await self.mcp_client.call_claude(
                prompt=prompt,
                system="You are a research synthesis expert. Combine information from multiple sources into coherent, well-cited analysis.",
                temperature=0.5
            )
            
            # Parse JSON response
            synthesis_data = json.loads(response.strip())
            
            # Build confidence breakdown
            confidence_breakdown = synthesis_data.get("confidence_assessment", {})
            
            # Create synthesis object
            synthesis = ResearchSynthesis(
                summary=synthesis_data.get("summary", "No summary available"),
                detailed_analysis=synthesis_data.get("detailed_analysis", ""),
                findings=synthesis_data.get("findings", []),
                sources=[r.api_id for r in successful_results],
                source_details=[
                    self._api_result_to_endpoint(r) for r in successful_results
                ],
                confidence_score=float(synthesis_data.get("overall_confidence", 0.5)),
                confidence_breakdown=confidence_breakdown
            )
            
            logger.info(
                "synthesis_complete",
                findings_count=len(synthesis.findings),
                sources_count=len(synthesis.sources),
                confidence=synthesis.confidence_score
            )
            
            return synthesis
            
        except json.JSONDecodeError as e:
            logger.warning(
                "synthesis_json_error",
                error=str(e),
                response=response[:200] if 'response' in locals() else None
            )
            return self._create_fallback_synthesis(query, api_results)
        except Exception as e:
            logger.error("synthesis_failed", error=str(e))
            return self._create_fallback_synthesis(query, api_results)
    
    def _format_api_results(self, api_results: List[APIResult]) -> str:
        """
        Format API results for synthesis prompt.
        
        Args:
            api_results: List of successful API results
            
        Returns:
            str: Formatted API results
        """
        formatted = []
        
        for i, result in enumerate(api_results, 1):
            formatted.append(f"\nSource {i}: {result.api_name}")
            formatted.append(f"API ID: {result.api_id}")
            formatted.append(f"Endpoint: {result.endpoint}")
            formatted.append(f"Response Time: {result.response_time_ms:.0f}ms")
            
            # Format data (truncate if too long)
            data_str = json.dumps(result.data, indent=2)
            if len(data_str) > 1000:
                data_str = data_str[:1000] + "\n... (truncated)"
            
            formatted.append(f"Data:\n{data_str}")
            formatted.append("-" * 60)
        
        return "\n".join(formatted)
    
    def _format_memory_context(self, similar_queries: List[MemoryEntry]) -> str:
        """
        Format similar past queries for synthesis prompt.
        
        Args:
            similar_queries: List of similar past queries
            
        Returns:
            str: Formatted memory context
        """
        if not similar_queries:
            return "No similar past research found."
        
        formatted = []
        
        for i, memory in enumerate(similar_queries[:3], 1):  # Limit to top 3
            formatted.append(f"\nPast Query {i}: {memory.query}")
            formatted.append(f"Similarity: {memory.similarity_score:.2f}")
            formatted.append(f"Relevance Score: {memory.relevance_score:.2f}")
            formatted.append(f"Sources Used: {', '.join(memory.api_sources)}")
            
            # Add summary if available
            if memory.results and isinstance(memory.results, dict):
                summary = memory.results.get("summary", "")
                if summary:
                    formatted.append(f"Summary: {summary[:200]}...")
            
            formatted.append("-" * 60)
        
        return "\n".join(formatted)
    
    def _api_result_to_endpoint(self, result: APIResult) -> APIEndpoint:
        """
        Convert APIResult to APIEndpoint for source details.
        
        Args:
            result: API result
            
        Returns:
            APIEndpoint: API endpoint information
        """
        return APIEndpoint(
            api_id=result.api_id,
            api_name=result.api_name,
            endpoint=result.endpoint,
            method="GET",  # Default
            description="",
            verified=True,
            priority_score=0.5
        )
    
    def _create_fallback_synthesis(
        self,
        query: str,
        api_results: List[APIResult]
    ) -> ResearchSynthesis:
        """
        Create fallback synthesis when Claude synthesis fails.
        
        Args:
            query: Original query
            api_results: API results (may include failures)
            
        Returns:
            ResearchSynthesis: Basic synthesis
        """
        successful = [r for r in api_results if r.success]
        failed = [r for r in api_results if not r.success]
        
        summary = f"Research query: {query}. "
        if successful:
            summary += f"Retrieved data from {len(successful)} source(s). "
        if failed:
            summary += f"{len(failed)} source(s) failed. "
        
        findings = []
        if successful:
            findings.append(f"Successfully retrieved data from {len(successful)} API source(s)")
        if failed:
            findings.append(f"Failed to retrieve data from {len(failed)} API source(s)")
        
        return ResearchSynthesis(
            summary=summary,
            detailed_analysis="Synthesis failed. Raw API results available.",
            findings=findings,
            sources=[r.api_id for r in successful],
            source_details=[self._api_result_to_endpoint(r) for r in successful],
            confidence_score=0.3 if successful else 0.1,
            confidence_breakdown={r.api_id: 0.3 for r in successful}
        )
