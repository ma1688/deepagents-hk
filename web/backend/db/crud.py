"""CRUD operations for database models."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    User,
    Conversation,
    Message,
    UserConfig,
    SearchCache,
    TokenStats,
)


# ==================== User CRUD ====================

async def get_or_create_user(db: AsyncSession, user_id: uuid.UUID | None = None) -> User:
    """Get existing user or create new one."""
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user
    
    # Create new user
    user = User(id=user_id or uuid.uuid4())
    db.add(user)
    await db.flush()
    return user


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ==================== Conversation CRUD ====================

async def create_conversation(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    title: str = "新对话"
) -> Conversation:
    """Create a new conversation."""
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    await db.flush()
    return conv


async def get_conversation(
    db: AsyncSession, 
    conversation_id: uuid.UUID,
    include_messages: bool = False
) -> Conversation | None:
    """Get conversation by ID."""
    query = select(Conversation).where(Conversation.id == conversation_id)
    if include_messages:
        query = query.options(selectinload(Conversation.messages))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_conversations(
    db: AsyncSession, 
    user_id: uuid.UUID,
    limit: int = 50
) -> list[Conversation]:
    """Get all conversations for a user, ordered by updated_at desc."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_conversation_title(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    title: str
) -> Conversation | None:
    """Update conversation title."""
    conv = await get_conversation(db, conversation_id)
    if conv:
        conv.title = title
        conv.updated_at = datetime.utcnow()
        await db.flush()
    return conv


async def delete_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> bool:
    """Delete a conversation and all its messages."""
    conv = await get_conversation(db, conversation_id)
    if conv:
        await db.delete(conv)
        await db.flush()
        return True
    return False


# ==================== Message CRUD ====================

async def create_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    token_count: int | None = None
) -> Message:
    """Create a new message in a conversation."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        token_count=token_count
    )
    db.add(msg)
    
    # Update conversation's updated_at
    conv = await get_conversation(db, conversation_id)
    if conv:
        conv.updated_at = datetime.utcnow()
    
    await db.flush()
    return msg


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID
) -> list[Message]:
    """Get all messages in a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


# ==================== UserConfig CRUD ====================

async def get_or_create_user_config(
    db: AsyncSession, 
    user_id: uuid.UUID
) -> UserConfig:
    """Get or create user configuration."""
    result = await db.execute(
        select(UserConfig).where(UserConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        config = UserConfig(user_id=user_id)
        db.add(config)
        await db.flush()
    
    return config


async def update_user_config(
    db: AsyncSession,
    user_id: uuid.UUID,
    **kwargs
) -> UserConfig:
    """Update user configuration."""
    config = await get_or_create_user_config(db, user_id)
    
    for key, value in kwargs.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)
    
    config.updated_at = datetime.utcnow()
    await db.flush()
    return config


# ==================== SearchCache CRUD ====================

async def get_search_cache(
    db: AsyncSession,
    stock_code: str,
    from_date: date,
    to_date: date,
    title_filter: str | None = None
) -> SearchCache | None:
    """Get cached search result if not expired."""
    conditions = [
        SearchCache.stock_code == stock_code,
        SearchCache.from_date == from_date,
        SearchCache.to_date == to_date,
        SearchCache.expires_at > datetime.utcnow()
    ]
    if title_filter:
        conditions.append(SearchCache.title_filter == title_filter)
    else:
        conditions.append(SearchCache.title_filter.is_(None))
    
    result = await db.execute(
        select(SearchCache).where(and_(*conditions))
    )
    return result.scalar_one_or_none()


async def create_search_cache(
    db: AsyncSession,
    stock_code: str,
    from_date: date,
    to_date: date,
    result_json: dict,
    title_filter: str | None = None,
    ttl_hours: int = 24
) -> SearchCache:
    """Create a new search cache entry."""
    cache = SearchCache(
        stock_code=stock_code,
        from_date=from_date,
        to_date=to_date,
        title_filter=title_filter,
        result_json=result_json,
        expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
    )
    db.add(cache)
    await db.flush()
    return cache


async def cleanup_expired_cache(db: AsyncSession) -> int:
    """Delete expired cache entries. Returns number deleted."""
    result = await db.execute(
        select(SearchCache).where(SearchCache.expires_at < datetime.utcnow())
    )
    expired = list(result.scalars().all())
    for cache in expired:
        await db.delete(cache)
    await db.flush()
    return len(expired)


# ==================== TokenStats CRUD ====================

async def record_token_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    cost_yuan: Decimal
) -> TokenStats:
    """Record token usage for today."""
    today = date.today()
    
    # Check if entry exists for today
    result = await db.execute(
        select(TokenStats).where(
            and_(
                TokenStats.user_id == user_id,
                TokenStats.date == today,
                TokenStats.model_name == model_name
            )
        )
    )
    stats = result.scalar_one_or_none()
    
    if stats:
        # Update existing
        stats.input_tokens += input_tokens
        stats.output_tokens += output_tokens
        stats.cost_yuan += cost_yuan
    else:
        # Create new
        stats = TokenStats(
            user_id=user_id,
            date=today,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_yuan=cost_yuan
        )
        db.add(stats)
    
    await db.flush()
    return stats


async def get_user_token_stats(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 30
) -> list[TokenStats]:
    """Get token usage stats for the last N days."""
    start_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(TokenStats)
        .where(
            and_(
                TokenStats.user_id == user_id,
                TokenStats.date >= start_date
            )
        )
        .order_by(TokenStats.date.desc())
    )
    return list(result.scalars().all())


async def get_user_total_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 30
) -> dict:
    """Get aggregated token usage for a user."""
    start_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(
            func.sum(TokenStats.input_tokens).label("total_input"),
            func.sum(TokenStats.output_tokens).label("total_output"),
            func.sum(TokenStats.cost_yuan).label("total_cost")
        )
        .where(
            and_(
                TokenStats.user_id == user_id,
                TokenStats.date >= start_date
            )
        )
    )
    row = result.one()
    return {
        "total_input_tokens": row.total_input or 0,
        "total_output_tokens": row.total_output or 0,
        "total_cost_yuan": float(row.total_cost or 0)
    }

