import argparse
import logging

from aizen.agents.agentrunner import AgentRunner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AgentRunner')

DEFAULT_MAX_GPT_CALLS = 5
DEFAULT_AGENT_CONFIG_PATH = "./src/aizen/agents/configs/cryptopulse.agent.json"

def main():
    parser = argparse.ArgumentParser(description='Run an AI agent with specified configuration')
    parser.add_argument('--agent', type=str, default=DEFAULT_AGENT_CONFIG_PATH,
                      help='Path to agent configuration file')
    parser.add_argument('--max_gpt_calls', type=int, default=DEFAULT_MAX_GPT_CALLS,
                      help='Max GPT calls for a particular task')
    args = parser.parse_args()
    
    try:
        # Create and run agent
        agent = AgentRunner(args.agent, args.max_gpt_calls)
        agent.run()
    except KeyboardInterrupt:
        logger.info("Shutting down agent...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()