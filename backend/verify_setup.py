"""
Setup verification script for Adaptive Research Agent
"""
import os
import sys
from pathlib import Path

def verify_setup():
    """Verify project setup is complete"""
    checks = []
    
    # Check files exist
    required_files = [
        "main.py",
        "requirements.txt",
        "../.env.example",
        "../.gitignore",
        "../mcp.json",
        "../reports"
    ]
    
    print("Verifying project setup...\n")
    
    for file_path in required_files:
        path = Path(file_path)
        exists = path.exists()
        status = "✓" if exists else "✗"
        checks.append(exists)
        print(f"{status} {file_path}")
    
    # Check .env.example content
    env_example = Path("../.env.example")
    if env_example.exists():
        content = env_example.read_text()
        required_vars = [
            "ANTHROPIC_API_KEY",
            "REDIS_URL",
            "POSTMAN_API_KEY",
            "ALERT_CHANNELS",
            "REPORT_OUTPUT_DIR",
            "LEARNING_RATE",
            "CONFIDENCE_THRESHOLD_INITIAL"
        ]
        
        print("\nEnvironment variables in .env.example:")
        for var in required_vars:
            exists = var in content
            status = "✓" if exists else "✗"
            checks.append(exists)
            print(f"{status} {var}")
    
    # Check mcp.json content
    mcp_config = Path("../mcp.json")
    if mcp_config.exists():
        import json
        config = json.loads(mcp_config.read_text())
        
        print("\nMCP servers configured:")
        required_servers = ["anthropic", "postman"]
        for server in required_servers:
            exists = server in config.get("mcpServers", {})
            status = "✓" if exists else "✗"
            checks.append(exists)
            print(f"{status} {server}")
    
    # Summary
    print("\n" + "="*50)
    if all(checks):
        print("✓ All setup checks passed!")
        print("="*50)
        return 0
    else:
        print("✗ Some setup checks failed")
        print("="*50)
        return 1

if __name__ == "__main__":
    sys.exit(verify_setup())
