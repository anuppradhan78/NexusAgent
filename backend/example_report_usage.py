"""
Example usage of ReportGenerator

This script demonstrates how to use the ReportGenerator to create
comprehensive markdown reports from research results.
"""
import asyncio
from report_generator import ReportGenerator
from agent_orchestrator import ResearchSynthesis, APIResult, QueryIntent
from memory_store import MemoryEntry
from mcp_client import APIEndpoint


async def main():
    """Demonstrate report generation"""
    
    # Initialize report generator
    generator = ReportGenerator(output_dir="./reports")
    
    # Create sample data
    query = "What are the latest developments in quantum computing?"
    query_id = "query_example_001"
    
    # Sample query intent
    intent = QueryIntent(
        original_query=query,
        intent_type="trend_analysis",
        key_topics=["quantum computing", "quantum algorithms", "quantum hardware"],
        search_terms=["quantum computing trends", "quantum breakthroughs", "quantum research"],
        context="User wants to understand recent advances in quantum computing"
    )
    
    # Sample synthesis
    synthesis = ResearchSynthesis(
        summary="Quantum computing is advancing rapidly with breakthroughs in error correction and new quantum algorithms.",
        detailed_analysis="""Recent developments in quantum computing show significant progress across multiple fronts.

Error correction techniques have improved dramatically, with new topological codes showing promise for fault-tolerant quantum computation. Major tech companies and research institutions are racing to achieve quantum advantage in practical applications.

Quantum algorithms for optimization and machine learning are being developed, with potential applications in drug discovery, financial modeling, and cryptography. Hardware improvements include longer coherence times and better qubit connectivity.""",
        findings=[
            "Error correction codes have improved by 40% in the last year",
            "New quantum algorithms show 10x speedup for certain optimization problems",
            "Quantum hardware coherence times have doubled",
            "Major investments from tech companies totaling $5B in 2024",
            "First practical quantum advantage demonstrated in drug discovery"
        ],
        sources=["quantum_news_api", "research_papers_api", "tech_trends_api"],
        source_details=[
            APIEndpoint(
                api_id="quantum_news_api",
                api_name="Quantum Computing News API",
                endpoint="/v1/news/quantum",
                method="GET",
                description="Latest quantum computing news",
                verified=True,
                priority_score=0.9
            ),
            APIEndpoint(
                api_id="research_papers_api",
                api_name="ArXiv Research Papers API",
                endpoint="/v1/papers/quantum",
                method="GET",
                description="Quantum computing research papers",
                verified=True,
                priority_score=0.85
            ),
            APIEndpoint(
                api_id="tech_trends_api",
                api_name="Tech Trends API",
                endpoint="/v1/trends/quantum",
                method="GET",
                description="Technology trends analysis",
                verified=True,
                priority_score=0.75
            )
        ],
        confidence_score=0.88,
        confidence_breakdown={
            "quantum_news_api": 0.92,
            "research_papers_api": 0.90,
            "tech_trends_api": 0.82
        }
    )
    
    # Sample API results
    api_results = [
        APIResult(
            api_id="quantum_news_api",
            api_name="Quantum Computing News API",
            endpoint="/v1/news/quantum",
            data={"articles": ["article1", "article2", "article3"]},
            success=True,
            response_time_ms=180.0
        ),
        APIResult(
            api_id="research_papers_api",
            api_name="ArXiv Research Papers API",
            endpoint="/v1/papers/quantum",
            data={"papers": ["paper1", "paper2"]},
            success=True,
            response_time_ms=320.0
        ),
        APIResult(
            api_id="tech_trends_api",
            api_name="Tech Trends API",
            endpoint="/v1/trends/quantum",
            data={"trends": ["trend1", "trend2"]},
            success=True,
            response_time_ms=250.0
        )
    ]
    
    # Sample similar queries
    similar_queries = [
        MemoryEntry(
            memory_id="mem_001",
            query="Quantum computing breakthroughs 2024",
            results={
                "summary": "Significant progress in quantum error correction and algorithm development"
            },
            relevance_score=0.92,
            api_sources=["quantum_news_api", "research_papers_api"],
            similarity_score=0.87,
            timestamp=1700000000.0
        ),
        MemoryEntry(
            memory_id="mem_002",
            query="Latest quantum hardware improvements",
            results={
                "summary": "Coherence times and qubit connectivity have improved"
            },
            relevance_score=0.85,
            api_sources=["tech_trends_api"],
            similarity_score=0.78,
            timestamp=1699000000.0
        )
    ]
    
    # Metadata
    metadata = {
        "processing_time_ms": 2850.0,
        "session_id": "session_example_001",
        "alert_triggered": True,
        "refinement_applied": True,
        "refinement_confidence": 0.82,
        "refinements": [
            "Added search term: quantum error correction",
            "Prioritized research papers API based on past success"
        ]
    }
    
    # Generate report
    print("Generating research report...")
    report_path = await generator.generate(
        query=query,
        query_id=query_id,
        intent=intent,
        synthesis=synthesis,
        api_results=api_results,
        similar_queries=similar_queries,
        metadata=metadata
    )
    
    print(f"\n✅ Report generated successfully!")
    print(f"📄 Filename: {report_path.filename}")
    print(f"📁 Full path: {report_path.full_path}")
    print(f"🆔 Report ID: {report_path.report_id}")
    print(f"⏰ Timestamp: {report_path.timestamp}")
    
    # Read and display first few lines
    with open(report_path.full_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"\n📋 Report preview (first 20 lines):")
        print("=" * 80)
        for line in lines[:20]:
            print(line.rstrip())
        print("=" * 80)
        print(f"\n... ({len(lines)} total lines)")


if __name__ == "__main__":
    asyncio.run(main())
