# Installation & Setup

## Basic Installation

```bash
pip install aizen-agents
```

!!! warning
There are documented issues using playwright sync within asyncio loop on Windows.
It's recommended to use Linux or MacOS.
See [Playwright Issue #462](https://github.com/microsoft/playwright-python/issues/462)

## Environment Setup

1. Create `.env` file and fill in your API keys:

```bash
OPENAI_API_KEY=
TWITTER_USERNAME=
TWITTER_PASSWORD=
BSC_PRIVATE_KEY=
```

These values are optional depending on agent config. For example, BSC_PRIVATE_KEY is needed if you want the agent to trade with its own wallet.

## System Requirements

-   Python 3.8+
-   Linux or MacOS recommended
-   pip (Python package installer)

## For Contributors

Clone the repo:

```bash
git clone https://github.com/redaicodes/aizen.git
```

Navigate to the repo:

```bash
cd aizen
```

Create environment file:

```bash
cp .env.example .env
```

Fill in your API keys as described above
