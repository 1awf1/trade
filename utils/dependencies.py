"""
Dependency checker for application startup.
Validates that all required services and libraries are available.
"""
import sys
from typing import List, Tuple
from utils.logger import setup_logger

logger = setup_logger(__name__)


def check_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if all required dependencies are available.
    
    Returns:
        Tuple of (all_ok: bool, missing_dependencies: List[str])
    """
    missing = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        missing.append(f"Python 3.10+ required (current: {sys.version_info.major}.{sys.version_info.minor})")
    
    # Check required packages
    required_packages = [
        'fastapi',
        'uvicorn',
        'pandas',
        'numpy',
        'talib',
        'hypothesis',
        'psycopg2',
        'sqlalchemy',
        'redis',
        'celery',
        'transformers',
        'requests',
        'aiohttp',
        'dotenv',
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(f"Python package: {package}")
    
    return len(missing) == 0, missing


def check_database_connection() -> bool:
    """
    Check if database connection is available.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import create_engine
        from utils.config import settings
        
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def check_redis_connection() -> bool:
    """
    Check if Redis connection is available.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        import redis
        from utils.config import settings
        
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


def startup_checks() -> None:
    """
    Perform all startup checks and report results.
    Exits application if critical dependencies are missing.
    """
    logger.info("Performing startup dependency checks...")
    
    # Check dependencies
    all_ok, missing = check_dependencies()
    
    if not all_ok:
        logger.error("Missing dependencies:")
        for dep in missing:
            logger.error(f"  - {dep}")
        logger.error("Please install missing dependencies before starting the application.")
        sys.exit(1)
    
    logger.info("All required dependencies are installed.")
    
    # Check database (non-critical for initial setup)
    if check_database_connection():
        logger.info("Database connection: OK")
    else:
        logger.warning("Database connection: FAILED (will retry on first use)")
    
    # Check Redis (non-critical for initial setup)
    if check_redis_connection():
        logger.info("Redis connection: OK")
    else:
        logger.warning("Redis connection: FAILED (will retry on first use)")
    
    logger.info("Startup checks completed.")
