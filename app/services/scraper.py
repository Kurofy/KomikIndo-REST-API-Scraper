import logging
from typing import List, Tuple
from app.config import get_base_url
from app.utils.http_client import http_client
from app.utils.cache import cache_manager
from app.models.comic import (
    HomeData,
    PaginatedComics,
    SearchData,
    ComicDetail,
    GenreItem,
    GenreComicsData,
)
from app.models.chapter import ChapterDetail
from app.services.parser import (
    parse_homepage,
    parse_comic_list,
    parse_comic_detail,
    parse_chapter_detail,
    parse_genres_sitemap,
)

logger = logging.getLogger(__name__)


class ScraperService:
    @staticmethod
    def get_home() -> Tuple[HomeData, bool]:
        base_url = get_base_url()
        cache_key = f"home:{base_url}"
        cached_data, is_cached = cache_manager.get("homepage", cache_key)
        if is_cached:
            return cached_data, True

        html = http_client.get(f"{base_url}/")
        data = parse_homepage(html)
        cache_manager.set("homepage", cache_key, data)
        return data, False

    @staticmethod
    def get_latest(page: int = 1) -> Tuple[PaginatedComics, bool]:
        base_url = get_base_url()
        cache_key = f"latest:{base_url}:{page}"
        cached_data, is_cached = cache_manager.get("latest", cache_key)
        if is_cached:
            return cached_data, True

        target_url = f"{base_url}/komik-terbaru/" if page <= 1 else f"{base_url}/komik-terbaru/page/{page}/"
        html = http_client.get(target_url)
        data = parse_comic_list(html, current_page=page)
        cache_manager.set("latest", cache_key, data)
        return data, False

    @staticmethod
    def get_search(query: str, page: int = 1) -> Tuple[SearchData, bool]:
        base_url = get_base_url()
        cache_key = f"search:{base_url}:{query}:{page}"
        cached_data, is_cached = cache_manager.get("search", cache_key)
        if is_cached:
            return cached_data, True

        target_url = f"{base_url}/?s={query}" if page <= 1 else f"{base_url}/page/{page}/?s={query}"
        html = http_client.get(target_url)
        paginated = parse_comic_list(html, current_page=page)
        data = SearchData(
            query=query,
            pagination=paginated.pagination,
            comics=paginated.comics,
        )
        cache_manager.set("search", cache_key, data)
        return data, False

    @staticmethod
    def get_comic_detail(comic_slug: str) -> Tuple[ComicDetail, bool]:
        base_url = get_base_url()
        cache_key = f"comic:{base_url}:{comic_slug}"
        cached_data, is_cached = cache_manager.get("comic_detail", cache_key)
        if is_cached:
            return cached_data, True

        target_url = f"{base_url}/komik/{comic_slug}/"
        html = http_client.get(target_url)
        data = parse_comic_detail(html, comic_slug=comic_slug)
        cache_manager.set("comic_detail", cache_key, data)
        return data, False

    @staticmethod
    def get_chapter_detail(chapter_slug: str, base_api_url: str) -> Tuple[ChapterDetail, bool]:
        base_url = get_base_url()
        cache_key = f"chapter:{base_url}:{chapter_slug}"
        cached_data, is_cached = cache_manager.get("chapter", cache_key)
        if is_cached:
            return cached_data, True

        target_url = f"{base_url}/{chapter_slug}/"
        html = http_client.get(target_url)
        data = parse_chapter_detail(html, chapter_slug=chapter_slug, base_api_url=base_api_url)
        cache_manager.set("chapter", cache_key, data)
        return data, False

    @staticmethod
    def get_genres() -> Tuple[List[GenreItem], bool]:
        base_url = get_base_url()
        cache_key = f"genres:{base_url}"
        cached_data, is_cached = cache_manager.get("genres", cache_key)
        if is_cached:
            return cached_data, True

        # Fetch from genres-sitemap.xml
        target_url = f"{base_url}/genres-sitemap.xml"
        try:
            xml_content = http_client.get(target_url)
            genres = parse_genres_sitemap(xml_content)
        except Exception as e:
            logger.warning("Failed to fetch genres sitemap (%s), falling back to common genres", e)
            # Comprehensive fallback list of standard Komikindo genres
            common_genres = [
                "action", "adventure", "comedy", "crime", "demons", "drama", "ecchi",
                "fantasy", "game", "gender-bender", "harem", "historical", "horror",
                "isekai", "josei", "magic", "martial-arts", "mature", "mecha", "medical",
                "mystery", "psychological", "reincarnation", "romance", "school",
                "school-life", "sci-fi", "seinen", "shoujo", "shounen", "slice-of-life",
                "sports", "superhero", "supernatural", "thriller", "tragedy", "wuxia"
            ]
            genres = [
                GenreItem(
                    title=g.replace("-", " ").title(),
                    slug=g,
                    endpoint=f"/api/v1/genres/{g}"
                )
                for g in common_genres
            ]

        cache_manager.set("genres", cache_key, genres)
        return genres, False

    @staticmethod
    def get_genre_comics(genre_slug: str, page: int = 1) -> Tuple[GenreComicsData, bool]:
        base_url = get_base_url()
        cache_key = f"genre_comics:{base_url}:{genre_slug}:{page}"
        cached_data, is_cached = cache_manager.get("genres", cache_key)
        if is_cached:
            return cached_data, True

        target_url = (
            f"{base_url}/genres/{genre_slug}/"
            if page <= 1
            else f"{base_url}/genres/{genre_slug}/page/{page}/"
        )
        html = http_client.get(target_url)
        paginated = parse_comic_list(html, current_page=page)
        genre_name = genre_slug.replace("-", " ").title()

        data = GenreComicsData(
            genre_slug=genre_slug,
            genre_name=genre_name,
            pagination=paginated.pagination,
            comics=paginated.comics,
        )
        cache_manager.set("genres", cache_key, data)
        return data, False


scraper_service = ScraperService()
