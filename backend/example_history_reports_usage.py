"""
Example usage of history and reports endpoints

This script demonstrates how to use the new history and reports endpoints
to retrieve past queries and generated reports.

Requirements: 12.3, 12.5
"""
import requests
import json
from datetime import datetime


# Base URL for the API
BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def get_history(limit=10, offset=0, min_relevance=0.0):
    """
    Get query history with pagination.
    
    Args:
        limit: Maximum number of queries to return
        offset: Number of queries to skip
        min_relevance: Minimum relevance score filter
    """
    print_section("GET QUERY HISTORY")
    
    url = f"{BASE_URL}/api/research/history"
    params = {
        "limit": limit,
        "offset": offset,
        "min_relevance": min_relevance
    }
    
    print(f"Request: GET {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Total Queries: {data['total']}")
        print(f"Returned: {len(data['queries'])} queries")
        print(f"Limit: {data['limit']}, Offset: {data['offset']}")
        
        if data['queries']:
            print("\nRecent Queries:")
            for i, query in enumerate(data['queries'][:5], 1):  # Show first 5
                timestamp = datetime.fromtimestamp(query['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n{i}. {query['query'][:60]}...")
                print(f"   Query ID: {query['query_id']}")
                print(f"   Timestamp: {timestamp}")
                print(f"   Relevance: {query['relevance_score']:.2f}")
                print(f"   Confidence: {query['confidence_score']:.2f}")
                print(f"   Sources: {query['sources_count']}")
                if query.get('session_id'):
                    print(f"   Session: {query['session_id']}")
        else:
            print("\nNo queries found in history.")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def list_reports(limit=10):
    """
    List generated reports.
    
    Args:
        limit: Maximum number of reports to return
    """
    print_section("LIST GENERATED REPORTS")
    
    url = f"{BASE_URL}/api/reports"
    params = {"limit": limit}
    
    print(f"Request: GET {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Total Reports: {data['total']}")
        print(f"Returned: {len(data['reports'])} reports")
        
        if data['reports']:
            print("\nAvailable Reports:")
            for i, report in enumerate(data['reports'], 1):
                print(f"\n{i}. {report['query'][:60]}...")
                print(f"   Report ID: {report['report_id']}")
                print(f"   Filename: {report['filename']}")
                print(f"   Timestamp: {report['timestamp']}")
                print(f"   Confidence: {report['confidence_score']:.2f}")
                print(f"   Size: {report['file_size_bytes']:,} bytes")
        else:
            print("\nNo reports found.")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def get_report(report_id):
    """
    Get a specific report by ID.
    
    Args:
        report_id: Report identifier (format: report_YYYY-MM-DD_HH-MM-SS)
    """
    print_section(f"GET REPORT: {report_id}")
    
    url = f"{BASE_URL}/api/reports/{report_id}"
    
    print(f"Request: GET {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Report ID: {data['report_id']}")
        print(f"Filename: {data['filename']}")
        
        # Print metadata
        metadata = data['metadata']
        print(f"\nMetadata:")
        print(f"  Query: {metadata['query']}")
        print(f"  Timestamp: {metadata['timestamp']}")
        print(f"  Confidence: {metadata['confidence_score']:.2f}")
        print(f"  Size: {metadata['file_size_bytes']:,} bytes")
        
        # Print first 500 characters of content
        content = data['content']
        print(f"\nContent Preview (first 500 chars):")
        print("-" * 60)
        print(content[:500])
        if len(content) > 500:
            print("...")
        print("-" * 60)
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def demonstrate_pagination():
    """Demonstrate pagination with history endpoint"""
    print_section("PAGINATION DEMONSTRATION")
    
    print("Fetching first page (limit=5, offset=0)...")
    page1 = get_history(limit=5, offset=0)
    
    if page1 and page1['total'] > 5:
        print("\n" + "-" * 60)
        print("\nFetching second page (limit=5, offset=5)...")
        page2 = get_history(limit=5, offset=5)


def demonstrate_filtering():
    """Demonstrate filtering with history endpoint"""
    print_section("FILTERING DEMONSTRATION")
    
    print("Fetching high-quality queries (min_relevance=0.7)...")
    high_quality = get_history(limit=10, min_relevance=0.7)
    
    if high_quality:
        print(f"\nFound {len(high_quality['queries'])} high-quality queries")


def main():
    """Main demonstration function"""
    print("\n" + "=" * 60)
    print("  HISTORY AND REPORTS ENDPOINTS DEMONSTRATION")
    print("=" * 60)
    print("\nThis script demonstrates the new endpoints:")
    print("  - GET /api/research/history (with pagination)")
    print("  - GET /api/reports (list reports)")
    print("  - GET /api/reports/{report_id} (get specific report)")
    print("\nMake sure the API server is running on http://localhost:8000")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("\n✓ API server is running")
        else:
            print("\n✗ API server returned unexpected status")
            return
    except requests.exceptions.RequestException:
        print("\n✗ API server is not running")
        print("Please start the server with: uvicorn main:app --reload")
        return
    
    # Demonstrate history endpoint
    history_data = get_history(limit=10)
    
    # Demonstrate pagination
    if history_data and history_data['total'] > 5:
        demonstrate_pagination()
    
    # Demonstrate filtering
    demonstrate_filtering()
    
    # Demonstrate reports list
    reports_data = list_reports(limit=10)
    
    # Demonstrate getting specific report
    if reports_data and reports_data['reports']:
        # Get the first report
        first_report_id = reports_data['reports'][0]['report_id']
        get_report(first_report_id)
    
    print_section("DEMONSTRATION COMPLETE")
    print("All endpoints are working correctly!")
    print("\nYou can now use these endpoints to:")
    print("  - Browse query history with pagination")
    print("  - Filter queries by relevance score")
    print("  - List all generated reports")
    print("  - Retrieve specific report content")


if __name__ == "__main__":
    main()
