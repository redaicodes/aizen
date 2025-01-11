from typing import Dict, List, Optional, Union
import logging
import asyncio
from datetime import datetime
# from twikit import Twitter
import os
from dotenv import load_dotenv
load_dotenv()

class TwitterClient:
    """
    Twitter integration tool using twikit for unrestricted access without API keys.
    Provides functionality for posting tweets, searching, and monitoring feeds.
    """
    
    def __init__(self,
                 cookies: Optional[Dict] = None,
                 debug_mode: bool = False):
        """
        Initialize Twitter scraper tool.
        
        Args:
            cookies: Twitter cookies for authentication (optional)
            debug_mode: Enable debug logging if True
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        username = os.getenv('TWITTER_USERNAME')
        password = os.getenv('TWITTER_PASSWORD')
        
        # if not self.logger.handlers:
        #     handler = logging.StreamHandler()
        #     formatter = logging.Formatter(
        #         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        #     )
        #     handler.setFormatter(formatter)
        #     self.logger.addHandler(handler)
        
        # self.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        
        # # Initialize Twitter client
        # self.client = Twitter()
        
        # # Login if credentials provided
        # if username and password:
        #     self.client.login(username, password)
        # elif cookies:
        #     self.client.set_cookies(cookies)
            
        self.logger.info("Twitter scraper tool initialized")

    async def post_tweet(self, text: str, media_urls: Optional[List[str]] = None) -> Dict:
        """
        Post a tweet, optionally with media.
        
        Args:
            text: Tweet text content
            media_urls: Optional list of media URLs to attach
            
        Returns:
            Dict containing tweet information
        """
        try:
            # tweet_id = await asyncio.to_thread(
            #     self.client.tweet,
            #     text,
            #     media_urls=media_urls if media_urls else None
            # )
            
            self.logger.info(f"Tweet posted successfully: ")
            return {}
            # return {
            #     'id': tweet_id,
            #     'text': text,
            #     'created_at': datetime.now().isoformat(),
            #     'media_urls': media_urls
            # }
            
        except Exception as e:
            self.logger.error(f"Error posting tweet: {str(e)}")
            raise

    async def search_tweets(self, 
                          query: str,
                          limit: int = 100) -> List[Dict]:
        """
        Search for tweets matching a query.
        
        Args:
            query: Search query string
            limit: Maximum number of tweets to return
            
        Returns:
            List of matching tweet dictionaries
        """
        try:
            tweets = await asyncio.to_thread(
                self.client.search,
                query,
                limit=limit
            )
            
            formatted_tweets = []
            for tweet in tweets:
                formatted_tweets.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'user': {
                        'id': tweet.user.id,
                        'username': tweet.user.username,
                        'name': tweet.user.name
                    },
                    'likes': tweet.likes,
                    'retweets': tweet.retweets,
                    'replies': tweet.replies,
                    'language': tweet.language
                })
            
            self.logger.info(f"Found {len(formatted_tweets)} tweets matching query")
            return formatted_tweets
                
        except Exception as e:
            self.logger.error(f"Error searching tweets: {str(e)}")
            raise

    async def get_user_tweets(self, 
                            username: str,
                            limit: int = 100) -> List[Dict]:
        """
        Get recent tweets from a user.
        
        Args:
            username: Twitter username to fetch tweets from
            limit: Maximum number of tweets to fetch
            
        Returns:
            List of tweet dictionaries
        """
        try:
            tweets = await asyncio.to_thread(
                self.client.user_tweets,
                username,
                limit=limit
            )
            
            formatted_tweets = []
            for tweet in tweets:
                formatted_tweets.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'likes': tweet.likes,
                    'retweets': tweet.retweets,
                    'replies': tweet.replies,
                    'language': tweet.language
                })
            
            self.logger.info(f"Retrieved {len(formatted_tweets)} tweets from user {username}")
            return formatted_tweets
                
        except Exception as e:
            self.logger.error(f"Error fetching tweets for {username}: {str(e)}")
            raise

    async def get_tweet_details(self, tweet_id: str) -> Dict:
        """
        Get detailed information about a specific tweet.
        
        Args:
            tweet_id: ID of tweet to fetch details for
            
        Returns:
            Dict containing tweet details
        """
        try:
            tweet = await asyncio.to_thread(
                self.client.tweet_detail,
                tweet_id
            )
            
            return {
                'id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at.isoformat(),
                'user': {
                    'id': tweet.user.id,
                    'username': tweet.user.username,
                    'name': tweet.user.name
                },
                'likes': tweet.likes,
                'retweets': tweet.retweets,
                'replies': tweet.replies,
                'language': tweet.language,
                'media': tweet.media if hasattr(tweet, 'media') else None,
                'quoted_tweet': tweet.quoted_tweet.id if tweet.quoted_tweet else None,
                'reply_to': tweet.reply_to if hasattr(tweet, 'reply_to') else None
            }
                
        except Exception as e:
            self.logger.error(f"Error getting tweet details for {tweet_id}: {str(e)}")
            raise

    async def monitor_user(self, 
                         username: str,
                         callback: Optional[callable] = None,
                         interval: int = 60,
                         track_metrics: bool = False) -> None:
        """
        Monitor a user's tweets and optionally track metrics over time.
        
        Args:
            username: Username to monitor
            callback: Optional callback function for new tweets
            interval: Polling interval in seconds
            track_metrics: Track follower/following counts if True
        """
        last_tweet_id = None
        metrics_history = [] if track_metrics else None
        
        while True:
            try:
                # Get latest tweets
                tweets = await self.get_user_tweets(username, limit=10)
                
                if tweets:
                    newest_id = tweets[0]['id']
                    if last_tweet_id and newest_id != last_tweet_id:
                        new_tweets = []
                        for tweet in tweets:
                            if tweet['id'] == last_tweet_id:
                                break
                            new_tweets.append(tweet)
                        
                        if callback and new_tweets:
                            await callback(new_tweets)
                        else:
                            self.logger.info(f"Found {len(new_tweets)} new tweets from {username}")
                    
                    last_tweet_id = newest_id
                
                # Track metrics if enabled
                if track_metrics:
                    user_info = await asyncio.to_thread(
                        self.client.user_info,
                        username
                    )
                    metrics_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'followers': user_info.followers,
                        'following': user_info.following
                    })
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring user {username}: {str(e)}")
                await asyncio.sleep(interval)
                
    async def get_user_info(self, username: str) -> Dict:
        """
        Get detailed information about a Twitter user.
        
        Args:
            username: Username to get info for
            
        Returns:
            Dict containing user information
        """
        try:
            user = await asyncio.to_thread(
                self.client.user_info,
                username
            )
            
            return {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'bio': user.bio,
                'location': user.location,
                'website': user.website,
                'join_date': user.join_date.isoformat(),
                'followers': user.followers,
                'following': user.following,
                'tweets': user.tweets,
                'likes': user.likes,
                'is_private': user.is_private,
                'is_verified': user.is_verified
            }
                
        except Exception as e:
            self.logger.error(f"Error getting user info for {username}: {str(e)}")
            raise