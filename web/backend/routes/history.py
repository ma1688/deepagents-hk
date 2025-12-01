"""Conversation history API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db, crud
from ..models.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    TokenStatsResponse,
    TokenUsageSummary,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{user_id}/conversations", response_model=list[ConversationListResponse])
async def get_conversations(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50
) -> list[ConversationListResponse]:
    """Get all conversations for a user."""
    # Ensure user exists
    await crud.get_or_create_user(db, user_id)
    
    conversations = await crud.get_user_conversations(db, user_id, limit)
    
    result = []
    for conv in conversations:
        messages = await crud.get_conversation_messages(db, conv.id)
        item = ConversationListResponse(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(messages)
        )
        result.append(item)
    
    return result


@router.post("/{user_id}/conversations", response_model=ConversationResponse)
async def create_conversation(
    user_id: uuid.UUID,
    request: ConversationCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ConversationResponse:
    """Create a new conversation."""
    # Ensure user exists
    await crud.get_or_create_user(db, user_id)
    
    conv = await crud.create_conversation(db, user_id, request.title)
    return ConversationResponse.model_validate(conv)


@router.get("/{user_id}/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ConversationResponse:
    """Get a specific conversation with all messages."""
    conv = await crud.get_conversation(db, conversation_id, include_messages=True)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ConversationResponse.model_validate(conv)


@router.put("/{user_id}/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    request: ConversationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ConversationResponse:
    """Update conversation title."""
    conv = await crud.get_conversation(db, conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated = await crud.update_conversation_title(db, conversation_id, request.title)
    return ConversationResponse.model_validate(updated)


@router.delete("/{user_id}/conversations/{conversation_id}")
async def delete_conversation(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """Delete a conversation."""
    conv = await crud.get_conversation(db, conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await crud.delete_conversation(db, conversation_id)
    return {"status": "ok", "message": "Conversation deleted"}


# ==================== Token Stats ====================

@router.get("/{user_id}/stats", response_model=TokenUsageSummary)
async def get_token_stats(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 30
) -> TokenUsageSummary:
    """Get token usage statistics for a user."""
    # Ensure user exists
    await crud.get_or_create_user(db, user_id)
    
    # Get daily stats
    daily_stats = await crud.get_user_token_stats(db, user_id, days)
    
    # Get totals
    totals = await crud.get_user_total_usage(db, user_id, days)
    
    return TokenUsageSummary(
        total_input_tokens=totals["total_input_tokens"],
        total_output_tokens=totals["total_output_tokens"],
        total_cost_yuan=totals["total_cost_yuan"],
        daily_stats=[TokenStatsResponse.model_validate(s) for s in daily_stats]
    )

