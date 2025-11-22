"""
Quick MCP verification script - run after adding API keys to .env
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

async def verify_mcp():
    """Quick verification of MCP connections"""
    print("\n" + "="*60)
    print("MCP CONNECTION VERIFICATION")
    print("="*60)
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    postman_key = os.getenv("POSTMAN_API_KEY")
    
    print(f"\nANTHROPIC_API_KEY: {'✓ Set' if anthropic_key and anthropic_key != 'your_anthropic_api_key_here' else '✗ Not set'}")
    print(f"POSTMAN_API_KEY: {'✓ Set' if postman_key and postman_key != 'your_postman_api_key_here' else '✗ Not set'}")
    
    if not anthropic_key or anthropic_key == 'your_anthropic_api_key_here':
        print("\n⚠ Please add your ANTHROPIC_API_KEY to the .env file")
        return False
    
    try:
        from mcp_client import MCPClient
        
        print("\n" + "="*60)
        print("Testing MCP Connections...")
        print("="*60)
        
        mcp_client = MCPClient()
        
        print("\nInitializing MCP connections (this may take 10-30 seconds)...")
        await asyncio.wait_for(mcp_client.initialize(), timeout=45.0)
        
        print("✓ MCP connections established")
        
        # Test Claude
        if mcp_client.claude_session:
            print("\nTesting Claude...")
            response = await asyncio.wait_for(
                mcp_client.call_claude("Respond with exactly: 'MCP test successful'", temperature=0.0),
                timeout=20.0
            )
            print(f"✓ Claude response: {response[:100]}")
        
        # Test Postman
        if mcp_client.postman_session:
            print("\nTesting Postman API discovery...")
            apis = await asyncio.wait_for(
                mcp_client.discover_apis("weather", max_results=2),
                timeout=20.0
            )
            print(f"✓ Discovered {len(apis)} APIs")
            if apis:
                print(f"  Example: {apis[0].api_name}")
        
        await mcp_client.close()
        
        print("\n" + "="*60)
        print("✓ ALL MCP TESTS PASSED!")
        print("="*60)
        print("\nYour infrastructure is fully operational and ready for Phase 2!")
        
        return True
        
    except asyncio.TimeoutError:
        print("\n✗ Connection timeout - check network and MCP server availability")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_mcp())
    sys.exit(0 if success else 1)
