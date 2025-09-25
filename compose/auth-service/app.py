import os
import time
from datetime import datetime, timedelta
from typing import Optional

import jwt
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import bcrypt

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
REDIS_URL = os.getenv("REDIS_URL", "redis://:password@redis:6379/1")

app = FastAPI(title="Enterprise Auth Service")
security = HTTPBearer()

# Global Redis connection
rds = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    email: str
    organization: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_id: str

@app.on_event("startup")
async def startup():
    global rds
    rds = await redis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown():
    await rds.close()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, username: str, organization: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "organization": organization,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
        "iss": "enterprise-chatbot"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register new user"""
    # Check if user exists
    user_key = f"user:{user_data.username}"
    if await rds.exists(user_key):
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user_id = f"user_{int(time.time())}"
    hashed_password = hash_password(user_data.password)
    
    user_info = {
        "user_id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "organization": user_data.organization,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True
    }
    
    # Store user in Redis
    await rds.hset(user_key, mapping=user_info)
    
    # Create token
    token = create_token(user_id, user_data.username, user_data.organization)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user_id=user_id
    )

@app.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user"""
    # Get user from Redis
    user_key = f"user:{user_data.username}"
    user_info = await rds.hgetall(user_key)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(user_data.password, user_info["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is active
    if not user_info.get("is_active", "True").lower() == "true":
        raise HTTPException(status_code=401, detail="User account disabled")
    
    # Create token
    token = create_token(
        user_info["user_id"], 
        user_data.username, 
        user_info["organization"]
    )
    
    # Update last login
    await rds.hset(user_key, "last_login", datetime.utcnow().isoformat())
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user_id=user_info["user_id"]
    )

@app.get("/verify")
async def verify_token_endpoint(user: dict = Depends(verify_token)):
    """Verify token and return user info"""
    return {
        "valid": True,
        "user_id": user["user_id"],
        "username": user["username"],
        "organization": user["organization"],
        "expires_at": datetime.fromtimestamp(user["exp"]).isoformat()
    }

@app.post("/logout")
async def logout(user: dict = Depends(verify_token)):
    """Logout user (invalidate token)"""
    # In production, you might want to maintain a blacklist of tokens
    # For now, we'll just return success since JWT is stateless
    return {"message": "Logged out successfully"}

@app.get("/users/me")
async def get_current_user(user: dict = Depends(verify_token)):
    """Get current user information"""
    user_key = f"user:{user['username']}"
    user_info = await rds.hgetall(user_key)
    
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user_info["user_id"],
        "username": user_info["username"],
        "email": user_info["email"],
        "organization": user_info["organization"],
        "created_at": user_info["created_at"],
        "last_login": user_info.get("last_login"),
        "is_active": user_info.get("is_active", "True")
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await rds.ping()
        return {"status": "healthy", "service": "auth"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")
