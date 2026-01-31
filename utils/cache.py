"""
Redis cache management with TTL settings.
Provides caching for price, OHLCV, social media, news, and analysis data.
"""
import redis
import json
from typing import Optional, Any, List, Dict
from datetime import datetime, timedelta
from utils.config import settings
from utils.logger import logger


class RedisCache:
    """Redis cache manager with predefined TTL settings."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # TTL settings from config
        self.ttl_price = settings.CACHE_TTL_PRICE  # 60 seconds
        self.ttl_ohlcv = settings.CACHE_TTL_OHLCV  # 300 seconds (5 minutes)
        self.ttl_social = settings.CACHE_TTL_SOCIAL  # 3600 seconds (1 hour)
        self.ttl_news = settings.CACHE_TTL_NEWS  # 3600 seconds (1 hour)
        self.ttl_analysis = settings.CACHE_TTL_ANALYSIS  # 600 seconds (10 minutes)
    
    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string."""
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str)
        return str(value)
    
    def _deserialize(self, value: Optional[str]) -> Optional[Any]:
        """Deserialize JSON string to Python object."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    # ========================================================================
    # Price Data Cache
    # ========================================================================
    
    def get_price(self, coin: str) -> Optional[Dict]:
        """
        Get cached price data for a coin.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
        
        Returns:
            Dict with price and timestamp, or None if not cached
        """
        key = f"price:{coin.upper()}"
        try:
            value = self.client.get(key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting price from cache: {e}")
            return None
    
    def set_price(self, coin: str, price: float, timestamp: Optional[datetime] = None) -> bool:
        """
        Cache price data for a coin.
        
        Args:
            coin: Coin symbol
            price: Current price
            timestamp: Price timestamp (defaults to now)
        
        Returns:
            True if successful, False otherwise
        """
        key = f"price:{coin.upper()}"
        data = {
            "price": price,
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        try:
            self.client.setex(key, self.ttl_price, self._serialize(data))
            return True
        except Exception as e:
            logger.error(f"Error setting price in cache: {e}")
            return False
    
    # ========================================================================
    # OHLCV Data Cache
    # ========================================================================
    
    def get_ohlcv(self, coin: str, timeframe: str) -> Optional[List[Dict]]:
        """
        Get cached OHLCV data.
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe (e.g., "1h", "4h")
        
        Returns:
            List of OHLCV candles, or None if not cached
        """
        key = f"ohlcv:{coin.upper()}:{timeframe}"
        try:
            value = self.client.get(key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting OHLCV from cache: {e}")
            return None
    
    def set_ohlcv(self, coin: str, timeframe: str, data: List[Dict]) -> bool:
        """
        Cache OHLCV data.
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe
            data: List of OHLCV candles
        
        Returns:
            True if successful, False otherwise
        """
        key = f"ohlcv:{coin.upper()}:{timeframe}"
        try:
            self.client.setex(key, self.ttl_ohlcv, self._serialize(data))
            return True
        except Exception as e:
            logger.error(f"Error setting OHLCV in cache: {e}")
            return False
    
    # ========================================================================
    # Social Media Data Cache
    # ========================================================================
    
    def get_social(self, coin: str, platform: str) -> Optional[List[Dict]]:
        """
        Get cached social media data.
        
        Args:
            coin: Coin symbol
            platform: Platform name (e.g., "twitter", "reddit")
        
        Returns:
            List of social media posts, or None if not cached
        """
        key = f"social:{coin.upper()}:{platform.lower()}"
        try:
            value = self.client.get(key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting social data from cache: {e}")
            return None
    
    def set_social(self, coin: str, platform: str, data: List[Dict]) -> bool:
        """
        Cache social media data.
        
        Args:
            coin: Coin symbol
            platform: Platform name
            data: List of social media posts
        
        Returns:
            True if successful, False otherwise
        """
        key = f"social:{coin.upper()}:{platform.lower()}"
        try:
            self.client.setex(key, self.ttl_social, self._serialize(data))
            return True
        except Exception as e:
            logger.error(f"Error setting social data in cache: {e}")
            return False
    
    # ========================================================================
    # News Data Cache
    # ========================================================================
    
    def get_news(self, coin: str) -> Optional[List[Dict]]:
        """
        Get cached news data.
        
        Args:
            coin: Coin symbol
        
        Returns:
            List of news articles, or None if not cached
        """
        key = f"news:{coin.upper()}"
        try:
            value = self.client.get(key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting news from cache: {e}")
            return None
    
    def set_news(self, coin: str, data: List[Dict]) -> bool:
        """
        Cache news data.
        
        Args:
            coin: Coin symbol
            data: List of news articles
        
        Returns:
            True if successful, False otherwise
        """
        key = f"news:{coin.upper()}"
        try:
            self.client.setex(key, self.ttl_news, self._serialize(data))
            return True
        except Exception as e:
            logger.error(f"Error setting news in cache: {e}")
            return False
    
    # ========================================================================
    # Analysis Results Cache
    # ========================================================================
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """
        Get cached analysis result.
        
        Args:
            analysis_id: Analysis ID
        
        Returns:
            Analysis result dict, or None if not cached
        """
        key = f"analysis:{analysis_id}"
        try:
            value = self.client.get(key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting analysis from cache: {e}")
            return None
    
    def set_analysis(self, analysis_id: str, data: Dict) -> bool:
        """
        Cache analysis result.
        
        Args:
            analysis_id: Analysis ID
            data: Analysis result dict
        
        Returns:
            True if successful, False otherwise
        """
        key = f"analysis:{analysis_id}"
        try:
            self.client.setex(key, self.ttl_analysis, self._serialize(data))
            return True
        except Exception as e:
            logger.error(f"Error setting analysis in cache: {e}")
            return False
    
    # ========================================================================
    # Alarm State Cache
    # ========================================================================
    
    def get_alarm_last_check(self, alarm_id: str) -> Optional[str]:
        """
        Get last check timestamp for an alarm.
        
        Args:
            alarm_id: Alarm ID
        
        Returns:
            ISO format timestamp string, or None if not cached
        """
        key = f"alarm:{alarm_id}:last_check"
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting alarm last check from cache: {e}")
            return None
    
    def set_alarm_last_check(self, alarm_id: str, timestamp: Optional[datetime] = None) -> bool:
        """
        Set last check timestamp for an alarm.
        
        Args:
            alarm_id: Alarm ID
            timestamp: Check timestamp (defaults to now)
        
        Returns:
            True if successful, False otherwise
        """
        key = f"alarm:{alarm_id}:last_check"
        ts = (timestamp or datetime.utcnow()).isoformat()
        try:
            # No expiration for alarm state
            self.client.set(key, ts)
            return True
        except Exception as e:
            logger.error(f"Error setting alarm last check in cache: {e}")
            return False
    
    # ========================================================================
    # Generic Cache Operations
    # ========================================================================
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value, or None if not found
        """
        try:
            value = self.client.get(key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting key '{key}' from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = self._serialize(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting key '{key}' in cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key '{key}' from cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking key '{key}' existence: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "price:*")
        
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern '{pattern}': {e}")
            return 0
    
    def flush_all(self) -> bool:
        """
        Clear all cache data. Use with caution!
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False
    
    # ========================================================================
    # Cache Invalidation Strategies
    # ========================================================================
    
    def invalidate_coin_data(self, coin: str) -> int:
        """
        Invalidate all cached data for a specific coin.
        
        Args:
            coin: Coin symbol
        
        Returns:
            Number of keys deleted
        """
        coin_upper = coin.upper()
        patterns = [
            f"price:{coin_upper}",
            f"ohlcv:{coin_upper}:*",
            f"social:{coin_upper}:*",
            f"news:{coin_upper}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            try:
                keys = self.client.keys(pattern)
                if keys:
                    total_deleted += self.client.delete(*keys)
            except Exception as e:
                logger.error(f"Error invalidating pattern '{pattern}': {e}")
        
        logger.info(f"Invalidated {total_deleted} cache keys for coin {coin}")
        return total_deleted
    
    def invalidate_analysis(self, analysis_id: str) -> bool:
        """
        Invalidate cached analysis result.
        
        Args:
            analysis_id: Analysis ID
        
        Returns:
            True if successful, False otherwise
        """
        return self.delete(f"analysis:{analysis_id}")
    
    def invalidate_stale_data(self) -> int:
        """
        Remove all expired keys (Redis handles this automatically,
        but this method can be used for manual cleanup).
        
        Returns:
            Number of keys deleted
        """
        # Redis automatically removes expired keys, but we can scan for
        # keys that should have expired but haven't been accessed
        total_deleted = 0
        try:
            # Get all keys
            all_keys = self.client.keys("*")
            for key in all_keys:
                # Check TTL
                ttl = self.client.ttl(key)
                if ttl == -1:  # No expiration set
                    # Skip alarm state keys (they don't expire)
                    if not key.startswith("alarm:"):
                        logger.warning(f"Key '{key}' has no expiration set")
                elif ttl == -2:  # Key doesn't exist
                    total_deleted += 1
        except Exception as e:
            logger.error(f"Error checking stale data: {e}")
        
        return total_deleted
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        try:
            info = self.client.info()
            stats = {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "total_keys": self.client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": 0.0
            }
            
            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            if total_requests > 0:
                stats["hit_rate"] = (stats["hits"] / total_requests) * 100
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    def get_ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Cache key
        
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key '{key}': {e}")
            return -2
    
    def refresh_ttl(self, key: str, ttl: int) -> bool:
        """
        Refresh TTL for an existing key.
        
        Args:
            key: Cache key
            ttl: New TTL in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Error refreshing TTL for key '{key}': {e}")
            return False
    
    # ========================================================================
    # Batch Operations
    # ========================================================================
    
    def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """
        Get multiple values at once.
        
        Args:
            keys: List of cache keys
        
        Returns:
            List of values (None for missing keys)
        """
        try:
            values = self.client.mget(keys)
            return [self._deserialize(v) for v in values]
        except Exception as e:
            logger.error(f"Error getting multiple keys: {e}")
            return [None] * len(keys)
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple key-value pairs at once.
        
        Args:
            mapping: Dict of key-value pairs
            ttl: Optional TTL for all keys
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize all values
            serialized = {k: self._serialize(v) for k, v in mapping.items()}
            
            # Use pipeline for atomic operation
            pipe = self.client.pipeline()
            pipe.mset(serialized)
            
            # Set TTL for each key if specified
            if ttl:
                for key in mapping.keys():
                    pipe.expire(key, ttl)
            
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting multiple keys: {e}")
            return False


# Create global cache instance
cache = RedisCache()
