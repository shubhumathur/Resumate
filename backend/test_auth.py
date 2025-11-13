"""
Test script to check authentication setup and MongoDB connection.
Run this to diagnose authentication issues.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """Test if all required packages are installed."""
    print("Testing imports...")
    try:
        from jose import JWTError, jwt
        print("✅ python-jose is installed")
    except ImportError as e:
        print(f"❌ python-jose not installed: {e}")
        return False
    
    try:
        from passlib.context import CryptContext
        print("✅ passlib is installed")
    except ImportError as e:
        print(f"❌ passlib not installed: {e}")
        return False
    
    try:
        from pymongo import MongoClient
        print("✅ pymongo is installed")
    except ImportError as e:
        print(f"❌ pymongo not installed: {e}")
        return False
    
    try:
        from auth import create_user, authenticate_user, get_db
        print("✅ auth module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import auth module: {e}")
        return False
    
    return True

def test_mongodb():
    """Test MongoDB connection."""
    print("\nTesting MongoDB connection...")
    try:
        from auth import get_db
        db = get_db()
        # Test by listing collections
        collections = db.list_collection_names()
        print(f"✅ MongoDB connected successfully")
        print(f"   Database: {db.name}")
        print(f"   Collections: {collections}")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Is MongoDB running? (mongod process)")
        print("2. Check MONGODB_URI in .env file")
        print("3. Default: mongodb://localhost:27017")
        return False

def test_jwt():
    """Test JWT token creation."""
    print("\nTesting JWT token creation...")
    try:
        from auth import create_access_token, decode_token
        token = create_access_token(data={"sub": "test_user_id"})
        print(f"✅ JWT token created: {token[:50]}...")
        
        payload = decode_token(token)
        if payload and payload.get("sub") == "test_user_id":
            print("✅ JWT token decoded successfully")
            return True
        else:
            print("❌ JWT token decoding failed")
            return False
    except Exception as e:
        print(f"❌ JWT test failed: {e}")
        return False

def test_password_hashing():
    """Test password hashing."""
    print("\nTesting password hashing...")
    try:
        from auth import get_password_hash, verify_password
        password = "test_password_123"
        hashed = get_password_hash(password)
        print(f"✅ Password hashed: {hashed[:50]}...")
        
        if verify_password(password, hashed):
            print("✅ Password verification works")
            return True
        else:
            print("❌ Password verification failed")
            return False
    except Exception as e:
        print(f"❌ Password hashing test failed: {e}")
        return False

def test_user_creation():
    """Test user creation (cleanup after)."""
    print("\nTesting user creation...")
    try:
        from auth import create_user, get_user_by_email
        test_email = "test@example.com"
        
        # Clean up if exists
        user = get_user_by_email(test_email)
        if user:
            from auth import get_db
            from bson import ObjectId
            db = get_db()
            db.users.delete_one({"_id": ObjectId(user["_id"])})
            print("   Cleaned up existing test user")
        
        # Create test user
        user = create_user("Test User", test_email, "test_password")
        if user:
            print(f"✅ User created: {user['email']}")
            
            # Clean up
            from auth import get_db
            from bson import ObjectId
            db = get_db()
            db.users.delete_one({"_id": ObjectId(user["_id"])})
            print("   Test user cleaned up")
            return True
        else:
            print("❌ User creation returned None")
            return False
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("ResuMate Authentication Diagnostic Tool")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("MongoDB", test_mongodb()))
    results.append(("JWT", test_jwt()))
    results.append(("Password Hashing", test_password_hashing()))
    results.append(("User Creation", test_user_creation()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✅ All tests passed! Authentication should work.")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

