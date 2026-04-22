"""
Database initialization script for PostgreSQL
Creates all tables for the AIGP application.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from common.db import engine, Base
from common import models  # noqa: F401
from govercore.models_db import *  # noqa: F401, F403

def init_database():
    """Initialize the database with all tables."""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Verify connection
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {str(e)}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. Environment variables are set correctly")
        print("3. Database exists and is accessible")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
