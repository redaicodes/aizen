<div align="center">
  <img src="./docs/assets/aizen_logo.png" width="50%">

  AI agents with superpowers - talk is good, action is better
  
  [![PyPI version](https://img.shields.io/pypi/v/aizen-agents?color=blue&style=for-the-badge)](https://pypi.org/project/aizen-agents/)
  [![Python version](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg?style=for-the-badge)](https://redaicodes.github.io/aizen)
</div>

---

**Documentation**: <a href="https://redaicodes.github.io/aizen" target="_blank">https://redaicodes.github.io/aizen</a>

**Source Code**: <a href="https://github.com/redaicodes/aizen" target="_blank">https://github.com/redaicodes/aizen</a>

---

  
## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [The Next Generation of AI Agents](#the-next-generation-of-ai-agents)
- [Platform Goals](#-platform-goals)
- [What makes Aizen Agents the Best](#what-makes-aizen-agents-the-best)
- [Key Features](#key-features)
- [Real-World Examples](#real-world-examples)
- [Why Python? The Perfect Fit for Our Platform](#why-python-the-perfect-fit-for-our-platform)
- [Upcoming Features: Building the Ultimate AI Agent Framework](#-upcoming-features-building-the-ultimate-ai-agent-framework)
- [Contributing](#contributing)
- [License](#license)

## Installation

```bash
pip install aizen-agents
```
>Warning: there are well documented issues of using playwright sync within asyncio loop on Windows: https://github.com/microsoft/playwright-python/issues/462. It's recommened to use Linux or MacOS

## Quick Start

### Users

1. Create `.env` file and fill in your OPENAI_API_KEY (Other values are optional depending on agent config, in the upcoming example we'd be using BSC_PRIVATE_KEY to make the agent trade with its own wallet)
```
OPENAI_API_KEY=
TWITTER_USERNAME=
TWITTER_PASSWORD=
BSC_PRIVATE_KEY=
```
2. Create an agent config file: `agent.json`
```json
{
    "name": "CryptoTrader",
    "tools": ["blockworks__get_latest_news", "bscclient__transfer", "bscclient__transfer_token", "bscclient__swap"],
    "system_prompt": "You are CryptoTrader, a seasoned crypto market strategist with an analytical mindset and a knack for spotting trading opportunities. Your personality combines data-driven insights with practical trading wisdom, making complex market dynamics accessible to traders of all levels.",
    "tasks": [
        {
            "prompt": "Fetch the latest news about crypto and if it is positive, I want you to swap 0.01 usdt with bnb, otherwise if negative then swap 0.0005 bnb with usdt",
            "frequency": 60
        }
    ]
}
```
3. Create a python file to run the agent:
```python
from aizen.agents.agentrunner import AgentRunner

agent = AgentRunner(config="agent.json", max_gpt_calls=5)
agent.run()
```
That's it! Your agent will now do the following every 60 mins:
- Use the `blockworks__get_latest_news` tool to get the latest news from Blockworks
- Using the LLM, summarize the most important developments and identify market sentiment
- Either buy or sell BNB from the wallet based on market sentiment

> [!NOTE]
> The agent comes up with the entire action plan based on the task and availability of tools. Tasks can be extremely complex and the agent would still work

### Contributors

1. Clone the repo: `git clone https://github.com/redaicodes/aizen.git`
2. Navigate to the repo: `cd aizen`
3. Create environment file: `cp .env.example .env` and fill in your OPENAI_API_KEY, TWITTER_USERNAME, TWITTER_PASSWORD and BSC_PRIVATE_KEY
4. Create your specialized tools as Python class within `src/aizen`
5. Define agent in a json file: `agent.json` with the right tools
6. Run the agent locally: `python run.py --agent agent.json --max_gpt_calls 5` 

##  The Next Generation of AI Agents  
We admire Eliza and Zerepy for pioneering autonomous Web3 AI agents, focusing on social interaction across platforms. However, the next generation of AI models must be more than just talkers—they need to plan and take action.  

**DeFAI (Decentralized Financial AI)** is about making AI active participants in DeFi ecosystems. These agents will generate yield, manage lending, provide liquidity, and optimize strategies for profitable financial participation. Their ability to automate complex financial operations can significantly expand market efficiency and accessibility.  

**DeScAI (Decentralized Scientific AI)** will transform how innovation happens. These models won't just summarize papers—they'll analyze research, propose novel ideas, run experiments, validate results, secure funding, and launch new protocols. By taking on end-to-end scientific processes, they can drive discovery at an unprecedented scale.  

Both DeFAI and DeScAI mark a shift from passive models to active agents capable of meaningful, autonomous contribution. This isn't just an upgrade—it's a transformation with outsized importance, as these agents won't just assist but directly impact financial markets and scientific progress.
These agents would need access to advanced tools like:

- 📊 **Data Retrievers:** Real-time data from APIs and sites like *Blockworks, Defillama, The Block, VC websites, X*, and more.  
- 🧮 **Mathematical Tools:** Perform complex calculations with high reliability.  
- 🤖 **Machine Learning Frameworks:** Solve problems using multiple ML models.  
- 🔗 **Onchain Tools:** Query onchain data, interact with smart contracts, and swap tokens.  
- 📣 **Social Interaction Tools:** Engage on platforms like *X, TikTok, Instagram*, and others.

## 🎯 **Platform Goals**
Aizen is **the** best platform for creating the next generation of smart agents. It's a **unified platform** empowering both builders and users! 🚀   

**🛠️ For Builders:**  Easily create Python-based tools and share them with the community. THese tools can be used by agents based on their planning  
**💡 For Users:** Launch powerful AI agents using **English** as your programming language

## What makes Aizen Agents the Best
>"A goal without a plan is just a wish." – Antoine de Saint-Exupéry

**It's All About the Complexity They Can Handle.**  

Aizen agents break complex tasks into smaller, manageable steps based on available tools. They don’t just plan—they execute, adjust when necessary, report success and failure, and provide proof of work every step of the way. Here's a diagram that illustrates how Aizen agents continuously plan, execute, adapt, and validate results throughout a task's lifecycle:

```mermaid
graph TD
    U[User Requests Task] --> A[Identify Tools & Plan Steps]
    A --> B[Execute Steps]
    B --> C{Task Complete?}
    C -->|Yes| D[Report Success & Proof of Work]
    C -->|No| E[Adjust Plan & Retry]
    E --> B
    D --> U
```

## Key Features  

Our library is designed with simplicity, efficiency, and developer experience in mind. Here’s what sets it apart:  

- **Minimal Boilerplate:** Write clean and concise code without unnecessary complexity, allowing you to focus on building functionality rather than setting up repetitive scaffolding.  

- **Smaller Codebase:** A lean and efficient codebase ensures easier navigation, quicker understanding, and reduced maintenance overhead.  

- **Minimally Restrictive:** Provides flexibility to adapt and integrate seamlessly into various workflows, giving developers the freedom to use it their way.  

- **Ease of Use:** Designed for simplicity and rapid learning. Spend less time reading documentation and more time building, thanks to intuitive APIs and clear examples.  

- **Robust Production-Ready Code:** Get features that are ready for deployment, including automatic generation of **interactive documentation** to streamline your development and collaboration processes.  

- **Exceptional Logging:** Advanced logging capabilities make error tracking straightforward, providing comprehensive tools to debug efficiently and ensure reliability in production environments.  

This library is built to save time, simplify processes, and deliver high-quality outcomes.  

## Real-World Examples

Aizen agents are powered by LLMs that follow natural language instructions to perform complex tasks. Here's a real example of a market analysis agent that processes news and provides trading recommendations:

### Market Analysis Agent

```python
{
  "name": "CryptoMarketAnalyst",
  "tools": [
    "theblock__get_latest_news",
    "blockworks__get_latest_news",
    "twitterclient"
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

The agent uses natural language instructions for analysis:

Using the agent is straightforward:

```python
async def main():
    from aizen.agents import AgentRunner

    # Initialize with above JSON file/variable
    agent = AgentRunner("config/crpto_market_analyst.json", max_gpt_calls=10)

    # Run the agent
    agent.run()
```

Sample output:
```
2025-01-14 08:11:06,390 - AgentRunner - INFO - Sending last message to GPT: {
  "role": "user",
  "content": "You are a crypto market analyst.\n1. Get the latest crypto news articles\n2. Search for relevant tweets about major cryptocurrencies\n3. Create a concise summary of market conditions\n4. Determine overall sentiment (Bullish/Neutral/Bearish)\n5. Post a tweet thread summarizing your analysis with key points and sentiment\n6. Monitor and engage with responses to your thread"
}
2025-01-14 08:11:08,786 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-01-14 08:11:08,799 - AgentRunner - INFO - GPT Response: No content
2025-01-14 08:11:08,800 - AgentRunner - INFO - Tool Calls in Response:
2025-01-14 08:11:08,800 - AgentRunner - INFO -   - Tool: theblock__get_latest_news
2025-01-14 08:11:08,800 - AgentRunner - INFO -     Args: {"topk": 5}
2025-01-14 08:11:08,800 - AgentRunner - INFO -   - Tool: blockworks__get_latest_news
2025-01-14 08:11:08,800 - AgentRunner - INFO -     Args: {"topk": 5}
2025-01-14 08:11:08,800 - AgentRunner - INFO -   - Tool: twitterclient__search_tweets
2025-01-14 08:11:08,800 - AgentRunner - INFO -     Args: {"query": "Bitcoin OR Ethereum OR Solana OR Cardano", "tweet_type": "Latest", "limit": 5}

2025-01-14 08:11:54,410 - AgentRunner - INFO - GPT Response: 
### Latest Crypto News Articles

1. **[Semler Scientific expands bitcoin holdings to 2,321 BTC with latest $23 million purchase](https://www.theblock.co/post/334403/semler-scientific-expands-bitcoin-holdings-to-2321-btc)** - Jan 14, 2025
   ![thumbnail](https://www.tbstat.com/cdn-cgi/image/format=avif,q=50/wp/uploads/2023/12/20231204_BitcoinMining_News-1200x675.jpg)

2. **[Sygnum Bank achieves Unicorn status following $58 million funding round to expand Bitcoin focus](https://www.theblock.co/post/334255/sygnum-bank-unicorn-status-funding-round-bitcoin)** - Jan 14, 2025
   ![thumbnail](https://www.tbstat.com/cdn-cgi/image/format=avif,q=50/wp/uploads/2024/07/20240729_Funding_News_3-1200x675.jpg)

3. **[Japan’s Remixpoint buys 33.3 additional bitcoin, boosting holdings to nearly $32 million](https://www.theblock.co/post/334405/japans-remixpoint-buys-33-3-additional-bitcoin-boosting-holdings-to-nearly-32-million)** - Jan 14, 2025
   ![thumbnail](https://www.tbstat.com/cdn-cgi/image/format=avif,q=50/wp/uploads/2019/06/japan-flag-building-1200x675.jpg)

### Additional Crypto News

1. **[MoonPay acquires Solana startup to grow payments services](https://www.blockworks.co/news/moonpay-acquires-solana-payments-startup)** - Jan 13, 2025
2. **[Bitcoin ETFs: Better year or sophomore slump?](https://www.blockworks.co/news/bitcoin-etf-adoption-outlook)** - Jan 13, 2025
3. **[Tis the season for campaign promises follow-throughs](https://www.blockworks.co/news/trump-campaign-promises-bitcoin-reserve)** - Jan 13, 2025
4. **[AI agent sector suffers 44% market cap wipeout](https://www.blockworks.co/news/ai-agent-market-wipeout)** - Jan 13, 2025

### Relevant Tweets about Major Cryptocurrencies

1. **Tweet by @Solig_18**: "the terminal evolves with precision...mastering the layers of complexity."
2. **Tweet by @RARE TRADING SIGNALS**: "Bitcoin Fear and Greed Index"

### Market Summary and Sentiment
Current market conditions show bullish activity in Bitcoin with significant institutional purchases and ETF discussions. The overall sentiment appears **Bullish**, supported by positive institutional movement and new technology implementations.

### Posting the Tweet Thread
Now I will post a tweet thread summarizing my analysis with key points and sentiment.
2025-01-14 08:11:54,410 - AgentRunner - INFO - Tool Calls in Response:
2025-01-14 08:11:54,410 - AgentRunner - INFO -   - Tool: twitterclient__post_tweet
2025-01-14 08:11:54,410 - AgentRunner - INFO -     Args: {"text":"🧵 [Thread]: Crypto Market Analysis Today (Jan 14, 2025)\n\n1/5 🚀 The market is seeing significant bullish momentum, especially for Bitcoin, with institutions increasing their holdings.\n\n2/5 🌐 Semler Scientific expands its Bitcoin holdings by purchasing an additional 2,321 BTC worth $23 million. Strong signal of institutional interest!\n\n3/5 💼 Sygnum Bank achieves unicorn status through a $58 million funding round, emphasizing the growing traction of Bitcoin in finance.\n\n4/5 🔍 Overall, sentiment remains optimistic with new tech innovations, like Sony's Soneium blockchain launch and a notable acquisition by MoonPay.\n\n5/5 📈 The overall sentiment is Bullish! Stay tuned for more updates and analysis."}

2025-01-14 08:11:54,411 - TwitterClient - INFO - Tweet posted successfully with ID: 1879073...
```

### Other Agent Examples

Aizen enables creating various specialized agents like:

- **Trading Agents**: Execute trades based on technical indicators, news sentiment, and on-chain data
- **Governance Agents**: Monitor and participate in DAO governance across protocols
- **Liquidity Management Agents**: Optimize liquidity provision across DEXs using ML-driven strategies
- **MEV Agents**: Identify and capture MEV opportunities while protecting user transactions
- **Research Agents**: Generate in-depth analysis combining on-chain data with market research

## Why Python? The Perfect Fit for Our Platform  

Python is the **leading language for scientific computing and AI**, making it ideal for our platform due to its powerful tools, flexibility, and wide adoption.  

### 🚀 **Proven Scientific Ecosystem**  
- **NumPy, Pandas, Matplotlib:** Data manipulation and visualization.  
- **TensorFlow, Scikit-Learn:** Industry-standard ML frameworks.  

### 🔗 **Seamless Integration & Modularity**  
- **APIs & Web Tools:** FastAPI, Flask.  
- **Blockchain Tools:** Web3.py.  
- **Automation:** Simple scripting with minimal code.  

### 🌍 **Massive Adoption & Community**  
- **450,000+** libraries available via `pip`.  
- **#1** language in TIOBE Index (2024).  
- **10M+** developers worldwide.  

### 🎯 **Why It Matters for Us?**  
- **Plug-and-play tools** for faster development.  
- **Scalable and efficient** for data-intensive tasks.  
- **Minimal setup, maximum flexibility.**  

Python ensures our platform is **powerful, adaptable, and ready for innovation.**  

## 🚀 Upcoming Features: Building the Ultimate AI Agent Framework  

We are developing a **universal AI agent framework** where agents can access **powerful tools** and intelligently use them to complete complex tasks. These agents will be capable of **reasoning, planning, and executing autonomously**, with initial focus areas in **DeFi** and **DeSci**, before expanding into DAOs and the broader Web3 ecosystem.  

☐ Develop **DeFAI tools** for market data fetching, smart contract interaction, and portfolio automation.  
☐ Develop **DeScAI tools** for data labeling, research validation, and decentralized knowledge synthesis.  
☐ Build an **intelligence layer** that breaks tasks into step-by-step execution plans.  
☐ Release a **Python SDK** for developers to build with.  
☐ Develop **DAO tools** for proposal monitoring, treasury management, and sentiment analysis.  
☐ Enable **cross-chain support** for Ethereum, Polygon, Arbitrum, Optimism, and Solana.  
☐ Launch a **drag-and-drop no-code interface** for agent creation and testing.  
☐ Integrate **real-time memory** using vector and temporal databases for long-term context retention.  
☐ Expand **decentralized storage & compute** with IPFS, Arweave, and Akash.  
☐ Build **autonomous agents** capable of multi-agent collaboration and self-improvement.  
☐ Launch **onchain governance** with token incentives for tool creation and platform contributions.  
☐ Create a **self-sustaining, community-driven agent ecosystem**.  

## Contributing

We love contributions! Whether you're fixing bugs, adding features, or improving documentation, check out our [contribution guide](CONTRIBUTING.md).

## License

MIT License - see the [LICENSE](LICENSE) file for details. 

Built with ❤️ by the Aizen team and community
