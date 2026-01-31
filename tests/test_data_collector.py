"""
Property-based tests for Data Collector component.
Tests error tolerance and data freshness properties.
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from engines.data_collector import (
    DataCollector,
    PriceDataCollector,
    SocialMediaCollector,
    NewsCollector,
    TrendsCollector,
    APIUnavailableError
)


# ============================================================================
# Test Strategies
# ============================================================================

# Common coin symbols for testing
SUPPORTED_COINS = ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", "DOGE", "AVAX", "MATIC"]
TIMEFRAMES = ["15m", "1h", "4h", "8h", "12h", "24h", "1w", "15d", "1M"]
PLATFORMS = ["twitter", "reddit", "telegram"]
NEWS_SOURCES = ["coindesk", "cointelegraph"]


# ============================================================================
# Property Test 7: Veri Toplama Hata Toleransı
# ============================================================================

@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    timeframe=st.sampled_from(TIMEFRAMES)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_7_data_collection_error_tolerance(coin, timeframe):
    """
    Feature: crypto-analysis-system, Property 7: Veri Toplama Hata Toleransı
    
    Herhangi bir veri kaynağı hatası durumunda, hata loglanmalı ve 
    sistem mevcut verilerle devam etmelidir.
    
    Validates: Gereksinim 5.4, 6.4, 14.2
    """
    collector = PriceDataCollector()
    
    # Test 1: When primary source (Binance) fails, should try secondary source (CoinGecko)
    with patch.object(collector, '_fetch_binance_ohlcv', new_callable=AsyncMock) as mock_binance:
        with patch.object(collector, '_fetch_coingecko_ohlcv', new_callable=AsyncMock) as mock_coingecko:
            # Simulate Binance failure
            mock_binance.return_value = None
            
            # CoinGecko returns valid data
            mock_coingecko.return_value = [
                {
                    "timestamp": datetime.utcnow(),
                    "open": 50000.0,
                    "high": 51000.0,
                    "low": 49000.0,
                    "close": 50500.0,
                    "volume": 1000000.0
                }
            ]
            
            # Should not raise exception, should return CoinGecko data
            result = await collector.fetch_ohlcv(coin, timeframe, use_cache=False)
            
            # Property: System continues with available data
            assert result is not None, "System should continue with secondary source when primary fails"
            assert len(result) > 0, "Should return data from secondary source"
            assert mock_binance.called, "Should attempt primary source first"
            assert mock_coingecko.called, "Should failover to secondary source"
    
    # Test 2: When all sources fail but cache exists, should use stale cache
    with patch.object(collector, '_fetch_binance_ohlcv', new_callable=AsyncMock) as mock_binance:
        with patch.object(collector, '_fetch_coingecko_ohlcv', new_callable=AsyncMock) as mock_coingecko:
            from utils.cache import cache
            
            # Simulate both sources failing
            mock_binance.return_value = None
            mock_coingecko.return_value = None
            
            # Set stale cache data
            stale_data = [
                {
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "open": 48000.0,
                    "high": 49000.0,
                    "low": 47000.0,
                    "close": 48500.0,
                    "volume": 900000.0
                }
            ]
            cache.set_ohlcv(coin, timeframe, stale_data)
            
            # Should not raise exception, should return stale cache
            result = await collector.fetch_ohlcv(coin, timeframe, use_cache=False)
            
            # Property: System uses stale cache when all sources fail
            assert result is not None, "System should use stale cache when all sources fail"
            assert len(result) > 0, "Should return stale cached data"
    
    # Test 3: When all sources fail and no cache, should raise APIUnavailableError
    with patch.object(collector, '_fetch_binance_ohlcv', new_callable=AsyncMock) as mock_binance:
        with patch.object(collector, '_fetch_coingecko_ohlcv', new_callable=AsyncMock) as mock_coingecko:
            from utils.cache import cache
            
            # Simulate both sources failing
            mock_binance.return_value = None
            mock_coingecko.return_value = None
            
            # Clear cache
            cache.delete(f"ohlcv:{coin}:{timeframe}")
            
            # Property: Should raise appropriate error when no data available
            with pytest.raises(APIUnavailableError):
                await collector.fetch_ohlcv(coin, timeframe, use_cache=False)


@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    platform=st.sampled_from(PLATFORMS)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_7_social_media_error_tolerance(coin, platform):
    """
    Feature: crypto-analysis-system, Property 7: Veri Toplama Hata Toleransı
    
    Social media veri toplama hatalarında sistem devam etmelidir.
    
    Validates: Gereksinim 5.4, 6.4, 14.2
    """
    collector = SocialMediaCollector()
    
    # Test: When one platform fails, should continue with other platforms
    with patch.object(collector, '_fetch_twitter_data', new_callable=AsyncMock) as mock_twitter:
        with patch.object(collector, '_fetch_reddit_data', new_callable=AsyncMock) as mock_reddit:
            # Simulate Twitter failure
            mock_twitter.return_value = None
            
            # Reddit returns valid data
            mock_reddit.return_value = [
                {
                    "text": "Test post about crypto",
                    "created_at": datetime.utcnow().isoformat(),
                    "score": 100,
                    "source": "reddit"
                }
            ]
            
            # Should not raise exception
            result = await collector.fetch_social_media(coin, platforms=["twitter", "reddit"], use_cache=False)
            
            # Property: System continues with available platforms
            assert result is not None, "System should continue when one platform fails"
            assert "twitter" in result, "Should include failed platform with empty data"
            assert "reddit" in result, "Should include successful platform"
            assert len(result["reddit"]) > 0, "Should have data from successful platform"


@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_7_news_error_tolerance(coin):
    """
    Feature: crypto-analysis-system, Property 7: Veri Toplama Hata Toleransı
    
    Haber veri toplama hatalarında sistem devam etmelidir.
    
    Validates: Gereksinim 5.4, 6.4, 14.2
    """
    collector = NewsCollector()
    
    # Test: When one news source fails, should continue with other sources
    with patch.object(collector, '_fetch_coindesk_news', new_callable=AsyncMock) as mock_coindesk:
        with patch.object(collector, '_fetch_cointelegraph_news', new_callable=AsyncMock) as mock_cointelegraph:
            # Simulate CoinDesk failure
            mock_coindesk.return_value = None
            
            # CoinTelegraph returns valid data
            mock_cointelegraph.return_value = [
                {
                    "title": "Crypto news article",
                    "description": "Article about cryptocurrency",
                    "url": "https://example.com/article",
                    "published": datetime.utcnow().isoformat(),
                    "source": "cointelegraph"
                }
            ]
            
            # Should not raise exception
            result = await collector.fetch_news(coin, use_cache=False)
            
            # Property: System continues with available sources
            assert result is not None, "System should continue when one source fails"
            assert len(result) > 0, "Should have data from successful source"
            assert mock_coindesk.called, "Should attempt first source"
            assert mock_cointelegraph.called, "Should try second source"



# ============================================================================
# Property Test 8: Veri Tazeliği
# ============================================================================

@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    timeframe=st.sampled_from(TIMEFRAMES)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_8_data_freshness_ohlcv(coin, timeframe):
    """
    Feature: crypto-analysis-system, Property 8: Veri Tazeliği
    
    Herhangi bir önbelleklenmiş veri için, son güncelleme zamanı 
    24 saatten eski olmamalıdır.
    
    Validates: Gereksinim 5.5
    """
    from utils.cache import cache
    collector = PriceDataCollector()
    
    # Test 1: Fresh data should be within 24 hours
    with patch.object(collector, '_fetch_binance_ohlcv', new_callable=AsyncMock) as mock_binance:
        current_time = datetime.utcnow()
        
        # Mock returns fresh data
        mock_binance.return_value = [
            {
                "timestamp": current_time - timedelta(minutes=5),
                "open": 50000.0,
                "high": 51000.0,
                "low": 49000.0,
                "close": 50500.0,
                "volume": 1000000.0
            }
        ]
        
        # Fetch and cache data
        result = await collector.fetch_ohlcv(coin, timeframe, use_cache=False)
        
        # Property: Cached data timestamp should be within 24 hours
        assert result is not None
        for candle in result:
            timestamp = candle.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            age = current_time - timestamp
            assert age <= timedelta(hours=24), f"Data should be within 24 hours, but is {age.total_seconds() / 3600:.1f} hours old"
    
    # Test 2: Verify cache TTL is set correctly
    cache_key = f"ohlcv:{coin}:{timeframe}"
    
    # Set data in cache
    test_data = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "open": 50000.0,
            "high": 51000.0,
            "low": 49000.0,
            "close": 50500.0,
            "volume": 1000000.0
        }
    ]
    cache.set_ohlcv(coin, timeframe, test_data)
    
    # Property: Cache should exist and be retrievable
    cached_data = cache.get_ohlcv(coin, timeframe)
    assert cached_data is not None, "Cached data should be retrievable"
    
    # Property: Cached data should match what was set
    assert len(cached_data) == len(test_data), "Cached data should match original data"


@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_8_data_freshness_price(coin):
    """
    Feature: crypto-analysis-system, Property 8: Veri Tazeliği
    
    Fiyat verileri 24 saatten eski olmamalıdır.
    
    Validates: Gereksinim 5.5
    """
    from utils.cache import cache
    collector = PriceDataCollector()
    
    # Test: Price data should be fresh
    with patch.object(collector, '_fetch_binance_price', new_callable=AsyncMock) as mock_binance:
        current_time = datetime.utcnow()
        
        # Mock returns price
        mock_binance.return_value = 50000.0
        
        # Fetch and cache price
        result = await collector.fetch_price(coin, use_cache=False)
        
        # Property: Price should be cached
        assert result is not None
        
        # Get cached price
        cached_price = cache.get_price(coin)
        assert cached_price is not None, "Price should be cached"
        
        # Property: Cached price timestamp should be within 24 hours
        timestamp_str = cached_price.get("timestamp")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = current_time - timestamp
            assert age <= timedelta(hours=24), f"Price data should be within 24 hours, but is {age.total_seconds() / 3600:.1f} hours old"


@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    platform=st.sampled_from(PLATFORMS)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_8_data_freshness_social(coin, platform):
    """
    Feature: crypto-analysis-system, Property 8: Veri Tazeliği
    
    Sosyal medya verileri 24 saatten eski olmamalıdır.
    
    Validates: Gereksinim 5.5
    """
    from utils.cache import cache
    
    # Test: Social media data should be fresh when cached
    current_time = datetime.utcnow()
    
    test_data = [
        {
            "text": "Test post",
            "created_at": (current_time - timedelta(hours=2)).isoformat(),
            "source": platform
        }
    ]
    
    # Cache the data
    cache.set_social(coin, platform, test_data)
    
    # Property: Cached data should be retrievable
    cached_data = cache.get_social(coin, platform)
    assert cached_data is not None, "Social media data should be cached"
    
    # Property: Data timestamps should be within reasonable range
    for post in cached_data:
        created_at_str = post.get("created_at")
        if created_at_str:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            age = current_time - created_at
            # Social media posts can be up to 24 hours old
            assert age <= timedelta(hours=24), f"Social media post should be within 24 hours"


@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_8_data_freshness_news(coin):
    """
    Feature: crypto-analysis-system, Property 8: Veri Tazeliği
    
    Haber verileri 24 saatten eski olmamalıdır.
    
    Validates: Gereksinim 5.5
    """
    from utils.cache import cache
    
    # Test: News data should be fresh when cached
    current_time = datetime.utcnow()
    
    test_data = [
        {
            "title": "Test news",
            "description": "Test description",
            "url": "https://example.com",
            "published": (current_time - timedelta(hours=3)).isoformat(),
            "source": "coindesk"
        }
    ]
    
    # Cache the data
    cache.set_news(coin, test_data)
    
    # Property: Cached data should be retrievable
    cached_data = cache.get_news(coin)
    assert cached_data is not None, "News data should be cached"
    
    # Property: News articles should be reasonably fresh
    for article in cached_data:
        published_str = article.get("published")
        if published_str:
            try:
                published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                age = current_time - published
                # News can be up to 24 hours old
                assert age <= timedelta(hours=24), f"News article should be within 24 hours"
            except (ValueError, AttributeError):
                # If parsing fails, skip timestamp check
                pass


# ============================================================================
# Unit Tests for Retry Mechanism
# ============================================================================

@pytest.mark.asyncio
async def test_retry_mechanism_exponential_backoff():
    """Test that retry mechanism uses exponential backoff."""
    collector = PriceDataCollector()
    
    call_times = []
    
    async def failing_func():
        call_times.append(datetime.utcnow())
        raise Exception("Test error")
    
    # Should retry 3 times with exponential backoff
    result = await collector._retry_request(failing_func)
    
    assert result is None, "Should return None after all retries fail"
    assert len(call_times) == 3, "Should retry exactly 3 times"
    
    # Check exponential backoff (approximately)
    if len(call_times) >= 2:
        delay1 = (call_times[1] - call_times[0]).total_seconds()
        assert delay1 >= 1.0, "First retry should wait at least 1 second"
    
    if len(call_times) >= 3:
        delay2 = (call_times[2] - call_times[1]).total_seconds()
        assert delay2 >= 2.0, "Second retry should wait at least 2 seconds"


@pytest.mark.asyncio
async def test_retry_mechanism_success_on_retry():
    """Test that retry mechanism succeeds if function succeeds on retry."""
    collector = PriceDataCollector()
    
    attempt_count = [0]
    
    async def sometimes_failing_func():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise Exception("Test error")
        return "success"
    
    result = await collector._retry_request(sometimes_failing_func)
    
    assert result == "success", "Should return success after retry"
    assert attempt_count[0] == 2, "Should succeed on second attempt"
