from fastapi import APIRouter, HTTPException, Path, Request
from app.config import get_base_url
from app.models.common import APIResponse
from app.models.chapter import ChapterDetail
from app.services.scraper import scraper_service

router = APIRouter(prefix="/api/v1", tags=["Chapter"])


@router.get("/chapter/{chapter_slug}", response_model=APIResponse[ChapterDetail])
def get_chapter(
    request: Request,
    chapter_slug: str = Path(..., description="Unique slug of the chapter, e.g. 'solo-swordmaster-chapter-22'"),
):
    """
    Returns chapter title, parent comic_slug, prev_chapter_slug, next_chapter_slug,
    and ordered array of image pages with original URL, proxied URL, and required CDN headers.
    Cached for 24 hours.
    """
    try:
        base_api_url = str(request.base_url).rstrip("/")
        data, cached = scraper_service.get_chapter_detail(
            chapter_slug=chapter_slug,
            base_api_url=base_api_url,
        )
        return APIResponse(
            status="success",
            message=f"Chapter '{chapter_slug}' retrieved successfully with {data.total_images} pages",
            base_url_used=get_base_url(),
            cached=cached,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chapter details: {str(e)}")
