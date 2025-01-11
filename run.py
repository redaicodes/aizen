import argparse
import json
import asyncio
import os
from typing import Dict, List, Any, Type
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from aizen.agents.base import BaseAgent, AgentConfig
import functools
import inspect

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_json(prefix: str, data: Any):
    """Helper function to log JSON data in a readable format."""
    try:
        if isinstance(data, str):
            formatted = json.dumps(json.loads(data), indent=2)
        else:
            formatted = json.dumps(data, indent=2)
        logger.info(f"{prefix}:\n{formatted}")
    except Exception as e:
        logger.info(f"{prefix}: {data}")

def safe_execute(func):
    """Improved wrapper that properly handles both sync and async functions."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            logger.info(f"Starting execution of {func.__name__}")
            
            if asyncio.iscoroutinefunction(func):
                # If async function, await it directly
                result = await func(*args, **kwargs)
            else:
                # If sync function, run in a separate thread using asyncio.to_thread
                result = await asyncio.to_thread(func, *args, **kwargs)
            
            # Wait a short time to ensure result is complete
            await asyncio.sleep(0.1)
            
            logger.info(f"Successfully executed {func.__name__}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing {func.__name__}: {str(e)}", exc_info=True)
            raise  # Re-raise to handle in calling context
            
    return wrapper

class AgentRunner:
    # Class mapping for dynamic imports
    CLASS_MAPPING = {
        'blockworks': 'aizen.data.news.blockworks.Blockworks',
        'theblock': 'aizen.data.news.theblock.TheBlock',
        'twitterclient': 'aizen.social.twitterclient.TwitterClient'
    }

    def __init__(self, agent_config: str, task_config: str):
        """Initialize the agent runner with configuration files."""
        self.agent_config = self._load_config(agent_config)
        self.task_config = self._load_config(task_config)
        self.agent = None
        self.conversation_history = []
        self.max_function_calls = 5
        self.initialized_classes = {}
        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.function_definitions = self._load_function_definitions()

    def _load_config(self, config_path: str) -> Dict:
        """Load and validate configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                log_json(f"Loaded config from {config_path}", config)
                return config
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            raise

    def _load_function_definitions(self) -> Dict:
        """Load function definitions from static file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            functions_path = os.path.join(script_dir, "src/function_definitions.json")
            with open(functions_path, 'r') as f:
                definitions = json.load(f)
                log_json("Loaded function definitions", definitions)
                return {func["name"]: func for func in definitions}
        except Exception as e:
            logger.error(f"Error loading function definitions: {e}")
            raise

    def _import_class(self, class_path: str) -> Type:
        """Dynamically import a class from string path."""
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Error importing class {class_path}: {str(e)}")
            raise ImportError(f"Could not import {class_path}: {str(e)}")

    def _validate_tools(self) -> None:
        """Validate that all requested tools exist in registry."""
        if "tools" in self.agent_config:
            for tool in self.agent_config["tools"]:
                if tool not in self.function_definitions:
                    raise ValueError(f"Tool {tool} not found in function definitions")

        if "classes" in self.agent_config:
            for class_name in self.agent_config["classes"]:
                if class_name not in self.CLASS_MAPPING:
                    raise ValueError(f"Class {class_name} not found in CLASS_MAPPING")
                class_funcs = [f for f in self.function_definitions.keys() 
                             if f.startswith(f"{class_name}__")]
                if not class_funcs:
                    raise ValueError(f"No functions found for class {class_name}")

    async def _initialize_class(self, class_name: str) -> Any:
        """Initialize a class instance if needed."""
        if class_name not in self.initialized_classes:
            try:
                class_path = self.CLASS_MAPPING.get(class_name)
                if not class_path:
                    raise ValueError(f"No class mapping found for {class_name}")

                class_type = self._import_class(class_path)
                instance = class_type()
                self.initialized_classes[class_name] = instance
                logger.info(f"Successfully initialized {class_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize {class_name}: {str(e)}")
                raise

        return self.initialized_classes[class_name]

    async def initialize_agent(self):
        """Initialize the agent with specified tools."""
        try:
            # Validate tools first
            self._validate_tools()
            
            # Initialize agent configuration
            config = AgentConfig(
                name=self.agent_config["name"],
                tools=self.agent_config.get("tools", [])
            )
            
            # Initialize agent
            self.agent = BaseAgent(config)
            
            # Initialize tool classes
            if "classes" in self.agent_config:
                for class_name in self.agent_config["classes"]:
                    instance = await self._initialize_class(class_name)
                    class_functions = [f for f in self.function_definitions.keys() 
                                     if f.startswith(f"{class_name}__")]
                    
                    # Register all functions for the class
                    for func_name in class_functions:
                        method_name = func_name.split('__')[1]
                        if hasattr(instance, method_name):
                            method = getattr(instance, method_name)
                            wrapped_method = safe_execute(method)
                            self.agent.register_tool(func_name.replace('__', '.'), wrapped_method)
            
            # Initialize individual tools
            if "tools" in self.agent_config:
                for tool_name in self.agent_config["tools"]:
                    class_name = tool_name.split('__')[0]
                    instance = await self._initialize_class(class_name)
                    method_name = tool_name.split('__')[1]
                    
                    if hasattr(instance, method_name):
                        method = getattr(instance, method_name)
                        wrapped_method = safe_execute(method)
                        self.agent.register_tool(tool_name.replace('__', '.'), wrapped_method)
            
            logger.info(f"Agent {config.name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            raise

    async def run_tool(self, tool_name: str, **kwargs):
        """Execute a tool with proper async handling and error management."""
        try:
            if tool_name not in self.agent.tools:
                raise ValueError(f"Tool {tool_name} not found")
            
            tool = self.agent.tools[tool_name]
            logger.info(f"Executing tool {tool_name} with args: {kwargs}")
            
            # Execute tool in a separate thread and wait for result
            result = await asyncio.to_thread(tool.run, **kwargs)
            
            # Add small delay to ensure completion
            await asyncio.sleep(0.1)
            
            if isinstance(result, dict) and "error" in result:
                raise Exception(result["error"])
                
            log_json(f"Tool {tool_name} result", result)
            return result
            
        except Exception as e:
            logger.error(f"Error running tool {tool_name}: {str(e)}")
            raise

    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        tools = []
        if "tools" in self.agent_config:
            tools.extend(self.agent_config["tools"])
        if "classes" in self.agent_config:
            for class_name in self.agent_config["classes"]:
                tools.extend([
                    f for f in self.function_definitions.keys() 
                    if f.startswith(f"{class_name}__")
                ])
        return tools

    async def execute_task(self, task: Dict):
        """Execute a single task with improved error handling and async management."""
        try:
            # Initialize conversation
            system_prompt = self.agent_config.get(
                "system_prompt", 
                "You are an AI agent that helps with crypto news and social media."
            )
            
            self.conversation_history = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task["prompt"]}
            ]
            
            call_count = 0
            while call_count < self.max_function_calls:
                try:
                    # Log current state
                    log_json("Current conversation history", self.conversation_history)
                    
                    # Get completion from OpenAI
                    completion = await self.openai_client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=self.conversation_history,
                        tools=[{
                            "type": "function",
                            "function": {
                                "name": name,
                                "description": self.function_definitions[name]["description"],
                                "parameters": self.function_definitions[name]["parameters"]
                            }
                        } for name in self.get_available_tools()]
                    )
                    
                    message = completion.choices[0].message
                    
                    # Add assistant message to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": message.tool_calls
                    })
                    
                    if not message.tool_calls:
                        logger.info("Task completed without additional function calls")
                        break
                        
                    # Handle tool calls with proper awaiting
                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        try:
                            # Execute tool and ensure we wait for result
                            result = await self.run_tool(
                                func_name.replace('__', '.'),
                                **func_args
                            )
                            
                            # Add result to conversation
                            self.conversation_history.append({
                                "role": "tool",
                                "content": json.dumps(result),
                                "tool_call_id": tool_call.id
                            })
                            
                        except Exception as e:
                            logger.error(f"Tool execution failed: {str(e)}")
                            # Add error to conversation
                            self.conversation_history.append({
                                "role": "tool",
                                "content": json.dumps({"error": str(e)}),
                                "tool_call_id": tool_call.id
                            })
                    
                    call_count += 1
                    
                except Exception as e:
                    logger.error(f"Error in task execution loop: {str(e)}")
                    raise
                    
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            raise

    async def run(self):
        """Main execution loop with improved error handling."""
        try:
            await self.initialize_agent()
            
            while True:
                for task in self.task_config:
                    try:
                        logger.info(f"Starting task: {task['prompt']}")
                        await self.execute_task(task)
                        
                        frequency = int(task["frequency"])
                        logger.info(f"Waiting {frequency} minutes")
                        await asyncio.sleep(frequency * 60)
                        
                    except Exception as e:
                        logger.error(f"Task failed: {str(e)}")
                        await asyncio.sleep(60)  # Wait before retry
                        
        except Exception as e:
            logger.error(f"Runner failed: {str(e)}")
            raise

def get_default_path(relative_path: str) -> str:
    """Get absolute path from relative path, trying both run.py location and project root."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path1 = os.path.join(script_dir, relative_path)
    
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    path2 = os.path.join(root_dir, relative_path)
    
    if os.path.exists(path1):
        return path1
    elif os.path.exists(path2):
        return path2
    else:
        return path1

def main():
    parser = argparse.ArgumentParser(description="Run AI agent with specified configuration")
    parser.add_argument(
        "--agent", 
        default=get_default_path("./src/aizen/agents/cryptopulse.agent.json"),
        help="Path to agent configuration JSON file"
    )
    parser.add_argument(
        "--task", 
        default=get_default_path("./src/aizen/agents/fetch_news_and_tweet.task.json"),
        help="Path to task configuration JSON file"
    )
    
    args = parser.parse_args()
    
    # Validate file paths
    for path_arg, path_name in [
        (args.agent, "Agent config"),
        (args.task, "Task config")
    ]:
        if not os.path.exists(path_arg):
            raise FileNotFoundError(
                f"{path_name} file not found: {path_arg}\n"
                f"Please ensure the file exists at the specified location."
            )
    
    # Log the paths being used
    logger.info(f"Using agent config: {args.agent}")
    logger.info(f"Using task config: {args.task}")
    
    # Create and run agent
    runner = AgentRunner(args.agent, args.task)
    asyncio.run(runner.run())

if __name__ == "__main__":
    main()