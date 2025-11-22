"""
MCP Client for Anthropic Claude and Postman API Network

This module provides the MCPClient class that manages connections to:
- Anthropic MCP server for Claude LLM interactions
- Postman MCP server for API discovery and execution

Requirements: 8.1, 8.2, 8.5, 9.1, 9.2
"""
import os
import asyncio
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import structlog

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    raise ImportError(
        "MCP package not found. Install with: pip install mcp"
    )

logger = structlog.get_logger()


@dataclass
class APIEndpoint:
    """Represents an API endpoint from Postman"""
    api_id: str
    api_name: str
    endpoint: str
    method: str
    description: str
    verified: bool
    priority_score: float = 0.5


class MCPConnectionError(Exception):
    """Raised when MCP connection fails"""
    pass


class MCPClient:
    """
    Client for interacting with Anthropic Claude and Postman via MCP protocol.
    
    Handles:
    - Connection management with retry logic
    - Claude LLM calls for reasoning and synthesis
    - Postman API discovery and execution
    - Graceful error handling and connection recovery
    """
    
    def __init__(self):
        """Initialize MCP client with configuration from environment"""
        self.claude_session: Optional[ClientSession] = None
        self.postman_session: Optional[ClientSession] = None
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.postman_api_key = os.getenv("POSTMAN_API_KEY")
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        
        # Validate required environment variables
        if not self.anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not set - Claude functionality will be limited")
        if not self.postman_api_key:
            logger.warning("POSTMAN_API_KEY not set - Postman functionality will be limited")
    
    async def initialize(self) -> None:
        """
        Initialize MCP connections to both Anthropic and Postman servers.
        
        Implements retry logic with exponential backoff for connection resilience.
        Requirements: 8.1, 8.5, 9.1
        """
        logger.info("initializing_mcp_client")
        
        # Connect to Anthropic MCP
        if self.anthropic_api_key:
            try:
                self.claude_session = await self._connect_with_retry(
                    self._connect_claude,
                    "Anthropic Claude"
                )
                logger.info("anthropic_mcp_connected")
            except MCPConnectionError as e:
                logger.error("anthropic_mcp_connection_failed", error=str(e))
                raise
        
        # Connect to Postman MCP
        if self.postman_api_key:
            try:
                self.postman_session = await self._connect_with_retry(
                    self._connect_postman,
                    "Postman"
                )
                logger.info("postman_mcp_connected")
            except MCPConnectionError as e:
                logger.error("postman_mcp_connection_failed", error=str(e))
                raise
        
        logger.info("mcp_client_initialized")
    
    async def _connect_with_retry(
        self,
        connect_func,
        service_name: str
    ) -> ClientSession:
        """
        Connect to MCP server with exponential backoff retry logic.
        
        Requirements: 8.5 - Connection retry logic with exponential backoff
        
        Args:
            connect_func: Async function that performs the connection
            service_name: Name of the service for logging
            
        Returns:
            ClientSession: Connected MCP session
            
        Raises:
            MCPConnectionError: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "mcp_connection_attempt",
                    service=service_name,
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                
                session = await connect_func()
                
                logger.info(
                    "mcp_connection_success",
                    service=service_name,
                    attempt=attempt + 1
                )
                
                return session
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "mcp_connection_failed",
                    service=service_name,
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(
                        "mcp_connection_retry",
                        service=service_name,
                        delay_seconds=delay
                    )
                    await asyncio.sleep(delay)
        
        # All retries failed
        error_msg = f"Failed to connect to {service_name} after {self.max_retries} attempts: {last_error}"
        logger.error("mcp_connection_exhausted", service=service_name, error=str(last_error))
        raise MCPConnectionError(error_msg)
    
    async def _connect_claude(self) -> ClientSession:
        """
        Connect to Anthropic Claude MCP server.
        
        Requirements: 8.1 - Connect to Anthropic_Claude via MCP protocol
        
        Returns:
            ClientSession: Connected Claude session
        """
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@anthropic-ai/mcp-server-anthropic"],
            env={"ANTHROPIC_API_KEY": self.anthropic_api_key}
        )
        
        # Use stdio_client as async context manager properly
        async with stdio_client(server_params) as (read_stream, write_stream):
            # Create and initialize session
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            
            # Store session (streams will remain open)
            return session
    
    async def _connect_postman(self) -> ClientSession:
        """
        Connect to Postman MCP server.
        
        Requirements: 9.1 - Connect to Postman_MCP server
        
        Returns:
            ClientSession: Connected Postman session
        """
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@postman/mcp-server"],
            env={"POSTMAN_API_KEY": self.postman_api_key}
        )
        
        # Use stdio_client as async context manager properly
        async with stdio_client(server_params) as (read_stream, write_stream):
            # Create and initialize session
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            
            # Store session (streams will remain open)
            return session

    async def call_claude(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Call Claude via MCP for reasoning, synthesis, and decision-making.
        
        Requirements: 8.2 - Use Claude for query intent parsing, information synthesis,
                            and relevance assessment
        
        Args:
            prompt: The user prompt/question
            system: System prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            str: Claude's response text
            
        Raises:
            MCPConnectionError: If Claude session is not initialized
        """
        if not self.claude_session:
            raise MCPConnectionError("Claude session not initialized. Call initialize() first.")
        
        try:
            logger.info(
                "calling_claude",
                prompt_length=len(prompt),
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Call Claude via MCP tool
            response = await self.claude_session.call_tool(
                "claude_chat",
                arguments={
                    "prompt": prompt,
                    "system": system,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "model": "claude-3-5-sonnet-20241022"
                }
            )
            
            # Extract content from response
            content = self._extract_content(response)
            
            logger.info(
                "claude_response_received",
                response_length=len(content)
            )
            
            return content
            
        except Exception as e:
            logger.error("claude_call_failed", error=str(e))
            raise MCPConnectionError(f"Failed to call Claude: {e}")
    
    async def discover_apis(
        self,
        query: str,
        verified_only: bool = True,
        max_results: int = 10
    ) -> List[APIEndpoint]:
        """
        Discover relevant APIs from Postman Public API Network.
        
        Requirements: 9.2 - Query Postman Public API Network to discover relevant APIs
        
        Args:
            query: Search query for API discovery
            verified_only: Only return verified publisher APIs
            max_results: Maximum number of APIs to return
            
        Returns:
            List[APIEndpoint]: List of discovered API endpoints
            
        Raises:
            MCPConnectionError: If Postman session is not initialized
        """
        if not self.postman_session:
            raise MCPConnectionError("Postman session not initialized. Call initialize() first.")
        
        try:
            logger.info(
                "discovering_apis",
                query=query,
                verified_only=verified_only,
                max_results=max_results
            )
            
            # Search for APIs via Postman MCP
            response = await self.postman_session.call_tool(
                "search_apis",
                arguments={
                    "query": query,
                    "verified_only": verified_only,
                    "limit": max_results
                }
            )
            
            # Parse API results
            api_endpoints = self._parse_api_results(response)
            
            logger.info(
                "apis_discovered",
                count=len(api_endpoints),
                query=query
            )
            
            return api_endpoints
            
        except Exception as e:
            logger.error("api_discovery_failed", error=str(e), query=query)
            # Return empty list instead of raising to allow graceful degradation
            return []
    
    async def call_api(
        self,
        api_id: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute an API request via Postman MCP.
        
        Requirements: 9.2 - Execute API requests through Postman MCP
        
        Args:
            api_id: Postman API identifier
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            headers: HTTP headers
            body: Request body for POST/PUT
            timeout: Request timeout in seconds
            
        Returns:
            Dict[str, Any]: API response data
            
        Raises:
            MCPConnectionError: If Postman session is not initialized
        """
        if not self.postman_session:
            raise MCPConnectionError("Postman session not initialized. Call initialize() first.")
        
        try:
            logger.info(
                "calling_api",
                api_id=api_id,
                endpoint=endpoint,
                method=method
            )
            
            # Prepare request arguments
            request_args = {
                "api_id": api_id,
                "endpoint": endpoint,
                "method": method,
                "timeout": timeout
            }
            
            if params:
                request_args["params"] = params
            if headers:
                request_args["headers"] = headers
            if body:
                request_args["body"] = body
            
            # Execute API request via Postman MCP
            response = await self.postman_session.call_tool(
                "execute_request",
                arguments=request_args
            )
            
            # Extract response content
            result = self._extract_content(response)
            
            logger.info(
                "api_call_success",
                api_id=api_id,
                endpoint=endpoint,
                status_code=result.get("status_code", "unknown")
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "api_call_failed",
                api_id=api_id,
                endpoint=endpoint,
                error=str(e)
            )
            # Return error response instead of raising to allow graceful degradation
            return {
                "error": str(e),
                "status_code": 500,
                "success": False
            }
    
    def _extract_content(self, response: Any) -> Any:
        """
        Extract content from MCP response.
        
        Args:
            response: MCP response object
            
        Returns:
            Extracted content (string or dict)
        """
        # Handle different response formats
        if hasattr(response, 'content'):
            content = response.content
            
            # If content is a list, join text items
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if hasattr(item, 'text'):
                        text_parts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                return '\n'.join(text_parts) if text_parts else ""
            
            return content
        
        # Fallback to string representation
        return str(response)
    
    def _parse_api_results(self, response: Any) -> List[APIEndpoint]:
        """
        Parse API discovery results from Postman MCP response.
        
        Args:
            response: MCP response from search_apis
            
        Returns:
            List[APIEndpoint]: Parsed API endpoints
        """
        api_endpoints = []
        
        try:
            # Extract content
            content = self._extract_content(response)
            
            # Parse JSON if string
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("failed_to_parse_api_results", content=content[:200])
                    return []
            
            # Handle different response structures
            apis = []
            if isinstance(content, dict):
                apis = content.get('apis', content.get('results', []))
            elif isinstance(content, list):
                apis = content
            
            # Parse each API
            for api_data in apis:
                if isinstance(api_data, dict):
                    api_endpoints.append(APIEndpoint(
                        api_id=api_data.get('id', api_data.get('api_id', '')),
                        api_name=api_data.get('name', api_data.get('api_name', 'Unknown')),
                        endpoint=api_data.get('endpoint', api_data.get('url', '')),
                        method=api_data.get('method', 'GET'),
                        description=api_data.get('description', ''),
                        verified=api_data.get('verified', False),
                        priority_score=api_data.get('priority_score', 0.5)
                    ))
        
        except Exception as e:
            logger.error("api_parsing_error", error=str(e))
        
        return api_endpoints
    
    async def close(self) -> None:
        """
        Close MCP connections gracefully.
        """
        logger.info("closing_mcp_connections")
        
        # Note: Sessions are managed by the stdio_client context manager
        # Just clear references
        self.claude_session = None
        self.postman_session = None
        
        logger.info("mcp_connections_closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
