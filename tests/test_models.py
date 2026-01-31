"""
Basic tests for database and Pydantic models.
"""
import pytest
from datetime import datetime
from decimal import Decimal

# Test imports
def test_database_models_import():
    """Test that database models can be imported."""
    from models.database import (
        Base, User, Analysis, PortfolioHolding, 
        TradeHistory, Alarm, AlarmHistory, Backtest
    )
    assert Base is not None
    assert User is not None
    assert Analysis is not None
    assert PortfolioHolding is not None
    assert TradeHistory is not None
    assert Alarm is not None
    assert AlarmHistory is not None
    assert Backtest is not None


def test_pydantic_models_import():
    """Test that Pydantic models can be imported."""
    from models.schemas import (
        SignalType, IndicatorResults, SentimentResults,
        Signal, AnalysisResult, Portfolio, Holding,
        Alarm as AlarmSchema, BacktestResult
    )
    assert SignalType is not None
    assert IndicatorResults is not None
    assert SentimentResults is not None
    assert Signal is not None
    assert AnalysisResult is not None
    assert Portfolio is not None
    assert Holding is not None
    assert AlarmSchema is not None
    assert BacktestResult is not None


def test_signal_type_enum():
    """Test SignalType enum values."""
    from models.schemas import SignalType
    
    assert SignalType.STRONG_BUY == "STRONG_BUY"
    assert SignalType.BUY == "BUY"
    assert SignalType.NEUTRAL == "NEUTRAL"
    assert SignalType.SELL == "SELL"
    assert SignalType.STRONG_SELL == "STRONG_SELL"
    assert SignalType.UNCERTAIN == "UNCERTAIN"


def test_analysis_request_validation():
    """Test AnalysisRequest validation."""
    from models.schemas import AnalysisRequest
    
    # Valid request
    request = AnalysisRequest(coin="BTC", timeframe="1h")
    assert request.coin == "BTC"
    assert request.timeframe == "1h"
    
    # Coin should be uppercased
    request = AnalysisRequest(coin="eth", timeframe="4h")
    assert request.coin == "ETH"
    
    # Invalid timeframe should raise error
    with pytest.raises(ValueError):
        AnalysisRequest(coin="BTC", timeframe="invalid")


def test_sentiment_results_validation():
    """Test SentimentResults validation."""
    from models.schemas import SentimentResults
    
    # Valid sentiment
    sentiment = SentimentResults(
        source="twitter",
        sentiment_score=0.5,
        confidence=0.8,
        sample_size=100,
        timestamp=datetime.utcnow()
    )
    assert sentiment.source == "twitter"
    assert -1 <= sentiment.sentiment_score <= 1
    assert 0 <= sentiment.confidence <= 1
    
    # Invalid sentiment score should raise error
    with pytest.raises(ValueError):
        SentimentResults(
            source="twitter",
            sentiment_score=2.0,  # Out of range
            confidence=0.8,
            sample_size=100,
            timestamp=datetime.utcnow()
        )


def test_signal_model():
    """Test Signal model creation."""
    from models.schemas import Signal, SignalType
    
    signal = Signal(
        signal_type=SignalType.BUY,
        success_probability=75.5,
        timestamp=datetime.utcnow(),
        coin="BTC",
        timeframe="1h",
        stop_loss=45000.0,
        take_profit=52000.0,
        ema_200_filter_applied=True
    )
    
    assert signal.signal_type == SignalType.BUY
    assert signal.success_probability == 75.5
    assert signal.coin == "BTC"
    assert signal.stop_loss == 45000.0


def test_portfolio_add_request_validation():
    """Test PortfolioAddRequest validation."""
    from models.schemas import PortfolioAddRequest
    
    # Valid request
    request = PortfolioAddRequest(
        coin="btc",
        amount=Decimal("0.5"),
        purchase_price=Decimal("50000.00"),
        purchase_date=datetime.utcnow()
    )
    assert request.coin == "BTC"  # Should be uppercased
    assert request.amount == Decimal("0.5")
    
    # Invalid amount should raise error
    with pytest.raises(ValueError):
        PortfolioAddRequest(
            coin="BTC",
            amount=Decimal("-0.5"),  # Negative amount
            purchase_price=Decimal("50000.00"),
            purchase_date=datetime.utcnow()
        )


def test_cache_import():
    """Test that cache module can be imported."""
    from utils.cache import RedisCache, cache
    
    assert RedisCache is not None
    assert cache is not None
    # Test that cache has the expected methods
    assert hasattr(cache, 'get_price')
    assert hasattr(cache, 'set_price')
    assert hasattr(cache, 'get_ohlcv')
    assert hasattr(cache, 'set_ohlcv')


@pytest.mark.skip(reason="Requires PostgreSQL connection")
def test_database_utils_import():
    """Test that database utils can be imported."""
    from utils.database import init_db, get_db, get_db_session
    
    assert init_db is not None
    assert get_db is not None
    assert get_db_session is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
