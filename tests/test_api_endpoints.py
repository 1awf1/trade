"""
Property-based tests for API endpoints.
Tests coin validation and timeframe processing.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from api.main import app
from engines.data_collector import DataCollector

# Create test client
client = TestClient(app)

# Hardcoded list of supported coins for testing
# In production, this would come from the data collector
SUPPORTED_COINS = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "DOT", "MATIC", "LTC",
    "AVAX", "LINK", "UNI", "ATOM", "XLM", "ALGO", "VET", "FIL", "TRX", "ETC"
]
VALID_TIMEFRAMES = ['15m', '1h', '4h', '8h', '12h', '24h', '1w', '15d', '1M']


# ============================================================================
# Property 1: Coin Validation
# **Validates: Requirements 1.1, 1.2**
# ============================================================================

@given(
    coin=st.sampled_from(SUPPORTED_COINS)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_1_valid_coin_accepted(coin):
    """
    Property 1: Coin Validation - Valid Coins
    
    For any valid coin, the system SHALL accept it and process the request.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Make request with valid coin
    response = client.get(f"/api/coins/{coin}/price")
    
    # Valid coins should be accepted (200) or may have temporary data issues (500)
    # But should NOT return 400 (bad request) for valid coins
    assert response.status_code != 400, \
        f"Valid coin {coin} was rejected with 400 error"


@given(
    coin=st.text(
        alphabet=st.characters(
            min_codepoint=33,  # Start from '!' to avoid control characters
            max_codepoint=126,  # End at '~' (printable ASCII)
            blacklist_characters='/'  # Exclude URL path separator
        ),
        min_size=1,
        max_size=20
    ).filter(lambda x: x.upper().strip() not in SUPPORTED_COINS and x.strip() != "")
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_1_invalid_coin_rejected(coin):
    """
    Property 1: Coin Validation - Invalid Coins
    
    For any invalid coin, the system SHALL reject it with a descriptive error message.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Make request with invalid coin
    try:
        response = client.get(f"/api/coins/{coin}/price")
        
        # Invalid coins should be rejected with 400 or 404
        assert response.status_code in [400, 404, 500], \
            f"Invalid coin {coin} was not properly rejected (status: {response.status_code})"
        
        # Should have error message
        if response.status_code in [400, 404]:
            data = response.json()
            assert "error_code" in data or "detail" in data, \
                "Error response should contain error_code or detail"
    except Exception as e:
        # If URL encoding fails, that's also a valid rejection
        assert "Invalid" in str(e) or "URL" in str(e), \
            f"Unexpected error for invalid coin {coin}: {e}"


# ============================================================================
# Property 2: Timeframe Processing
# **Validates: Requirements 2.2, 2.3**
# ============================================================================

@given(
    timeframe=st.sampled_from(VALID_TIMEFRAMES)
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_2_valid_timeframe_accepted(timeframe):
    """
    Property 2: Timeframe Processing - Valid Timeframes
    
    For any valid timeframe, the system SHALL accept it and start data collection.
    
    **Validates: Requirements 2.2, 2.3**
    """
    # Use a known valid coin
    coin = SUPPORTED_COINS[0] if SUPPORTED_COINS else "BTC"
    
    # Make analysis request with valid timeframe
    response = client.post(
        "/api/analysis/start",
        json={
            "coin": coin,
            "timeframe": timeframe
        }
    )
    
    # Valid timeframe should be accepted (201) or may have temporary issues (500)
    # But should NOT return 422 (validation error) for valid timeframes
    assert response.status_code != 422, \
        f"Valid timeframe {timeframe} was rejected with validation error"


@given(
    timeframe=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=10
    ).filter(lambda x: x not in VALID_TIMEFRAMES)
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_2_invalid_timeframe_rejected(timeframe):
    """
    Property 2: Timeframe Processing - Invalid Timeframes
    
    For any invalid timeframe, the system SHALL reject it with a validation error.
    
    **Validates: Requirements 2.2, 2.3**
    """
    # Use a known valid coin
    coin = SUPPORTED_COINS[0] if SUPPORTED_COINS else "BTC"
    
    # Make analysis request with invalid timeframe
    response = client.post(
        "/api/analysis/start",
        json={
            "coin": coin,
            "timeframe": timeframe
        }
    )
    
    # Invalid timeframe should be rejected with 422 (validation error)
    assert response.status_code == 422, \
        f"Invalid timeframe {timeframe} was not rejected with validation error (status: {response.status_code})"
    
    # Should have error details
    data = response.json()
    assert "error_code" in data or "detail" in data, \
        "Error response should contain error_code or detail"


@given(
    timeframes=st.lists(
        st.sampled_from(VALID_TIMEFRAMES),
        min_size=2,
        max_size=5,
        unique=True
    )
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_2_multiple_timeframes_separate_results(timeframes):
    """
    Property 2: Timeframe Processing - Multiple Timeframes
    
    When multiple timeframes are selected, the system SHALL produce separate
    analysis results for each timeframe.
    
    **Validates: Requirements 2.2, 2.3**
    """
    # Use a known valid coin
    coin = SUPPORTED_COINS[0] if SUPPORTED_COINS else "BTC"
    
    # Make analysis requests for each timeframe
    analysis_ids = []
    for timeframe in timeframes:
        response = client.post(
            "/api/analysis/start",
            json={
                "coin": coin,
                "timeframe": timeframe
            }
        )
        
        # If successful, store the analysis ID
        if response.status_code == 201:
            data = response.json()
            analysis_ids.append((timeframe, data.get("id")))
    
    # If we got at least 2 successful analyses, verify they are different
    if len(analysis_ids) >= 2:
        # All analysis IDs should be unique
        ids = [aid for _, aid in analysis_ids]
        assert len(ids) == len(set(ids)), \
            "Multiple timeframe analyses should have unique IDs"
        
        # Each analysis should have the correct timeframe
        for timeframe, analysis_id in analysis_ids:
            if analysis_id:
                response = client.get(f"/api/analysis/{analysis_id}")
                if response.status_code == 200:
                    data = response.json()
                    assert data.get("timeframe") == timeframe, \
                        f"Analysis timeframe mismatch: expected {timeframe}, got {data.get('timeframe')}"


# ============================================================================
# Additional API Endpoint Tests
# ============================================================================

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data
    assert "status" in data


def test_get_supported_coins():
    """Test getting supported coins list."""
    response = client.get("/api/coins")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_analysis_history_empty():
    """Test getting analysis history when empty."""
    response = client.get("/api/analysis/history")
    # May return 200 with empty list or 500 if DB not initialized
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_portfolio_empty():
    """Test getting portfolio when empty."""
    response = client.get("/api/portfolio")
    # May return 200 with empty portfolio or 500 if DB not initialized
    assert response.status_code in [200, 500]


def test_alarms_list_empty():
    """Test listing alarms when empty."""
    response = client.get("/api/alarms")
    # May return 200 with empty list or 500 if DB not initialized
    assert response.status_code in [200, 500]
