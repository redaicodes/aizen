from .agentrunner import AgentRunner
import json
import os

def _load_json(filename):
    """Load a JSON config file from the configs directory."""
    path = os.path.join(os.path.dirname(__file__), 'configs', filename)
    with open(path, 'r') as f:
        return json.load(f)

# Expose sample configurations as module-level variables
TWITTER_AGENT_CONFIG = _load_json('cryptoecho.agent.json')
NEWS_AGENT_CONFIG = _load_json('cryptopulse.agent.json')
TRADING_AGENT_CONFIG = _load_json('cryptotrader.agent.json')

__all__ = [
    'AgentRunner',
    'NEWS_AGENT_CONFIG',
    'TRADING_AGENT_CONFIG',
    'TWITTER_AGENT_CONFIG'
]