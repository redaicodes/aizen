from typing import Dict, List, Optional, Callable, Any, Type
from pydantic import BaseModel
import asyncio
import logging
import inspect
from functools import partial


class AgentConfig(BaseModel):
    """Configuration for an autonomous agent."""
    name: str
    description: str = ""
    tools: List[str] = []
    async_mode: bool = True
    max_iterations: int = 5
    debug_mode: bool = False


class BaseAgent:
    """Base class for autonomous agents with flexible tool integration."""

    def __init__(self, config: AgentConfig, llm_callback: Optional[Callable] = None):
        self.config = config
        self.tools: Dict[str, Any] = {}  # Tools are stored directly on self
        self.llm = llm_callback
        self.state: Dict = {"transactions": [], "observations": []}
        
        # Initialize logger
        self.logger = logging.getLogger(f"Agent.{self.config.name}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        self.logger.setLevel(
            logging.DEBUG if self.config.debug_mode else logging.INFO
        )

    def register_tool(self, name: str, tool_func: Callable):
        """Register a tool function."""
        try:
            self.logger.debug(f"Registering tool: {name}")
            self.tools[name] = tool_func
            self.logger.debug(f"Successfully registered tool: {name}")
        except Exception as e:
            self.logger.error(f"Error registering tool {name}: {str(e)}")
            raise

    async def run_tool(self, tool_name: str, **kwargs):
        """Execute a tool with improved error handling."""
        try:
            if tool_name not in self.tools:  # Check tools directly on self
                available_tools = list(self.tools.keys())
                raise ValueError(
                    f"Tool {tool_name} not found. Available tools: {available_tools}"
                )
            
            tool = self.tools[tool_name]  # Get tool directly from self.tools
            result = await tool(**kwargs)
            
            if not result["success"]:
                self.logger.error(f"Tool {tool_name} failed: {result['error']}")
                return result["error"]  # Return error message for GPT
                
            self.logger.info(f"Tool {tool_name} executed successfully")
            return result["data"]  # Return actual data for GPT
            
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return error_msg  # Return error message for GPT

    async def think(self, context: Dict):
        """Process context and decide next action."""
        self.logger.debug("Processing context to decide next action")

        if not self.llm:
            self.logger.error("No LLM callback provided")
            raise ValueError("No LLM callback provided")

        try:
            result = await self.llm(context)
            self.logger.debug("Successfully determined next action")
            return result
        except Exception as e:
            self.logger.error(f"Error in think phase: {str(e)}")
            raise