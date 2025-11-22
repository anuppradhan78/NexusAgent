"""
Learning Engine for Adaptive Research Agent

This module provides the LearningEngine class that implements continuous
improvement through pattern analysis and adaptive behavior.

Capabilities:
- Query refinement based on successful past patterns
- Confidence threshold adjustment based on feedback
- API source performance tracking and prioritization
- Learning from relevance feedback

Requirements: 4.1, 4.2, 4.3, 4.4, 3.3, 3.4, 3.5
"""
import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
import structlog

from memory_store import MemoryStore, MemoryEntry
from mcp_client import MCPClient

logger = structlog.get_logger()


@dataclass
class RefinedQuery:
    """
    Result of query refinement process.
    
    Attributes:
        query: Original query text
        refinements: List of suggested refinements
        confidence: Confidence in refinement quality
        prioritized_sources: API sources to prioritize based on history
        reasoning: Explanation of refinement decisions
    """
    query: str
    refinements: List[str]
    confidence: float
    prioritized_sources: List[str]
    reasoning: str = ""


@dataclass
class SourceMetrics:
    """
    Performance metrics for an API source.
    
    Attributes:
        api_id: API identifier
        api_name: API name
        total_uses: Total times this source was used
        success_rate: Percentage of high-relevance results
        avg_relevance: Average relevance score
        priority_score: Calculated priority for future use
    """
    api_id: str
    api_name: str
    total_uses: int
    success_rate: float
    avg_relevance: float
    priority_score: float


@dataclass
class FeedbackEntry:
    """
    Feedback entry for learning analysis.
    
    Attributes:
        query_id: Query identifier
        confidence: Confidence score at time of query
        relevance_score: User-provided relevance score
        timestamp: When feedback was provided
    """
    query_id: str
    confidence: float
    relevance_score: float
    timestamp: float


class LearningEngine:
    """
    Continuous improvement engine that learns from feedback and patterns.
    
    Implements:
    - Query refinement based on successful patterns (Req 4.1, 4.2, 4.3)
    - Confidence threshold adaptation (Req 3.3, 3.4)
    - API source performance tracking (Req 3.5, 4.4)
    - Pattern recognition and application
    
    The engine analyzes past interactions stored in memory to:
    1. Identify successful query patterns
    2. Prioritize high-performing API sources
    3. Adjust confidence thresholds to reduce false positives
    4. Refine queries to improve results
    """
    
    def __init__(
        self,
        memory_store: MemoryStore,
        mcp_client: MCPClient,
        initial_confidence_threshold: float = None,
        learning_rate: float = None
    ):
        """
        Initialize learning engine.
        
        Args:
            memory_store: Memory store for accessing past interactions
            mcp_client: MCP client for Claude reasoning
            initial_confidence_threshold: Starting confidence threshold
            learning_rate: Rate of threshold adjustment (0.0-1.0)
        """
        self.memory_store = memory_store
        self.mcp_client = mcp_client
        
        # Get configuration from environment
        self.confidence_threshold = initial_confidence_threshold or float(
            os.getenv("CONFIDENCE_THRESHOLD_INITIAL", "0.5")
        )
        self.learning_rate = learning_rate or float(
            os.getenv("LEARNING_RATE", "0.1")
        )
        
        # Clamp values to valid ranges
        self.confidence_threshold = max(0.3, min(0.9, self.confidence_threshold))
        self.learning_rate = max(0.01, min(0.5, self.learning_rate))
        
        # Cache for source performance metrics
        self._source_metrics_cache: Optional[Dict[str, SourceMetrics]] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = 300.0  # 5 minutes
        
        logger.info(
            "learning_engine_initialized",
            confidence_threshold=self.confidence_threshold,
            learning_rate=self.learning_rate
        )
    
    async def refine_query(
        self,
        original_query: str,
        similar_patterns: List[MemoryEntry]
    ) -> RefinedQuery:
        """
        Refine query based on successful past patterns.
        
        Requirements:
        - 4.1: Retrieve top 5 most similar past queries from Agent_Memory
        - 4.2: Analyze successful patterns (API sources, query parameters, result quality)
        - 4.3: Automatically refine current query by incorporating successful parameters
        
        Args:
            original_query: The original user query
            similar_patterns: Similar past queries from memory
            
        Returns:
            RefinedQuery: Refined query with suggestions and prioritized sources
        """
        try:
            logger.info(
                "refining_query",
                query=original_query[:100],
                similar_patterns_count=len(similar_patterns)
            )
            
            # Filter for high-quality patterns (relevance >= 0.7)
            successful_patterns = [
                p for p in similar_patterns
                if p.relevance_score >= 0.7
            ]
            
            # If no successful patterns, return original query with default confidence
            if not successful_patterns:
                logger.info(
                    "no_successful_patterns",
                    query=original_query[:100]
                )
                return RefinedQuery(
                    query=original_query,
                    refinements=[],
                    confidence=0.5,
                    prioritized_sources=[],
                    reasoning="No successful past patterns found for refinement"
                )
            
            # Extract top API sources from successful patterns
            prioritized_sources = self._extract_top_sources(successful_patterns)
            
            # Use Claude to analyze patterns and suggest refinements
            pattern_analysis = await self._analyze_patterns_with_claude(
                original_query,
                successful_patterns
            )
            
            # Parse refinements from Claude's analysis
            refinements = self._parse_refinements(pattern_analysis)
            
            # Calculate confidence based on pattern quality
            confidence = self._calculate_confidence(successful_patterns)
            
            logger.info(
                "query_refined",
                query=original_query[:100],
                refinements_count=len(refinements),
                confidence=confidence,
                prioritized_sources_count=len(prioritized_sources)
            )
            
            return RefinedQuery(
                query=original_query,
                refinements=refinements,
                confidence=confidence,
                prioritized_sources=prioritized_sources,
                reasoning=pattern_analysis
            )
            
        except Exception as e:
            logger.error("query_refinement_error", error=str(e), query=original_query[:100])
            # Return original query on error
            return RefinedQuery(
                query=original_query,
                refinements=[],
                confidence=0.5,
                prioritized_sources=[],
                reasoning=f"Error during refinement: {str(e)}"
            )
    
    async def _analyze_patterns_with_claude(
        self,
        original_query: str,
        successful_patterns: List[MemoryEntry]
    ) -> str:
        """
        Use Claude to analyze successful patterns and suggest refinements.
        
        Requirements: 4.2 - Analyze successful patterns
        
        Args:
            original_query: Current query to refine
            successful_patterns: Past successful queries
            
        Returns:
            str: Claude's analysis and suggestions
        """
        # Format patterns for Claude
        patterns_text = self._format_patterns(successful_patterns)
        
        prompt = f"""Analyze these successful past queries and suggest refinements for the current query.

Current query: {original_query}

Successful past patterns:
{patterns_text}

Suggest:
1. Additional search terms to include
2. API sources to prioritize (based on which sources worked well in past)
3. Query parameters or filters that worked well
4. Information types that were most relevant

Provide concrete, actionable refinements in JSON format:
{{
    "refinements": [
        "refinement 1",
        "refinement 2",
        ...
    ],
    "reasoning": "explanation of why these refinements will help"
}}
"""
        
        try:
            response = await self.mcp_client.call_claude(
                prompt=prompt,
                system="You are a query optimization expert. Suggest concrete, actionable refinements based on successful patterns.",
                temperature=0.3  # Lower temperature for more focused suggestions
            )
            return response
        except Exception as e:
            logger.error("claude_pattern_analysis_error", error=str(e))
            return json.dumps({
                "refinements": [],
                "reasoning": "Error analyzing patterns"
            })
    
    def _format_patterns(self, patterns: List[MemoryEntry]) -> str:
        """
        Format memory patterns for Claude analysis.
        
        Args:
            patterns: List of memory entries
            
        Returns:
            str: Formatted patterns text
        """
        formatted = []
        for i, pattern in enumerate(patterns[:5], 1):  # Limit to top 5
            formatted.append(f"""
Pattern {i}:
- Query: {pattern.query}
- Relevance Score: {pattern.relevance_score:.2f}
- API Sources: {', '.join(pattern.api_sources)}
- Similarity: {pattern.similarity_score:.2f}
""")
        return '\n'.join(formatted)
    
    def _parse_refinements(self, analysis: str) -> List[str]:
        """
        Parse refinements from Claude's analysis.
        
        Args:
            analysis: Claude's response text
            
        Returns:
            List[str]: List of refinement suggestions
        """
        try:
            # Try to parse as JSON
            data = json.loads(analysis)
            return data.get('refinements', [])
        except json.JSONDecodeError:
            # Fallback: extract bullet points or numbered items
            refinements = []
            for line in analysis.split('\n'):
                line = line.strip()
                # Look for bullet points or numbered items
                if line.startswith(('-', '•', '*')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
                    # Remove bullet/number prefix
                    cleaned = line.lstrip('-•*0123456789.): ').strip()
                    if cleaned and len(cleaned) > 10:  # Meaningful refinement
                        refinements.append(cleaned)
            return refinements[:5]  # Limit to 5 refinements
    
    def _extract_top_sources(self, patterns: List[MemoryEntry]) -> List[str]:
        """
        Extract top-performing API sources from successful patterns.
        
        Requirements: 3.5 - Increase priority for API sources with high relevance
        
        Args:
            patterns: List of successful memory entries
            
        Returns:
            List[str]: Prioritized API source identifiers
        """
        # Count source usage weighted by relevance
        source_scores = defaultdict(float)
        source_counts = defaultdict(int)
        
        for pattern in patterns:
            for source in pattern.api_sources:
                source_scores[source] += pattern.relevance_score
                source_counts[source] += 1
        
        # Calculate average relevance per source
        source_avg = {
            source: source_scores[source] / source_counts[source]
            for source in source_scores
        }
        
        # Sort by average relevance
        sorted_sources = sorted(
            source_avg.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top sources
        return [source for source, _ in sorted_sources[:5]]
    
    def _calculate_confidence(self, patterns: List[MemoryEntry]) -> float:
        """
        Calculate confidence in refinement based on pattern quality.
        
        Args:
            patterns: List of successful patterns
            
        Returns:
            float: Confidence score (0.0-1.0)
        """
        if not patterns:
            return 0.5
        
        # Factors:
        # 1. Average relevance of patterns
        avg_relevance = np.mean([p.relevance_score for p in patterns])
        
        # 2. Average similarity to current query
        avg_similarity = np.mean([p.similarity_score for p in patterns])
        
        # 3. Number of patterns (more = higher confidence, up to a point)
        pattern_count_factor = min(len(patterns) / 5.0, 1.0)
        
        # Weighted combination
        confidence = (
            avg_relevance * 0.5 +
            avg_similarity * 0.3 +
            pattern_count_factor * 0.2
        )
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    async def adjust_confidence_threshold(
        self,
        recent_feedback: List[FeedbackEntry]
    ) -> float:
        """
        Dynamically adjust confidence threshold based on feedback patterns.
        
        Requirements:
        - 3.3: Adjust Confidence_Threshold values based on feedback patterns
        - 3.4: Analyze which API sources contributed poor results
        
        Args:
            recent_feedback: Recent feedback entries (last 50 queries)
            
        Returns:
            float: New confidence threshold
        """
        try:
            if len(recent_feedback) < 10:
                logger.info(
                    "insufficient_feedback_for_adjustment",
                    feedback_count=len(recent_feedback)
                )
                return self.confidence_threshold
            
            logger.info(
                "adjusting_confidence_threshold",
                current_threshold=self.confidence_threshold,
                feedback_count=len(recent_feedback)
            )
            
            # Calculate false positive rate
            # False positive = high confidence but low relevance
            false_positives = sum(
                1 for f in recent_feedback
                if f.confidence > self.confidence_threshold and f.relevance_score < 0.5
            )
            
            fp_rate = false_positives / len(recent_feedback)
            
            # Calculate false negative rate
            # False negative = low confidence but high relevance
            false_negatives = sum(
                1 for f in recent_feedback
                if f.confidence <= self.confidence_threshold and f.relevance_score >= 0.7
            )
            
            fn_rate = false_negatives / len(recent_feedback)
            
            # Adjust threshold based on error rates
            old_threshold = self.confidence_threshold
            
            if fp_rate > 0.2:  # Too many false positives
                # Increase threshold to be more conservative
                self.confidence_threshold += self.learning_rate
                adjustment_reason = f"high false positive rate ({fp_rate:.2%})"
            elif fn_rate > 0.2:  # Too many false negatives
                # Decrease threshold to be more aggressive
                self.confidence_threshold -= self.learning_rate
                adjustment_reason = f"high false negative rate ({fn_rate:.2%})"
            elif fp_rate < 0.05 and fn_rate < 0.05:  # Very good performance
                # Slightly decrease threshold to capture more results
                self.confidence_threshold -= self.learning_rate * 0.5
                adjustment_reason = "excellent performance, being more aggressive"
            else:
                adjustment_reason = "no adjustment needed"
            
            # Clamp threshold between 0.3 and 0.9
            self.confidence_threshold = max(0.3, min(0.9, self.confidence_threshold))
            
            logger.info(
                "confidence_threshold_adjusted",
                old_threshold=old_threshold,
                new_threshold=self.confidence_threshold,
                fp_rate=fp_rate,
                fn_rate=fn_rate,
                sample_size=len(recent_feedback),
                reason=adjustment_reason
            )
            
            return self.confidence_threshold
            
        except Exception as e:
            logger.error("threshold_adjustment_error", error=str(e))
            return self.confidence_threshold
    
    async def analyze_source_performance(
        self,
        lookback_queries: int = 50,
        use_cache: bool = True
    ) -> Dict[str, SourceMetrics]:
        """
        Analyze which API sources perform best over recent queries.
        
        Requirements:
        - 3.4: Analyze which API sources contributed poor results
        - 3.5: Increase priority for API sources with high relevance
        - 4.4: Deprioritize sources that consistently fail
        
        Args:
            lookback_queries: Number of recent queries to analyze
            use_cache: Whether to use cached metrics if available
            
        Returns:
            Dict[str, SourceMetrics]: Metrics by API source ID
        """
        try:
            # Check cache
            import time
            current_time = time.time()
            if use_cache and self._source_metrics_cache and (current_time - self._cache_timestamp) < self._cache_ttl:
                logger.info("using_cached_source_metrics")
                return self._source_metrics_cache
            
            logger.info(
                "analyzing_source_performance",
                lookback_queries=lookback_queries
            )
            
            # Get recent memories
            recent = await self.memory_store.get_recent(limit=lookback_queries)
            
            if not recent:
                logger.warning("no_recent_memories_for_analysis")
                return {}
            
            # Aggregate statistics by source
            source_stats = defaultdict(lambda: {
                "total": 0,
                "high_relevance": 0,
                "scores": [],
                "name": "Unknown"
            })
            
            for memory in recent:
                for source in memory.api_sources:
                    source_stats[source]["total"] += 1
                    source_stats[source]["scores"].append(memory.relevance_score)
                    if memory.relevance_score >= 0.7:
                        source_stats[source]["high_relevance"] += 1
            
            # Calculate metrics for each source
            metrics = {}
            for source_id, stats in source_stats.items():
                if stats["total"] == 0:
                    continue
                
                success_rate = stats["high_relevance"] / stats["total"]
                avg_relevance = np.mean(stats["scores"])
                priority_score = self._calculate_priority(stats)
                
                metrics[source_id] = SourceMetrics(
                    api_id=source_id,
                    api_name=stats["name"],
                    total_uses=stats["total"],
                    success_rate=success_rate,
                    avg_relevance=float(avg_relevance),
                    priority_score=priority_score
                )
            
            # Update cache
            self._source_metrics_cache = metrics
            self._cache_timestamp = current_time
            
            logger.info(
                "source_performance_analyzed",
                sources_count=len(metrics),
                lookback_queries=lookback_queries
            )
            
            return metrics
            
        except Exception as e:
            logger.error("source_analysis_error", error=str(e))
            return {}
    
    def _calculate_priority(self, stats: Dict[str, Any]) -> float:
        """
        Calculate priority score for an API source.
        
        Requirements: 4.4 - Deprioritize sources that consistently fail
        
        Priority is based on:
        - Success rate (high relevance results)
        - Average relevance score
        - Usage confidence (more usage = more confidence in metrics)
        
        Args:
            stats: Statistics dictionary for a source
            
        Returns:
            float: Priority score (0.0-1.0)
        """
        if stats["total"] == 0:
            return 0.5  # Default for unused sources
        
        # Success rate (percentage of high-relevance results)
        success_rate = stats["high_relevance"] / stats["total"]
        
        # Average relevance score
        avg_score = np.mean(stats["scores"])
        
        # Usage weight (more usage = more confidence, up to 10 uses)
        usage_weight = min(stats["total"] / 10.0, 1.0)
        
        # Weighted combination
        # Success rate is most important, then avg score, then usage confidence
        priority = (
            success_rate * 0.5 +
            avg_score * 0.3 +
            usage_weight * 0.2
        )
        
        return float(np.clip(priority, 0.0, 1.0))
    
    def get_confidence_threshold(self) -> float:
        """
        Get current confidence threshold.
        
        Returns:
            float: Current confidence threshold
        """
        return self.confidence_threshold
    
    def get_learning_rate(self) -> float:
        """
        Get current learning rate.
        
        Returns:
            float: Current learning rate
        """
        return self.learning_rate
    
    async def get_learning_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the learning engine's performance.
        
        Returns:
            Dict[str, Any]: Learning metrics
        """
        try:
            # Get source performance metrics
            source_metrics = await self.analyze_source_performance()
            
            # Calculate aggregate metrics
            if source_metrics:
                avg_priority = np.mean([m.priority_score for m in source_metrics.values()])
                top_sources = sorted(
                    source_metrics.values(),
                    key=lambda m: m.priority_score,
                    reverse=True
                )[:5]
            else:
                avg_priority = 0.5
                top_sources = []
            
            return {
                "confidence_threshold": self.confidence_threshold,
                "learning_rate": self.learning_rate,
                "sources_tracked": len(source_metrics),
                "avg_source_priority": float(avg_priority),
                "top_sources": [
                    {
                        "api_id": s.api_id,
                        "priority_score": s.priority_score,
                        "success_rate": s.success_rate,
                        "total_uses": s.total_uses
                    }
                    for s in top_sources
                ]
            }
        except Exception as e:
            logger.error("get_learning_metrics_error", error=str(e))
            return {
                "confidence_threshold": self.confidence_threshold,
                "learning_rate": self.learning_rate,
                "sources_tracked": 0,
                "avg_source_priority": 0.5,
                "top_sources": []
            }
