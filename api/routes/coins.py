"""
Coin helper API endpoints.
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict
from engines.data_collector import DataCollector
from utils.logger import setup_logger
import uuid

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/coins", tags=["coins"])

# Initialize data collector
data_collector = DataCollector()

# Supported coins list (in production, this could come from a database or config)
SUPPORTED_COINS = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "DOT", "MATIC", "LTC",
    "AVAX", "LINK", "UNI", "ATOM", "XLM", "ALGO", "VET", "FIL", "TRX", "ETC",
    "SHIB", "APT", "ARB", "OP", "NEAR", "ICP", "HBAR", "QNT", "IMX", "SAND",
    "MANA", "AXS", "GALA", "ENJ", "CHZ", "THETA", "FTM", "AAVE", "MKR", "SNX",
    "CRV", "COMP", "YFI", "SUSHI", "BAL", "1INCH", "LRC", "ZRX", "KNC", "REN"
]


@router.get("", response_model=List[str])
async def get_supported_coins(http_request: Request = None):
    """
    Get list of supported coins.
    
    Returns list of coin symbols that can be analyzed.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4())) if http_request else None
    
    logger.info(
        "Fetching supported coins",
        extra={"request_id": request_id}
    )
    
    try:
        return SUPPORTED_COINS
        
    except Exception as e:
        logger.error(
            f"Error fetching supported coins: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch supported coins: {str(e)}"
        )


@router.get("/{symbol}/price", response_model=Dict)
async def get_coin_price(
    symbol: str,
    http_request: Request
):
    """
    Get current price for a specific coin.
    
    - **symbol**: Coin symbol (e.g., BTC, ETH)
    
    Returns current price information including:
    - price: Current price in USD
    - timestamp: Time of price data
    - 24h_change: 24-hour price change percentage
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    symbol = symbol.upper().strip()
    
    logger.info(
        f"Fetching price for {symbol}",
        extra={"request_id": request_id, "symbol": symbol}
    )
    
    try:
        # Validate coin
        if symbol not in SUPPORTED_COINS:
            raise HTTPException(
                status_code=400,
                detail=f"Coin {symbol} is not supported. Supported coins: {', '.join(SUPPORTED_COINS[:10])}..."
            )
        
        # Fetch price data
        price_data = data_collector.fetch_price_data(symbol, '1h')
        
        if price_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Price data not available for {symbol}"
            )
        
        # Get latest price
        latest = price_data.iloc[-1]
        
        # Calculate 24h change if we have enough data
        change_24h = None
        if len(price_data) >= 24:
            price_24h_ago = price_data.iloc[-24]['close']
            current_price = latest['close']
            change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
        
        return {
            "symbol": symbol,
            "price": float(latest['close']),
            "timestamp": latest.name.isoformat() if hasattr(latest.name, 'isoformat') else str(latest.name),
            "24h_change": float(change_24h) if change_24h is not None else None,
            "volume": float(latest['volume']) if 'volume' in latest else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching price for {symbol}: {str(e)}",
            extra={"request_id": request_id, "symbol": symbol},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch price: {str(e)}"
        )
