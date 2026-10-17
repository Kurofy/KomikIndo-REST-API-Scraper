from typing import Any, Tuple, Optional
from cachetools import TTLCache
from app.config import settings


class CacheManager:
    """
    In-memory TTL Cache Manager with distinct caches for different entity lifecycles.
    """

    def __init__(self):
        # Homepage & Latest Updates: 10 minutes TTL
        self.homepage_cache = TTLCache(maxsize=100, ttl=settings.homepage_cache_ttl)
        self.latest_cache = TTLCache(maxsize=500, ttl=settings.latest_cache_ttl)
        self.popular_cache = TTLCache(maxsize=500, ttl=settings.popular_cache_ttl)

        # Comic Detail & Search: 30 minutes TTL
        self.comic_detail_cache = TTLCache(maxsize=2000, ttl=settings.comic_detail_cache_ttl)
        self.search_cache = TTLCache(maxsize=1000, ttl=settings.search_cache_ttl)

        # Genres: 24 hours TTL
        self.genres_cache = TTLCache(maxsize=500, ttl=settings.genres_cache_ttl)

        # Chapter Images & Navigation: 24 hours TTL
        self.chapter_cache = TTLCache(maxsize=5000, ttl=settings.chapter_cache_ttl)

        self._registry = {
            "homepage": self.homepage_cache,
            "latest": self.latest_cache,
            "popular": self.popular_cache,
            "comic_detail": self.comic_detail_cache,
            "search": self.search_cache,
            "genres": self.genres_cache,
            "chapter": self.chapter_cache,
        }

    def get(self, cache_type: str, key: str) -> Tuple[Optional[Any], bool]:
        """
        Attempts to fetch an item from the specified cache.
        Returns (data, is_cached).
        """
        cache = self._registry.get(cache_type)
        if cache is not None and key in cache:
            return cache[key], True
        return None, False

    def set(self, cache_type: str, key: str, value: Any) -> None:
        """Stores an item in the specified cache."""
        cache = self._registry.get(cache_type)
        if cache is not None:
            cache[key] = value

    def clear(self, cache_type: Optional[str] = None) -> None:
        """Clears a specific cache or all caches."""
        if cache_type and cache_type in self._registry:
            self._registry[cache_type].clear()
        else:
            for cache in self._registry.values():
                cache.clear()


cache_manager = CacheManager()
