from fastapi import APIRouter, HTTPException, Path
from app.config import get_base_url
from app.models.common import APIResponse
from app.models.comic import ComicDetail
from app.services.scraper import scraper_service

router = APIRouter(prefix="/api/v1", tags=["Comic"])


@router.get("/comic/{comic_slug}", response_model=APIResponse[ComicDetail])
def get_comic(
    comic_slug: str = Path(..., description="Unique slug of the comic, e.g. 'solo-swordmaster' or '846048-eleceed'")
):
    """
    Returns complete comic details, genres, synopsis, thumbnail, and ordered list of chapters.
    Cached for 30 minutes.
    """
    try:
        data, cached = scraper_service.get_comic_detail(comic_slug=comic_slug)
        return APIResponse(
            status="success",
            message=f"Comic details for '{comic_slug}' retrieved successfully",
            base_url_used=get_base_url(),
            cached=cached,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comic details: {str(e)}")
