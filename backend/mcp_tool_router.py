"""
MCP Tool Router - Routes tool calls from Claude to appropriate MCP servers
Uses direct subprocess communication instead of MCP SDK stdio (which has compatibility issues)
"""
import asyncio
import os
import json
import subprocess
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()


class MCPToolRouter:
    """Routes tool calls to our custom MCP servers using direct subprocess communication"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.tool_registry: Dict[str, str] = {}
        self.tool_schemas: Dict[str, Dict[str, Any]] = {}
        
        # Get absolute paths for MCP servers
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # MCP server configurations
        self.mcp_config = {
            "postman": {
                "command": "node",
                "args": [os.path.join(base_dir, "mcp-servers", "postman", "dist", "index.js")],
                "env": {"POSTMAN_API_KEY": os.getenv("POSTMAN_API_KEY", "")},
                "tools": [
                    {
                        "name": "send_api_request",
                        "description": "Send HTTP request using Postman-like interface",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                                "url": {"type": "string"},
                                "headers": {"type": "object"},
                                "body": {"type": "object"}
                            },
                            "required": ["method", "url"]
                        }
                    }
                ]
            },
            "memory": {
                "command": "node",
                "args": [os.path.join(base_dir, "mcp-servers", "memory", "dist", "index.js")],
                "env": {"REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379")},
                "tools": [
                    {
                        "name": "store_memory",
                        "description": "Store information in memory for later retrieval",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"},
                                "value": {"type": "string"},
                                "ttl": {"type": "number"}
                            },
                            "required": ["key", "value"]
                        }
                    },
                    {
                        "name": "retrieve_memory",
                        "description": "Retrieve stored information from memory",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"}
                            },
                            "required": ["key"]
                        }
                    }
                ]
            },
            "research": {
                "command": "node",
                "args": [os.path.join(base_dir, "mcp-servers", "research-tools", "dist", "index.js")],
                "env": {"REPORT_OUTPUT_DIR": os.getenv("REPORT_OUTPUT_DIR", "./reports")},
                "tools": [
                    {
                        "name": "search_web",
                        "description": "Search the web for information",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "max_results": {"type": "number"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "fetch_url",
                        "description": "Fetch content from a URL",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"}
                            },
                            "required": ["url"]
                        }
                    },
                    {
                        "name": "generate_report",
                        "description": "Generate a research report",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "sources": {"type": "array"}
                            },
                            "required": ["title", "content"]
                        }
                    }
                ]
            }
        }
    
    async def connect_all(self):
        """Register all MCP tools from configuration"""
        logger.info("Registering MCP tools...")
        
        for server_name, config in self.mcp_config.items():
            try:
                # Register tools from configuration
                for tool in config.get("tools", []):
                    tool_name = tool["name"]
                    self.tool_registry[tool_name] = server_name
                    self.tool_schemas[tool_name] = tool
                    logger.debug(f"Registered tool: {tool_name} -> {server_name}")
                
                logger.info(f"Registered {len(config.get('tools', []))} tools from {server_name}")
            except Exception as e:
                logger.error(f"Failed to register tools from {server_name}", error=str(e))
        
        logger.info(f"MCP Tool Router initialized with {len(self.tool_registry)} tools")
        
        if len(self.tool_registry) == 0:
            logger.warning("No MCP tools available - running in degraded mode")
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for Claude"""
        all_tools = []
        
        for tool_name, tool_schema in self.tool_schemas.items():
            all_tools.append({
                "name": tool_schema["name"],
                "description": tool_schema["description"],
                "input_schema": tool_schema["input_schema"]
            })
        
        return all_tools
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        max_retries: int = 3
    ) -> Any:
        """Execute a tool by calling the MCP server directly via subprocess"""
        server_name = self.tool_registry.get(tool_name)
        if not server_name:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        config = self.mcp_config.get(server_name)
        if not config:
            raise RuntimeError(f"No configuration for server: {server_name}")
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.info(f"Executing tool: {tool_name}", server=server_name, attempt=attempt + 1)
                
                # Create MCP request
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": tool_input
                    }
                }
                
                # Execute via subprocess
                env = {**os.environ.copy(), **config.get("env", {})}
                process = await asyncio.create_subprocess_exec(
                    config["command"],
                    *config["args"],
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                # Send request and get response
                request_json = json.dumps(request) + "\n"
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(request_json.encode()),
                    timeout=30.0
                )
                
                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    raise RuntimeError(f"MCP server error: {error_msg}")
                
                # Parse response
                response_text = stdout.decode().strip()
                if not response_text:
                    raise RuntimeError("Empty response from MCP server")
                
                # Handle multiple JSON objects (initialization + response)
                lines = response_text.split("\n")
                response = None
                for line in lines:
                    if line.strip():
                        try:
                            obj = json.loads(line)
                            if obj.get("id") == 1:  # Our request
                                response = obj
                                break
                        except json.JSONDecodeError:
                            continue
                
                if not response:
                    raise RuntimeError(f"No valid response found in: {response_text}")
                
                if "error" in response:
                    raise RuntimeError(f"MCP error: {response['error']}")
                
                logger.info(f"Tool executed successfully: {tool_name}")
                return response.get("result", {})
                
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
        """Cleanup (no persistent connections in subprocess mode)"""
        logger.info("Cleaning up MCP tool router...")
        self.tool_registry.clear()
        self.tool_schemas.clear()
