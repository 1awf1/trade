"""
Signal Generator Engine for producing buy/sell signals with success probability.
Implements success probability calculation, signal generation, and explanation.
"""
from typing import Optional, List, Dict
from datetime import datetime
from utils.logger import logger
from models.schemas import (
    IndicatorResults, OverallSentiment, Signal, SignalExplanation,
    SignalType, SentimentClassification, TrendDirection
)


class SignalGenerator:
    """
    Signal Generator for cryptocurrency trading signals.
    Combines technical and fundamental analysis to produce actionable signals.
    """
    
    def __init__(self):
        """Initialize signal generator with default weights."""
        # Weights for success probability calculation
        self.technical_weight = 0.6
        self.fundamental_weight = 0.3
        self.confluence_weight = 0.1
        
        # Conflict penalty multiplier
        self.conflict_penalty = 0.8
        
        # Signal thresholds
        self.strong_signal_threshold = 0.80  # >= 80%
        self.normal_signal_threshold = 0.60  # >= 60%
        self.neutral_threshold = 0.40  # >= 40%
        # Below 40% is UNCERTAIN
        
        logger.info("Signal Generator initialized")
    
    def generate_technical_score(self, indicators: IndicatorResults) -> float:
        """
        Generate normalized technical analysis score (0-1) from indicators.
        
        Args:
            indicators: Technical indicator results
        
        Returns:
            Technical score between 0 and 1
        """
        # Count bullish and bearish signals
        bullish_count = 0
        bearish_count = 0
        total_count = 0
        
        # RSI
        if indicators.rsi_signal == "oversold":
            bullish_count += 1
        elif indicators.rsi_signal == "overbought":
            bearish_count += 1
        total_count += 1
        
        # MACD
        if indicators.macd_signal == "bullish":
            bullish_count += 1
        elif indicators.macd_signal == "bearish":
            bearish_count += 1
        total_count += 1
        
        # Bollinger Bands
        if indicators.bollinger_signal == "oversold":
            bullish_count += 1
        elif indicators.bollinger_signal == "overbought":
            bearish_count += 1
        total_count += 1
        
        # Moving Averages
        if indicators.ma_signal == "bullish":
            bullish_count += 1
        elif indicators.ma_signal == "bearish":
            bearish_count += 1
        total_count += 1
        
        # Stochastic
        if indicators.stochastic_signal == "oversold":
            bullish_count += 1
        elif indicators.stochastic_signal == "overbought":
            bearish_count += 1
        total_count += 1
        
        # VWAP
        if indicators.vwap_signal == "above":
            bullish_count += 1
        elif indicators.vwap_signal == "below":
            bearish_count += 1
        total_count += 1
        
        # OBV
        if indicators.obv_signal == "volume_supported":
            # Check if trend is bullish or bearish
            if indicators.ma_signal == "bullish":
                bullish_count += 1
            elif indicators.ma_signal == "bearish":
                bearish_count += 1
        total_count += 1
        
        # Calculate base score (0 = all bearish, 0.5 = neutral, 1 = all bullish)
        if total_count > 0:
            net_signals = bullish_count - bearish_count
            technical_score = 0.5 + (net_signals / (2 * total_count))
        else:
            technical_score = 0.5
        
        # Clamp to [0, 1]
        technical_score = max(0.0, min(1.0, technical_score))
        
        logger.info(
            f"Technical score: {technical_score:.3f} "
            f"(Bullish: {bullish_count}, Bearish: {bearish_count}, Total: {total_count})"
        )
        
        return technical_score
    
    def calculate_success_probability(
        self,
        technical_score: float,
        fundamental_score: float,
        confluence: float
    ) -> float:
        """
        Calculate success probability from technical, fundamental, and confluence scores.
        
        Args:
            technical_score: Technical analysis score (0-1)
            fundamental_score: Fundamental analysis score (0-1)
            confluence: Confluence score (0-1)
        
        Returns:
            Success probability (0-1)
        
        Validates: Gereksinim 7.1, 7.2, 7.3 - Başarı ihtimali hesaplama
        """
        # Validate inputs
        technical_score = max(0.0, min(1.0, technical_score))
        fundamental_score = max(0.0, min(1.0, fundamental_score))
        confluence = max(0.0, min(1.0, confluence))
        
        # Calculate weighted success probability
        success_probability = (
            technical_score * self.technical_weight +
            fundamental_score * self.fundamental_weight +
            confluence * self.confluence_weight
        )
        
        # Ensure result is in [0, 1]
        success_probability = max(0.0, min(1.0, success_probability))
        
        logger.info(
            f"Base success probability: {success_probability:.3f} "
            f"(Tech: {technical_score:.3f}, Fund: {fundamental_score:.3f}, Conf: {confluence:.3f})"
        )
        
        return success_probability
    
    def apply_conflict_penalty(
        self,
        success_probability: float,
        technical_score: float,
        fundamental_score: float
    ) -> float:
        """
        Apply conflict penalty when technical and fundamental signals disagree.
        
        Args:
            success_probability: Base success probability
            technical_score: Technical analysis score (0-1)
            fundamental_score: Fundamental analysis score (0-1)
        
        Returns:
            Adjusted success probability
        
        Validates: Gereksinim 7.4, 7.5 - Çelişki cezası
        """
        # Determine signal directions
        # > 0.5 = bullish, < 0.5 = bearish, = 0.5 = neutral
        technical_direction = "bullish" if technical_score > 0.55 else ("bearish" if technical_score < 0.45 else "neutral")
        fundamental_direction = "bullish" if fundamental_score > 0.55 else ("bearish" if fundamental_score < 0.45 else "neutral")
        
        # Check for conflict
        if technical_direction != "neutral" and fundamental_direction != "neutral":
            if technical_direction != fundamental_direction:
                # Conflict detected - apply penalty
                adjusted_probability = success_probability * self.conflict_penalty
                logger.info(
                    f"Conflict detected: Technical={technical_direction}, Fundamental={fundamental_direction}. "
                    f"Applying {self.conflict_penalty}x penalty: {success_probability:.3f} -> {adjusted_probability:.3f}"
                )
                return adjusted_probability
        
        # No conflict or one is neutral
        logger.info("No conflict between technical and fundamental signals")
        return success_probability
    
    def apply_harmony_bonus(
        self,
        success_probability: float,
        technical_score: float,
        fundamental_score: float
    ) -> float:
        """
        Apply harmony bonus when technical and fundamental signals agree strongly.
        
        Args:
            success_probability: Base success probability
            technical_score: Technical analysis score (0-1)
            fundamental_score: Fundamental analysis score (0-1)
        
        Returns:
            Adjusted success probability
        
        Validates: Gereksinim 7.5 - Uyum bonusu
        """
        # Determine signal directions and strengths
        technical_direction = "bullish" if technical_score > 0.55 else ("bearish" if technical_score < 0.45 else "neutral")
        fundamental_direction = "bullish" if fundamental_score > 0.55 else ("bearish" if fundamental_score < 0.45 else "neutral")
        
        # Check for strong agreement
        if technical_direction == fundamental_direction and technical_direction != "neutral":
            # Calculate strength of agreement
            if technical_direction == "bullish":
                # Both bullish - check how bullish
                avg_score = (technical_score + fundamental_score) / 2
                if avg_score > 0.7:  # Strong bullish agreement
                    bonus_multiplier = 1.1  # 10% bonus
                    adjusted_probability = min(1.0, success_probability * bonus_multiplier)
                    logger.info(
                        f"Strong bullish harmony detected (avg={avg_score:.3f}). "
                        f"Applying {bonus_multiplier}x bonus: {success_probability:.3f} -> {adjusted_probability:.3f}"
                    )
                    return adjusted_probability
            else:  # bearish
                # Both bearish - check how bearish
                avg_score = (technical_score + fundamental_score) / 2
                if avg_score < 0.3:  # Strong bearish agreement
                    bonus_multiplier = 1.1  # 10% bonus
                    adjusted_probability = min(1.0, success_probability * bonus_multiplier)
                    logger.info(
                        f"Strong bearish harmony detected (avg={avg_score:.3f}). "
                        f"Applying {bonus_multiplier}x bonus: {success_probability:.3f} -> {adjusted_probability:.3f}"
                    )
                    return adjusted_probability
        
        # No strong harmony
        return success_probability


    def apply_ema_200_trend_filter(
        self,
        success_probability: float,
        indicators: IndicatorResults,
        signal_direction: str
    ) -> float:
        """
        Apply EMA 200 trend filter to weaken signals against the trend.
        
        Args:
            success_probability: Current success probability
            indicators: Technical indicator results
            signal_direction: "LONG" or "SHORT"
        
        Returns:
            Adjusted success probability
        
        Validates: Gereksinim 4.11, 4.12 - EMA 200 Trend Filtresi
        """
        ema_filter = indicators.ema_200_trend_filter
        
        # If filter is neutral, no adjustment needed
        if ema_filter == "neutral":
            logger.info("EMA 200 filter is neutral, no adjustment")
            return success_probability
        
        # Check for signal against the trend
        if ema_filter == "long_only" and signal_direction == "SHORT":
            # Price above EMA 200 but signal is SHORT - weaken signal
            adjusted_probability = success_probability * 0.5
            logger.info(
                f"EMA 200 filter: Price above EMA 200 but SHORT signal. "
                f"Weakening: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        elif ema_filter == "short_only" and signal_direction == "LONG":
            # Price below EMA 200 but signal is LONG - weaken signal
            adjusted_probability = success_probability * 0.5
            logger.info(
                f"EMA 200 filter: Price below EMA 200 but LONG signal. "
                f"Weakening: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        # Signal is with the trend - no penalty
        logger.info(f"EMA 200 filter: Signal aligns with trend ({ema_filter})")
        return success_probability
    
    def apply_golden_death_cross_bonus(
        self,
        success_probability: float,
        indicators: IndicatorResults,
        signal_direction: str
    ) -> float:
        """
        Apply bonus for Golden Cross or Death Cross alignment with signal.
        
        Args:
            success_probability: Current success probability
            indicators: Technical indicator results
            signal_direction: "LONG" or "SHORT"
        
        Returns:
            Adjusted success probability
        
        Validates: Gereksinim 4.9 - Golden Cross / Death Cross bonusu
        """
        cross_type = indicators.golden_death_cross
        
        if cross_type is None:
            logger.info("No Golden/Death Cross detected")
            return success_probability
        
        # Apply bonus if cross aligns with signal direction
        if cross_type == "golden_cross" and signal_direction == "LONG":
            # Golden Cross + Long signal = bullish confirmation
            bonus_multiplier = 1.15  # 15% bonus
            adjusted_probability = min(1.0, success_probability * bonus_multiplier)
            logger.info(
                f"Golden Cross detected with LONG signal. "
                f"Applying {bonus_multiplier}x bonus: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        elif cross_type == "death_cross" and signal_direction == "SHORT":
            # Death Cross + Short signal = bearish confirmation
            bonus_multiplier = 1.15  # 15% bonus
            adjusted_probability = min(1.0, success_probability * bonus_multiplier)
            logger.info(
                f"Death Cross detected with SHORT signal. "
                f"Applying {bonus_multiplier}x bonus: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        # Cross doesn't align with signal
        logger.info(f"{cross_type} detected but doesn't align with {signal_direction} signal")
        return success_probability
    
    def apply_rsi_divergence_bonus(
        self,
        success_probability: float,
        indicators: IndicatorResults,
        signal_direction: str
    ) -> float:
        """
        Apply bonus for RSI divergence alignment with signal.
        
        Args:
            success_probability: Current success probability
            indicators: Technical indicator results
            signal_direction: "LONG" or "SHORT"
        
        Returns:
            Adjusted success probability
        
        Validates: Gereksinim 4.10 - RSI Divergence bonusu
        """
        divergence = indicators.rsi_divergence
        
        if divergence is None:
            logger.info("No RSI divergence detected")
            return success_probability
        
        # Apply bonus if divergence aligns with signal direction
        if divergence == "positive" and signal_direction == "LONG":
            # Positive divergence + Long signal = bullish confirmation
            bonus_multiplier = 1.10  # 10% bonus
            adjusted_probability = min(1.0, success_probability * bonus_multiplier)
            logger.info(
                f"Positive RSI divergence detected with LONG signal. "
                f"Applying {bonus_multiplier}x bonus: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        elif divergence == "negative" and signal_direction == "SHORT":
            # Negative divergence + Short signal = bearish confirmation
            bonus_multiplier = 1.10  # 10% bonus
            adjusted_probability = min(1.0, success_probability * bonus_multiplier)
            logger.info(
                f"Negative RSI divergence detected with SHORT signal. "
                f"Applying {bonus_multiplier}x bonus: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        # Divergence doesn't align with signal
        logger.info(f"{divergence} RSI divergence detected but doesn't align with {signal_direction} signal")
        return success_probability
    
    def apply_atr_volatility_adjustment(
        self,
        success_probability: float,
        indicators: IndicatorResults
    ) -> float:
        """
        Apply volatility adjustment based on ATR percentile.
        High volatility reduces success probability slightly.
        
        Args:
            success_probability: Current success probability
            indicators: Technical indicator results
        
        Returns:
            Adjusted success probability
        
        Validates: Gereksinim 4.5 - ATR bazlı volatilite ayarlaması
        """
        atr_percentile = indicators.atr.percentile
        
        # High volatility (above 80th percentile) = higher risk
        if atr_percentile > 0.8:
            adjustment_multiplier = 0.95  # 5% penalty for high volatility
            adjusted_probability = success_probability * adjustment_multiplier
            logger.info(
                f"High volatility detected (ATR percentile: {atr_percentile:.2f}). "
                f"Applying {adjustment_multiplier}x adjustment: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        # Low volatility (below 20th percentile) = slightly more reliable
        elif atr_percentile < 0.2:
            adjustment_multiplier = 1.02  # 2% bonus for low volatility
            adjusted_probability = min(1.0, success_probability * adjustment_multiplier)
            logger.info(
                f"Low volatility detected (ATR percentile: {atr_percentile:.2f}). "
                f"Applying {adjustment_multiplier}x adjustment: {success_probability:.3f} -> {adjusted_probability:.3f}"
            )
            return adjusted_probability
        
        # Normal volatility - no adjustment
        logger.info(f"Normal volatility (ATR percentile: {atr_percentile:.2f}), no adjustment")
        return success_probability

    def determine_signal_direction(
        self,
        technical_score: float,
        fundamental_score: float
    ) -> str:
        """
        Determine signal direction (LONG or SHORT) based on scores.
        
        Args:
            technical_score: Technical analysis score (0-1)
            fundamental_score: Fundamental analysis score (0-1)
        
        Returns:
            "LONG" or "SHORT"
        """
        # Average the scores
        avg_score = (technical_score + fundamental_score) / 2
        
        # > 0.5 = bullish (LONG), < 0.5 = bearish (SHORT)
        if avg_score >= 0.5:
            return "LONG"
        else:
            return "SHORT"
    
    def generate_signal(
        self,
        success_probability: float,
        signal_direction: str,
        coin: str,
        timeframe: str,
        indicators: IndicatorResults
    ) -> Signal:
        """
        Generate trading signal based on success probability and direction.
        
        Args:
            success_probability: Success probability (0-1)
            signal_direction: "LONG" or "SHORT"
            coin: Coin symbol
            timeframe: Timeframe
            indicators: Technical indicator results
        
        Returns:
            Signal object
        
        Validates: Gereksinim 8.1, 8.2, 8.3, 8.4 - Sinyal eşikleri
        Validates: Gereksinim 4.5 - ATR bazlı Stop-Loss ve Take-Profit
        """
        # Convert to percentage (0-100)
        success_percent = success_probability * 100
        
        # Determine signal type based on thresholds
        if success_percent >= self.strong_signal_threshold * 100:
            # Strong signal (>= 80%)
            if signal_direction == "LONG":
                signal_type = SignalType.STRONG_BUY
            else:
                signal_type = SignalType.STRONG_SELL
        
        elif success_percent >= self.normal_signal_threshold * 100:
            # Normal signal (60-79%)
            if signal_direction == "LONG":
                signal_type = SignalType.BUY
            else:
                signal_type = SignalType.SELL
        
        elif success_percent >= self.neutral_threshold * 100:
            # Neutral (40-59%)
            signal_type = SignalType.NEUTRAL
        
        else:
            # Uncertain (< 40%)
            signal_type = SignalType.UNCERTAIN
        
        # Add ATR-based Stop-Loss and Take-Profit
        # These are already calculated in the indicators
        stop_loss = indicators.atr_stop_loss
        take_profit = indicators.atr_take_profit
        
        # For SHORT signals, invert the stop-loss and take-profit
        # (stop-loss should be above current price, take-profit below)
        if signal_direction == "SHORT":
            # Get current price from indicators (approximate from ATR calculations)
            # stop_loss was calculated as: current_price - (2 * ATR)
            # So current_price ≈ stop_loss + (2 * ATR)
            atr = indicators.atr.atr
            estimated_current_price = stop_loss + (2 * atr)
            
            # For short: stop-loss above, take-profit below
            stop_loss = estimated_current_price + (2 * atr)
            take_profit = estimated_current_price - (3 * atr)
        
        # Create signal
        signal = Signal(
            signal_type=signal_type,
            success_probability=success_percent,
            timestamp=datetime.utcnow(),
            coin=coin,
            timeframe=timeframe,
            stop_loss=stop_loss,
            take_profit=take_profit,
            ema_200_filter_applied=indicators.ema_200_trend_filter != "neutral",
            golden_death_cross_detected=indicators.golden_death_cross,
            rsi_divergence_detected=indicators.rsi_divergence
        )
        
        logger.info(
            f"Signal generated: {signal_type.value} for {coin} ({timeframe}) "
            f"with {success_percent:.1f}% success probability. "
            f"Stop-Loss: {stop_loss:.2f}, Take-Profit: {take_profit:.2f}"
        )
        
        return signal

    def explain_signal(
        self,
        signal: Signal,
        indicators: IndicatorResults,
        fundamental: OverallSentiment,
        technical_score: float,
        fundamental_score: float
    ) -> SignalExplanation:
        """
        Generate detailed explanation for the signal.
        
        Args:
            signal: Generated signal
            indicators: Technical indicator results
            fundamental: Fundamental analysis results
            technical_score: Technical analysis score
            fundamental_score: Fundamental analysis score
        
        Returns:
            SignalExplanation with detailed reasoning
        
        Validates: Gereksinim 8.5 - Sinyal açıklama
        Validates: Gereksinim 4.9, 4.10 - Golden Cross, Death Cross, RSI Divergence bilgileri
        """
        technical_reasons = []
        fundamental_reasons = []
        supporting_indicators = []
        conflicting_indicators = []
        risk_factors = []
        
        # Determine signal direction
        is_bullish = signal.signal_type in [SignalType.STRONG_BUY, SignalType.BUY]
        is_bearish = signal.signal_type in [SignalType.STRONG_SELL, SignalType.SELL]
        
        # ===== Technical Reasons =====
        
        # RSI
        if indicators.rsi_signal == "oversold":
            if is_bullish:
                supporting_indicators.append("RSI")
                technical_reasons.append(f"RSI ({indicators.rsi:.1f}) aşırı satım bölgesinde (oversold)")
            else:
                conflicting_indicators.append("RSI")
        elif indicators.rsi_signal == "overbought":
            if is_bearish:
                supporting_indicators.append("RSI")
                technical_reasons.append(f"RSI ({indicators.rsi:.1f}) aşırı alım bölgesinde (overbought)")
            else:
                conflicting_indicators.append("RSI")
        
        # RSI Divergence
        if indicators.rsi_divergence == "positive":
            if is_bullish:
                supporting_indicators.append("RSI Divergence")
                technical_reasons.append("Pozitif RSI divergence tespit edildi (yükseliş sinyali)")
            else:
                conflicting_indicators.append("RSI Divergence")
        elif indicators.rsi_divergence == "negative":
            if is_bearish:
                supporting_indicators.append("RSI Divergence")
                technical_reasons.append("Negatif RSI divergence tespit edildi (düşüş sinyali)")
            else:
                conflicting_indicators.append("RSI Divergence")
        
        # MACD
        if indicators.macd_signal == "bullish":
            if is_bullish:
                supporting_indicators.append("MACD")
                technical_reasons.append("MACD yükseliş sinyali veriyor")
            else:
                conflicting_indicators.append("MACD")
        elif indicators.macd_signal == "bearish":
            if is_bearish:
                supporting_indicators.append("MACD")
                technical_reasons.append("MACD düşüş sinyali veriyor")
            else:
                conflicting_indicators.append("MACD")
        
        # Bollinger Bands
        if indicators.bollinger_signal == "oversold":
            if is_bullish:
                supporting_indicators.append("Bollinger Bands")
                technical_reasons.append("Fiyat Bollinger alt bandına yakın (aşırı satım)")
            else:
                conflicting_indicators.append("Bollinger Bands")
        elif indicators.bollinger_signal == "overbought":
            if is_bearish:
                supporting_indicators.append("Bollinger Bands")
                technical_reasons.append("Fiyat Bollinger üst bandına yakın (aşırı alım)")
            else:
                conflicting_indicators.append("Bollinger Bands")
        
        # Moving Averages
        if indicators.ma_signal == "bullish":
            if is_bullish:
                supporting_indicators.append("Moving Averages")
                technical_reasons.append("Hareketli ortalamalar yükseliş trendi gösteriyor")
            else:
                conflicting_indicators.append("Moving Averages")
        elif indicators.ma_signal == "bearish":
            if is_bearish:
                supporting_indicators.append("Moving Averages")
                technical_reasons.append("Hareketli ortalamalar düşüş trendi gösteriyor")
            else:
                conflicting_indicators.append("Moving Averages")
        
        # Golden Cross / Death Cross
        if indicators.golden_death_cross == "golden_cross":
            if is_bullish:
                supporting_indicators.append("Golden Cross")
                technical_reasons.append("Golden Cross tespit edildi: EMA 50, EMA 200'ü yukarı kesti (güçlü yükseliş sinyali)")
            else:
                conflicting_indicators.append("Golden Cross")
        elif indicators.golden_death_cross == "death_cross":
            if is_bearish:
                supporting_indicators.append("Death Cross")
                technical_reasons.append("Death Cross tespit edildi: EMA 50, EMA 200'ü aşağı kesti (güçlü düşüş sinyali)")
            else:
                conflicting_indicators.append("Death Cross")
        
        # Stochastic
        if indicators.stochastic_signal == "oversold":
            if is_bullish:
                supporting_indicators.append("Stochastic")
                technical_reasons.append(f"Stochastic aşırı satım bölgesinde (K={indicators.stochastic.k:.1f})")
            else:
                conflicting_indicators.append("Stochastic")
        elif indicators.stochastic_signal == "overbought":
            if is_bearish:
                supporting_indicators.append("Stochastic")
                technical_reasons.append(f"Stochastic aşırı alım bölgesinde (K={indicators.stochastic.k:.1f})")
            else:
                conflicting_indicators.append("Stochastic")
        
        # VWAP
        if indicators.vwap_signal == "above":
            if is_bullish:
                supporting_indicators.append("VWAP")
                technical_reasons.append("Fiyat VWAP'ın üzerinde (kısa vadeli yükseliş trendi)")
            else:
                conflicting_indicators.append("VWAP")
        elif indicators.vwap_signal == "below":
            if is_bearish:
                supporting_indicators.append("VWAP")
                technical_reasons.append("Fiyat VWAP'ın altında (kısa vadeli düşüş trendi)")
            else:
                conflicting_indicators.append("VWAP")
        
        # OBV
        if indicators.obv_signal == "volume_supported":
            supporting_indicators.append("OBV")
            technical_reasons.append("Fiyat hareketi hacim ile destekleniyor (OBV)")
        elif indicators.obv_signal == "volume_divergence":
            risk_factors.append("OBV hacim divergence gösteriyor (uyarı sinyali)")
        
        # EMA 200 Trend Filter
        if indicators.ema_200_trend_filter == "long_only":
            if is_bullish:
                technical_reasons.append("Fiyat EMA 200'ün üzerinde (uzun vadeli yükseliş trendi)")
            else:
                risk_factors.append("Fiyat EMA 200'ün üzerinde ancak sinyal düşüş yönünde")
        elif indicators.ema_200_trend_filter == "short_only":
            if is_bearish:
                technical_reasons.append("Fiyat EMA 200'ün altında (uzun vadeli düşüş trendi)")
            else:
                risk_factors.append("Fiyat EMA 200'ün altında ancak sinyal yükseliş yönünde")
        
        # Confluence Score
        if indicators.confluence_score > 0.7:
            technical_reasons.append(f"Yüksek indikatör uyumu (confluence: {indicators.confluence_score:.2f})")
        elif indicators.confluence_score < 0.3:
            risk_factors.append(f"Düşük indikatör uyumu (confluence: {indicators.confluence_score:.2f})")
        
        # ===== Fundamental Reasons =====
        
        # Sentiment
        if fundamental.classification == SentimentClassification.POSITIVE:
            if is_bullish:
                fundamental_reasons.append(f"Piyasa duygusu pozitif (skor: {fundamental.overall_score:.2f})")
            else:
                fundamental_reasons.append(f"Piyasa duygusu pozitif ancak sinyal düşüş yönünde (skor: {fundamental.overall_score:.2f})")
        elif fundamental.classification == SentimentClassification.NEGATIVE:
            if is_bearish:
                fundamental_reasons.append(f"Piyasa duygusu negatif (skor: {fundamental.overall_score:.2f})")
            else:
                fundamental_reasons.append(f"Piyasa duygusu negatif ancak sinyal yükseliş yönünde (skor: {fundamental.overall_score:.2f})")
        else:
            fundamental_reasons.append(f"Piyasa duygusu nötr (skor: {fundamental.overall_score:.2f})")
        
        # Sentiment Trend
        if fundamental.trend == TrendDirection.RISING:
            fundamental_reasons.append("Duygu trendi yükseliyor")
        elif fundamental.trend == TrendDirection.FALLING:
            fundamental_reasons.append("Duygu trendi düşüyor")
        else:
            fundamental_reasons.append("Duygu trendi sabit")
        
        # ===== Risk Factors =====
        
        # ATR Volatility
        atr_percentile = indicators.atr.percentile
        if atr_percentile > 0.8:
            risk_factors.append(
                f"Yüksek volatilite (ATR: {indicators.atr.atr:.2f}, "
                f"{indicators.atr.atr_percent:.2f}% of price)"
            )
        elif atr_percentile < 0.2:
            risk_factors.append(
                f"Düşük volatilite (ATR: {indicators.atr.atr:.2f}, "
                f"{indicators.atr.atr_percent:.2f}% of price)"
            )
        
        # Stop-Loss and Take-Profit
        risk_factors.append(
            f"Önerilen Stop-Loss: {signal.stop_loss:.2f}, "
            f"Take-Profit: {signal.take_profit:.2f} (ATR bazlı)"
        )
        
        # Support/Resistance Levels
        if indicators.support_levels:
            risk_factors.append(
                f"Destek seviyeleri: {', '.join([f'{s:.2f}' for s in indicators.support_levels[:3]])}"
            )
        if indicators.resistance_levels:
            risk_factors.append(
                f"Direnç seviyeleri: {', '.join([f'{r:.2f}' for r in indicators.resistance_levels[:3]])}"
            )
        
        # Create explanation
        explanation = SignalExplanation(
            signal=signal,
            technical_reasons=technical_reasons,
            fundamental_reasons=fundamental_reasons,
            supporting_indicators=supporting_indicators,
            conflicting_indicators=conflicting_indicators,
            risk_factors=risk_factors
        )
        
        logger.info(
            f"Signal explanation generated: "
            f"{len(supporting_indicators)} supporting, "
            f"{len(conflicting_indicators)} conflicting indicators"
        )
        
        return explanation

    def generate_complete_signal(
        self,
        coin: str,
        timeframe: str,
        indicators: IndicatorResults,
        fundamental: OverallSentiment
    ) -> tuple[Signal, SignalExplanation]:
        """
        Complete signal generation pipeline.
        Combines all analysis and generates signal with explanation.
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe
            indicators: Technical indicator results
            fundamental: Fundamental analysis results
        
        Returns:
            Tuple of (Signal, SignalExplanation)
        """
        logger.info(f"Starting complete signal generation for {coin} ({timeframe})")
        
        # Step 1: Generate technical score
        technical_score = self.generate_technical_score(indicators)
        
        # Step 2: Generate fundamental score
        from engines.fundamental_analysis import FundamentalAnalysisEngine
        fundamental_engine = FundamentalAnalysisEngine()
        fundamental_score = fundamental_engine.generate_fundamental_score(fundamental)
        
        # Step 3: Calculate base success probability
        success_probability = self.calculate_success_probability(
            technical_score,
            fundamental_score,
            indicators.confluence_score
        )
        
        # Step 4: Apply conflict penalty
        success_probability = self.apply_conflict_penalty(
            success_probability,
            technical_score,
            fundamental_score
        )
        
        # Step 5: Apply harmony bonus
        success_probability = self.apply_harmony_bonus(
            success_probability,
            technical_score,
            fundamental_score
        )
        
        # Step 6: Determine signal direction
        signal_direction = self.determine_signal_direction(
            technical_score,
            fundamental_score
        )
        
        # Step 7: Apply EMA 200 trend filter
        success_probability = self.apply_ema_200_trend_filter(
            success_probability,
            indicators,
            signal_direction
        )
        
        # Step 8: Apply Golden/Death Cross bonus
        success_probability = self.apply_golden_death_cross_bonus(
            success_probability,
            indicators,
            signal_direction
        )
        
        # Step 9: Apply RSI Divergence bonus
        success_probability = self.apply_rsi_divergence_bonus(
            success_probability,
            indicators,
            signal_direction
        )
        
        # Step 10: Apply ATR volatility adjustment
        success_probability = self.apply_atr_volatility_adjustment(
            success_probability,
            indicators
        )
        
        # Step 11: Generate signal
        signal = self.generate_signal(
            success_probability,
            signal_direction,
            coin,
            timeframe,
            indicators
        )
        
        # Step 12: Generate explanation
        explanation = self.explain_signal(
            signal,
            indicators,
            fundamental,
            technical_score,
            fundamental_score
        )
        
        logger.info(
            f"Complete signal generation finished: {signal.signal_type.value} "
            f"with {signal.success_probability:.1f}% success probability"
        )
        
        return signal, explanation
