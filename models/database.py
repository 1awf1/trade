"""
Database models using SQLAlchemy ORM.
Defines tables: users, analyses, portfolio_holdings, trade_history, alarms, alarm_history, backtests
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, 
    ForeignKey, Index, DECIMAL, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID as string."""
    return str(uuid.uuid4())


class User(Base):
    """User table for authentication and user management."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    portfolio_holdings = relationship("PortfolioHolding", back_populates="user", cascade="all, delete-orphan")
    trade_history = relationship("TradeHistory", back_populates="user", cascade="all, delete-orphan")
    alarms = relationship("Alarm", back_populates="user", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="user", cascade="all, delete-orphan")


class Analysis(Base):
    """Analysis results table storing all analysis data."""
    __tablename__ = "analyses"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coin = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    technical_data = Column(JSON, nullable=False)
    fundamental_data = Column(JSON, nullable=False)
    signal = Column(JSON, nullable=False)
    ai_report = Column(Text, nullable=True)
    price_at_analysis = Column(DECIMAL(20, 8), nullable=True)
    price_after_period = Column(DECIMAL(20, 8), nullable=True)
    actual_outcome = Column(String(20), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    
    # Indexes
    __table_args__ = (
        Index("idx_analysis_user_coin", "user_id", "coin"),
        Index("idx_timestamp", "timestamp"),
    )


class PortfolioHolding(Base):
    """Portfolio holdings table for tracking user's crypto assets."""
    __tablename__ = "portfolio_holdings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coin = Column(String(20), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    purchase_price = Column(DECIMAL(20, 8), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="portfolio_holdings")
    trades = relationship("TradeHistory", back_populates="holding", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_portfolio_user_active", "user_id", "is_active"),
    )


class TradeHistory(Base):
    """Trade history table for tracking buy/sell transactions."""
    __tablename__ = "trade_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    holding_id = Column(String(36), ForeignKey("portfolio_holdings.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(10), nullable=False)  # 'buy' or 'sell'
    coin = Column(String(20), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    date = Column(DateTime, nullable=False)
    profit_loss = Column(DECIMAL(20, 8), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trade_history")
    holding = relationship("PortfolioHolding", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_date", "user_id", "date"),
    )


class Alarm(Base):
    """Alarms table for price/signal/probability-based notifications."""
    __tablename__ = "alarms"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coin = Column(String(20), nullable=False)
    type = Column(String(30), nullable=False)  # 'price', 'signal', 'success_probability'
    condition = Column(String(20), nullable=False)  # 'above', 'below', 'equals'
    threshold = Column(DECIMAL(20, 8), nullable=False)
    notification_channels = Column(JSON, nullable=False)  # ['email', 'web_push']
    auto_disable = Column(Boolean, default=False, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="alarms")
    alarm_history = relationship("AlarmHistory", back_populates="alarm", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_alarm_user_active", "user_id", "active"),
    )


class AlarmHistory(Base):
    """Alarm history table for tracking alarm triggers."""
    __tablename__ = "alarm_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    alarm_id = Column(String(36), ForeignKey("alarms.id", ondelete="CASCADE"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    trigger_value = Column(DECIMAL(20, 8), nullable=False)
    notification_sent = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    alarm = relationship("Alarm", back_populates="alarm_history")


class Backtest(Base):
    """Backtests table for storing strategy testing results."""
    __tablename__ = "backtests"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coin = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    parameters = Column(JSON, nullable=False)
    trades = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False)
    equity_curve = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="backtests")
    
    # Indexes
    __table_args__ = (
        Index("idx_backtest_user_coin", "user_id", "coin"),
    )
