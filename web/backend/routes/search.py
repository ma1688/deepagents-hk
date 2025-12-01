"""HKEX announcement search API routes."""

import uuid
from datetime import datetime, date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db, crud
from ..models.schemas import (
    SearchRequest,
    SearchResponse,
    AnnouncementItem,
)
from ..services.agent_service import AgentService

router = APIRouter(prefix="/search", tags=["search"])


def parse_date(date_str: str) -> date:
    """Parse YYYYMMDD string to date."""
    return datetime.strptime(date_str, "%Y%m%d").date()


@router.post("/announcements", response_model=SearchResponse)
async def search_announcements(
    request: SearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> SearchResponse:
    """Search HKEX announcements with caching."""
    from_date = parse_date(request.from_date)
    to_date = parse_date(request.to_date)
    
    # Check cache first
    cached = await crud.get_search_cache(
        db,
        stock_code=request.stock_code,
        from_date=from_date,
        to_date=to_date,
        title_filter=request.title
    )
    
    if cached:
        return SearchResponse(
            stock_code=request.stock_code,
            total_count=len(cached.result_json.get("announcements", [])),
            announcements=[
                AnnouncementItem(**item) 
                for item in cached.result_json.get("announcements", [])
            ],
            cached=True,
            cache_expires_at=cached.expires_at
        )
    
    # Perform search using the HKEX tool
    try:
        # Import the tool directly
        from src.tools.hkex_tools import search_hkex_announcements
        
        result = search_hkex_announcements.invoke({
            "stock_code": request.stock_code,
            "from_date": request.from_date,
            "to_date": request.to_date,
            "title": request.title,
            "market": request.market,
            "row_range": request.row_range,
        })
        
        # Parse result
        if isinstance(result, str):
            # Handle error message
            raise HTTPException(status_code=400, detail=result)
        
        announcements = []
        if isinstance(result, dict):
            # Extract announcements from result
            items = result.get("records", result.get("announcements", []))
            for item in items:
                announcements.append(AnnouncementItem(
                    title=item.get("title", item.get("TITLE", "")),
                    date=item.get("date", item.get("DATE_TIME", "")),
                    url=item.get("url", item.get("FILE_LINK", None)),
                    category=item.get("category", item.get("CATEGORY_NAME", None))
                ))
        
        # Cache the result
        cache_data = {
            "announcements": [a.model_dump() for a in announcements]
        }
        cache_entry = await crud.create_search_cache(
            db,
            stock_code=request.stock_code,
            from_date=from_date,
            to_date=to_date,
            result_json=cache_data,
            title_filter=request.title,
            ttl_hours=24
        )
        
        return SearchResponse(
            stock_code=request.stock_code,
            total_count=len(announcements),
            announcements=announcements,
            cached=False,
            cache_expires_at=cache_entry.expires_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/stock/{stock_code}/recent", response_model=SearchResponse)
async def get_recent_announcements(
    stock_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 30
) -> SearchResponse:
    """Get recent announcements for a stock."""
    from datetime import timedelta
    
    today = date.today()
    from_date = today - timedelta(days=days)
    
    request = SearchRequest(
        stock_code=stock_code,
        from_date=from_date.strftime("%Y%m%d"),
        to_date=today.strftime("%Y%m%d"),
        row_range=100
    )
    
    return await search_announcements(request, db)


@router.delete("/cache")
async def clear_expired_cache(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """Clear expired cache entries."""
    deleted = await crud.cleanup_expired_cache(db)
    return {"status": "ok", "deleted_count": deleted}

