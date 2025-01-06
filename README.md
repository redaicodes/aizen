<div align="center">

# Aizen: Web3 Agents with Powerful Tools & Real-Time Data

[![PyPI version](https://badge.fury.io/py/aizen.svg)](https://badge.fury.io/py/aizen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Create, deploy, and scale autonomous Web3 agents with unlimited access to protocols and tools.

[Documentation](https://docs.aizen.ai) | [Examples](./examples) | [Contributing](./CONTRIBUTING.md)

</div>

## Why Tools & Data Matter

Autonomous agents are only as capable as the tools they can use and the data they can access. Aizen provides:

- **Tools for Action**: Enabling agents to interact with protocols, analyze market conditions, and execute strategies
- **Real-Time Data**: Providing agents with current information to make informed decisions
- **Extensible Design**: Easily add new capabilities as the Web3 ecosystem evolves

## Key Features

### Powerful Tool System
```python
from aizen.tools import BaseTool
from transformers import pipeline

class SentimentTool(BaseTool):
    def __init__(self):
        self.model = pipeline("sentiment-analysis")
        
    async def run(self, text: str):
        return await self.model(text)

# Register custom tool
agent.register_tool("sentiment", SentimentTool())
```

### Protocol Integration Tools
```
Trading          Lending      Derivatives
├─ Uniswap      ├─ Aave      ├─ dYdX
├─ Curve        ├─ Compound   ├─ GMX
└─ Balancer     └─ Spark     └─ Perpetual
```

### Social Integration

Agents can interact with and collect data from major social platforms:

#### Discord
```python
from aizen.tools import DiscordTool

# Monitor and interact with Discord
agent.register_tool("discord", DiscordTool(
    channels=["defi", "governance"],
    actions=["read", "write", "react"]
))
```
- Server monitoring
- Channel interactions
- Governance participation
- Event notifications

#### Twitter/X
```python
from aizen.tools import TwitterTool

# Real-time Twitter analysis
agent.register_tool("twitter", TwitterTool(
    track_keywords=["DeFi", "Airdrop"],
    monitor_accounts=["@ethereum", "@uniswap"]
))
```
- Sentiment analysis
- Trend monitoring
- Network analysis

#### Telegram
```python
from aizen.tools import TelegramTool

# Telegram group management
agent.register_tool("telegram", TelegramTool(
    groups=["trading_signals", "alpha"],
    bot_token="YOUR_BOT_TOKEN"
))
```
- Group monitoring
- Message broadcasting
- Alert systems

### Advanced Capabilities
- **Web Automation**: 
  - Playwright for complex web interactions
  - Automated form filling
  - Dynamic content extraction

- **Data Processing**: 
  - DOM parsing (lxml)
  - PDF processing
  - Image analysis
  - Structured data extraction

- **Machine Learning**:
  - Sentiment analysis
  - Price prediction
  - Pattern recognition
  - Anomaly detection

- **Market Analysis**:
  - Technical indicators
  - Statistical analysis
  - Backtesting
  - Risk assessment

### Data Access
```
On-Chain        Off-Chain         Social
├─ DeFi Stats   ├─ Crypto News   ├─ Twitter
├─ DEX Metrics  ├─ Market Data   ├─ Discord
└─ Protocol TVL └─ Research      └─ Telegram
```

### Deployment Options
```
Ethereum    L2s        Sidechains
├─ Mainnet  ├─ Arbitrum  ├─ Polygon
├─ Goerli   ├─ Optimism  ├─ BSC
└─ Sepolia  └─ Base      └─ Avalanche
```

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from aizen.agents import BaseAgent, AgentConfig
from aizen.tools import (
    UniswapTool, 
    PlaywrightTool, 
    DataTool,
    MLTool
)

# Initialize agent with multiple capabilities
agent = BaseAgent(
    config=AgentConfig(
        name="research_trader",
        chain_id=1
    ),
    llm_callback=your_llm_function
)

# Add trading capabilities
agent.register_tool("uniswap", UniswapTool(
    router="0x...",
    private_key="0x..."
))

# Add web automation
agent.register_tool("browser", PlaywrightTool())

# Add ML capabilities
agent.register_tool("ml", MLTool(model_path="..."))

# Add social monitoring
agent.register_tool("discord", DiscordTool())
agent.register_tool("twitter", TwitterTool())
agent.register_tool("telegram", TelegramTool())

# Launch agent
await agent.run({
    "task": "Research and trade new DeFi protocols"
})
```

## Social Integration Example
```python
async def monitor_social_signals():
    # Multi-platform monitoring
    discord_feed = agent.tools["discord"].monitor_channels()
    twitter_feed = agent.tools["twitter"].track_mentions()
    telegram_feed = agent.tools["telegram"].get_messages()

    # Unified analysis
    signals = await asyncio.gather(
        discord_feed,
        twitter_feed,
        telegram_feed
    )
    
    # Process and act on signals
    await agent.analyze_social_sentiment(signals)
```

## Deploy On-Chain

Deploy agents as tokenized entities on any EVM chain:

```python
from aizen.deployment import AgentDeployer

deployment = await AgentDeployer.deploy(
    chain="ethereum",
    agent=agent,
    token_config={
        "name": "Research Agent",
        "symbol": "RAID",
        "initial_supply": 1_000_000
    }
)
```

## Why Python?

Modern AI development is Python-centric:
- Major AI frameworks (PyTorch, TensorFlow)
- LLM integrations (OpenAI, Anthropic)
- Data science ecosystem (pandas, numpy)
- Extensive ML/AI tools and libraries
- Rich Web3 development tools

Aizen bridges this AI ecosystem with Web3 capabilities.

## Architecture

Aizen is built for extensibility and performance:
- Tool-based architecture for easy capability addition
- Async-first design for optimal performance
- Strong typing with Pydantic
- Comprehensive logging and monitoring
- Built-in security features
- Modular plugin system
- Real-time event processing
- Cross-platform integration

## Documentation

Visit [docs.aizen.ai](https://docs.aizen.ai) for:
- Detailed guides
- API reference
- Example agents
- Custom tool creation
- Best practices
- Security guidelines
- Social integration setup
- Protocol integration guides

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Coding standards
- Testing guidelines
- Tool creation guide
- Security policies

## License

MIT License - see [LICENSE](LICENSE)
