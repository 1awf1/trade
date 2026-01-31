"""
Portfolio Manager component for managing user's crypto portfolio.
Handles CRUD operations, calculations, performance tracking, and trade history.
"""
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from models.database import PortfolioHolding, TradeHistory, User
from models.schemas import (
    Holding, Portfolio, TradeHistory as TradeHistorySchema,
    PerformanceSnapshot, ProfitLoss, Signal
)
from engines.data_collector import DataCollector
from utils.logger import logger
import uuid


class PortfolioManagerError(Exception):
    """Base exception for portfolio manager errors."""
    pass


class HoldingNotFoundError(PortfolioManagerError):
    """Raised when a holding is not found."""
    pass


class PortfolioManager:
    """
    Portfolio Manager for tracking and managing user's crypto assets.
    
    Responsibilities:
    - Add/remove coins from portfolio
    - Calculate current values and profit/loss
    - Track trade history
    - Generate performance graphs
    """
    
    def __init__(self, db: Session, user_id: str):
        """
        Initialize portfolio manager.
        
        Args:
            db: Database session
            user_id: User ID
        """
        self.db = db
        self.user_id = user_id
        self.data_collector = DataCollector()
    
    def add_coin(
        self,
        coin: str,
        amount: Decimal,
        purchase_price: Decimal,
        purchase_date: datetime
    ) -> str:
        """
        Add a coin to the portfolio.
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            amount: Amount of coins purchased
            purchase_price: Purchase price per coin
            purchase_date: Date of purchase
        
        Returns:
            Holding ID
        
        Raises:
            PortfolioManagerError: If operation fails
        """
        try:
            coin = coin.upper()
            
            # Create portfolio holding
            holding = PortfolioHolding(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                coin=coin,
                amount=amount,
                purchase_price=purchase_price,
                purchase_date=purchase_date,
                is_active=True
            )
            
            self.db.add(holding)
            
            # Create trade history entry
            trade = TradeHistory(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                holding_id=holding.id,
                type="buy",
                coin=coin,
                amount=amount,
                price=purchase_price,
                date=purchase_date,
                profit_loss=None
            )
            
            self.db.add(trade)
            self.db.commit()
            
            logger.info(
                f"Added {amount} {coin} to portfolio for user {self.user_id} "
                f"at ${purchase_price} on {purchase_date}"
            )
            
            return holding.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding coin to portfolio: {e}")
            raise PortfolioManagerError(f"Failed to add coin to portfolio: {e}")
    
    def remove_coin(
        self,
        holding_id: str,
        sale_price: Decimal,
        sale_date: datetime
    ) -> None:
        """
        Remove a coin from the portfolio (sell).
        
        Args:
            holding_id: ID of the holding to remove
            sale_price: Sale price per coin
            sale_date: Date of sale
        
        Raises:
            HoldingNotFoundError: If holding not found
            PortfolioManagerError: If operation fails
        """
        try:
            # Find the holding
            holding = self.db.query(PortfolioHolding).filter(
                and_(
                    PortfolioHolding.id == holding_id,
                    PortfolioHolding.user_id == self.user_id,
                    PortfolioHolding.is_active == True
                )
            ).first()
            
            if not holding:
                raise HoldingNotFoundError(f"Holding {holding_id} not found or already sold")
            
            # Calculate profit/loss
            profit_loss = (sale_price - holding.purchase_price) * holding.amount
            
            # Mark holding as inactive
            holding.is_active = False
            
            # Create trade history entry for sale
            trade = TradeHistory(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                holding_id=holding_id,
                type="sell",
                coin=holding.coin,
                amount=holding.amount,
                price=sale_price,
                date=sale_date,
                profit_loss=profit_loss
            )
            
            self.db.add(trade)
            self.db.commit()
            
            logger.info(
                f"Removed {holding.amount} {holding.coin} from portfolio for user {self.user_id} "
                f"at ${sale_price} on {sale_date}. Profit/Loss: ${profit_loss}"
            )
            
        except HoldingNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing coin from portfolio: {e}")
            raise PortfolioManagerError(f"Failed to remove coin from portfolio: {e}")
    
    async def get_portfolio(self, include_signals: bool = False) -> Portfolio:
        """
        Get complete portfolio with current values.
        
        Args:
            include_signals: Whether to include last signal for each coin
        
        Returns:
            Portfolio object with all holdings and calculations
        
        Raises:
            PortfolioManagerError: If operation fails
        """
        try:
            # Get all active holdings
            holdings_db = self.db.query(PortfolioHolding).filter(
                and_(
                    PortfolioHolding.user_id == self.user_id,
                    PortfolioHolding.is_active == True
                )
            ).all()
            
            if not holdings_db:
                # Return empty portfolio
                return Portfolio(
                    holdings=[],
                    total_value=Decimal("0"),
                    total_invested=Decimal("0"),
                    total_profit_loss=Decimal("0"),
                    total_profit_loss_percent=0.0
                )
            
            # Fetch current prices for all coins
            holdings = []
            total_value = Decimal("0")
            total_invested = Decimal("0")
            
            for holding_db in holdings_db:
                try:
                    # Fetch current price
                    current_price = await self.data_collector.fetch_price(holding_db.coin)
                    
                    if current_price is None:
                        logger.warning(f"Could not fetch price for {holding_db.coin}, skipping")
                        continue
                    
                    current_price_decimal = Decimal(str(current_price))
                    current_value = current_price_decimal * holding_db.amount
                    invested = holding_db.purchase_price * holding_db.amount
                    profit_loss_amount = current_value - invested
                    profit_loss_percent = float((profit_loss_amount / invested) * 100) if invested > 0 else 0.0
                    
                    # Get last signal if requested
                    last_signal = None
                    if include_signals:
                        # TODO: Fetch last signal from analyses table
                        pass
                    
                    holding = Holding(
                        id=holding_db.id,
                        coin=holding_db.coin,
                        amount=holding_db.amount,
                        purchase_price=holding_db.purchase_price,
                        purchase_date=holding_db.purchase_date,
                        current_price=current_price_decimal,
                        current_value=current_value,
                        profit_loss_percent=profit_loss_percent,
                        profit_loss_amount=profit_loss_amount,
                        last_signal=last_signal
                    )
                    
                    holdings.append(holding)
                    total_value += current_value
                    total_invested += invested
                    
                except Exception as e:
                    logger.error(f"Error processing holding {holding_db.id}: {e}")
                    continue
            
            # Calculate total profit/loss
            total_profit_loss = total_value - total_invested
            total_profit_loss_percent = float((total_profit_loss / total_invested) * 100) if total_invested > 0 else 0.0
            
            portfolio = Portfolio(
                holdings=holdings,
                total_value=total_value,
                total_invested=total_invested,
                total_profit_loss=total_profit_loss,
                total_profit_loss_percent=total_profit_loss_percent
            )
            
            logger.info(
                f"Retrieved portfolio for user {self.user_id}: "
                f"{len(holdings)} holdings, total value ${total_value}"
            )
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            raise PortfolioManagerError(f"Failed to get portfolio: {e}")
    
    async def calculate_total_value(self) -> Decimal:
        """
        Calculate total portfolio value.
        
        Returns:
            Total portfolio value in USD
        
        Raises:
            PortfolioManagerError: If operation fails
        """
        try:
            portfolio = await self.get_portfolio()
            return portfolio.total_value
        except Exception as e:
            logger.error(f"Error calculating total value: {e}")
            raise PortfolioManagerError(f"Failed to calculate total value: {e}")
    
    async def calculate_profit_loss(self) -> ProfitLoss:
        """
        Calculate profit/loss for the portfolio.
        
        Returns:
            ProfitLoss object with detailed calculations
        
        Raises:
            PortfolioManagerError: If operation fails
        """
        try:
            portfolio = await self.get_portfolio()
            
            return ProfitLoss(
                total_invested=portfolio.total_invested,
                current_value=portfolio.total_value,
                profit_loss_amount=portfolio.total_profit_loss,
                profit_loss_percent=portfolio.total_profit_loss_percent
            )
        except Exception as e:
            logger.error(f"Error calculating profit/loss: {e}")
            raise PortfolioManagerError(f"Failed to calculate profit/loss: {e}")
    
    async def get_performance_history(self, days: int = 30) -> List[PerformanceSnapshot]:
        """
        Get portfolio performance history over time.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of performance snapshots
        
        Raises:
            PortfolioManagerError: If operation fails
        """
        try:
            # Get all active holdings
            holdings_db = self.db.query(PortfolioHolding).filter(
                and_(
                    PortfolioHolding.user_id == self.user_id,
                    PortfolioHolding.is_active == True
                )
            ).all()
            
            if not holdings_db:
                return []
            
            # Generate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # For simplicity, we'll sample at daily intervals
            # In production, you might want to store historical snapshots
            snapshots = []
            current_date = start_date
            
            while current_date <= end_date:
                # Calculate portfolio value at this date
                # Note: This is a simplified implementation
                # In production, you'd need historical price data
                total_value = Decimal("0")
                total_invested = Decimal("0")
                
                for holding_db in holdings_db:
                    # Only include holdings purchased before this date
                    if holding_db.purchase_date <= current_date:
                        # For now, use current price (should use historical price)
                        try:
                            current_price = await self.data_collector.fetch_price(holding_db.coin)
                            if current_price:
                                current_price_decimal = Decimal(str(current_price))
                                total_value += current_price_decimal * holding_db.amount
                                total_invested += holding_db.purchase_price * holding_db.amount
                        except Exception as e:
                            logger.warning(f"Error fetching price for {holding_db.coin}: {e}")
                            continue
                
                profit_loss_percent = float((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0.0
                
                snapshot = PerformanceSnapshot(
                    timestamp=current_date,
                    total_value=total_value,
                    profit_loss_percent=profit_loss_percent
                )
                
                snapshots.append(snapshot)
                current_date += timedelta(days=1)
            
            logger.info(f"Generated {len(snapshots)} performance snapshots for user {self.user_id}")
            return snapshots
            
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            raise PortfolioManagerError(f"Failed to get performance history: {e}")
    
    def get_trade_history(self, limit: int = 100) -> List[TradeHistorySchema]:
        """
        Get trade history for the user.
        
        Args:
            limit: Maximum number of trades to return
        
        Returns:
            List of trade history records
        
        Raises:
            PortfolioManagerError: If operation fails
        """
        try:
            trades_db = self.db.query(TradeHistory).filter(
                TradeHistory.user_id == self.user_id
            ).order_by(desc(TradeHistory.date)).limit(limit).all()
            
            trades = []
            for trade_db in trades_db:
                trade = TradeHistorySchema(
                    id=trade_db.id,
                    coin=trade_db.coin,
                    type=trade_db.type,
                    amount=trade_db.amount,
                    price=trade_db.price,
                    date=trade_db.date,
                    profit_loss=trade_db.profit_loss
                )
                trades.append(trade)
            
            logger.info(f"Retrieved {len(trades)} trade history records for user {self.user_id}")
            return trades
            
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            raise PortfolioManagerError(f"Failed to get trade history: {e}")
