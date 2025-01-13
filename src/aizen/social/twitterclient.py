# twitterclient.py
from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime
from twikit import Client
import os
from dotenv import load_dotenv, find_dotenv

def format_tweet_object(tweet) -> Dict:
    """Helper function to format a Tweet object into a dictionary."""
    return {
        'id': str(tweet.id),
        'text': str(tweet.text),
        'full_text': str(tweet.full_text) if hasattr(tweet, 'full_text') else str(tweet.text),
        'created_at': str(tweet.created_at),
        'language': str(tweet.lang),
        'user': {
            'id': str(tweet.user.id) if tweet.user else '',
            'username': str(tweet.user.screen_name) if tweet.user else '',
            'name': str(tweet.user.name) if tweet.user else ''
        },
        'engagement': {
            'replies': int(tweet.reply_count),
            'retweets': int(tweet.retweet_count),
            'likes': int(tweet.favorite_count),
            'quotes': int(tweet.quote_count),
            'views': int(tweet.view_count) if tweet.view_count else 0
        },
        'hashtags': tweet.hashtags,
        'urls': tweet.urls,
        'in_reply_to': str(tweet.in_reply_to) if tweet.in_reply_to else None,
        'is_quote': bool(tweet.is_quote_status),
        'quoted_tweet': format_tweet_object(tweet.quote) if tweet.quote else None,
        'retweeted_tweet': format_tweet_object(tweet.retweeted_tweet) if tweet.retweeted_tweet else None,
        'has_media': bool(tweet.media),
        'sensitive': bool(tweet.possibly_sensitive)
    }

class TwitterClient:
    """
    A Twitter client implementation using twikit library.
    Provides functionality for tweeting, searching, and interacting with Twitter's API.
    
    Attributes:
        logger (logging.Logger): Logger instance for the class
        client (Client): twikit Client instance for Twitter API interactions
    
    Required Environment Variables:
        TWITTER_USERNAME: Twitter account username
        TWITTER_EMAIL: Email associated with Twitter account
        TWITTER_PASSWORD: Twitter account password
    """

    def __init__(self, debug_mode: bool = False, language: str = 'en-US'):
        """Initialize Twitter client with credentials and setup logging."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        
        # Get credentials
        load_dotenv(find_dotenv(), override=True)
        username = os.getenv('TWITTER_USERNAME')
        email = os.getenv('TWITTER_EMAIL')
        password = os.getenv('TWITTER_PASSWORD')
        
        # Validate credentials
        if not all([username, email, password]):
            missing = []
            if not username: missing.append("TWITTER_USERNAME")
            if not email: missing.append("TWITTER_EMAIL")
            if not password: missing.append("TWITTER_PASSWORD")
            error_msg = f"Missing Twitter credentials: {', '.join(missing)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Store validated credentials
        self.username = username
        self.email = email
        self.password = password
        
        # Initialize client
        self.client = Client(language)
        
        # Initialize in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Login using the event loop
        try:
            loop.run_until_complete(self._async_init())
            self.logger.info(f"Successfully logged in as user: {self.username}")
            self.logger.info("Twitter client initialized and logged in successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Twitter client: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    async def _async_init(self):
        """Async initialization for the client."""
        await self.client.login(
            auth_info_1=self.username,
            auth_info_2=self.email,
            password=self.password
        )

    async def post_tweet(self, text: str) -> Dict:
        """
        Post a new tweet.
        
        Args:
            text (str): Content of the tweet to post
        
        Returns:
            Dict: A dictionary containing tweet information with full engagement metrics,
                text content, and metadata
        
        Raises:
            Exception: If tweet posting fails
        """
        try:
            tweet = await self.client.create_tweet(text=text)
            self.logger.info(f"Tweet posted successfully with ID: {tweet.id}")
            return format_tweet_object(tweet)
            
        except Exception as e:
            self.logger.error(f"Error posting tweet: {str(e)}")
            raise

    async def reply_to_tweet(self, tweet_id: str, text: str) -> Dict:
        """
        Reply to an existing tweet.
        
        Args:
            tweet_id (str): ID of the tweet to reply to
            text (str): Content of the reply tweet
        
        Returns:
            Dict: A dictionary containing tweet information with full engagement metrics,
                text content, and metadata
        
        Raises:
            Exception: If reply posting fails
        """
        try:
            tweet = await self.client.create_tweet(
                text=text,
                reply_to=tweet_id
            )
            self.logger.info(f"Reply tweet posted successfully for tweet {tweet.id}")
            return format_tweet_object(tweet)
            
        except Exception as e:
            self.logger.error(f"Error posting reply: {str(e)}")
            raise

    async def quote_tweet(self, tweet_id: str, username: str, text: str) -> Dict:
        """
        Quote an existing tweet with additional text.
        
        Args:
            tweet_id (str): ID of the tweet to quote
            username (str): Twitter username of the original tweet author
            text (str): Text to add to the quote tweet
        
        Returns:
            Dict: A dictionary containing tweet information with full engagement metrics,
                text content, and metadata including the quoted tweet
        
        Raises:
            Exception: If quote tweet posting fails
        """
        try:
            # Construct the tweet URL from the ID
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            
            tweet = await self.client.create_tweet(
                text=text,
                attachment_url=tweet_url
            )
            print(tweet)
            self.logger.info(f"Quote tweet posted successfully for tweet {tweet.id}")
            return format_tweet_object(tweet)
            
        except Exception as e:
            self.logger.error(f"Error posting quote tweet: {str(e)}")
            raise

    async def search_tweets(self, query: str, tweet_type: str = 'Latest', limit: int = 100) -> List[Dict]:
        """
        Search for tweets matching a query.
        
        Args:
            query (str): Search query string
            tweet_type (str): Type of tweets to search ('Latest' or 'Top')
            limit (int): Maximum number of tweets to return
        
        Returns:
            List[Dict]: List of tweets with full metadata and engagement metrics
        
        Raises:
            Exception: If search operation fails
        """
        try:
            tweets = await self.client.search_tweet(query, tweet_type)
            
            formatted_tweets = []
            for tweet in tweets[:limit]:
                formatted_tweets.append(format_tweet_object(tweet))
            
            self.logger.info(f"Found {len(formatted_tweets)} tweets matching query")
            return formatted_tweets
                
        except Exception as e:
            self.logger.error(f"Error searching tweets: {str(e)}")
            raise

    async def get_user_tweets(self, user_id: str, tweet_type: str = 'Tweets', limit: int = 100) -> List[Dict]:
        """
        Get recent tweets from a specific user.
        
        Args:
            user_id (str): Twitter user ID
            tweet_type (str): Type of tweets to fetch ('Tweets', 'Replies', etc.)
            limit (int): Maximum number of tweets to return
        
        Returns:
            List[Dict]: List of tweets with full metadata and engagement metrics
        
        Raises:
            Exception: If fetching tweets fails
        """
        try:
            tweets = await self.client.get_user_tweets(user_id, tweet_type)
            
            formatted_tweets = []
            for tweet in tweets[:limit]:
                formatted_tweets.append(format_tweet_object(tweet))
            
            self.logger.info(f"Retrieved {len(formatted_tweets)} tweets from user {user_id}")
            return formatted_tweets
                
        except Exception as e:
            self.logger.error(f"Error fetching tweets for {user_id}: {str(e)}")
            raise

    async def get_trends(self) -> List[Dict]:
        """
        Get current trending topics on Twitter.
        
        Returns:
            List[Dict]: List of trending topics with format:
            {
                'name': str,
                'tweet_count': int
            }
        
        Raises:
            Exception: If fetching trends fails
        """
        try:
            trends = await self.client.get_trends('trending')
            return [{
                'name': str(trend.name), 
                'tweet_count': 0
            } for trend in trends]
        except Exception as e:
            self.logger.error(f"Error getting trends: {str(e)}")
            raise