"""
Technical Analysis Engine for calculating indicators and detecting patterns.
Implements RSI, MACD, Bollinger Bands, Moving Averages, ATR, VWAP, OBV, Fibonacci, etc.
"""
import pandas as pd
import numpy as np
import talib
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from utils.logger import logger
from models.schemas import (
    IndicatorResults, MACDValues, BollingerBands, MovingAverages,
    StochasticValues, VolumeProfile, ATRValues, FibonacciLevels, Pattern
)


class TechnicalAnalysisEngine:
    """
    Technical Analysis Engine for cryptocurrency price data.
    Calculates technical indicators and detects chart patterns.
    """
    
    def __init__(self):
        """Initialize technical analysis engine."""
        self.min_data_points = 200  # Minimum candles needed for reliable analysis
    
    def fetch_ohlcv(self, coin: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """
        Fetch and process OHLCV data into DataFrame format.
        This is a wrapper that will be called by the main analysis flow.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            timeframe: Timeframe (e.g., "1h", "4h")
            limit: Number of candles to fetch
        
        Returns:
            DataFrame with OHLCV data
        
        Note:
            This method should be called with data from DataCollector.
            It processes the raw data into a clean DataFrame.
        """
        # This will be integrated with DataCollector in the main flow
        # For now, it's a placeholder that expects processed data
        raise NotImplementedError("Use process_ohlcv_data with data from DataCollector")
    
    def process_ohlcv_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """
        Process raw OHLCV data into clean DataFrame format.
        Performs data cleaning and normalization.
        
        Args:
            raw_data: List of OHLCV candles from DataCollector
        
        Returns:
            Clean DataFrame with OHLCV data
        
        Raises:
            ValueError: If data is invalid or insufficient
        """
        if not raw_data:
            raise ValueError("No OHLCV data provided")
        
        if len(raw_data) < 50:
            raise ValueError(f"Insufficient data points: {len(raw_data)} (minimum 50 required)")
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Ensure required columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert timestamp to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
        
        # Data validation
        # 1. Check for NaN values
        if df[['open', 'high', 'low', 'close']].isnull().any().any():
            logger.warning("Found NaN values in OHLCV data, filling with forward fill")
            df.fillna(method='ffill', inplace=True)
            df.fillna(method='bfill', inplace=True)
        
        # 2. Validate OHLC relationships (high >= low, high >= open/close, low <= open/close)
        invalid_candles = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        
        if invalid_candles.any():
            logger.warning(f"Found {invalid_candles.sum()} invalid candles, correcting...")
            # Correct invalid candles
            df.loc[invalid_candles, 'high'] = df.loc[invalid_candles, [
                'open', 'high', 'low', 'close'
            ]].max(axis=1)
            df.loc[invalid_candles, 'low'] = df.loc[invalid_candles, [
                'open', 'high', 'low', 'close'
            ]].min(axis=1)
        
        # 3. Remove duplicate timestamps
        if df.index.duplicated().any():
            logger.warning(f"Found {df.index.duplicated().sum()} duplicate timestamps, keeping last")
            df = df[~df.index.duplicated(keep='last')]
        
        # 4. Ensure volume is non-negative
        df['volume'] = df['volume'].clip(lower=0)
        
        # 5. Remove outliers (prices that are more than 10x or less than 0.1x the median)
        median_price = df['close'].median()
        outliers = (df['close'] > median_price * 10) | (df['close'] < median_price * 0.1)
        if outliers.any():
            logger.warning(f"Found {outliers.sum()} price outliers, removing...")
            df = df[~outliers]
        
        logger.info(f"Processed {len(df)} OHLCV candles successfully")
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> IndicatorResults:
        """
        Calculate all technical indicators.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            IndicatorResults with all calculated indicators
        
        Raises:
            ValueError: If insufficient data for calculations
        """
        if len(df) < 50:
            raise ValueError(f"Insufficient data for indicator calculation: {len(df)} candles")
        
        logger.info("Calculating technical indicators...")
        
        # Extract price arrays for TA-Lib
        open_prices = df['open'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        close_prices = df['close'].values
        volume = df['volume'].values
        
        # Current price (last close)
        current_price = float(close_prices[-1])
        
        # ===== RSI (Relative Strength Index) =====
        rsi_period = 14
        rsi_values = talib.RSI(close_prices, timeperiod=rsi_period)
        rsi = float(rsi_values[-1])
        
        # RSI signal interpretation
        if rsi < 30:
            rsi_signal = "oversold"
        elif rsi > 70:
            rsi_signal = "overbought"
        else:
            rsi_signal = "neutral"
        
        # ===== RSI Divergence Detection =====
        # Positive divergence: Price makes lower low, but RSI makes higher low (bullish)
        # Negative divergence: Price makes higher high, but RSI makes lower high (bearish)
        
        rsi_divergence = None
        lookback_divergence = min(20, len(close_prices) - 1)
        
        if lookback_divergence >= 10:
            # Get recent price and RSI data
            recent_prices = close_prices[-lookback_divergence:]
            recent_rsi = rsi_values[-lookback_divergence:]
            
            # Find local peaks and troughs
            price_peaks = []
            price_troughs = []
            rsi_peaks = []
            rsi_troughs = []
            
            for i in range(1, len(recent_prices) - 1):
                # Price peaks
                if recent_prices[i] > recent_prices[i-1] and recent_prices[i] > recent_prices[i+1]:
                    price_peaks.append((i, recent_prices[i]))
                # Price troughs
                if recent_prices[i] < recent_prices[i-1] and recent_prices[i] < recent_prices[i+1]:
                    price_troughs.append((i, recent_prices[i]))
                
                # RSI peaks
                if recent_rsi[i] > recent_rsi[i-1] and recent_rsi[i] > recent_rsi[i+1]:
                    rsi_peaks.append((i, recent_rsi[i]))
                # RSI troughs
                if recent_rsi[i] < recent_rsi[i-1] and recent_rsi[i] < recent_rsi[i+1]:
                    rsi_troughs.append((i, recent_rsi[i]))
            
            # Check for positive divergence (bullish)
            if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
                # Get last two troughs
                last_price_trough = price_troughs[-1][1]
                prev_price_trough = price_troughs[-2][1]
                last_rsi_trough = rsi_troughs[-1][1]
                prev_rsi_trough = rsi_troughs[-2][1]
                
                # Price making lower low, RSI making higher low
                if last_price_trough < prev_price_trough and last_rsi_trough > prev_rsi_trough:
                    rsi_divergence = "positive"
                    logger.info("RSI Positive Divergence detected (bullish signal)")
            
            # Check for negative divergence (bearish)
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                # Get last two peaks
                last_price_peak = price_peaks[-1][1]
                prev_price_peak = price_peaks[-2][1]
                last_rsi_peak = rsi_peaks[-1][1]
                prev_rsi_peak = rsi_peaks[-2][1]
                
                # Price making higher high, RSI making lower high
                if last_price_peak > prev_price_peak and last_rsi_peak < prev_rsi_peak:
                    rsi_divergence = "negative"
                    logger.info("RSI Negative Divergence detected (bearish signal)")
        
        logger.info(f"RSI: {rsi:.2f} ({rsi_signal}), Divergence: {rsi_divergence}")
        
        # ===== MACD (Moving Average Convergence Divergence) =====
        macd_line, macd_signal_line, macd_histogram = talib.MACD(
            close_prices,
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )
        
        macd_values = MACDValues(
            macd=float(macd_line[-1]),
            signal=float(macd_signal_line[-1]),
            histogram=float(macd_histogram[-1])
        )
        
        # MACD signal interpretation
        if macd_values.histogram > 0 and macd_values.macd > macd_values.signal:
            macd_signal = "bullish"
        elif macd_values.histogram < 0 and macd_values.macd < macd_values.signal:
            macd_signal = "bearish"
        else:
            macd_signal = "neutral"
        
        logger.info(f"MACD: {macd_values.macd:.2f}, Signal: {macd_values.signal:.2f} ({macd_signal})")
        
        # ===== Bollinger Bands =====
        bb_period = 20
        bb_std = 2
        upper_band, middle_band, lower_band = talib.BBANDS(
            close_prices,
            timeperiod=bb_period,
            nbdevup=bb_std,
            nbdevdn=bb_std,
            matype=0
        )
        
        bollinger = BollingerBands(
            upper=float(upper_band[-1]),
            middle=float(middle_band[-1]),
            lower=float(lower_band[-1]),
            bandwidth=float((upper_band[-1] - lower_band[-1]) / middle_band[-1] * 100)
        )
        
        # Bollinger Bands signal interpretation
        if current_price <= bollinger.lower:
            bollinger_signal = "oversold"
        elif current_price >= bollinger.upper:
            bollinger_signal = "overbought"
        else:
            bollinger_signal = "neutral"
        
        logger.info(f"Bollinger Bands: Upper={bollinger.upper:.2f}, Middle={bollinger.middle:.2f}, Lower={bollinger.lower:.2f}")
        
        # ===== Moving Averages =====
        sma_20 = talib.SMA(close_prices, timeperiod=20)
        sma_50 = talib.SMA(close_prices, timeperiod=50)
        sma_200 = talib.SMA(close_prices, timeperiod=200)
        ema_12 = talib.EMA(close_prices, timeperiod=12)
        ema_26 = talib.EMA(close_prices, timeperiod=26)
        ema_50 = talib.EMA(close_prices, timeperiod=50)
        ema_200 = talib.EMA(close_prices, timeperiod=200)
        
        moving_averages = MovingAverages(
            sma_20=float(sma_20[-1]) if not np.isnan(sma_20[-1]) else current_price,
            sma_50=float(sma_50[-1]) if not np.isnan(sma_50[-1]) else current_price,
            sma_200=float(sma_200[-1]) if not np.isnan(sma_200[-1]) else current_price,
            ema_12=float(ema_12[-1]) if not np.isnan(ema_12[-1]) else current_price,
            ema_26=float(ema_26[-1]) if not np.isnan(ema_26[-1]) else current_price
        )
        
        ema_50_value = float(ema_50[-1]) if not np.isnan(ema_50[-1]) else current_price
        ema_200_value = float(ema_200[-1]) if not np.isnan(ema_200[-1]) else current_price
        
        # Moving Average signal interpretation
        if current_price > moving_averages.sma_50 and current_price > moving_averages.sma_200:
            ma_signal = "bullish"
        elif current_price < moving_averages.sma_50 and current_price < moving_averages.sma_200:
            ma_signal = "bearish"
        else:
            ma_signal = "neutral"
        
        logger.info(f"Moving Averages: SMA50={moving_averages.sma_50:.2f}, SMA200={moving_averages.sma_200:.2f}")
        
        # ===== Golden Cross / Death Cross Detection =====
        # Golden Cross: EMA 50 crosses above EMA 200 (bullish signal)
        # Death Cross: EMA 50 crosses below EMA 200 (bearish signal)
        
        golden_death_cross = None
        
        # Need at least 2 data points to detect crossover
        if len(ema_50) >= 2 and len(ema_200) >= 2:
            ema_50_current = ema_50[-1]
            ema_50_previous = ema_50[-2]
            ema_200_current = ema_200[-1]
            ema_200_previous = ema_200[-2]
            
            # Check for Golden Cross (EMA 50 crosses above EMA 200)
            if ema_50_previous <= ema_200_previous and ema_50_current > ema_200_current:
                golden_death_cross = "golden_cross"
                logger.info("Golden Cross detected: EMA 50 crossed above EMA 200 (bullish)")
            
            # Check for Death Cross (EMA 50 crosses below EMA 200)
            elif ema_50_previous >= ema_200_previous and ema_50_current < ema_200_current:
                golden_death_cross = "death_cross"
                logger.info("Death Cross detected: EMA 50 crossed below EMA 200 (bearish)")
            
            # Also check for recent crossovers (within last 5 candles)
            elif golden_death_cross is None and len(ema_50) >= 5:
                for i in range(2, min(6, len(ema_50))):
                    if ema_50[-i-1] <= ema_200[-i-1] and ema_50[-i] > ema_200[-i]:
                        golden_death_cross = "golden_cross"
                        logger.info(f"Recent Golden Cross detected ({i} candles ago)")
                        break
                    elif ema_50[-i-1] >= ema_200[-i-1] and ema_50[-i] < ema_200[-i]:
                        golden_death_cross = "death_cross"
                        logger.info(f"Recent Death Cross detected ({i} candles ago)")
                        break
        
        # ===== Stochastic Oscillator =====
        stoch_k, stoch_d = talib.STOCH(
            high_prices,
            low_prices,
            close_prices,
            fastk_period=14,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0
        )
        
        stochastic = StochasticValues(
            k=float(stoch_k[-1]) if not np.isnan(stoch_k[-1]) else 50.0,
            d=float(stoch_d[-1]) if not np.isnan(stoch_d[-1]) else 50.0
        )
        
        # Stochastic signal interpretation
        if stochastic.k < 20 and stochastic.d < 20:
            stochastic_signal = "oversold"
        elif stochastic.k > 80 and stochastic.d > 80:
            stochastic_signal = "overbought"
        else:
            stochastic_signal = "neutral"
        
        logger.info(f"Stochastic: K={stochastic.k:.2f}, D={stochastic.d:.2f} ({stochastic_signal})")
        
        # ===== Volume Profile (simplified) =====
        # Calculate Point of Control (POC) - price level with highest volume
        price_volume = df.groupby(df['close'].round(2))['volume'].sum().sort_values(ascending=False)
        poc = float(price_volume.index[0]) if len(price_volume) > 0 else current_price
        
        # Value Area High/Low (70% of volume)
        total_volume = price_volume.sum()
        cumsum = price_volume.cumsum()
        value_area_threshold = total_volume * 0.70
        value_area_prices = price_volume[cumsum <= value_area_threshold].index
        
        vah = float(value_area_prices.max()) if len(value_area_prices) > 0 else current_price * 1.05
        val = float(value_area_prices.min()) if len(value_area_prices) > 0 else current_price * 0.95
        
        volume_profile = VolumeProfile(
            poc=poc,
            vah=vah,
            val=val,
            total_volume=float(total_volume)
        )
        
        logger.info(f"Volume Profile: POC={poc:.2f}, VAH={vah:.2f}, VAL={val:.2f}")
        
        # ===== ATR (Average True Range) =====
        atr_period = 14
        atr_array = talib.ATR(high_prices, low_prices, close_prices, timeperiod=atr_period)
        atr = float(atr_array[-1]) if not np.isnan(atr_array[-1]) else current_price * 0.02
        atr_percent = (atr / current_price) * 100
        
        # Calculate ATR percentile (where current ATR stands in historical distribution)
        atr_percentile = float(np.percentile(atr_array[~np.isnan(atr_array)], 50))
        if atr > 0:
            atr_percentile_value = float(np.sum(atr_array[~np.isnan(atr_array)] <= atr) / len(atr_array[~np.isnan(atr_array)]))
        else:
            atr_percentile_value = 0.5
        
        atr_values = ATRValues(
            atr=atr,
            atr_percent=atr_percent,
            percentile=atr_percentile_value
        )
        
        logger.info(f"ATR: {atr:.2f} ({atr_percent:.2f}% of price, percentile: {atr_percentile_value:.2f})")
        
        # ===== VWAP (Volume Weighted Average Price) =====
        # VWAP = Sum(Price * Volume) / Sum(Volume)
        typical_price = (high_prices + low_prices + close_prices) / 3
        vwap_array = np.cumsum(typical_price * volume) / np.cumsum(volume)
        vwap = float(vwap_array[-1]) if not np.isnan(vwap_array[-1]) else current_price
        
        # VWAP signal interpretation
        if current_price > vwap * 1.01:  # 1% above VWAP
            vwap_signal = "above"
        elif current_price < vwap * 0.99:  # 1% below VWAP
            vwap_signal = "below"
        else:
            vwap_signal = "neutral"
        
        logger.info(f"VWAP: {vwap:.2f} (price is {vwap_signal})")
        
        # ===== OBV (On-Balance Volume) =====
        obv_array = talib.OBV(close_prices, volume)
        obv = float(obv_array[-1]) if not np.isnan(obv_array[-1]) else 0.0
        
        # OBV signal interpretation - check if OBV trend matches price trend
        if len(obv_array) >= 20:
            # Calculate recent trends
            obv_trend = obv_array[-1] - obv_array[-20]
            price_trend = close_prices[-1] - close_prices[-20]
            
            # Check for divergence
            if price_trend > 0 and obv_trend > 0:
                obv_signal = "volume_supported"  # Price up, volume up - healthy
            elif price_trend < 0 and obv_trend < 0:
                obv_signal = "volume_supported"  # Price down, volume down - healthy
            elif (price_trend > 0 and obv_trend < 0) or (price_trend < 0 and obv_trend > 0):
                obv_signal = "volume_divergence"  # Divergence - warning sign
            else:
                obv_signal = "neutral"
        else:
            obv_signal = "neutral"
        
        logger.info(f"OBV: {obv:.0f} ({obv_signal})")
        
        # ===== Fibonacci Retracement Levels =====
        # Find recent swing high and low (last 50 candles)
        lookback = min(50, len(close_prices))
        recent_high = float(np.max(high_prices[-lookback:]))
        recent_low = float(np.min(low_prices[-lookback:]))
        price_range = recent_high - recent_low
        
        # Calculate Fibonacci levels (retracement from high to low)
        fibonacci_levels = FibonacciLevels(
            level_0=recent_high,  # 0% - swing high
            level_236=recent_high - (price_range * 0.236),  # 23.6%
            level_382=recent_high - (price_range * 0.382),  # 38.2%
            level_500=recent_high - (price_range * 0.500),  # 50%
            level_618=recent_high - (price_range * 0.618),  # 61.8%
            level_100=recent_low  # 100% - swing low
        )
        
        logger.info(f"Fibonacci Levels: 0%={fibonacci_levels.level_0:.2f}, 61.8%={fibonacci_levels.level_618:.2f}, 100%={fibonacci_levels.level_100:.2f}")
        
        # ===== ATR-based Dynamic Stop-Loss and Take-Profit =====
        # Stop-Loss: Current price - (2 * ATR) for long positions
        # Take-Profit: Current price + (3 * ATR) for long positions
        # These are dynamic levels that adjust based on volatility
        
        atr_stop_loss_multiplier = 2.0
        atr_take_profit_multiplier = 3.0
        
        # For long positions
        atr_stop_loss = current_price - (atr * atr_stop_loss_multiplier)
        atr_take_profit = current_price + (atr * atr_take_profit_multiplier)
        
        # Ensure stop-loss is not negative
        atr_stop_loss = max(atr_stop_loss, current_price * 0.5)
        
        logger.info(f"ATR-based levels: Stop-Loss={atr_stop_loss:.2f} (-{atr_stop_loss_multiplier}*ATR), Take-Profit={atr_take_profit:.2f} (+{atr_take_profit_multiplier}*ATR)")
        
        # ===== EMA 200 Trend Filter =====
        # Determines if we should only consider long or short signals based on price vs EMA 200
        # If price > EMA 200: Long-only mode (bullish trend)
        # If price < EMA 200: Short-only mode (bearish trend)
        # If price ≈ EMA 200: Neutral (consider both)
        
        ema_200_threshold = 0.02  # 2% threshold for "neutral" zone
        
        if current_price > ema_200_value * (1 + ema_200_threshold):
            ema_200_trend_filter = "long_only"
            logger.info(f"EMA 200 Trend Filter: LONG ONLY (price {current_price:.2f} > EMA200 {ema_200_value:.2f})")
        elif current_price < ema_200_value * (1 - ema_200_threshold):
            ema_200_trend_filter = "short_only"
            logger.info(f"EMA 200 Trend Filter: SHORT ONLY (price {current_price:.2f} < EMA200 {ema_200_value:.2f})")
        else:
            ema_200_trend_filter = "neutral"
            logger.info(f"EMA 200 Trend Filter: NEUTRAL (price {current_price:.2f} ≈ EMA200 {ema_200_value:.2f})")
        
        # Placeholder values for features from later tasks
        
        # ===== Calculate Confluence Score =====
        # Confluence measures how many indicators agree on the direction
        # Score ranges from 0 (all bearish) to 1 (all bullish)
        
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        # RSI
        if rsi_signal == "oversold":
            bullish_signals += 1
        elif rsi_signal == "overbought":
            bearish_signals += 1
        total_signals += 1
        
        # MACD
        if macd_signal == "bullish":
            bullish_signals += 1
        elif macd_signal == "bearish":
            bearish_signals += 1
        total_signals += 1
        
        # Bollinger Bands
        if bollinger_signal == "oversold":
            bullish_signals += 1
        elif bollinger_signal == "overbought":
            bearish_signals += 1
        total_signals += 1
        
        # Moving Averages
        if ma_signal == "bullish":
            bullish_signals += 1
        elif ma_signal == "bearish":
            bearish_signals += 1
        total_signals += 1
        
        # Stochastic
        if stochastic_signal == "oversold":
            bullish_signals += 1
        elif stochastic_signal == "overbought":
            bearish_signals += 1
        total_signals += 1
        
        # VWAP
        if vwap_signal == "above":
            bullish_signals += 1
        elif vwap_signal == "below":
            bearish_signals += 1
        total_signals += 1
        
        # OBV
        if obv_signal == "volume_supported":
            # OBV supports the current trend
            if current_price > moving_averages.sma_50:
                bullish_signals += 1
            else:
                bearish_signals += 1
        elif obv_signal == "volume_divergence":
            # Divergence is a warning, count as neutral
            pass
        total_signals += 1
        
        # RSI Divergence
        if rsi_divergence == "positive":
            bullish_signals += 1
            total_signals += 1
        elif rsi_divergence == "negative":
            bearish_signals += 1
            total_signals += 1
        
        # Golden/Death Cross
        if golden_death_cross == "golden_cross":
            bullish_signals += 2  # Strong signal, count double
            total_signals += 2
        elif golden_death_cross == "death_cross":
            bearish_signals += 2  # Strong signal, count double
            total_signals += 2
        
        # EMA 200 Trend Filter
        if ema_200_trend_filter == "long_only":
            bullish_signals += 1
            total_signals += 1
        elif ema_200_trend_filter == "short_only":
            bearish_signals += 1
            total_signals += 1
        
        # Calculate confluence score
        # 0.5 = neutral, 1.0 = all bullish, 0.0 = all bearish
        if total_signals > 0:
            net_signals = bullish_signals - bearish_signals
            confluence_score = 0.5 + (net_signals / (2 * total_signals))
            confluence_score = max(0.0, min(1.0, confluence_score))  # Clamp to [0, 1]
        else:
            confluence_score = 0.5
        
        logger.info(f"Confluence Score: {confluence_score:.2f} (Bullish: {bullish_signals}, Bearish: {bearish_signals}, Total: {total_signals})")
        
        # ===== Detect Patterns and Support/Resistance =====
        patterns = self.detect_patterns(df)
        support_levels, resistance_levels = self.identify_support_resistance(df)
        
        # Create and return IndicatorResults
        results = IndicatorResults(
            rsi=rsi,
            rsi_signal=rsi_signal,
            rsi_divergence=rsi_divergence,
            macd=macd_values,
            macd_signal=macd_signal,
            bollinger=bollinger,
            bollinger_signal=bollinger_signal,
            moving_averages=moving_averages,
            ma_signal=ma_signal,
            ema_50=ema_50_value,
            ema_200=ema_200_value,
            golden_death_cross=golden_death_cross,
            stochastic=stochastic,
            stochastic_signal=stochastic_signal,
            volume_profile=volume_profile,
            atr=atr_values,
            atr_stop_loss=atr_stop_loss,
            atr_take_profit=atr_take_profit,
            vwap=vwap,
            vwap_signal=vwap_signal,
            obv=obv,
            obv_signal=obv_signal,
            fibonacci_levels=fibonacci_levels,
            patterns=patterns,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            confluence_score=confluence_score,
            ema_200_trend_filter=ema_200_trend_filter
        )
        
        logger.info("Technical indicators calculated successfully")
        return results
    
    def detect_patterns(self, df: pd.DataFrame) -> List[Pattern]:
        """
        Detect chart patterns (head-and-shoulders, triangles, flags, etc.).
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        if len(df) < 20:
            logger.warning("Insufficient data for pattern detection")
            return patterns
        
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        
        # ===== Detect Double Top/Bottom =====
        lookback = min(50, len(close_prices))
        recent_highs = high_prices[-lookback:]
        recent_lows = low_prices[-lookback:]
        
        # Find peaks and troughs
        peaks = []
        troughs = []
        
        for i in range(2, len(recent_highs) - 2):
            # Peak detection
            if (recent_highs[i] > recent_highs[i-1] and 
                recent_highs[i] > recent_highs[i-2] and
                recent_highs[i] > recent_highs[i+1] and 
                recent_highs[i] > recent_highs[i+2]):
                peaks.append((i, recent_highs[i]))
            
            # Trough detection
            if (recent_lows[i] < recent_lows[i-1] and 
                recent_lows[i] < recent_lows[i-2] and
                recent_lows[i] < recent_lows[i+1] and 
                recent_lows[i] < recent_lows[i+2]):
                troughs.append((i, recent_lows[i]))
        
        # Double Top: Two peaks at similar levels
        if len(peaks) >= 2:
            last_peak = peaks[-1][1]
            for i in range(len(peaks) - 2, max(-1, len(peaks) - 5), -1):
                prev_peak = peaks[i][1]
                if abs(last_peak - prev_peak) / prev_peak < 0.02:  # Within 2%
                    patterns.append(Pattern(
                        name="Double Top",
                        confidence=0.7,
                        description="Bearish reversal pattern with two peaks at similar levels"
                    ))
                    logger.info("Double Top pattern detected")
                    break
        
        # Double Bottom: Two troughs at similar levels
        if len(troughs) >= 2:
            last_trough = troughs[-1][1]
            for i in range(len(troughs) - 2, max(-1, len(troughs) - 5), -1):
                prev_trough = troughs[i][1]
                if abs(last_trough - prev_trough) / prev_trough < 0.02:  # Within 2%
                    patterns.append(Pattern(
                        name="Double Bottom",
                        confidence=0.7,
                        description="Bullish reversal pattern with two troughs at similar levels"
                    ))
                    logger.info("Double Bottom pattern detected")
                    break
        
        # ===== Detect Triangle Patterns =====
        if len(close_prices) >= 20:
            recent_prices = close_prices[-20:]
            
            # Ascending Triangle: Higher lows, flat highs
            lows_trend = np.polyfit(range(len(recent_prices)), 
                                    [min(recent_prices[max(0, i-2):i+3]) for i in range(len(recent_prices))], 
                                    1)[0]
            highs_trend = np.polyfit(range(len(recent_prices)), 
                                     [max(recent_prices[max(0, i-2):i+3]) for i in range(len(recent_prices))], 
                                     1)[0]
            
            if lows_trend > 0 and abs(highs_trend) < lows_trend * 0.3:
                patterns.append(Pattern(
                    name="Ascending Triangle",
                    confidence=0.6,
                    description="Bullish continuation pattern with rising lows and flat highs"
                ))
                logger.info("Ascending Triangle pattern detected")
            
            # Descending Triangle: Flat lows, lower highs
            elif abs(lows_trend) < abs(highs_trend) * 0.3 and highs_trend < 0:
                patterns.append(Pattern(
                    name="Descending Triangle",
                    confidence=0.6,
                    description="Bearish continuation pattern with flat lows and falling highs"
                ))
                logger.info("Descending Triangle pattern detected")
        
        # ===== Detect Flag Pattern =====
        if len(close_prices) >= 30:
            # Flag: Strong move followed by consolidation
            pole_start = close_prices[-30]
            pole_end = close_prices[-10]
            flag_prices = close_prices[-10:]
            
            # Check for strong upward move (pole)
            if pole_end > pole_start * 1.05:  # 5% move
                # Check for consolidation (flag)
                flag_range = (max(flag_prices) - min(flag_prices)) / np.mean(flag_prices)
                if flag_range < 0.03:  # Less than 3% range
                    patterns.append(Pattern(
                        name="Bull Flag",
                        confidence=0.65,
                        description="Bullish continuation pattern: strong upward move followed by consolidation"
                    ))
                    logger.info("Bull Flag pattern detected")
            
            # Check for strong downward move
            elif pole_end < pole_start * 0.95:  # 5% move down
                flag_range = (max(flag_prices) - min(flag_prices)) / np.mean(flag_prices)
                if flag_range < 0.03:
                    patterns.append(Pattern(
                        name="Bear Flag",
                        confidence=0.65,
                        description="Bearish continuation pattern: strong downward move followed by consolidation"
                    ))
                    logger.info("Bear Flag pattern detected")
        
        logger.info(f"Detected {len(patterns)} chart patterns")
        return patterns
    
    def identify_support_resistance(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        Identify support and resistance levels.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        if len(df) < 20:
            logger.warning("Insufficient data for support/resistance detection")
            return [], []
        
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        
        support_levels = []
        resistance_levels = []
        
        # Use recent data for level detection
        lookback = min(100, len(df))
        recent_highs = high_prices[-lookback:]
        recent_lows = low_prices[-lookback:]
        recent_closes = close_prices[-lookback:]
        
        # ===== Find Resistance Levels (peaks) =====
        for i in range(2, len(recent_highs) - 2):
            if (recent_highs[i] > recent_highs[i-1] and 
                recent_highs[i] > recent_highs[i-2] and
                recent_highs[i] > recent_highs[i+1] and 
                recent_highs[i] > recent_highs[i+2]):
                resistance_levels.append(float(recent_highs[i]))
        
        # ===== Find Support Levels (troughs) =====
        for i in range(2, len(recent_lows) - 2):
            if (recent_lows[i] < recent_lows[i-1] and 
                recent_lows[i] < recent_lows[i-2] and
                recent_lows[i] < recent_lows[i+1] and 
                recent_lows[i] < recent_lows[i+2]):
                support_levels.append(float(recent_lows[i]))
        
        # ===== Cluster similar levels =====
        def cluster_levels(levels, threshold=0.02):
            """Cluster levels that are within threshold% of each other."""
            if not levels:
                return []
            
            levels = sorted(levels)
            clustered = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] < threshold:
                    current_cluster.append(level)
                else:
                    # Average the cluster
                    clustered.append(sum(current_cluster) / len(current_cluster))
                    current_cluster = [level]
            
            # Add last cluster
            if current_cluster:
                clustered.append(sum(current_cluster) / len(current_cluster))
            
            return clustered
        
        support_levels = cluster_levels(support_levels)
        resistance_levels = cluster_levels(resistance_levels)
        
        # Keep only the most significant levels (top 5 each)
        current_price = float(close_prices[-1])
        
        # Sort support levels by proximity to current price (but below it)
        support_levels = [s for s in support_levels if s < current_price]
        support_levels = sorted(support_levels, reverse=True)[:5]
        
        # Sort resistance levels by proximity to current price (but above it)
        resistance_levels = [r for r in resistance_levels if r > current_price]
        resistance_levels = sorted(resistance_levels)[:5]
        
        logger.info(f"Identified {len(support_levels)} support levels and {len(resistance_levels)} resistance levels")
        
        return support_levels, resistance_levels
    
    def generate_technical_score(self, indicators: IndicatorResults) -> float:
        """
        Generate overall technical analysis score (0-1).
        
        Args:
            indicators: Calculated indicator results
        
        Returns:
            Technical score between 0 and 1
        """
        # Technical score generation will be implemented after all indicators
        raise NotImplementedError("Technical score generation will be implemented later")

