from fastapi import APIRouter, Query, HTTPException
from app.config import get_base_url
from app.models.common import APIResponse
from app.models.comic import HomeData, PaginatedComics
from app.services.scraper import scraper_service

router = APIRouter(prefix="/api/v1", tags=["Home & Latest"])


@router.get("/home", response_model=APIResponse[HomeData])
def get_home():
    """
    Returns popular/trending comics and latest updated comics.
    Cached for 10 minutes.
    """
    try:
        data, cached = scraper_service.get_home()
        return APIResponse(
            status="success",
            message="Home comics retrieved successfully",
            base_url_used=get_base_url(),
            cached=cached,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch home data: {str(e)}")


@router.get("/latest", response_model=APIResponse[PaginatedComics])
def get_latest(page: int = Query(default=1, ge=1, description="Page number")):
    """
    Returns a paginated list of latest comic updates.
    Cached for 10 minutes.
    """
    try:
        data, cached = scraper_service.get_latest(page=page)
        return APIResponse(
            status="success",
            message=f"Latest updates for page {page} retrieved successfully",
            base_url_used=get_base_url(),
            cached=cached,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest comics: {str(e)}")
