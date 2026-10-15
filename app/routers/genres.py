from typing import List
from fastapi import APIRouter, HTTPException, Path, Query
from app.config import get_base_url
from app.models.common import APIResponse
from app.models.comic import GenreItem, GenreComicsData
from app.services.scraper import scraper_service

router = APIRouter(prefix="/api/v1", tags=["Genres"])


@router.get("/genres", response_model=APIResponse[List[GenreItem]])
def list_genres():
    """
    Lists all available comic genres.
    Cached for 24 hours.
    """
    try:
        data, cached = scraper_service.get_genres()
        return APIResponse(
            status="success",
            message=f"Retrieved {len(data)} genres",
            base_url_used=get_base_url(),
            cached=cached,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch genres: {str(e)}")


@router.get("/genres/{genre_slug}", response_model=APIResponse[GenreComicsData])
def get_comics_by_genre(
    genre_slug: str = Path(..., description="Slug of the genre, e.g. 'action', 'romance', 'isekai'"),
    page: int = Query(default=1, ge=1, description="Page number"),
):
    """
    Fetches paginated comics associated with a specific genre.
    Cached for 24 hours.
    """
    try:
        data, cached = scraper_service.get_genre_comics(genre_slug=genre_slug, page=page)
        return APIResponse(
            status="success",
            message=f"Comics for genre '{genre_slug}' on page {page} retrieved successfully",
            base_url_used=get_base_url(),
            cached=cached,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comics by genre: {str(e)}")
