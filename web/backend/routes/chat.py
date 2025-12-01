"""Chat API routes with WebSocket support for streaming."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db, crud
from ..models.schemas import (
    ChatRequest,
    ChatStreamChunk,
    MessageResponse,
    ConversationResponse,
)
from ..services.agent_service import decrypt_api_key

# Lazy import to avoid circular imports
def _get_agent_service_class():
    from ..services.agent_service import AgentService
    return AgentService

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_agent_service(
    db: AsyncSession,
    user_id: uuid.UUID
):
    """Create agent service with user's configuration."""
    config = await crud.get_or_create_user_config(db, user_id)
    
    api_key = None
    if config.api_key_encrypted:
        try:
            api_key = decrypt_api_key(config.api_key_encrypted)
        except Exception:
            pass
    
    AgentService = _get_agent_service_class()
    return AgentService(
        provider=config.provider,
        model_name=config.model_name,
        api_key=api_key,
        base_url=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


@router.websocket("/ws/{user_id}")
async def chat_websocket(
    websocket: WebSocket,
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    
    try:
        # Get or create user
        user = await crud.get_or_create_user(db, user_id)
        
        # Create agent service
        try:
            agent_service = await get_agent_service(db, user_id)
        except ValueError as e:
            await websocket.send_json({
                "type": "error",
                "content": f"配置错误: {str(e)}. 请先设置API密钥。"
            })
            await websocket.close()
            return
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            conversation_id = data.get("conversation_id")
            
            if not message:
                continue
            
            # Get or create conversation
            if conversation_id:
                conv_uuid = uuid.UUID(conversation_id)
                conv = await crud.get_conversation(db, conv_uuid)
                if not conv:
                    conv = await crud.create_conversation(db, user_id)
            else:
                conv = await crud.create_conversation(db, user_id)
            
            # Save user message
            user_msg = await crud.create_message(
                db, conv.id, "user", message
            )
            
            # Send conversation info
            await websocket.send_json({
                "type": "info",
                "conversation_id": str(conv.id),
                "message_id": str(user_msg.id)
            })
            
            # Stream response
            response_parts = []
            try:
                async for chunk in agent_service.chat_stream(
                    message, 
                    thread_id=str(conv.id)
                ):
                    response_parts.append(chunk)
                    await websocket.send_json({
                        "type": "content",
                        "content": chunk
                    })
                
                # Save assistant message
                full_response = "".join(response_parts)
                assistant_msg = await crud.create_message(
                    db, conv.id, "assistant", full_response
                )
                
                # Auto-generate title from first user message if new conversation
                if conv.title == "新对话" and len(message) > 0:
                    title = message[:50] + ("..." if len(message) > 50 else "")
                    await crud.update_conversation_title(db, conv.id, title)
                
                await websocket.send_json({
                    "type": "done",
                    "message_id": str(assistant_msg.id),
                    "conversation_id": str(conv.id)
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"生成回复时出错: {str(e)}"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"连接错误: {str(e)}"
            })
        except Exception:
            pass


@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: ChatRequest,
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    """Non-streaming chat endpoint."""
    # Get or create user
    user = await crud.get_or_create_user(db, user_id)
    
    # Create agent service
    agent_service = await get_agent_service(db, user_id)
    
    # Get or create conversation
    if request.conversation_id:
        conv = await crud.get_conversation(db, request.conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = await crud.create_conversation(db, user_id)
    
    # Save user message
    await crud.create_message(db, conv.id, "user", request.message)
    
    # Get response
    response = await agent_service.chat(request.message, thread_id=str(conv.id))
    
    # Save assistant message
    assistant_msg = await crud.create_message(db, conv.id, "assistant", response)
    
    return MessageResponse.model_validate(assistant_msg)

