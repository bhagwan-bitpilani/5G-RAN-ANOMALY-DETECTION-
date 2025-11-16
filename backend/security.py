# app/security.py
import os
import secrets
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from typing import Optional, Dict, Any
import logging
from pydantic import BaseModel
import redis
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

# Security configurations - Use environment variables in production
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Redis for token blacklisting (optional)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme for FastAPI
security_scheme = HTTPBearer(auto_error=False)

# Pydantic models for token data
class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class User(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = "user"
    disabled: bool = False
    permissions: list = []

class UserInDB(User):
    hashed_password: str

# In-memory user store (replace with database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@5g-kpi.local",
        "role": "administrator",
        "hashed_password": pwd_context.hash("admin"),  # Change in production!
        "disabled": False,
        "permissions": ["read", "write", "admin"]
    },
    "operator": {
        "username": "operator",
        "email": "operator@5g-kpi.local",
        "role": "operator",
        "hashed_password": pwd_context.hash("operator123"),
        "disabled": False,
        "permissions": ["read", "write"]
    },
    "viewer": {
        "username": "viewer",
        "email": "viewer@5g-kpi.local",
        "role": "viewer",
        "hashed_password": pwd_context.hash("viewer123"),
        "disabled": False,
        "permissions": ["read"]
    }
}

class TokenBlacklist:
    """Simple token blacklist using Redis"""
    
    def __init__(self):
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connected for token blacklisting")
        except Exception as e:
            logger.warning(f"Redis not available for token blacklisting: {e}")
            self.redis_client = None
    
    def add_to_blacklist(self, token: str, expire_seconds: int = None):
        """Add token to blacklist"""
        if not self.redis_client:
            return False
        
        try:
            if expire_seconds is None:
                expire_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
            
            self.redis_client.setex(
                f"blacklist:{token}",
                expire_seconds,
                "blacklisted"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(f"blacklist:{token}") == 1
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False

# Initialize token blacklist
token_blacklist = TokenBlacklist()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def get_user(db, username: str) -> Optional[UserInDB]:
    """Get user from database"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(db, username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password"""
    user = get_user(db, username)
    if not user:
        logger.warning(f"Authentication failed: User '{username}' not found")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed: Invalid password for user '{username}'")
        return None
    if user.disabled:
        logger.warning(f"Authentication failed: User '{username}' is disabled")
        return None
    logger.info(f"User '{username}' authenticated successfully")
    return user

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_urlsafe(16)  # Unique token ID
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_tokens(data: dict) -> Token:
    """Create both access and refresh tokens"""
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

def validate_token(token: str, expected_type: str = "access") -> TokenData:
    """
    Validate JWT token and return token data
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
    
    Returns:
        TokenData object with token payload
    
    Raises:
        HTTPException if token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check if token is blacklisted
        if token_blacklist.is_blacklisted(token):
            logger.warning("Attempt to use blacklisted token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Decode and validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate token type
        token_type = payload.get("type")
        if token_type != expected_type:
            logger.warning(f"Invalid token type: expected {expected_type}, got {token_type}")
            raise credentials_exception
        
        # Validate expiration
        exp = payload.get("exp")
        if exp is None:
            raise credentials_exception
        
        exp_datetime = datetime.fromtimestamp(exp)
        if exp_datetime < datetime.utcnow():
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Extract user data
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        return TokenData(
            username=username,
            user_id=payload.get("user_id"),
            role=payload.get("role"),
            exp=exp_datetime
        )
        
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> User:
    """
    Dependency to get current user from JWT token
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = validate_token(credentials.credentials)
    user = get_user(fake_users_db, token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def require_permission(permission: str):
    """Dependency factory for permission-based authorization"""
    async def permission_dependency(current_user: User = Depends(get_current_active_user)):
        if permission not in current_user.permissions:
            logger.warning(f"User '{current_user.username}' lacks permission '{permission}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_dependency

# Common permission dependencies
require_admin = require_permission("admin")
require_write = require_permission("write")
require_read = require_permission("read")

async def validate_refresh_token(refresh_token: str) -> TokenData:
    """Validate refresh token and return token data"""
    return validate_token(refresh_token, expected_type="refresh")

async def refresh_access_token(refresh_token: str) -> Token:
    """Create new access token using refresh token"""
    try:
        # Validate refresh token
        token_data = await validate_refresh_token(refresh_token)
        
        # Create new tokens
        user_data = {
            "sub": token_data.username,
            "role": token_data.role
        }
        
        return create_tokens(user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

async def revoke_token(token: str) -> bool:
    """Revoke/blacklist a token"""
    try:
        # Validate token first to get expiration
        token_data = validate_token(token)
        
        # Calculate remaining time for blacklist expiration
        now = datetime.utcnow()
        if token_data.exp:
            remaining_seconds = max(0, int((token_data.exp - now).total_seconds()))
        else:
            remaining_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        # Add to blacklist
        return token_blacklist.add_to_blacklist(token, remaining_seconds)
        
    except Exception as e:
        logger.error(f"Token revocation failed: {e}")
        return False

async def logout_user(token: str) -> bool:
    """Logout user by revoking their token"""
    return await revoke_token(token)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def validate_api_key(api_key: str, stored_hash: str) -> bool:
    """Validate API key against stored hash"""
    # For API keys, we might want to use a different verification method
    # Here we're using the same password verification for simplicity
    return verify_password(api_key, stored_hash)

# Security middleware for additional protection
async def security_headers_middleware(request: Request, call_next):
    """Middleware to add security headers"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Remove server header
    if "server" in response.headers:
        del response.headers["server"]
    
    return response

# Rate limiting (simple in-memory implementation)
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_rate_limited(self, identifier: str) -> bool:
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > window_start
        ]
        
        # Check if rate limited
        if len(self.requests[identifier]) >= self.requests_per_minute:
            return True
        
        # Add current request
        self.requests[identifier].append(now)
        return False

# Initialize rate limiter
rate_limiter = RateLimiter(requests_per_minute=100)

async def rate_limit_middleware(request: Request, call_next):
    """Middleware for rate limiting"""
    # Use client IP as identifier (you might want to use user ID for authenticated users)
    identifier = request.client.host
    
    if rate_limiter.is_rate_limited(identifier):
        logger.warning(f"Rate limit exceeded for {identifier}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"}
        )
    
    response = await call_next(request)
    return response

# Password strength validation
import re

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        issues.append("Password must contain at least one digit")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        issues.append("Password must contain at least one special character")
    
    is_strong = len(issues) == 0
    score = max(0, min(100, 100 - len(issues) * 20))  # Simple scoring
    
    return {
        "is_strong": is_strong,
        "score": score,
        "issues": issues
    }

# Utility function to create initial admin user
def create_initial_admin():
    """Create initial admin user if not exists"""
    if "admin" not in fake_users_db:
        admin_user = {
            "username": "admin",
            "email": "admin@5g-kpi.local",
            "role": "administrator",
            "hashed_password": get_password_hash("admin"),  # Change this!
            "disabled": False,
            "permissions": ["read", "write", "admin"]
        }
        fake_users_db["admin"] = admin_user
        logger.info("Initial admin user created")
    else:
        logger.info("Admin user already exists")

# Initialize on module import
create_initial_admin()
