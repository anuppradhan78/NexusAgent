"""
Example usage of the metrics endpoint

This script demonstrates how to query and interpret the metrics endpoint
to monitor the Adaptive Research Agent's self-improvement.

Requirements: 12.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""
import requests
import json
from datetime import datetime


def get_metrics(base_url: str = "http://localhost:8000") -> dict:
    """
    Fetch current metrics from the agent
    
    Args:
        base_url: Base URL of the agent API
        
    Returns:
        dict: Metrics data
    """
    response = requests.get(f"{base_url}/api/metrics")
    response.raise_for_status()
    return response.json()


def print_metrics_summary(metrics: dict):
    """
    Print a human-readable summary of metrics
    
    Args:
        metrics: Metrics dictionary from API
    """
    print("=" * 60)
    print("ADAPTIVE RESEARCH AGENT - METRICS SUMMARY")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Overall Statistics
    print("📊 OVERALL STATISTICS")
    print("-" * 60)
    print(f"Total Queries Processed: {metrics['total_queries']}")
    print(f"Average Relevance Score: {metrics['avg_relevance_score']:.2%}")
    print(f"Average Confidence Score: {metrics['avg_confidence_score']:.2%}")
    print(f"Current Confidence Threshold: {metrics['confidence_threshold']:.2%}")
    print()
    
    # Learning Progress
    print("📈 LEARNING PROGRESS")
    print("-" * 60)
    trend = metrics['improvement_trend']
    if trend > 0.05:
        status = "🟢 IMPROVING"
    elif trend < -0.05:
        status = "🔴 DECLINING"
    else:
        status = "🟡 STABLE"
    
    print(f"Improvement Trend: {trend:+.3f} {status}")
    print(f"  (Positive = improving, Negative = declining)")
    print()
    
    # Activity
    print("⏰ RECENT ACTIVITY")
    print("-" * 60)
    print(f"Queries in Last Hour: {metrics['queries_last_hour']}")
    print(f"Queries in Last Day: {metrics['queries_last_day']}")
    print()
    
    # Top Sources
    print("🏆 TOP PERFORMING API SOURCES")
    print("-" * 60)
    if metrics['top_sources']:
        for i, source in enumerate(metrics['top_sources'][:5], 1):
            print(f"{i}. {source['api_name']} ({source['api_id']})")
            print(f"   Priority Score: {source['priority_score']:.2%}")
            print(f"   Success Rate: {source['success_rate']:.2%}")
            print(f"   Avg Relevance: {source['avg_relevance']:.2%}")
            print(f"   Total Uses: {source['total_uses']}")
            if source['avg_response_time_ms'] > 0:
                print(f"   Avg Response Time: {source['avg_response_time_ms']:.0f}ms")
            print()
    else:
        print("No source data available yet")
        print()
    
    # Memory Statistics
    print("💾 MEMORY STATISTICS")
    print("-" * 60)
    mem_stats = metrics['memory_stats']
    print(f"Total Memories: {mem_stats['total_memories']}")
    print(f"Average Relevance: {mem_stats['avg_relevance']:.2%}")
    print(f"High Quality Memories: {mem_stats['high_quality_memories']}")
    print(f"Memory Size: {mem_stats['memory_size_bytes'] / 1024 / 1024:.2f} MB")
    print()
    
    print("=" * 60)


def analyze_improvement(metrics: dict):
    """
    Analyze and provide recommendations based on metrics
    
    Args:
        metrics: Metrics dictionary from API
    """
    print("\n🔍 ANALYSIS & RECOMMENDATIONS")
    print("-" * 60)
    
    recommendations = []
    
    # Check improvement trend
    if metrics['improvement_trend'] < -0.1:
        recommendations.append(
            "⚠️  Agent performance is declining. Consider:\n"
            "   - Reviewing recent feedback patterns\n"
            "   - Checking if API sources are still reliable\n"
            "   - Adjusting confidence threshold"
        )
    elif metrics['improvement_trend'] > 0.1:
        recommendations.append(
            "✅ Agent is improving well! Continue current approach."
        )
    
    # Check average relevance
    if metrics['avg_relevance_score'] < 0.6:
        recommendations.append(
            "⚠️  Low average relevance score. Consider:\n"
            "   - Providing more feedback on queries\n"
            "   - Reviewing API source selection\n"
            "   - Refining query processing logic"
        )
    elif metrics['avg_relevance_score'] > 0.8:
        recommendations.append(
            "✅ Excellent relevance scores! Agent is performing well."
        )
    
    # Check confidence threshold
    if metrics['confidence_threshold'] > 0.8:
        recommendations.append(
            "ℹ️  High confidence threshold may be filtering too aggressively.\n"
            "   Consider providing positive feedback to lower threshold."
        )
    elif metrics['confidence_threshold'] < 0.4:
        recommendations.append(
            "ℹ️  Low confidence threshold may allow low-quality results.\n"
            "   Consider providing negative feedback to raise threshold."
        )
    
    # Check memory usage
    mem_stats = metrics['memory_stats']
    if mem_stats['total_memories'] > 0:
        quality_ratio = mem_stats['high_quality_memories'] / mem_stats['total_memories']
        if quality_ratio < 0.5:
            recommendations.append(
                "⚠️  Less than 50% of memories are high quality.\n"
                "   Agent may need more positive feedback to learn better patterns."
            )
    
    # Check activity
    if metrics['total_queries'] < 10:
        recommendations.append(
            "ℹ️  Limited data available. Agent needs more queries to learn effectively."
        )
    
    if recommendations:
        for rec in recommendations:
            print(rec)
            print()
    else:
        print("✅ No issues detected. Agent is operating normally.")
        print()


def compare_metrics(old_metrics: dict, new_metrics: dict):
    """
    Compare two metric snapshots to show changes
    
    Args:
        old_metrics: Previous metrics
        new_metrics: Current metrics
    """
    print("\n📊 METRICS COMPARISON")
    print("-" * 60)
    
    # Calculate changes
    query_change = new_metrics['total_queries'] - old_metrics['total_queries']
    relevance_change = new_metrics['avg_relevance_score'] - old_metrics['avg_relevance_score']
    trend_change = new_metrics['improvement_trend'] - old_metrics['improvement_trend']
    
    print(f"New Queries: {query_change:+d}")
    print(f"Relevance Change: {relevance_change:+.3f}")
    print(f"Trend Change: {trend_change:+.3f}")
    print()


def main():
    """Main example function"""
    try:
        print("Fetching metrics from Adaptive Research Agent...")
        print()
        
        # Get metrics
        metrics = get_metrics()
        
        # Print summary
        print_metrics_summary(metrics)
        
        # Analyze and provide recommendations
        analyze_improvement(metrics)
        
        # Save metrics to file for historical tracking
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_snapshot_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"💾 Metrics saved to: {filename}")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to agent API")
        print("   Make sure the agent is running on http://localhost:8000")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error: API returned error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
