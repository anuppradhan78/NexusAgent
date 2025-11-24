"""
MCP Tool Router - Routes tool calls from Claude to appropriate MCP servers
"""
import asyncio
import os
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import structlog

logger = structlog.get_logger()


class MCPToolRouter:
    """Routes tool calls to our custom MCP servers"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.contexts: Dict[str, Any] = {}
        self.tool_registry: Dict[str, str] = {}
        
        # Get absolute paths for MCP servers
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # MCP server configurations
        self.mcp_config = {
            "postman": {
                "command": "node",
                "args": [os.path.join(base_dir, "mcp-servers", "postman", "dist", "index.js")],
                "env": {"POSTMAN_API_KEY": os.getenv("POSTMAN_API_KEY", "")}
            },
            "memory": {
                "command": "node",
                "args": [os.path.join(base_dir, "mcp-servers", "memory", "dist", "index.js")],
                "env": {"REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379")}
            },
            "research": {
                "command": "node",
                "args": [os.path.join(base_dir, "mcp-servers", "research-tools", "dist", "index.js")],
                "env": {"REPORT_OUTPUT_DIR": os.getenv("REPORT_OUTPUT_DIR", "./reports")}
            }
        }
    
    async def connect_all(self):
        """Connect to all MCP servers and discover their tools"""
        logger.info("Connecting to MCP servers...")
        
        for server_name, config in self.mcp_config.items():
            try:
                await self._connect_server(server_name, config)
                logger.info(f"Connected to {server_name} MCP server")
            except Exception as e:
                logger.error(f"Failed to connect to {server_name} MCP server", error=str(e))
                # Continue with other servers even if one fails
        
        logger.info(f"MCP Tool Router initialized with {len(self.tool_registry)} tools")
    
    async def _connect_server(self, server_name: str, config: Dict[str, Any]):
        """Connect to a single MCP server"""
        server_params = StdioServerParameters(
            command=config["command"],
            args=config["args"],
            env={**os.environ.copy(), **config.get("env", {})}
        )
        
        # Create and enter context with timeout
        context = stdio_client(server_params)
        
        # Add timeout for connection
        try:
            read_stream, write_stream = await asyncio.wait_for(
                context.__aenter__(),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Timeout connecting to {server_name} MCP server")
        
        # Store context to keep it alive
        self.contexts[server_name] = context
        
        # Create session
        session = ClientSession(read_stream, write_stream)
        await asyncio.wait_for(session.initialize(), timeout=10.0)
        
        self.sessions[server_name] = session
        
        # Discover tools from this server
        try:
            tools_result = await asyncio.wait_for(session.list_tools(), timeout=5.0)
            for tool in tools_result.tools:
                self.tool_registry[tool.name] = server_name
                logger.debug(f"Registered tool: {tool.name} -> {server_name}")
        except Exception as e:
            logger.error(f"Failed to list tools from {server_name}", error=str(e))
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for Claude from all connected MCP servers"""
        all_tools = []
        
        for server_name, session in self.sessions.items():
            try:
                # Get tools from each MCP server synchronously
                tools_result = asyncio.run(session.list_tools())
                for tool in tools_result.tools:
                    all_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    })
            except Exception as e:
                logger.error(f"Failed to get tools from {server_name}", error=str(e))
        
        return all_tools
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        max_retries: int = 3
    ) -> Any:
        """Execute a tool by routing to appropriate MCP server with retry logic"""
        server_name = self.tool_registry.get(tool_name)
        if not server_name:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        session = self.sessions.get(server_name)
        if not session:
            raise RuntimeError(f"No session for server: {server_name}")
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.info(f"Executing tool: {tool_name}", server=server_name, attempt=attempt + 1)
                
                # Call tool via MCP protocol
                result = await session.call_tool(tool_name, arguments=tool_input)
                
                logger.info(f"Tool executed successfully: {tool_name}")
                return result.content
                
            except Exception as e:
                logger.error(
                    f"Tool execution failed: {tool_name}",
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt failed
                    raise RuntimeError(
                        f"Tool execution failed after {max_retries} attempts: {tool_name}"
                    ) from e
    
    async def close_all(self):
        """Close all MCP server connections"""
        logger.info("Closing MCP server connections...")
        
        for server_name, context in self.contexts.items():
            try:
                await context.__aexit__(None, None, None)
                logger.info(f"Closed connection to {server_name}")
            except Exception as e:
                logger.error(f"Error closing {server_name}", error=str(e))
        
        self.sessions.clear()
        self.contexts.clear()
        self.tool_registry.clear()
