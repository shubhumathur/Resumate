"""
Debug script to test login flow and identify issues.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from auth import create_user, authenticate_user, get_user_by_email
from pymongo import MongoClient

def debug_user_in_db(email: str):
    """Check what's actually in the database for a user."""
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("MONGODB_DB_NAME", "resumate")
    
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    
    user = db.users.find_one({"email": email})
    if user:
        print(f"\nUser in database:")
        print(f"  _id: {user.get('_id')}")
        print(f"  name: {user.get('name')}")
        print(f"  email: {user.get('email')}")
        print(f"  provider: {user.get('provider')}")
        print(f"  password_hash exists: {'password_hash' in user}")
        print(f"  hashed_password exists: {'hashed_password' in user}")
        if 'password_hash' in user:
            print(f"  password_hash: {user['password_hash'][:50]}...")
        return user
    else:
        print(f"\nUser {email} not found in database")
        return None

def test_login_flow(email: str, password: str):
    """Test the complete login flow."""
    print(f"\n{'='*60}")
    print(f"Testing login flow for: {email}")
    print(f"{'='*60}")
    
    # Check what's in DB
    db_user = debug_user_in_db(email)
    if not db_user:
        print("❌ User not found in database")
        return False
    
    # Test get_user_by_email
    print(f"\n1. Testing get_user_by_email...")
    try:
        user = get_user_by_email(email)
        if user:
            print(f"   ✅ User found: {user.get('name')}")
            print(f"   Keys in user dict: {list(user.keys())}")
        else:
            print(f"   ❌ User not found")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test authenticate_user
    print(f"\n2. Testing authenticate_user...")
    try:
        auth_user = authenticate_user(email, password)
        if auth_user:
            print(f"   ✅ Authentication successful")
            print(f"   User: {auth_user.get('name')}")
            return True
        else:
            print(f"   ❌ Authentication failed")
            print(f"   Checking password hash...")
            
            # Check if password_hash exists in the user dict from get_user_by_email
            user_with_pw = get_user_by_email(email)
            if user_with_pw:
                has_pw_hash = 'password_hash' in user_with_pw
                has_hashed_pw = 'hashed_password' in user_with_pw
                print(f"   password_hash in user dict: {has_pw_hash}")
                print(f"   hashed_password in user dict: {has_hashed_pw}")
            
            return False
    except Exception as e:
        print(f"   ❌ Error during authentication: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_login_debug.py <email> <password>")
        print("\nExample: python test_login_debug.py test@example.com mypassword")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    test_login_flow(email, password)

