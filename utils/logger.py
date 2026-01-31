"""
Logging configuration for the application with structured logging support.
"""
import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with structured data."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'coin'):
            log_data['coin'] = record.coin
        if hasattr(record, 'error_code'):
            log_data['error_code'] = record.error_code
        
        # Add all extra attributes
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'request_id', 'user_id', 'coin',
                          'error_code']:
                try:
                    # Only add JSON-serializable values
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    pass
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for console output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record in human-readable format."""
        # Base format
        base_msg = super().format(record)
        
        # Add extra context if available
        extras = []
        if hasattr(record, 'request_id'):
            extras.append(f"request_id={record.request_id}")
        if hasattr(record, 'user_id'):
            extras.append(f"user_id={record.user_id}")
        if hasattr(record, 'coin'):
            extras.append(f"coin={record.coin}")
        if hasattr(record, 'error_code'):
            extras.append(f"error_code={record.error_code}")
        
        if extras:
            base_msg += f" [{', '.join(extras)}]"
        
        return base_msg


def setup_logger(
    name: str,
    level: int = logging.INFO,
    structured: bool = False
) -> logging.Logger:
    """
    Setup and configure logger with structured logging support.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        structured: If True, use JSON structured logging for file output
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler with human-readable format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    console_formatter = HumanReadableFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create file handler with structured or human-readable format
    file_handler = logging.FileHandler(logs_dir / "app.log")
    file_handler.setLevel(level)
    
    if structured:
        file_formatter = StructuredFormatter()
    else:
        file_formatter = HumanReadableFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Create error log file for ERROR and above
    error_handler = logging.FileHandler(logs_dir / "error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding contextual information."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add extra context."""
        extra = kwargs.get('extra', {})
        
        # Merge adapter's extra with call's extra
        if self.extra:
            extra.update(self.extra)
        
        kwargs['extra'] = extra
        return msg, kwargs


def get_logger(
    name: str,
    extra: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Get a logger with optional extra context.
    
    Args:
        name: Logger name
        extra: Extra context to add to all log messages
        
    Returns:
        Logger or LoggerAdapter instance
    """
    logger = logging.getLogger(name)
    
    if extra:
        return LoggerAdapter(logger, extra)
    
    return logger


# Create default logger instance
logger = setup_logger("crypto_analysis", structured=True)
