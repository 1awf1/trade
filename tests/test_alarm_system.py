"""
Tests for Alarm System Engine.
Includes unit tests and property-based tests.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, User, Alarm as AlarmDB
from models.schemas import AlarmConfig, AlarmType, AlarmCondition
from engines.alarm_system import AlarmSystem


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test user
    user = User(
        id="test-user-1",
        email="test@example.com",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    
    yield session
    session.close()


@pytest.fixture
def alarm_system(db_session):
    """Create AlarmSystem instance."""
    return AlarmSystem(db_session)


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "test-user-1"


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Valid coins
SUPPORTED_COINS = ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", "DOGE", "AVAX", "MATIC"]

# Alarm type strategy
alarm_type_strategy = st.sampled_from([AlarmType.PRICE, AlarmType.SIGNAL, AlarmType.SUCCESS_PROBABILITY])

# Alarm condition strategy
alarm_condition_strategy = st.sampled_from([AlarmCondition.ABOVE, AlarmCondition.BELOW, AlarmCondition.EQUALS])

# Notification channels strategy
notification_channels_strategy = st.lists(
    st.sampled_from(["email", "web_push"]),
    min_size=1,
    max_size=2,
    unique=True
)

# Threshold strategy (depends on alarm type)
def threshold_strategy(alarm_type):
    """Generate appropriate threshold based on alarm type."""
    if alarm_type == AlarmType.PRICE:
        return st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False)
    elif alarm_type == AlarmType.SUCCESS_PROBABILITY:
        return st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
    else:  # SIGNAL
        return st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)


# ============================================================================
# Unit Tests
# ============================================================================

def test_create_alarm_basic(alarm_system, test_user_id):
    """Test basic alarm creation."""
    config = AlarmConfig(
        coin="BTC",
        type=AlarmType.PRICE,
        condition=AlarmCondition.ABOVE,
        threshold=50000.0,
        notification_channels=["email"],
        auto_disable=False,
        active=True
    )
    
    alarm_id = alarm_system.create_alarm(test_user_id, config)
    
    assert alarm_id is not None
    assert len(alarm_id) > 0
    
    # Verify alarm was created
    alarm = alarm_system.get_alarm(alarm_id)
    assert alarm is not None
    assert alarm.config.coin == "BTC"
    assert alarm.config.type == AlarmType.PRICE
    assert alarm.config.threshold == 50000.0


def test_list_alarms(alarm_system, test_user_id):
    """Test listing alarms."""
    # Create multiple alarms
    for i in range(3):
        config = AlarmConfig(
            coin="BTC",
            type=AlarmType.PRICE,
            condition=AlarmCondition.ABOVE,
            threshold=50000.0 + i * 1000,
            notification_channels=["email"],
            auto_disable=False,
            active=True
        )
        alarm_system.create_alarm(test_user_id, config)
    
    # List all alarms
    alarms = alarm_system.list_alarms(test_user_id)
    assert len(alarms) == 3


def test_update_alarm(alarm_system, test_user_id):
    """Test updating an alarm."""
    config = AlarmConfig(
        coin="BTC",
        type=AlarmType.PRICE,
        condition=AlarmCondition.ABOVE,
        threshold=50000.0,
        notification_channels=["email"],
        auto_disable=False,
        active=True
    )
    
    alarm_id = alarm_system.create_alarm(test_user_id, config)
    
    # Update threshold
    alarm_system.update_alarm(alarm_id, {"threshold": 55000.0})
    
    # Verify update
    alarm = alarm_system.get_alarm(alarm_id)
    assert alarm.config.threshold == 55000.0


def test_delete_alarm(alarm_system, test_user_id):
    """Test deleting an alarm."""
    config = AlarmConfig(
        coin="BTC",
        type=AlarmType.PRICE,
        condition=AlarmCondition.ABOVE,
        threshold=50000.0,
        notification_channels=["email"],
        auto_disable=False,
        active=True
    )
    
    alarm_id = alarm_system.create_alarm(test_user_id, config)
    
    # Delete alarm
    alarm_system.delete_alarm(alarm_id)
    
    # Verify deletion
    alarm = alarm_system.get_alarm(alarm_id)
    assert alarm is None


def test_check_alarms_price_above(alarm_system, test_user_id):
    """Test alarm checking for price above condition."""
    config = AlarmConfig(
        coin="BTC",
        type=AlarmType.PRICE,
        condition=AlarmCondition.ABOVE,
        threshold=50000.0,
        notification_channels=["email"],
        auto_disable=False,
        active=True
    )
    
    alarm_system.create_alarm(test_user_id, config)
    
    # Check with price above threshold
    current_data = {
        "BTC": {"price": 51000.0, "signal": None, "success_probability": None}
    }
    
    triggered = alarm_system.check_alarms(current_data)
    assert len(triggered) == 1
    assert triggered[0].trigger_data["coin"] == "BTC"


def test_check_alarms_price_below(alarm_system, test_user_id):
    """Test alarm checking for price below condition."""
    config = AlarmConfig(
        coin="BTC",
        type=AlarmType.PRICE,
        condition=AlarmCondition.BELOW,
        threshold=50000.0,
        notification_channels=["email"],
        auto_disable=False,
        active=True
    )
    
    alarm_system.create_alarm(test_user_id, config)
    
    # Check with price below threshold
    current_data = {
        "BTC": {"price": 49000.0, "signal": None, "success_probability": None}
    }
    
    triggered = alarm_system.check_alarms(current_data)
    assert len(triggered) == 1


def test_alarm_auto_disable(alarm_system, test_user_id):
    """Test alarm auto-disable after triggering."""
    config = AlarmConfig(
        coin="BTC",
        type=AlarmType.PRICE,
        condition=AlarmCondition.ABOVE,
        threshold=50000.0,
        notification_channels=["email"],
        auto_disable=True,
        active=True
    )
    
    alarm_id = alarm_system.create_alarm(test_user_id, config)
    
    # Trigger alarm
    current_data = {
        "BTC": {"price": 51000.0, "signal": None, "success_probability": None}
    }
    
    triggered = alarm_system.check_alarms(current_data)
    assert len(triggered) == 1
    
    # Verify alarm is now inactive
    alarm = alarm_system.get_alarm(alarm_id)
    assert alarm.config.active == False


def test_alarm_history(alarm_system, test_user_id):
    """Test alarm history recording."""
    config = AlarmConfig(
        coin="BTC",
        type=AlarmType.PRICE,
        condition=AlarmCondition.ABOVE,
        threshold=50000.0,
        notification_channels=["email"],
        auto_disable=False,
        active=True
    )
    
    alarm_id = alarm_system.create_alarm(test_user_id, config)
    
    # Trigger alarm
    current_data = {
        "BTC": {"price": 51000.0, "signal": None, "success_probability": None}
    }
    
    alarm_system.check_alarms(current_data)
    
    # Check history
    history = alarm_system.get_alarm_history(alarm_id)
    assert len(history) == 1
    assert history[0].trigger_value == 51000.0


# ============================================================================
# Property-Based Tests
# ============================================================================

@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    alarm_type=alarm_type_strategy,
    condition=alarm_condition_strategy,
    notification_channels=notification_channels_strategy,
    auto_disable=st.booleans(),
    active=st.booleans()
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_44_alarm_creation(
    coin, alarm_type, condition, notification_channels, auto_disable, active
):
    """
    Feature: crypto-analysis-system, Property 44: Alarm Oluşturma
    Herhangi bir geçerli alarm konfigürasyonu (fiyat, sinyal veya başarı ihtimali bazlı) için,
    alarm oluşturulabilmelidir.
    
    Validates: Requirement 18.1, 18.2, 18.3
    """
    # Create fresh database session for each test
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    try:
        # Create test user
        user = User(
            id="test-user-prop-44",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        alarm_system = AlarmSystem(db_session)
        
        # Generate appropriate threshold
        if alarm_type == AlarmType.PRICE:
            threshold = 50000.0
        elif alarm_type == AlarmType.SUCCESS_PROBABILITY:
            threshold = 75.0
        else:
            threshold = 50.0
        
        config = AlarmConfig(
            coin=coin,
            type=alarm_type,
            condition=condition,
            threshold=threshold,
            notification_channels=notification_channels,
            auto_disable=auto_disable,
            active=active
        )
        
        # Create alarm
        alarm_id = alarm_system.create_alarm("test-user-prop-44", config)
        
        # Verify alarm was created
        assert alarm_id is not None
        assert len(alarm_id) > 0
        
        # Verify alarm can be retrieved
        alarm = alarm_system.get_alarm(alarm_id)
        assert alarm is not None
        assert alarm.config.coin == coin
        assert alarm.config.type == alarm_type
        assert alarm.config.condition == condition
        assert alarm.config.threshold == threshold
        assert alarm.config.notification_channels == notification_channels
        assert alarm.config.auto_disable == auto_disable
        assert alarm.config.active == active
        
        # Verify alarm appears in list
        alarms = alarm_system.list_alarms("test-user-prop-44")
        assert len(alarms) >= 1
        assert any(a.id == alarm_id for a in alarms)
        
    finally:
        db_session.close()


@given(
    coin=st.sampled_from(SUPPORTED_COINS),
    alarm_type=alarm_type_strategy,
    condition=alarm_condition_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_45_alarm_triggering(coin, alarm_type, condition):
    """
    Feature: crypto-analysis-system, Property 45: Alarm Tetikleme
    Herhangi bir alarm koşulu gerçekleştiğinde, kullanıcıya bildirim gönderilmelidir.
    
    Validates: Requirement 18.4
    """
    # Create fresh database session for each test
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    try:
        # Create test user
        user = User(
            id="test-user-prop-45",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        alarm_system = AlarmSystem(db_session)
        
        # Set threshold and test value based on condition
        if alarm_type == AlarmType.PRICE:
            threshold = 50000.0
            if condition == AlarmCondition.ABOVE:
                test_value = 51000.0
            elif condition == AlarmCondition.BELOW:
                test_value = 49000.0
            else:  # EQUALS
                test_value = 50000.0
        elif alarm_type == AlarmType.SUCCESS_PROBABILITY:
            threshold = 75.0
            if condition == AlarmCondition.ABOVE:
                test_value = 80.0
            elif condition == AlarmCondition.BELOW:
                test_value = 70.0
            else:  # EQUALS
                test_value = 75.0
        else:  # SIGNAL
            threshold = 50.0
            if condition == AlarmCondition.ABOVE:
                test_value = 60.0
            elif condition == AlarmCondition.BELOW:
                test_value = 40.0
            else:  # EQUALS
                test_value = 50.0
        
        config = AlarmConfig(
            coin=coin,
            type=alarm_type,
            condition=condition,
            threshold=threshold,
            notification_channels=["email"],
            auto_disable=False,
            active=True
        )
        
        alarm_id = alarm_system.create_alarm("test-user-prop-45", config)
        
        # Prepare current data
        current_data = {coin: {}}
        if alarm_type == AlarmType.PRICE:
            current_data[coin]["price"] = test_value
            current_data[coin]["signal"] = None
            current_data[coin]["success_probability"] = None
        elif alarm_type == AlarmType.SUCCESS_PROBABILITY:
            current_data[coin]["price"] = None
            current_data[coin]["signal"] = None
            current_data[coin]["success_probability"] = test_value
        else:  # SIGNAL
            current_data[coin]["price"] = None
            current_data[coin]["signal"] = test_value
            current_data[coin]["success_probability"] = None
        
        # Check alarms
        triggered = alarm_system.check_alarms(current_data)
        
        # Verify alarm was triggered
        assert len(triggered) >= 1
        assert any(t.alarm.id == alarm_id for t in triggered)
        
        # Verify trigger data
        triggered_alarm = next(t for t in triggered if t.alarm.id == alarm_id)
        assert triggered_alarm.trigger_data["coin"] == coin
        assert triggered_alarm.trigger_data["type"] == alarm_type.value
        assert triggered_alarm.trigger_data["condition"] == condition.value
        
        # Verify alarm was updated
        alarm = alarm_system.get_alarm(alarm_id)
        assert alarm.last_triggered is not None
        assert alarm.trigger_count >= 1
        
        # Verify history was recorded
        history = alarm_system.get_alarm_history(alarm_id)
        assert len(history) >= 1
        
    finally:
        db_session.close()
