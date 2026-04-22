"""
Database configuration - PostgreSQL setup
This file provides database connection for modules that need direct access.
For most cases, use the centralized configuration from common.db
"""
from common.db import engine, SessionLocal, Base

# Re-export for backward compatibility
__all__ = ['engine', 'SessionLocal', 'Base']
