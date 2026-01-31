"""
Property-based tests for Fundamental Analysis Engine.
Tests sentiment score range and classification properties.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from engines.fundamental_analysis import FundamentalAnalysisEngine
from models.schemas import (
    SentimentResults, 
    SentimentClassification, 
    TrendDirection,
    OverallSentiment
)



# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_sentiment_analyzer():
    """Create a mock sentiment analyzer that returns predictable results."""
    def mock_analyze(text):
        # Simple rule-based mock for testing
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_words = ['moon', 'great', 'bullish', 'amazing', 'excellent', 'strong', 'optimistic', 'gains', 'buy', 'hold']
        negative_words = ['crash', 'bearish', 'worried', 'terrible', 'scam', 'down', 'trouble', 'sell']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return [{'label': 'POSITIVE', 'score': 0.8}]
        elif neg_count > pos_count:
            return [{'label': 'NEGATIVE', 'score': 0.8}]
        else:
            return [{'label': 'POSITIVE', 'score': 0.5}]  # Neutral-ish
    
    return mock_analyze


@pytest.fixture
def engine_with_mock(mock_sentiment_analyzer):
    """Create engine with mocked sentiment analyzer."""
    engine = FundamentalAnalysisEngine()
    engine.sentiment_analyzer = mock_sentiment_analyzer
    return engine


# ============================================================================
# Test Strategies
# ============================================================================

# Strategy for generating text samples
@st.composite
def text_samples(draw):
    """Generate realistic text samples for sentiment analysis."""
    # Mix of positive, negative, and neutral phrases
    positive_phrases = [
        "Bitcoin is going to the moon! Great investment opportunity.",
        "Ethereum is showing strong bullish signals. Very optimistic about the future.",
        "Amazing gains today! The market is looking very healthy.",
        "This cryptocurrency has excellent fundamentals and strong community support.",
        "Bullish trend continues. Perfect time to buy and hold.",
    ]
    
    negative_phrases = [
        "Bitcoin is crashing hard. Time to sell everything.",
        "Ethereum looks bearish. I'm worried about my investment.",
        "Terrible market conditions. Everything is going down.",
        "This coin is a scam. Stay away from it.",
        "Bearish signals everywhere. The market is in trouble.",
    ]
    
    neutral_phrases = [
        "Bitcoin price is stable today. No major movements.",
        "Ethereum trading sideways. Waiting for a breakout.",
        "The market is consolidating. Need to wait and see.",
        "Price action is unclear. Could go either way.",
        "Holding my position. No clear direction yet.",
    ]
    
    # Randomly select phrase type
    phrase_type = draw(st.sampled_from(['positive', 'negative', 'neutral', 'mixed']))
    
    if phrase_type == 'positive':
        return draw(st.sampled_from(positive_phrases))
    elif phrase_type == 'negative':
        return draw(st.sampled_from(negative_phrases))
    elif phrase_type == 'neutral':
        return draw(st.sampled_from(neutral_phrases))
    else:  # mixed
        # Combine multiple phrases
        phrases = draw(st.lists(
            st.sampled_from(positive_phrases + negative_phrases + neutral_phrases),
            min_size=1,
            max_size=3
        ))
        return " ".join(phrases)


# Strategy for generating lists of texts
text_list_strategy = st.lists(text_samples(), min_size=1, max_size=50)

# Strategy for generating source names
source_strategy = st.sampled_from(['twitter', 'reddit', 'news', 'telegram', 'unknown'])


# ============================================================================
# Property Test 9: Duygu Skoru Aralığı
# ============================================================================

@given(
    texts=text_list_strategy,
    source=source_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
def test_property_9_sentiment_score_range(texts, source, engine_with_mock):
    """
    Feature: crypto-analysis-system, Property 9: Duygu Skoru Aralığı
    
    Herhangi bir metin içeriği için, hesaplanan duygu skoru [-1, 1] aralığında olmalıdır.
    
    Validates: Gereksinim 6.1
    """
    # Use mocked engine
    engine = engine_with_mock
    
    # Analyze sentiment
    result = engine.analyze_sentiment(texts, source=source)
    
    # Property 1: Sentiment score must be in [-1, 1] range
    assert -1.0 <= result.sentiment_score <= 1.0, (
        f"Sentiment score {result.sentiment_score} is outside [-1, 1] range"
    )
    
    # Property 2: Confidence must be in [0, 1] range
    assert 0.0 <= result.confidence <= 1.0, (
        f"Confidence {result.confidence} is outside [0, 1] range"
    )
    
    # Property 3: Sample size must match input
    assert result.sample_size == len(texts), (
        f"Sample size {result.sample_size} doesn't match input size {len(texts)}"
    )
    
    # Property 4: Source must match
    assert result.source == source, (
        f"Source {result.source} doesn't match input source {source}"
    )
    
    # Property 5: Timestamp must be recent (within last minute)
    time_diff = datetime.utcnow() - result.timestamp
    assert time_diff < timedelta(minutes=1), (
        f"Timestamp is not recent: {time_diff}"
    )


# ============================================================================
# Property Test 10: Duygu Sınıflandırması
# ============================================================================

@st.composite
def sentiment_results_list(draw):
    """Generate a list of SentimentResults for testing aggregation."""
    num_sources = draw(st.integers(min_value=1, max_value=5))
    sources = ['twitter', 'reddit', 'news', 'telegram', 'google_trends']
    
    results = []
    for i in range(num_sources):
        # Generate sentiment score in [-1, 1]
        score = draw(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False))
        
        # Generate confidence in [0, 1]
        confidence = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
        
        # Generate sample size
        sample_size = draw(st.integers(min_value=1, max_value=1000))
        
        # Create timestamp (recent)
        timestamp = datetime.utcnow() - timedelta(minutes=draw(st.integers(min_value=0, max_value=60)))
        
        result = SentimentResults(
            source=sources[i % len(sources)],
            sentiment_score=score,
            confidence=confidence,
            sample_size=sample_size,
            timestamp=timestamp
        )
        results.append(result)
    
    return results


@given(
    sentiment_results=sentiment_results_list()
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
def test_property_10_sentiment_classification(sentiment_results):
    """
    Feature: crypto-analysis-system, Property 10: Duygu Sınıflandırması
    
    Herhangi bir duygu skoru seti için, genel piyasa duygusu (pozitif/nötr/negatif) 
    ve trend (yükseliş/düşüş/sabit) belirlenmelidir.
    
    Validates: Gereksinim 6.2, 6.3
    """
    # Initialize engine
    engine = FundamentalAnalysisEngine()
    
    # Test aggregation (without trend detection)
    overall_sentiment = engine.aggregate_sentiment(sentiment_results)
    
    # Property 1: Overall score must be in [-1, 1] range
    assert -1.0 <= overall_sentiment.overall_score <= 1.0, (
        f"Overall sentiment score {overall_sentiment.overall_score} is outside [-1, 1] range"
    )
    
    # Property 2: Classification must be valid
    assert overall_sentiment.classification in [
        SentimentClassification.POSITIVE,
        SentimentClassification.NEUTRAL,
        SentimentClassification.NEGATIVE
    ], f"Invalid classification: {overall_sentiment.classification}"
    
    # Property 3: Classification must match score
    if overall_sentiment.overall_score > 0.2:
        assert overall_sentiment.classification == SentimentClassification.POSITIVE, (
            f"Score {overall_sentiment.overall_score} > 0.2 should be POSITIVE, "
            f"got {overall_sentiment.classification}"
        )
    elif overall_sentiment.overall_score < -0.2:
        assert overall_sentiment.classification == SentimentClassification.NEGATIVE, (
            f"Score {overall_sentiment.overall_score} < -0.2 should be NEGATIVE, "
            f"got {overall_sentiment.classification}"
        )
    else:
        assert overall_sentiment.classification == SentimentClassification.NEUTRAL, (
            f"Score {overall_sentiment.overall_score} in [-0.2, 0.2] should be NEUTRAL, "
            f"got {overall_sentiment.classification}"
        )
    
    # Property 4: Sources must be preserved
    assert len(overall_sentiment.sources) == len(sentiment_results), (
        f"Number of sources {len(overall_sentiment.sources)} doesn't match "
        f"input {len(sentiment_results)}"
    )
    
    # Property 5: Trend must be valid
    assert overall_sentiment.trend in [
        TrendDirection.RISING,
        TrendDirection.FALLING,
        TrendDirection.STABLE
    ], f"Invalid trend: {overall_sentiment.trend}"
    
    # Test trend detection with historical data
    if len(sentiment_results) >= 2:
        # Sort by timestamp
        sorted_results = sorted(sentiment_results, key=lambda x: x.timestamp)
        
        # Detect trend
        trend = engine.detect_sentiment_trend(sorted_results)
        
        # Property 6: Trend must be valid
        assert trend in [
            TrendDirection.RISING,
            TrendDirection.FALLING,
            TrendDirection.STABLE
        ], f"Invalid trend from detection: {trend}"
        
        # Property 7: Trend should be consistent with score changes
        # If first half average < second half average significantly, should be RISING
        # If first half average > second half average significantly, should be FALLING
        mid = len(sorted_results) // 2
        if mid > 0:
            first_half_avg = sum(r.sentiment_score for r in sorted_results[:mid]) / mid
            second_half_avg = sum(r.sentiment_score for r in sorted_results[mid:]) / (len(sorted_results) - mid)
            
            diff = second_half_avg - first_half_avg
            
            # Allow some tolerance for STABLE classification
            if diff > 0.15:  # Significant increase
                # Should be RISING or STABLE (depending on slope)
                assert trend in [TrendDirection.RISING, TrendDirection.STABLE], (
                    f"Significant increase (diff={diff:.3f}) should result in RISING or STABLE, got {trend}"
                )
            elif diff < -0.15:  # Significant decrease
                # Should be FALLING or STABLE (depending on slope)
                assert trend in [TrendDirection.FALLING, TrendDirection.STABLE], (
                    f"Significant decrease (diff={diff:.3f}) should result in FALLING or STABLE, got {trend}"
                )


# ============================================================================
# Additional Unit Tests for Edge Cases
# ============================================================================

def test_empty_texts(engine_with_mock):
    """Test sentiment analysis with empty text list."""
    engine = engine_with_mock
    result = engine.analyze_sentiment([], source="test")
    
    assert result.sentiment_score == 0.0
    assert result.confidence == 0.0
    assert result.sample_size == 0


def test_empty_sentiment_results(engine_with_mock):
    """Test aggregation with empty sentiment results."""
    engine = engine_with_mock
    overall = engine.aggregate_sentiment([])
    
    assert overall.overall_score == 0.0
    assert overall.classification == SentimentClassification.NEUTRAL
    assert overall.trend == TrendDirection.STABLE
    assert len(overall.sources) == 0


def test_single_sentiment_result(engine_with_mock):
    """Test aggregation with single sentiment result."""
    engine = engine_with_mock
    
    result = SentimentResults(
        source="twitter",
        sentiment_score=0.5,
        confidence=0.8,
        sample_size=100,
        timestamp=datetime.utcnow()
    )
    
    overall = engine.aggregate_sentiment([result])
    
    assert overall.overall_score == 0.5
    assert overall.classification == SentimentClassification.POSITIVE
    assert len(overall.sources) == 1


def test_trend_detection_insufficient_data(engine_with_mock):
    """Test trend detection with insufficient data."""
    engine = engine_with_mock
    
    # Single data point
    result = SentimentResults(
        source="twitter",
        sentiment_score=0.5,
        confidence=0.8,
        sample_size=100,
        timestamp=datetime.utcnow()
    )
    
    trend = engine.detect_sentiment_trend([result])
    assert trend == TrendDirection.STABLE


def test_trend_detection_rising(engine_with_mock):
    """Test trend detection with clear rising trend."""
    engine = engine_with_mock
    
    # Create rising trend data
    results = []
    base_time = datetime.utcnow() - timedelta(hours=10)
    
    for i in range(10):
        score = -0.5 + (i * 0.15)  # Rising from -0.5 to 0.85
        result = SentimentResults(
            source="twitter",
            sentiment_score=score,
            confidence=0.8,
            sample_size=100,
            timestamp=base_time + timedelta(hours=i)
        )
        results.append(result)
    
    trend = engine.detect_sentiment_trend(results)
    assert trend == TrendDirection.RISING


def test_trend_detection_falling(engine_with_mock):
    """Test trend detection with clear falling trend."""
    engine = engine_with_mock
    
    # Create falling trend data
    results = []
    base_time = datetime.utcnow() - timedelta(hours=10)
    
    for i in range(10):
        score = 0.5 - (i * 0.15)  # Falling from 0.5 to -0.85
        result = SentimentResults(
            source="twitter",
            sentiment_score=score,
            confidence=0.8,
            sample_size=100,
            timestamp=base_time + timedelta(hours=i)
        )
        results.append(result)
    
    trend = engine.detect_sentiment_trend(results)
    assert trend == TrendDirection.FALLING


def test_fundamental_score_generation(engine_with_mock):
    """Test fundamental score generation from overall sentiment."""
    engine = engine_with_mock
    
    # Test positive sentiment with rising trend
    overall = OverallSentiment(
        overall_score=0.6,
        classification=SentimentClassification.POSITIVE,
        trend=TrendDirection.RISING,
        sources=[]
    )
    
    score = engine.generate_fundamental_score(overall)
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # Positive sentiment should give score > 0.5
    
    # Test negative sentiment with falling trend
    overall = OverallSentiment(
        overall_score=-0.6,
        classification=SentimentClassification.NEGATIVE,
        trend=TrendDirection.FALLING,
        sources=[]
    )
    
    score = engine.generate_fundamental_score(overall)
    assert 0.0 <= score <= 1.0
    assert score < 0.5  # Negative sentiment should give score < 0.5


def test_text_preprocessing(engine_with_mock):
    """Test text preprocessing functionality."""
    engine = engine_with_mock
    
    # Test URL removal
    text = "Check out this article https://example.com/article Bitcoin is great!"
    clean = engine._preprocess_text(text)
    assert "https://" not in clean
    assert "bitcoin" in clean.lower()
    
    # Test mention removal
    text = "@user1 @user2 Bitcoin is going up!"
    clean = engine._preprocess_text(text)
    assert "@user" not in clean
    assert "bitcoin" in clean.lower()
    
    # Test hashtag processing
    text = "#Bitcoin #crypto are trending"
    clean = engine._preprocess_text(text)
    assert "bitcoin" in clean.lower()
    assert "crypto" in clean.lower()


def test_complete_fundamental_analysis(engine_with_mock):
    """Test complete fundamental analysis pipeline."""
    engine = engine_with_mock
    
    # Prepare test data
    social_media_data = {
        'twitter': [
            {'text': 'Bitcoin is going to the moon! Great investment.'},
            {'text': 'Ethereum looks very bullish today.'}
        ],
        'reddit': [
            {'text': 'Amazing gains in crypto market today!'}
        ]
    }
    
    news_data = [
        {
            'title': 'Bitcoin Reaches New High',
            'description': 'Bitcoin price surges to new all-time high amid strong demand.'
        }
    ]
    
    # Run analysis
    overall = engine.analyze_fundamental_data(
        social_media_data=social_media_data,
        news_data=news_data
    )
    
    # Verify results
    assert -1.0 <= overall.overall_score <= 1.0
    assert overall.classification in [
        SentimentClassification.POSITIVE,
        SentimentClassification.NEUTRAL,
        SentimentClassification.NEGATIVE
    ]
    assert len(overall.sources) > 0
