"""Test database connection"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Environment variables loaded:")
    print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
    print(f"POSTGRES_HOST: {os.getenv('POSTGRES_HOST')}")
    print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")
    print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print()
    
    print("Testing database connection...")
    from common.db import engine, SessionLocal
    from sqlalchemy import text
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 'Connection successful!' as status;"))
        row = result.fetchone()
        print(f"✅ Database connection successful: {row[0]}")
        
    # Test session
    db = SessionLocal()
    try:
        print("✅ Database session created successfully")
    finally:
        db.close()
        
    print("\n🎉 All database tests passed!")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc()
