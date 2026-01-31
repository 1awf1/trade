"""
Unit and property-based tests for Portfolio Manager.
Tests portfolio CRUD operations, calculations, and trade history.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, User, PortfolioHolding, TradeHistory
from engines.portfolio_manager import PortfolioManager, HoldingNotFoundError, PortfolioManagerError
from unittest.mock import AsyncMock, patch, MagicMock
import uuid


# ============================================================================
# Test Setup
# ============================================================================

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create a test user
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    
    yield session, user.id
    
    session.close()


@pytest.fixture
def portfolio_manager(db_session):
    """Create a portfolio manager instance."""
    session, user_id = db_session
    return PortfolioManager(session, user_id)


# ============================================================================
# Hypothesis Strategies
# ============================================================================

SUPPORTED_COINS = ["BTC", "ETH", "ADA", "SOL", "DOT", "BNB", "XRP", "DOGE", "AVAX", "MATIC"]

coin_strategy = st.sampled_from(SUPPORTED_COINS)
amount_strategy = st.decimals(min_value=Decimal("0.001"), max_value=Decimal("1000"), places=8)
price_strategy = st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100000"), places=8)
date_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime.utcnow()
)


# ============================================================================
# Unit Tests - Portfolio CRUD Operations
# ============================================================================

def test_add_coin_basic(portfolio_manager, db_session):
    """Test basic coin addition to portfolio."""
    session, user_id = db_session
    
    holding_id = portfolio_manager.add_coin(
        coin="BTC",
        amount=Decimal("1.5"),
        purchase_price=Decimal("50000"),
        purchase_date=datetime(2024, 1, 1)
    )
    
    assert holding_id is not None
    
    # Verify holding in database
    holding = session.query(PortfolioHolding).filter_by(id=holding_id).first()
    assert holding is not None
    assert holding.coin == "BTC"
    assert holding.amount == Decimal("1.5")
    assert holding.purchase_price == Decimal("50000")
    assert holding.is_active == True
    
    # Verify trade history
    trade = session.query(TradeHistory).filter_by(holding_id=holding_id).first()
    assert trade is not None
    assert trade.type == "buy"
    assert trade.coin == "BTC"
    assert trade.amount == Decimal("1.5")


def test_remove_coin_basic(portfolio_manager, db_session):
    """Test basic coin removal from portfolio."""
    session, user_id = db_session
    
    # Add a coin first
    holding_id = portfolio_manager.add_coin(
        coin="ETH",
        amount=Decimal("10"),
        purchase_price=Decimal("2000"),
        purchase_date=datetime(2024, 1, 1)
    )
    
    # Remove the coin
    portfolio_manager.remove_coin(
        holding_id=holding_id,
        sale_price=Decimal("2500"),
        sale_date=datetime(2024, 2, 1)
    )
    
    # Verify holding is inactive
    holding = session.query(PortfolioHolding).filter_by(id=holding_id).first()
    assert holding.is_active == False
    
    # Verify sell trade history
    sell_trade = session.query(TradeHistory).filter_by(
        holding_id=holding_id,
        type="sell"
    ).first()
    assert sell_trade is not None
    assert sell_trade.price == Decimal("2500")
    assert sell_trade.profit_loss == Decimal("5000")  # (2500 - 2000) * 10


def test_remove_nonexistent_holding(portfolio_manager):
    """Test removing a non-existent holding raises error."""
    with pytest.raises(HoldingNotFoundError):
        portfolio_manager.remove_coin(
            holding_id="nonexistent-id",
            sale_price=Decimal("1000"),
            sale_date=datetime.utcnow()
        )


@pytest.mark.asyncio
async def test_get_empty_portfolio(portfolio_manager):
    """Test getting an empty portfolio."""
    portfolio = await portfolio_manager.get_portfolio()
    
    assert portfolio.holdings == []
    assert portfolio.total_value == Decimal("0")
    assert portfolio.total_invested == Decimal("0")
    assert portfolio.total_profit_loss == Decimal("0")
    assert portfolio.total_profit_loss_percent == 0.0


@pytest.mark.asyncio
async def test_get_portfolio_with_holdings(portfolio_manager, db_session):
    """Test getting portfolio with holdings."""
    session, user_id = db_session
    
    # Add some coins
    portfolio_manager.add_coin(
        coin="BTC",
        amount=Decimal("1"),
        purchase_price=Decimal("50000"),
        purchase_date=datetime(2024, 1, 1)
    )
    
    portfolio_manager.add_coin(
        coin="ETH",
        amount=Decimal("10"),
        purchase_price=Decimal("2000"),
        purchase_date=datetime(2024, 1, 1)
    )
    
    # Mock price fetching
    with patch.object(portfolio_manager.data_collector, 'fetch_price', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = lambda coin: {
            "BTC": 60000.0,
            "ETH": 2500.0
        }.get(coin)
        
        portfolio = await portfolio_manager.get_portfolio()
        
        assert len(portfolio.holdings) == 2
        assert portfolio.total_invested == Decimal("70000")  # 50000 + 20000
        assert portfolio.total_value == Decimal("85000")  # 60000 + 25000
        assert portfolio.total_profit_loss == Decimal("15000")
        assert portfolio.total_profit_loss_percent == pytest.approx(21.43, rel=0.01)


def test_get_trade_history(portfolio_manager, db_session):
    """Test getting trade history."""
    session, user_id = db_session
    
    # Add and remove some coins
    holding_id1 = portfolio_manager.add_coin(
        coin="BTC",
        amount=Decimal("1"),
        purchase_price=Decimal("50000"),
        purchase_date=datetime(2024, 1, 1)
    )
    
    holding_id2 = portfolio_manager.add_coin(
        coin="ETH",
        amount=Decimal("10"),
        purchase_price=Decimal("2000"),
        purchase_date=datetime(2024, 1, 15)
    )
    
    portfolio_manager.remove_coin(
        holding_id=holding_id1,
        sale_price=Decimal("55000"),
        sale_date=datetime(2024, 2, 1)
    )
    
    # Get trade history
    trades = portfolio_manager.get_trade_history()
    
    assert len(trades) == 3  # 2 buys + 1 sell
    assert trades[0].type == "sell"  # Most recent first
    assert trades[0].coin == "BTC"
    assert trades[1].type == "buy"
    assert trades[1].coin == "ETH"
    assert trades[2].type == "buy"
    assert trades[2].coin == "BTC"


# ============================================================================
# Property-Based Tests
# ============================================================================

@given(
    coin=coin_strategy,
    amount=amount_strategy,
    purchase_price=price_strategy,
    purchase_date=date_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_37_portfolio_addition(coin, amount, purchase_price, purchase_date):
    """
    Feature: crypto-analysis-system, Property 37: Portföy Ekleme
    
    Herhangi bir geçerli coin ve miktar için, portföye eklenebilmeli ve 
    alış detayları kaydedilmelidir.
    
    Validates: Gereksinim 17.1, 17.2
    """
    # Create fresh database session for each test
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test user
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    user_id = user.id
    
    # Create portfolio manager
    portfolio_manager = PortfolioManager(session, user_id)
    
    # Add coin to portfolio
    holding_id = portfolio_manager.add_coin(
        coin=coin,
        amount=amount,
        purchase_price=purchase_price,
        purchase_date=purchase_date
    )
    
    # Verify holding was created
    assert holding_id is not None
    assert isinstance(holding_id, str)
    
    # Verify holding in database
    holding = session.query(PortfolioHolding).filter_by(id=holding_id).first()
    assert holding is not None
    assert holding.coin == coin.upper()
    assert holding.amount == amount
    assert holding.purchase_price == purchase_price
    assert holding.purchase_date == purchase_date
    assert holding.is_active == True
    assert holding.user_id == user_id
    
    # Verify trade history was created
    trade = session.query(TradeHistory).filter_by(
        holding_id=holding_id,
        type="buy"
    ).first()
    assert trade is not None
    assert trade.coin == coin.upper()
    assert trade.amount == amount
    assert trade.price == purchase_price
    assert trade.date == purchase_date
    assert trade.profit_loss is None  # No profit/loss on buy
    
    # Cleanup
    session.close()


@pytest.mark.asyncio
@given(
    coin=coin_strategy,
    amount=amount_strategy,
    purchase_price=price_strategy,
    current_price_multiplier=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100, deadline=None)
async def test_property_38_portfolio_calculations(
    coin,
    amount,
    purchase_price,
    current_price_multiplier
):
    """
    Feature: crypto-analysis-system, Property 38: Portföy Hesaplamaları
    
    Herhangi bir portföy holding'i için, güncel fiyat, toplam değer ve 
    kar/zarar yüzdesi hesaplanmalıdır.
    
    Validates: Gereksinim 17.3
    """
    # Ensure valid price
    assume(purchase_price > 0)
    
    # Create fresh database session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test user
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    user_id = user.id
    
    # Create portfolio manager
    portfolio_manager = PortfolioManager(session, user_id)
    
    # Add coin to portfolio
    holding_id = portfolio_manager.add_coin(
        coin=coin,
        amount=amount,
        purchase_price=purchase_price,
        purchase_date=datetime.utcnow()
    )
    
    # Calculate current price
    current_price = float(purchase_price) * current_price_multiplier
    
    # Mock price fetching
    with patch.object(portfolio_manager.data_collector, 'fetch_price', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = current_price
        
        # Get portfolio
        portfolio = await portfolio_manager.get_portfolio()
        
        # Verify calculations
        assert len(portfolio.holdings) == 1
        holding = portfolio.holdings[0]
        
        # Check current price
        assert holding.current_price == pytest.approx(Decimal(str(current_price)), rel=0.0001)
        
        # Check current value
        expected_value = Decimal(str(current_price)) * amount
        assert holding.current_value == pytest.approx(expected_value, rel=0.0001)
        
        # Check profit/loss amount
        invested = purchase_price * amount
        expected_profit_loss = expected_value - invested
        assert holding.profit_loss_amount == pytest.approx(expected_profit_loss, rel=0.0001)
        
        # Check profit/loss percent
        expected_percent = float((expected_profit_loss / invested) * 100)
        assert holding.profit_loss_percent == pytest.approx(expected_percent, rel=0.01)
    
    # Cleanup
    session.close()


@pytest.mark.asyncio
@given(
    num_holdings=st.integers(min_value=1, max_value=5),
    amounts=st.lists(amount_strategy, min_size=1, max_size=5),
    purchase_prices=st.lists(price_strategy, min_size=1, max_size=5),
    current_price_multipliers=st.lists(st.floats(min_value=0.5, max_value=2.0), min_size=1, max_size=5)
)
@settings(max_examples=100, deadline=None)
async def test_property_39_portfolio_total_values(
    num_holdings,
    amounts,
    purchase_prices,
    current_price_multipliers
):
    """
    Feature: crypto-analysis-system, Property 39: Portföy Toplam Değerleri
    
    Herhangi bir portföy için, toplam değer ve toplam kar/zarar oranı 
    hesaplanmalıdır.
    
    Validates: Gereksinim 17.4
    """
    # Ensure we have enough data
    num_holdings = min(num_holdings, len(amounts), len(purchase_prices), len(current_price_multipliers))
    assume(num_holdings > 0)
    
    # Create fresh database session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test user
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    user_id = user.id
    
    # Create portfolio manager
    portfolio_manager = PortfolioManager(session, user_id)
    
    # Add multiple holdings
    holding_ids = []
    expected_total_invested = Decimal("0")
    expected_total_value = Decimal("0")
    price_map = {}
    
    for i in range(num_holdings):
        coin = SUPPORTED_COINS[i % len(SUPPORTED_COINS)]
        amount = amounts[i]
        purchase_price = purchase_prices[i]
        
        assume(purchase_price > 0)
        
        holding_id = portfolio_manager.add_coin(
            coin=coin,
            amount=amount,
            purchase_price=purchase_price,
            purchase_date=datetime.utcnow()
        )
        holding_ids.append(holding_id)
        
        # Calculate expected values
        current_price = float(purchase_price) * current_price_multipliers[i]
        price_map[coin] = current_price
        
        expected_total_invested += purchase_price * amount
        expected_total_value += Decimal(str(current_price)) * amount
    
    # Mock price fetching
    with patch.object(portfolio_manager.data_collector, 'fetch_price', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = lambda coin: price_map.get(coin)
        
        # Get portfolio
        portfolio = await portfolio_manager.get_portfolio()
        
        # Verify total calculations
        assert portfolio.total_invested == pytest.approx(expected_total_invested, rel=0.0001)
        assert portfolio.total_value == pytest.approx(expected_total_value, rel=0.0001)
        
        expected_profit_loss = expected_total_value - expected_total_invested
        assert portfolio.total_profit_loss == pytest.approx(expected_profit_loss, rel=0.0001)
        
        if expected_total_invested > 0:
            expected_percent = float((expected_profit_loss / expected_total_invested) * 100)
            assert portfolio.total_profit_loss_percent == pytest.approx(expected_percent, rel=0.01)
    
    # Cleanup
    session.close()


# ============================================================================
# Additional Unit Tests
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_total_value(portfolio_manager, db_session):
    """Test calculate_total_value method."""
    session, user_id = db_session
    
    # Add holdings
    portfolio_manager.add_coin(
        coin="BTC",
        amount=Decimal("1"),
        purchase_price=Decimal("50000"),
        purchase_date=datetime.utcnow()
    )
    
    # Mock price fetching
    with patch.object(portfolio_manager.data_collector, 'fetch_price', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = 60000.0
        
        total_value = await portfolio_manager.calculate_total_value()
        assert total_value == Decimal("60000")


@pytest.mark.asyncio
async def test_calculate_profit_loss(portfolio_manager, db_session):
    """Test calculate_profit_loss method."""
    session, user_id = db_session
    
    # Add holdings
    portfolio_manager.add_coin(
        coin="ETH",
        amount=Decimal("10"),
        purchase_price=Decimal("2000"),
        purchase_date=datetime.utcnow()
    )
    
    # Mock price fetching
    with patch.object(portfolio_manager.data_collector, 'fetch_price', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = 2500.0
        
        profit_loss = await portfolio_manager.calculate_profit_loss()
        
        assert profit_loss.total_invested == Decimal("20000")
        assert profit_loss.current_value == Decimal("25000")
        assert profit_loss.profit_loss_amount == Decimal("5000")
        assert profit_loss.profit_loss_percent == pytest.approx(25.0, rel=0.01)


@pytest.mark.asyncio
async def test_get_performance_history(portfolio_manager, db_session):
    """Test get_performance_history method."""
    session, user_id = db_session
    
    # Add holdings
    portfolio_manager.add_coin(
        coin="BTC",
        amount=Decimal("1"),
        purchase_price=Decimal("50000"),
        purchase_date=datetime.utcnow() - timedelta(days=10)
    )
    
    # Mock price fetching
    with patch.object(portfolio_manager.data_collector, 'fetch_price', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = 55000.0
        
        snapshots = await portfolio_manager.get_performance_history(days=7)
        
        assert len(snapshots) == 8  # 7 days + today
        assert all(isinstance(s.timestamp, datetime) for s in snapshots)
        assert all(isinstance(s.total_value, Decimal) for s in snapshots)
        assert all(isinstance(s.profit_loss_percent, float) for s in snapshots)


def test_coin_symbol_normalization(portfolio_manager):
    """Test that coin symbols are normalized to uppercase."""
    holding_id = portfolio_manager.add_coin(
        coin="btc",  # lowercase
        amount=Decimal("1"),
        purchase_price=Decimal("50000"),
        purchase_date=datetime.utcnow()
    )
    
    session = portfolio_manager.db
    holding = session.query(PortfolioHolding).filter_by(id=holding_id).first()
    assert holding.coin == "BTC"  # Should be uppercase
