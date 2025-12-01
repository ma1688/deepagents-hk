"""Authentication service with JWT and password hashing."""

import os
from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hkex-agent-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_guest: bool = False
    exp: Optional[datetime] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    user_id: uuid.UUID,
    email: Optional[str] = None,
    username: Optional[str] = None,
    is_guest: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "username": username,
        "is_guest": is_guest,
        "exp": expire,
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        return TokenData(
            user_id=user_id,
            email=payload.get("email"),
            username=payload.get("username"),
            is_guest=payload.get("is_guest", False),
            exp=datetime.fromtimestamp(payload.get("exp", 0)),
        )
    except JWTError:
        return None


def create_guest_token() -> tuple[uuid.UUID, str]:
    """Create a guest user token.
    
    Returns:
        Tuple of (user_id, access_token)
    """
    guest_id = uuid.uuid4()
    token = create_access_token(
        user_id=guest_id,
        is_guest=True,
    )
    return guest_id, token

