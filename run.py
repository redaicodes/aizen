import asyncio
import json
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
from importlib import import_module
from pathlib import Path
import functools
import os
from openai import OpenAI
import inspect
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Validate OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AgentRunner')

DEFAULT_SYSTEM_PROMPT = """You are an AI agent that can leverage various tools to achieve specific goals.
Call the appropriate tools when needed and process their outputs to complete your tasks effectively."""

DEFAULT_MAX_GPT_CALLS = 5
DEFAULT_AGENT_CONFIG_PATH = "./src/aizen/agents/cryptopulse.agent.json"

class ToolWrapper:
    """Wrapper for standardizing tool outputs and handling errors."""
    
    @staticmethod
    def wrap_tool(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Special handling for Playwright functions
                if 'playwright' in func.__module__ or 'get_page_content' in func.__name__:
                    import multiprocessing
                    
                    def run_playwright_func(*a, **kw):
                        try:
                            return func(*a, **kw)
                        except Exception as e:
                            return {"error": str(e)}
                    
                    # Use spawn context to avoid any asyncio issues
                    ctx = multiprocessing.get_context('spawn')
                    with ctx.Pool(1) as pool:
                        result = pool.apply(run_playwright_func, args=args, kwds=kwargs)
                        
                        if isinstance(result, dict) and "error" in result:
                            return {
                                "success": False,
                                "data": None,
                                "error": result["error"]
                            }
                        return {
                            "success": True,
                            "data": result,
                            "error": None
                        }
                
                # Normal function execution for non-Playwright functions
                result = func(*args, **kwargs)
                return {
                    "success": True,
                    "data": result,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Error in tool {func.__name__}: {str(e)}")
                return {
                    "success": False,
                    "data": None,
                    "error": str(e)
                }
        return wrapper

class AgentRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.tool_instances = {}
        self.tools = {}
        self.chat_history = []
        self.max_gpt_calls = self.config.get('max_gpt_calls', DEFAULT_MAX_GPT_CALLS)
        
        # Initialize OpenAI client
        self.client = OpenAI()
        # Store function schemas for OpenAI
        self.function_schemas = []
        
        # Initialize tools
        self._initialize_tools()
        
    def _load_config(self) -> Dict:
        """Load and validate agent configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Validate required fields
            required_fields = ['name', 'tools', 'tasks']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
                    
            # Set default system prompt if not provided
            if 'system_prompt' not in config:
                config['system_prompt'] = DEFAULT_SYSTEM_PROMPT
                
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise

    def _get_class_from_path(self, class_path: str) -> Any:
        """Import and return class from path string."""
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = import_module(module_path)
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Error importing class {class_path}: {str(e)}")
            raise

    def _get_function_schema(self, func) -> Dict:
        """Generate OpenAI function schema from function signature."""
        sig = inspect.signature(func)
        
        # Get function parameters
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter for instance methods
            if param_name == 'self':
                continue
                
            # Get parameter annotation if available
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else "string"
            
            # Convert Python types to JSON schema types
            type_mapping = {
                str: "string",
                int: "number",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
            
            param_schema = {"type": type_mapping.get(param_type, "string")}
            parameters["properties"][param_name] = param_schema
            
            # Add to required parameters if no default value
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        # Get function docstring for description
        doc = inspect.getdoc(func) or ""
        
        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": doc,
                "parameters": parameters
            }
        }

    def _load_function_definitions(self) -> Dict:
        """Load and parse function definitions from JSON file."""
        try:
            # Load from ./src/function_definitions.json
            definitions_path = Path("./src/function_definitions.json")
            with open(definitions_path) as f:
                definitions = json.load(f)
                
            # Convert to dict for easier lookup
            return {func["name"]: func for func in definitions}
        except Exception as e:
            logger.error(f"Error loading function definitions: {str(e)}")
            raise

    def _initialize_tools(self):
        """Initialize tool classes and register their methods."""
        CLASS_MAPPING = {
            'blockworks': 'aizen.data.news.blockworks.Blockworks',
            'theblock': 'aizen.data.news.theblock.TheBlock',
            'twitterclient': 'aizen.social.twitterclient.TwitterClient',
            'bscclient': 'aizen.chains.bsc.BscClient'
        }

        # Load function definitions
        self.function_definitions = self._load_function_definitions()
        
        # Track unique class names from both specific functions and class-level tools
        required_classes = set()
        tools_to_register = []  # Store tools for registration after class initialization
        
        # First pass: validate tools and collect required classes
        for tool in self.config['tools']:
            if '__' in tool:
                # Specific function mentioned (e.g., 'blockworks__get_latest_news')
                if tool not in self.function_definitions:
                    raise ValueError(f"Function {tool} not found in function definitions")
                class_name, method_name = tool.split('__')
                required_classes.add(class_name)
                tools_to_register.append(("method", tool))
            else:
                # Full class mentioned (e.g., 'blockworks')
                if tool not in CLASS_MAPPING:
                    raise ValueError(f"Unknown tool class: {tool}")
                required_classes.add(tool)
                tools_to_register.append(("class", tool))

        # Initialize all required classes
        logger.info(f"Initializing classes: {required_classes}")
        for class_name in required_classes:
            if class_name not in CLASS_MAPPING:
                raise ValueError(f"Unknown tool class: {class_name}")
            
            class_path = CLASS_MAPPING[class_name]
            cls = self._get_class_from_path(class_path)
            self.tool_instances[class_name] = cls()
            logger.info(f"Initialized {class_name} instance")

        # Second pass: register tools and methods
        for tool_type, tool in tools_to_register:
            if tool_type == "method":
                # Register specific method
                class_name, method_name = tool.split('__')
                method = getattr(self.tool_instances[class_name], method_name)
                self.tools[tool] = method
                self.function_schemas.append({
                    "type": "function",
                    "function": self.function_definitions[tool]
                })
            else:
                # Register all methods of the class that are in function definitions
                instance = self.tool_instances[tool]
                for attr_name in dir(instance):
                    if not attr_name.startswith('_'):
                        full_name = f"{tool}__{attr_name}"
                        if full_name in self.function_definitions:
                            attr = getattr(instance, attr_name)
                            if callable(attr):
                                self.tools[full_name] = attr
                                self.function_schemas.append({
                                    "type": "function",
                                    "function": self.function_definitions[full_name]
                                })
    
    def execute_task(self, task: Dict):
        """Execute a single task with GPT interaction."""
        gpt_calls = 0
        
        # Initialize messages for the conversation
        messages = [
            {"role": "system", "content": self.config['system_prompt']},
            *self.chat_history,
            {"role": "user", "content": task['prompt']}
        ]
        
        while gpt_calls < self.max_gpt_calls:
            try:
                last_message = messages[-1] if messages else None
                prev_messages_count = len(messages) - 1 if messages else 0

                logger.info(f"Context: {prev_messages_count} previous messages")
                logger.info(f"Sending last message to GPT: {json.dumps(last_message, indent=2)}")  

                # Call GPT with tools
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=self.function_schemas
                )
                
                message = completion.choices[0].message
                logger.info(f"GPT Response: {message.content if message.content else 'No content'}")
                
                # Log tool calls if present
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    logger.info("Tool Calls in Response:")
                    for tool_call in message.tool_calls:
                        logger.info(f"  - Tool: {tool_call.function.name}")
                        logger.info(f"    Args: {tool_call.function.arguments}")
                
                # Add assistant's message to conversation
                messages.append({
                    "role": "assistant",
                    "content": message.content if message.content else "",
                    **({"tool_calls": [
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        } for call in message.tool_calls
                    ]} if hasattr(message, 'tool_calls') and message.tool_calls else {})
                })
                
                # If no tool calls, task is complete
                if not hasattr(message, 'tool_calls') or not message.tool_calls:
                    self.chat_history.append(messages[-1])  # Add final response to chat history
                    break
                
                # Execute tool calls and add results to conversation
                for tool_call in message.tool_calls:
                    if tool_call.type == 'function':
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        if func_name in self.tools:
                            try:
                                logger.info(f"Executing tool: {func_name} with args: {func_args}")
                                tool_func = self.tools[func_name]
                                # Execute tool with proper sync/async handling
                                if asyncio.iscoroutinefunction(tool_func):
                                    loop = asyncio.get_event_loop()
                                    result = loop.run_until_complete(tool_func(**func_args))
                                else:
                                    result = tool_func(**func_args)
                                
                                # Standardize result format
                                if isinstance(result, dict) and "success" in result:
                                    formatted_result = result
                                else:
                                    formatted_result = {
                                        "success": True,
                                        "data": result,
                                        "error": None
                                    }
                                
                                logger.info(f"Tool {func_name} result: {formatted_result}")
                                messages.append({
                                    "role": "tool",
                                    "content": json.dumps(formatted_result),
                                    "tool_call_id": tool_call.id
                                })
                                
                            except Exception as e:
                                logger.error(f"Error in tool {func_name}: {str(e)}")
                                messages.append({
                                    "role": "tool",
                                    "content": json.dumps({
                                        "success": False,
                                        "data": None,
                                        "error": str(e)
                                    }),
                                    "tool_call_id": tool_call.id
                                })
                
                gpt_calls += 1
                
            except Exception as e:
                logger.error(f"Error in execute_task: {str(e)}")
                break
        
        # Log if we hit the max calls limit
        if gpt_calls >= self.max_gpt_calls:
            logger.warning(f"Task exceeded maximum GPT calls limit ({self.max_gpt_calls})")
    
        # Sleep if frequency is specified
        if 'frequency' in task:
            minutes = task['frequency']
            logger.info(f"Sleeping for {minutes} minutes")
            time.sleep(minutes * 60)

    def run(self):
        """Main execution loop for the agent."""
        while True:
            for task in self.config['tasks']:
                try:
                    self.execute_task(task)
                except Exception as e:
                    logger.error(f"Error in run loop: {str(e)}")
                    # Sleep briefly before retrying on error
                    time.sleep(5)
                    continue

def main():
    parser = argparse.ArgumentParser(description='Run an AI agent with specified configuration')
    parser.add_argument('--agent', type=str, default=DEFAULT_AGENT_CONFIG_PATH,
                      help='Path to agent configuration file')
    args = parser.parse_args()
    
    try:
        # Create and run agent
        agent = AgentRunner(args.agent)
        agent.run()
    except KeyboardInterrupt:
        logger.info("Shutting down agent...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()