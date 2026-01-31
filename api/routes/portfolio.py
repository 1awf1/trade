"""
Portfolio API endpoints.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
from models.schemas import (
    PortfolioAddRequest,
    PortfolioRemoveRequest,
    Portfolio,
    PerformanceSnapshot
)
from engines.portfolio_manager import PortfolioManager
from utils.database import get_db
from utils.logger import setup_logger
from sqlalchemy.orm import Session
import uuid

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def get_portfolio_manager(db: Session = Depends(get_db)) -> PortfolioManager:
    """Dependency to get portfolio manager instance."""
    # TODO: Get user_id from authentication
    user_id = "default_user"  # Placeholder
    return PortfolioManager(db, user_id)


@router.get("", response_model=Portfolio)
async def get_portfolio(
    http_request: Request,
    portfolio_manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """
    Get current portfolio with all holdings.
    
    Returns complete portfolio including:
    - All holdings with current prices and P&L
    - Total portfolio value
    - Total profit/loss
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        "Fetching portfolio",
        extra={"request_id": request_id}
    )
    
    try:
        portfolio = portfolio_manager.get_portfolio()
        return portfolio
        
    except Exception as e:
        logger.error(
            f"Error fetching portfolio: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch portfolio: {str(e)}"
        )


@router.post("/add", response_model=dict, status_code=201)
async def add_to_portfolio(
    request: PortfolioAddRequest,
    http_request: Request,
    portfolio_manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """
    Add a coin to the portfolio.
    
    - **coin**: Coin symbol (e.g., BTC, ETH)
    - **amount**: Amount of coins purchased
    - **purchase_price**: Price per coin at purchase
    - **purchase_date**: Date of purchase
    
    Returns the holding ID.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Adding {request.amount} {request.coin} to portfolio",
        extra={
            "request_id": request_id,
            "coin": request.coin,
            "amount": str(request.amount),
            "purchase_price": str(request.purchase_price)
        }
    )
    
    try:
        holding_id = portfolio_manager.add_coin(
            coin=request.coin,
            amount=request.amount,
            purchase_price=request.purchase_price,
            purchase_date=request.purchase_date
        )
        
        logger.info(
            f"Successfully added {request.coin} to portfolio with ID: {holding_id}",
            extra={"request_id": request_id, "holding_id": holding_id}
        )
        
        return {
            "holding_id": holding_id,
            "message": f"Successfully added {request.amount} {request.coin} to portfolio"
        }
        
    except Exception as e:
        logger.error(
            f"Error adding to portfolio: {str(e)}",
            extra={"request_id": request_id, "coin": request.coin},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add to portfolio: {str(e)}"
        )


@router.delete("/{holding_id}", response_model=dict)
async def remove_from_portfolio(
    holding_id: str,
    sale_price: float,
    sale_date: str,
    http_request: Request,
    portfolio_manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """
    Remove a coin from the portfolio (sell).
    
    - **holding_id**: ID of the holding to remove
    - **sale_price**: Price per coin at sale
    - **sale_date**: Date of sale (ISO format)
    
    Returns confirmation message with profit/loss.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Removing holding {holding_id} from portfolio",
        extra={
            "request_id": request_id,
            "holding_id": holding_id,
            "sale_price": sale_price
        }
    )
    
    try:
        from datetime import datetime
        from decimal import Decimal
        
        sale_date_obj = datetime.fromisoformat(sale_date.replace('Z', '+00:00'))
        
        portfolio_manager.remove_coin(
            holding_id=holding_id,
            sale_price=Decimal(str(sale_price)),
            sale_date=sale_date_obj
        )
        
        logger.info(
            f"Successfully removed holding {holding_id} from portfolio",
            extra={"request_id": request_id, "holding_id": holding_id}
        )
        
        return {
            "message": f"Successfully removed holding from portfolio",
            "holding_id": holding_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Error removing from portfolio: {str(e)}",
            extra={"request_id": request_id, "holding_id": holding_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove from portfolio: {str(e)}"
        )


@router.get("/performance", response_model=List[PerformanceSnapshot])
async def get_portfolio_performance(
    days: int = 30,
    http_request: Request = None,
    portfolio_manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """
    Get portfolio performance history.
    
    - **days**: Number of days of history to retrieve (default: 30)
    
    Returns list of performance snapshots showing portfolio value over time.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4())) if http_request else None
    
    logger.info(
        f"Fetching portfolio performance for {days} days",
        extra={"request_id": request_id, "days": days}
    )
    
    try:
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=400,
                detail="Days must be between 1 and 365"
            )
        
        performance = portfolio_manager.get_performance_history(days)
        return performance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching portfolio performance: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch portfolio performance: {str(e)}"
        )
