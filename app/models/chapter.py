from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ImagePage(BaseModel):
    page_number: int
    original_image_url: str
    proxied_image_url: str
    required_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Headers needed for direct client fetching to bypass anti-hotlink",
    )


class ChapterDetail(BaseModel):
    chapter_title: str
    chapter_slug: str
    comic_slug: str
    prev_chapter_slug: Optional[str] = None
    next_chapter_slug: Optional[str] = None
    total_images: int = 0
    images: List[ImagePage] = Field(default_factory=list)
