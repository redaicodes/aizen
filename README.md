<div align="center">
  <img src="./docs/assets/aizen_logo.png" width="50%">
  
  [![PyPI version](https://img.shields.io/pypi/v/aizen?color=blue&style=for-the-badge)](https://pypi.org/project/aizen)
  [![Python version](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg?style=for-the-badge)](https://docs.aizen.io)
  [![Discord](https://img.shields.io/discord/1234567890?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/aizen)
</div>

  
---

Empowering Web3 AI agents with real superpowers - because talking is nice, but doing is better.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [The Problem We're Solving](#the-problem-were-solving)
- [What Makes Aizen Different](#what-makes-aizen-different)
- [Features](#features)
- [Real-World Examples](#real-world-examples)
- [Why Python](#why-python)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Community](#community)
- [License](#license)

## Installation

Getting started is as simple as:

```bash
pip install aizen
```

Need help? Check out our [installation guide](https://docs.aizen.io/installation).

## Quick Start

Create your first AI agent in minutes:

```python
from aizen import Agent
from aizen.tools import ChainTools

# Initialize a basic agent with common tools
agent = Agent(
    name="CryptoWatcher",
    openai_key="your-openai-key",  # For AI capabilities
    wallet_key="your-private-key"   # For on-chain actions
)

# Register tools the agent might need
agent.register_tools([
    ChainTools.Ethereum(),      # Ethereum data and interactions
    ChainTools.PriceFeeds(),    # Price monitoring
    ChainTools.Notifications()  # Alerts and updates
])

# Set up monitoring with natural language
async def main():
    # Tell the agent what to do in plain English
    await agent.execute("""
        Monitor ETH price and volume.
        If any of these happen:
        - Volume increases by 50% in 24h
        - Price drops more than 10% in an hour
        - Large whale wallet moves over 1000 ETH
        Then:
        - Send an alert to Discord
        - If it's a price drop, check social sentiment
        - If sentiment is positive, buy $100 worth of ETH
    """)

# Start the agent
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

That's it! Your agent will now:
- Monitor ETH market conditions
- Send alerts when significant events occur
- Automatically analyze and act on opportunities

Want more advanced features? Visit our [documentation](https://docs.aizen.io) for:
- Trading strategies
- Portfolio management
- MEV protection
- Cross-chain operations
- Custom tool creation

## The Problem We're Solving

Here's a question: Why are most Web3 AI agents today just fancy chatbots? They can talk about blockchain, sure. They might even sound smart. But when it comes to actually doing something meaningful - monitoring real-time data, executing trades, participating in governance - they fall flat.

It's like having a financial advisor who can only read yesterday's newspaper and can't actually make trades for you. Not very useful, right?

The problem isn't with the AI models themselves. The problem is that these agents lack the tools to interact with the real world of Web3. They're like craftsmen without their tools, or artists without their brushes.

## What Makes Aizen Different

Aizen is built on a simple principle: an agent's power comes from its ability to access information and take action. Think of it as giving your AI agents superpowers.

Want an agent that:
- Monitors whale movements across multiple chains and reacts instantly?
- Analyzes governance proposals and votes based on your criteria?
- Tracks specific smart contract events and automatically provides liquidity?
- Combines news sentiment with on-chain data to make trading decisions?

With Aizen, this isn't science fiction - it's just a few lines of code.

## Features

The power of Aizen comes from its ability to understand natural language instructions and automatically choose the right tools for the job. Here's how it works:

### Natural Language Commands

Instead of writing complex code, just tell your agent what you want:

```python
# Create an agent with access to various tools
agent = Agent(
    name="CryptoTrader",
    tools=[
        "news", "dex", "social_sentiment",
        "wallet", "governance", "nft"
    ]
)

# Give instructions in plain English
await agent.execute("""
    If ETH price increases by more than 5% in the last hour 
    and social sentiment is positive, buy $1000 worth of ETH. 
    Also check NFT floor prices and if any blue chips are down >20%, 
    buy the cheapest one.
""")
```

The agent automatically:
1. Picks the right tools for price checking and sentiment analysis
2. Monitors relevant data sources
3. Executes trades when conditions are met

### Composable Tools

Agents can access a growing ecosystem of tools:

```python
# Register available tools
agent.register_tools([
    NewsTools(),          # News and market updates
    DexTools(),           # DEX interactions and pricing
    SocialTools(),        # Social media sentiment
    WalletTools(),        # Wallet operations
    GovernanceTools(),    # DAO participation
    NFTTools()            # NFT market data
])

# Agent automatically picks relevant tools based on the task
await agent.execute("""
    Monitor Uniswap governance.
    If any proposal affects trading fees,
    analyze sentiment from Discord and Twitter.
    If community is positive and price impact looks minimal,
    vote in favor and notify me on Discord.
""")
```

### Built-in Safety

Agents have built-in safety features:
- Transaction simulation before execution
- Slippage protection
- Gas optimization
- Sandwich attack prevention
- Intelligent error handling

For example:
```python
await agent.execute("""
    Find arbitrage opportunities between Uniswap V3 and Sushiswap 
    for the USDC/ETH pair. Execute trades only if:
    - Profit > $100 after gas
    - Slippage < 1%
    - No sandwich attack risk
    Send me a Discord message before executing.
""")
```

### Community-Driven Tool Ecosystem

Anyone can create and share tools:

```python
from aizen import Tool, register

@register("sentiment_analysis")
class CustomSentimentTool(Tool):
    """Analyzes market sentiment from custom data sources"""
    
    async def analyze(self, text: str) -> float:
        # Your custom sentiment analysis logic
        return sentiment_score

# Now other agents can use your tool
await agent.execute("""
    Use the custom sentiment analyzer to check market mood.
    If sentiment is above 0.8, increase ETH position by 10%.
""")
```

## Real-World Examples

Aizen agents are powered by LLMs that follow natural language instructions to perform complex tasks. Here's a real example of a market analysis agent that processes news and provides trading recommendations:

### Market Analysis Agent

```python
from aizen import Agent, AgentConfig
from aizen.tools import NewsTools

class NewsCommentaryAgent(Agent):
    def __init__(self, config: AgentConfig, openai_api_key: str):
        super().__init__(config)
        
        # Initialize news sources
        self.register_tool_class("theblock", NewsTools.TheBlock)
        self.register_tool_class("blockworks", NewsTools.Blockworks)
```

The agent uses natural language instructions for analysis:

```python
system_prompt = """You are a crypto market analyst. Based on the provided news articles:
1. Create a concise summary of current market conditions
2. Determine overall sentiment (Bullish/Neutral/Bearish)
3. Recommend ONE token to buy with reasoning if clear opportunity exists
4. Recommend ONE token to sell with reasoning if clear risk exists"""
```

Using the agent is straightforward:

```python
async def main():
    # Initialize the agent
    config = AgentConfig(
        name="CryptoMarketAnalyst",
        description="Crypto market analysis and token recommendations",
        debug_mode=True
    )
    agent = NewsCommentaryAgent(config, openai_api_key="your-key")

    # Get market analysis
    result = await agent.get_market_analysis(num_articles=10)

    # Print the report
    print("\nMarket Analysis Report")
    print("=====================")
    print(f"\nBased on {result['data_points']} articles from {', '.join(result['sources'])}")
    print(f"\nMarket Summary:")
    print(result['analysis']['market_summary'])
    print(f"\nSentiment: {result['analysis']['sentiment']}")
    
    # Print recommendations
    recs = result['analysis']['recommendations']
    print(f"\nBUY: {recs['buy'] or 'No clear buy recommendation'}")
    print(f"SELL: {recs['sell'] or 'No clear sell recommendation'}")
```

Sample output:
```
Market Analysis Report
=====================

Based on 20 articles from TheBlock, Blockworks

Market Summary:
Bitcoin continues to show strength above $50k with institutional inflows reaching new highs. 
DeFi TVL has grown 20% MoM, led by liquid staking protocols. Layer 2 adoption metrics 
show sustained growth with Arbitrum leading in daily active users.

Sentiment: Bullish

BUY: ARB - Arbitrum's ecosystem growth and increasing revenue metrics suggest undervaluation
SELL: No clear sell recommendation at this time
```

### Other Agent Examples

Aizen enables creating various specialized agents like:

- **Trading Agents**: Execute trades based on technical indicators, news sentiment, and on-chain data
- **Governance Agents**: Monitor and participate in DAO governance across protocols
- **Liquidity Management Agents**: Optimize liquidity provision across DEXs using ML-driven strategies
- **MEV Agents**: Identify and capture MEV opportunities while protecting user transactions
- **Research Agents**: Generate in-depth analysis combining on-chain data with market research


## Why Python

We chose Python for a few simple reasons:

1. It's the language most ML practitioners know and love. Want to add your custom sentiment analysis model? It's just another import.

2. The Python ecosystem is incredible. Need to analyze data? Pandas. Want to add machine learning? PyTorch or TensorFlow. Need to scale? FastAPI or Ray.

3. Most Web3 infrastructure tools have great Python support. Whether you're interacting with nodes, indexers, or APIs, there's probably a Python SDK.

## Roadmap

### Q2 2025: Power Tools
- MEV protection suite: Keep your agents' transactions safe
- Cross-chain arbitrage toolkit: Find opportunities across 20+ chains
- Advanced governance automation: Proposal analysis, voting strategies, delegate management

### Q3 2025: Going Pro
- Private pool trading: Execute trades without frontrunning
- Validator management suite: Run validators across multiple networks
- DAO coordination framework: Manage complex governance operations

### Q4 2025: Next Level
- ZK-proof integration: Privacy-preserving agent operations
- Advanced liquidity optimization: ML-powered liquidity management
- Multi-agent coordination: Create agent networks that work together

## Contributing

We love contributions! Whether you're fixing bugs, adding features, or improving documentation, check out our [contribution guide](CONTRIBUTING.md).

Want to add a new tool? Check out the [tool creation guide](https://docs.aizen.io/tools/creating).

## Community

- Discord: [Join our community](https://discord.gg/aizen)
- Twitter: [@AizenProtocol](https://twitter.com/aizenprotocol)
- Forum: [Discuss ideas](https://forum.aizen.io)

## License

MIT License - see the [LICENSE](LICENSE) file for details. 

Built with ❤️ by the Aizen team and community
