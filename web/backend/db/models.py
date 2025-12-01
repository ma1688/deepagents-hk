"""SQLAlchemy ORM models for HKEX Agent."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Date,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model for tracking individual users."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    config: Mapped["UserConfig"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    token_stats: Mapped[list["TokenStats"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Conversation(Base):
    """Conversation/chat session model."""
    
    __tablename__ = "conversations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="新对话")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    """Individual message within a conversation."""
    
    __tablename__ = "messages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class UserConfig(Base):
    """User configuration for model and API settings."""
    
    __tablename__ = "user_configs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )
    provider: Mapped[str] = mapped_column(
        String(50), 
        default="siliconflow"
    )  # siliconflow, openai, anthropic
    model_name: Mapped[str] = mapped_column(
        String(100), 
        default="deepseek-chat"
    )
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=20000)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="config")


class SearchCache(Base):
    """Cache for HKEX announcement search results."""
    
    __tablename__ = "search_cache"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    stock_code: Mapped[str] = mapped_column(String(10), index=True)
    from_date: Mapped[datetime] = mapped_column(Date)
    to_date: Mapped[datetime] = mapped_column(Date)
    title_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_json: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class TokenStats(Base):
    """Daily token usage statistics per user and model."""
    
    __tablename__ = "token_stats"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    date: Mapped[datetime] = mapped_column(Date, index=True)
    model_name: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_yuan: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), 
        default=Decimal("0.0000")
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="token_stats")

