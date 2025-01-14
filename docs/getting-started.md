# Getting Started with Aizen

## Installation

### Prerequisites

-   Python 3.8 or later
-   pip package manager

### Basic Setup

```bash
pip install aizen-agents
```

!!! warning "Windows Compatibility"
There are well documented issues of using playwright sync within asyncio loop on Windows.
See [the GitHub issue](https://github.com/microsoft/playwright-python/issues/462) for more details.
It's recommended to use Linux or MacOS.

### Environment Configuration

Create a `.env` file and add your API keys:

```bash
# Required
OPENAI_API_KEY=your-key-here

# Optional (depending on your agent configuration)
TWITTER_USERNAME=
TWITTER_PASSWORD=
BSC_PRIVATE_KEY=
```

## Quick Start Guide

### For Users

1. Create an agent configuration file `agent.json`:

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

2. Create and run your agent:

```python
from aizen.agents import AgentRunner

agent = AgentRunner(config="agent.json", max_gpt_calls=5)
agent.run()
```

That's it! Your agent will now:

-   Fetch latest news from Blockworks
-   Analyze market sentiment using LLM
-   Execute trades based on sentiment analysis

!!! note "Task Complexity"
The agent comes up with the entire action plan based on the task and availability of tools.
Tasks can be extremely complex and the agent would still work effectively.

### For Contributors

1. Clone and setup:

```bash
git clone https://github.com/redaicodes/aizen.git
cd aizen
cp .env.example .env  # Then add your API keys
```

2. Create tools:

-   Add your specialized tools as Python classes within `src/aizen`
-   Define agent configurations in JSON format
-   Test locally: `python run.py --agent agent.json --max_gpt_calls 5`

## Key Features

### Minimal Boilerplate

Write clean and concise code without unnecessary complexity, allowing you to focus on building functionality rather than setting up repetitive scaffolding.

### Production Ready

-   Robust logging capabilities
-   Comprehensive error tracking
-   Built-in reliability features
-   Detailed debug information

### Flexible Integration

-   Easy tool registration
-   Customizable agent behaviors
-   Extensible architecture
-   Plugin system support
