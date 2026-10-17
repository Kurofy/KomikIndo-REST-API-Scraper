import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self._base_url: str = os.getenv("BASE_URL", "https://komikindo.ch").rstrip("/")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "10000"))
        self.environment: str = os.getenv("ENVIRONMENT", "production")
        self.default_user_agent: str = os.getenv(
            "DEFAULT_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))

        # Cache TTLs (seconds)
        self.homepage_cache_ttl: int = int(os.getenv("HOMEPAGE_CACHE_TTL", "600"))
        self.latest_cache_ttl: int = int(os.getenv("LATEST_CACHE_TTL", "600"))
        self.popular_cache_ttl: int = int(os.getenv("POPULAR_CACHE_TTL", "600"))
        self.comic_detail_cache_ttl: int = int(os.getenv("COMIC_DETAIL_CACHE_TTL", "1800"))
        self.search_cache_ttl: int = int(os.getenv("SEARCH_CACHE_TTL", "1800"))
        self.genres_cache_ttl: int = int(os.getenv("GENRES_CACHE_TTL", "86400"))
        self.chapter_cache_ttl: int = int(os.getenv("CHAPTER_CACHE_TTL", "86400"))

    @property
    def base_url(self) -> str:
        return self._base_url

    def update_base_url(self, new_url: str) -> str:
        clean_url = new_url.strip().rstrip("/")
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"
        self._base_url = clean_url
        return self._base_url


settings = Settings()


def get_base_url() -> str:
    """Returns the current active target base URL."""
    return settings.base_url


def set_base_url(url: str) -> str:
    """Updates the active target base URL dynamically at runtime."""
    return settings.update_base_url(url)
