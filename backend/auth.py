"""
Authentication utilities for ResuMate backend.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
try:
    from jose import JWTError, jwt
    JWT_AVAILABLE = True
except ImportError:
    # Fallback if python-jose is not installed
    JWTError = Exception
    jwt = None
    JWT_AVAILABLE = False
from passlib.context import CryptContext
from pymongo import MongoClient
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "resumate")

def get_db():
    """Get MongoDB database instance."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        db = client[DB_NAME]
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise ConnectionError(f"MongoDB connection failed: {e}. Please ensure MongoDB is running.")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    if not JWT_AVAILABLE or jwt is None:
        raise ImportError("python-jose is required for JWT token creation")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    if not JWT_AVAILABLE or jwt is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_user_by_email(email: str):
    """Get user by email from MongoDB."""
    try:
        db = get_db()
        user = db.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        raise

def get_user_by_id(user_id: str):
    """Get user by ID from MongoDB."""
    try:
        db = get_db()
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None

def create_user(name: str, email: str, password: str, provider: str = "email"):
    """Create a new user in MongoDB."""
    try:
        db = get_db()
        
        # Check if user already exists
        if db.users.find_one({"email": email}):
            return None
        
        # Create user
        user = {
            "name": name,
            "email": email,
            "provider": provider,
            "password_hash": get_password_hash(password) if provider == "email" else None,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        result = db.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        user.pop("password_hash", None)
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise



def authenticate_user(email: str, password: str):
    """Authenticate a user by email and password."""
    try:
        user = get_user_by_email(email)
        if not user:
            logger.warning(f"User not found for email: {email}")
            return False
        
        # Get password hash from user dict
        hashed_pw = user.get("password_hash")
        if not hashed_pw:
            logger.warning(f"No password hash found for user: {email}")
            return False
        
        # Verify password
        if not verify_password(password, hashed_pw):
            logger.warning(f"Password verification failed for user: {email}")
            return False
        
        # Remove password hash before returning
        user.pop("password_hash", None)
        user.pop("hashed_password", None)
        logger.info(f"User authenticated successfully: {email}")
        return user
    except Exception as e:
        logger.error(f"Error in authenticate_user: {e}", exc_info=True)
        return False


