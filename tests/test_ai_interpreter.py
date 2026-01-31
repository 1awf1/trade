"""
Property-based and unit tests for AI Interpreter.
Tests AI interpretation output, technical term explanations, and Turkish language support.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from engines.ai_interpreter import AIInterpreter
from models.schemas import (
    IndicatorResults, OverallSentiment, Signal, SignalExplanation,
    SignalType, SentimentClassification, TrendDirection,
    MACDValues, BollingerBands, MovingAverages, StochasticValues,
    VolumeProfile, ATRValues, FibonacciLevels, SentimentResults
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def ai_interpreter():
    """Create an AI interpreter instance (without OpenAI API for testing)."""
    # Use fallback mode for testing (no API key)
    return AIInterpreter(api_key=None)


@pytest.fixture
def sample_indicators():
    """Create sample indicator results."""
    return IndicatorResults(
        rsi=55.0,
        rsi_signal="neutral",
        rsi_divergence="positive",
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
        golden_death_cross="golden_cross",
        stochastic=StochasticValues(k=55.0, d=50.0),
        stochastic_signal="neutral",
        volume_profile=VolumeProfile(poc=50000, vah=51000, val=49000, total_volume=1000000),
        atr=ATRValues(atr=1000.0, atr_percent=2.0, percentile=0.5),
        atr_stop_loss=48000.0,
        atr_take_profit=53000.0,
        vwap=50100.0,
        vwap_signal="above",
        obv=1000000.0,
        obv_signal="volume_supported",
        fibonacci_levels=FibonacciLevels(
            level_0=52000, level_236=51000, level_382=50500,
            level_500=50000, level_618=49500, level_100=48000
        ),
        patterns=[],
        support_levels=[48000, 47500, 47000],
        resistance_levels=[52000, 52500, 53000],
        confluence_score=0.7,
        ema_200_trend_filter="long_only"
    )


@pytest.fixture
def sample_sentiment():
    """Create sample sentiment results."""
    return OverallSentiment(
        overall_score=0.4,
        classification=SentimentClassification.POSITIVE,
        trend=TrendDirection.RISING,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=0.5,
                confidence=0.8,
                sample_size=150,
                timestamp=datetime.utcnow()
            ),
            SentimentResults(
                source="reddit",
                sentiment_score=0.3,
                confidence=0.7,
                sample_size=80,
                timestamp=datetime.utcnow()
            )
        ]
    )


@pytest.fixture
def sample_signal():
    """Create sample signal."""
    return Signal(
        signal_type=SignalType.BUY,
        success_probability=72.5,
        timestamp=datetime.utcnow(),
        coin="BTC",
        timeframe="4h",
        stop_loss=48000.0,
        take_profit=53000.0,
        ema_200_filter_applied=True,
        golden_death_cross_detected="golden_cross",
        rsi_divergence_detected="positive"
    )


@pytest.fixture
def sample_explanation(sample_signal):
    """Create sample signal explanation."""
    return SignalExplanation(
        signal=sample_signal,
        technical_reasons=[
            "RSI pozitif divergence gösteriyor",
            "MACD yükseliş sinyali veriyor",
            "Golden Cross tespit edildi"
        ],
        fundamental_reasons=[
            "Piyasa duygusu pozitif",
            "Sosyal medya aktivitesi artıyor"
        ],
        supporting_indicators=["RSI", "MACD", "Golden Cross", "VWAP"],
        conflicting_indicators=[],
        risk_factors=["Orta seviye volatilite"]
    )


# ============================================================================
# Property-Based Tests
# ============================================================================

@given(
    rsi=st.floats(min_value=0.0, max_value=100.0),
    macd_histogram=st.floats(min_value=-10.0, max_value=10.0),
    confluence=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_property_15_ai_interpretation_output(
    rsi,
    macd_histogram,
    confluence
):
    """
    Feature: crypto-analysis-system, Property 15: AI Yorumlama Çıktısı
    
    Herhangi bir analiz sonucu için, AI yorumlayıcı teknik ve temel analiz 
    açıklamaları ile kapsamlı bir rapor üretmelidir ve tüm çıktılar Türkçe olmalıdır.
    
    Validates: Gereksinim 9.1, 9.2, 9.3, 9.4
    """
    # Create AI interpreter instance
    ai_interpreter = AIInterpreter(api_key=None)
    
    # Create indicators with random values
    indicators = IndicatorResults(
        rsi=rsi,
        rsi_signal="oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral",
        rsi_divergence=None,
        macd=MACDValues(
            macd=macd_histogram + 0.5,
            signal=0.5,
            histogram=macd_histogram
        ),
        macd_signal="bullish" if macd_histogram > 0 else "bearish",
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
        confluence_score=confluence,
        ema_200_trend_filter="neutral"
    )
    
    sentiment = OverallSentiment(
        overall_score=0.3,
        classification=SentimentClassification.POSITIVE,
        trend=TrendDirection.STABLE,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=0.3,
                confidence=0.7,
                sample_size=100,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    signal = Signal(
        signal_type=SignalType.BUY,
        success_probability=65.0,
        timestamp=datetime.utcnow(),
        coin="BTC",
        timeframe="4h",
        stop_loss=48000.0,
        take_profit=53000.0,
        ema_200_filter_applied=False,
        golden_death_cross_detected=None,
        rsi_divergence_detected=None
    )
    
    explanation = SignalExplanation(
        signal=signal,
        technical_reasons=["Test reason"],
        fundamental_reasons=["Test reason"],
        supporting_indicators=["RSI"],
        conflicting_indicators=[],
        risk_factors=[]
    )
    
    # Test technical interpretation
    technical_interp = ai_interpreter.interpret_technical(indicators)
    
    # Property 1: Output must not be empty
    assert technical_interp is not None
    assert len(technical_interp) > 0
    
    # Property 2: Output must be a string
    assert isinstance(technical_interp, str)
    
    # Property 3: Output should contain Turkish characters or common Turkish words
    # (fallback mode uses Turkish templates)
    turkish_indicators = [
        've', 'veya', 'için', 'ile', 'bu', 'bir', 'olan',  # Common Turkish words
        'ş', 'ğ', 'ı', 'ö', 'ü', 'ç'  # Turkish characters
    ]
    has_turkish = any(indicator in technical_interp.lower() for indicator in turkish_indicators)
    assert has_turkish, "Output should contain Turkish language elements"
    
    # Test fundamental interpretation
    fundamental_interp = ai_interpreter.interpret_fundamental(sentiment)
    
    # Property 4: Fundamental interpretation must not be empty
    assert fundamental_interp is not None
    assert len(fundamental_interp) > 0
    assert isinstance(fundamental_interp, str)
    
    # Property 5: Should contain Turkish language elements
    has_turkish_fund = any(indicator in fundamental_interp.lower() for indicator in turkish_indicators)
    assert has_turkish_fund, "Fundamental output should contain Turkish language elements"
    
    # Test comprehensive report
    report = ai_interpreter.generate_report(signal, explanation, indicators, sentiment)
    
    # Property 6: Report must not be empty
    assert report is not None
    assert len(report) > 0
    assert isinstance(report, str)
    
    # Property 7: Report should be comprehensive (longer than individual interpretations)
    assert len(report) > len(technical_interp)
    assert len(report) > len(fundamental_interp)
    
    # Property 8: Report should contain key information
    assert signal.coin in report
    assert signal.timeframe in report
    assert str(signal.success_probability) in report or f"{signal.success_probability:.1f}" in report
    
    # Property 9: Report should contain Turkish language elements
    has_turkish_report = any(indicator in report.lower() for indicator in turkish_indicators)
    assert has_turkish_report, "Report should contain Turkish language elements"
    
    # Property 10: Report should mention signal type
    signal_mentioned = (
        signal.signal_type.value in report or
        "AL" in report.upper() or
        "SAT" in report.upper() or
        "NÖTR" in report.upper()
    )
    assert signal_mentioned, "Report should mention the signal type"


@given(
    sentiment_score=st.floats(min_value=-1.0, max_value=1.0),
    sample_size=st.integers(min_value=1, max_value=1000)
)
@settings(max_examples=100, deadline=None)
def test_property_15_fundamental_interpretation_completeness(
    sentiment_score,
    sample_size
):
    """
    Test that fundamental interpretation is complete for any sentiment data.
    
    Validates: Gereksinim 9.2 - Temel analiz özeti
    """
    # Create AI interpreter instance
    ai_interpreter = AIInterpreter(api_key=None)
    
    # Determine classification based on score
    if sentiment_score > 0.2:
        classification = SentimentClassification.POSITIVE
    elif sentiment_score < -0.2:
        classification = SentimentClassification.NEGATIVE
    else:
        classification = SentimentClassification.NEUTRAL
    
    sentiment = OverallSentiment(
        overall_score=sentiment_score,
        classification=classification,
        trend=TrendDirection.STABLE,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=sentiment_score,
                confidence=0.7,
                sample_size=sample_size,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    # Generate interpretation
    interpretation = ai_interpreter.interpret_fundamental(sentiment)
    
    # Property 1: Must return non-empty string
    assert interpretation is not None
    assert isinstance(interpretation, str)
    assert len(interpretation) > 0
    
    # Property 2: Should mention sentiment classification
    classification_mentioned = (
        classification.value in interpretation.lower() or
        "pozitif" in interpretation.lower() or
        "negatif" in interpretation.lower() or
        "nötr" in interpretation.lower()
    )
    assert classification_mentioned, "Interpretation should mention sentiment classification"
    
    # Property 3: Should be in Turkish
    turkish_words = ['duygu', 'piyasa', 'analiz', 'skor', 'trend']
    has_turkish_words = any(word in interpretation.lower() for word in turkish_words)
    assert has_turkish_words, "Interpretation should contain Turkish words"


@given(
    success_probability=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_property_15_report_contains_all_sections(
    success_probability
):
    """
    Test that comprehensive report contains all required sections.
    
    Validates: Gereksinim 9.3 - Kapsamlı rapor üretimi
    """
    # Create AI interpreter instance
    ai_interpreter = AIInterpreter(api_key=None)
    
    # Create sample indicators
    sample_indicators = IndicatorResults(
        rsi=55.0,
        rsi_signal="neutral",
        rsi_divergence="positive",
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
        golden_death_cross="golden_cross",
        stochastic=StochasticValues(k=55.0, d=50.0),
        stochastic_signal="neutral",
        volume_profile=VolumeProfile(poc=50000, vah=51000, val=49000, total_volume=1000000),
        atr=ATRValues(atr=1000.0, atr_percent=2.0, percentile=0.5),
        atr_stop_loss=48000.0,
        atr_take_profit=53000.0,
        vwap=50100.0,
        vwap_signal="above",
        obv=1000000.0,
        obv_signal="volume_supported",
        fibonacci_levels=FibonacciLevels(
            level_0=52000, level_236=51000, level_382=50500,
            level_500=50000, level_618=49500, level_100=48000
        ),
        patterns=[],
        support_levels=[48000, 47500, 47000],
        resistance_levels=[52000, 52500, 53000],
        confluence_score=0.7,
        ema_200_trend_filter="long_only"
    )
    
    # Create sample sentiment
    sample_sentiment = OverallSentiment(
        overall_score=0.4,
        classification=SentimentClassification.POSITIVE,
        trend=TrendDirection.RISING,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=0.5,
                confidence=0.8,
                sample_size=150,
                timestamp=datetime.utcnow()
            ),
            SentimentResults(
                source="reddit",
                sentiment_score=0.3,
                confidence=0.7,
                sample_size=80,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    # Determine signal type based on success probability
    if success_probability >= 80:
        signal_type = SignalType.STRONG_BUY
    elif success_probability >= 60:
        signal_type = SignalType.BUY
    elif success_probability >= 40:
        signal_type = SignalType.NEUTRAL
    else:
        signal_type = SignalType.UNCERTAIN
    
    signal = Signal(
        signal_type=signal_type,
        success_probability=success_probability,
        timestamp=datetime.utcnow(),
        coin="ETH",
        timeframe="1h",
        stop_loss=3000.0,
        take_profit=3500.0,
        ema_200_filter_applied=False,
        golden_death_cross_detected=None,
        rsi_divergence_detected=None
    )
    
    explanation = SignalExplanation(
        signal=signal,
        technical_reasons=["Technical reason 1", "Technical reason 2"],
        fundamental_reasons=["Fundamental reason 1"],
        supporting_indicators=["RSI", "MACD"],
        conflicting_indicators=[],
        risk_factors=["Risk factor 1"]
    )
    
    # Generate report
    report = ai_interpreter.generate_report(signal, explanation, sample_indicators, sample_sentiment)
    
    # Property 1: Report must be comprehensive (minimum length)
    assert len(report) > 500, "Report should be comprehensive (at least 500 characters)"
    
    # Property 2: Report should contain coin and timeframe
    assert signal.coin in report
    assert signal.timeframe in report
    
    # Property 3: Report should contain success probability
    prob_str = f"{success_probability:.1f}" if success_probability % 1 != 0 else f"{int(success_probability)}"
    assert prob_str in report or str(int(success_probability)) in report
    
    # Property 4: Report should contain stop-loss and take-profit
    assert str(int(signal.stop_loss)) in report or f"{signal.stop_loss:.0f}" in report
    assert str(int(signal.take_profit)) in report or f"{signal.take_profit:.0f}" in report
    
    # Property 5: Report should be in Turkish
    turkish_section_words = ['özet', 'analiz', 'değerlendirme', 'öneri', 'risk', 'sonuç']
    turkish_words_found = sum(1 for word in turkish_section_words if word in report.lower())
    assert turkish_words_found >= 3, "Report should contain multiple Turkish section keywords"


# ============================================================================
# Property-Based Tests for Technical Term Explanations
# ============================================================================

@given(
    term_count=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100, deadline=None)
def test_property_16_technical_term_explanation(
    term_count
):
    """
    Feature: crypto-analysis-system, Property 16: Teknik Terim Açıklaması
    
    Herhangi bir AI yorumunda kullanılan teknik terim için, açıklama sağlanmalıdır.
    
    Validates: Gereksinim 9.5
    """
    # Create AI interpreter instance
    ai_interpreter = AIInterpreter(api_key=None)
    
    # Get available technical terms
    available_terms = list(ai_interpreter.technical_terms.keys())
    
    if term_count == 0 or not available_terms:
        # Test with no terms
        text = "Bu bir test metnidir."
        detected = ai_interpreter._detect_technical_terms(text)
        
        # Property 1: Should return empty list for text without terms
        assert isinstance(detected, list)
        assert len(detected) == 0
        
        # Property 2: Adding explanations to text without terms should not change it much
        text_with_explanations = ai_interpreter._add_term_explanations(text, detected)
        assert text in text_with_explanations
        
    else:
        # Select random terms (up to available count)
        import random
        selected_terms = random.sample(available_terms, min(term_count, len(available_terms)))
        
        # Create text containing these terms
        text = f"Bu analizde {', '.join(selected_terms)} kullanılmıştır."
        
        # Detect terms
        detected = ai_interpreter._detect_technical_terms(text)
        
        # Property 3: Should detect all terms that are in the text
        for term in selected_terms:
            assert term in detected, f"Term '{term}' should be detected"
        
        # Property 4: Detected terms should be in technical terms dictionary
        for term in detected:
            assert term in ai_interpreter.technical_terms
        
        # Property 5: Adding explanations should include all detected terms
        text_with_explanations = ai_interpreter._add_term_explanations(text, detected)
        
        # Should contain original text
        assert text in text_with_explanations or all(term in text_with_explanations for term in selected_terms)
        
        # Should contain explanations section if terms were detected
        if detected:
            assert "Teknik Terimler" in text_with_explanations or "Sözlük" in text_with_explanations
            
            # Each detected term should have its explanation
            for term in detected:
                explanation = ai_interpreter.technical_terms[term]
                # At least the term name should appear in the explanations section
                assert term in text_with_explanations


def test_property_16_all_technical_terms_have_explanations():
    """
    Test that all technical terms in the dictionary have non-empty explanations.
    
    Validates: Gereksinim 9.5
    """
    # Create AI interpreter instance
    ai_interpreter = AIInterpreter(api_key=None)
    
    # Property: Every term in the dictionary must have a non-empty explanation
    for term, explanation in ai_interpreter.technical_terms.items():
        assert term is not None
        assert isinstance(term, str)
        assert len(term) > 0
        
        assert explanation is not None
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        
        # Explanation should be in Turkish (contain Turkish characters or words)
        turkish_indicators = ['ş', 'ğ', 'ı', 'ö', 'ü', 'ç', 've', 'bir', 'için']
        has_turkish = any(indicator in explanation.lower() for indicator in turkish_indicators)
        assert has_turkish, f"Explanation for '{term}' should be in Turkish"


# ============================================================================
# Unit Tests
# ============================================================================

def test_ai_interpreter_initialization():
    """Test AI interpreter initialization."""
    # Test without API key
    interpreter = AIInterpreter(api_key=None)
    assert interpreter is not None
    assert interpreter.client is None
    assert len(interpreter.technical_terms) > 0
    
    # Test with invalid API key (should not crash)
    interpreter2 = AIInterpreter(api_key="invalid_key")
    assert interpreter2 is not None


def test_technical_terms_dictionary_completeness(ai_interpreter):
    """Test that technical terms dictionary contains essential terms."""
    essential_terms = [
        "RSI", "MACD", "Bollinger Bands", "Moving Average", "EMA",
        "ATR", "VWAP", "OBV", "Fibonacci", "Golden Cross", "Death Cross",
        "Stop-Loss", "Take-Profit", "Volatility", "Bullish", "Bearish"
    ]
    
    for term in essential_terms:
        assert term in ai_interpreter.technical_terms, f"Essential term '{term}' missing"
        assert len(ai_interpreter.technical_terms[term]) > 20, f"Explanation for '{term}' too short"


def test_detect_technical_terms(ai_interpreter):
    """Test technical term detection."""
    # Test with multiple terms
    text = "RSI ve MACD göstergeleri yükseliş sinyali veriyor. Bollinger Bands nötr."
    detected = ai_interpreter._detect_technical_terms(text)
    
    assert "RSI" in detected
    assert "MACD" in detected
    assert "Bollinger Bands" in detected
    
    # Test case insensitivity
    text_lower = "rsi ve macd göstergeleri"
    detected_lower = ai_interpreter._detect_technical_terms(text_lower)
    assert "RSI" in detected_lower
    assert "MACD" in detected_lower
    
    # Test with no terms
    text_no_terms = "Bu sadece normal bir metin."
    detected_none = ai_interpreter._detect_technical_terms(text_no_terms)
    assert len(detected_none) == 0


def test_add_term_explanations(ai_interpreter):
    """Test adding term explanations to text."""
    text = "Analiz sonucu"
    terms = ["RSI", "MACD"]
    
    result = ai_interpreter._add_term_explanations(text, terms)
    
    # Should contain original text
    assert text in result
    
    # Should contain explanations section
    assert "Teknik Terimler" in result or "Sözlük" in result
    
    # Should contain both terms
    assert "RSI" in result
    assert "MACD" in result
    
    # Should contain explanations
    assert ai_interpreter.technical_terms["RSI"] in result
    assert ai_interpreter.technical_terms["MACD"] in result


def test_fallback_technical_interpretation(ai_interpreter, sample_indicators):
    """Test fallback technical interpretation."""
    interpretation = ai_interpreter._fallback_technical_interpretation(sample_indicators)
    
    assert interpretation is not None
    assert len(interpretation) > 100
    assert "RSI" in interpretation
    assert "MACD" in interpretation
    assert isinstance(interpretation, str)


def test_fallback_fundamental_interpretation(ai_interpreter, sample_sentiment):
    """Test fallback fundamental interpretation."""
    interpretation = ai_interpreter._fallback_fundamental_interpretation(sample_sentiment)
    
    assert interpretation is not None
    assert len(interpretation) > 100
    assert "duygu" in interpretation.lower() or "sentiment" in interpretation.lower()
    assert isinstance(interpretation, str)


def test_fallback_report_generation(
    ai_interpreter,
    sample_signal,
    sample_explanation,
    sample_indicators,
    sample_sentiment
):
    """Test fallback report generation."""
    report = ai_interpreter._fallback_report_generation(
        sample_signal,
        sample_explanation,
        sample_indicators,
        sample_sentiment
    )
    
    assert report is not None
    assert len(report) > 500
    assert sample_signal.coin in report
    assert sample_signal.timeframe in report
    assert isinstance(report, str)
    
    # Should contain Turkish section headers
    turkish_sections = ['özet', 'analiz', 'risk', 'öneri']
    found_sections = sum(1 for section in turkish_sections if section in report.lower())
    assert found_sections >= 2


def test_interpret_technical_with_various_indicators(ai_interpreter):
    """Test technical interpretation with various indicator combinations."""
    # Test with oversold RSI
    indicators_oversold = IndicatorResults(
        rsi=25.0,
        rsi_signal="oversold",
        rsi_divergence=None,
        macd=MACDValues(macd=-0.5, signal=-0.3, histogram=-0.2),
        macd_signal="bearish",
        bollinger=BollingerBands(upper=52000, middle=50000, lower=48000, bandwidth=4.0),
        bollinger_signal="oversold",
        moving_averages=MovingAverages(
            sma_20=49500, sma_50=49000, sma_200=48000,
            ema_12=49800, ema_26=49500
        ),
        ma_signal="bearish",
        ema_50=49000.0,
        ema_200=48000.0,
        golden_death_cross=None,
        stochastic=StochasticValues(k=15.0, d=12.0),
        stochastic_signal="oversold",
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
        confluence_score=0.3,
        ema_200_trend_filter="neutral"
    )
    
    interpretation = ai_interpreter.interpret_technical(indicators_oversold)
    
    assert interpretation is not None
    assert len(interpretation) > 0
    assert "RSI" in interpretation or "rsi" in interpretation.lower()


def test_interpret_fundamental_with_various_sentiments(ai_interpreter):
    """Test fundamental interpretation with various sentiment scenarios."""
    # Test with negative sentiment
    sentiment_negative = OverallSentiment(
        overall_score=-0.6,
        classification=SentimentClassification.NEGATIVE,
        trend=TrendDirection.FALLING,
        sources=[
            SentimentResults(
                source="twitter",
                sentiment_score=-0.7,
                confidence=0.8,
                sample_size=200,
                timestamp=datetime.utcnow()
            ),
            SentimentResults(
                source="news",
                sentiment_score=-0.5,
                confidence=0.9,
                sample_size=50,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    interpretation = ai_interpreter.interpret_fundamental(sentiment_negative)
    
    assert interpretation is not None
    assert len(interpretation) > 0
    assert "negatif" in interpretation.lower() or "negative" in interpretation.lower()

