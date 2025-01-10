import argparse
import json
import asyncio
import os
from typing import Dict, List, Any
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from aizen.agents.base import BaseAgent, AgentConfig
from aizen.data.news.blockworks import Blockworks
from aizen.social.twitter_client import TwitterClient

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

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Registry of available tools and their function definitions
TOOL_REGISTRY = {
    "blockworks__get_latest_news": {
        "type": "function",
        "function": {
            "name": "blockworks__get_latest_news",
            "description": "Get latest news articles from Blockworks",
            "parameters": {
                "type": "object",
                "properties": {
                    "topk": {
                        "type": "integer",
                        "description": "Number of articles to fetch"
                    }
                },
                "required": ["topk"]
            }
        }
    },
    "twitter_client__post_tweet": {
        "type": "function",
        "function": {
            "name": "twitter_client__post_tweet",
            "description": "Post a tweet",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Content of the tweet"
                    },
                    "media_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of media URLs to attach"
                    }
                },
                "required": ["text"]
            }
        }
    }
}

class AgentRunner:
    def __init__(self, agent_config: str, task_config: str):
        """Initialize the agent runner with configuration files."""
        self.agent_config = self._load_config(agent_config)
        self.task_config = self._load_config(task_config)
        self.agent = None
        self.conversation_history = []
        self.max_function_calls = 5  # Maximum number of function calls per task

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

    def _convert_function_name(self, func_name: str) -> str:
        """Convert function name from double underscore to dot notation."""
        return func_name.replace("__", ".")

    async def initialize_agent(self):
        """Initialize the agent with specified tools."""
        try:
            # Convert tool names for agent configuration
            config = AgentConfig(
                name=self.agent_config["name"],
                tools=[self._convert_function_name(tool) for tool in self.agent_config["tools"]]
            )
            
            # Initialize agent
            self.agent = BaseAgent(config)
            
            # Register tools based on configuration
            if "blockworks__get_latest_news" in self.agent_config["tools"]:
                self.agent.register_tool_class("blockworks", Blockworks)
            
            if "twitter_client__post_tweet" in self.agent_config["tools"]:
                twitter_client = TwitterClient()
                self.agent.register_tool("twitter_client.post_tweet", twitter_client.post_tweet)

            logger.info(f"Agent {config.name} initialized with tools: {config.tools}")
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            raise

    async def execute_task(self, task: Dict):
        """Execute a single task using OpenAI function calling."""
        try:
            # Reset conversation for new task
            self.conversation_history = [
                {"role": "system", "content": "You are an AI agent that helps with crypto news and social media. Execute the given task using the available tools."}
            ]
            
            # Add task to conversation
            self.conversation_history.append({
                "role": "user", 
                "content": task["prompt"]
            })
            
            # Track function calls
            call_count = 0
            
            while call_count < self.max_function_calls:
                # Log current conversation state
                log_json("Current conversation history", self.conversation_history)
                
                # Call OpenAI API
                logger.info(f"Making OpenAI API call #{call_count + 1}")
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.conversation_history,
                    tools=[TOOL_REGISTRY[tool] for tool in self.agent_config["tools"]]
                )
                
                # Log the complete API response
                log_json("OpenAI API Response", {
                    "id": completion.id,
                    "model": completion.model,
                    "choices": [{
                        "message": {
                            "content": completion.choices[0].message.content,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments
                                    }
                                } for tc in (completion.choices[0].message.tool_calls or [])
                            ]
                        }
                    }]
                })
                
                message = completion.choices[0].message
                
                # Add assistant's message to conversation first
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content if message.content else None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        } for tool_call in (message.tool_calls or [])
                    ]
                })
                
                # If no tool calls, task is complete
                if not message.tool_calls:
                    logger.info("Task completed without additional function calls")
                    break
                
                # Handle each tool call
                for tool_call in message.tool_calls:
                    # Convert function name and execute function call
                    func_name = self._convert_function_name(tool_call.function.name)
                    func_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing function {func_name} with args {func_args}")
                    
                    # Execute the function through the agent using converted name
                    result = await self.agent.run_tool(func_name, **func_args)
                    log_json(f"Function {func_name} result", result)
                    
                    # Add function response to conversation using 'tool' role
                    self.conversation_history.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id
                    })
                    
                    call_count += 1
                
            if call_count >= self.max_function_calls:
                logger.warning("Maximum function calls reached for task")
                
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            raise

    async def run(self):
        """Main loop to run tasks at specified frequencies."""
        await self.initialize_agent()
        
        while True:
            try:
                for task in self.task_config:
                    logger.info(f"Executing task: {task['prompt']}")
                    await self.execute_task(task)
                    
                    # Wait for specified frequency before next execution
                    frequency_minutes = int(task["frequency"])
                    logger.info(f"Waiting {frequency_minutes} minutes before next execution")
                    await asyncio.sleep(frequency_minutes * 60)
                    
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

def main():
    parser = argparse.ArgumentParser(description="Run AI agent with specified configuration")
    parser.add_argument("--agent", required=True, help="Path to agent configuration JSON file")
    parser.add_argument("--task", required=True, help="Path to task configuration JSON file")
    
    args = parser.parse_args()
    
    # Create and run agent
    runner = AgentRunner(args.agent, args.task)
    asyncio.run(runner.run())

if __name__ == "__main__":
    main()