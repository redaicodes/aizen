# Examples & Use Cases

## Market Analysis Agent

Here's a detailed example of a market analysis agent that processes news and provides trading recommendations:

```json
{
  "name": "CryptoMarketAnalyst",
  "tools": [
    "theblock__get_latest_news",
    "blockworks__get_latest_news",
    "twitterclient__search_tweets",
    "twitterclient__post_tweet"
  ],
  "system_prompt": "You are an experienced crypto market analyst with over 10 years of experience in digital assets. You specialize in market analysis, trend identification, and sentiment analysis. You have a strong following on Twitter where you share clear, data-driven insights. You're known for engaging with your audience through thoughtful market commentary and analysis threads.",
  "tasks": [
    {
      "prompt": "You are a crypto market analyst.\n1. Get the latest crypto news articles\n2. Search for relevant tweets about major cryptocurrencies\n3. Create a concise summary of market conditions\n4. Determine overall sentiment (Bullish/Neutral/Bearish)\n5. Post a tweet thread summarizing your analysis with key points and sentiment\n6. Monitor and engage with responses to your thread",
      "frequency": 60
    }
  ]
}
```

### Implementation

```python
from aizen.agents import AgentRunner

# Initialize with market analyst configuration
agent = AgentRunner("config/market_analyst.json", max_gpt_calls=10)

# Run the agent
agent.run()
```

### Sample Output

```
2025-01-14 08:11:06 - INFO - Starting market analysis...
2025-01-14 08:11:08 - INFO - Fetching news from sources...

Latest Crypto News Articles:
1. Semler Scientific expands bitcoin holdings to 2,321 BTC ($23M)
2. Sygnum Bank achieves Unicorn status ($58M funding)
3. Japan's Remixpoint adds 33.3 BTC ($32M holdings)

Market Summary and Sentiment:
Current market conditions show bullish activity in Bitcoin with significant 
institutional purchases and ETF discussions. Overall sentiment: BULLISH

Publishing Analysis on Twitter:
🧵 [Thread]: Crypto Market Analysis Today
1/5 🚀 Significant bullish momentum, institutions increasing holdings...
```

## Other Agent Examples

### Trading Agent

```json
{
  "name": "TradingBot",
  "tools": [
    "bscclient__swap",
    "defillama__get_tvl",
    "theblock__get_latest_news"
  ],
  "system_prompt": "You are a DeFi trading expert focused on identifying market opportunities and executing trades with careful risk management...",
  "tasks": [
    {
      "prompt": "Monitor DEX liquidity and news. If positive sentiment and increasing TVL, swap 0.1 ETH for the token with highest growth...",
      "frequency": 30
    }
  ]
}
```

### Research Agent

```json
{
  "name": "ResearchAnalyst",
  "tools": [
    "theblock__get_latest_news",
    "twitter__search",
    "github__get_commits"
  ],
  "system_prompt": "You are a blockchain research analyst specializing in protocol analysis and development trends...",
  "tasks": [
    {
      "prompt": "Track development activity, social sentiment, and news for major L1/L2 protocols. Generate weekly report...",
      "frequency": 1440
    }
  ]
}
```

### Governance Agent

```json
{
  "name": "DAOMonitor",
  "tools": [
    "snapshot__get_proposals",
    "discord__monitor",
    "twitter__post"
  ],
  "system_prompt": "You monitor DAO governance activities and ensure community engagement...",
  "tasks": [
    {
      "prompt": "Monitor governance proposals, alert on new votes, summarize discussions...",
      "frequency": 120
    }
  ]
}
```

## Best Practices

### Agent Design
1. Clear task definition
2. Appropriate tool selection
3. Personality-driven system prompts
4. Reasonable execution frequency

### Error Handling
1. Validate configurations
2. Monitor tool outputs
3. Implement retries
4. Log all actions

### Performance
1. Optimize API calls
2. Cache results when possible
3. Use appropriate intervals
4. Monitor resource usage