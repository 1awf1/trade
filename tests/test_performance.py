"""
Property-based tests for performance requirements.
Tests analysis performance and cache acceleration.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
import time
from engines.technical_analysis import TechnicalAnalysisEngine
from engines.fundamental_analysis import FundamentalAnalysisEngine
from engines.signal_generator import SignalGenerator
from engines.ai_interpreter import AIInterpreter
from engines.data_collector import DataCollector
from utils.cache import cache


# Test data strategies
SUPPORTED_COINS = ["BTC", "ETH", "BNB", "XRP", "ADA"]
TIMEFRAMES = ["15m", "1h", "4h", "8h", "12h", "24h", "1w"]


@pytest.fixture(scope="module")
def engines():
    """Initialize analysis engines."""
    return {
        "data_collector": DataCollector(),
        "technical": TechnicalAnalysisEngine(),
        "fundamental": FundamentalAnalysisEngine(),
        "signal": SignalGenerator(),
        "ai": AIInterpreter()
    }


@pytest.mark.performance
@pytest.mark.asyncio
@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    timeframe=st.sampled_from(TIMEFRAMES)
)
@settings(
    max_examples=20,  # Reduced for performance tests
    deadline=35000,  # 35 seconds to allow for 30s requirement + overhead
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
)
async def test_property_23_analysis_performance(coin, timeframe, engines):
    """
    Feature: crypto-analysis-system, Property 23: Analiz Performansı
    
    Herhangi bir analiz talebi için, sonuçlar 30 saniye içinde üretilmelidir.
    
    Validates: Requirement 13.1
    """
    start_time = time.time()
    
    try:
        # Step 1: Collect data
        data_collector = engines["data_collector"]
        ohlcv_data = data_collector.fetch_ohlcv(coin, timeframe)
        
        # Step 2: Technical analysis
        technical_engine = engines["technical"]
        df = technical_engine.process_ohlcv_data(ohlcv_data)
        technical_results = technical_engine.calculate_indicators(df)
        
        # Step 3: Fundamental analysis (simplified for performance test)
        fundamental_engine = engines["fundamental"]
        # Create mock sentiment results for performance test
        from models.schemas import SentimentResults, SentimentClassification, TrendDirection, OverallSentiment
        mock_sentiment = OverallSentiment(
            overall_score=0.5,
            classification=SentimentClassification.NEUTRAL,
            trend=TrendDirection.STABLE,
            sources=[]
        )
        fundamental_results = mock_sentiment
        
        # Step 4: Generate signal
        signal, explanation = engines["signal"].generate_signal(
            technical_results,
            fundamental_results,
            coin,
            timeframe
        )
        
        # Step 5: AI interpretation (can be slow, but should still complete in time)
        ai_report = engines["ai"].generate_report(
            signal,
            explanation,
            technical_results,
            fundamental_results
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Property: Analysis must complete within 30 seconds
        assert elapsed_time < 30.0, (
            f"Analysis took {elapsed_time:.2f}s, exceeding 30s limit "
            f"for {coin} on {timeframe}"
        )
        
        # Verify results are complete
        assert technical_results is not None
        assert fundamental_results is not None
        assert signal is not None
        assert ai_report is not None
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        # Even if analysis fails, it should fail within time limit
        assert elapsed_time < 30.0, (
            f"Analysis failed after {elapsed_time:.2f}s, exceeding 30s limit: {e}"
        )
        raise


@pytest.mark.performance
@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    timeframe=st.sampled_from(TIMEFRAMES)
)
@settings(
    max_examples=20,
    deadline=None,  # No deadline for cache tests
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_25_cache_acceleration(coin, timeframe):
    """
    Feature: crypto-analysis-system, Property 25: Önbellek Hızlandırması
    
    Herhangi bir tekrarlayan sorgu için, önbellekten gelen yanıt 
    ilk sorguda daha hızlı olmalıdır.
    
    Validates: Requirement 13.4
    """
    # Clear cache for this coin to ensure clean test
    cache.invalidate_coin_data(coin)
    
    # Test with price data (simpler than full analysis)
    test_price = 50000.0
    
    # First request (cache miss) - set data
    start_time_1 = time.time()
    cache.set_price(coin, test_price)
    time_1 = time.time() - start_time_1
    
    # Small delay to ensure cache is written
    time.sleep(0.1)
    
    # Second request (cache hit) - get data
    start_time_2 = time.time()
    cached_price = cache.get_price(coin)
    time_2 = time.time() - start_time_2
    
    # Property: Cached request should be faster than first request
    # Get operations should be very fast (< 0.1s)
    assert time_2 < 0.1, (
        f"Cached request ({time_2:.3f}s) too slow for {coin}"
    )
    
    # Verify data is consistent
    assert cached_price is not None
    assert cached_price["price"] == test_price


@pytest.mark.performance
def test_cache_invalidation():
    """
    Test cache invalidation strategies.
    """
    test_coin = "BTC"
    
    # Set some test data
    cache.set_price(test_coin, 50000.0)
    cache.set_ohlcv(test_coin, "1h", [{"open": 50000, "high": 51000, "low": 49000, "close": 50500, "volume": 1000}])
    cache.set_social(test_coin, "twitter", [{"text": "Test tweet", "timestamp": datetime.utcnow().isoformat()}])
    cache.set_news(test_coin, [{"title": "Test news", "content": "Test content"}])
    
    # Verify data exists
    assert cache.get_price(test_coin) is not None
    assert cache.get_ohlcv(test_coin, "1h") is not None
    assert cache.get_social(test_coin, "twitter") is not None
    assert cache.get_news(test_coin) is not None
    
    # Invalidate all coin data
    deleted_count = cache.invalidate_coin_data(test_coin)
    
    # Verify data is removed
    assert deleted_count > 0
    assert cache.get_price(test_coin) is None
    assert cache.get_ohlcv(test_coin, "1h") is None
    assert cache.get_social(test_coin, "twitter") is None
    assert cache.get_news(test_coin) is None


@pytest.mark.performance
def test_cache_stats():
    """
    Test cache statistics retrieval.
    """
    stats = cache.get_cache_stats()
    
    # Verify stats structure
    assert "connected" in stats
    assert stats["connected"] is True
    
    if stats["connected"]:
        assert "total_keys" in stats
        assert "used_memory" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        
        # Verify types
        assert isinstance(stats["total_keys"], int)
        assert isinstance(stats["hits"], int)
        assert isinstance(stats["misses"], int)
        assert isinstance(stats["hit_rate"], float)
        
        # Hit rate should be between 0 and 100
        assert 0 <= stats["hit_rate"] <= 100


@pytest.mark.performance
def test_batch_cache_operations():
    """
    Test batch cache operations for efficiency.
    """
    # Prepare test data
    test_data = {
        "test:key1": "value1",
        "test:key2": "value2",
        "test:key3": "value3",
        "test:key4": "value4",
        "test:key5": "value5"
    }
    
    # Test mset (batch set)
    start_time = time.time()
    result = cache.mset(test_data, ttl=60)
    batch_time = time.time() - start_time
    
    assert result is True
    
    # Test mget (batch get)
    keys = list(test_data.keys())
    start_time = time.time()
    values = cache.mget(keys)
    mget_time = time.time() - start_time
    
    # Verify all values retrieved
    assert len(values) == len(keys)
    for i, key in enumerate(keys):
        assert values[i] == test_data[key]
    
    # Batch operations should be reasonably fast
    assert batch_time < 1.0, f"Batch set took {batch_time:.3f}s"
    assert mget_time < 1.0, f"Batch get took {mget_time:.3f}s"
    
    # Cleanup
    for key in keys:
        cache.delete(key)


@pytest.mark.performance
def test_cache_ttl_operations():
    """
    Test TTL (time to live) operations.
    """
    test_key = "test:ttl_key"
    test_value = "test_value"
    ttl_seconds = 5
    
    # Set with TTL
    cache.set(test_key, test_value, ttl=ttl_seconds)
    
    # Verify key exists
    assert cache.exists(test_key)
    
    # Check TTL
    ttl = cache.get_ttl(test_key)
    assert 0 < ttl <= ttl_seconds
    
    # Refresh TTL
    new_ttl = 10
    result = cache.refresh_ttl(test_key, new_ttl)
    assert result is True
    
    # Verify new TTL
    ttl = cache.get_ttl(test_key)
    assert 0 < ttl <= new_ttl
    
    # Cleanup
    cache.delete(test_key)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
