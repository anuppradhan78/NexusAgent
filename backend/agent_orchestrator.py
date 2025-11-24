"""
Agent Orchestrator - Core agent logic coordinating Claude and MCP tools
"""
import time
import uuid
from typing import Dict, Any, List, Optional
import structlog

from claude_client import ClaudeClient
from mcp_tool_router import MCPToolRouter

logger = structlog.get_logger()


class AgentOrchestrator:
    """Core agent logic coordinating Claude and MCP tools"""
    
    def __init__(
        self,
        claude_client: ClaudeClient,
        mcp_tool_router: MCPToolRouter
    ):
        self.claude_client = claude_client
        self.mcp_tool_router = mcp_tool_router
    
    async def process_query(
        self,
        query: str,
        max_sources: int = 5,
        include_report: bool = True
    ) -> Dict[str, Any]:
        """
        Main agent processing pipeline using Claude with MCP tools
        
        Flow:
        1. Call Claude with query and available MCP tools
        2. Claude decides which tools to use (search_apis, call_api, etc.)
        3. Execute tool calls via MCP servers
        4. Return results to Claude for synthesis
        5. Claude generates final response
        6. Store results and optionally generate report
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())
        
        logger.info("Processing query", query_id=query_id, query=query)
        
        try:
            # Step 1: Get tool definitions from MCP Tool Router
            available_tools = self.mcp_tool_router.get_tool_definitions()
            logger.info(f"Available tools: {len(available_tools)}")
            
            # Step 2: Call Claude with query and tools
            messages = [
                {
                    "role": "user",
                    "content": f"Research query: {query}. Use available tools to gather information from APIs, then synthesize a comprehensive answer."
                }
            ]
            
            response = await self.claude_client.call_with_tools(
                messages=messages,
                tools=available_tools
            )
            
            # Step 3: Handle tool use loop
            tool_results = []
            sources_used = []
            conversation_messages = messages.copy()
            
            while response.stop_reason == "tool_use":
                logger.info("Claude requested tool use")
                
                # Add assistant's response to conversation
                conversation_messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Execute all tool calls
                tool_result_content = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        logger.info(f"Executing tool: {content_block.name}")
                        
                        try:
                            # Execute tool via MCP server
                            result = await self.mcp_tool_router.execute_tool(
                                tool_name=content_block.name,
                                tool_input=content_block.input
                            )
                            
                            tool_result_content.append({
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": str(result)
                            })
                            
                            tool_results.append({
                                "tool": content_block.name,
                                "input": content_block.input,
                                "result": result
                            })
                            
                            # Track sources if it's an API search/call
                            if content_block.name in ["search_apis", "call_api"]:
                                sources_used.append({
                                    "tool": content_block.name,
                                    "input": content_block.input
                                })
                            
                        except Exception as e:
                            logger.error(f"Tool execution failed: {content_block.name}", error=str(e))
                            tool_result_content.append({
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True
                            })
                
                # Add tool results to conversation
                conversation_messages.append({
                    "role": "user",
                    "content": tool_result_content
                })
                
                # Continue conversation with tool results
                response = await self.claude_client.call_with_tools(
                    messages=conversation_messages,
                    tools=available_tools
                )
            
            # Step 4: Extract final synthesis from Claude
            synthesis = self._extract_text_from_response(response)
            
            logger.info("Claude synthesis complete", tool_calls=len(tool_results))
            
            # Step 5: Store results in memory (via Memory MCP Server)
            try:
                await self.mcp_tool_router.execute_tool(
                    "store_result",
                    {
                        "query": query,
                        "results": {
                            "answer": synthesis,
                            "sources": sources_used
                        },
                        "timestamp": time.time()
                    }
                )
                logger.info("Results stored in memory")
            except Exception as e:
                logger.error("Failed to store results in memory", error=str(e))
            
            # Step 6: Optionally generate report
            report_path = None
            if include_report:
                try:
                    report_result = await self.mcp_tool_router.execute_tool(
                        "generate_report",
                        {
                            "query": query,
                            "answer": synthesis,
                            "sources": sources_used,
                            "metadata": {
                                "query_id": query_id,
                                "processing_time_ms": int((time.time() - start_time) * 1000)
                            }
                        }
                    )
                    
                    # Extract report path from result
                    import json
                    if report_result and len(report_result) > 0:
                        report_data = json.loads(report_result[0].get("text", "{}"))
                        report_path = report_data.get("report_path")
                    
                    logger.info("Report generated", report_path=report_path)
                except Exception as e:
                    logger.error("Failed to generate report", error=str(e))
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "query_id": query_id,
                "synthesized_answer": synthesis,
                "sources": sources_used,
                "report_path": report_path,
                "processing_time_ms": processing_time_ms,
                "tool_calls_made": len(tool_results)
            }
            
        except Exception as e:
            logger.error("Query processing failed", error=str(e), query_id=query_id)
            raise
    
    def _extract_text_from_response(self, response: Any) -> str:
        """Extract text content from Claude response"""
        text_parts = []
        for content_block in response.content:
            if content_block.type == "text":
                text_parts.append(content_block.text)
        return "\n".join(text_parts)
