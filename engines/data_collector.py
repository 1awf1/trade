"""
Data Collector component for fetching price, social media, news, and trends data.
Implements retry mechanism, failover, and caching.
"""
import aiohttp
import asyncio
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from utils.config import settings
from utils.cache import cache
from utils.logger import logger
import time


class DataCollectorError(Exception):
    """Base exception for data collector errors."""
    pass


class APIUnavailableError(DataCollectorError):
    """Raised when all API sources are unavailable."""
    pass


class PriceDataCollector:
    """Collects price and OHLCV data from multiple sources with failover."""
    
    def __init__(self):
        """Initialize price data collector."""
        self.binance_base_url = "https://api.binance.com/api/v3"
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.timeout = 10  # seconds
    
    async def _retry_request(self, func, *args, **kwargs) -> Optional[Any]:
        """
        Execute request with exponential backoff retry.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    return None
    
    async def _fetch_binance_price(self, coin: str) -> Optional[float]:
        """
        Fetch current price from Binance.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
        
        Returns:
            Current price or None if failed
        """
        symbol = f"{coin}USDT"
        url = f"{self.binance_base_url}/ticker/price"
        params = {"symbol": symbol}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data.get("price", 0))
                        logger.info(f"Fetched {coin} price from Binance: ${price}")
                        return price
                    else:
                        logger.error(f"Binance API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching price from Binance: {e}")
            return None
    
    async def _fetch_coingecko_price(self, coin: str) -> Optional[float]:
        """
        Fetch current price from CoinGecko.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
        
        Returns:
            Current price or None if failed
        """
        # Map common symbols to CoinGecko IDs
        coin_id_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "ADA": "cardano",
            "SOL": "solana",
            "XRP": "ripple",
            "DOT": "polkadot",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "MATIC": "matic-network"
        }
        
        coin_id = coin_id_map.get(coin.upper(), coin.lower())
        url = f"{self.coingecko_base_url}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd"
        }
        
        if settings.COINGECKO_API_KEY:
            params["x_cg_pro_api_key"] = settings.COINGECKO_API_KEY
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get(coin_id, {}).get("usd")
                        if price:
                            logger.info(f"Fetched {coin} price from CoinGecko: ${price}")
                            return float(price)
                    else:
                        logger.error(f"CoinGecko API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching price from CoinGecko: {e}")
            return None
    
    async def fetch_price(self, coin: str, use_cache: bool = True) -> Optional[float]:
        """
        Fetch current price with failover and caching.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            use_cache: Whether to use cached data
        
        Returns:
            Current price or None if all sources failed
        
        Raises:
            APIUnavailableError: If all API sources are unavailable
        """
        coin = coin.upper()
        
        # Check cache first
        if use_cache:
            cached = cache.get_price(coin)
            if cached:
                logger.info(f"Using cached price for {coin}")
                return cached.get("price")
        
        # Try Binance first
        price = await self._retry_request(self._fetch_binance_price, coin)
        
        # Failover to CoinGecko if Binance failed
        if price is None:
            logger.warning(f"Binance unavailable, trying CoinGecko for {coin}")
            price = await self._retry_request(self._fetch_coingecko_price, coin)
        
        # If both failed, try to use stale cache data
        if price is None:
            logger.error(f"All price sources failed for {coin}")
            cached = cache.get_price(coin)
            if cached:
                logger.warning(f"Using stale cached price for {coin}")
                return cached.get("price")
            raise APIUnavailableError(f"Unable to fetch price for {coin} from any source")
        
        # Cache the result
        cache.set_price(coin, price)
        return price

    
    async def _fetch_binance_ohlcv(self, coin: str, timeframe: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch OHLCV data from Binance.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            timeframe: Timeframe (e.g., "1h", "4h")
            limit: Number of candles to fetch
        
        Returns:
            List of OHLCV candles or None if failed
        """
        symbol = f"{coin}USDT"
        
        # Map timeframe to Binance interval
        interval_map = {
            "15m": "15m",
            "1h": "1h",
            "4h": "4h",
            "8h": "8h",
            "12h": "12h",
            "24h": "1d",
            "1w": "1w",
            "15d": "1d",  # Will fetch daily and aggregate
            "1M": "1M"
        }
        
        interval = interval_map.get(timeframe, "1h")
        url = f"{self.binance_base_url}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        candles = []
                        for candle in data:
                            candles.append({
                                "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                                "open": float(candle[1]),
                                "high": float(candle[2]),
                                "low": float(candle[3]),
                                "close": float(candle[4]),
                                "volume": float(candle[5])
                            })
                        logger.info(f"Fetched {len(candles)} OHLCV candles from Binance for {coin}")
                        return candles
                    else:
                        logger.error(f"Binance OHLCV API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching OHLCV from Binance: {e}")
            return None
    
    async def _fetch_coingecko_ohlcv(self, coin: str, timeframe: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch OHLCV data from CoinGecko.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            timeframe: Timeframe (e.g., "1h", "4h")
            limit: Number of candles to fetch
        
        Returns:
            List of OHLCV candles or None if failed
        """
        # Map common symbols to CoinGecko IDs
        coin_id_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "ADA": "cardano",
            "SOL": "solana",
            "XRP": "ripple",
            "DOT": "polkadot",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "MATIC": "matic-network"
        }
        
        coin_id = coin_id_map.get(coin.upper(), coin.lower())
        
        # CoinGecko uses days parameter
        days_map = {
            "15m": 1,
            "1h": 1,
            "4h": 7,
            "8h": 14,
            "12h": 30,
            "24h": 30,
            "1w": 90,
            "15d": 90,
            "1M": 365
        }
        
        days = days_map.get(timeframe, 7)
        url = f"{self.coingecko_base_url}/coins/{coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        if settings.COINGECKO_API_KEY:
            params["x_cg_pro_api_key"] = settings.COINGECKO_API_KEY
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        candles = []
                        for candle in data[-limit:]:  # Get last 'limit' candles
                            candles.append({
                                "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                                "open": float(candle[1]),
                                "high": float(candle[2]),
                                "low": float(candle[3]),
                                "close": float(candle[4])
                            })
                        logger.info(f"Fetched {len(candles)} OHLCV candles from CoinGecko for {coin}")
                        return candles
                    else:
                        logger.error(f"CoinGecko OHLCV API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching OHLCV from CoinGecko: {e}")
            return None
    
    async def fetch_ohlcv(
        self,
        coin: str,
        timeframe: str,
        limit: int = 100,
        use_cache: bool = True
    ) -> Optional[List[Dict]]:
        """
        Fetch OHLCV data with failover and caching.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            timeframe: Timeframe (e.g., "1h", "4h")
            limit: Number of candles to fetch
            use_cache: Whether to use cached data
        
        Returns:
            List of OHLCV candles or None if all sources failed
        
        Raises:
            APIUnavailableError: If all API sources are unavailable
        """
        coin = coin.upper()
        
        # Check cache first
        if use_cache:
            cached = cache.get_ohlcv(coin, timeframe)
            if cached:
                logger.info(f"Using cached OHLCV for {coin} {timeframe}")
                return cached
        
        # Try Binance first
        candles = await self._retry_request(self._fetch_binance_ohlcv, coin, timeframe, limit)
        
        # Failover to CoinGecko if Binance failed
        if candles is None:
            logger.warning(f"Binance unavailable, trying CoinGecko for {coin} OHLCV")
            candles = await self._retry_request(self._fetch_coingecko_ohlcv, coin, timeframe, limit)
        
        # If both failed, try to use stale cache data
        if candles is None:
            logger.error(f"All OHLCV sources failed for {coin}")
            cached = cache.get_ohlcv(coin, timeframe)
            if cached:
                logger.warning(f"Using stale cached OHLCV for {coin} {timeframe}")
                return cached
            raise APIUnavailableError(f"Unable to fetch OHLCV for {coin} from any source")
        
        # Cache the result
        cache.set_ohlcv(coin, timeframe, candles)
        return candles



class SocialMediaCollector:
    """Collects social media data from Twitter, Reddit, and Telegram."""
    
    def __init__(self):
        """Initialize social media collector."""
        self.max_retries = 3
        self.retry_delay = 1
        self.timeout = 10
    
    async def _retry_request(self, func, *args, **kwargs) -> Optional[Any]:
        """Execute request with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    return None
    
    async def _fetch_twitter_data(self, coin: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch Twitter data for a coin.
        
        Args:
            coin: Coin symbol or name
            limit: Maximum number of tweets to fetch
        
        Returns:
            List of tweets or None if failed
        """
        if not settings.TWITTER_BEARER_TOKEN:
            logger.warning("Twitter API credentials not configured")
            return None
        
        try:
            import tweepy
            
            # Initialize Twitter client
            client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)
            
            # Search for tweets
            query = f"({coin} OR ${coin}) (crypto OR cryptocurrency) -is:retweet lang:en"
            tweets = client.search_recent_tweets(
                query=query,
                max_results=min(limit, 100),
                tweet_fields=["created_at", "public_metrics", "lang"]
            )
            
            if not tweets.data:
                logger.info(f"No tweets found for {coin}")
                return []
            
            results = []
            for tweet in tweets.data:
                results.append({
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat(),
                    "likes": tweet.public_metrics.get("like_count", 0),
                    "retweets": tweet.public_metrics.get("retweet_count", 0),
                    "source": "twitter"
                })
            
            logger.info(f"Fetched {len(results)} tweets for {coin}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching Twitter data: {e}")
            return None
    
    async def _fetch_reddit_data(self, coin: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch Reddit data for a coin.
        
        Args:
            coin: Coin symbol or name
            limit: Maximum number of posts to fetch
        
        Returns:
            List of Reddit posts or None if failed
        """
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            logger.warning("Reddit API credentials not configured")
            return None
        
        try:
            import praw
            
            # Initialize Reddit client
            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
            
            # Search in cryptocurrency subreddits
            subreddits = ["cryptocurrency", "CryptoMarkets", "Bitcoin", "ethereum"]
            results = []
            
            for subreddit_name in subreddits:
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    # Search for posts
                    for post in subreddit.search(coin, limit=limit // len(subreddits), time_filter="day"):
                        results.append({
                            "text": f"{post.title} {post.selftext}",
                            "created_at": datetime.fromtimestamp(post.created_utc).isoformat(),
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "subreddit": subreddit_name,
                            "source": "reddit"
                        })
                except Exception as e:
                    logger.warning(f"Error fetching from r/{subreddit_name}: {e}")
                    continue
            
            logger.info(f"Fetched {len(results)} Reddit posts for {coin}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            return None
    
    async def _fetch_telegram_data(self, coin: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch Telegram data for a coin (optional implementation).
        
        Args:
            coin: Coin symbol or name
            limit: Maximum number of messages to fetch
        
        Returns:
            List of Telegram messages or None if not implemented/failed
        """
        # Telegram scraping is optional and complex
        # Would require Telethon or similar library and proper authentication
        logger.info("Telegram scraping not implemented (optional feature)")
        return []
    
    async def fetch_social_media(
        self,
        coin: str,
        platforms: Optional[List[str]] = None,
        limit: int = 100,
        use_cache: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Fetch social media data from multiple platforms.
        
        Args:
            coin: Coin symbol or name
            platforms: List of platforms to fetch from (default: all)
            limit: Maximum number of posts per platform
            use_cache: Whether to use cached data
        
        Returns:
            Dictionary mapping platform names to lists of posts
        """
        coin = coin.upper()
        
        if platforms is None:
            platforms = ["twitter", "reddit", "telegram"]
        
        results = {}
        
        for platform in platforms:
            # Check cache first
            if use_cache:
                cached = cache.get_social(coin, platform)
                if cached:
                    logger.info(f"Using cached {platform} data for {coin}")
                    results[platform] = cached
                    continue
            
            # Fetch data based on platform
            data = None
            if platform == "twitter":
                data = await self._retry_request(self._fetch_twitter_data, coin, limit)
            elif platform == "reddit":
                data = await self._retry_request(self._fetch_reddit_data, coin, limit)
            elif platform == "telegram":
                data = await self._retry_request(self._fetch_telegram_data, coin, limit)
            
            # Handle failures gracefully
            if data is None:
                logger.warning(f"Failed to fetch {platform} data for {coin}, continuing with other sources")
                # Try to use stale cache
                cached = cache.get_social(coin, platform)
                if cached:
                    logger.warning(f"Using stale cached {platform} data for {coin}")
                    data = cached
                else:
                    data = []
            
            results[platform] = data
            
            # Cache the result
            if data:
                cache.set_social(coin, platform, data)
        
        return results



class NewsCollector:
    """Collects news data from CoinDesk, CoinTelegraph, and other sources."""
    
    def __init__(self):
        """Initialize news collector."""
        self.coindesk_rss = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        self.cointelegraph_rss = "https://cointelegraph.com/rss"
        self.max_retries = 3
        self.retry_delay = 1
        self.timeout = 10
    
    async def _retry_request(self, func, *args, **kwargs) -> Optional[Any]:
        """Execute request with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    return None
    
    async def _parse_rss_feed(self, url: str, coin: str) -> Optional[List[Dict]]:
        """
        Parse RSS feed and filter for coin-related articles.
        
        Args:
            url: RSS feed URL
            coin: Coin symbol or name to filter for
        
        Returns:
            List of news articles or None if failed
        """
        try:
            from bs4 import BeautifulSoup
            import feedparser
            
            # Fetch RSS feed
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status != 200:
                        logger.error(f"RSS feed error: {response.status}")
                        return None
                    
                    content = await response.text()
            
            # Parse feed
            feed = feedparser.parse(content)
            
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {url}")
                return []
            
            results = []
            coin_lower = coin.lower()
            
            for entry in feed.entries:
                title = entry.get("title", "")
                description = entry.get("description", "") or entry.get("summary", "")
                
                # Filter for coin-related articles
                if coin_lower in title.lower() or coin_lower in description.lower():
                    # Clean HTML from description
                    soup = BeautifulSoup(description, "html.parser")
                    clean_description = soup.get_text()
                    
                    results.append({
                        "title": title,
                        "description": clean_description,
                        "url": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "source": url
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {url}: {e}")
            return None
    
    async def _fetch_coindesk_news(self, coin: str) -> Optional[List[Dict]]:
        """
        Fetch news from CoinDesk RSS feed.
        
        Args:
            coin: Coin symbol or name
        
        Returns:
            List of news articles or None if failed
        """
        articles = await self._parse_rss_feed(self.coindesk_rss, coin)
        if articles:
            logger.info(f"Fetched {len(articles)} CoinDesk articles for {coin}")
        return articles
    
    async def _fetch_cointelegraph_news(self, coin: str) -> Optional[List[Dict]]:
        """
        Fetch news from CoinTelegraph RSS feed.
        
        Args:
            coin: Coin symbol or name
        
        Returns:
            List of news articles or None if failed
        """
        articles = await self._parse_rss_feed(self.cointelegraph_rss, coin)
        if articles:
            logger.info(f"Fetched {len(articles)} CoinTelegraph articles for {coin}")
        return articles
    
    async def fetch_news(
        self,
        coin: str,
        sources: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Fetch news from multiple sources.
        
        Args:
            coin: Coin symbol or name
            sources: List of sources to fetch from (default: all)
            use_cache: Whether to use cached data
        
        Returns:
            List of news articles from all sources
        """
        coin = coin.upper()
        
        # Check cache first
        if use_cache:
            cached = cache.get_news(coin)
            if cached:
                logger.info(f"Using cached news for {coin}")
                return cached
        
        if sources is None:
            sources = ["coindesk", "cointelegraph"]
        
        all_articles = []
        
        # Fetch from each source
        for source in sources:
            articles = None
            if source == "coindesk":
                articles = await self._retry_request(self._fetch_coindesk_news, coin)
            elif source == "cointelegraph":
                articles = await self._retry_request(self._fetch_cointelegraph_news, coin)
            
            # Handle failures gracefully
            if articles is None:
                logger.warning(f"Failed to fetch news from {source} for {coin}, continuing with other sources")
                continue
            
            all_articles.extend(articles)
        
        # If all sources failed, try to use stale cache
        if not all_articles:
            logger.warning(f"All news sources failed for {coin}")
            cached = cache.get_news(coin)
            if cached:
                logger.warning(f"Using stale cached news for {coin}")
                return cached
        
        # Cache the result
        if all_articles:
            cache.set_news(coin, all_articles)
        
        return all_articles



class TrendsCollector:
    """Collects Google Trends data using pytrends."""
    
    def __init__(self):
        """Initialize trends collector."""
        self.max_retries = 3
        self.retry_delay = 2  # Google Trends can be rate-limited
    
    def _retry_request_sync(self, func, *args, **kwargs) -> Optional[Any]:
        """Execute synchronous request with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    return None
    
    def _fetch_google_trends_sync(self, coin: str, timeframe: str = "today 7-d") -> Optional[Dict]:
        """
        Fetch Google Trends data (synchronous).
        
        Args:
            coin: Coin symbol or name
            timeframe: Timeframe for trends (e.g., "today 7-d", "today 1-m")
        
        Returns:
            Trends data or None if failed
        """
        try:
            from pytrends.request import TrendReq
            
            # Initialize pytrends
            pytrends = TrendReq(hl='en-US', tz=360)
            
            # Build search terms
            search_terms = [f"{coin} crypto", f"{coin} cryptocurrency"]
            
            # Build payload
            pytrends.build_payload(search_terms, timeframe=timeframe)
            
            # Get interest over time
            interest_over_time = pytrends.interest_over_time()
            
            if interest_over_time.empty:
                logger.info(f"No Google Trends data found for {coin}")
                return {
                    "coin": coin,
                    "timeframe": timeframe,
                    "average_interest": 0,
                    "trend_direction": "stable",
                    "data_points": []
                }
            
            # Calculate metrics
            data_points = []
            for index, row in interest_over_time.iterrows():
                data_points.append({
                    "date": index.isoformat(),
                    "interest": int(row[search_terms[0]]) if search_terms[0] in row else 0
                })
            
            # Calculate average and trend
            values = [dp["interest"] for dp in data_points]
            average_interest = sum(values) / len(values) if values else 0
            
            # Simple trend detection
            if len(values) >= 2:
                first_half = sum(values[:len(values)//2]) / (len(values)//2)
                second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
                
                if second_half > first_half * 1.1:
                    trend_direction = "rising"
                elif second_half < first_half * 0.9:
                    trend_direction = "falling"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "stable"
            
            result = {
                "coin": coin,
                "timeframe": timeframe,
                "average_interest": average_interest,
                "trend_direction": trend_direction,
                "data_points": data_points
            }
            
            logger.info(f"Fetched Google Trends for {coin}: avg={average_interest:.1f}, trend={trend_direction}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Google Trends: {e}")
            return None
    
    async def fetch_trends(
        self,
        coin: str,
        timeframe: str = "today 7-d",
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Fetch Google Trends data (async wrapper).
        
        Args:
            coin: Coin symbol or name
            timeframe: Timeframe for trends
            use_cache: Whether to use cached data
        
        Returns:
            Trends data or None if failed
        """
        coin = coin.upper()
        cache_key = f"trends:{coin}:{timeframe}"
        
        # Check cache first
        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Using cached Google Trends for {coin}")
                return cached
        
        # Fetch data (run in executor since pytrends is synchronous)
        loop = asyncio.get_event_loop()
        trends_data = await loop.run_in_executor(
            None,
            self._retry_request_sync,
            self._fetch_google_trends_sync,
            coin,
            timeframe
        )
        
        # Handle failure gracefully
        if trends_data is None:
            logger.warning(f"Failed to fetch Google Trends for {coin}")
            # Try to use stale cache
            cached = cache.get(cache_key)
            if cached:
                logger.warning(f"Using stale cached Google Trends for {coin}")
                return cached
            # Return empty data instead of None
            return {
                "coin": coin,
                "timeframe": timeframe,
                "average_interest": 0,
                "trend_direction": "stable",
                "data_points": []
            }
        
        # Cache the result
        cache.set(cache_key, trends_data, ttl=settings.CACHE_TTL_SOCIAL)
        return trends_data


# ============================================================================
# Main Data Collector Class
# ============================================================================

class DataCollector:
    """
    Main data collector that aggregates all data sources.
    Provides unified interface for fetching price, social media, news, and trends data.
    """
    
    def __init__(self):
        """Initialize all collectors."""
        self.price_collector = PriceDataCollector()
        self.social_collector = SocialMediaCollector()
        self.news_collector = NewsCollector()
        self.trends_collector = TrendsCollector()
    
    async def fetch_price(self, coin: str, use_cache: bool = True) -> Optional[float]:
        """Fetch current price."""
        return await self.price_collector.fetch_price(coin, use_cache)
    
    async def fetch_ohlcv(
        self,
        coin: str,
        timeframe: str,
        limit: int = 100,
        use_cache: bool = True
    ) -> Optional[List[Dict]]:
        """Fetch OHLCV data."""
        return await self.price_collector.fetch_ohlcv(coin, timeframe, limit, use_cache)
    
    async def fetch_social_media(
        self,
        coin: str,
        platforms: Optional[List[str]] = None,
        limit: int = 100,
        use_cache: bool = True
    ) -> Dict[str, List[Dict]]:
        """Fetch social media data."""
        return await self.social_collector.fetch_social_media(coin, platforms, limit, use_cache)
    
    async def fetch_news(
        self,
        coin: str,
        sources: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> List[Dict]:
        """Fetch news data."""
        return await self.news_collector.fetch_news(coin, sources, use_cache)
    
    async def fetch_trends(
        self,
        coin: str,
        timeframe: str = "today 7-d",
        use_cache: bool = True
    ) -> Optional[Dict]:
        """Fetch Google Trends data."""
        return await self.trends_collector.fetch_trends(coin, timeframe, use_cache)
    
    async def fetch_all_fundamental_data(
        self,
        coin: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch all fundamental analysis data (social media, news, trends).
        
        Args:
            coin: Coin symbol
            use_cache: Whether to use cached data
        
        Returns:
            Dictionary containing all fundamental data
        """
        logger.info(f"Fetching all fundamental data for {coin}")
        
        # Fetch all data concurrently
        social_task = self.fetch_social_media(coin, use_cache=use_cache)
        news_task = self.fetch_news(coin, use_cache=use_cache)
        trends_task = self.fetch_trends(coin, use_cache=use_cache)
        
        social_data, news_data, trends_data = await asyncio.gather(
            social_task,
            news_task,
            trends_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(social_data, Exception):
            logger.error(f"Error fetching social media data: {social_data}")
            social_data = {}
        
        if isinstance(news_data, Exception):
            logger.error(f"Error fetching news data: {news_data}")
            news_data = []
        
        if isinstance(trends_data, Exception):
            logger.error(f"Error fetching trends data: {trends_data}")
            trends_data = None
        
        return {
            "social_media": social_data,
            "news": news_data,
            "trends": trends_data
        }
