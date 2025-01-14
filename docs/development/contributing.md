# Contributing to Aizen

We love contributions! Whether you're fixing bugs, adding features, or improving documentation, your help is welcome.

## Getting Started

1. Clone the repo:

```bash
git clone https://github.com/redaicodes/aizen.git
```

2. Navigate to the repo:

```bash
cd aizen
```

3. Create environment file:

```bash
cp .env.example .env
```

4. Fill in your credentials:

```bash
OPENAI_API_KEY=
TWITTER_USERNAME=
TWITTER_PASSWORD=
BSC_PRIVATE_KEY=
```

## Development

1. Create your specialized tools as Python class within `src/aizen`
2. Define agent in a json file: `agent.json` with the right tools
3. Run the agent locally:

```bash
python run.py --agent agent.json --max_gpt_calls 5
```

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Built with ❤️ by the Aizen team and community
