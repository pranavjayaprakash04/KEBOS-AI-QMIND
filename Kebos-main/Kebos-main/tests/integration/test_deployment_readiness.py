#!/usr/bin/env python3
"""
Deployment Readiness Test for CTP with CatBoost Integration

This script tests critical components before deployment:
1. CatBoost model integration
2. API endpoints
3. Configuration validation
4. Dependencies check
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_model_files():
    """Test that all required CatBoost model files exist"""
    print("🧪 Testing model files...")
    
    model_dir = Path("backend/models")
    required_files = [
        "binary_classifier_basic.cbm",
        "multiclass_classifier_basic.cbm", 
        "scaler_basic.pkl",
        "label_encoder_basic.pkl",
        "model_metadata_basic.json"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = model_dir / file
        if not file_path.exists():
            missing_files.append(str(file_path))
        else:
            print(f"✅ Found: {file}")
    
    if missing_files:
        print(f"❌ Missing model files: {missing_files}")
        return False
    
    print("✅ All model files present")
    return True

def test_catboost_import():
    """Test that CatBoost can be imported and detector initialized"""
    print("\n🧪 Testing CatBoost import and initialization...")
    
    try:
        from threat_detection.catboost_detector import CatBoostThreatDetector, catboost_detector
        print("✅ CatBoost detector imported successfully")
        
        # Test detector initialization
        async def test_init():
            try:
                await catboost_detector.initialize()
                print("✅ CatBoost detector initialized successfully")
                
                # Test health status
                status = await catboost_detector.get_health_status()
                print(f"✅ Health status: {status['status']}")
                print(f"✅ Models loaded: {status['models']}")
                print(f"✅ Feature count: {status['feature_count']}")
                print(f"✅ Attack types supported: {status['attack_types_supported']}")
                
                return True
            except Exception as e:
                print(f"❌ Error initializing CatBoost detector: {e}")
                return False
        
        return asyncio.run(test_init())
        
    except Exception as e:
        print(f"❌ Error importing CatBoost detector: {e}")
        return False

def test_dependencies():
    """Test that all required Python dependencies are available"""
    print("\n🧪 Testing Python dependencies...")
    
    required_deps = [
        "fastapi",
        "uvicorn", 
        "catboost",
        "sklearn",  # Changed from scikit-learn
        "pandas",
        "numpy",
        "joblib"
    ]
    
    missing_deps = []
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} available")
        except ImportError:
            missing_deps.append(dep)
            print(f"❌ {dep} missing")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {missing_deps}")
        print("💡 Run: pip install -r backend/requirements.ctp.txt")
        return False
    
    print("✅ All dependencies available")
    return True

def test_environment_config():
    """Test environment configuration"""
    print("\n🧪 Testing environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("💡 Copy .env.production to .env and update values")
        return False
    
    print("✅ .env file exists")
    
    # Check for placeholder values that need to be changed
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    if "CHANGE_THIS" in env_content:
        print("⚠️  Found 'CHANGE_THIS' placeholders in .env")
        print("💡 Update security values before production deployment")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def test_docker_config():
    """Test Docker configuration files"""
    print("\n🧪 Testing Docker configuration...")
    
    required_files = [
        "docker-compose.ctp.yml",
        "backend/Dockerfile", 
        "frontend/Dockerfile"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"✅ Found: {file}")
    
    if missing_files:
        print(f"❌ Missing Docker files: {missing_files}")
        return False
    
    print("✅ All Docker configuration files present")
    return True

def test_api_imports():
    """Test that API modules can be imported"""
    print("\n🧪 Testing API imports...")
    
    try:
        from main import app
        print("✅ FastAPI app imported successfully")
        
        # Check that CatBoost routes are registered
        catboost_routes = [route for route in app.routes 
                          if hasattr(route, 'path') and 'catboost' in route.path]
        
        if catboost_routes:
            print("✅ CatBoost API routes found:")
            for route in catboost_routes:
                methods = getattr(route, 'methods', ['GET'])
                print(f"   {methods} {route.path}")
        else:
            print("⚠️  No CatBoost-specific routes found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing API: {e}")
        return False

def main():
    """Run all deployment readiness tests"""
    print("🚀 CTP Deployment Readiness Check")
    print("=" * 50)
    
    tests = [
        ("Model Files", test_model_files),
        ("CatBoost Integration", test_catboost_import), 
        ("Python Dependencies", test_dependencies),
        ("Environment Config", test_environment_config),
        ("Docker Config", test_docker_config),
        ("API Imports", test_api_imports)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT!")
        print("\nNext steps:")
        print("1. Update .env with production values")
        print("2. Run: ./deploy.sh")
        print("3. Verify deployment: ./verify-deployment.sh")
    else:
        print("⚠️  SOME TESTS FAILED - FIX ISSUES BEFORE DEPLOYMENT")
        print("\nResolve the failed tests and run this script again.")
    
    print("=" * 50)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
