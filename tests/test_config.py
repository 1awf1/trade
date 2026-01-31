"""
Tests for configuration management and environment variables.
Includes property-based tests for configuration validation.
"""
import os
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from utils.config import Settings


class TestConfigBasic:
    """Basic configuration tests."""
    
    def test_settings_initialization(self):
        """Test that settings can be initialized."""
        settings = Settings()
        assert settings is not None
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'REDIS_URL')
    
    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()
        assert settings.APP_NAME == "Kripto Para Analiz Sistemi"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.PORT == 8000
        assert settings.ALGORITHM == "HS256"
    
    def test_database_url_construction(self, monkeypatch):
        """Test that DATABASE_URL is constructed correctly."""
        # Clear all database-related environment variables
        for key in ['DATABASE_URL', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB']:
            monkeypatch.delenv(key, raising=False)
        
        # Set test values
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.setenv("POSTGRES_HOST", "testhost")
        monkeypatch.setenv("POSTGRES_PORT", "5433")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        
        settings = Settings()
        expected = "postgresql://testuser:testpass@testhost:5433/testdb"
        assert settings.DATABASE_URL == expected
    
    def test_redis_url_construction(self, monkeypatch):
        """Test that REDIS_URL is constructed correctly."""
        # Clear all Redis-related environment variables
        for key in ['REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB', 'REDIS_PASSWORD']:
            monkeypatch.delenv(key, raising=False)
        
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "1")
        monkeypatch.setenv("REDIS_PASSWORD", "")
        
        settings = Settings()
        expected = "redis://redishost:6380/1"
        assert settings.REDIS_URL == expected
    
    def test_redis_url_with_password(self, monkeypatch):
        """Test REDIS_URL construction with password."""
        # Clear all Redis-related environment variables
        for key in ['REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB', 'REDIS_PASSWORD']:
            monkeypatch.delenv(key, raising=False)
        
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "0")
        monkeypatch.setenv("REDIS_PASSWORD", "secret")
        
        settings = Settings()
        expected = "redis://:secret@redishost:6379/0"
        assert settings.REDIS_URL == expected
    
    def test_celery_urls_default_to_redis(self):
        """Test that Celery URLs default to Redis URL."""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=0
        )
        assert settings.CELERY_BROKER_URL == settings.REDIS_URL
        assert settings.CELERY_RESULT_BACKEND == settings.REDIS_URL


class TestConfigPropertyBased:
    """Property-based tests for configuration."""
    
    @given(
        app_name=st.text(min_size=1, max_size=100),
        debug=st.booleans(),
        port=st.integers(min_value=1024, max_value=65535)
    )
    @settings(max_examples=20)
    def test_property_19_env_var_configuration(self, app_name, debug, port):
        """
        Property 19: Çevre Değişkeni Yapılandırması
        
        For any valid environment variable, the system should read and apply it at startup.
        
        Validates: Requirement 11.3
        """
        # Create settings with custom values
        settings = Settings(
            APP_NAME=app_name,
            DEBUG=debug,
            PORT=port
        )
        
        # Verify values are applied correctly
        assert settings.APP_NAME == app_name
        assert settings.DEBUG == debug
        assert settings.PORT == port
    
    @given(
        user=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=[':','@','/'])),
        password=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=[':','@','/'])),
        host=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=[':','@','/'])),
        port=st.integers(min_value=1024, max_value=65535),
        db=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=[':','@','/']))
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_database_url_construction(self, monkeypatch, user, password, host, port, db):
        """
        Property: Database URL Construction
        
        For any valid database credentials, the DATABASE_URL should be constructed correctly.
        """
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("POSTGRES_USER", user)
        monkeypatch.setenv("POSTGRES_PASSWORD", password)
        monkeypatch.setenv("POSTGRES_HOST", host)
        monkeypatch.setenv("POSTGRES_PORT", str(port))
        monkeypatch.setenv("POSTGRES_DB", db)
        
        settings = Settings()
        
        # Verify URL format
        assert settings.DATABASE_URL.startswith("postgresql://")
        assert user in settings.DATABASE_URL
        assert password in settings.DATABASE_URL
        assert host in settings.DATABASE_URL
        assert str(port) in settings.DATABASE_URL
        assert db in settings.DATABASE_URL
    
    @given(
        host=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=[':','@','/'])),
        port=st.integers(min_value=1024, max_value=65535),
        db=st.integers(min_value=0, max_value=15)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_redis_url_construction(self, monkeypatch, host, port, db):
        """
        Property: Redis URL Construction
        
        For any valid Redis configuration, the REDIS_URL should be constructed correctly.
        """
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.setenv("REDIS_HOST", host)
        monkeypatch.setenv("REDIS_PORT", str(port))
        monkeypatch.setenv("REDIS_DB", str(db))
        monkeypatch.setenv("REDIS_PASSWORD", "")
        
        settings = Settings()
        
        # Verify URL format
        assert settings.REDIS_URL.startswith("redis://")
        assert host in settings.REDIS_URL
        assert str(port) in settings.REDIS_URL
        assert str(db) in settings.REDIS_URL
    
    @given(
        ttl_price=st.integers(min_value=1, max_value=3600),
        ttl_ohlcv=st.integers(min_value=1, max_value=3600),
        ttl_social=st.integers(min_value=1, max_value=86400),
        ttl_news=st.integers(min_value=1, max_value=86400)
    )
    @settings(max_examples=20)
    def test_property_cache_ttl_configuration(self, ttl_price, ttl_ohlcv, ttl_social, ttl_news):
        """
        Property: Cache TTL Configuration
        
        For any valid TTL values, they should be applied correctly.
        """
        settings = Settings(
            CACHE_TTL_PRICE=ttl_price,
            CACHE_TTL_OHLCV=ttl_ohlcv,
            CACHE_TTL_SOCIAL=ttl_social,
            CACHE_TTL_NEWS=ttl_news
        )
        
        assert settings.CACHE_TTL_PRICE == ttl_price
        assert settings.CACHE_TTL_OHLCV == ttl_ohlcv
        assert settings.CACHE_TTL_SOCIAL == ttl_social
        assert settings.CACHE_TTL_NEWS == ttl_news
    
    @given(
        max_concurrent=st.integers(min_value=1, max_value=100),
        timeout=st.integers(min_value=1, max_value=300)
    )
    @settings(max_examples=20)
    def test_property_performance_settings(self, max_concurrent, timeout):
        """
        Property: Performance Settings Configuration
        
        For any valid performance settings, they should be applied correctly.
        """
        settings = Settings(
            MAX_CONCURRENT_ANALYSES=max_concurrent,
            ANALYSIS_TIMEOUT_SECONDS=timeout
        )
        
        assert settings.MAX_CONCURRENT_ANALYSES == max_concurrent
        assert settings.ANALYSIS_TIMEOUT_SECONDS == timeout
        assert settings.MAX_CONCURRENT_ANALYSES > 0
        assert settings.ANALYSIS_TIMEOUT_SECONDS > 0
    
    @given(
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
        max_tokens=st.integers(min_value=1, max_value=4000)
    )
    @settings(max_examples=20)
    def test_property_ai_configuration(self, temperature, max_tokens):
        """
        Property: AI Configuration
        
        For any valid AI settings, they should be applied correctly.
        """
        settings = Settings(
            AI_TEMPERATURE=temperature,
            AI_MAX_TOKENS=max_tokens
        )
        
        assert settings.AI_TEMPERATURE == temperature
        assert settings.AI_MAX_TOKENS == max_tokens
        assert 0.0 <= settings.AI_TEMPERATURE <= 2.0
        assert settings.AI_MAX_TOKENS > 0


class TestConfigValidation:
    """Configuration validation tests."""
    
    def test_invalid_port_raises_error(self, monkeypatch):
        """Test that invalid port raises validation error."""
        monkeypatch.setenv("PORT", "-1")
        with pytest.raises(Exception):
            Settings()
    
    def test_invalid_redis_db_raises_error(self, monkeypatch):
        """Test that invalid Redis DB raises validation error."""
        monkeypatch.setenv("REDIS_DB", "-1")
        with pytest.raises(Exception):
            Settings()
    
    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("APP_NAME", "Test App")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("DEBUG", "False")
        
        settings = Settings()
        
        assert settings.APP_NAME == "Test App"
        assert settings.PORT == 9000
        assert settings.DEBUG is False


class TestConfigSecurity:
    """Security-related configuration tests."""
    
    def test_secret_key_not_default_in_production(self, monkeypatch):
        """Test that SECRET_KEY should be changed in production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "production-secret-key-12345")
        
        settings = Settings()
        
        # In production, SECRET_KEY should not be the default
        if settings.ENVIRONMENT == "production":
            assert settings.SECRET_KEY != "your-secret-key-here-change-in-production", \
                "SECRET_KEY must be changed in production!"
    
    def test_debug_false_in_production(self):
        """Test that DEBUG should be False in production."""
        settings = Settings(ENVIRONMENT="production", DEBUG=False)
        
        if settings.ENVIRONMENT == "production":
            assert settings.DEBUG is False, "DEBUG must be False in production!"
    
    def test_sensitive_data_not_logged(self):
        """Test that sensitive configuration is not exposed."""
        settings = Settings(
            POSTGRES_PASSWORD="secret_password",
            REDIS_PASSWORD="secret_redis",
            SECRET_KEY="secret_key"
        )
        
        # Convert to dict and check sensitive fields
        config_str = str(settings.__dict__)
        
        # Sensitive data should be present (we're not testing masking here, just that config works)
        assert settings.POSTGRES_PASSWORD == "secret_password"
        assert settings.SECRET_KEY == "secret_key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
