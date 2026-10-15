import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, get_base_url
from app.routers import all_routers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("komikindo-api")

app = FastAPI(
    title="Komikindo REST API Scraper",
    description=(
        "Production-ready, resilient, and modular REST API scraper for Komikindo "
        "designed to power comic reader mobile and web applications."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for cross-origin mobile/web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all modular routers
for r in all_routers:
    app.include_router(r)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": f"Internal Server Error: {str(exc)}",
            "base_url_used": get_base_url(),
            "cached": False,
            "data": None,
        },
    )


@app.get("/", tags=["Root"])
def root():
    """Health check and API overview."""
    return {
        "status": "online",
        "service": "Komikindo REST API Scraper",
        "version": "1.0.0",
        "target_base_url": get_base_url(),
        "documentation": "/docs",
        "endpoints": {
            "home": "/api/v1/home",
            "latest": "/api/v1/latest?page=1",
            "search": "/api/v1/search?q={query}&page=1",
            "genres": "/api/v1/genres",
            "genre_comics": "/api/v1/genres/{genre_slug}?page=1",
            "comic_detail": "/api/v1/comic/{comic_slug}",
            "chapter_detail": "/api/v1/chapter/{chapter_slug}",
            "image_proxy": "/api/v1/image-proxy?url={encoded_image_url}",
            "domain_config": "/api/v1/config/domain",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
