#!/usr/bin/env python3
"""
Adaptive Research Agent - Comprehensive Demo Script

This script demonstrates the key features of the Adaptive Research Agent:
1. Autonomous query processing with API discovery
2. Learning from feedback
3. Alert generation for critical information
4. Automated report generation
5. Self-improvement metrics over time
6. Scheduled queries
7. Multi-turn conversations

Requirements:
- Redis running on localhost:6379
- API server running on localhost:8000
- Environment variables configured (.env file)
"""

import asyncio
import httpx
import time
from datetime import datetime
from typing import Dict, Any, List
import json


class DemoRunner:
    """Runs comprehensive demo of Adaptive Research Agent features"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.query_ids: List[str] = []
        self.session_id: str = ""
        
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✓ {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"✗ {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ {message}")
    
    async def check_health(self) -> bool:
        """Check if API server is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.print_success("API server is healthy")
                return True
            else:
                self.print_error(f"API server returned status {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Cannot connect to API server: {e}")
            return False
    
    async def demo_query_processing(self):
        """Demo 1: Autonomous query processing"""
        self.print_header("DEMO 1: Autonomous Query Processing")
        
        queries = [
            "What are the latest developments in artificial intelligence?",
            "Tell me about recent advances in quantum computing",
            "What are the current trends in renewable energy?"
        ]
        
        for i, query in enumerate(queries, 1):
            self.print_info(f"Query {i}: {query}")
            
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/research/query",
                    json={
                        "query": query,
                        "max_sources": 3,
                        "include_report": True,
                        "alert_enabled": True
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.query_ids.append(data["query_id"])
                    
                    self.print_success(f"Query processed in {data['processing_time_ms']}ms")
                    print(f"  Query ID: {data['query_id']}")
                    print(f"  Confidence: {data['confidence_score']:.2f}")
                    print(f"  Sources used: {len(data['sources'])}")
                    print(f"  Alert triggered: {data['alert_triggered']}")
                    
                    if data.get('report_path'):
                        print(f"  Report: {data['report_path']}")
                    
                    # Print synthesized answer (truncated)
                    answer = data['synthesized_answer']
                    if len(answer) > 200:
                        answer = answer[:200] + "..."
                    print(f"\n  Answer: {answer}\n")
                    
                    # Show similar past queries if any
                    if data.get('similar_past_queries'):
                        print(f"  Found {len(data['similar_past_queries'])} similar past queries")
                    
                else:
                    self.print_error(f"Query failed with status {response.status_code}")
                    print(f"  Error: {response.text}")
                
                # Small delay between queries
                await asyncio.sleep(2)
                
            except Exception as e:
                self.print_error(f"Query failed: {e}")
    
    async def demo_learning_from_feedback(self):
        """Demo 2: Learning from feedback"""
        self.print_header("DEMO 2: Learning from Feedback")
        
        if not self.query_ids:
            self.print_error("No queries to provide feedback on")
            return
        
        # Provide feedback on processed queries
        feedback_scores = [0.9, 0.85, 0.75]
        
        for query_id, score in zip(self.query_ids[:3], feedback_scores):
            self.print_info(f"Submitting feedback for query {query_id[:8]}...")
            
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/research/feedback",
                    json={
                        "query_id": query_id,
                        "relevance_score": score,
                        "feedback_notes": f"Relevance score: {score}"
                    }
                )
                
                if response.status_code == 200:
                    self.print_success(f"Feedback submitted (score: {score})")
                else:
                    self.print_error(f"Feedback failed with status {response.status_code}")
                    
            except Exception as e:
                self.print_error(f"Feedback submission failed: {e}")
        
        # Show that the agent learns from feedback
        self.print_info("\nSubmitting a similar query to demonstrate learning...")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/research/query",
                json={
                    "query": "What are recent AI breakthroughs?",  # Similar to first query
                    "max_sources": 3,
                    "include_report": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Query processed with learned patterns")
                
                if data.get('similar_past_queries'):
                    print(f"  Agent found {len(data['similar_past_queries'])} similar past queries")
                    print(f"  Using learned patterns to improve results")
                    
                    # Show refinements applied
                    if len(data['similar_past_queries']) > 0:
                        print(f"  Previous relevance scores: ", end="")
                        scores = [q.get('relevance_score', 0) for q in data['similar_past_queries']]
                        print(", ".join([f"{s:.2f}" for s in scores]))
                
        except Exception as e:
            self.print_error(f"Learning demo failed: {e}")
    
    async def demo_alerts(self):
        """Demo 3: Alert generation"""
        self.print_header("DEMO 3: Alert Generation for Critical Information")
        
        # Submit queries that might trigger alerts
        alert_queries = [
            "Breaking news in cybersecurity threats",
            "Critical vulnerabilities discovered in popular software"
        ]
        
        for query in alert_queries:
            self.print_info(f"Query: {query}")
            
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/research/query",
                    json={
                        "query": query,
                        "max_sources": 2,
                        "alert_enabled": True
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data['alert_triggered']:
                        self.print_success("Alert triggered!")
                        print(f"  Alert sent via configured channels")
                    else:
                        self.print_info("No alert triggered (information not critical)")
                        
            except Exception as e:
                self.print_error(f"Alert demo failed: {e}")
            
            await asyncio.sleep(2)
    
    async def demo_reports(self):
        """Demo 4: Automated report generation"""
        self.print_header("DEMO 4: Automated Report Generation")
        
        try:
            # List generated reports
            response = await self.client.get(f"{self.base_url}/api/reports")
            
            if response.status_code == 200:
                reports = response.json()
                
                if reports:
                    self.print_success(f"Found {len(reports)} generated reports")
                    
                    # Show first few reports
                    for i, report in enumerate(reports[:3], 1):
                        print(f"\n  Report {i}:")
                        print(f"    ID: {report.get('report_id', 'N/A')}")
                        print(f"    Query: {report.get('query', 'N/A')[:60]}...")
                        print(f"    Generated: {report.get('timestamp', 'N/A')}")
                        print(f"    Path: {report.get('path', 'N/A')}")
                    
                    # Retrieve a specific report
                    if reports:
                        report_id = reports[0].get('report_id')
                        if report_id:
                            self.print_info(f"\nRetrieving report {report_id}...")
                            
                            report_response = await self.client.get(
                                f"{self.base_url}/api/reports/{report_id}"
                            )
                            
                            if report_response.status_code == 200:
                                report_content = report_response.json()
                                self.print_success("Report retrieved successfully")
                                
                                # Show report structure
                                content = report_content.get('content', '')
                                if content:
                                    lines = content.split('\n')
                                    print(f"  Report has {len(lines)} lines")
                                    print(f"  First few lines:")
                                    for line in lines[:5]:
                                        if line.strip():
                                            print(f"    {line}")
                else:
                    self.print_info("No reports generated yet")
                    
            else:
                self.print_error(f"Failed to list reports: {response.status_code}")
                
        except Exception as e:
            self.print_error(f"Report demo failed: {e}")
    
    async def demo_metrics(self):
        """Demo 5: Self-improvement metrics"""
        self.print_header("DEMO 5: Self-Improvement Metrics Over Time")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/metrics")
            
            if response.status_code == 200:
                metrics = response.json()
                
                self.print_success("Metrics retrieved successfully")
                print(f"\n  System Performance:")
                print(f"    Total queries: {metrics.get('total_queries', 0)}")
                print(f"    Average relevance: {metrics.get('avg_relevance_score', 0):.2f}")
                print(f"    Average confidence: {metrics.get('avg_confidence_score', 0):.2f}")
                print(f"    Improvement trend: {metrics.get('improvement_trend', 0):.3f}")
                
                if metrics.get('improvement_trend', 0) > 0:
                    self.print_success("Agent is improving over time! 📈")
                elif metrics.get('improvement_trend', 0) < 0:
                    self.print_info("Agent performance is declining (needs more feedback)")
                else:
                    self.print_info("Agent performance is stable")
                
                print(f"\n  Learning System:")
                print(f"    Confidence threshold: {metrics.get('confidence_threshold', 0.5):.2f}")
                
                # Show top performing sources
                if metrics.get('top_sources'):
                    print(f"\n  Top Performing API Sources:")
                    for i, source in enumerate(metrics['top_sources'][:5], 1):
                        source_name = source.get('source', 'Unknown')
                        score = source.get('score', 0)
                        print(f"    {i}. {source_name}: {score:.2f}")
                
                # Show memory stats
                if metrics.get('memory_stats'):
                    print(f"\n  Memory Statistics:")
                    mem_stats = metrics['memory_stats']
                    print(f"    Total memories: {mem_stats.get('total_memories', 0)}")
                    print(f"    High quality: {mem_stats.get('high_quality_memories', 0)}")
                    
            else:
                self.print_error(f"Failed to retrieve metrics: {response.status_code}")
                
        except Exception as e:
            self.print_error(f"Metrics demo failed: {e}")
    
    async def demo_scheduled_queries(self):
        """Demo 6: Scheduled recurring queries"""
        self.print_header("DEMO 6: Scheduled Recurring Queries")
        
        self.print_info("Creating a scheduled query...")
        
        try:
            # Create a scheduled query
            response = await self.client.post(
                f"{self.base_url}/api/schedule",
                json={
                    "query": "Daily AI news summary",
                    "schedule": "0 9 * * *",  # Daily at 9 AM
                    "max_sources": 3,
                    "alert_enabled": True
                }
            )
            
            if response.status_code == 200:
                schedule_data = response.json()
                schedule_id = schedule_data.get('schedule_id')
                
                self.print_success(f"Scheduled query created: {schedule_id}")
                print(f"  Query: {schedule_data.get('query')}")
                print(f"  Schedule: {schedule_data.get('schedule')}")
                print(f"  Next run: {schedule_data.get('next_run')}")
                
                # List all schedules
                self.print_info("\nListing all scheduled queries...")
                
                list_response = await self.client.get(f"{self.base_url}/api/schedule")
                
                if list_response.status_code == 200:
                    schedules = list_response.json()
                    self.print_success(f"Found {len(schedules)} scheduled queries")
                    
                    for schedule in schedules:
                        print(f"\n  Schedule ID: {schedule.get('schedule_id')}")
                        print(f"    Query: {schedule.get('query')}")
                        print(f"    Cron: {schedule.get('schedule')}")
                        print(f"    Enabled: {schedule.get('enabled', True)}")
                
            else:
                self.print_error(f"Failed to create schedule: {response.status_code}")
                print(f"  Error: {response.text}")
                
        except Exception as e:
            self.print_error(f"Scheduled queries demo failed: {e}")
    
    async def demo_multi_turn_conversation(self):
        """Demo 7: Multi-turn conversations"""
        self.print_header("DEMO 7: Multi-Turn Conversations")
        
        self.print_info("Starting a multi-turn conversation...")
        
        conversation_queries = [
            "What is machine learning?",
            "Tell me more about neural networks",
            "How do they relate to deep learning?"
        ]
        
        try:
            # Create a session
            session_response = await self.client.post(f"{self.base_url}/api/session")
            
            if session_response.status_code == 200:
                session_data = session_response.json()
                self.session_id = session_data.get('session_id')
                self.print_success(f"Session created: {self.session_id}")
            else:
                self.print_info("Using auto-generated session")
                self.session_id = None
            
            # Process queries in conversation
            for i, query in enumerate(conversation_queries, 1):
                print(f"\n  Turn {i}: {query}")
                
                request_data = {
                    "query": query,
                    "max_sources": 2,
                    "include_report": False
                }
                
                if self.session_id:
                    request_data["session_id"] = self.session_id
                
                response = await self.client.post(
                    f"{self.base_url}/api/research/query",
                    json=request_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.print_success(f"Response received (confidence: {data['confidence_score']:.2f})")
                    
                    # Show context awareness
                    if i > 1 and data.get('similar_past_queries'):
                        print(f"    Agent using context from previous turns")
                    
                    # Print brief answer
                    answer = data['synthesized_answer']
                    if len(answer) > 150:
                        answer = answer[:150] + "..."
                    print(f"    {answer}")
                else:
                    self.print_error(f"Query failed: {response.status_code}")
                
                await asyncio.sleep(1)
            
            # Show conversation history
            if self.session_id:
                self.print_info(f"\nRetrieving conversation history...")
                
                history_response = await self.client.get(
                    f"{self.base_url}/api/session/{self.session_id}/history"
                )
                
                if history_response.status_code == 200:
                    history = history_response.json()
                    self.print_success(f"Conversation has {len(history)} turns")
                    
        except Exception as e:
            self.print_error(f"Multi-turn conversation demo failed: {e}")
    
    async def demo_query_history(self):
        """Demo: Query history retrieval"""
        self.print_header("BONUS: Query History")
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/research/history",
                params={"limit": 5}
            )
            
            if response.status_code == 200:
                history = response.json()
                
                if history:
                    self.print_success(f"Retrieved {len(history)} recent queries")
                    
                    for i, entry in enumerate(history, 1):
                        print(f"\n  Query {i}:")
                        print(f"    ID: {entry.get('query_id', 'N/A')[:8]}...")
                        print(f"    Query: {entry.get('query', 'N/A')[:50]}...")
                        print(f"    Relevance: {entry.get('relevance_score', 0):.2f}")
                        print(f"    Timestamp: {entry.get('timestamp', 'N/A')}")
                else:
                    self.print_info("No query history available")
                    
            else:
                self.print_error(f"Failed to retrieve history: {response.status_code}")
                
        except Exception as e:
            self.print_error(f"History demo failed: {e}")
    
    async def run_all_demos(self):
        """Run all demo scenarios"""
        print("\n" + "="*80)
        print("  ADAPTIVE RESEARCH AGENT - COMPREHENSIVE DEMO")
        print("  Demonstrating Autonomous, Self-Improving AI Research")
        print("="*80)
        
        # Check health first
        if not await self.check_health():
            print("\n⚠️  Please ensure:")
            print("  1. Redis is running (docker run -d -p 6379:6379 redis/redis-stack:latest)")
            print("  2. API server is running (cd backend && python main.py)")
            print("  3. Environment variables are configured (.env file)")
            return
        
        # Run all demos
        await self.demo_query_processing()
        await self.demo_learning_from_feedback()
        await self.demo_alerts()
        await self.demo_reports()
        await self.demo_metrics()
        await self.demo_scheduled_queries()
        await self.demo_multi_turn_conversation()
        await self.demo_query_history()
        
        # Final summary
        self.print_header("DEMO COMPLETE")
        print("Key Features Demonstrated:")
        print("  ✓ Autonomous query processing with API discovery")
        print("  ✓ Learning from feedback and pattern recognition")
        print("  ✓ Alert generation for critical information")
        print("  ✓ Automated report generation")
        print("  ✓ Self-improvement metrics tracking")
        print("  ✓ Scheduled recurring queries")
        print("  ✓ Multi-turn conversations with context")
        print("  ✓ Query history and analytics")
        print("\nThe Adaptive Research Agent is continuously learning and improving!")
        print("Try submitting more queries and feedback to see it get better over time.")
        print("\n" + "="*80 + "\n")


async def main():
    """Main entry point"""
    demo = DemoRunner()
    
    try:
        await demo.run_all_demos()
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())
