"""
Analysis API endpoints.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Query
from typing import List, Optional
from models.schemas import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisSummary,
    ComparisonReport
)
from engines.technical_analysis import TechnicalAnalysisEngine
from engines.fundamental_analysis import FundamentalAnalysisEngine
from engines.signal_generator import SignalGenerator
from engines.ai_interpreter import AIInterpreter
from engines.analysis_history import AnalysisHistoryManager
from engines.data_collector import DataCollector
from utils.logger import setup_logger
from utils.cache import cache
import uuid
from datetime import datetime

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Initialize engines (non-user-specific)
data_collector = DataCollector()
technical_engine = TechnicalAnalysisEngine()
fundamental_engine = FundamentalAnalysisEngine()
signal_generator = SignalGenerator()
ai_interpreter = AIInterpreter()

# Supported coins list
SUPPORTED_COINS = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "DOT", "MATIC", "LTC",
    "AVAX", "LINK", "UNI", "ATOM", "XLM", "ALGO", "VET", "FIL", "TRX", "ETC",
    "SHIB", "APT", "ARB", "OP", "NEAR", "ICP", "HBAR", "QNT", "IMX", "SAND",
    "MANA", "AXS", "GALA", "ENJ", "CHZ", "THETA", "FTM", "AAVE", "MKR", "SNX",
    "CRV", "COMP", "YFI", "SUSHI", "BAL", "1INCH", "LRC", "ZRX", "KNC", "REN"
]


def get_history_manager() -> AnalysisHistoryManager:
    """Get history manager for current user."""
    # TODO: Get user_id from authentication
    user_id = "default_user"  # Placeholder
    return AnalysisHistoryManager(user_id)


@router.post("/start", response_model=AnalysisResult, status_code=201)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    async_mode: bool = Query(False, description="Run analysis asynchronously")
):
    """
    Start a new analysis for a coin.
    
    - **coin**: Coin symbol (e.g., BTC, ETH)
    - **timeframe**: Time interval (15m, 1h, 4h, 8h, 12h, 24h, 1w, 15d, 1M)
    - **async_mode**: If True, returns task ID immediately and runs analysis in background
    
    Returns complete analysis result with technical indicators, sentiment,
    signal, and AI interpretation.
    
    If async_mode=True, returns a task ID that can be used to check status.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Starting analysis for {request.coin} on {request.timeframe} (async={async_mode})",
        extra={"request_id": request_id, "coin": request.coin, "timeframe": request.timeframe}
    )
    
    try:
        # Validate coin
        if request.coin not in SUPPORTED_COINS:
            raise HTTPException(
                status_code=400,
                detail=f"Coin {request.coin} is not supported. Supported coins: {', '.join(SUPPORTED_COINS[:10])}..."
            )
        
        # If async mode, queue the task
        if async_mode:
            from utils.tasks import run_analysis_task
            
            # Get user_id (placeholder for now)
            user_id = "default_user"
            
            # Queue the task
            task = run_analysis_task.delay(
                coin=request.coin,
                timeframe=request.timeframe,
                user_id=user_id,
                use_cache=True
            )
            
            logger.info(
                f"Analysis queued with task ID: {task.id}",
                extra={"request_id": request_id, "task_id": task.id}
            )
            
            # Return task info
            return {
                "id": task.id,
                "coin": request.coin,
                "timeframe": request.timeframe,
                "status": "queued",
                "message": f"Analysis queued. Check status at /api/analysis/task/{task.id}"
            }
        
        # Synchronous execution (original behavior)
        # Perform technical analysis
        logger.info(f"Performing technical analysis for {request.coin}")
        technical_results = technical_engine.analyze(request.coin, request.timeframe)
        
        # Perform fundamental analysis
        logger.info(f"Performing fundamental analysis for {request.coin}")
        fundamental_results = fundamental_engine.analyze(request.coin)
        
        # Generate signal
        logger.info(f"Generating signal for {request.coin}")
        signal, explanation = signal_generator.generate_signal(
            technical_results,
            fundamental_results,
            request.coin,
            request.timeframe
        )
        
        # Get AI interpretation
        logger.info(f"Generating AI interpretation for {request.coin}")
        ai_report = ai_interpreter.generate_report(
            signal,
            explanation,
            technical_results,
            fundamental_results
        )
        
        # Get current price
        price_data = data_collector.fetch_price_data(request.coin, request.timeframe)
        current_price = price_data['close'].iloc[-1] if not price_data.empty else 0.0
        
        # Create analysis result
        analysis_result = AnalysisResult(
            id=str(uuid.uuid4()),
            coin=request.coin,
            timeframe=request.timeframe,
            timestamp=datetime.utcnow(),
            technical_results=technical_results,
            fundamental_results=fundamental_results,
            signal=signal,
            explanation=explanation,
            ai_report=ai_report,
            actual_outcome=None,
            price_at_analysis=float(current_price),
            price_after_period=None
        )
        
        # Save analysis to history
        history_manager = get_history_manager()
        analysis_id = history_manager.save_analysis(analysis_result)
        
        # Cache the result
        cache.set_analysis(analysis_id, analysis_result.dict())
        
        logger.info(
            f"Analysis completed and saved with ID: {analysis_id}",
            extra={"request_id": request_id, "analysis_id": analysis_id}
        )
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error during analysis: {str(e)}",
            extra={"request_id": request_id, "coin": request.coin},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str, http_request: Request):
    """
    Get a specific analysis result by ID.
    
    - **analysis_id**: Unique analysis identifier
    
    Returns the complete analysis result.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Fetching analysis {analysis_id}",
        extra={"request_id": request_id, "analysis_id": analysis_id}
    )
    
    try:
        # Try cache first
        cached_result = cache.get_analysis(analysis_id)
        if cached_result:
            logger.info(f"Analysis {analysis_id} found in cache")
            return AnalysisResult(**cached_result)
        
        # Fetch from database
        history_manager = get_history_manager()
        analysis = history_manager.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        # Cache for future requests
        cache.set_analysis(analysis_id, analysis.dict())
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching analysis: {str(e)}",
            extra={"request_id": request_id, "analysis_id": analysis_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch analysis: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, http_request: Request):
    """
    Get status of an async analysis task.
    
    - **task_id**: Celery task ID
    
    Returns task status and result if completed.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Checking task status for {task_id}",
        extra={"request_id": request_id, "task_id": task_id}
    )
    
    try:
        from celery.result import AsyncResult
        from utils.celery_app import celery_app
        
        # Get task result
        task = AsyncResult(task_id, app=celery_app)
        
        response = {
            "task_id": task_id,
            "status": task.state,
            "ready": task.ready()
        }
        
        if task.ready():
            if task.successful():
                response["result"] = task.result
                response["message"] = "Analysis completed successfully"
            else:
                response["error"] = str(task.info)
                response["message"] = "Analysis failed"
        else:
            response["message"] = "Analysis in progress"
        
        return response
        
    except Exception as e:
        logger.error(
            f"Error checking task status: {str(e)}",
            extra={"request_id": request_id, "task_id": task_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check task status: {str(e)}"
        )


@router.get("/history", response_model=List[AnalysisSummary])
async def get_analysis_history(
    coin: str = None,
    limit: int = 100,
    http_request: Request = None
):
    """
    Get analysis history.
    
    - **coin**: Optional coin filter
    - **limit**: Maximum number of results (default: 100)
    
    Returns list of analysis summaries ordered by timestamp (newest first).
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4())) if http_request else None
    
    logger.info(
        f"Fetching analysis history",
        extra={"request_id": request_id, "coin": coin, "limit": limit}
    )
    
    try:
        history_manager = get_history_manager()
        analyses = history_manager.list_analyses(coin=coin, limit=limit)
        return analyses
        
    except Exception as e:
        logger.error(
            f"Error fetching analysis history: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch analysis history: {str(e)}"
        )


@router.post("/compare", response_model=ComparisonReport)
async def compare_analyses(
    analysis_ids: List[str],
    http_request: Request
):
    """
    Compare multiple analyses.
    
    - **analysis_ids**: List of analysis IDs to compare (2-10 analyses)
    
    Returns comparison report with changes in signals, probabilities, and indicators.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    if len(analysis_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 analysis IDs are required for comparison"
        )
    
    if len(analysis_ids) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 analyses can be compared at once"
        )
    
    logger.info(
        f"Comparing {len(analysis_ids)} analyses",
        extra={"request_id": request_id, "analysis_ids": analysis_ids}
    )
    
    try:
        history_manager = get_history_manager()
        comparison = history_manager.compare_analyses(analysis_ids)
        
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail="One or more analysis IDs not found"
            )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error comparing analyses: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare analyses: {str(e)}"
        )
