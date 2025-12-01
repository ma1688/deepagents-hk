"""Configuration API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db, crud
from ..models.schemas import (
    ConfigUpdate,
    ConfigResponse,
    ModelOption,
    ModelsListResponse,
)
from ..services.agent_service import encrypt_api_key

router = APIRouter(prefix="/config", tags=["config"])


# Available models configuration
AVAILABLE_MODELS = [
    # SiliconFlow models
    ModelOption(
        provider="siliconflow",
        model_name="deepseek-chat",
        display_name="DeepSeek-V3 Chat",
        context_limit=163840,
        price_per_million=1.33
    ),
    ModelOption(
        provider="siliconflow",
        model_name="deepseek-ai/DeepSeek-V3.1-Terminus",
        display_name="DeepSeek-V3.1 Terminus",
        context_limit=163840,
        price_per_million=1.33
    ),
    ModelOption(
        provider="siliconflow",
        model_name="deepseek-reasoner",
        display_name="DeepSeek-R1 Reasoner",
        context_limit=163840,
        price_per_million=2.0
    ),
    ModelOption(
        provider="siliconflow",
        model_name="Qwen/Qwen2.5-7B-Instruct",
        display_name="Qwen 2.5 7B",
        context_limit=32768,
        price_per_million=0.42
    ),
    ModelOption(
        provider="siliconflow",
        model_name="Qwen/Qwen2.5-32B-Instruct",
        display_name="Qwen 2.5 32B",
        context_limit=131072,
        price_per_million=1.26
    ),
    ModelOption(
        provider="siliconflow",
        model_name="Qwen/Qwen2.5-72B-Instruct",
        display_name="Qwen 2.5 72B",
        context_limit=131072,
        price_per_million=3.5
    ),
    ModelOption(
        provider="siliconflow",
        model_name="MiniMaxAI/MiniMax-M2",
        display_name="MiniMax M2",
        context_limit=186000,
        price_per_million=2.0
    ),
    # OpenAI models
    ModelOption(
        provider="openai",
        model_name="gpt-4o",
        display_name="GPT-4o",
        context_limit=128000,
        price_per_million=5.0
    ),
    ModelOption(
        provider="openai",
        model_name="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        context_limit=128000,
        price_per_million=10.0
    ),
    ModelOption(
        provider="openai",
        model_name="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        context_limit=16385,
        price_per_million=0.5
    ),
    # Anthropic models
    ModelOption(
        provider="anthropic",
        model_name="claude-sonnet-4-5-20250929",
        display_name="Claude Sonnet 4.5",
        context_limit=200000,
        price_per_million=3.0
    ),
    ModelOption(
        provider="anthropic",
        model_name="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        context_limit=200000,
        price_per_million=3.0
    ),
    ModelOption(
        provider="anthropic",
        model_name="claude-opus-4",
        display_name="Claude Opus 4",
        context_limit=200000,
        price_per_million=15.0
    ),
]


@router.get("/models", response_model=ModelsListResponse)
async def get_available_models() -> ModelsListResponse:
    """Get list of available models."""
    return ModelsListResponse(models=AVAILABLE_MODELS)


@router.get("/models/{provider}", response_model=ModelsListResponse)
async def get_models_by_provider(provider: str) -> ModelsListResponse:
    """Get models filtered by provider."""
    filtered = [m for m in AVAILABLE_MODELS if m.provider == provider]
    return ModelsListResponse(models=filtered)


@router.get("/{user_id}", response_model=ConfigResponse)
async def get_user_config(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ConfigResponse:
    """Get user's current configuration."""
    # Ensure user exists
    await crud.get_or_create_user(db, user_id)
    
    config = await crud.get_or_create_user_config(db, user_id)
    
    response = ConfigResponse.model_validate(config)
    response.has_api_key = bool(config.api_key_encrypted)
    return response


@router.put("/{user_id}", response_model=ConfigResponse)
async def update_user_config(
    user_id: uuid.UUID,
    update: ConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ConfigResponse:
    """Update user's configuration."""
    # Ensure user exists
    await crud.get_or_create_user(db, user_id)
    
    # Prepare update data
    update_data = update.model_dump(exclude_none=True)
    
    # Encrypt API key if provided
    if "api_key" in update_data:
        api_key = update_data.pop("api_key")
        if api_key:
            update_data["api_key_encrypted"] = encrypt_api_key(api_key)
        else:
            update_data["api_key_encrypted"] = None
    
    config = await crud.update_user_config(db, user_id, **update_data)
    
    response = ConfigResponse.model_validate(config)
    response.has_api_key = bool(config.api_key_encrypted)
    return response


@router.delete("/{user_id}/api-key")
async def delete_api_key(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """Delete user's stored API key."""
    await crud.update_user_config(db, user_id, api_key_encrypted=None)
    return {"status": "ok", "message": "API key deleted"}


@router.post("/{user_id}/test")
async def test_configuration(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """Test if the current configuration is valid."""
    from ..services.agent_service import AgentService, decrypt_api_key
    
    config = await crud.get_or_create_user_config(db, user_id)
    
    if not config.api_key_encrypted:
        raise HTTPException(
            status_code=400, 
            detail="No API key configured"
        )
    
    try:
        api_key = decrypt_api_key(config.api_key_encrypted)
        service = AgentService(
            provider=config.provider,
            model_name=config.model_name,
            api_key=api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=100,  # Small for testing
        )
        
        # Try a simple request
        response = await service.chat("Hello, respond with 'OK' only.")
        
        return {
            "status": "ok",
            "message": "Configuration is valid",
            "test_response": response[:100]
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration test failed: {str(e)}"
        )

