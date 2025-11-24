"""
Claude Client - Direct interface with Anthropic Claude API
"""
import os
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import structlog
import asyncio

logger = structlog.get_logger()


class ClaudeClient:
    """Direct interface with Anthropic Claude API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.max_retries = 3
    
    async def call_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 4096
    ) -> Any:
        """Call Claude with tool definitions and handle retries"""
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "Calling Claude API",
                    model=self.model,
                    num_tools=len(tools),
                    attempt=attempt + 1
                )
                
                # Call Claude API (synchronous)
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    tools=tools,
                    messages=messages
                )
                
                logger.info(
                    "Claude API call successful",
                    stop_reason=response.stop_reason,
                    usage=response.usage.model_dump() if response.usage else None
                )
                
                return response
                
            except Exception as e:
                logger.error(
                    "Claude API call failed",
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt failed
                    raise RuntimeError(
                        f"Claude API call failed after {self.max_retries} attempts"
                    ) from e
    
    def create_message(
        self,
        role: str,
        content: Any
    ) -> Dict[str, Any]:
        """Helper to create a message dict"""
        return {
            "role": role,
            "content": content
        }
