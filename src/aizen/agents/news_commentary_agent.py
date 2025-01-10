from typing import Dict, List
import aiohttp
import json
from datetime import datetime
from aizen.agents.base import BaseAgent, AgentConfig
from aizen.data.news.blockworks import Blockworks
from aizen.data.news.theblock import TheBlock


class NewsCommentaryAgent(BaseAgent):
    """
    Agent that fetches crypto news and generates market summaries with token recommendations.
    """

    def __init__(self, config: AgentConfig, openai_api_key: str):
        """
        Initialize NewsCommentaryAgent.

        Args:
            config: AgentConfig instance
            openai_api_key: OpenAI API key for GPT access
        """
        super().__init__(config)
        self.openai_api_key = openai_api_key

        # Initialize news sources
        self.register_tool_class("theblock", TheBlock,
                                 debug_mode=config.debug_mode)
        self.register_tool_class(
            "blockworks", Blockworks, debug_mode=config.debug_mode)

        # Register analysis tool
        self.register_tool("analyze_market", self._analyze_market)

    async def _call_gpt(self, messages: List[Dict]) -> str:
        """
        Make an API call to GPT with error handling.

        Args:
            messages: List of message dictionaries for GPT

        Returns:
            str: GPT's response text

        Raises:
            Exception: If API call fails or response is invalid
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "temperature": 0.7
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"GPT API error: {error_text}")
                        raise Exception(f"GPT API returned status {
                                        response.status}: {error_text}")

                    result = await response.json()

                    # Log the raw response for debugging
                    self.logger.debug(f"Raw GPT response: {result}")

                    if 'error' in result:
                        raise Exception(f"GPT API error: {result['error']}")

                    if 'choices' not in result or not result['choices']:
                        raise Exception("No choices in GPT response")

                    if 'message' not in result['choices'][0]:
                        raise Exception("No message in GPT response choice")

                    if 'content' not in result['choices'][0]['message']:
                        raise Exception("No content in GPT response message")

                    return result['choices'][0]['message']['content']

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error calling GPT API: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding GPT API response: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error in GPT API call: {str(e)}")
            raise

    async def _analyze_market(self, articles: List[Dict]) -> Dict:
        """
        Analyze news articles and generate market summary with token recommendations.

        Args:
            articles: List of news articles

        Returns:
            Dict containing market summary, sentiment, and token recommendations
        """
        # Prepare articles for analysis
        article_texts = []
        for idx, article in enumerate(articles, 1):
            article_texts.append(
                f"Article {idx}:\n"
                f"Headline: {article['headline']}\n"
                f"Description: {article.get('description', 'N/A')}\n"
                f"Published: {article.get('metadata', 'N/A')}\n"
            )

        # Create prompt for GPT
        system_prompt = """You are a crypto market analyst. Based on the provided news articles:
1. Create a concise one-paragraph summary of current market conditions and major events
2. Determine overall market sentiment (Bullish/Neutral/Bearish)
3. If there's a clear opportunity, recommend ONE token to buy with a brief reason. If no clear buy opportunity exists, state "No clear buy recommendation at this time."
4. If there's a clear risk, recommend ONE token to sell with a brief reason. If no clear sell opportunity exists, state "No clear sell recommendation at this time."

Keep each point brief but informative. Only make token recommendations if there's strong justification in the news."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(article_texts)}
        ]

        # Get analysis from GPT
        response = await self._call_gpt(messages)

        # Parse response into structured format
        try:
            # Split response into sections
            sections = response.split('\n')

            # Extract information
            market_summary = sections[0].strip()

            # Find sentiment (case insensitive)
            sentiment_markers = ['bullish', 'neutral', 'bearish']
            sentiment = next((s for s in sentiment_markers
                              if s.lower() in response.lower()), 'neutral')

            # Extract token recommendations
            buy_rec = next((s for s in sections if 'buy' in s.lower()),
                           'No clear buy recommendation at this time.')
            sell_rec = next((s for s in sections if 'sell' in s.lower()),
                            'No clear sell recommendation at this time.')

            # Clean up recommendations
            buy_rec = buy_rec.replace('Buy:', '').strip()
            sell_rec = sell_rec.replace('Sell:', '').strip()

            # Check if recommendations are actually present
            if "no clear buy" in buy_rec.lower():
                buy_rec = None
            if "no clear sell" in sell_rec.lower():
                sell_rec = None

            return {
                "timestamp": datetime.now().isoformat(),
                "market_summary": market_summary,
                "sentiment": sentiment.title(),
                "recommendations": {
                    "buy": buy_rec,
                    "sell": sell_rec
                }
            }
        except Exception as e:
            self.logger.error(f"Error parsing GPT response: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "market_summary": response,
                "sentiment": "Neutral",
                "recommendations": {
                    "buy": "Error parsing recommendation",
                    "sell": "Error parsing recommendation"
                }
            }

    async def get_market_analysis(self, num_articles: int = 10) -> Dict:
        """
        Fetch news and generate market analysis with recommendations.

        Args:
            num_articles: Number of articles to analyze from each source

        Returns:
            Dict containing market analysis and recommendations
        """
        try:
            # Fetch news from different sources
            self.logger.info("Fetching news from sources...")
            theblock_news = await self.run_tool("theblock.get_latest_news", topk=num_articles)
            blockworks_news = await self.run_tool("blockworks.get_latest_news", topk=num_articles)

            # Combine articles
            all_articles = theblock_news + blockworks_news

            # Generate market analysis
            self.logger.info("Analyzing market conditions...")
            analysis = await self._analyze_market(all_articles)

            return {
                "analysis": analysis,
                "data_points": len(all_articles),
                "sources": ["TheBlock", "Blockworks"]
            }

        except Exception as e:
            self.logger.error(f"Error in get_market_analysis: {str(e)}")
            raise
