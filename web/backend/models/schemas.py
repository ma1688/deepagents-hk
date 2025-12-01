"""Pydantic schemas for API requests and responses."""

from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ==================== User Schemas ====================

class UserCreate(BaseModel):
    """Schema for creating a user."""
    pass


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Conversation Schemas ====================

class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""
    title: str = Field(default="新对话", max_length=255)


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: str = Field(max_length=255)


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    token_count: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Schema for conversation response with messages."""
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for conversation list item (without messages)."""
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


# ==================== Message Schemas ====================

class MessageCreate(BaseModel):
    """Schema for creating a message."""
    role: str = Field(pattern="^(user|assistant)$")
    content: str
    token_count: int | None = None


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(min_length=1)
    conversation_id: UUID | None = None
    stream: bool = True


class ChatStreamChunk(BaseModel):
    """Schema for streaming chat response chunk."""
    type: str  # "content", "error", "done", "info"
    content: str = ""
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    token_count: int | None = None


# ==================== Config Schemas ====================

class ConfigUpdate(BaseModel):
    """Schema for updating user configuration."""
    provider: str | None = Field(
        None, 
        pattern="^(siliconflow|openai|anthropic)$"
    )
    model_name: str | None = Field(None, max_length=100)
    api_key: str | None = None  # Will be encrypted before storage
    base_url: str | None = Field(None, max_length=255)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=100, le=200000)


class ConfigResponse(BaseModel):
    """Schema for user configuration response."""
    id: UUID
    user_id: UUID
    provider: str
    model_name: str
    base_url: str | None
    temperature: float
    max_tokens: int
    has_api_key: bool = False  # Don't expose actual key
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Search Schemas ====================

class SearchRequest(BaseModel):
    """Schema for announcement search request."""
    stock_code: str = Field(pattern=r"^\d{5}$")
    from_date: str = Field(pattern=r"^\d{8}$")  # YYYYMMDD
    to_date: str = Field(pattern=r"^\d{8}$")
    title: str | None = None
    market: str = Field(default="SEHK", pattern="^(SEHK|GEM)$")
    row_range: int = Field(default=100, ge=1, le=500)


class AnnouncementItem(BaseModel):
    """Schema for a single announcement."""
    title: str
    date: str
    url: str | None = None
    category: str | None = None


class SearchResponse(BaseModel):
    """Schema for search response."""
    stock_code: str
    total_count: int
    announcements: list[AnnouncementItem]
    cached: bool = False
    cache_expires_at: datetime | None = None


# ==================== Token Stats Schemas ====================

class TokenStatsResponse(BaseModel):
    """Schema for daily token stats."""
    id: UUID
    date: date
    model_name: str
    input_tokens: int
    output_tokens: int
    cost_yuan: Decimal

    class Config:
        from_attributes = True


class TokenUsageSummary(BaseModel):
    """Schema for aggregated token usage summary."""
    total_input_tokens: int
    total_output_tokens: int
    total_cost_yuan: float
    daily_stats: list[TokenStatsResponse] = []


# ==================== Model Options ====================

class ModelOption(BaseModel):
    """Schema for available model option."""
    provider: str
    model_name: str
    display_name: str
    context_limit: int
    price_per_million: float | None = None


class ModelsListResponse(BaseModel):
    """Schema for available models list."""
    models: list[ModelOption]

