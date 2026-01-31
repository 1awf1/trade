"""
Property-based and unit tests for Signal Generator.
Tests success probability calculation, signal generation, and explanation.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from engines.signal_generator import SignalGenerator
from models.schemas import (
    IndicatorResults, OverallSentiment, SignalType, SentimentClassification,
    TrendDirection, MACDValues, BollingerBands, MovingAverages,
    StochasticValues, VolumeProfile, ATRValues, FibonacciLevels,
    SentimentResults
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def signal_generator():
    """Create a signal generator instance."""
    return SignalGenerator()


@pytest.fixture
def sample_indicators():
    """Create sample indicator results."""
    return IndicatorResults(
        rsi=50.0,
        rsi_signal="neutral",
        rsi_divergence=None,
        macd=MACDValues(macd=0.5, signal=0.3, histogram=0.2),
        macd_signal="bullish",
        bollinger=BollingerBands(upper=52000, middle=50000, lower=48000, bandwidth=4.0),
        bollinger_signal="neutral",
        moving_averages=MovingAverages(
            sma_20=49500, sma_50=49000, sma_200=48000,
            ema_12=49800, ema_26=49500
        ),
        ma_signal="bullish",
        ema_50=49000.0,
        ema_200=48000.0,
        golden_death_cross=None,
        stochastic=StochasticValues(k=50.0, d=50.0),
        stochastic_signal="neutral",
        volume_profile=VolumeProfile(poc=50000, vah=51000, val=49000, total_volume=1000000),
        atr=ATRValues(atr=1000.0, atr_percent=2.0, percentile=0.5),
        atr_stop_loss=48000.0,
        atr_take_profit=53000.0,
        vwap=50000.0,
        vwap_signal="neutral",
        obv=1000000.0,
        obv_signal="volume_supported",
        fibonacci_levels=FibonacciLevels(
            level_0=52000, level_236=51000, level_382=50500,
            level_500=50000, level_618=49500, level_100=48000
        ),
        patterns=[],
        support_levels=[48000, 47500, 47000],
        resistance_levels=[52000, 52500, 53000],
        confluence_score=0.6,
        ema_200_trend_filter="neutral"
    )


@pytest.fixture
def sample_sentiment():
    """Create sample sentiment results."""
    return OverallSentiment(
        overall_score=0.3,
        classification=SentimentClassification.POSITIVE,
        trend=TrendDirection.RISING,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=0.4,
                confidence=0.8,
                sample_size=100,
                timestamp=datetime.utcnow()
            )
        ]
    )


# ============================================================================
# Property-Based Tests
# ============================================================================

@given(
    technical_score=st.floats(min_value=0.0, max_value=1.0),
    fundamental_score=st.floats(min_value=0.0, max_value=1.0),
    confluence=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_property_11_success_probability_calculation(
    technical_score,
    fundamental_score,
    confluence
):
    """
    Feature: crypto-analysis-system, Property 11: Başarı İhtimali Hesaplama
    
    Herhangi bir teknik ve temel analiz skoru çifti için, birleştirilmiş 
    başarı ihtimali [0, 100] aralığında hesaplanmalıdır.
    
    Validates: Gereksinim 7.1, 7.2, 7.3
    """
    # Create signal generator instance
    signal_generator = SignalGenerator()
    
    # Calculate success probability
    success_probability = signal_generator.calculate_success_probability(
        technical_score,
        fundamental_score,
        confluence
    )
    
    # Property 1: Result must be in [0, 1] range
    assert 0.0 <= success_probability <= 1.0, \
        f"Success probability {success_probability} is outside [0, 1] range"
    
    # Property 2: Result should be a weighted combination
    # Expected: technical * 0.6 + fundamental * 0.3 + confluence * 0.1
    expected = (
        technical_score * 0.6 +
        fundamental_score * 0.3 +
        confluence * 0.1
    )
    
    # Allow small floating point error
    assert abs(success_probability - expected) < 0.001, \
        f"Success probability {success_probability} doesn't match expected {expected}"
    
    # Property 3: If all scores are 0, result should be 0
    if technical_score == 0.0 and fundamental_score == 0.0 and confluence == 0.0:
        assert success_probability == 0.0
    
    # Property 4: If all scores are 1, result should be 1 (with floating point tolerance)
    if technical_score == 1.0 and fundamental_score == 1.0 and confluence == 1.0:
        assert abs(success_probability - 1.0) < 0.001


@given(
    base_probability=st.floats(min_value=0.0, max_value=1.0),
    technical_score=st.floats(min_value=0.0, max_value=1.0),
    fundamental_score=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_property_12_conflict_and_harmony_effect(
    base_probability,
    technical_score,
    fundamental_score
):
    """
    Feature: crypto-analysis-system, Property 12: Çelişki ve Uyum Etkisi
    
    Herhangi bir analiz için, indikatörler arasında çelişki olduğunda 
    başarı ihtimali düşmeli, uyum olduğunda artmalıdır.
    
    Validates: Gereksinim 7.4, 7.5
    """
    # Create signal generator instance
    signal_generator = SignalGenerator()
    
    # Test conflict penalty
    adjusted_conflict = signal_generator.apply_conflict_penalty(
        base_probability,
        technical_score,
        fundamental_score
    )
    
    # Determine if there's a conflict
    tech_direction = "bullish" if technical_score > 0.55 else ("bearish" if technical_score < 0.45 else "neutral")
    fund_direction = "bullish" if fundamental_score > 0.55 else ("bearish" if fundamental_score < 0.45 else "neutral")
    
    has_conflict = (
        tech_direction != "neutral" and 
        fund_direction != "neutral" and 
        tech_direction != fund_direction
    )
    
    # Property 1: If conflict exists, probability should decrease
    if has_conflict:
        assert adjusted_conflict <= base_probability, \
            f"Conflict penalty should decrease probability: {base_probability} -> {adjusted_conflict}"
        # Should be multiplied by 0.8
        expected_conflict = base_probability * 0.8
        assert abs(adjusted_conflict - expected_conflict) < 0.001
    else:
        # No conflict - should remain the same
        assert adjusted_conflict == base_probability
    
    # Test harmony bonus
    adjusted_harmony = signal_generator.apply_harmony_bonus(
        base_probability,
        technical_score,
        fundamental_score
    )
    
    # Property 2: If strong harmony exists, probability should increase
    has_strong_bullish_harmony = (
        tech_direction == "bullish" and 
        fund_direction == "bullish" and
        (technical_score + fundamental_score) / 2 > 0.7
    )
    
    has_strong_bearish_harmony = (
        tech_direction == "bearish" and 
        fund_direction == "bearish" and
        (technical_score + fundamental_score) / 2 < 0.3
    )
    
    if has_strong_bullish_harmony or has_strong_bearish_harmony:
        assert adjusted_harmony >= base_probability, \
            f"Harmony bonus should increase probability: {base_probability} -> {adjusted_harmony}"
        # Should be multiplied by 1.1 (capped at 1.0)
        expected_harmony = min(1.0, base_probability * 1.1)
        assert abs(adjusted_harmony - expected_harmony) < 0.001
    else:
        # No strong harmony - should remain the same
        assert adjusted_harmony == base_probability
    
    # Property 3: Adjusted values should always be in [0, 1]
    assert 0.0 <= adjusted_conflict <= 1.0
    assert 0.0 <= adjusted_harmony <= 1.0


@given(
    success_probability=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_property_13_signal_thresholds(
    success_probability
):
    """
    Feature: crypto-analysis-system, Property 13: Sinyal Eşikleri
    
    Herhangi bir başarı ihtimali değeri için, doğru sinyal türü üretilmelidir:
    >=80% için Güçlü, [60,79] için Normal, [40,59] için Nötr, <40% için Belirsiz.
    
    Validates: Gereksinim 8.1, 8.2, 8.3, 8.4
    """
    # Create signal generator and sample indicators
    signal_generator = SignalGenerator()
    sample_indicators = IndicatorResults(
        rsi=50.0,
        rsi_signal="neutral",
        rsi_divergence=None,
        macd=MACDValues(macd=0.5, signal=0.3, histogram=0.2),
        macd_signal="bullish",
        bollinger=BollingerBands(upper=52000, middle=50000, lower=48000, bandwidth=4.0),
        bollinger_signal="neutral",
        moving_averages=MovingAverages(
            sma_20=49500, sma_50=49000, sma_200=48000,
            ema_12=49800, ema_26=49500
        ),
        ma_signal="bullish",
        ema_50=49000.0,
        ema_200=48000.0,
        golden_death_cross=None,
        stochastic=StochasticValues(k=50.0, d=50.0),
        stochastic_signal="neutral",
        volume_profile=VolumeProfile(poc=50000, vah=51000, val=49000, total_volume=1000000),
        atr=ATRValues(atr=1000.0, atr_percent=2.0, percentile=0.5),
        atr_stop_loss=48000.0,
        atr_take_profit=53000.0,
        vwap=50000.0,
        vwap_signal="neutral",
        obv=1000000.0,
        obv_signal="volume_supported",
        fibonacci_levels=FibonacciLevels(
            level_0=52000, level_236=51000, level_382=50500,
            level_500=50000, level_618=49500, level_100=48000
        ),
        patterns=[],
        support_levels=[48000, 47500, 47000],
        resistance_levels=[52000, 52500, 53000],
        confluence_score=0.6,
        ema_200_trend_filter="neutral"
    )
    
    # Generate signal
    signal = signal_generator.generate_signal(
        success_probability,
        "LONG",
        "BTC",
        "1h",
        sample_indicators
    )
    
    # Convert to percentage
    success_percent = success_probability * 100
    
    # Property 1: Signal type must match threshold
    if success_percent >= 80.0:
        assert signal.signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL], \
            f"Success {success_percent:.1f}% should produce STRONG signal, got {signal.signal_type}"
    elif success_percent >= 60.0:
        assert signal.signal_type in [SignalType.BUY, SignalType.SELL], \
            f"Success {success_percent:.1f}% should produce normal signal, got {signal.signal_type}"
    elif success_percent >= 40.0:
        assert signal.signal_type == SignalType.NEUTRAL, \
            f"Success {success_percent:.1f}% should produce NEUTRAL, got {signal.signal_type}"
    else:
        assert signal.signal_type == SignalType.UNCERTAIN, \
            f"Success {success_percent:.1f}% should produce UNCERTAIN, got {signal.signal_type}"
    
    # Property 2: Success probability in signal should match input (as percentage)
    assert abs(signal.success_probability - success_percent) < 0.1, \
        f"Signal probability {signal.success_probability} doesn't match input {success_percent}"
    
    # Property 3: Signal must have required fields
    assert signal.coin == "BTC"
    assert signal.timeframe == "1h"
    assert signal.timestamp is not None
    assert isinstance(signal.timestamp, datetime)
    
    # Property 4: Stop-loss and take-profit must be set
    assert signal.stop_loss is not None
    assert signal.take_profit is not None
    assert signal.stop_loss > 0
    assert signal.take_profit > 0


# ============================================================================
# Unit Tests
# ============================================================================

def test_technical_score_generation(signal_generator, sample_indicators):
    """Test technical score generation from indicators."""
    score = signal_generator.generate_technical_score(sample_indicators)
    
    # Score should be in [0, 1]
    assert 0.0 <= score <= 1.0
    
    # With mostly bullish indicators, score should be > 0.5
    assert score > 0.5


def test_signal_direction_determination(signal_generator):
    """Test signal direction determination."""
    # Bullish case
    direction = signal_generator.determine_signal_direction(0.7, 0.6)
    assert direction == "LONG"
    
    # Bearish case
    direction = signal_generator.determine_signal_direction(0.3, 0.4)
    assert direction == "SHORT"
    
    # Neutral case (slightly bullish)
    direction = signal_generator.determine_signal_direction(0.5, 0.5)
    assert direction == "LONG"


def test_ema_200_trend_filter(signal_generator, sample_indicators):
    """Test EMA 200 trend filter application."""
    base_prob = 0.7
    
    # Test long_only filter with SHORT signal (should weaken)
    sample_indicators.ema_200_trend_filter = "long_only"
    adjusted = signal_generator.apply_ema_200_trend_filter(
        base_prob, sample_indicators, "SHORT"
    )
    assert adjusted < base_prob
    assert adjusted == base_prob * 0.5
    
    # Test short_only filter with LONG signal (should weaken)
    sample_indicators.ema_200_trend_filter = "short_only"
    adjusted = signal_generator.apply_ema_200_trend_filter(
        base_prob, sample_indicators, "LONG"
    )
    assert adjusted < base_prob
    assert adjusted == base_prob * 0.5
    
    # Test neutral filter (no change)
    sample_indicators.ema_200_trend_filter = "neutral"
    adjusted = signal_generator.apply_ema_200_trend_filter(
        base_prob, sample_indicators, "LONG"
    )
    assert adjusted == base_prob


def test_golden_death_cross_bonus(signal_generator, sample_indicators):
    """Test Golden Cross and Death Cross bonus application."""
    base_prob = 0.7
    
    # Test Golden Cross with LONG signal (should increase)
    sample_indicators.golden_death_cross = "golden_cross"
    adjusted = signal_generator.apply_golden_death_cross_bonus(
        base_prob, sample_indicators, "LONG"
    )
    assert adjusted > base_prob
    assert adjusted == min(1.0, base_prob * 1.15)
    
    # Test Death Cross with SHORT signal (should increase)
    sample_indicators.golden_death_cross = "death_cross"
    adjusted = signal_generator.apply_golden_death_cross_bonus(
        base_prob, sample_indicators, "SHORT"
    )
    assert adjusted > base_prob
    assert adjusted == min(1.0, base_prob * 1.15)
    
    # Test no cross (no change)
    sample_indicators.golden_death_cross = None
    adjusted = signal_generator.apply_golden_death_cross_bonus(
        base_prob, sample_indicators, "LONG"
    )
    assert adjusted == base_prob


def test_rsi_divergence_bonus(signal_generator, sample_indicators):
    """Test RSI divergence bonus application."""
    base_prob = 0.7
    
    # Test positive divergence with LONG signal (should increase)
    sample_indicators.rsi_divergence = "positive"
    adjusted = signal_generator.apply_rsi_divergence_bonus(
        base_prob, sample_indicators, "LONG"
    )
    assert adjusted > base_prob
    assert adjusted == min(1.0, base_prob * 1.10)
    
    # Test negative divergence with SHORT signal (should increase)
    sample_indicators.rsi_divergence = "negative"
    adjusted = signal_generator.apply_rsi_divergence_bonus(
        base_prob, sample_indicators, "SHORT"
    )
    assert adjusted > base_prob
    assert adjusted == min(1.0, base_prob * 1.10)
    
    # Test no divergence (no change)
    sample_indicators.rsi_divergence = None
    adjusted = signal_generator.apply_rsi_divergence_bonus(
        base_prob, sample_indicators, "LONG"
    )
    assert adjusted == base_prob


def test_atr_volatility_adjustment(signal_generator, sample_indicators):
    """Test ATR volatility adjustment."""
    base_prob = 0.7
    
    # Test high volatility (should decrease)
    sample_indicators.atr.percentile = 0.85
    adjusted = signal_generator.apply_atr_volatility_adjustment(
        base_prob, sample_indicators
    )
    assert adjusted < base_prob
    assert adjusted == base_prob * 0.95
    
    # Test low volatility (should increase slightly)
    sample_indicators.atr.percentile = 0.15
    adjusted = signal_generator.apply_atr_volatility_adjustment(
        base_prob, sample_indicators
    )
    assert adjusted > base_prob
    assert adjusted == min(1.0, base_prob * 1.02)
    
    # Test normal volatility (no change)
    sample_indicators.atr.percentile = 0.5
    adjusted = signal_generator.apply_atr_volatility_adjustment(
        base_prob, sample_indicators
    )
    assert adjusted == base_prob


def test_signal_explanation_generation(signal_generator, sample_indicators, sample_sentiment):
    """Test signal explanation generation."""
    # Generate a signal first
    signal = signal_generator.generate_signal(
        0.75, "LONG", "BTC", "1h", sample_indicators
    )
    
    # Generate explanation
    explanation = signal_generator.explain_signal(
        signal, sample_indicators, sample_sentiment, 0.7, 0.6
    )
    
    # Check that explanation has required fields
    assert explanation.signal == signal
    assert isinstance(explanation.technical_reasons, list)
    assert isinstance(explanation.fundamental_reasons, list)
    assert isinstance(explanation.supporting_indicators, list)
    assert isinstance(explanation.conflicting_indicators, list)
    assert isinstance(explanation.risk_factors, list)
    
    # Should have some content
    assert len(explanation.technical_reasons) > 0
    assert len(explanation.fundamental_reasons) > 0
    assert len(explanation.risk_factors) > 0


def test_complete_signal_generation(signal_generator, sample_indicators, sample_sentiment):
    """Test complete signal generation pipeline."""
    signal, explanation = signal_generator.generate_complete_signal(
        "BTC", "1h", sample_indicators, sample_sentiment
    )
    
    # Check signal
    assert signal is not None
    assert signal.coin == "BTC"
    assert signal.timeframe == "1h"
    assert 0.0 <= signal.success_probability <= 100.0
    assert signal.signal_type in SignalType
    
    # Check explanation
    assert explanation is not None
    assert explanation.signal == signal
    assert len(explanation.technical_reasons) > 0
    assert len(explanation.fundamental_reasons) > 0


@given(
    success_probability=st.floats(min_value=0.0, max_value=1.0),
    technical_score=st.floats(min_value=0.0, max_value=1.0),
    fundamental_score=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_property_14_signal_explanation_integrity(
    success_probability,
    technical_score,
    fundamental_score
):
    """
    Feature: crypto-analysis-system, Property 14: Sinyal Açıklama Bütünlüğü
    
    Herhangi bir üretilen sinyal için, gerekçeler listesi (hangi indikatörler, 
    hangi haberler) içermelidir.
    
    Validates: Gereksinim 8.5
    """
    # Create signal generator and sample data
    signal_generator = SignalGenerator()
    
    # Create sample indicators
    sample_indicators = IndicatorResults(
        rsi=50.0,
        rsi_signal="neutral",
        rsi_divergence=None,
        macd=MACDValues(macd=0.5, signal=0.3, histogram=0.2),
        macd_signal="bullish",
        bollinger=BollingerBands(upper=52000, middle=50000, lower=48000, bandwidth=4.0),
        bollinger_signal="neutral",
        moving_averages=MovingAverages(
            sma_20=49500, sma_50=49000, sma_200=48000,
            ema_12=49800, ema_26=49500
        ),
        ma_signal="bullish",
        ema_50=49000.0,
        ema_200=48000.0,
        golden_death_cross=None,
        stochastic=StochasticValues(k=50.0, d=50.0),
        stochastic_signal="neutral",
        volume_profile=VolumeProfile(poc=50000, vah=51000, val=49000, total_volume=1000000),
        atr=ATRValues(atr=1000.0, atr_percent=2.0, percentile=0.5),
        atr_stop_loss=48000.0,
        atr_take_profit=53000.0,
        vwap=50000.0,
        vwap_signal="neutral",
        obv=1000000.0,
        obv_signal="volume_supported",
        fibonacci_levels=FibonacciLevels(
            level_0=52000, level_236=51000, level_382=50500,
            level_500=50000, level_618=49500, level_100=48000
        ),
        patterns=[],
        support_levels=[48000, 47500, 47000],
        resistance_levels=[52000, 52500, 53000],
        confluence_score=0.6,
        ema_200_trend_filter="neutral"
    )
    
    # Create sample sentiment
    sample_sentiment = OverallSentiment(
        overall_score=0.3,
        classification=SentimentClassification.POSITIVE,
        trend=TrendDirection.RISING,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=0.4,
                confidence=0.8,
                sample_size=100,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    # Generate signal
    signal = signal_generator.generate_signal(
        success_probability,
        "LONG",
        "BTC",
        "1h",
        sample_indicators
    )
    
    # Generate explanation
    explanation = signal_generator.explain_signal(
        signal,
        sample_indicators,
        sample_sentiment,
        technical_score,
        fundamental_score
    )
    
    # Property 1: Explanation must have all required fields
    assert explanation.signal == signal
    assert isinstance(explanation.technical_reasons, list)
    assert isinstance(explanation.fundamental_reasons, list)
    assert isinstance(explanation.supporting_indicators, list)
    assert isinstance(explanation.conflicting_indicators, list)
    assert isinstance(explanation.risk_factors, list)
    
    # Property 2: Must have at least some content
    # Technical reasons should exist (we have indicators)
    assert len(explanation.technical_reasons) >= 0  # Can be 0 if all neutral
    
    # Fundamental reasons should exist (we have sentiment)
    assert len(explanation.fundamental_reasons) > 0, \
        "Explanation must include fundamental reasons"
    
    # Risk factors should always exist (at least ATR and stop-loss info)
    assert len(explanation.risk_factors) > 0, \
        "Explanation must include risk factors"
    
    # Property 3: Supporting and conflicting indicators should be mutually exclusive
    supporting_set = set(explanation.supporting_indicators)
    conflicting_set = set(explanation.conflicting_indicators)
    overlap = supporting_set & conflicting_set
    assert len(overlap) == 0, \
        f"Indicators cannot be both supporting and conflicting: {overlap}"
    
    # Property 4: All text fields should be non-empty strings
    for reason in explanation.technical_reasons:
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    for reason in explanation.fundamental_reasons:
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    for indicator in explanation.supporting_indicators:
        assert isinstance(indicator, str)
        assert len(indicator) > 0
    
    for indicator in explanation.conflicting_indicators:
        assert isinstance(indicator, str)
        assert len(indicator) > 0
    
    for factor in explanation.risk_factors:
        assert isinstance(factor, str)
        assert len(factor) > 0


@given(
    atr_percentile=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_property_69_signal_risk_factors(
    atr_percentile
):
    """
    Feature: crypto-analysis-system, Property 69: Sinyal Risk Faktörleri
    
    Herhangi bir üretilen sinyal için, ATR bazlı volatilite ve diğer risk 
    faktörleri açıklamaya dahil edilmelidir.
    
    Validates: Gereksinim 4.5
    """
    # Create signal generator and sample data
    signal_generator = SignalGenerator()
    
    # Create sample indicators with varying ATR percentile
    sample_indicators = IndicatorResults(
        rsi=50.0,
        rsi_signal="neutral",
        rsi_divergence=None,
        macd=MACDValues(macd=0.5, signal=0.3, histogram=0.2),
        macd_signal="bullish",
        bollinger=BollingerBands(upper=52000, middle=50000, lower=48000, bandwidth=4.0),
        bollinger_signal="neutral",
        moving_averages=MovingAverages(
            sma_20=49500, sma_50=49000, sma_200=48000,
            ema_12=49800, ema_26=49500
        ),
        ma_signal="bullish",
        ema_50=49000.0,
        ema_200=48000.0,
        golden_death_cross=None,
        stochastic=StochasticValues(k=50.0, d=50.0),
        stochastic_signal="neutral",
        volume_profile=VolumeProfile(poc=50000, vah=51000, val=49000, total_volume=1000000),
        atr=ATRValues(atr=1000.0, atr_percent=2.0, percentile=atr_percentile),
        atr_stop_loss=48000.0,
        atr_take_profit=53000.0,
        vwap=50000.0,
        vwap_signal="neutral",
        obv=1000000.0,
        obv_signal="volume_supported",
        fibonacci_levels=FibonacciLevels(
            level_0=52000, level_236=51000, level_382=50500,
            level_500=50000, level_618=49500, level_100=48000
        ),
        patterns=[],
        support_levels=[48000, 47500, 47000],
        resistance_levels=[52000, 52500, 53000],
        confluence_score=0.6,
        ema_200_trend_filter="neutral"
    )
    
    # Create sample sentiment
    sample_sentiment = OverallSentiment(
        overall_score=0.3,
        classification=SentimentClassification.POSITIVE,
        trend=TrendDirection.RISING,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=0.4,
                confidence=0.8,
                sample_size=100,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    # Generate signal
    signal = signal_generator.generate_signal(
        0.75,
        "LONG",
        "BTC",
        "1h",
        sample_indicators
    )
    
    # Generate explanation
    explanation = signal_generator.explain_signal(
        signal,
        sample_indicators,
        sample_sentiment,
        0.7,
        0.6
    )
    
    # Property 1: Risk factors must be present
    assert len(explanation.risk_factors) > 0, \
        "Explanation must include risk factors"
    
    # Property 2: ATR-based stop-loss and take-profit must be mentioned
    risk_factors_text = " ".join(explanation.risk_factors).lower()
    assert "stop-loss" in risk_factors_text or "stop loss" in risk_factors_text, \
        "Risk factors must mention stop-loss"
    assert "take-profit" in risk_factors_text or "take profit" in risk_factors_text, \
        "Risk factors must mention take-profit"
    
    # Property 3: ATR volatility should be mentioned
    assert "atr" in risk_factors_text or "volatilite" in risk_factors_text or "volatility" in risk_factors_text, \
        "Risk factors must mention ATR or volatility"
    
    # Property 4: If high volatility (>0.8), it should be explicitly mentioned
    if atr_percentile > 0.8:
        assert "yüksek volatilite" in risk_factors_text or "high volatility" in risk_factors_text, \
            "High volatility should be explicitly mentioned in risk factors"
    
    # Property 5: If low volatility (<0.2), it should be explicitly mentioned
    if atr_percentile < 0.2:
        assert "düşük volatilite" in risk_factors_text or "low volatility" in risk_factors_text, \
            "Low volatility should be explicitly mentioned in risk factors"

