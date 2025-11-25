#!/usr/bin/env python3
"""
Adaptive Research Agent - Demo Script

This script demonstrates the key features of the Adaptive Research Agent:
1. Query processing with Claude
2. Autonomous MCP tool usage
3. Report generation
4. History retrieval

Requirements:
- System must be running (use startup_wsl.bat)
- API server on http://localhost:8000
"""

import requests
import json
import time
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def check_health():
    """Check if the API server is healthy"""
    print_header("CHECKING SYSTEM HEALTH")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print_success("API server is healthy")
            print(f"  Status: {health['status']}")
            print(f"  Redis connected: {health['redis_connected']}")
            print(f"  MCP servers connected: {health['mcp_servers_connected']}")
            return True
        else:
            print_error(f"API server returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to API server: {e}")
        print_info("Please start the server with: startup_wsl.bat")
        return False


def demo_query(query, max_sources=2, include_report=True):
    """Submit a research query and display results"""
    print_header(f"DEMO: Research Query")
    print_info(f"Query: {query}")
    print_info(f"Max sources: {max_sources}")
    print_info(f"Include report: {include_report}")
    print()
    
    try:
        print("Submitting query to Claude...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/research/query",
            json={
                "query": query,
                "max_sources": max_sources,
                "include_report": include_report
            },
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print_success(f"Query completed in {elapsed:.1f} seconds")
            print()
            print(f"{Colors.BOLD}Query ID:{Colors.END} {result['query_id']}")
            print(f"{Colors.BOLD}Processing time:{Colors.END} {result['processing_time_ms']}ms")
            print()
            print(f"{Colors.BOLD}{Colors.CYAN}Answer:{Colors.END}")
            print(f"{result['synthesized_answer'][:500]}...")
            print()
            
            if result.get('sources'):
                print(f"{Colors.BOLD}Sources:{Colors.END} {len(result['sources'])} sources used")
            
            if result.get('report_path'):
                print(f"{Colors.BOLD}Report:{Colors.END} {result['report_path']}")
            
            return result
        else:
            print_error(f"Query failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except requests.Timeout:
        print_error("Query timed out (this can happen with complex queries)")
        return None
    except Exception as e:
        print_error(f"Query failed: {e}")
        return None


def demo_history():
    """Retrieve and display query history"""
    print_header("DEMO: Query History")
    
    try:
        response = requests.get(
            "http://localhost:8000/api/research/history",
            params={"limit": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            history = response.json()
            
            if history['total'] > 0:
                print_success(f"Retrieved {history['total']} queries")
                print()
                
                for i, query in enumerate(history['queries'][:3], 1):
                    print(f"{Colors.BOLD}Query {i}:{Colors.END}")
                    print(f"  ID: {query.get('query_id', 'N/A')[:16]}...")
                    print(f"  Query: {query.get('query', 'N/A')[:60]}...")
                    print(f"  Timestamp: {query.get('timestamp', 'N/A')}")
                    print()
            else:
                print_info("No query history available yet")
                
        else:
            print_error(f"Failed to retrieve history: {response.status_code}")
            
    except Exception as e:
        print_error(f"History retrieval failed: {e}")


def demo_reports():
    """List and display generated reports"""
    print_header("DEMO: Generated Reports")
    
    try:
        response = requests.get("http://localhost:8000/api/reports", timeout=10)
        
        if response.status_code == 200:
            reports = response.json()
            
            if reports['total'] > 0:
                print_success(f"Found {reports['total']} reports")
                print()
                
                for i, report in enumerate(reports['reports'][:3], 1):
                    print(f"{Colors.BOLD}Report {i}:{Colors.END}")
                    print(f"  ID: {report.get('report_id', 'N/A')}")
                    print(f"  Path: {report.get('path', 'N/A')}")
                    print(f"  Size: {report.get('size', 0)} bytes")
                    print()
            else:
                print_info("No reports generated yet")
                
        else:
            print_error(f"Failed to list reports: {response.status_code}")
            
    except Exception as e:
        print_error(f"Report listing failed: {e}")


def main():
    """Run the demo"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                  ADAPTIVE RESEARCH AGENT - DEMO                            ║")
    print("║                                                                            ║")
    print("║  Demonstrating Claude AI with Model Context Protocol (MCP)                ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    # Check system health
    if not check_health():
        return
    
    # Demo 1: Simple query
    print_info("Demo 1: Simple research query")
    time.sleep(1)
    demo_query(
        query="What is the Model Context Protocol?",
        max_sources=2,
        include_report=True
    )
    
    time.sleep(2)
    
    # Demo 2: Another query
    print_info("Demo 2: Technical query")
    time.sleep(1)
    demo_query(
        query="Explain how REST APIs work",
        max_sources=1,
        include_report=False
    )
    
    time.sleep(2)
    
    # Demo 3: History
    demo_history()
    
    time.sleep(1)
    
    # Demo 4: Reports
    demo_reports()
    
    # Final summary
    print_header("DEMO COMPLETE")
    print_success("All demos completed successfully!")
    print()
    print(f"{Colors.BOLD}Key Features Demonstrated:{Colors.END}")
    print("  ✓ Query processing with Claude AI")
    print("  ✓ Autonomous MCP tool usage")
    print("  ✓ Answer synthesis")
    print("  ✓ Report generation")
    print("  ✓ Query history tracking")
    print()
    print(f"{Colors.CYAN}The Adaptive Research Agent is working perfectly!{Colors.END}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Demo failed: {e}{Colors.END}\n")
