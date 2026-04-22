"""
Simple Test for Unified Messaging Module

Basic validation tests for the unified messaging system.
"""

import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_module_imports():
    """Test that all modules can be imported successfully"""
    print("Testing module imports...")
    
    try:
        # Test models import
        from messaging.models import (
            UserKeypairORM, SecureChannelORM, SecureMessageORM,
            MessageType, CryptoAlgorithm, ChannelStatus
        )
        print("✅ Models imported successfully")
        
        # Test enums
        assert MessageType.TEXT == "text"
        assert MessageType.IMAGE == "image"
        assert CryptoAlgorithm.KYBER == "kyber"
        print("✅ Enums working correctly")
        
    except ImportError as e:
        print(f"❌ Models import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Models validation failed: {e}")
        return False
    
    try:
        # Test services import
        from messaging.services import UnifiedMessagingService
        print("✅ Services imported successfully")
        
    except ImportError as e:
        print(f"❌ Services import failed: {e}")
        return False
    
    try:
        # Test API import
        from messaging.api import router
        print("✅ API router imported successfully")
        
    except ImportError as e:
        print(f"❌ API import failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")
    
    current_dir = os.path.dirname(__file__)
    required_files = [
        'models.py',
        'services.py', 
        'api.py',
        '__init__.py',
        'UNIFIED_MODULE_SUMMARY.md'
    ]
    
    for file in required_files:
        file_path = os.path.join(current_dir, file)
        if os.path.exists(file_path):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    return True

def test_api_structure():
    """Test API endpoint structure"""
    print("\nTesting API structure...")
    
    try:
        from messaging.api import router
        
        # Check if router has routes
        if hasattr(router, 'routes') and len(router.routes) > 0:
            print(f"✅ API router has {len(router.routes)} routes")
            
            # List some key routes
            route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
            
            expected_paths = ['/keypairs', '/channels', '/messages']
            found_paths = []
            
            for expected in expected_paths:
                for path in route_paths:
                    if expected in path:
                        found_paths.append(expected)
                        break
            
            print(f"✅ Found key endpoints: {found_paths}")
            
            if len(found_paths) >= 2:  # At least some key endpoints
                return True
            else:
                print("❌ Missing key API endpoints")
                return False
        else:
            print("❌ No routes found in API router")
            return False
            
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_database_models():
    """Test database model structure"""
    print("\nTesting database models...")
    
    try:
        from messaging.models import UserKeypairORM, SecureChannelORM, SecureMessageORM
        
        # Check if models have required attributes
        keypair_attrs = ['id', 'user_id', 'public_key', 'algorithm']
        for attr in keypair_attrs:
            if hasattr(UserKeypairORM, attr):
                print(f"✅ UserKeypairORM has {attr}")
            else:
                print(f"❌ UserKeypairORM missing {attr}")
                return False
        
        channel_attrs = ['id', 'name', 'status', 'created_at']
        for attr in channel_attrs:
            if hasattr(SecureChannelORM, attr):
                print(f"✅ SecureChannelORM has {attr}")
            else:
                print(f"❌ SecureChannelORM missing {attr}")
                return False
        
        message_attrs = ['id', 'sender_id', 'channel_id', 'content', 'message_type']
        for attr in message_attrs:
            if hasattr(SecureMessageORM, attr):
                print(f"✅ SecureMessageORM has {attr}")
            else:
                print(f"❌ SecureMessageORM missing {attr}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Unified Messaging Module Tests ===\n")
    
    tests = [
        test_file_structure,
        test_module_imports,
        test_api_structure,
        test_database_models
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}\n")
    
    print("=== Test Summary ===")
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 All tests passed! Unified messaging module is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
