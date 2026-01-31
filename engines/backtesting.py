"""
Backtesting Engine for testing trading strategies on historical data.
Implements core backtesting algorithm, trade simulation, and metrics calculation.
"""
import uuid
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import logger
from models.schemas import (
    BacktestParameters, BacktestTrade, BacktestMetrics, BacktestResult,
    BacktestComparison, Signal, SignalType, IndicatorResults, OverallSentiment
)
from engines.technical_analysis import TechnicalAnalysisEngine
from engines.fundamental_analysis import FundamentalAnalysisEngine
from engines.signal_generator import SignalGenerator
from engines.data_collector import PriceDataCollector
import asyncio


class BacktestingEngine:
    """
    Backtesting Engine for cryptocurrency trading strategies.
    Tests strategies on historical data and calculates performance metrics.
    """
    
    def __init__(self):
        """Initialize backtesting engine with required components."""
        self.technical_engine = TechnicalAnalysisEngine()
        self.fundamental_engine = FundamentalAnalysisEngine()
        self.signal_generator = SignalGenerator()
        self.data_collector = PriceDataCollector()
        
        logger.info("Backtesting Engine initialized")
    
    async def start_backtest(
        self,
        coin: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        parameters: BacktestParameters
    ) -> str:
        """
        Start a backtest and return the backtest ID.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            timeframe: Timeframe (e.g., "1h", "4h")
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Initial capital in USD
            parameters: Backtesting parameters
        
        Returns:
            Backtest ID (UUID)
        
        Validates: Gereksinim 19.1 - Backtesting başlatma
        """
        backtest_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting backtest {backtest_id} for {coin} {timeframe} "
            f"from {start_date} to {end_date} with ${initial_capital} initial capital"
        )
        
        # Validate dates
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
        
        # Validate timeframe
        valid_timeframes = ['15m', '1h', '4h', '8h', '12h', '24h', '1w', '15d', '1M']
        if timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe. Must be one of {valid_timeframes}")
        
        # Calculate required data points
        # Need enough historical data for indicators (at least 200 candles)
        period_days = (end_date - start_date).days
        
        # Estimate candles needed based on timeframe
        timeframe_to_hours = {
            '15m': 0.25,
            '1h': 1,
            '4h': 4,
            '8h': 8,
            '12h': 12,
            '24h': 24,
            '1w': 168,
            '15d': 360,
            '1M': 720
        }
        
        hours_per_candle = timeframe_to_hours.get(timeframe, 1)
        estimated_candles = int((period_days * 24) / hours_per_candle)
        
        if estimated_candles < 50:
            raise ValueError(
                f"Insufficient data points for backtest. "
                f"Period too short for {timeframe} timeframe. "
                f"Estimated candles: {estimated_candles}, minimum: 50"
            )
        
        logger.info(
            f"Backtest period: {period_days} days, "
            f"estimated candles: {estimated_candles}"
        )
        
        return backtest_id
    
    async def run_backtest_core(
        self,
        coin: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        parameters: BacktestParameters
    ) -> BacktestResult:
        """
        Core backtesting algorithm - iterates through historical data,
        performs analysis at each point, generates signals, and simulates trades.
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            initial_capital: Initial capital
            parameters: Backtesting parameters
        
        Returns:
            Complete backtest result with trades and metrics
        
        Validates: Gereksinim 19.3, 19.4 - Analiz ve sinyal üretimi
        """
        backtest_id = await self.start_backtest(
            coin, timeframe, start_date, end_date, initial_capital, parameters
        )
        
        logger.info(f"Running core backtest algorithm for {backtest_id}")
        
        # Fetch historical OHLCV data
        # Calculate required limit (add buffer for indicators)
        period_days = (end_date - start_date).days
        timeframe_to_hours = {
            '15m': 0.25, '1h': 1, '4h': 4, '8h': 8, '12h': 12,
            '24h': 24, '1w': 168, '15d': 360, '1M': 720
        }
        hours_per_candle = timeframe_to_hours.get(timeframe, 1)
        limit = int((period_days * 24) / hours_per_candle) + 200  # Add 200 for indicator warmup
        
        try:
            ohlcv_data = await self.data_collector.fetch_ohlcv(
                coin, timeframe, limit=min(limit, 1000), use_cache=False
            )
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data for backtest: {e}")
            raise ValueError(f"Unable to fetch historical data for {coin}")
        
        if not ohlcv_data:
            raise ValueError(f"No historical data available for {coin}")
        
        # Process OHLCV data
        df = self.technical_engine.process_ohlcv_data(ohlcv_data)
        
        # Filter data to backtest period
        df_backtest = df[(df.index >= start_date) & (df.index <= end_date)]
        
        if len(df_backtest) < 50:
            raise ValueError(
                f"Insufficient data in backtest period. "
                f"Found {len(df_backtest)} candles, minimum 50 required"
            )
        
        logger.info(
            f"Backtesting on {len(df_backtest)} candles "
            f"from {df_backtest.index[0]} to {df_backtest.index[-1]}"
        )
        
        # Initialize backtest state
        trades: List[BacktestTrade] = []
        equity_curve: List[Tuple[datetime, float]] = []
        current_capital = initial_capital
        current_position = None  # None or dict with entry details
        
        # Iterate through each data point
        for i in range(200, len(df)):  # Start after warmup period
            current_timestamp = df.index[i]
            
            # Skip if outside backtest period
            if current_timestamp < start_date:
                continue
            if current_timestamp > end_date:
                break
            
            # Get data up to current point (for analysis)
            historical_df = df.iloc[:i+1]
            
            try:
                # Perform technical analysis
                indicators = self.technical_engine.calculate_indicators(historical_df)
                
                # Perform fundamental analysis if enabled
                if parameters.use_fundamental:
                    # For backtesting, we'll use a simplified sentiment (neutral)
                    # In production, this would fetch historical sentiment data
                    fundamental = OverallSentiment(
                        overall_score=0.0,
                        classification="neutral",
                        trend="stable",
                        sources=[]
                    )
                else:
                    fundamental = OverallSentiment(
                        overall_score=0.0,
                        classification="neutral",
                        trend="stable",
                        sources=[]
                    )
                
                # Generate signal
                technical_score = self.signal_generator.generate_technical_score(indicators)
                fundamental_score = 0.5  # Neutral for backtesting
                
                success_probability = self.signal_generator.calculate_success_probability(
                    technical_score, fundamental_score, indicators.confluence_score
                )
                
                # Apply adjustments
                success_probability = self.signal_generator.apply_conflict_penalty(
                    success_probability, technical_score, fundamental_score
                )
                success_probability = self.signal_generator.apply_harmony_bonus(
                    success_probability, technical_score, fundamental_score
                )
                
                signal_direction = self.signal_generator.determine_signal_direction(
                    technical_score, fundamental_score
                )
                
                success_probability = self.signal_generator.apply_ema_200_trend_filter(
                    success_probability, indicators, signal_direction
                )
                success_probability = self.signal_generator.apply_golden_death_cross_bonus(
                    success_probability, indicators, signal_direction
                )
                success_probability = self.signal_generator.apply_rsi_divergence_bonus(
                    success_probability, indicators, signal_direction
                )
                success_probability = self.signal_generator.apply_atr_volatility_adjustment(
                    success_probability, indicators
                )
                
                signal = self.signal_generator.generate_signal(
                    success_probability, signal_direction, coin, timeframe, indicators
                )
                
                # Get current price
                current_price = float(historical_df['close'].iloc[-1])
                
                # Trade simulation logic
                # Check if signal meets threshold
                if signal.success_probability >= parameters.signal_threshold:
                    # BUY signal and no position
                    if signal.signal_type in [SignalType.STRONG_BUY, SignalType.BUY] and current_position is None:
                        # Enter long position
                        current_position = {
                            'entry_date': current_timestamp,
                            'entry_price': current_price,
                            'signal': signal,
                            'type': 'LONG'
                        }
                        logger.debug(
                            f"[{current_timestamp}] ENTER LONG at ${current_price:.2f} "
                            f"(signal: {signal.signal_type.value}, prob: {signal.success_probability:.1f}%)"
                        )
                    
                    # SELL signal and have position
                    elif signal.signal_type in [SignalType.STRONG_SELL, SignalType.SELL] and current_position is not None:
                        # Exit position
                        entry_price = current_position['entry_price']
                        entry_date = current_position['entry_date']
                        
                        # Calculate profit/loss
                        profit_loss = current_capital * ((current_price - entry_price) / entry_price)
                        profit_loss_percent = ((current_price - entry_price) / entry_price) * 100
                        
                        # Update capital
                        current_capital += profit_loss
                        
                        # Record trade
                        trade = BacktestTrade(
                            entry_date=entry_date,
                            entry_price=entry_price,
                            exit_date=current_timestamp,
                            exit_price=current_price,
                            profit_loss=profit_loss,
                            profit_loss_percent=profit_loss_percent,
                            signal_at_entry=current_position['signal']
                        )
                        trades.append(trade)
                        
                        logger.debug(
                            f"[{current_timestamp}] EXIT LONG at ${current_price:.2f} "
                            f"(P/L: ${profit_loss:.2f}, {profit_loss_percent:.2f}%)"
                        )
                        
                        # Clear position
                        current_position = None
                
                # Record equity curve
                equity = current_capital
                if current_position is not None:
                    # Add unrealized P/L
                    unrealized_pl = current_capital * (
                        (current_price - current_position['entry_price']) / current_position['entry_price']
                    )
                    equity += unrealized_pl
                
                equity_curve.append((current_timestamp, equity))
                
            except Exception as e:
                logger.warning(f"Error analyzing data point at {current_timestamp}: {e}")
                # Continue with next data point
                continue
        
        # Close any open position at end of backtest
        if current_position is not None:
            final_price = float(df_backtest['close'].iloc[-1])
            final_timestamp = df_backtest.index[-1]
            
            entry_price = current_position['entry_price']
            entry_date = current_position['entry_date']
            
            profit_loss = current_capital * ((final_price - entry_price) / entry_price)
            profit_loss_percent = ((final_price - entry_price) / entry_price) * 100
            
            current_capital += profit_loss
            
            trade = BacktestTrade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=final_timestamp,
                exit_price=final_price,
                profit_loss=profit_loss,
                profit_loss_percent=profit_loss_percent,
                signal_at_entry=current_position['signal']
            )
            trades.append(trade)
            
            logger.info(f"Closed final position at end of backtest: P/L ${profit_loss:.2f}")
        
        logger.info(
            f"Backtest complete: {len(trades)} trades executed, "
            f"final capital: ${current_capital:.2f}"
        )
        
        # Calculate metrics
        metrics = self.calculate_metrics(trades, initial_capital, equity_curve)
        
        # Create result
        result = BacktestResult(
            id=backtest_id,
            coin=coin,
            timeframe=timeframe,
            period=(start_date, end_date),
            parameters=parameters,
            trades=trades,
            metrics=metrics,
            equity_curve=equity_curve
        )
        
        return result
    
    def calculate_metrics(
        self,
        trades: List[BacktestTrade],
        initial_capital: float,
        equity_curve: List[Tuple[datetime, float]]
    ) -> BacktestMetrics:
        """
        Calculate performance metrics from trades and equity curve.
        
        Args:
            trades: List of executed trades
            initial_capital: Initial capital
            equity_curve: Equity curve data
        
        Returns:
            Calculated metrics
        
        Validates: Gereksinim 19.6 - Metrik hesaplamaları
        """
        if not trades:
            # No trades executed
            return BacktestMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_profit_loss=0.0,
                total_profit_loss_percent=0.0,
                max_drawdown=0.0,
                max_drawdown_percent=0.0,
                average_trade_duration=timedelta(0),
                sharpe_ratio=0.0,
                profit_factor=0.0
            )
        
        # Count winning and losing trades
        winning_trades = sum(1 for t in trades if t.profit_loss > 0)
        losing_trades = sum(1 for t in trades if t.profit_loss <= 0)
        total_trades = len(trades)
        
        # Win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        # Total profit/loss
        total_profit_loss = sum(t.profit_loss for t in trades)
        total_profit_loss_percent = (total_profit_loss / initial_capital) * 100
        
        # Maximum drawdown
        max_drawdown, max_drawdown_percent = self._calculate_max_drawdown(equity_curve)
        
        # Average trade duration
        trade_durations = [(t.exit_date - t.entry_date) for t in trades]
        average_trade_duration = sum(trade_durations, timedelta(0)) / len(trade_durations)
        
        # Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio(trades, equity_curve)
        
        # Profit factor
        profit_factor = self._calculate_profit_factor(trades)
        
        metrics = BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percent=total_profit_loss_percent,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            average_trade_duration=average_trade_duration,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor
        )
        
        logger.info(
            f"Metrics calculated: {total_trades} trades, "
            f"{win_rate:.1f}% win rate, "
            f"{total_profit_loss_percent:.2f}% total return"
        )
        
        return metrics
    
    def _calculate_max_drawdown(
        self,
        equity_curve: List[Tuple[datetime, float]]
    ) -> Tuple[float, float]:
        """
        Calculate maximum drawdown from equity curve.
        
        Args:
            equity_curve: List of (timestamp, equity) tuples
        
        Returns:
            Tuple of (max_drawdown_absolute, max_drawdown_percent)
        """
        if not equity_curve:
            return 0.0, 0.0
        
        equity_values = [e[1] for e in equity_curve]
        
        max_drawdown = 0.0
        max_drawdown_percent = 0.0
        peak = equity_values[0]
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            
            drawdown = peak - equity
            drawdown_percent = (drawdown / peak * 100) if peak > 0 else 0.0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_percent = drawdown_percent
        
        return max_drawdown, max_drawdown_percent
    
    def _calculate_sharpe_ratio(
        self,
        trades: List[BacktestTrade],
        equity_curve: List[Tuple[datetime, float]],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            trades: List of trades
            equity_curve: Equity curve data
            risk_free_rate: Annual risk-free rate (default 2%)
        
        Returns:
            Sharpe ratio
        """
        if not trades or len(equity_curve) < 2:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i-1][1]
            curr_equity = equity_curve[i][1]
            if prev_equity > 0:
                ret = (curr_equity - prev_equity) / prev_equity
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        # Calculate average return and standard deviation
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming daily returns)
        # Sharpe = (avg_return - risk_free_rate) / std_return * sqrt(periods_per_year)
        periods_per_year = 365
        sharpe = (avg_return - risk_free_rate / periods_per_year) / std_return * np.sqrt(periods_per_year)
        
        return float(sharpe)
    
    def _calculate_profit_factor(self, trades: List[BacktestTrade]) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Args:
            trades: List of trades
        
        Returns:
            Profit factor
        """
        if not trades:
            return 0.0
        
        gross_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in trades if t.profit_loss < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def compare_backtests(self, backtest_ids: List[str]) -> BacktestComparison:
        """
        Compare multiple backtest results.
        
        Args:
            backtest_ids: List of backtest IDs to compare
        
        Returns:
            Comparison of backtest results
        
        Validates: Gereksinim 19.10 - Backtesting karşılaştırma
        """
        # This will be implemented after database integration
        # For now, return a placeholder
        raise NotImplementedError("Backtest comparison will be implemented with database integration")
    
    def generate_backtest_report(self, result: BacktestResult) -> Dict:
        """
        Generate detailed backtest report with charts and tables.
        
        Args:
            result: Backtest result
        
        Returns:
            Report data dictionary
        
        Validates: Gereksinim 19.7 - Backtesting sonuç sunumu
        """
        report = {
            'id': result.id,
            'coin': result.coin,
            'timeframe': result.timeframe,
            'period': {
                'start': result.period[0].isoformat(),
                'end': result.period[1].isoformat()
            },
            'parameters': {
                'indicators': result.parameters.indicators,
                'indicator_thresholds': result.parameters.indicator_thresholds,
                'use_fundamental': result.parameters.use_fundamental,
                'signal_threshold': result.parameters.signal_threshold
            },
            'metrics': {
                'total_trades': result.metrics.total_trades,
                'winning_trades': result.metrics.winning_trades,
                'losing_trades': result.metrics.losing_trades,
                'win_rate': result.metrics.win_rate,
                'total_profit_loss': result.metrics.total_profit_loss,
                'total_profit_loss_percent': result.metrics.total_profit_loss_percent,
                'max_drawdown': result.metrics.max_drawdown,
                'max_drawdown_percent': result.metrics.max_drawdown_percent,
                'average_trade_duration': str(result.metrics.average_trade_duration),
                'sharpe_ratio': result.metrics.sharpe_ratio,
                'profit_factor': result.metrics.profit_factor
            },
            'trades': [
                {
                    'entry_date': t.entry_date.isoformat(),
                    'entry_price': t.entry_price,
                    'exit_date': t.exit_date.isoformat(),
                    'exit_price': t.exit_price,
                    'profit_loss': t.profit_loss,
                    'profit_loss_percent': t.profit_loss_percent,
                    'duration': str(t.exit_date - t.entry_date)
                }
                for t in result.trades
            ],
            'equity_curve': [
                {
                    'timestamp': timestamp.isoformat(),
                    'equity': equity
                }
                for timestamp, equity in result.equity_curve
            ]
        }
        
        logger.info(f"Generated backtest report for {result.id}")
        return report
