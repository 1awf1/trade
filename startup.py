#!/usr/bin/env python3
"""
Application startup script.
Performs all necessary checks and initializations before starting the application.
"""
import sys
import time
from utils.dependencies import startup_checks, check_database_connection, check_redis_connection
from utils.logger import setup_logger
from migrate import run_migrations, check_migration_status

logger = setup_logger(__name__)


def wait_for_services(max_retries=30, retry_interval=2):
    """
    Wait for required services (database, redis) to be available.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_interval: Seconds to wait between retries
    
    Returns:
        True if all services are available, False otherwise
    """
    logger.info("Waiting for required services...")
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Service check attempt {attempt}/{max_retries}")
        
        db_ok = check_database_connection()
        redis_ok = check_redis_connection()
        
        if db_ok and redis_ok:
            logger.info("All services are available.")
            return True
        
        if not db_ok:
            logger.warning("Database not ready yet...")
        if not redis_ok:
            logger.warning("Redis not ready yet...")
        
        if attempt < max_retries:
            logger.info(f"Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
    
    logger.error("Services did not become available in time.")
    return False


def initialize_application():
    """
    Initialize the application.
    Performs all startup checks and migrations.
    
    Returns:
        True if initialization successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Starting Kripto Para Analiz Sistemi")
    logger.info("=" * 60)
    
    # Step 1: Check dependencies
    logger.info("\n[1/3] Checking dependencies...")
    try:
        startup_checks()
    except SystemExit:
        logger.error("Dependency check failed. Exiting.")
        return False
    
    # Step 2: Wait for services
    logger.info("\n[2/3] Waiting for services...")
    if not wait_for_services():
        logger.error("Required services are not available. Exiting.")
        return False
    
    # Step 3: Run migrations
    logger.info("\n[3/3] Running database migrations...")
    if not check_migration_status():
        logger.info("Database not initialized. Running migrations...")
        if not run_migrations():
            logger.error("Database migration failed. Exiting.")
            return False
    else:
        logger.info("Database already initialized. Skipping migrations.")
    
    logger.info("\n" + "=" * 60)
    logger.info("Application initialization completed successfully!")
    logger.info("=" * 60 + "\n")
    
    return True


if __name__ == "__main__":
    success = initialize_application()
    
    if success:
        logger.info("Starting application server...")
        # The actual server start will be handled by the Docker CMD or manual uvicorn command
        sys.exit(0)
    else:
        logger.error("Application initialization failed.")
        sys.exit(1)
