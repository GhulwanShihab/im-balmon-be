"""JWT token handling with blacklist support using existing Redis infrastructure."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status

from src.core.config import settings
from src.core.redis import redis_set, redis_exists, redis_delete

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token with longer expiration."""
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    # Use different secret for refresh tokens (more secure)
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_REFRESH_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


async def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode a JWT token with blacklist check.
    
    Uses existing Redis infrastructure from src.core.redis
    """
    try:
        # Check if token is blacklisted using existing Redis function
        is_blacklisted = await redis_exists(f"blacklist:{token}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Choose secret key based on token type
        secret_key = settings.JWT_REFRESH_SECRET_KEY if token_type == "refresh" else settings.JWT_SECRET_KEY
        
        payload = jwt.decode(
            token, 
            secret_key, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}"
            )
        
        return payload
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def blacklist_token(token: str, expire_seconds: int = None):
    """
    Add token to blacklist using existing Redis infrastructure.
    
    Uses redis_set from src.core.redis
    """
    if expire_seconds is None:
        expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    # Use existing Redis function
    await redis_set(
        key=f"blacklist:{token}",
        value="1",
        expire=expire_seconds
    )


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted using existing Redis infrastructure.
    
    Uses redis_exists from src.core.redis
    """
    return await redis_exists(f"blacklist:{token}")


async def blacklist_user_tokens(user_id: int):
    """
    Blacklist all tokens for a user (logout all devices).
    
    Uses existing Redis infrastructure.
    """
    expire_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await redis_set(
        key=f"user_blacklist:{user_id}",
        value="1",
        expire=expire_seconds
    )


async def is_user_blacklisted(user_id: int) -> bool:
    """
    Check if all user tokens are blacklisted.
    
    Uses redis_exists from src.core.redis
    """
    return await redis_exists(f"user_blacklist:{user_id}")


async def remove_user_blacklist(user_id: int):
    """Remove user from global blacklist (allow login again)."""
    await redis_delete(f"user_blacklist:{user_id}")


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get token expiration time without verification."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None
    except:
        return None