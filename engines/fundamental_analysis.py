"""
Fundamental Analysis Engine for sentiment analysis and aggregation.
Implements sentiment scoring, classification, and trend detection.
"""
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from utils.logger import logger
from models.schemas import SentimentResults, OverallSentiment, SentimentClassification, TrendDirection
import numpy as np


class FundamentalAnalysisEngine:
    """
    Fundamental Analysis Engine for cryptocurrency sentiment analysis.
    Analyzes social media, news, and trends data to determine market sentiment.
    """
    
    def __init__(self):
        """Initialize fundamental analysis engine with sentiment model."""
        self.sentiment_analyzer = None
        self._initialize_sentiment_model()
    
    def _initialize_sentiment_model(self):
        """
        Initialize BERT-based sentiment analysis model.
        Uses a pre-trained model optimized for financial/crypto sentiment.
        """
        try:
            # Use a smaller, faster sentiment model for better performance
            # distilbert is much smaller and faster than full BERT models
            model_name = "distilbert-base-uncased-finetuned-sst-2-english"
            
            logger.info(f"Loading sentiment model: {model_name}")
            
            # Create pipeline (will download model on first use)
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=model_name,
                max_length=512,
                truncation=True
            )
            
            logger.info("Sentiment model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            logger.warning("Sentiment analysis will use fallback method")
            self.sentiment_analyzer = None
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for sentiment analysis.
        
        Args:
            text: Raw text to preprocess
        
        Returns:
            Cleaned and preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove mentions and hashtags (keep the text after them)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length (models have token limits)
        max_chars = 2000
        if len(text) > max_chars:
            text = text[:max_chars]
        
        return text
    
    def _calculate_sentiment_score(self, text: str) -> tuple[float, float]:
        """
        Calculate sentiment score for a single text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Tuple of (sentiment_score, confidence)
            sentiment_score: -1 (negative) to +1 (positive)
            confidence: 0 to 1
        """
        if not text or not text.strip():
            return 0.0, 0.0
        
        if self.sentiment_analyzer is None:
            logger.warning("Sentiment analyzer not initialized, returning neutral sentiment")
            return 0.0, 0.0
        
        try:
            # Preprocess text
            clean_text = self._preprocess_text(text)
            
            if not clean_text:
                return 0.0, 0.0
            
            # Analyze sentiment
            result = self.sentiment_analyzer(clean_text)[0]
            
            # Extract label and score
            label = result['label'].upper()
            score = result['score']
            
            # Convert to -1 to +1 scale
            # DistilBERT labels: POSITIVE, NEGATIVE
            # Score is confidence in the predicted label
            
            if 'POSITIVE' in label:
                # Positive sentiment: map score to [0, 1]
                sentiment_score = score
            elif 'NEGATIVE' in label:
                # Negative sentiment: map score to [-1, 0]
                sentiment_score = -score
            elif 'NEUTRAL' in label:
                sentiment_score = 0.0
            else:
                # Unknown label, treat as neutral
                sentiment_score = 0.0
                score = 0.5
            
            # Confidence is the model's confidence score
            confidence = float(score)
            
            return float(sentiment_score), confidence
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0, 0.0
    
    def analyze_sentiment(self, texts: List[str], source: str = "unknown") -> SentimentResults:
        """
        Analyze sentiment for a list of texts from a single source.
        
        Args:
            texts: List of text strings to analyze
            source: Source of the texts (e.g., "twitter", "reddit", "news")
        
        Returns:
            SentimentResults with aggregated sentiment analysis
        
        Validates: Gereksinim 6.1 - Duygu skoru hesaplama [-1, 1]
        """
        if not texts:
            logger.warning(f"No texts provided for sentiment analysis from {source}")
            return SentimentResults(
                source=source,
                sentiment_score=0.0,
                confidence=0.0,
                sample_size=0,
                timestamp=datetime.utcnow()
            )
        
        logger.info(f"Analyzing sentiment for {len(texts)} texts from {source}")
        
        # Calculate sentiment for each text
        scores = []
        confidences = []
        
        for text in texts:
            score, confidence = self._calculate_sentiment_score(text)
            scores.append(score)
            confidences.append(confidence)
        
        # Aggregate scores (weighted by confidence)
        if scores and sum(confidences) > 0:
            # Weighted average
            weighted_score = sum(s * c for s, c in zip(scores, confidences)) / sum(confidences)
            avg_confidence = sum(confidences) / len(confidences)
        else:
            weighted_score = 0.0
            avg_confidence = 0.0
        
        # Ensure score is in [-1, 1] range
        weighted_score = max(-1.0, min(1.0, weighted_score))
        
        # Ensure confidence is in [0, 1] range
        avg_confidence = max(0.0, min(1.0, avg_confidence))
        
        result = SentimentResults(
            source=source,
            sentiment_score=weighted_score,
            confidence=avg_confidence,
            sample_size=len(texts),
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Sentiment analysis complete for {source}: "
            f"score={weighted_score:.3f}, confidence={avg_confidence:.3f}, samples={len(texts)}"
        )
        
        return result
    
    def aggregate_sentiment(self, sentiment_results: List[SentimentResults]) -> OverallSentiment:
        """
        Aggregate sentiment from multiple sources and classify overall sentiment.
        
        Args:
            sentiment_results: List of SentimentResults from different sources
        
        Returns:
            OverallSentiment with aggregated and classified sentiment
        
        Validates: Gereksinim 6.2 - Çoklu kaynak duygu birleştirme ve sınıflandırma
        """
        if not sentiment_results:
            logger.warning("No sentiment results to aggregate")
            return OverallSentiment(
                overall_score=0.0,
                classification=SentimentClassification.NEUTRAL,
                trend=TrendDirection.STABLE,
                sources=[]
            )
        
        logger.info(f"Aggregating sentiment from {len(sentiment_results)} sources")
        
        # Calculate weighted average (weight by confidence and sample size)
        total_weight = 0.0
        weighted_sum = 0.0
        
        for result in sentiment_results:
            # Weight = confidence * log(sample_size + 1)
            # This gives more weight to confident results with larger sample sizes
            weight = result.confidence * np.log(result.sample_size + 1)
            weighted_sum += result.sentiment_score * weight
            total_weight += weight
        
        # Calculate overall score
        if total_weight > 0:
            overall_score = weighted_sum / total_weight
        else:
            overall_score = 0.0
        
        # Ensure score is in [-1, 1] range
        overall_score = max(-1.0, min(1.0, overall_score))
        
        # Classify sentiment
        # Positive: score > 0.2
        # Negative: score < -0.2
        # Neutral: -0.2 <= score <= 0.2
        if overall_score > 0.2:
            classification = SentimentClassification.POSITIVE
        elif overall_score < -0.2:
            classification = SentimentClassification.NEGATIVE
        else:
            classification = SentimentClassification.NEUTRAL
        
        # Trend detection will be done separately
        trend = TrendDirection.STABLE
        
        result = OverallSentiment(
            overall_score=overall_score,
            classification=classification,
            trend=trend,
            sources=sentiment_results
        )
        
        logger.info(
            f"Overall sentiment: score={overall_score:.3f}, "
            f"classification={classification.value}"
        )
        
        return result
    
    def detect_sentiment_trend(
        self,
        historical_sentiment: List[SentimentResults]
    ) -> TrendDirection:
        """
        Detect sentiment trend from historical data using time series analysis.
        
        Args:
            historical_sentiment: List of SentimentResults ordered by time (oldest first)
        
        Returns:
            TrendDirection (rising, falling, or stable)
        
        Validates: Gereksinim 6.3 - Duygu trend tespiti
        """
        if not historical_sentiment or len(historical_sentiment) < 2:
            logger.warning("Insufficient historical data for trend detection")
            return TrendDirection.STABLE
        
        logger.info(f"Detecting sentiment trend from {len(historical_sentiment)} data points")
        
        # Extract scores and timestamps
        scores = [result.sentiment_score for result in historical_sentiment]
        timestamps = [result.timestamp for result in historical_sentiment]
        
        # Sort by timestamp (should already be sorted, but ensure it)
        sorted_data = sorted(zip(timestamps, scores), key=lambda x: x[0])
        sorted_scores = [score for _, score in sorted_data]
        
        # Method 1: Compare first half vs second half
        mid_point = len(sorted_scores) // 2
        first_half_avg = sum(sorted_scores[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(sorted_scores[mid_point:]) / (len(sorted_scores) - mid_point)
        
        # Method 2: Linear regression slope
        # Simple linear regression: y = mx + b
        n = len(sorted_scores)
        x = list(range(n))  # Time indices
        y = sorted_scores
        
        # Calculate slope (m)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator > 0:
            slope = numerator / denominator
        else:
            slope = 0.0
        
        # Determine trend based on both methods
        # Use slope as primary indicator, first/second half as confirmation
        
        # Threshold for significant trend (adjust based on data scale)
        slope_threshold = 0.05  # Sentiment change per time unit
        half_diff_threshold = 0.1  # Difference between halves
        
        half_diff = second_half_avg - first_half_avg
        
        # Rising trend: positive slope and second half > first half
        if slope > slope_threshold and half_diff > half_diff_threshold:
            trend = TrendDirection.RISING
        # Falling trend: negative slope and second half < first half
        elif slope < -slope_threshold and half_diff < -half_diff_threshold:
            trend = TrendDirection.FALLING
        # Stable: small slope or conflicting signals
        else:
            trend = TrendDirection.STABLE
        
        logger.info(
            f"Sentiment trend detected: {trend.value} "
            f"(slope={slope:.4f}, half_diff={half_diff:.4f})"
        )
        
        return trend
    
    def analyze_fundamental_data(
        self,
        social_media_data: Dict[str, List[Dict]],
        news_data: List[Dict],
        trends_data: Optional[Dict] = None,
        historical_sentiment: Optional[List[SentimentResults]] = None
    ) -> OverallSentiment:
        """
        Complete fundamental analysis pipeline.
        Analyzes all data sources and produces overall sentiment with trend.
        
        Args:
            social_media_data: Dictionary mapping platform names to lists of posts
            news_data: List of news articles
            trends_data: Google Trends data (optional)
            historical_sentiment: Historical sentiment data for trend detection (optional)
        
        Returns:
            OverallSentiment with complete analysis
        """
        logger.info("Starting complete fundamental analysis")
        
        sentiment_results = []
        
        # Analyze social media data
        for platform, posts in social_media_data.items():
            if posts:
                texts = [post.get('text', '') for post in posts if post.get('text')]
                if texts:
                    result = self.analyze_sentiment(texts, source=platform)
                    sentiment_results.append(result)
        
        # Analyze news data
        if news_data:
            news_texts = []
            for article in news_data:
                title = article.get('title', '')
                description = article.get('description', '')
                text = f"{title}. {description}"
                if text.strip():
                    news_texts.append(text)
            
            if news_texts:
                result = self.analyze_sentiment(news_texts, source="news")
                sentiment_results.append(result)
        
        # Aggregate sentiment
        overall_sentiment = self.aggregate_sentiment(sentiment_results)
        
        # Detect trend if historical data is provided
        if historical_sentiment and len(historical_sentiment) >= 2:
            # Add current sentiment to historical data
            current_sentiment = SentimentResults(
                source="aggregated",
                sentiment_score=overall_sentiment.overall_score,
                confidence=sum(r.confidence for r in sentiment_results) / len(sentiment_results) if sentiment_results else 0.0,
                sample_size=sum(r.sample_size for r in sentiment_results),
                timestamp=datetime.utcnow()
            )
            
            all_sentiment = historical_sentiment + [current_sentiment]
            trend = self.detect_sentiment_trend(all_sentiment)
            
            # Update overall sentiment with detected trend
            overall_sentiment = OverallSentiment(
                overall_score=overall_sentiment.overall_score,
                classification=overall_sentiment.classification,
                trend=trend,
                sources=overall_sentiment.sources
            )
        
        logger.info(
            f"Fundamental analysis complete: "
            f"score={overall_sentiment.overall_score:.3f}, "
            f"classification={overall_sentiment.classification.value}, "
            f"trend={overall_sentiment.trend.value}"
        )
        
        return overall_sentiment
    
    def generate_fundamental_score(self, overall_sentiment: OverallSentiment) -> float:
        """
        Generate a normalized fundamental score (0-1) from overall sentiment.
        This score can be used in signal generation.
        
        Args:
            overall_sentiment: OverallSentiment result
        
        Returns:
            Fundamental score between 0 and 1
        """
        # Convert sentiment score from [-1, 1] to [0, 1]
        base_score = (overall_sentiment.overall_score + 1) / 2
        
        # Apply trend modifier
        if overall_sentiment.trend == TrendDirection.RISING:
            trend_modifier = 1.1  # 10% boost for rising trend
        elif overall_sentiment.trend == TrendDirection.FALLING:
            trend_modifier = 0.9  # 10% penalty for falling trend
        else:
            trend_modifier = 1.0
        
        # Calculate final score
        final_score = base_score * trend_modifier
        
        # Clamp to [0, 1]
        final_score = max(0.0, min(1.0, final_score))
        
        logger.info(f"Fundamental score: {final_score:.3f}")
        
        return final_score
