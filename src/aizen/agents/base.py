from typing import Dict, List, Optional, Callable
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)


class ToolInterface:
    """Base interface for agent tools."""

    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func

    async def run(self, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(*args, **kwargs)
            return self.func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in tool {self.name}: {str(e)}")
            raise


class AgentConfig(BaseModel):
    """Configuration for an autonomous agent."""
    name: str
    description: str = ""
    tools: List[str] = []
    async_mode: bool = True
    max_iterations: int = 5


class BaseAgent:
    """Base class for autonomous Web3 agents."""

    def __init__(self, config: AgentConfig, llm_callback: Optional[Callable] = None):
        self.config = config
        self.tools: Dict[str, ToolInterface] = {}
        self.llm = llm_callback  # Function that handles LLM calls
        self.state: Dict = {"transactions": [], "observations": []}

    def register_tool(self, name: str, tool_func: Callable):
        """Register a new tool."""
        self.tools[name] = ToolInterface(name, tool_func)

    async def run_tool(self, tool_name: str, *args, **kwargs):
        """Execute a specific tool."""
        if tool_name not in self.tools:
            raise KeyError(f"Tool {tool_name} not found")

        result = await self.tools[tool_name].run(*args, **kwargs)
        self.state["observations"].append({
            "tool": tool_name,
            "args": args,
            "kwargs": kwargs,
            "result": result
        })
        return result

    async def think(self, context: Dict):
        """Process context and decide next action."""
        if not self.llm:
            raise ValueError("No LLM callback provided")
        return await self.llm(context)

    async def run(self, task: Dict):
        """Execute agent task."""
        iteration = 0
        while iteration < self.config.max_iterations:
            try:
                action = await self.think({
                    "task": task,
                    "state": self.state,
                    "tools": list(self.tools.keys())
                })

                if not action or action.get("type") == "complete":
                    break

                result = await self.run_tool(
                    action["tool"],
                    *action.get("args", []),
                    **action.get("kwargs", {})
                )

                iteration += 1

            except Exception as e:
                logger.error(f"Error in agent execution: {str(e)}")
                raise

        return self.state
