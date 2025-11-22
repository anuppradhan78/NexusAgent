"""
Report Generator for Adaptive Research Agent

This module provides the ReportGenerator class that creates comprehensive
markdown reports from research results.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
import structlog

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from agent_orchestrator import ResearchSynthesis, APIResult, QueryIntent
    from memory_store import MemoryEntry

logger = structlog.get_logger()


@dataclass
class ReportPath:
    """
    Information about a generated report.
    
    Attributes:
        filename: Report filename
        full_path: Full path to report file
        timestamp: Generation timestamp
        report_id: Unique report identifier
    """
    filename: str
    full_path: str
    timestamp: str
    report_id: str


class ReportGeneratorError(Exception):
    """Raised when report generation fails"""
    pass


class ReportGenerator:
    """
    Generate comprehensive markdown reports from research results.
    
    Creates structured reports with:
    - Executive summary
    - Key findings
    - Detailed analysis
    - Source citations
    - Confidence assessment
    - Metadata
    
    Requirements:
    - 6.1: Generate Research_Report documents in markdown format
    - 6.2: Include executive summary, detailed findings, source citations, confidence assessments
    - 6.3: Organize information by topic with clear headings and bullet points
    - 6.4: Highlight key insights and patterns
    - 6.5: Include metadata (timestamp, query parameters, API sources)
    - 6.6: Save reports to configured output directory with timestamped filenames
    """
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize report generator.
        
        Requirements:
        - 6.6: Save to configured output directory
        
        Args:
            output_dir: Directory to save reports (default: ./reports)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "report_generator_initialized",
            output_dir=str(self.output_dir)
        )
    
    async def generate(
        self,
        query: str,
        query_id: str,
        intent: "QueryIntent",
        synthesis: "ResearchSynthesis",
        api_results: List["APIResult"],
        similar_queries: List["MemoryEntry"],
        metadata: Dict[str, Any]
    ) -> ReportPath:
        """
        Generate comprehensive research report.
        
        Requirements:
        - 6.1: Generate markdown format report
        - 6.2: Include all required sections
        - 6.3: Organize with clear headings
        - 6.4: Highlight key insights
        - 6.5: Include metadata
        - 6.6: Save with timestamped filename
        
        Args:
            query: Original research query
            query_id: Unique query identifier
            intent: Parsed query intent
            synthesis: Synthesized research results
            api_results: Raw API results
            similar_queries: Similar past queries from memory
            metadata: Additional metadata (processing time, etc.)
            
        Returns:
            ReportPath: Information about generated report
            
        Raises:
            ReportGeneratorError: If report generation fails
        """
        try:
            # Generate timestamp and filename
            # Requirements: 6.6 - Timestamped filenames
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            report_id = f"report_{timestamp}_{hash(query) % 10000}"
            filename = f"research_report_{timestamp}.md"
            filepath = self.output_dir / filename
            
            logger.info(
                "generating_report",
                query_id=query_id,
                report_id=report_id,
                filename=filename
            )
            
            # Build report content
            # Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
            report_content = self._build_report(
                query=query,
                query_id=query_id,
                intent=intent,
                synthesis=synthesis,
                api_results=api_results,
                similar_queries=similar_queries,
                metadata=metadata,
                timestamp=timestamp,
                report_id=report_id
            )
            
            # Write report to file
            filepath.write_text(report_content, encoding='utf-8')
            
            logger.info(
                "report_generated",
                report_id=report_id,
                path=str(filepath),
                size_bytes=len(report_content)
            )
            
            return ReportPath(
                filename=filename,
                full_path=str(filepath),
                timestamp=timestamp,
                report_id=report_id
            )
            
        except Exception as e:
            logger.error(
                "report_generation_failed",
                query_id=query_id,
                error=str(e)
            )
            raise ReportGeneratorError(f"Failed to generate report: {e}")
    
    def _build_report(
        self,
        query: str,
        query_id: str,
        intent: "QueryIntent",
        synthesis: "ResearchSynthesis",
        api_results: List["APIResult"],
        similar_queries: List["MemoryEntry"],
        metadata: Dict[str, Any],
        timestamp: str,
        report_id: str
    ) -> str:
        """
        Build complete markdown report content.
        
        Requirements:
        - 6.1: Markdown format with structured sections
        - 6.2: Executive summary, findings, sources, confidence
        - 6.3: Clear headings and bullet points
        - 6.4: Highlight key insights
        - 6.5: Include metadata
        
        Args:
            query: Original query
            query_id: Query identifier
            intent: Parsed intent
            synthesis: Synthesized results
            api_results: API results
            similar_queries: Similar past queries
            metadata: Additional metadata
            timestamp: Generation timestamp
            report_id: Report identifier
            
        Returns:
            str: Complete markdown report
        """
        # Build report sections
        header = self._build_header(query, query_id, report_id, timestamp, synthesis, metadata)
        executive_summary = self._build_executive_summary(synthesis)
        key_findings = self._build_key_findings(synthesis)
        detailed_analysis = self._build_detailed_analysis(synthesis)
        sources = self._build_sources_section(synthesis, api_results)
        confidence = self._build_confidence_assessment(synthesis)
        insights = self._build_insights_section(synthesis, intent)
        related_research = self._build_related_research(similar_queries)
        metadata_section = self._build_metadata_section(intent, api_results, similar_queries, metadata)
        footer = self._build_footer()
        
        # Combine all sections
        # Requirements: 6.3 - Organized with clear headings
        report = f"""{header}

{executive_summary}

{key_findings}

{detailed_analysis}

{sources}

{confidence}

{insights}

{related_research}

{metadata_section}

{footer}"""
        
        return report

    
    def _build_header(
        self,
        query: str,
        query_id: str,
        report_id: str,
        timestamp: str,
        synthesis: "ResearchSynthesis",
        metadata: Dict[str, Any]
    ) -> str:
        """
        Build report header with title and key information.
        
        Requirements:
        - 6.5: Include metadata (timestamp, query parameters)
        
        Args:
            query: Original query
            query_id: Query identifier
            report_id: Report identifier
            timestamp: Generation timestamp
            synthesis: Synthesized results
            metadata: Additional metadata
            
        Returns:
            str: Markdown header section
        """
        formatted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# Research Report: {query}

**Generated:** {formatted_timestamp}  
**Report ID:** {report_id}  
**Query ID:** {query_id}  
**Confidence Score:** {synthesis.confidence_score:.2f}  
**Processing Time:** {metadata.get('processing_time_ms', 0):.0f}ms

---"""
    
    def _build_executive_summary(self, synthesis: "ResearchSynthesis") -> str:
        """
        Build executive summary section.
        
        Requirements:
        - 6.2: Include executive summary
        
        Args:
            synthesis: Synthesized results
            
        Returns:
            str: Markdown executive summary section
        """
        return f"""## Executive Summary

{synthesis.summary}"""
    
    def _build_key_findings(self, synthesis: "ResearchSynthesis") -> str:
        """
        Build key findings section.
        
        Requirements:
        - 6.2: Include detailed findings
        - 6.3: Use bullet points
        
        Args:
            synthesis: Synthesized results
            
        Returns:
            str: Markdown key findings section
        """
        if not synthesis.findings:
            return """## Key Findings

No specific findings identified."""
        
        findings_list = "\n".join([f"- {finding}" for finding in synthesis.findings])
        
        return f"""## Key Findings

{findings_list}"""
    
    def _build_detailed_analysis(self, synthesis: "ResearchSynthesis") -> str:
        """
        Build detailed analysis section.
        
        Requirements:
        - 6.2: Include detailed findings
        - 6.3: Organize by topic
        
        Args:
            synthesis: Synthesized results
            
        Returns:
            str: Markdown detailed analysis section
        """
        return f"""## Detailed Analysis

{synthesis.detailed_analysis}"""
    
    def _build_sources_section(
        self,
        synthesis: "ResearchSynthesis",
        api_results: List["APIResult"]
    ) -> str:
        """
        Build sources section with citations.
        
        Requirements:
        - 6.2: Include source citations
        - 6.3: Format with clear structure
        
        Args:
            synthesis: Synthesized results
            api_results: Raw API results
            
        Returns:
            str: Markdown sources section
        """
        if not synthesis.source_details:
            return """## Sources

No sources available."""
        
        sources_text = ["## Sources\n"]
        
        for i, source in enumerate(synthesis.source_details, 1):
            # Find corresponding API result for additional details
            api_result = next(
                (r for r in api_results if r.api_id == source.api_id),
                None
            )
            
            sources_text.append(f"### {i}. {source.api_name}")
            sources_text.append(f"- **API ID:** {source.api_id}")
            sources_text.append(f"- **Endpoint:** {source.endpoint}")
            sources_text.append(f"- **Verified:** {'Yes' if source.verified else 'No'}")
            sources_text.append(f"- **Priority Score:** {source.priority_score:.2f}")
            
            if api_result:
                sources_text.append(f"- **Status:** {'Success' if api_result.success else 'Failed'}")
                sources_text.append(f"- **Response Time:** {api_result.response_time_ms:.0f}ms")
                
                if not api_result.success and api_result.error:
                    sources_text.append(f"- **Error:** {api_result.error}")
            
            # Add confidence for this source if available
            if source.api_id in synthesis.confidence_breakdown:
                confidence = synthesis.confidence_breakdown[source.api_id]
                sources_text.append(f"- **Confidence:** {confidence:.2f}")
            
            sources_text.append("")  # Empty line between sources
        
        return "\n".join(sources_text)
    
    def _build_confidence_assessment(self, synthesis: "ResearchSynthesis") -> str:
        """
        Build confidence assessment section.
        
        Requirements:
        - 6.2: Include confidence assessments
        - 6.4: Highlight key insights
        
        Args:
            synthesis: Synthesized results
            
        Returns:
            str: Markdown confidence assessment section
        """
        confidence_text = [f"""## Confidence Assessment

**Overall Confidence:** {synthesis.confidence_score:.2f}

"""]
        
        if synthesis.confidence_breakdown:
            confidence_text.append("### Confidence by Source\n")
            
            # Sort by confidence (highest first)
            sorted_sources = sorted(
                synthesis.confidence_breakdown.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for source_id, confidence in sorted_sources:
                # Find source name
                source_name = source_id
                for source in synthesis.source_details:
                    if source.api_id == source_id:
                        source_name = source.api_name
                        break
                
                # Add visual indicator
                indicator = "🟢" if confidence >= 0.7 else "🟡" if confidence >= 0.5 else "🔴"
                confidence_text.append(f"- {indicator} **{source_name}:** {confidence:.2f}")
            
            confidence_text.append("")
        
        # Add interpretation
        if synthesis.confidence_score >= 0.8:
            interpretation = "High confidence - Results are well-supported by multiple reliable sources."
        elif synthesis.confidence_score >= 0.6:
            interpretation = "Moderate confidence - Results are reasonably supported but may benefit from additional verification."
        elif synthesis.confidence_score >= 0.4:
            interpretation = "Low confidence - Results should be verified with additional sources."
        else:
            interpretation = "Very low confidence - Results are preliminary and require significant additional research."
        
        confidence_text.append(f"\n**Interpretation:** {interpretation}")
        
        return "\n".join(confidence_text)
    
    def _build_insights_section(
        self,
        synthesis: "ResearchSynthesis",
        intent: "QueryIntent"
    ) -> str:
        """
        Build insights and patterns section.
        
        Requirements:
        - 6.4: Highlight key insights and patterns
        
        Args:
            synthesis: Synthesized results
            intent: Query intent
            
        Returns:
            str: Markdown insights section
        """
        insights_text = ["## Key Insights & Patterns\n"]
        
        # Analyze findings for patterns
        if len(synthesis.findings) >= 3:
            insights_text.append("### Identified Patterns\n")
            insights_text.append(f"- Research covered {len(intent.key_topics)} main topic areas")
            insights_text.append(f"- Information synthesized from {len(synthesis.sources)} independent sources")
            
            if synthesis.confidence_score >= 0.7:
                insights_text.append("- High agreement across sources indicates reliable information")
            elif synthesis.confidence_score < 0.5:
                insights_text.append("- Low confidence suggests conflicting information or limited data")
            
            insights_text.append("")
        
        # Add topic coverage
        if intent.key_topics:
            insights_text.append("### Topics Covered\n")
            for topic in intent.key_topics:
                insights_text.append(f"- {topic}")
            insights_text.append("")
        
        return "\n".join(insights_text)
    
    def _build_related_research(self, similar_queries: List["MemoryEntry"]) -> str:
        """
        Build related research section from similar past queries.
        
        Requirements:
        - 6.4: Highlight patterns from past research
        
        Args:
            similar_queries: Similar past queries from memory
            
        Returns:
            str: Markdown related research section
        """
        if not similar_queries:
            return """## Related Research

No similar past research found."""
        
        related_text = ["## Related Research\n"]
        related_text.append("Similar queries from memory that informed this research:\n")
        
        for i, memory in enumerate(similar_queries[:5], 1):  # Limit to top 5
            related_text.append(f"### {i}. {memory.query}")
            related_text.append(f"- **Similarity:** {memory.similarity_score:.2f}")
            related_text.append(f"- **Relevance Score:** {memory.relevance_score:.2f}")
            related_text.append(f"- **Sources Used:** {', '.join(memory.api_sources)}")
            
            # Add summary if available
            if memory.results and isinstance(memory.results, dict):
                summary = memory.results.get("summary", "")
                if summary:
                    # Truncate long summaries
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                    related_text.append(f"- **Summary:** {summary}")
            
            related_text.append("")
        
        return "\n".join(related_text)
    
    def _build_metadata_section(
        self,
        intent: "QueryIntent",
        api_results: List["APIResult"],
        similar_queries: List["MemoryEntry"],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Build metadata section with technical details.
        
        Requirements:
        - 6.5: Include metadata (query parameters, API sources, timestamps)
        
        Args:
            intent: Query intent
            api_results: API results
            similar_queries: Similar queries
            metadata: Additional metadata
            
        Returns:
            str: Markdown metadata section
        """
        successful_apis = [r for r in api_results if r.success]
        failed_apis = [r for r in api_results if not r.success]
        
        metadata_text = ["""## Metadata

### Query Information
"""]
        
        metadata_text.append(f"- **Intent Type:** {intent.intent_type}")
        metadata_text.append(f"- **Key Topics:** {', '.join(intent.key_topics)}")
        metadata_text.append(f"- **Search Terms Used:** {len(intent.search_terms)}")
        
        metadata_text.append("\n### API Sources\n")
        metadata_text.append(f"- **Total APIs Queried:** {len(api_results)}")
        metadata_text.append(f"- **Successful:** {len(successful_apis)}")
        metadata_text.append(f"- **Failed:** {len(failed_apis)}")
        
        if successful_apis:
            api_names = [r.api_name for r in successful_apis]
            metadata_text.append(f"- **APIs Used:** {', '.join(api_names)}")
        
        metadata_text.append("\n### Learning & Memory\n")
        metadata_text.append(f"- **Similar Past Queries Found:** {len(similar_queries)}")
        
        # Add refinement information if available
        if metadata.get('refinement_applied'):
            metadata_text.append(f"- **Query Refinement Applied:** Yes")
            metadata_text.append(f"- **Refinement Confidence:** {metadata.get('refinement_confidence', 0.0):.2f}")
            refinements = metadata.get('refinements', [])
            if refinements:
                metadata_text.append(f"- **Refinements:** {len(refinements)}")
        else:
            metadata_text.append(f"- **Query Refinement Applied:** No")
        
        metadata_text.append("\n### Performance\n")
        metadata_text.append(f"- **Total Processing Time:** {metadata.get('processing_time_ms', 0):.0f}ms")
        
        if successful_apis:
            avg_response_time = sum(r.response_time_ms for r in successful_apis) / len(successful_apis)
            metadata_text.append(f"- **Average API Response Time:** {avg_response_time:.0f}ms")
        
        # Add session info if available
        if metadata.get('session_id'):
            metadata_text.append(f"- **Session ID:** {metadata['session_id']}")
        
        # Add alert info if available
        if 'alert_triggered' in metadata:
            alert_status = "Yes" if metadata['alert_triggered'] else "No"
            metadata_text.append(f"- **Alert Triggered:** {alert_status}")
        
        return "\n".join(metadata_text)
    
    def _build_footer(self) -> str:
        """
        Build report footer.
        
        Returns:
            str: Markdown footer
        """
        return """---

*Generated by Adaptive Research Agent*  
*This report synthesizes information from multiple API sources using AI-powered analysis.*"""
