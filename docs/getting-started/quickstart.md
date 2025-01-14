# Quick Start Guide

## Creating Your First Agent

1. Create an agent config file: `agent.json`

```json
{
    "name": "CryptoTrader",
    "tools": [
        "blockworks__get_latest_news",
        "bscclient__transfer",
        "bscclient__transfer_token",
        "bscclient__swap"
    ],
    "system_prompt": "You are CryptoTrader, a seasoned crypto market strategist with an analytical mindset and a knack for spotting trading opportunities. Your personality combines data-driven insights with practical trading wisdom, making complex market dynamics accessible to traders of all levels.",
    "tasks": [
        {
            "prompt": "Fetch the latest news about crypto and if it is positive, I want you to swap 0.01 usdt with bnb, otherwise if negative then swap 0.0005 bnb with usdt",
            "frequency": 60
        }
    ]
}
```

2. Create a Python file to run the agent:

```python
from aizen.agents.agentrunner import AgentRunner

agent = AgentRunner(config="agent.json", max_gpt_calls=5)
agent.run()
```

That's it! Your agent will now:

-   Use the `blockworks__get_latest_news` tool to get the latest news
-   Using the LLM, summarize developments and identify market sentiment
-   Either buy or sell BNB from the wallet based on market sentiment

## Note on Task Complexity

The agent comes up with the entire action plan based on the task and availability of tools. Tasks can be extremely complex and the agent would still work effectively by breaking them down into manageable steps.
