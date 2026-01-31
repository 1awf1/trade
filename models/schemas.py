"""
Pydantic models for request/response validation and serialization.
Includes: AnalysisResult, Signal, IndicatorResults, SentimentResults,
Portfolio, Holding, Alarm, BacktestResult
"""
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class SignalType(str, Enum):
    """Signal types for buy/sell recommendations."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    UNCERTAIN = "UNCERTAIN"


class SentimentClassification(str, Enum):
    """Sentiment classification categories."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TrendDirection(str, Enum):
    """Trend direction categories."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


class AlarmType(str, Enum):
    """Alarm types."""
    PRICE = "price"
    SIGNAL = "signal"
    SUCCESS_PROBABILITY = "success_probability"


class AlarmCondition(str, Enum):
    """Alarm condition operators."""
    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"


class TradeType(str, Enum):
    """Trade types."""
    BUY = "buy"
    SELL = "sell"


# ============================================================================
# Technical Analysis Models
# ============================================================================

class MACDValues(BaseModel):
    """MACD indicator values."""
    macd: float
    signal: float
    histogram: float


class BollingerBands(BaseModel):
    """Bollinger Bands values."""
    upper: float
    middle: float
    lower: float
    bandwidth: float


class MovingAverages(BaseModel):
    """Moving average values."""
    sma_20: float
    sma_50: float
    sma_200: float
    ema_12: float
    ema_26: float


class StochasticValues(BaseModel):
    """Stochastic Oscillator values."""
    k: float
    d: float


class VolumeProfile(BaseModel):
    """Volume profile data."""
    poc: float  # Point of Control
    vah: float  # Value Area High
    val: float  # Value Area Low
    total_volume: float


class ATRValues(BaseModel):
    """ATR (Average True Range) values."""
    atr: float
    atr_percent: float
    percentile: float  # ATR percentile (0-1)


class FibonacciLevels(BaseModel):
    """Fibonacci Retracement levels."""
    level_0: float  # 0%
    level_236: float  # 23.6%
    level_382: float  # 38.2%
    level_500: float  # 50%
    level_618: float  # 61.8%
    level_100: float  # 100%


class Pattern(BaseModel):
    """Chart pattern detection."""
    name: str
    confidence: float = Field(ge=0, le=1)
    description: str


class IndicatorResults(BaseModel):
    """Complete technical indicator results."""
    # RSI
    rsi: float = Field(ge=0, le=100)
    rsi_signal: str  # "oversold", "neutral", "overbought"
    rsi_divergence: Optional[str] = None  # "positive", "negative", None
    
    # MACD
    macd: MACDValues
    macd_signal: str  # "bullish", "bearish", "neutral"
    
    # Bollinger Bands
    bollinger: BollingerBands
    bollinger_signal: str
    
    # Moving Averages
    moving_averages: MovingAverages
    ma_signal: str
    ema_50: float
    ema_200: float
    golden_death_cross: Optional[str] = None  # "golden_cross", "death_cross", None
    
    # Stochastic
    stochastic: StochasticValues
    stochastic_signal: str
    
    # Volume
    volume_profile: VolumeProfile
    
    # ATR
    atr: ATRValues
    atr_stop_loss: float
    atr_take_profit: float
    
    # VWAP
    vwap: float
    vwap_signal: str  # "above", "below", "neutral"
    
    # OBV
    obv: float
    obv_signal: str  # "volume_supported", "volume_divergence", "neutral"
    
    # Fibonacci
    fibonacci_levels: FibonacciLevels
    
    # Patterns and Levels
    patterns: List[Pattern]
    support_levels: List[float]
    resistance_levels: List[float]
    
    # Confluence
    confluence_score: float = Field(ge=0, le=1)
    ema_200_trend_filter: str  # "long_only", "short_only", "neutral"


# ============================================================================
# Fundamental Analysis Models
# ============================================================================

class SentimentResults(BaseModel):
    """Sentiment analysis results from a single source."""
    source: str  # "twitter", "reddit", "news", "telegram"
    sentiment_score: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    sample_size: int = Field(ge=0)
    timestamp: datetime


class OverallSentiment(BaseModel):
    """Aggregated sentiment analysis results."""
    overall_score: float = Field(ge=-1, le=1)
    classification: SentimentClassification
    trend: TrendDirection
    sources: List[SentimentResults]


# ============================================================================
# Signal Models
# ============================================================================

class Signal(BaseModel):
    """Trading signal with success probability."""
    signal_type: SignalType
    success_probability: float = Field(ge=0, le=100)
    timestamp: datetime
    coin: str
    timeframe: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    ema_200_filter_applied: bool = False
    golden_death_cross_detected: Optional[str] = None
    rsi_divergence_detected: Optional[str] = None


class SignalExplanation(BaseModel):
    """Detailed explanation of signal generation."""
    signal: Signal
    technical_reasons: List[str]
    fundamental_reasons: List[str]
    supporting_indicators: List[str]
    conflicting_indicators: List[str]
    risk_factors: List[str]


# ============================================================================
# Analysis Models
# ============================================================================

class AnalysisResult(BaseModel):
    """Complete analysis result."""
    id: str
    coin: str
    timeframe: str
    timestamp: datetime
    technical_results: IndicatorResults
    fundamental_results: OverallSentiment
    signal: Signal
    explanation: SignalExplanation
    ai_report: str
    actual_outcome: Optional[str] = None  # "correct", "incorrect", None
    price_at_analysis: float
    price_after_period: Optional[float] = None


class AnalysisSummary(BaseModel):
    """Summary of analysis for listing."""
    id: str
    coin: str
    timeframe: str
    timestamp: datetime
    signal_type: SignalType
    success_probability: float
    price_at_analysis: float


class ComparisonReport(BaseModel):
    """Comparison report for multiple analyses."""
    analyses: List[AnalysisResult]
    success_probability_changes: List[float]
    signal_changes: List[str]
    indicator_differences: Dict[str, List[float]]
    sentiment_changes: List[float]


class AccuracyStats(BaseModel):
    """User's prediction accuracy statistics."""
    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
    accuracy_rate: float = Field(ge=0, le=100)
    by_signal_type: Dict[str, Dict[str, int]]


# ============================================================================
# Portfolio Models
# ============================================================================

class Holding(BaseModel):
    """Individual portfolio holding."""
    id: str
    coin: str
    amount: Decimal
    purchase_price: Decimal
    purchase_date: datetime
    current_price: Decimal
    current_value: Decimal
    profit_loss_percent: float
    profit_loss_amount: Decimal
    last_signal: Optional[Signal] = None


class Portfolio(BaseModel):
    """Complete portfolio with all holdings."""
    holdings: List[Holding]
    total_value: Decimal
    total_invested: Decimal
    total_profit_loss: Decimal
    total_profit_loss_percent: float


class TradeHistory(BaseModel):
    """Trade history record."""
    id: str
    coin: str
    type: TradeType
    amount: Decimal
    price: Decimal
    date: datetime
    profit_loss: Optional[Decimal] = None


class PerformanceSnapshot(BaseModel):
    """Portfolio performance at a point in time."""
    timestamp: datetime
    total_value: Decimal
    profit_loss_percent: float


class ProfitLoss(BaseModel):
    """Profit/loss calculation."""
    total_invested: Decimal
    current_value: Decimal
    profit_loss_amount: Decimal
    profit_loss_percent: float


# ============================================================================
# Alarm Models
# ============================================================================

class AlarmConfig(BaseModel):
    """Alarm configuration."""
    coin: str
    type: AlarmType
    condition: AlarmCondition
    threshold: float
    notification_channels: List[str]  # ["email", "web_push"]
    auto_disable: bool = False
    active: bool = True


class Alarm(BaseModel):
    """Alarm with metadata."""
    id: str
    config: AlarmConfig
    created_at: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class AlarmHistoryRecord(BaseModel):
    """Alarm history record."""
    alarm_id: str
    triggered_at: datetime
    trigger_value: float
    notification_sent: bool


class TriggeredAlarm(BaseModel):
    """Alarm that has been triggered."""
    alarm: Alarm
    trigger_data: Dict


# ============================================================================
# Backtest Models
# ============================================================================

class BacktestParameters(BaseModel):
    """Backtesting parameters."""
    indicators: List[str]
    indicator_thresholds: Dict[str, float]
    use_fundamental: bool = False
    signal_threshold: float = Field(ge=0, le=100, default=60)


class BacktestTrade(BaseModel):
    """Individual trade in backtest."""
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    profit_loss: float
    profit_loss_percent: float
    signal_at_entry: Signal


class BacktestMetrics(BaseModel):
    """Backtesting performance metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float = Field(ge=0, le=100)
    total_profit_loss: float
    total_profit_loss_percent: float
    max_drawdown: float
    max_drawdown_percent: float
    average_trade_duration: timedelta
    sharpe_ratio: float
    profit_factor: float


class BacktestResult(BaseModel):
    """Complete backtest result."""
    id: str
    coin: str
    timeframe: str
    period: Tuple[datetime, datetime]
    parameters: BacktestParameters
    trades: List[BacktestTrade]
    metrics: BacktestMetrics
    equity_curve: List[Tuple[datetime, float]]


class BacktestComparison(BaseModel):
    """Comparison of multiple backtest results."""
    backtests: List[BacktestResult]
    metric_comparisons: Dict[str, List[float]]


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to start a new analysis."""
    coin: str = Field(min_length=1, max_length=20)
    timeframe: str
    
    @validator('coin')
    def validate_coin(cls, v):
        """Validate coin symbol."""
        return v.upper().strip()
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe."""
        valid_timeframes = ['15m', '1h', '4h', '8h', '12h', '24h', '1w', '15d', '1M']
        if v not in valid_timeframes:
            raise ValueError(f'Timeframe must be one of {valid_timeframes}')
        return v


class PortfolioAddRequest(BaseModel):
    """Request to add coin to portfolio."""
    coin: str = Field(min_length=1, max_length=20)
    amount: Decimal = Field(gt=0)
    purchase_price: Decimal = Field(gt=0)
    purchase_date: datetime
    
    @validator('coin')
    def validate_coin(cls, v):
        """Validate coin symbol."""
        return v.upper().strip()


class PortfolioRemoveRequest(BaseModel):
    """Request to remove coin from portfolio."""
    holding_id: str
    sale_price: Decimal = Field(gt=0)
    sale_date: datetime


class AlarmCreateRequest(BaseModel):
    """Request to create an alarm."""
    config: AlarmConfig


class BacktestRequest(BaseModel):
    """Request to start a backtest."""
    coin: str = Field(min_length=1, max_length=20)
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(gt=0, default=10000)
    parameters: BacktestParameters
    
    @validator('coin')
    def validate_coin(cls, v):
        """Validate coin symbol."""
        return v.upper().strip()
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        """Validate that end_date is after start_date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


# ============================================================================
# Error Response Model
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error_code: str
    message: str
    details: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
