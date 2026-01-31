"""
Tests for Analysis History Manager.
Includes unit tests and property-based tests.
"""
import pytest
from hypothesis import given, strategies as st, settings as hyp_settings
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from engines.analysis_history import AnalysisHistoryManager
from models.schemas import (
    AnalysisResult, Signal, SignalType, IndicatorResults, OverallSentiment,
    SignalExplanation, SentimentClassification, TrendDirection,
    MACDValues, BollingerBands, MovingAverages, StochasticValues,
    VolumeProfile, ATRValues, FibonacciLevels, Pattern, SentimentResults
)
from models.database import Analysis, User, Base


# ============================================================================
# Test Database Setup
# ============================================================================

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test_analysis_history.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@contextmanager
def get_test_db():
    """Get test database session."""
    db = TestSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize test database."""
    # Remove existing test database if it exists
    if os.path.exists("./test_analysis_history.db"):
        os.remove("./test_analysis_history.db")
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)
    # Remove test database file
    if os.path.exists("./test_analysis_history.db"):
        os.remove("./test_analysis_history.db")


@pytest.fixture(scope="module")
def test_user_id():
    """Create a test user and return user_id."""
    user_id = str(uuid.uuid4())
    with get_test_db() as db:
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            password_hash="test_hash"
        )
        db.add(user)
        db.commit()
    return user_id


@pytest.fixture(scope="module")
def analysis_manager(test_user_id):
    """Create AnalysisHistoryManager instance."""
    return AnalysisHistoryManager(test_user_id, db_session_factory=get_test_db)


@pytest.fixture
def sample_analysis_result():
    """Create a sample AnalysisResult for testing."""
    analysis_id = str(uuid.uuid4())  # Generate new ID each time
    timestamp = datetime.utcnow()
    
    return AnalysisResult(
        id=analysis_id,
        coin="BTC",
        timeframe="1h",
        timestamp=timestamp,
        technical_results=IndicatorResults(
            rsi=65.5,
            rsi_signal="neutral",
            rsi_divergence=None,
            macd=MACDValues(macd=0.5, signal=0.3, histogram=0.2),
            macd_signal="bullish",
            bollinger=BollingerBands(upper=50000, middle=48000, lower=46000, bandwidth=4000),
            bollinger_signal="neutral",
            moving_averages=MovingAverages(
                sma_20=48500, sma_50=47000, sma_200=45000,
                ema_12=48800, ema_26=47500
            ),
            ma_signal="bullish",
            ema_50=47000,
            ema_200=45000,
            golden_death_cross=None,
            stochastic=StochasticValues(k=70, d=65),
            stochastic_signal="neutral",
            volume_profile=VolumeProfile(
                poc=48000, vah=49000, val=47000, total_volume=1000000
            ),
            atr=ATRValues(atr=1500, atr_percent=3.1, percentile=0.6),
            atr_stop_loss=46500,
            atr_take_profit=51000,
            vwap=48200,
            vwap_signal="above",
            obv=5000000,
            obv_signal="volume_supported",
            fibonacci_levels=FibonacciLevels(
                level_0=50000, level_236=48820, level_382=48090,
                level_500=47500, level_618=46910, level_100=45000
            ),
            patterns=[],
            support_levels=[46000, 45000],
            resistance_levels=[50000, 52000],
            confluence_score=0.75,
            ema_200_trend_filter="long_only"
        ),
        fundamental_results=OverallSentiment(
            overall_score=0.6,
            classification=SentimentClassification.POSITIVE,
            trend=TrendDirection.RISING,
            sources=[
                SentimentResults(
                    source="twitter",
                    sentiment_score=0.7,
                    confidence=0.8,
                    sample_size=100,
                    timestamp=timestamp
                )
            ]
        ),
        signal=Signal(
            signal_type=SignalType.BUY,
            success_probability=72.5,
            timestamp=timestamp,
            coin="BTC",
            timeframe="1h",
            stop_loss=46500,
            take_profit=51000,
            ema_200_filter_applied=True,
            golden_death_cross_detected=None,
            rsi_divergence_detected=None
        ),
        explanation=SignalExplanation(
            signal=Signal(
                signal_type=SignalType.BUY,
                success_probability=72.5,
                timestamp=timestamp,
                coin="BTC",
                timeframe="1h",
                stop_loss=46500,
                take_profit=51000,
                ema_200_filter_applied=True,
                golden_death_cross_detected=None,
                rsi_divergence_detected=None
            ),
            technical_reasons=["RSI neutral", "MACD bullish"],
            fundamental_reasons=["Positive sentiment"],
            supporting_indicators=["MACD", "Sentiment"],
            conflicting_indicators=[],
            risk_factors=["Moderate volatility"]
        ),
        ai_report="Test AI report",
        actual_outcome=None,
        price_at_analysis=48500.0,
        price_after_period=None
    )


# ============================================================================
# Unit Tests
# ============================================================================

def test_save_and_retrieve_analysis(analysis_manager, sample_analysis_result):
    """Test saving and retrieving an analysis."""
    # Save analysis
    analysis_id = analysis_manager.save_analysis(sample_analysis_result)
    assert analysis_id == sample_analysis_result.id
    
    # Retrieve analysis
    retrieved = analysis_manager.get_analysis(analysis_id)
    assert retrieved is not None
    assert retrieved.id == sample_analysis_result.id
    assert retrieved.coin == sample_analysis_result.coin
    assert retrieved.timeframe == sample_analysis_result.timeframe
    assert retrieved.signal.signal_type == sample_analysis_result.signal.signal_type


def test_list_analyses(analysis_manager, sample_analysis_result):
    """Test listing analyses."""
    # Save multiple analyses
    analysis_manager.save_analysis(sample_analysis_result)
    
    # Create another analysis
    analysis2 = sample_analysis_result.model_copy(deep=True)
    analysis2.id = str(uuid.uuid4())
    analysis2.coin = "ETH"
    analysis2.timestamp = datetime.utcnow() + timedelta(hours=1)
    analysis_manager.save_analysis(analysis2)
    
    # List all analyses
    summaries = analysis_manager.list_analyses()
    assert len(summaries) >= 2
    
    # Check ordering (newest first)
    assert summaries[0].timestamp >= summaries[1].timestamp
    
    # List with coin filter
    btc_summaries = analysis_manager.list_analyses(coin="BTC")
    assert all(s.coin == "BTC" for s in btc_summaries)


def test_compare_analyses(analysis_manager, sample_analysis_result):
    """Test comparing multiple analyses."""
    # Save first analysis
    id1 = analysis_manager.save_analysis(sample_analysis_result)
    
    # Create and save second analysis with different values
    analysis2 = sample_analysis_result.model_copy(deep=True)
    analysis2.id = str(uuid.uuid4())
    analysis2.signal.success_probability = 85.0
    analysis2.signal.signal_type = SignalType.STRONG_BUY
    analysis2.technical_results.rsi = 75.0
    analysis2.fundamental_results.overall_score = 0.8
    analysis2.timestamp = datetime.utcnow() + timedelta(hours=1)
    id2 = analysis_manager.save_analysis(analysis2)
    
    # Compare analyses
    comparison = analysis_manager.compare_analyses([id1, id2])
    
    assert len(comparison.analyses) == 2
    assert len(comparison.success_probability_changes) == 2
    assert comparison.success_probability_changes[0] == 72.5
    assert comparison.success_probability_changes[1] == 85.0
    assert len(comparison.signal_changes) == 2
    assert comparison.signal_changes[0] == "BUY"
    assert comparison.signal_changes[1] == "STRONG_BUY"


def test_update_accuracy(analysis_manager, sample_analysis_result):
    """Test updating analysis accuracy."""
    # Save analysis
    analysis_id = analysis_manager.save_analysis(sample_analysis_result)
    
    # Update accuracy
    analysis_manager.update_accuracy(analysis_id, "correct")
    
    # Verify update
    retrieved = analysis_manager.get_analysis(analysis_id)
    assert retrieved.actual_outcome == "correct"


def test_get_user_accuracy_stats(analysis_manager, sample_analysis_result):
    """Test calculating user accuracy statistics."""
    # Save multiple analyses with outcomes
    analysis1 = sample_analysis_result.model_copy(deep=True)
    analysis1.id = str(uuid.uuid4())
    id1 = analysis_manager.save_analysis(analysis1)
    analysis_manager.update_accuracy(id1, "correct")
    
    analysis2 = sample_analysis_result.model_copy(deep=True)
    analysis2.id = str(uuid.uuid4())
    analysis2.timestamp = datetime.utcnow() + timedelta(hours=1)
    id2 = analysis_manager.save_analysis(analysis2)
    analysis_manager.update_accuracy(id2, "incorrect")
    
    analysis3 = sample_analysis_result.model_copy(deep=True)
    analysis3.id = str(uuid.uuid4())
    analysis3.timestamp = datetime.utcnow() + timedelta(hours=2)
    id3 = analysis_manager.save_analysis(analysis3)
    analysis_manager.update_accuracy(id3, "correct")
    
    # Get accuracy stats
    stats = analysis_manager.get_user_accuracy_stats()
    
    assert stats.total_predictions >= 3
    assert stats.correct_predictions >= 2
    assert stats.incorrect_predictions >= 1
    assert 0 <= stats.accuracy_rate <= 100


# ============================================================================
# Property-Based Tests
# ============================================================================

@given(
    coin=st.sampled_from(["BTC", "ETH", "ADA", "SOL", "DOT"]),
    timeframe=st.sampled_from(["15m", "1h", "4h", "24h"]),
    success_probability=st.floats(min_value=0, max_value=100),
    price=st.floats(min_value=0.01, max_value=100000)
)
@hyp_settings(max_examples=100, deadline=None)
def test_property_32_analysis_save_integrity(
    coin, timeframe, success_probability, price,
    test_user_id
):
    """
    Feature: crypto-analysis-system, Property 32: Analiz Kaydetme Bütünlüğü
    Herhangi bir analiz sonucu için, tarih, saat ve tüm parametrelerle 
    birlikte kaydedilmelidir.
    
    **Validates: Requirement 16.1**
    """
    manager = AnalysisHistoryManager(test_user_id, db_session_factory=get_test_db)
    
    # Create analysis with given parameters
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    
    analysis = AnalysisResult(
        id=analysis_id,
        coin=coin,
        timeframe=timeframe,
        timestamp=timestamp,
        technical_results=IndicatorResults(
            rsi=50.0,
            rsi_signal="neutral",
            rsi_divergence=None,
            macd=MACDValues(macd=0.0, signal=0.0, histogram=0.0),
            macd_signal="neutral",
            bollinger=BollingerBands(upper=price*1.1, middle=price, lower=price*0.9, bandwidth=price*0.2),
            bollinger_signal="neutral",
            moving_averages=MovingAverages(
                sma_20=price, sma_50=price, sma_200=price,
                ema_12=price, ema_26=price
            ),
            ma_signal="neutral",
            ema_50=price,
            ema_200=price,
            golden_death_cross=None,
            stochastic=StochasticValues(k=50, d=50),
            stochastic_signal="neutral",
            volume_profile=VolumeProfile(
                poc=price, vah=price*1.05, val=price*0.95, total_volume=1000000
            ),
            atr=ATRValues(atr=price*0.02, atr_percent=2.0, percentile=0.5),
            atr_stop_loss=price*0.95,
            atr_take_profit=price*1.05,
            vwap=price,
            vwap_signal="neutral",
            obv=1000000,
            obv_signal="neutral",
            fibonacci_levels=FibonacciLevels(
                level_0=price*1.1, level_236=price*1.076, level_382=price*1.062,
                level_500=price*1.05, level_618=price*1.038, level_100=price
            ),
            patterns=[],
            support_levels=[price*0.9],
            resistance_levels=[price*1.1],
            confluence_score=0.5,
            ema_200_trend_filter="neutral"
        ),
        fundamental_results=OverallSentiment(
            overall_score=0.0,
            classification=SentimentClassification.NEUTRAL,
            trend=TrendDirection.STABLE,
            sources=[]
        ),
        signal=Signal(
            signal_type=SignalType.NEUTRAL,
            success_probability=success_probability,
            timestamp=timestamp,
            coin=coin,
            timeframe=timeframe,
            stop_loss=None,
            take_profit=None,
            ema_200_filter_applied=False,
            golden_death_cross_detected=None,
            rsi_divergence_detected=None
        ),
        explanation=SignalExplanation(
            signal=Signal(
                signal_type=SignalType.NEUTRAL,
                success_probability=success_probability,
                timestamp=timestamp,
                coin=coin,
                timeframe=timeframe,
                stop_loss=None,
                take_profit=None,
                ema_200_filter_applied=False,
                golden_death_cross_detected=None,
                rsi_divergence_detected=None
            ),
            technical_reasons=[],
            fundamental_reasons=[],
            supporting_indicators=[],
            conflicting_indicators=[],
            risk_factors=[]
        ),
        ai_report="Property test report",
        actual_outcome=None,
        price_at_analysis=price,
        price_after_period=None
    )
    
    # Save analysis
    saved_id = manager.save_analysis(analysis)
    
    # Retrieve and verify all parameters are saved
    retrieved = manager.get_analysis(saved_id)
    
    assert retrieved is not None
    assert retrieved.id == analysis_id
    assert retrieved.coin == coin
    assert retrieved.timeframe == timeframe
    assert retrieved.timestamp == timestamp
    assert retrieved.signal.success_probability == success_probability
    # Use approximate comparison for floating point values (SQLite precision)
    assert abs(retrieved.price_at_analysis - price) < 0.01
    
    # Verify technical and fundamental data are saved
    assert retrieved.technical_results is not None
    assert retrieved.fundamental_results is not None
    assert retrieved.signal is not None



@given(
    num_analyses=st.integers(min_value=2, max_value=10),
    coin=st.sampled_from(["BTC", "ETH", "ADA"])
)
@hyp_settings(max_examples=100, deadline=None)
def test_property_33_analysis_listing_order(
    num_analyses, coin, test_user_id
):
    """
    Feature: crypto-analysis-system, Property 33: Analiz Listeleme Sıralaması
    Herhangi bir geçmiş analiz seti için, tarih sırasına göre listelenmeli 
    (kronolojik sıra - en yeni önce).
    
    **Validates: Requirement 16.2**
    """
    manager = AnalysisHistoryManager(test_user_id, db_session_factory=get_test_db)
    
    # Create and save multiple analyses with different timestamps
    timestamps = []
    for i in range(num_analyses):
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.utcnow() + timedelta(hours=i)
        timestamps.append(timestamp)
        
        analysis = AnalysisResult(
            id=analysis_id,
            coin=coin,
            timeframe="1h",
            timestamp=timestamp,
            technical_results=IndicatorResults(
                rsi=50.0,
                rsi_signal="neutral",
                rsi_divergence=None,
                macd=MACDValues(macd=0.0, signal=0.0, histogram=0.0),
                macd_signal="neutral",
                bollinger=BollingerBands(upper=50000, middle=48000, lower=46000, bandwidth=4000),
                bollinger_signal="neutral",
                moving_averages=MovingAverages(
                    sma_20=48000, sma_50=47000, sma_200=45000,
                    ema_12=48000, ema_26=47000
                ),
                ma_signal="neutral",
                ema_50=47000,
                ema_200=45000,
                golden_death_cross=None,
                stochastic=StochasticValues(k=50, d=50),
                stochastic_signal="neutral",
                volume_profile=VolumeProfile(
                    poc=48000, vah=49000, val=47000, total_volume=1000000
                ),
                atr=ATRValues(atr=1500, atr_percent=3.0, percentile=0.5),
                atr_stop_loss=46500,
                atr_take_profit=49500,
                vwap=48000,
                vwap_signal="neutral",
                obv=1000000,
                obv_signal="neutral",
                fibonacci_levels=FibonacciLevels(
                    level_0=50000, level_236=48820, level_382=48090,
                    level_500=47500, level_618=46910, level_100=45000
                ),
                patterns=[],
                support_levels=[46000],
                resistance_levels=[50000],
                confluence_score=0.5,
                ema_200_trend_filter="neutral"
            ),
            fundamental_results=OverallSentiment(
                overall_score=0.0,
                classification=SentimentClassification.NEUTRAL,
                trend=TrendDirection.STABLE,
                sources=[]
            ),
            signal=Signal(
                signal_type=SignalType.NEUTRAL,
                success_probability=50.0,
                timestamp=timestamp,
                coin=coin,
                timeframe="1h",
                stop_loss=None,
                take_profit=None,
                ema_200_filter_applied=False,
                golden_death_cross_detected=None,
                rsi_divergence_detected=None
            ),
            explanation=SignalExplanation(
                signal=Signal(
                    signal_type=SignalType.NEUTRAL,
                    success_probability=50.0,
                    timestamp=timestamp,
                    coin=coin,
                    timeframe="1h",
                    stop_loss=None,
                    take_profit=None,
                    ema_200_filter_applied=False,
                    golden_death_cross_detected=None,
                    rsi_divergence_detected=None
                ),
                technical_reasons=[],
                fundamental_reasons=[],
                supporting_indicators=[],
                conflicting_indicators=[],
                risk_factors=[]
            ),
            ai_report="Test report",
            actual_outcome=None,
            price_at_analysis=48000.0,
            price_after_period=None
        )
        
        manager.save_analysis(analysis)
    
    # List analyses
    summaries = manager.list_analyses(coin=coin)
    
    # Verify ordering (newest first)
    assert len(summaries) >= num_analyses
    
    # Check that timestamps are in descending order
    for i in range(len(summaries) - 1):
        assert summaries[i].timestamp >= summaries[i + 1].timestamp


@given(
    num_analyses=st.integers(min_value=2, max_value=5),
    success_probs=st.lists(
        st.floats(min_value=0, max_value=100),
        min_size=2,
        max_size=5
    )
)
@hyp_settings(max_examples=100, deadline=None)
def test_property_34_analysis_comparison(
    num_analyses, success_probs, test_user_id
):
    """
    Feature: crypto-analysis-system, Property 34: Analiz Karşılaştırma
    Herhangi bir iki veya daha fazla analiz için, yan yana karşılaştırma 
    yapılabilmeli ve tüm gerekli karşılaştırma bilgileri gösterilmelidir.
    
    **Validates: Requirements 16.3, 16.4**
    """
    manager = AnalysisHistoryManager(test_user_id, db_session_factory=get_test_db)
    
    # Ensure we have matching number of analyses and probabilities
    num_analyses = min(num_analyses, len(success_probs))
    success_probs = success_probs[:num_analyses]
    
    # Create and save multiple analyses
    analysis_ids = []
    for i in range(num_analyses):
        analysis_id = str(uuid.uuid4())
        analysis_ids.append(analysis_id)
        
        analysis = AnalysisResult(
            id=analysis_id,
            coin="BTC",
            timeframe="1h",
            timestamp=datetime.utcnow() + timedelta(hours=i),
            technical_results=IndicatorResults(
                rsi=50.0 + i * 5,
                rsi_signal="neutral",
                rsi_divergence=None,
                macd=MACDValues(macd=0.1 * i, signal=0.0, histogram=0.1 * i),
                macd_signal="neutral",
                bollinger=BollingerBands(
                    upper=50000, middle=48000, lower=46000, bandwidth=4000
                ),
                bollinger_signal="neutral",
                moving_averages=MovingAverages(
                    sma_20=48000, sma_50=47000, sma_200=45000,
                    ema_12=48000, ema_26=47000
                ),
                ma_signal="neutral",
                ema_50=47000,
                ema_200=45000,
                golden_death_cross=None,
                stochastic=StochasticValues(k=50, d=50),
                stochastic_signal="neutral",
                volume_profile=VolumeProfile(
                    poc=48000, vah=49000, val=47000, total_volume=1000000
                ),
                atr=ATRValues(atr=1500 + i * 100, atr_percent=3.0, percentile=0.5),
                atr_stop_loss=46500,
                atr_take_profit=49500,
                vwap=48000,
                vwap_signal="neutral",
                obv=1000000,
                obv_signal="neutral",
                fibonacci_levels=FibonacciLevels(
                    level_0=50000, level_236=48820, level_382=48090,
                    level_500=47500, level_618=46910, level_100=45000
                ),
                patterns=[],
                support_levels=[46000],
                resistance_levels=[50000],
                confluence_score=0.5 + i * 0.05,
                ema_200_trend_filter="neutral"
            ),
            fundamental_results=OverallSentiment(
                overall_score=0.1 * i,
                classification=SentimentClassification.NEUTRAL,
                trend=TrendDirection.STABLE,
                sources=[]
            ),
            signal=Signal(
                signal_type=SignalType.NEUTRAL,
                success_probability=success_probs[i],
                timestamp=datetime.utcnow() + timedelta(hours=i),
                coin="BTC",
                timeframe="1h",
                stop_loss=None,
                take_profit=None,
                ema_200_filter_applied=False,
                golden_death_cross_detected=None,
                rsi_divergence_detected=None
            ),
            explanation=SignalExplanation(
                signal=Signal(
                    signal_type=SignalType.NEUTRAL,
                    success_probability=success_probs[i],
                    timestamp=datetime.utcnow() + timedelta(hours=i),
                    coin="BTC",
                    timeframe="1h",
                    stop_loss=None,
                    take_profit=None,
                    ema_200_filter_applied=False,
                    golden_death_cross_detected=None,
                    rsi_divergence_detected=None
                ),
                technical_reasons=[],
                fundamental_reasons=[],
                supporting_indicators=[],
                conflicting_indicators=[],
                risk_factors=[]
            ),
            ai_report="Test report",
            actual_outcome=None,
            price_at_analysis=48000.0,
            price_after_period=None
        )
        
        manager.save_analysis(analysis)
    
    # Compare analyses
    comparison = manager.compare_analyses(analysis_ids)
    
    # Verify comparison contains all required information
    assert len(comparison.analyses) == num_analyses
    assert len(comparison.success_probability_changes) == num_analyses
    assert len(comparison.signal_changes) == num_analyses
    assert len(comparison.sentiment_changes) == num_analyses
    
    # Verify indicator differences are present
    assert 'rsi' in comparison.indicator_differences
    assert 'macd_histogram' in comparison.indicator_differences
    assert 'confluence_score' in comparison.indicator_differences
    assert 'atr' in comparison.indicator_differences
    
    # Verify success probability changes match input
    for i, prob in enumerate(success_probs):
        assert comparison.success_probability_changes[i] == prob
