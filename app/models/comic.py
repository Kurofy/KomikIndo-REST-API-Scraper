from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.common import Pagination


class ChapterSummary(BaseModel):
    chapter_title: str
    chapter_slug: str
    release_date: Optional[str] = None


class ComicCard(BaseModel):
    title: str
    comic_slug: str
    thumbnail: str
    type: Optional[str] = None  # Manga / Manhwa / Manhua
    rating: Optional[str] = None
    views: Optional[str] = None
    color: Optional[str] = None  # Warna / Hitam Putih
    status: Optional[str] = None  # Ongoing / Completed
    latest_chapters: List[ChapterSummary] = Field(default_factory=list)


class GenreItem(BaseModel):
    title: str
    slug: str
    endpoint: str


class ComicDetail(BaseModel):
    title: str
    alternative_title: Optional[str] = None
    comic_slug: str
    thumbnail: str
    rating: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    author: Optional[str] = None
    illustrator: Optional[str] = None
    synopsis: Optional[str] = None
    genres: List[GenreItem] = Field(default_factory=list)
    chapters: List[ChapterSummary] = Field(default_factory=list)


class HomeData(BaseModel):
    popular_comics: List[ComicCard] = Field(default_factory=list)
    latest_comics: List[ComicCard] = Field(default_factory=list)


class PaginatedComics(BaseModel):
    pagination: Pagination
    comics: List[ComicCard] = Field(default_factory=list)


class SearchData(BaseModel):
    query: str
    pagination: Pagination
    comics: List[ComicCard] = Field(default_factory=list)


class GenreComicsData(BaseModel):
    genre_slug: str
    genre_name: Optional[str] = None
    pagination: Pagination
    comics: List[ComicCard] = Field(default_factory=list)
