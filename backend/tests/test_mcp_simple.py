"""
Simple MCP connection test without complex retry logic
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

async def test_anthropic_direct():
    """Test Anthropic MCP connection directly"""
    print("\n" + "="*60)
    print("TESTING ANTHROPIC MCP CONNECTION")
    print("="*60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("✗ ANTHROPIC_API_KEY not set in .env")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...")
    
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        print("\n✓ MCP packages imported successfully")
        
        # Set up server parameters
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@anthropic-ai/mcp-server-anthropic"],
            env={"ANTHROPIC_API_KEY": api_key}
        )
        
        print("\n✓ Server parameters configured")
        print(f"  Command: npx -y @anthropic-ai/mcp-server-anthropic")
        
        print("\nConnecting to Anthropic MCP server...")
        print("(This may take 30-60 seconds on first run to download packages)")
        
        # Connect with timeout
        try:
            async with asyncio.timeout(90):  # 90 second timeout
                async with stdio_client(server_params) as (read_stream, write_stream):
                    print("✓ Stdio streams established")
                    
                    # Create session
                    session = ClientSession(read_stream, write_stream)
                    print("✓ Client session created")
                    
                    # Initialize
                    await session.initialize()
                    print("✓ Session initialized")
                    
                    # List available tools
                    tools_result = await session.list_tools()
                    print(f"\n✓ Connected! Available tools: {len(tools_result.tools)}")
                    
                    if tools_result.tools:
                        print("\nAvailable MCP tools:")
                        for tool in tools_result.tools[:5]:  # Show first 5
                            print(f"  - {tool.name}")
                    
                    print("\n" + "="*60)
                    print("✓ ANTHROPIC MCP CONNECTION SUCCESSFUL!")
                    print("="*60)
                    
                    return True
                    
        except asyncio.TimeoutError:
            print("\n✗ Connection timeout after 90 seconds")
            print("  This might be due to:")
            print("  - Slow network connection")
            print("  - First-time package download")
            print("  - Firewall blocking npx/npm")
            return False
            
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("  Install MCP: pip install mcp")
        return False
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_anthropic_direct())
    sys.exit(0 if success else 1)
