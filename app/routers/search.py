from fastapi import APIRouter, Query, HTTPException
from app.config import get_base_url
from app.models.common import APIResponse
from app.models.comic import SearchData
from app.services.scraper import scraper_service

router = APIRouter(prefix="/api/v1", tags=["Search"])


@router.get("/search", response_model=APIResponse[SearchData])
def search_comics(
    q: str = Query(..., min_length=1, description="Search query keyword"),
    page: int = Query(default=1, ge=1, description="Page number"),
):
    """
    Searches comics by keyword with pagination support.
    Cached for 30 minutes.
    """
    try:
        clean_query = q.strip()
        data, cached = scraper_service.get_search(query=clean_query, page=page)
        return APIResponse(
            status="success",
            message=f"Search results for '{clean_query}' on page {page} retrieved successfully",
            base_url_used=get_base_url(),
            cached=cached,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search comics: {str(e)}")
