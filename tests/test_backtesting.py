"""
Property-based and unit tests for Backtesting Engine.
Tests backtesting initialization, trade simulation, and metrics calculation.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from engines.backtesting import BacktestingEngine
from models.schemas import (
    BacktestParameters, BacktestTrade, Signal, SignalType
)
import asyncio


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def backtesting_engine():
    """Create a backtesting engine instance."""
    return BacktestingEngine()


@pytest.fixture
def sample_parameters():
    """Create sample backtesting parameters."""
    return BacktestParameters(
        indicators=["RSI", "MACD", "Bollinger Bands"],
        indicator_thresholds={"RSI": 30, "MACD": 0},
        use_fundamental=False,
        signal_threshold=60.0
    )


@pytest.fixture
def sample_signal():
    """Create a sample signal."""
    return Signal(
        signal_type=SignalType.BUY,
        success_probability=65.0,
        timestamp=datetime.utcnow(),
        coin="BTC",
        timeframe="1h",
        stop_loss=48000.0,
        take_profit=53000.0,
        ema_200_filter_applied=False,
        golden_death_cross_detected=None,
        rsi_divergence_detected=None
    )


# ============================================================================
# Property-Based Tests
# ============================================================================

@given(
    coin=st.sampled_from(["BTC", "ETH", "BNB", "ADA", "SOL"]),
    timeframe=st.sampled_from(["1h", "4h", "24h"])
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_51_backtesting_initialization(
    backtesting_engine,
    sample_parameters,
    coin,
    timeframe
):
    """
    Feature: crypto-analysis-system, Property 51: Backtesting Başlatma
    
    Herhangi bir geçerli coin ve zaman aralığı için, backtesting başlatılabilmelidir.
    
    **Validates: Gereksinim 19.1**
    """
    # Create valid date range based on timeframe
    # For 24h timeframe, need at least 50 days for 50 candles
    # For 4h timeframe, need at least 10 days for 60 candles
    # For 1h timeframe, need at least 3 days for 72 candles
    end_date = datetime.utcnow()
    
    if timeframe == "24h":
        days = 60  # 60 candles
    elif timeframe == "4h":
        days = 15  # 90 candles
    else:  # 1h
        days = 5  # 120 candles
    
    start_date = end_date - timedelta(days=days)
    initial_capital = 10000.0
    
    # Start backtest
    backtest_id = asyncio.run(
        backtesting_engine.start_backtest(
            coin=coin,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            parameters=sample_parameters
        )
    )
    
    # Verify backtest ID is generated
    assert backtest_id is not None
    assert isinstance(backtest_id, str)
    assert len(backtest_id) > 0
    
    # Verify it's a valid UUID format
    import uuid
    try:
        uuid.UUID(backtest_id)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    
    assert is_valid_uuid, f"Backtest ID should be a valid UUID, got: {backtest_id}"


@given(
    initial_capital=st.floats(min_value=1000, max_value=100000),
    num_trades=st.integers(min_value=0, max_value=50)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_55_backtesting_metrics_integrity(
    backtesting_engine,
    sample_signal,
    initial_capital,
    num_trades
):
    """
    Feature: crypto-analysis-system, Property 55: Backtesting Metrik Bütünlüğü
    
    Herhangi bir tamamlanan backtesting için, tüm gerekli metrikler hesaplanmalıdır:
    toplam kar/zarar yüzdesi, kazanan/kaybeden işlem sayısı, başarı oranı,
    maksimum düşüş, ortalama işlem süresi.
    
    **Validates: Gereksinim 19.6**
    """
    # Generate sample trades
    trades = []
    current_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(num_trades):
        entry_date = current_date + timedelta(hours=i * 24)
        exit_date = entry_date + timedelta(hours=12)
        
        # Randomize profit/loss
        entry_price = 50000.0
        # Some trades win, some lose
        if i % 3 == 0:
            exit_price = entry_price * 1.02  # 2% profit
        else:
            exit_price = entry_price * 0.98  # 2% loss
        
        profit_loss = initial_capital * ((exit_price - entry_price) / entry_price)
        profit_loss_percent = ((exit_price - entry_price) / entry_price) * 100
        
        trade = BacktestTrade(
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=exit_date,
            exit_price=exit_price,
            profit_loss=profit_loss,
            profit_loss_percent=profit_loss_percent,
            signal_at_entry=sample_signal
        )
        trades.append(trade)
    
    # Generate equity curve
    equity_curve = []
    equity = initial_capital
    for i, trade in enumerate(trades):
        equity += trade.profit_loss
        equity_curve.append((trade.exit_date, equity))
    
    # Calculate metrics
    metrics = backtesting_engine.calculate_metrics(
        trades, initial_capital, equity_curve
    )
    
    # Verify all required metrics are present and valid
    assert metrics is not None
    
    # Total trades
    assert metrics.total_trades == num_trades
    assert metrics.total_trades >= 0
    
    # Winning and losing trades
    assert metrics.winning_trades >= 0
    assert metrics.losing_trades >= 0
    assert metrics.winning_trades + metrics.losing_trades == num_trades
    
    # Win rate
    assert 0.0 <= metrics.win_rate <= 100.0
    if num_trades > 0:
        expected_win_rate = (metrics.winning_trades / num_trades) * 100
        assert abs(metrics.win_rate - expected_win_rate) < 0.01
    
    # Total profit/loss
    assert isinstance(metrics.total_profit_loss, float)
    assert isinstance(metrics.total_profit_loss_percent, float)
    
    # Max drawdown
    assert metrics.max_drawdown >= 0.0
    assert metrics.max_drawdown_percent >= 0.0
    
    # Average trade duration
    assert isinstance(metrics.average_trade_duration, timedelta)
    if num_trades > 0:
        assert metrics.average_trade_duration >= timedelta(0)
    
    # Sharpe ratio
    assert isinstance(metrics.sharpe_ratio, float)
    
    # Profit factor
    assert isinstance(metrics.profit_factor, float)
    assert metrics.profit_factor >= 0.0


# ============================================================================
# Unit Tests
# ============================================================================

def test_backtest_initialization_invalid_dates(backtesting_engine, sample_parameters):
    """Test that backtest initialization fails with invalid dates."""
    coin = "BTC"
    timeframe = "1h"
    start_date = datetime.utcnow()
    end_date = start_date - timedelta(days=1)  # End before start
    initial_capital = 10000.0
    
    with pytest.raises(ValueError, match="End date must be after start date"):
        asyncio.run(
            backtesting_engine.start_backtest(
                coin=coin,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                parameters=sample_parameters
            )
        )


def test_backtest_initialization_invalid_timeframe(backtesting_engine, sample_parameters):
    """Test that backtest initialization fails with invalid timeframe."""
    coin = "BTC"
    timeframe = "invalid"
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    initial_capital = 10000.0
    
    with pytest.raises(ValueError, match="Invalid timeframe"):
        asyncio.run(
            backtesting_engine.start_backtest(
                coin=coin,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                parameters=sample_parameters
            )
        )


def test_backtest_initialization_insufficient_period(backtesting_engine, sample_parameters):
    """Test that backtest initialization fails with too short period."""
    coin = "BTC"
    timeframe = "24h"
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)  # Too short
    initial_capital = 10000.0
    
    with pytest.raises(ValueError, match="Insufficient data points"):
        asyncio.run(
            backtesting_engine.start_backtest(
                coin=coin,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                parameters=sample_parameters
            )
        )


def test_calculate_metrics_no_trades(backtesting_engine):
    """Test metrics calculation with no trades."""
    trades = []
    initial_capital = 10000.0
    equity_curve = [(datetime.utcnow(), initial_capital)]
    
    metrics = backtesting_engine.calculate_metrics(trades, initial_capital, equity_curve)
    
    assert metrics.total_trades == 0
    assert metrics.winning_trades == 0
    assert metrics.losing_trades == 0
    assert metrics.win_rate == 0.0
    assert metrics.total_profit_loss == 0.0
    assert metrics.total_profit_loss_percent == 0.0


def test_calculate_metrics_all_winning_trades(backtesting_engine, sample_signal):
    """Test metrics calculation with all winning trades."""
    initial_capital = 10000.0
    trades = []
    
    # Create 5 winning trades
    for i in range(5):
        entry_date = datetime.utcnow() - timedelta(days=5-i)
        exit_date = entry_date + timedelta(hours=12)
        
        trade = BacktestTrade(
            entry_date=entry_date,
            entry_price=50000.0,
            exit_date=exit_date,
            exit_price=51000.0,  # 2% profit
            profit_loss=200.0,
            profit_loss_percent=2.0,
            signal_at_entry=sample_signal
        )
        trades.append(trade)
    
    equity_curve = [(datetime.utcnow(), initial_capital + 1000)]
    
    metrics = backtesting_engine.calculate_metrics(trades, initial_capital, equity_curve)
    
    assert metrics.total_trades == 5
    assert metrics.winning_trades == 5
    assert metrics.losing_trades == 0
    assert metrics.win_rate == 100.0
    assert metrics.total_profit_loss == 1000.0


def test_calculate_metrics_mixed_trades(backtesting_engine, sample_signal):
    """Test metrics calculation with mixed winning and losing trades."""
    initial_capital = 10000.0
    trades = []
    
    # Create 3 winning and 2 losing trades
    for i in range(5):
        entry_date = datetime.utcnow() - timedelta(days=5-i)
        exit_date = entry_date + timedelta(hours=12)
        
        if i < 3:
            # Winning trade
            profit_loss = 200.0
            profit_loss_percent = 2.0
            exit_price = 51000.0
        else:
            # Losing trade
            profit_loss = -100.0
            profit_loss_percent = -1.0
            exit_price = 49500.0
        
        trade = BacktestTrade(
            entry_date=entry_date,
            entry_price=50000.0,
            exit_date=exit_date,
            exit_price=exit_price,
            profit_loss=profit_loss,
            profit_loss_percent=profit_loss_percent,
            signal_at_entry=sample_signal
        )
        trades.append(trade)
    
    equity_curve = [(datetime.utcnow(), initial_capital + 400)]
    
    metrics = backtesting_engine.calculate_metrics(trades, initial_capital, equity_curve)
    
    assert metrics.total_trades == 5
    assert metrics.winning_trades == 3
    assert metrics.losing_trades == 2
    assert metrics.win_rate == 60.0
    assert metrics.total_profit_loss == 400.0


def test_max_drawdown_calculation(backtesting_engine):
    """Test maximum drawdown calculation."""
    # Create equity curve with drawdown
    equity_curve = [
        (datetime.utcnow() - timedelta(days=5), 10000),
        (datetime.utcnow() - timedelta(days=4), 11000),  # Peak
        (datetime.utcnow() - timedelta(days=3), 10500),
        (datetime.utcnow() - timedelta(days=2), 9500),   # Drawdown of 1500
        (datetime.utcnow() - timedelta(days=1), 10000),
        (datetime.utcnow(), 10500)
    ]
    
    max_dd, max_dd_pct = backtesting_engine._calculate_max_drawdown(equity_curve)
    
    assert max_dd == 1500.0
    assert abs(max_dd_pct - 13.636) < 0.01  # (1500/11000)*100


def test_profit_factor_calculation(backtesting_engine, sample_signal):
    """Test profit factor calculation."""
    trades = [
        BacktestTrade(
            entry_date=datetime.utcnow() - timedelta(days=3),
            entry_price=50000.0,
            exit_date=datetime.utcnow() - timedelta(days=2),
            exit_price=51000.0,
            profit_loss=1000.0,
            profit_loss_percent=2.0,
            signal_at_entry=sample_signal
        ),
        BacktestTrade(
            entry_date=datetime.utcnow() - timedelta(days=2),
            entry_price=51000.0,
            exit_date=datetime.utcnow() - timedelta(days=1),
            exit_price=50500.0,
            profit_loss=-500.0,
            profit_loss_percent=-1.0,
            signal_at_entry=sample_signal
        )
    ]
    
    profit_factor = backtesting_engine._calculate_profit_factor(trades)
    
    # Profit factor = gross profit / gross loss = 1000 / 500 = 2.0
    assert profit_factor == 2.0


def test_generate_backtest_report(backtesting_engine, sample_parameters, sample_signal):
    """Test backtest report generation."""
    from models.schemas import BacktestResult, BacktestMetrics
    
    # Create sample result
    result = BacktestResult(
        id="test-123",
        coin="BTC",
        timeframe="1h",
        period=(datetime.utcnow() - timedelta(days=30), datetime.utcnow()),
        parameters=sample_parameters,
        trades=[
            BacktestTrade(
                entry_date=datetime.utcnow() - timedelta(days=2),
                entry_price=50000.0,
                exit_date=datetime.utcnow() - timedelta(days=1),
                exit_price=51000.0,
                profit_loss=200.0,
                profit_loss_percent=2.0,
                signal_at_entry=sample_signal
            )
        ],
        metrics=BacktestMetrics(
            total_trades=1,
            winning_trades=1,
            losing_trades=0,
            win_rate=100.0,
            total_profit_loss=200.0,
            total_profit_loss_percent=2.0,
            max_drawdown=0.0,
            max_drawdown_percent=0.0,
            average_trade_duration=timedelta(days=1),
            sharpe_ratio=1.5,
            profit_factor=2.0
        ),
        equity_curve=[(datetime.utcnow(), 10200.0)]
    )
    
    report = backtesting_engine.generate_backtest_report(result)
    
    # Verify report structure
    assert report is not None
    assert 'id' in report
    assert 'coin' in report
    assert 'timeframe' in report
    assert 'period' in report
    assert 'parameters' in report
    assert 'metrics' in report
    assert 'trades' in report
    assert 'equity_curve' in report
    
    # Verify content
    assert report['id'] == "test-123"
    assert report['coin'] == "BTC"
    assert report['timeframe'] == "1h"
    assert len(report['trades']) == 1
    assert len(report['equity_curve']) == 1
