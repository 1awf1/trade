"""
Configuration management using Pydantic settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    APP_NAME: str = "Kripto Para Analiz Sistemi"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "crypto_analysis"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: Optional[str] = None
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: Optional[str] = None
    
    # Celery Configuration
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Keys - External Services
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    COINGECKO_API_KEY: str = ""
    
    # Social Media APIs
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_SECRET: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "CryptoAnalysisBot/1.0"
    
    # AI Configuration
    GEMINI_API_KEY: str = ""
    AI_MODEL: str = "gemini-2.5-flash"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 1000
    
    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@cryptoanalysis.com"
    
    # Cache Settings
    CACHE_TTL_PRICE: int = 60
    CACHE_TTL_OHLCV: int = 300
    CACHE_TTL_SOCIAL: int = 3600
    CACHE_TTL_NEWS: int = 3600
    CACHE_TTL_ANALYSIS: int = 600
    
    # Performance Settings
    MAX_CONCURRENT_ANALYSES: int = 10
    ANALYSIS_TIMEOUT_SECONDS: int = 30
    
    @field_validator('PORT')
    @classmethod
    def validate_port(cls, v):
        """Validate that PORT is in valid range."""
        if v < 0 or v > 65535:
            raise ValueError(f"PORT must be between 0 and 65535, got {v}")
        return v
    
    @field_validator('REDIS_DB')
    @classmethod
    def validate_redis_db(cls, v):
        """Validate that REDIS_DB is in valid range."""
        if v < 0 or v > 15:
            raise ValueError(f"REDIS_DB must be between 0 and 15, got {v}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Build DATABASE_URL if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        
        # Build REDIS_URL if not provided
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        
        # Build Celery URLs if not provided
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


# Create global settings instance
settings = Settings()
