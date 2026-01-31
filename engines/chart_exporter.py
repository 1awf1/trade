"""
Chart Exporter
Exports charts as PNG images for inclusion in reports.
Supports: Price charts, indicator charts, equity curves, performance charts
"""
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import base64
from io import BytesIO

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import pandas as pd
import numpy as np

from models.schemas import (
    IndicatorResults, BacktestResult, PerformanceSnapshot
)


class ChartExporter:
    """
    Exports various chart types as PNG images.
    Charts are returned as base64 encoded strings for embedding in HTML/PDF.
    """
    
    def __init__(self, dpi: int = 100, figsize: Tuple[int, int] = (12, 6)):
        """
        Initialize chart exporter.
        
        Args:
            dpi: Resolution of exported images
            figsize: Figure size in inches (width, height)
        """
        self.dpi = dpi
        self.figsize = figsize
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
    
    # ========================================================================
    # Price and Technical Analysis Charts
    # ========================================================================
    
    def export_price_chart(
        self,
        df: pd.DataFrame,
        coin: str,
        indicators: Optional[IndicatorResults] = None
    ) -> str:
        """
        Export price chart with optional technical indicators.
        
        Args:
            df: DataFrame with OHLCV data (columns: timestamp, open, high, low, close, volume)
            coin: Coin symbol
            indicators: Optional technical indicators to overlay
        
        Returns:
            Base64 encoded PNG image
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, 
                                        gridspec_kw={'height_ratios': [3, 1]})
        
        # Price chart
        ax1.plot(df['timestamp'], df['close'], label='Close Price', color='#1976D2', linewidth=2)
        
        # Add moving averages if available
        if indicators:
            if 'sma_20' in df.columns:
                ax1.plot(df['timestamp'], df['sma_20'], label='SMA 20', 
                        color='#FFA726', linestyle='--', alpha=0.7)
            if 'ema_50' in df.columns:
                ax1.plot(df['timestamp'], df['ema_50'], label='EMA 50', 
                        color='#66BB6A', linestyle='--', alpha=0.7)
            if 'ema_200' in df.columns:
                ax1.plot(df['timestamp'], df['ema_200'], label='EMA 200', 
                        color='#EF5350', linestyle='--', alpha=0.7)
            
            # Add support/resistance levels
            for level in indicators.support_levels[:3]:  # Top 3 support levels
                ax1.axhline(y=level, color='green', linestyle=':', alpha=0.5, linewidth=1)
            for level in indicators.resistance_levels[:3]:  # Top 3 resistance levels
                ax1.axhline(y=level, color='red', linestyle=':', alpha=0.5, linewidth=1)
        
        ax1.set_title(f'{coin} Fiyat Grafiği', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Fiyat ($)', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Volume chart
        colors = ['green' if df['close'].iloc[i] >= df['open'].iloc[i] else 'red' 
                  for i in range(len(df))]
        ax2.bar(df['timestamp'], df['volume'], color=colors, alpha=0.5)
        ax2.set_ylabel('Hacim', fontsize=12)
        ax2.set_xlabel('Tarih', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Convert to base64
        return self._fig_to_base64(fig)
    
    def export_rsi_chart(self, df: pd.DataFrame, coin: str) -> str:
        """
        Export RSI indicator chart.
        
        Args:
            df: DataFrame with timestamp and rsi columns
            coin: Coin symbol
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        ax.plot(df['timestamp'], df['rsi'], label='RSI', color='#9C27B0', linewidth=2)
        ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought (70)')
        ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold (30)')
        ax.fill_between(df['timestamp'], 30, 70, alpha=0.1, color='gray')
        
        ax.set_title(f'{coin} RSI İndikatörü', fontsize=14, fontweight='bold')
        ax.set_ylabel('RSI', fontsize=12)
        ax.set_xlabel('Tarih', fontsize=12)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def export_macd_chart(self, df: pd.DataFrame, coin: str) -> str:
        """
        Export MACD indicator chart.
        
        Args:
            df: DataFrame with timestamp, macd, signal, histogram columns
            coin: Coin symbol
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        ax.plot(df['timestamp'], df['macd'], label='MACD', color='#2196F3', linewidth=2)
        ax.plot(df['timestamp'], df['signal'], label='Signal', color='#FF9800', linewidth=2)
        
        # Histogram
        colors = ['green' if val >= 0 else 'red' for val in df['histogram']]
        ax.bar(df['timestamp'], df['histogram'], label='Histogram', 
               color=colors, alpha=0.3, width=0.8)
        
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        
        ax.set_title(f'{coin} MACD İndikatörü', fontsize=14, fontweight='bold')
        ax.set_ylabel('MACD', fontsize=12)
        ax.set_xlabel('Tarih', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def export_bollinger_bands_chart(self, df: pd.DataFrame, coin: str) -> str:
        """
        Export Bollinger Bands chart.
        
        Args:
            df: DataFrame with timestamp, close, bb_upper, bb_middle, bb_lower columns
            coin: Coin symbol
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        ax.plot(df['timestamp'], df['close'], label='Close Price', 
                color='#1976D2', linewidth=2)
        ax.plot(df['timestamp'], df['bb_upper'], label='Upper Band', 
                color='red', linestyle='--', alpha=0.7)
        ax.plot(df['timestamp'], df['bb_middle'], label='Middle Band', 
                color='gray', linestyle='--', alpha=0.7)
        ax.plot(df['timestamp'], df['bb_lower'], label='Lower Band', 
                color='green', linestyle='--', alpha=0.7)
        
        ax.fill_between(df['timestamp'], df['bb_lower'], df['bb_upper'], 
                        alpha=0.1, color='gray')
        
        ax.set_title(f'{coin} Bollinger Bands', fontsize=14, fontweight='bold')
        ax.set_ylabel('Fiyat ($)', fontsize=12)
        ax.set_xlabel('Tarih', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    # ========================================================================
    # Backtest Charts
    # ========================================================================
    
    def export_equity_curve(self, backtest: BacktestResult) -> str:
        """
        Export equity curve from backtest result.
        
        Args:
            backtest: Backtest result with equity curve
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Extract data
        timestamps = [point[0] for point in backtest.equity_curve]
        equity = [point[1] for point in backtest.equity_curve]
        
        ax.plot(timestamps, equity, label='Equity', color='#1976D2', linewidth=2)
        ax.fill_between(timestamps, equity, alpha=0.2, color='#1976D2')
        
        # Add horizontal line at starting equity
        initial_equity = equity[0]
        ax.axhline(y=initial_equity, color='gray', linestyle='--', 
                   alpha=0.5, label=f'Başlangıç: ${initial_equity:.2f}')
        
        ax.set_title(f'{backtest.coin} Equity Curve', fontsize=14, fontweight='bold')
        ax.set_ylabel('Portföy Değeri ($)', fontsize=12)
        ax.set_xlabel('Tarih', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def export_drawdown_chart(self, backtest: BacktestResult) -> str:
        """
        Export drawdown chart from backtest result.
        
        Args:
            backtest: Backtest result with equity curve
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Calculate drawdown
        timestamps = [point[0] for point in backtest.equity_curve]
        equity = np.array([point[1] for point in backtest.equity_curve])
        
        # Running maximum
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100
        
        ax.fill_between(timestamps, drawdown, 0, color='red', alpha=0.3)
        ax.plot(timestamps, drawdown, color='red', linewidth=2, label='Drawdown')
        
        ax.set_title(f'{backtest.coin} Drawdown', fontsize=14, fontweight='bold')
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.set_xlabel('Tarih', fontsize=12)
        ax.legend(loc='lower left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def export_trade_distribution(self, backtest: BacktestResult) -> str:
        """
        Export trade profit/loss distribution chart.
        
        Args:
            backtest: Backtest result with trades
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Extract profit/loss percentages
        pl_percentages = [trade.profit_loss_percent for trade in backtest.trades]
        
        # Create histogram
        colors = ['green' if pl >= 0 else 'red' for pl in pl_percentages]
        ax.bar(range(len(pl_percentages)), pl_percentages, color=colors, alpha=0.6)
        
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        
        ax.set_title(f'{backtest.coin} İşlem Kar/Zarar Dağılımı', 
                    fontsize=14, fontweight='bold')
        ax.set_ylabel('Kar/Zarar (%)', fontsize=12)
        ax.set_xlabel('İşlem #', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    # ========================================================================
    # Portfolio Charts
    # ========================================================================
    
    def export_portfolio_performance(
        self,
        performance_history: List[PerformanceSnapshot]
    ) -> str:
        """
        Export portfolio performance over time.
        
        Args:
            performance_history: List of performance snapshots
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        timestamps = [snap.timestamp for snap in performance_history]
        values = [float(snap.total_value) for snap in performance_history]
        
        ax.plot(timestamps, values, label='Portföy Değeri', 
                color='#1976D2', linewidth=2, marker='o', markersize=4)
        ax.fill_between(timestamps, values, alpha=0.2, color='#1976D2')
        
        # Add starting value line
        if values:
            ax.axhline(y=values[0], color='gray', linestyle='--', 
                      alpha=0.5, label=f'Başlangıç: ${values[0]:.2f}')
        
        ax.set_title('Portföy Performansı', fontsize=14, fontweight='bold')
        ax.set_ylabel('Toplam Değer ($)', fontsize=12)
        ax.set_xlabel('Tarih', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def export_portfolio_allocation(self, holdings: List[Dict]) -> str:
        """
        Export portfolio allocation pie chart.
        
        Args:
            holdings: List of holdings with coin and current_value
        
        Returns:
            Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        
        coins = [h['coin'] for h in holdings]
        values = [float(h['current_value']) for h in holdings]
        
        # Create pie chart
        colors = plt.cm.Set3(range(len(coins)))
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=coins, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        
        # Beautify text
        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.set_title('Portföy Dağılımı', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _fig_to_base64(self, fig: Figure) -> str:
        """
        Convert matplotlib figure to base64 encoded PNG.
        
        Args:
            fig: Matplotlib figure
        
        Returns:
            Base64 encoded string
        """
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight')
        buffer.seek(0)
        
        # Encode to base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        # Close figure to free memory
        plt.close(fig)
        
        return image_base64
    
    def export_multiple_charts(
        self,
        df: pd.DataFrame,
        coin: str,
        indicators: Optional[IndicatorResults] = None
    ) -> Dict[str, str]:
        """
        Export multiple charts at once for a complete analysis.
        
        Args:
            df: DataFrame with OHLCV and indicator data
            coin: Coin symbol
            indicators: Technical indicators
        
        Returns:
            Dictionary mapping chart names to base64 encoded images
        """
        charts = {}
        
        # Price chart
        charts['Fiyat Grafiği'] = self.export_price_chart(df, coin, indicators)
        
        # RSI chart (if available)
        if 'rsi' in df.columns:
            charts['RSI İndikatörü'] = self.export_rsi_chart(df, coin)
        
        # MACD chart (if available)
        if all(col in df.columns for col in ['macd', 'signal', 'histogram']):
            charts['MACD İndikatörü'] = self.export_macd_chart(df, coin)
        
        # Bollinger Bands (if available)
        if all(col in df.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
            charts['Bollinger Bands'] = self.export_bollinger_bands_chart(df, coin)
        
        return charts
