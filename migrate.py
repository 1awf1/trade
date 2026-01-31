#!/usr/bin/env python3
"""
Database migration script.
Creates all necessary tables and indexes.
"""
import sys
from sqlalchemy import create_engine, text
from utils.config import settings
from utils.logger import setup_logger
from models.database import Base, engine

logger = setup_logger(__name__)


def run_migrations():
    """Run database migrations."""
    try:
        logger.info("Starting database migrations...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully.")
        
        # Create indexes
        with engine.connect() as conn:
            logger.info("Creating additional indexes...")
            
            # Add any custom indexes here
            # Example:
            # conn.execute(text("CREATE INDEX IF NOT EXISTS idx_custom ON table_name(column)"))
            
            conn.commit()
        
        logger.info("Database migrations completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def check_migration_status():
    """Check if migrations have been run."""
    try:
        with engine.connect() as conn:
            # Try to query a table that should exist
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            count = result.scalar()
            return count > 0
    except Exception as e:
        logger.warning(f"Could not check migration status: {e}")
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
