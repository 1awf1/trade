"""
Custom exception classes and error handling utilities.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for the application."""
    
    # API Errors
    API_UNAVAILABLE = "API_UNAVAILABLE"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_TIMEOUT = "API_TIMEOUT"
    API_INVALID_RESPONSE = "API_INVALID_RESPONSE"
    
    # Input Validation Errors
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_COIN = "INVALID_COIN"
    INVALID_TIMEFRAME = "INVALID_TIMEFRAME"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    
    # Analysis Errors
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    TECHNICAL_ANALYSIS_FAILED = "TECHNICAL_ANALYSIS_FAILED"
    FUNDAMENTAL_ANALYSIS_FAILED = "FUNDAMENTAL_ANALYSIS_FAILED"
    SIGNAL_GENERATION_FAILED = "SIGNAL_GENERATION_FAILED"
    AI_INTERPRETATION_FAILED = "AI_INTERPRETATION_FAILED"
    
    # Data Errors
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    
    # Database Errors
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    
    # Cache Errors
    CACHE_ERROR = "CACHE_ERROR"
    CACHE_CONNECTION_ERROR = "CACHE_CONNECTION_ERROR"
    
    # Portfolio Errors
    PORTFOLIO_NOT_FOUND = "PORTFOLIO_NOT_FOUND"
    HOLDING_NOT_FOUND = "HOLDING_NOT_FOUND"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    
    # Alarm Errors
    ALARM_NOT_FOUND = "ALARM_NOT_FOUND"
    ALARM_CREATION_FAILED = "ALARM_CREATION_FAILED"
    NOTIFICATION_FAILED = "NOTIFICATION_FAILED"
    
    # Backtesting Errors
    BACKTEST_FAILED = "BACKTEST_FAILED"
    BACKTEST_NOT_FOUND = "BACKTEST_NOT_FOUND"
    
    # Performance Errors
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    
    # Security Errors
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # General Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


@dataclass
class ErrorResponse:
    """Standardized error response format."""
    
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CryptoAnalysisException(Exception):
    """Base exception for all application-specific exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def to_error_response(self, request_id: Optional[str] = None) -> ErrorResponse:
        """Convert exception to error response."""
        return ErrorResponse(
            error_code=self.error_code.value,
            message=self.message,
            details=self.details,
            request_id=request_id
        )


# API Exceptions
class APIException(CryptoAnalysisException):
    """Exception for external API errors."""
    
    def __init__(self, message: str, api_name: str, **kwargs):
        details = kwargs.get('details', {})
        details['api_name'] = api_name
        kwargs['details'] = details
        kwargs.setdefault('error_code', ErrorCode.API_UNAVAILABLE)
        super().__init__(message, **kwargs)


class APIRateLimitException(APIException):
    """Exception for API rate limit errors."""
    
    def __init__(self, api_name: str, retry_after: Optional[int] = None, **kwargs):
        message = f"Rate limit exceeded for {api_name}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        details = kwargs.get('details', {})
        details['retry_after'] = retry_after
        kwargs['details'] = details
        kwargs['error_code'] = ErrorCode.API_RATE_LIMIT
        super().__init__(message, api_name, **kwargs)


class APITimeoutException(APIException):
    """Exception for API timeout errors."""
    
    def __init__(self, api_name: str, timeout: float, **kwargs):
        message = f"Request to {api_name} timed out after {timeout} seconds"
        kwargs['error_code'] = ErrorCode.API_TIMEOUT
        super().__init__(message, api_name, **kwargs)


# Validation Exceptions
class ValidationException(CryptoAnalysisException):
    """Exception for input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        kwargs['details'] = details
        kwargs.setdefault('error_code', ErrorCode.INVALID_INPUT)
        super().__init__(message, **kwargs)


class InvalidCoinException(ValidationException):
    """Exception for invalid coin symbol."""
    
    def __init__(self, coin: str, **kwargs):
        message = f"Invalid or unsupported coin: {coin}"
        kwargs['error_code'] = ErrorCode.INVALID_COIN
        kwargs['details'] = {'coin': coin}
        super().__init__(message, field='coin', **kwargs)


class InvalidTimeframeException(ValidationException):
    """Exception for invalid timeframe."""
    
    def __init__(self, timeframe: str, **kwargs):
        message = f"Invalid timeframe: {timeframe}"
        kwargs['error_code'] = ErrorCode.INVALID_TIMEFRAME
        kwargs['details'] = {'timeframe': timeframe}
        super().__init__(message, field='timeframe', **kwargs)


# Analysis Exceptions
class AnalysisException(CryptoAnalysisException):
    """Exception for analysis errors."""
    
    def __init__(self, message: str, analysis_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if analysis_type:
            details['analysis_type'] = analysis_type
        kwargs['details'] = details
        kwargs.setdefault('error_code', ErrorCode.ANALYSIS_FAILED)
        super().__init__(message, **kwargs)


class TechnicalAnalysisException(AnalysisException):
    """Exception for technical analysis errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs['error_code'] = ErrorCode.TECHNICAL_ANALYSIS_FAILED
        super().__init__(message, analysis_type='technical', **kwargs)


class FundamentalAnalysisException(AnalysisException):
    """Exception for fundamental analysis errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs['error_code'] = ErrorCode.FUNDAMENTAL_ANALYSIS_FAILED
        super().__init__(message, analysis_type='fundamental', **kwargs)


class SignalGenerationException(AnalysisException):
    """Exception for signal generation errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs['error_code'] = ErrorCode.SIGNAL_GENERATION_FAILED
        super().__init__(message, analysis_type='signal_generation', **kwargs)


class AIInterpretationException(AnalysisException):
    """Exception for AI interpretation errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs['error_code'] = ErrorCode.AI_INTERPRETATION_FAILED
        super().__init__(message, analysis_type='ai_interpretation', **kwargs)


# Data Exceptions
class DataException(CryptoAnalysisException):
    """Exception for data-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', ErrorCode.DATA_NOT_FOUND)
        super().__init__(message, **kwargs)


class InsufficientDataException(DataException):
    """Exception for insufficient data errors."""
    
    def __init__(self, message: str, required: Optional[int] = None, available: Optional[int] = None, **kwargs):
        details = kwargs.get('details', {})
        if required is not None:
            details['required'] = required
        if available is not None:
            details['available'] = available
        kwargs['details'] = details
        kwargs['error_code'] = ErrorCode.INSUFFICIENT_DATA
        super().__init__(message, **kwargs)


# Database Exceptions
class DatabaseException(CryptoAnalysisException):
    """Exception for database errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', ErrorCode.DATABASE_ERROR)
        super().__init__(message, **kwargs)


# Cache Exceptions
class CacheException(CryptoAnalysisException):
    """Exception for cache errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', ErrorCode.CACHE_ERROR)
        super().__init__(message, **kwargs)


# Portfolio Exceptions
class PortfolioException(CryptoAnalysisException):
    """Exception for portfolio-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', ErrorCode.PORTFOLIO_NOT_FOUND)
        super().__init__(message, **kwargs)


class HoldingNotFoundException(PortfolioException):
    """Exception for holding not found errors."""
    
    def __init__(self, holding_id: str, **kwargs):
        message = f"Holding not found: {holding_id}"
        kwargs['error_code'] = ErrorCode.HOLDING_NOT_FOUND
        kwargs['details'] = {'holding_id': holding_id}
        super().__init__(message, **kwargs)


# Alarm Exceptions
class AlarmException(CryptoAnalysisException):
    """Exception for alarm-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', ErrorCode.ALARM_NOT_FOUND)
        super().__init__(message, **kwargs)


class NotificationException(AlarmException):
    """Exception for notification errors."""
    
    def __init__(self, message: str, channel: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if channel:
            details['channel'] = channel
        kwargs['details'] = details
        kwargs['error_code'] = ErrorCode.NOTIFICATION_FAILED
        super().__init__(message, **kwargs)


# Backtesting Exceptions
class BacktestException(CryptoAnalysisException):
    """Exception for backtesting errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', ErrorCode.BACKTEST_FAILED)
        super().__init__(message, **kwargs)


# Performance Exceptions
class RateLimitException(CryptoAnalysisException):
    """Exception for rate limit errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        details = kwargs.get('details', {})
        if retry_after:
            details['retry_after'] = retry_after
        kwargs['details'] = details
        kwargs['error_code'] = ErrorCode.RATE_LIMIT_EXCEEDED
        super().__init__(message, **kwargs)


class TimeoutException(CryptoAnalysisException):
    """Exception for timeout errors."""
    
    def __init__(self, message: str, timeout: float, **kwargs):
        details = kwargs.get('details', {})
        details['timeout'] = timeout
        kwargs['details'] = details
        kwargs['error_code'] = ErrorCode.TIMEOUT_ERROR
        super().__init__(message, **kwargs)


# Security Exceptions
class SecurityException(CryptoAnalysisException):
    """Exception for security-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('error_code', ErrorCode.AUTHENTICATION_FAILED)
        super().__init__(message, **kwargs)


class AuthenticationException(SecurityException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        kwargs['error_code'] = ErrorCode.AUTHENTICATION_FAILED
        super().__init__(message, **kwargs)


class AuthorizationException(SecurityException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Authorization failed", **kwargs):
        kwargs['error_code'] = ErrorCode.AUTHORIZATION_FAILED
        super().__init__(message, **kwargs)


class InvalidTokenException(SecurityException):
    """Exception for invalid token errors."""
    
    def __init__(self, message: str = "Invalid token", **kwargs):
        kwargs['error_code'] = ErrorCode.INVALID_TOKEN
        super().__init__(message, **kwargs)


class TokenExpiredException(SecurityException):
    """Exception for expired token errors."""
    
    def __init__(self, message: str = "Token has expired", **kwargs):
        kwargs['error_code'] = ErrorCode.TOKEN_EXPIRED
        super().__init__(message, **kwargs)
