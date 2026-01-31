"""
Property-based and unit tests for Report Generator.
Tests report generation, integrity, and export functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from decimal import Decimal
import re

from engines.report_generator import ReportGenerator
from models.schemas import (
    AnalysisResult, Signal, SignalType, IndicatorResults, OverallSentiment,
    SignalExplanation, MACDValues, BollingerBands, MovingAverages,
    StochasticValues, VolumeProfile, ATRValues, FibonacciLevels, Pattern,
    SentimentResults, SentimentClassification, TrendDirection,
    BacktestResult, BacktestParameters, BacktestTrade, BacktestMetrics,
    Portfolio, Holding
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def report_generator():
    """Create report generator instance."""
    return ReportGenerator()


@pytest.fixture
def sample_analysis_result():
    """Create sample analysis result for testing."""
    return AnalysisResult(
        id="test-analysis-123",
        coin="BTC",
        timeframe="1h",
        timestamp=datetime.utcnow(),
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
                Pattern(name="Bullish Flag", confidence=0.75, description="Upward continuation pattern")
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
            golden_death_cross_detected=None,
            rsi_divergence_detected=None
        ),
        explanation=SignalExplanation(
            signal=Signal(
                signal_type=SignalType.BUY,
                success_probability=72.5,
                timestamp=datetime.utcnow(),
                coin="BTC",
                timeframe="1h"
            ),
            technical_reasons=["RSI neutral", "MACD bullish crossover"],
            fundamental_reasons=["Positive sentiment on social media"],
            supporting_indicators=["MACD", "EMA", "VWAP"],
            conflicting_indicators=["Stochastic overbought"],
            risk_factors=["High volatility (ATR 3.1%)"]
        ),
        ai_report="BTC shows bullish momentum with positive technical and fundamental indicators.",
        actual_outcome=None,
        price_at_analysis=48000.0,
        price_after_period=None
    )


@pytest.fixture
def sample_backtest_result():
    """Create sample backtest result for testing."""
    return BacktestResult(
        id="test-backtest-123",
        coin="ETH",
        timeframe="4h",
        period=(datetime.utcnow() - timedelta(days=30), datetime.utcnow()),
        parameters=BacktestParameters(
            indicators=["RSI", "MACD", "EMA"],
            indicator_thresholds={"rsi_oversold": 30, "rsi_overbought": 70},
            use_fundamental=False,
            signal_threshold=60
        ),
        trades=[
            BacktestTrade(
                entry_date=datetime.utcnow() - timedelta(days=20),
                entry_price=3000,
                exit_date=datetime.utcnow() - timedelta(days=18),
                exit_price=3150,
                profit_loss=150,
                profit_loss_percent=5.0,
                signal_at_entry=Signal(
                    signal_type=SignalType.BUY,
                    success_probability=75,
                    timestamp=datetime.utcnow() - timedelta(days=20),
                    coin="ETH",
                    timeframe="4h"
                )
            )
        ],
        metrics=BacktestMetrics(
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            win_rate=70.0,
            total_profit_loss=500,
            total_profit_loss_percent=5.0,
            max_drawdown=200,
            max_drawdown_percent=2.0,
            average_trade_duration=timedelta(days=2),
            sharpe_ratio=1.5,
            profit_factor=2.3
        ),
        equity_curve=[
            (datetime.utcnow() - timedelta(days=30), 10000),
            (datetime.utcnow() - timedelta(days=15), 10250),
            (datetime.utcnow(), 10500)
        ]
    )


@pytest.fixture
def sample_portfolio():
    """Create sample portfolio for testing."""
    return Portfolio(
        holdings=[
            Holding(
                id="holding-1",
                coin="BTC",
                amount=Decimal("0.5"),
                purchase_price=Decimal("40000"),
                purchase_date=datetime.utcnow() - timedelta(days=30),
                current_price=Decimal("48000"),
                current_value=Decimal("24000"),
                profit_loss_percent=20.0,
                profit_loss_amount=Decimal("4000"),
                last_signal=None
            ),
            Holding(
                id="holding-2",
                coin="ETH",
                amount=Decimal("5"),
                purchase_price=Decimal("2500"),
                purchase_date=datetime.utcnow() - timedelta(days=20),
                current_price=Decimal("3000"),
                current_value=Decimal("15000"),
                profit_loss_percent=20.0,
                profit_loss_amount=Decimal("2500"),
                last_signal=None
            )
        ],
        total_value=Decimal("39000"),
        total_invested=Decimal("32500"),
        total_profit_loss=Decimal("6500"),
        total_profit_loss_percent=20.0
    )


# ============================================================================
# Property Test 21: Report Integrity
# ============================================================================

@given(
    coin=st.sampled_from(["BTC", "ETH", "ADA", "SOL", "DOGE"]),
    success_probability=st.floats(min_value=0, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_property_21_report_integrity(coin, success_probability):
    """
    Feature: crypto-analysis-system, Property 21: Rapor Bütünlüğü
    
    Herhangi bir analiz için, üretilen rapor tüm gerekli alanları içermelidir:
    coin adı, zaman aralığı, analiz tarihi, teknik indikatör sonuçları,
    temel analiz özeti, başarı ihtimali, sinyal, AI yorumu.
    
    Validates: Requirement 12.1, 12.2
    """
    # Create report generator
    report_generator = ReportGenerator()
    
    # Create analysis with given parameters
    analysis = AnalysisResult(
        id=f"test-{coin}-{int(success_probability)}",
        coin=coin,
        timeframe="1h",
        timestamp=datetime.utcnow(),
        technical_results=IndicatorResults(
            rsi=50.0,
            rsi_signal="neutral",
            macd=MACDValues(macd=0.0, signal=0.0, histogram=0.0),
            macd_signal="neutral",
            bollinger=BollingerBands(upper=100, middle=90, lower=80, bandwidth=20),
            bollinger_signal="neutral",
            moving_averages=MovingAverages(
                sma_20=90, sma_50=85, sma_200=80, ema_12=91, ema_26=88
            ),
            ma_signal="neutral",
            ema_50=85,
            ema_200=80,
            stochastic=StochasticValues(k=50, d=50),
            stochastic_signal="neutral",
            volume_profile=VolumeProfile(poc=90, vah=95, val=85, total_volume=100000),
            atr=ATRValues(atr=5, atr_percent=5.0, percentile=0.5),
            atr_stop_loss=85,
            atr_take_profit=95,
            vwap=90,
            vwap_signal="neutral",
            obv=100000,
            obv_signal="neutral",
            fibonacci_levels=FibonacciLevels(
                level_0=80, level_236=84, level_382=87,
                level_500=90, level_618=93, level_100=100
            ),
            patterns=[],
            support_levels=[80, 75, 70],
            resistance_levels=[100, 105, 110],
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
            timestamp=datetime.utcnow(),
            coin=coin,
            timeframe="1h"
        ),
        explanation=SignalExplanation(
            signal=Signal(
                signal_type=SignalType.NEUTRAL,
                success_probability=success_probability,
                timestamp=datetime.utcnow(),
                coin=coin,
                timeframe="1h"
            ),
            technical_reasons=["Neutral indicators"],
            fundamental_reasons=["Neutral sentiment"],
            supporting_indicators=[],
            conflicting_indicators=[],
            risk_factors=[]
        ),
        ai_report=f"Analysis for {coin} shows neutral conditions.",
        price_at_analysis=90.0
    )
    
    # Generate HTML report
    html_report = report_generator.generate_html_report(analysis)
    
    # Verify all required fields are present in the report
    assert coin in html_report, "Coin name must be in report"
    assert "1h" in html_report, "Timeframe must be in report"
    assert "Analiz Tarihi" in html_report or "timestamp" in html_report.lower(), \
        "Analysis date must be in report"
    
    # Technical indicators
    assert "RSI" in html_report or "rsi" in html_report.lower(), \
        "Technical indicators (RSI) must be in report"
    assert "MACD" in html_report or "macd" in html_report.lower(), \
        "Technical indicators (MACD) must be in report"
    
    # Fundamental analysis
    assert "Temel Analiz" in html_report or "fundamental" in html_report.lower() or \
           "Duygu" in html_report or "sentiment" in html_report.lower(), \
        "Fundamental analysis summary must be in report"
    
    # Success probability
    assert str(int(success_probability)) in html_report or \
           f"{success_probability:.1f}" in html_report, \
        "Success probability must be in report"
    
    # Signal
    assert "NEUTRAL" in html_report or "Nötr" in html_report, \
        "Signal must be in report"
    
    # AI report
    assert f"Analysis for {coin}" in html_report or "Yapay Zeka" in html_report, \
        "AI report must be in report"
    
    # Verify HTML structure
    assert "<html" in html_report.lower(), "Must be valid HTML"
    assert "</html>" in html_report.lower(), "Must be valid HTML"
    assert "<body" in html_report.lower(), "Must have body tag"
    assert "</body>" in html_report.lower(), "Must have closing body tag"


# ============================================================================
# Unit Tests for Report Generation
# ============================================================================

def test_generate_html_report(report_generator, sample_analysis_result):
    """Test HTML report generation for analysis."""
    html = report_generator.generate_html_report(sample_analysis_result)
    
    # Verify HTML structure
    assert html.startswith("<!DOCTYPE html>") or html.startswith("\n<!DOCTYPE html>")
    assert "<html" in html
    assert "</html>" in html
    
    # Verify content
    assert "BTC" in html
    assert "1h" in html
    assert "72.5" in html or "72" in html  # Success probability
    assert "BUY" in html or "Al" in html
    
    # Verify sections
    assert "Teknik Analiz" in html
    assert "Temel Analiz" in html
    assert "Sinyal Açıklaması" in html
    assert "Yapay Zeka Yorumu" in html


def test_generate_backtest_html_report(report_generator, sample_backtest_result):
    """Test HTML report generation for backtest."""
    html = report_generator.generate_backtest_html_report(sample_backtest_result)
    
    # Verify HTML structure
    assert "<html" in html
    assert "</html>" in html
    
    # Verify content
    assert "ETH" in html
    assert "4h" in html
    assert "70.0" in html or "70" in html  # Win rate
    assert "10" in html  # Total trades
    
    # Verify sections
    assert "Performans Metrikleri" in html or "Performance" in html
    assert "İşlem Geçmişi" in html or "Trade" in html


def test_generate_portfolio_html_report(report_generator, sample_portfolio):
    """Test HTML report generation for portfolio."""
    html = report_generator.generate_portfolio_html_report(sample_portfolio)
    
    # Verify HTML structure
    assert "<html" in html
    assert "</html>" in html
    
    # Verify content
    assert "BTC" in html
    assert "ETH" in html
    assert "39000" in html or "39,000" in html  # Total value
    
    # Verify sections
    assert "Portföy" in html
    assert "Holding" in html or "Coin" in html


def test_generate_pdf_report(report_generator, sample_analysis_result):
    """Test PDF report generation for analysis."""
    pdf_bytes = report_generator.generate_pdf_report(sample_analysis_result)
    
    # Verify PDF format
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')  # PDF magic number


def test_generate_backtest_pdf_report(report_generator, sample_backtest_result):
    """Test PDF report generation for backtest."""
    pdf_bytes = report_generator.generate_backtest_pdf_report(sample_backtest_result)
    
    # Verify PDF format
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')


def test_generate_portfolio_pdf_report(report_generator, sample_portfolio):
    """Test PDF report generation for portfolio."""
    pdf_bytes = report_generator.generate_portfolio_pdf_report(sample_portfolio)
    
    # Verify PDF format
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')


def test_report_with_chart_images(report_generator, sample_analysis_result):
    """Test report generation with embedded chart images."""
    # Mock chart images (base64 encoded)
    chart_images = {
        "Price Chart": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "RSI Chart": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }
    
    html = report_generator.generate_html_report(sample_analysis_result, chart_images)
    
    # Verify charts are embedded
    assert "Price Chart" in html
    assert "RSI Chart" in html
    assert "data:image/png;base64," in html
    assert chart_images["Price Chart"] in html


def test_signal_color_mapping(report_generator):
    """Test signal color mapping."""
    assert report_generator._get_signal_color(SignalType.STRONG_BUY) == '#00C853'
    assert report_generator._get_signal_color(SignalType.BUY) == '#4CAF50'
    assert report_generator._get_signal_color(SignalType.NEUTRAL) == '#FFC107'
    assert report_generator._get_signal_color(SignalType.SELL) == '#FF5722'
    assert report_generator._get_signal_color(SignalType.STRONG_SELL) == '#D32F2F'
    assert report_generator._get_signal_color(SignalType.UNCERTAIN) == '#9E9E9E'


def test_pdf_css_generation(report_generator):
    """Test PDF CSS generation."""
    css = report_generator._get_pdf_css()
    
    assert "@page" in css
    assert "font-family" in css
    assert "margin" in css
    assert "table" in css


def test_report_with_optional_fields(report_generator):
    """Test report generation with optional fields."""
    # Create analysis with optional fields
    analysis = AnalysisResult(
        id="test-optional",
        coin="BTC",
        timeframe="1h",
        timestamp=datetime.utcnow(),
        technical_results=IndicatorResults(
            rsi=65.5,
            rsi_signal="neutral",
            rsi_divergence="positive",  # Optional field
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
            golden_death_cross="golden_cross",  # Optional field
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
            patterns=[],
            support_levels=[46000, 45000],
            resistance_levels=[50000, 51000],
            confluence_score=0.72,
            ema_200_trend_filter="long_only"
        ),
        fundamental_results=OverallSentiment(
            overall_score=0.45,
            classification=SentimentClassification.POSITIVE,
            trend=TrendDirection.RISING,
            sources=[]
        ),
        signal=Signal(
            signal_type=SignalType.BUY,
            success_probability=72.5,
            timestamp=datetime.utcnow(),
            coin="BTC",
            timeframe="1h",
            stop_loss=46500,  # Optional field
            take_profit=51500,  # Optional field
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
            technical_reasons=["RSI neutral"],
            fundamental_reasons=["Positive sentiment"],
            supporting_indicators=["MACD"],
            conflicting_indicators=[],
            risk_factors=["High volatility"]
        ),
        ai_report="Test report",
        price_at_analysis=48000.0
    )
    
    html = report_generator.generate_html_report(analysis)
    
    # Verify optional fields are included
    assert "positive" in html.lower()  # RSI divergence
    assert "golden_cross" in html.lower()  # Golden cross
    assert "46500" in html  # Stop loss
    assert "51500" in html  # Take profit



# ============================================================================
# Property Test 22: Report Export
# ============================================================================

@given(
    coin=st.sampled_from(["BTC", "ETH", "ADA", "SOL", "DOGE"]),
    report_format=st.sampled_from(["html", "pdf"])
)
@settings(max_examples=100, deadline=None)
def test_property_22_report_export(coin, report_format):
    """
    Feature: crypto-analysis-system, Property 22: Rapor Dışa Aktarma
    
    Herhangi bir rapor için, PDF ve HTML formatlarında dışa aktarılabilmeli
    ve grafikler içermelidir.
    
    Validates: Requirement 12.3, 12.4
    """
    # Create report generator
    report_generator = ReportGenerator()
    
    # Create sample analysis
    analysis = AnalysisResult(
        id=f"test-export-{coin}",
        coin=coin,
        timeframe="1h",
        timestamp=datetime.utcnow(),
        technical_results=IndicatorResults(
            rsi=50.0,
            rsi_signal="neutral",
            macd=MACDValues(macd=0.0, signal=0.0, histogram=0.0),
            macd_signal="neutral",
            bollinger=BollingerBands(upper=100, middle=90, lower=80, bandwidth=20),
            bollinger_signal="neutral",
            moving_averages=MovingAverages(
                sma_20=90, sma_50=85, sma_200=80, ema_12=91, ema_26=88
            ),
            ma_signal="neutral",
            ema_50=85,
            ema_200=80,
            stochastic=StochasticValues(k=50, d=50),
            stochastic_signal="neutral",
            volume_profile=VolumeProfile(poc=90, vah=95, val=85, total_volume=100000),
            atr=ATRValues(atr=5, atr_percent=5.0, percentile=0.5),
            atr_stop_loss=85,
            atr_take_profit=95,
            vwap=90,
            vwap_signal="neutral",
            obv=100000,
            obv_signal="neutral",
            fibonacci_levels=FibonacciLevels(
                level_0=80, level_236=84, level_382=87,
                level_500=90, level_618=93, level_100=100
            ),
            patterns=[],
            support_levels=[80, 75, 70],
            resistance_levels=[100, 105, 110],
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
            timestamp=datetime.utcnow(),
            coin=coin,
            timeframe="1h"
        ),
        explanation=SignalExplanation(
            signal=Signal(
                signal_type=SignalType.NEUTRAL,
                success_probability=50.0,
                timestamp=datetime.utcnow(),
                coin=coin,
                timeframe="1h"
            ),
            technical_reasons=["Neutral indicators"],
            fundamental_reasons=["Neutral sentiment"],
            supporting_indicators=[],
            conflicting_indicators=[],
            risk_factors=[]
        ),
        ai_report=f"Analysis for {coin} shows neutral conditions.",
        price_at_analysis=90.0
    )
    
    # Mock chart images
    chart_images = {
        "Price Chart": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }
    
    if report_format == "html":
        # Test HTML export
        html_report = report_generator.generate_html_report(analysis, chart_images)
        
        # Verify HTML format
        assert isinstance(html_report, str), "HTML report must be a string"
        assert len(html_report) > 0, "HTML report must not be empty"
        assert "<html" in html_report.lower(), "Must be valid HTML"
        assert "</html>" in html_report.lower(), "Must have closing HTML tag"
        
        # Verify coin is in report
        assert coin in html_report, "Coin must be in HTML report"
        
        # Verify charts are included
        assert "data:image/png;base64," in html_report, "Charts must be embedded in HTML"
        assert chart_images["Price Chart"] in html_report, "Chart data must be in HTML"
        
    elif report_format == "pdf":
        # Test PDF export
        pdf_bytes = report_generator.generate_pdf_report(analysis, chart_images)
        
        # Verify PDF format
        assert isinstance(pdf_bytes, bytes), "PDF report must be bytes"
        assert len(pdf_bytes) > 0, "PDF report must not be empty"
        assert pdf_bytes.startswith(b'%PDF'), "Must be valid PDF format"
        
        # Verify PDF has content (size check)
        assert len(pdf_bytes) > 1000, "PDF must have substantial content"


@given(
    coin=st.sampled_from(["BTC", "ETH", "ADA"]),
    total_trades=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=50, deadline=None)
def test_property_22_backtest_report_export(coin, total_trades):
    """
    Test backtest report export in both HTML and PDF formats.
    Validates: Requirement 12.3, 12.4
    """
    report_generator = ReportGenerator()
    
    # Create sample backtest
    backtest = BacktestResult(
        id=f"test-backtest-{coin}",
        coin=coin,
        timeframe="4h",
        period=(datetime.utcnow() - timedelta(days=30), datetime.utcnow()),
        parameters=BacktestParameters(
            indicators=["RSI", "MACD"],
            indicator_thresholds={},
            use_fundamental=False,
            signal_threshold=60
        ),
        trades=[
            BacktestTrade(
                entry_date=datetime.utcnow() - timedelta(days=i*2),
                entry_price=100.0,
                exit_date=datetime.utcnow() - timedelta(days=i*2-1),
                exit_price=105.0,
                profit_loss=5.0,
                profit_loss_percent=5.0,
                signal_at_entry=Signal(
                    signal_type=SignalType.BUY,
                    success_probability=70,
                    timestamp=datetime.utcnow() - timedelta(days=i*2),
                    coin=coin,
                    timeframe="4h"
                )
            )
            for i in range(min(total_trades, 5))  # Limit to 5 trades for test
        ],
        metrics=BacktestMetrics(
            total_trades=total_trades,
            winning_trades=int(total_trades * 0.7),
            losing_trades=int(total_trades * 0.3),
            win_rate=70.0,
            total_profit_loss=500,
            total_profit_loss_percent=5.0,
            max_drawdown=200,
            max_drawdown_percent=2.0,
            average_trade_duration=timedelta(days=2),
            sharpe_ratio=1.5,
            profit_factor=2.3
        ),
        equity_curve=[
            (datetime.utcnow() - timedelta(days=30), 10000),
            (datetime.utcnow(), 10500)
        ]
    )
    
    # Test HTML export
    html_report = report_generator.generate_backtest_html_report(backtest)
    assert isinstance(html_report, str)
    assert len(html_report) > 0
    assert coin in html_report
    assert str(total_trades) in html_report
    
    # Test PDF export
    pdf_bytes = report_generator.generate_backtest_pdf_report(backtest)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')


@given(
    num_holdings=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50, deadline=None)
def test_property_22_portfolio_report_export(num_holdings):
    """
    Test portfolio report export in both HTML and PDF formats.
    Validates: Requirement 12.3, 12.4
    """
    report_generator = ReportGenerator()
    
    # Create sample portfolio
    holdings = []
    total_value = Decimal("0")
    total_invested = Decimal("0")
    
    for i in range(num_holdings):
        coin = ["BTC", "ETH", "ADA", "SOL", "DOGE"][i % 5]
        amount = Decimal(str(0.5 + i * 0.1))
        purchase_price = Decimal(str(1000 + i * 100))
        current_price = Decimal(str(1100 + i * 100))
        current_value = amount * current_price
        invested = amount * purchase_price
        
        holdings.append(Holding(
            id=f"holding-{i}",
            coin=coin,
            amount=amount,
            purchase_price=purchase_price,
            purchase_date=datetime.utcnow() - timedelta(days=30),
            current_price=current_price,
            current_value=current_value,
            profit_loss_percent=10.0,
            profit_loss_amount=current_value - invested,
            last_signal=None
        ))
        
        total_value += current_value
        total_invested += invested
    
    portfolio = Portfolio(
        holdings=holdings,
        total_value=total_value,
        total_invested=total_invested,
        total_profit_loss=total_value - total_invested,
        total_profit_loss_percent=float((total_value - total_invested) / total_invested * 100)
    )
    
    # Test HTML export
    html_report = report_generator.generate_portfolio_html_report(portfolio)
    assert isinstance(html_report, str)
    assert len(html_report) > 0
    assert "Portföy" in html_report
    
    # Test PDF export
    pdf_bytes = report_generator.generate_portfolio_pdf_report(portfolio)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')
