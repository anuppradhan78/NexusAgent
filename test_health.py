"""
Simple test to check if the server can start without MCP servers
"""
import requests
import time

print("Waiting for server to start...")
time.sleep(10)

try:
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
