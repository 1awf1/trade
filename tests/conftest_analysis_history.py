"""
Pytest configuration for analysis history tests.
Sets up test database before any imports.
"""
import os
import sys

# Set test database URL before any imports
os.environ['DATABASE_URL'] = 'sqlite:///./test_analysis_history.db'
