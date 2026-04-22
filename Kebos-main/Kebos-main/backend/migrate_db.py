#!/usr/bin/env python3
"""
Database migration script for PostgreSQL
Handles database migrations using Alembic.
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_database_connection():
    """Check if database connection is working."""
    try:
        import psycopg2
        from common.db import DB_URL
        
        # Extract connection details from URL
        url_parts = DB_URL.replace('postgresql://', '').split('@')
        user_pass = url_parts[0].split(':')
        host_db = url_parts[1].split('/')
        host_port = host_db[0].split(':')
        
        conn = psycopg2.connect(
            host=host_port[0],
            port=host_port[1] if len(host_port) > 1 else 5432,
            database=host_db[1],
            user=user_pass[0],
            password=user_pass[1]
        )
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def create_initial_migration():
    """Create initial migration if none exists."""
    if not os.path.exists("alembic/versions"):
        print("📁 Creating initial migration...")
        return run_command(
            "alembic revision --autogenerate -m 'Initial migration'",
            "Creating initial migration"
        )
    return True

def main():
    """Main migration function."""
    print("🚀 Starting PostgreSQL Database Migration")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"  {var}=your_value")
        sys.exit(1)
    
    # Check database connection
    if not check_database_connection():
        print("\nPlease ensure PostgreSQL is running and accessible.")
        sys.exit(1)
    
    # Initialize Alembic if not already done
    if not os.path.exists("alembic.ini"):
        print("❌ alembic.ini not found. Please run 'alembic init alembic' first.")
        sys.exit(1)
    
    # Create initial migration if needed
    if not create_initial_migration():
        sys.exit(1)
    
    # Run migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        sys.exit(1)
    
    print("\n🎉 Database migration completed successfully!")
    print("\nNext steps:")
    print("1. Verify all tables were created: python init_db.py")
    print("2. Start the application: uvicorn main:app --reload")
    print("3. Check the API documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 