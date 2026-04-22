"""Test messaging module imports"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

try:
    print("Testing database import...")
    from db import Base, engine, SessionLocal
    print("✅ db.py imports successful")
    
    print("\nTesting messaging module...")
    from messaging import DB_AVAILABLE
    print(f"✅ messaging module loaded, DB_AVAILABLE: {DB_AVAILABLE}")
    
    if not DB_AVAILABLE:
        print("❌ Database models are reported as not available")
        # Try to understand why
        try:
            from db import Base, engine, SessionLocal
            print("✅ But direct import from db.py works fine!")
        except ImportError as e:
            print(f"❌ Direct import from db.py failed: {e}")
    else:
        print("✅ Database models are available!")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
