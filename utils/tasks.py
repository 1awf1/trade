"""
Celery tasks for async processing.
Handles analysis and backtesting operations in background.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from celery import Task
from utils.celery_app import celery_app
from utils.logger import logger
from utils.cache import cache
from utils.errors import (
    AnalysisException,
    BacktestException,
    TimeoutException,
    ErrorCode
)


class CallbackTask(Task):
    """Base task with callbacks for success/failure."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="tasks.run_analysis",
    max_retries=3,
    default_retry_delay=60
)
def run_analysis_task(
    self,
    coin: str,
    timeframe: str,
    user_id: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Run analysis asynchronously.
    
    Args:
        coin: Coin symbol
        timeframe: Timeframe for analysis
        user_id: Optional user ID
        use_cache: Whether to use cached data
    
    Returns:
        Analysis result dict
    
    Raises:
        AnalysisException: If analysis fails
    """
    try:
        logger.info(f"Starting async analysis for {coin} ({timeframe})")
        
        # Import here to avoid circular dependencies
        from engines.data_collector import DataCollector
        from engines.technical_analysis import TechnicalAnalysisEngine
        from engines.fundamental_analysis import FundamentalAnalysisEngine
        from engines.signal_generator import SignalGenerator
        from engines.ai_interpreter import AIInterpreter
        from engines.analysis_history import AnalysisHistoryManager
        
        # Initialize engines
        data_collector = DataCollector()
        technical_engine = TechnicalAnalysisEngine()
        fundamental_engine = FundamentalAnalysisEngine()
        signal_generator = SignalGenerator()
        ai_interpreter = AIInterpreter()
        history_manager = AnalysisHistoryManager()
        
        # Step 1: Collect data
        logger.info(f"Collecting data for {coin}")
        price_data = data_collector.fetch_price_data(coin, timeframe, use_cache=use_cache)
        social_data = data_collector.fetch_social_media_data(coin, use_cache=use_cache)
        news_data = data_collector.fetch_news_data(coin, use_cache=use_cache)
        
        # Step 2: Technical analysis
        logger.info(f"Running technical analysis for {coin}")
        technical_results = technical_engine.analyze(price_data)
        
        # Step 3: Fundamental analysis
        logger.info(f"Running fundamental analysis for {coin}")
        fundamental_results = fundamental_engine.analyze(social_data, news_data)
        
        # Step 4: Generate signal
        logger.info(f"Generating signal for {coin}")
        signal = signal_generator.generate_signal(
            technical_results,
            fundamental_results,
            price_data['current_price']
        )
        
        # Step 5: AI interpretation
        logger.info(f"Generating AI interpretation for {coin}")
        ai_report = ai_interpreter.generate_report(
            signal,
            technical_results,
            fundamental_results
        )
        
        # Step 6: Save analysis
        analysis_result = {
            "coin": coin,
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat(),
            "technical_results": technical_results,
            "fundamental_results": fundamental_results,
            "signal": signal,
            "ai_report": ai_report,
            "price_at_analysis": price_data['current_price']
        }
        
        if user_id:
            analysis_id = history_manager.save_analysis(user_id, analysis_result)
            analysis_result["id"] = analysis_id
            
            # Cache the result
            cache.set_analysis(analysis_id, analysis_result)
        
        logger.info(f"Analysis completed for {coin}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Analysis failed for {coin}: {e}")
        
        # Retry on transient errors
        if isinstance(e, (ConnectionError, TimeoutError)):
            raise self.retry(exc=e)
        
        raise AnalysisException(
            message=f"Analysis failed for {coin}",
            error_code=ErrorCode.ANALYSIS_FAILED,
            details={"coin": coin, "timeframe": timeframe, "error": str(e)}
        )


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="tasks.run_backtest",
    max_retries=1,
    time_limit=600  # 10 minutes max
)
def run_backtest_task(
    self,
    coin: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    parameters: Dict[str, Any],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run backtest asynchronously.
    
    Args:
        coin: Coin symbol
        timeframe: Timeframe for backtest
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        initial_capital: Initial capital amount
        parameters: Backtest parameters
        user_id: Optional user ID
    
    Returns:
        Backtest result dict
    
    Raises:
        BacktestException: If backtest fails
    """
    try:
        logger.info(f"Starting async backtest for {coin} ({timeframe})")
        
        # Import here to avoid circular dependencies
        from engines.backtesting import BacktestingEngine
        
        # Initialize engine
        backtest_engine = BacktestingEngine()
        
        # Convert date strings to datetime
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Run backtest
        logger.info(f"Running backtest for {coin} from {start_date} to {end_date}")
        result = backtest_engine.run_backtest(
            coin=coin,
            timeframe=timeframe,
            start_date=start_dt,
            end_date=end_dt,
            initial_capital=initial_capital,
            parameters=parameters,
            user_id=user_id
        )
        
        logger.info(f"Backtest completed for {coin}")
        return result
        
    except Exception as e:
        logger.error(f"Backtest failed for {coin}: {e}")
        
        raise BacktestException(
            message=f"Backtest failed for {coin}",
            error_code=ErrorCode.BACKTEST_FAILED,
            details={
                "coin": coin,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "error": str(e)
            }
        )


@celery_app.task(
    bind=True,
    name="tasks.check_alarms",
    max_retries=3
)
def check_alarms_task(self) -> Dict[str, Any]:
    """
    Check all active alarms and trigger notifications.
    This task is scheduled to run periodically (every minute).
    
    Returns:
        Dict with check results
    """
    try:
        logger.info("Starting alarm check")
        
        # Import here to avoid circular dependencies
        from engines.alarm_system import AlarmSystem
        
        # Initialize alarm system
        alarm_system = AlarmSystem()
        
        # Check all alarms
        triggered_alarms = alarm_system.check_alarms()
        
        logger.info(f"Alarm check completed. {len(triggered_alarms)} alarms triggered")
        
        return {
            "checked_at": datetime.utcnow().isoformat(),
            "triggered_count": len(triggered_alarms),
            "triggered_alarms": [
                {
                    "alarm_id": alarm.id,
                    "coin": alarm.config.coin,
                    "type": alarm.config.type
                }
                for alarm in triggered_alarms
            ]
        }
        
    except Exception as e:
        logger.error(f"Alarm check failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(name="tasks.cleanup_cache")
def cleanup_cache_task() -> Dict[str, Any]:
    """
    Clean up stale cache entries.
    This task is scheduled to run periodically (daily).
    
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info("Starting cache cleanup")
        
        # Get cache stats before cleanup
        stats_before = cache.get_cache_stats()
        
        # Clean up stale data
        deleted_count = cache.invalidate_stale_data()
        
        # Get cache stats after cleanup
        stats_after = cache.get_cache_stats()
        
        logger.info(f"Cache cleanup completed. Deleted {deleted_count} keys")
        
        return {
            "cleaned_at": datetime.utcnow().isoformat(),
            "deleted_count": deleted_count,
            "keys_before": stats_before.get("total_keys", 0),
            "keys_after": stats_after.get("total_keys", 0)
        }
        
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return {
            "cleaned_at": datetime.utcnow().isoformat(),
            "error": str(e)
        }


# Celery Beat Schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    'check-alarms-every-minute': {
        'task': 'tasks.check_alarms',
        'schedule': 60.0,  # Every 60 seconds
    },
    'cleanup-cache-daily': {
        'task': 'tasks.cleanup_cache',
        'schedule': 86400.0,  # Every 24 hours
    },
}
