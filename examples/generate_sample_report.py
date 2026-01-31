"""
Sample script demonstrating report generation functionality.
Generates HTML and PDF reports for analysis, backtest, and portfolio.
"""
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.report_generator import ReportGenerator
from models.schemas import (
    AnalysisResult, Signal, SignalType, IndicatorResults, OverallSentiment,
    SignalExplanation, MACDValues, BollingerBands, MovingAverages,
    StochasticValues, VolumeProfile, ATRValues, FibonacciLevels, Pattern,
    SentimentResults, SentimentClassification, TrendDirection,
    BacktestResult, BacktestParameters, BacktestTrade, BacktestMetrics,
    Portfolio, Holding
)


def create_sample_analysis():
    """Create a sample analysis result."""
    return AnalysisResult(
        id="sample-analysis-001",
        coin="BTC",
        timeframe="1h",
        timestamp=datetime.utcnow(),
        technical_results=IndicatorResults(
            rsi=65.5,
            rsi_signal="neutral",
            rsi_divergence="positive",
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
            golden_death_cross="golden_cross",
            stochastic=StochasticValues(k=70, d=65),
            stochastic_signal="overbought",
            volume_profile=VolumeProfile(poc=48000, vah=49000, val=47000, total_volume=1000000),
            atr=ATRValues(atr=1500, atr_percent=3.1, percentile=0.6),
            atr_stop_loss=46500,
            atr_take_profit=51500,
            vwap=48200,
            vwap_signal="above",
            obv=5000000,
            obv_signal="volume_supported",
            fibonacci_levels=FibonacciLevels(
                level_0=45000, level_236=46180, level_382=46910,
                level_500=47500, level_618=48090, level_100=50000
            ),
            patterns=[
                Pattern(name="Bullish Flag", confidence=0.75, 
                       description="Upward continuation pattern indicating potential breakout")
            ],
            support_levels=[46000, 45000, 44000],
            resistance_levels=[50000, 51000, 52000],
            confluence_score=0.72,
            ema_200_trend_filter="long_only"
        ),
        fundamental_results=OverallSentiment(
            overall_score=0.45,
            classification=SentimentClassification.POSITIVE,
            trend=TrendDirection.RISING,
            sources=[
                SentimentResults(
                    source="twitter",
                    sentiment_score=0.5,
                    confidence=0.8,
                    sample_size=100,
                    timestamp=datetime.utcnow()
                ),
                SentimentResults(
                    source="reddit",
                    sentiment_score=0.4,
                    confidence=0.75,
                    sample_size=50,
                    timestamp=datetime.utcnow()
                )
            ]
        ),
        signal=Signal(
            signal_type=SignalType.BUY,
            success_probability=72.5,
            timestamp=datetime.utcnow(),
            coin="BTC",
            timeframe="1h",
            stop_loss=46500,
            take_profit=51500,
            ema_200_filter_applied=True,
            golden_death_cross_detected="golden_cross",
            rsi_divergence_detected="positive"
        ),
        explanation=SignalExplanation(
            signal=Signal(
                signal_type=SignalType.BUY,
                success_probability=72.5,
                timestamp=datetime.utcnow(),
                coin="BTC",
                timeframe="1h"
            ),
            technical_reasons=[
                "RSI showing neutral momentum with positive divergence",
                "MACD bullish crossover confirmed",
                "Golden Cross detected (EMA 50 crossed above EMA 200)",
                "Price trading above VWAP indicating bullish sentiment"
            ],
            fundamental_reasons=[
                "Positive sentiment on social media (Twitter: 0.5, Reddit: 0.4)",
                "Rising sentiment trend across all sources",
                "Strong community engagement"
            ],
            supporting_indicators=["MACD", "EMA", "VWAP", "OBV", "Golden Cross"],
            conflicting_indicators=["Stochastic overbought"],
            risk_factors=[
                "High volatility (ATR 3.1%)",
                "Stochastic indicator showing overbought conditions",
                "Approaching resistance level at $50,000"
            ]
        ),
        ai_report="""Bitcoin (BTC) Analysis Summary:

The current technical analysis shows a bullish setup with strong momentum indicators. The recent Golden Cross (EMA 50 crossing above EMA 200) is a significant bullish signal that often precedes sustained upward trends.

Key Strengths:
- MACD showing bullish momentum with positive histogram
- Price trading above VWAP, indicating institutional buying support
- On-Balance Volume (OBV) confirms price movement with volume support
- Positive RSI divergence suggests underlying strength
- Strong confluence score (0.72) indicates multiple indicators aligning

Considerations:
- Stochastic oscillator is in overbought territory, suggesting potential short-term pullback
- ATR at 3.1% indicates elevated volatility
- Approaching major resistance at $50,000

Fundamental Analysis:
Social media sentiment is positive and rising, with Twitter and Reddit showing bullish sentiment. This aligns with the technical picture and suggests strong community support.

Recommendation:
BUY signal with 72.5% success probability. Consider entering with stop-loss at $46,500 (ATR-based) and take-profit at $51,500. Monitor the $50,000 resistance level closely for potential breakout or rejection.""",
        actual_outcome=None,
        price_at_analysis=48000.0,
        price_after_period=None
    )


def main():
    """Generate sample reports."""
    print("Generating sample reports...")
    print("=" * 60)
    
    # Create report generator
    generator = ReportGenerator()
    
    # 1. Generate Analysis Report
    print("\n1. Generating Analysis Report...")
    analysis = create_sample_analysis()
    
    # HTML report
    html_report = generator.generate_html_report(analysis)
    with open("sample_analysis_report.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    print("   ✓ HTML report saved: sample_analysis_report.html")
    
    # PDF report
    pdf_bytes = generator.generate_pdf_report(analysis)
    with open("sample_analysis_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("   ✓ PDF report saved: sample_analysis_report.pdf")
    
    print("\n" + "=" * 60)
    print("Sample reports generated successfully!")
    print("\nGenerated files:")
    print("  - sample_analysis_report.html")
    print("  - sample_analysis_report.pdf")
    print("\nOpen these files in your browser/PDF viewer to see the reports.")


if __name__ == "__main__":
    main()
