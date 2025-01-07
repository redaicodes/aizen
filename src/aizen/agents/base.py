from typing import Dict, List, Optional, Callable, Any, Type
from pydantic import BaseModel
import asyncio
import logging
import inspect
from functools import partial


class ToolInterface:
    """Base interface for agent tools."""

    def __init__(self, name: str, func: Callable, logger: logging.Logger):
        self.name = name
        self.func = func
        self.logger = logger

    async def run(self, *args, **kwargs):
        """Execute the tool function."""
        try:
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(*args, **kwargs)
            return self.func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in tool {self.name}: {str(e)}")
            raise


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
        self.tools: Dict[str, ToolInterface] = {}
        self.llm = llm_callback
        self.state: Dict = {"transactions": [], "observations": []}
        self.tool_instances: Dict[str, Any] = {}  # Store tool class instances

        # Initialize logger
        self.logger = logging.getLogger(f"Agent.{self.config.name}")
        if not self.logger.handlers:  # Prevent duplicate handlers
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Set logging level based on config
        self.logger.setLevel(
            logging.DEBUG if self.config.debug_mode else logging.INFO)

        self.logger.debug("Agent initialized with debug mode") if self.config.debug_mode \
            else self.logger.info("Agent initialized")

    def register_tool_class(self, name: str, tool_class: Type, **kwargs):
        """
        Register a tool class and all its public methods as tools.

        Args:
            name (str): Base name for the tool
            tool_class (Type): Class to instantiate as a tool
            **kwargs: Arguments to pass to the tool class constructor
        """
        self.logger.info(f"Registering tool class: {name}")

        # Create instance of the tool class
        try:
            instance = tool_class(**kwargs)
            self.tool_instances[name] = instance

            # Get all public methods that don't start with _
            methods = inspect.getmembers(instance,
                                         predicate=lambda x: inspect.ismethod(x) and not x.__name__.startswith('_'))

            # Register each method as a tool
            for method_name, method in methods:
                tool_full_name = f"{name}.{method_name}"
                self.register_tool(tool_full_name, method)
                self.logger.debug(f"Registered tool method: {tool_full_name}")

            self.logger.info(f"Successfully registered {
                             len(methods)} methods from {name}")

        except Exception as e:
            self.logger.error(f"Error registering tool class {name}: {str(e)}")
            raise

    def register_tool(self, name: str, tool_func: Callable):
        """Register a single tool function."""
        self.logger.debug(f"Registering individual tool: {name}")
        self.tools[name] = ToolInterface(name, tool_func, self.logger)

    async def run_tool(self, tool_name: str, *args, **kwargs):
        """Execute a specific tool."""
        self.logger.debug(f"Executing tool: {tool_name} with args: {
                          args}, kwargs: {kwargs}")

        if tool_name not in self.tools:
            self.logger.error(f"Tool not found: {tool_name}")
            raise KeyError(f"Tool {tool_name} not found")

        try:
            tool_func = self.tools[tool_name].func

            # If it's a synchronous function, run it in a thread pool
            if not asyncio.iscoroutinefunction(tool_func):
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool_func(*args, **kwargs))
            else:
                result = await tool_func(*args, **kwargs)

            self.state["observations"].append({
                "tool": tool_name,
                "args": args,
                "kwargs": kwargs,
                "result": result
            })

            self.logger.debug(f"Tool {tool_name} executed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            raise

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

    async def run(self, task: Dict):
        """Execute agent task."""
        self.logger.info(f"Starting task execution with max {
                         self.config.max_iterations} iterations")
        iteration = 0

        while iteration < self.config.max_iterations:
            try:
                self.logger.debug(f"Starting iteration {iteration + 1}")

                action = await self.think({
                    "task": task,
                    "state": self.state,
                    "tools": list(self.tools.keys())
                })

                if not action or action.get("type") == "complete":
                    self.logger.info("Task completion signaled")
                    break

                result = await self.run_tool(
                    action["tool"],
                    *action.get("args", []),
                    **action.get("kwargs", {})
                )

                # Store the result and action in state
                self.state["transactions"].append({
                    "iteration": iteration,
                    "action": action,
                    "result": result
                })

                iteration += 1
                self.logger.debug(f"Completed iteration {
                                  iteration} with result: {result}")

            except Exception as e:
                self.logger.error(f"Error in task execution: {str(e)}")
                raise

        self.logger.info("Task execution completed")
        return self.state
