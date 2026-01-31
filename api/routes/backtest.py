"""
Backtesting API endpoints.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import List
from models.schemas import (
    BacktestRequest,
    BacktestResult,
    BacktestComparison
)
from engines.backtesting import BacktestingEngine
from utils.logger import setup_logger
import uuid

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# Initialize backtesting engine
backtest_engine = BacktestingEngine()


@router.post("/start", response_model=dict, status_code=202)
async def start_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """
    Start a new backtest.
    
    - **coin**: Coin symbol (e.g., BTC, ETH)
    - **timeframe**: Time interval (15m, 1h, 4h, 8h, 12h, 24h, 1w, 15d, 1M)
    - **start_date**: Start date for backtest period
    - **end_date**: End date for backtest period
    - **initial_capital**: Starting capital (default: 10000)
    - **parameters**: Backtesting parameters including indicators and thresholds
    
    Returns backtest ID. The backtest runs asynchronously.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Starting backtest for {request.coin} from {request.start_date} to {request.end_date}",
        extra={
            "request_id": request_id,
            "coin": request.coin,
            "timeframe": request.timeframe,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat()
        }
    )
    
    try:
        # Start backtest (async)
        backtest_id = await backtest_engine.start_backtest(
            coin=request.coin,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            parameters=request.parameters
        )
        
        logger.info(
            f"Backtest started with ID: {backtest_id}",
            extra={"request_id": request_id, "backtest_id": backtest_id}
        )
        
        return {
            "backtest_id": backtest_id,
            "message": "Backtest started successfully",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(
            f"Error starting backtest: {str(e)}",
            extra={"request_id": request_id, "coin": request.coin},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start backtest: {str(e)}"
        )


@router.get("/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(
    backtest_id: str,
    http_request: Request
):
    """
    Get backtest result by ID.
    
    - **backtest_id**: Unique backtest identifier
    
    Returns complete backtest result including trades, metrics, and equity curve.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Fetching backtest result {backtest_id}",
        extra={"request_id": request_id, "backtest_id": backtest_id}
    )
    
    try:
        result = backtest_engine.get_backtest_result(backtest_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Backtest with ID {backtest_id} not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching backtest result: {str(e)}",
            extra={"request_id": request_id, "backtest_id": backtest_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch backtest result: {str(e)}"
        )


@router.post("/compare", response_model=BacktestComparison)
async def compare_backtests(
    backtest_ids: List[str],
    http_request: Request
):
    """
    Compare multiple backtest results.
    
    - **backtest_ids**: List of backtest IDs to compare (2-10 backtests)
    
    Returns comparison report with metric comparisons across all backtests.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    if len(backtest_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 backtest IDs are required for comparison"
        )
    
    if len(backtest_ids) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 backtests can be compared at once"
        )
    
    logger.info(
        f"Comparing {len(backtest_ids)} backtests",
        extra={"request_id": request_id, "backtest_ids": backtest_ids}
    )
    
    try:
        comparison = backtest_engine.compare_backtests(backtest_ids)
        
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail="One or more backtest IDs not found"
            )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error comparing backtests: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare backtests: {str(e)}"
        )
