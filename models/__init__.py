"""
Data models module.
Contains Pydantic models and database schemas.
"""

# Database models
from models.database import (
    Base,
    User,
    Analysis,
    PortfolioHolding,
    TradeHistory,
    Alarm,
    AlarmHistory,
    Backtest
)

# Pydantic schemas
from models.schemas import (
    # Enums
    SignalType,
    SentimentClassification,
    TrendDirection,
    AlarmType,
    AlarmCondition,
    TradeType,
    
    # Technical Analysis
    MACDValues,
    BollingerBands,
    MovingAverages,
    StochasticValues,
    VolumeProfile,
    ATRValues,
    FibonacciLevels,
    Pattern,
    IndicatorResults,
    
    # Fundamental Analysis
    SentimentResults,
    OverallSentiment,
    
    # Signals
    Signal,
    SignalExplanation,
    
    # Analysis
    AnalysisResult,
    AnalysisSummary,
    ComparisonReport,
    AccuracyStats,
    
    # Portfolio
    Holding,
    Portfolio,
    TradeHistory as TradeHistorySchema,
    PerformanceSnapshot,
    ProfitLoss,
    
    # Alarms
    AlarmConfig,
    Alarm as AlarmSchema,
    AlarmHistoryRecord,
    TriggeredAlarm,
    
    # Backtesting
    BacktestParameters,
    BacktestTrade,
    BacktestMetrics,
    BacktestResult,
    BacktestComparison,
    
    # Requests/Responses
    AnalysisRequest,
    PortfolioAddRequest,
    PortfolioRemoveRequest,
    AlarmCreateRequest,
    BacktestRequest,
    ErrorResponse
)

__all__ = [
    # Database models
    "Base",
    "User",
    "Analysis",
    "PortfolioHolding",
    "TradeHistory",
    "Alarm",
    "AlarmHistory",
    "Backtest",
    
    # Enums
    "SignalType",
    "SentimentClassification",
    "TrendDirection",
    "AlarmType",
    "AlarmCondition",
    "TradeType",
    
    # Technical Analysis
    "MACDValues",
    "BollingerBands",
    "MovingAverages",
    "StochasticValues",
    "VolumeProfile",
    "ATRValues",
    "FibonacciLevels",
    "Pattern",
    "IndicatorResults",
    
    # Fundamental Analysis
    "SentimentResults",
    "OverallSentiment",
    
    # Signals
    "Signal",
    "SignalExplanation",
    
    # Analysis
    "AnalysisResult",
    "AnalysisSummary",
    "ComparisonReport",
    "AccuracyStats",
    
    # Portfolio
    "Holding",
    "Portfolio",
    "TradeHistorySchema",
    "PerformanceSnapshot",
    "ProfitLoss",
    
    # Alarms
    "AlarmConfig",
    "AlarmSchema",
    "AlarmHistoryRecord",
    "TriggeredAlarm",
    
    # Backtesting
    "BacktestParameters",
    "BacktestTrade",
    "BacktestMetrics",
    "BacktestResult",
    "BacktestComparison",
    
    # Requests/Responses
    "AnalysisRequest",
    "PortfolioAddRequest",
    "PortfolioRemoveRequest",
    "AlarmCreateRequest",
    "BacktestRequest",
    "ErrorResponse"
]
