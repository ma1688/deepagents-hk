"""Authentication API routes."""

import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..db.models import User
from ..services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    create_guest_token,
    TokenData,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Security scheme
security = HTTPBearer(auto_error=False)


# ==================== Schemas ====================

class UserRegister(BaseModel):
    """Registration request schema."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Login request schema."""
    email_or_username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_guest: bool = False


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_guest: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


# ==================== Dependencies ====================

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[User, TokenData]:
    """Get current user from JWT token.
    
    Returns:
        Tuple of (User, TokenData)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = uuid.UUID(token_data.user_id)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    # For guest users, create if doesn't exist
    if user is None and token_data.is_guest:
        user = User(
            id=user_id,
            is_guest=True,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    elif user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user, token_data


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[User | None, TokenData | None]:
    """Get current user if authenticated, otherwise return None."""
    if credentials is None:
        return None, None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None, None


# ==================== Routes ====================

@router.post("/register", response_model=TokenResponse)
async def register(
    request: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Register a new user."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username exists
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Create user
    user = User(
        email=request.email,
        username=request.username,
        password_hash=get_password_hash(request.password),
        is_guest=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    
    # Generate token
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        username=user.username,
        is_guest=False,
    )
    
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_guest=False,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login with email/username and password."""
    # Find user by email or username
    result = await db.execute(
        select(User).where(
            (User.email == request.email_or_username) | 
            (User.username == request.email_or_username)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.flush()
    
    # Generate token
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        username=user.username,
        is_guest=False,
    )
    
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_guest=False,
    )


@router.post("/guest", response_model=TokenResponse)
async def create_guest_user(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Create a guest user account."""
    guest_id, token = create_guest_token()
    
    # Create guest user in database
    user = User(
        id=guest_id,
        is_guest=True,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    
    return TokenResponse(
        access_token=token,
        user_id=str(guest_id),
        is_guest=True,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_data: Annotated[tuple[User, TokenData], Depends(get_current_user)],
) -> UserResponse:
    """Get current user information."""
    user, _ = user_data
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        is_guest=user.is_guest,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.post("/upgrade", response_model=TokenResponse)
async def upgrade_guest(
    request: UserRegister,
    user_data: Annotated[tuple[User, TokenData], Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Upgrade a guest account to a full account."""
    user, token_data = user_data
    
    if not user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a registered user",
        )
    
    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing = result.scalar_one_or_none()
    if existing and existing.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username exists
    result = await db.execute(select(User).where(User.username == request.username))
    existing = result.scalar_one_or_none()
    if existing and existing.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Upgrade user
    user.email = request.email
    user.username = request.username
    user.password_hash = get_password_hash(request.password)
    user.is_guest = False
    await db.flush()
    
    # Generate new token
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        username=user.username,
        is_guest=False,
    )
    
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_guest=False,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    user_data: Annotated[tuple[User, TokenData], Depends(get_current_user)],
) -> TokenResponse:
    """Refresh access token."""
    user, _ = user_data
    
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        username=user.username,
        is_guest=user.is_guest,
    )
    
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_guest=user.is_guest,
    )

