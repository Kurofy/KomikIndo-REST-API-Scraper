from app.routers.home import router as home_router
from app.routers.comic import router as comic_router
from app.routers.chapter import router as chapter_router
from app.routers.search import router as search_router
from app.routers.genres import router as genres_router
from app.routers.proxy import router as proxy_router
from app.routers.config import router as config_router

all_routers = [
    home_router,
    comic_router,
    chapter_router,
    search_router,
    genres_router,
    proxy_router,
    config_router,
]

__all__ = ["all_routers"]
