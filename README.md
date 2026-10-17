# KomikIndo REST API Scraper

A production-ready, resilient, and modular REST API scraper for [https://komikindo.ch/](https://komikindo.ch/) designed to power comic reader mobile applications (Flutter, React Native) and web frontends.

---

## 🚀 Key Features

- **Anti-Bot & TLS Fingerprint Impersonation**: Uses `curl_cffi` with `impersonate="chrome120"` and an automated fallback to `httpx` with realistic browser headers to prevent Cloudflare/WAF challenge blocks.
- **In-Memory TTL Multi-Tier Caching**: Powered by `cachetools`, reducing response times to <50ms for frequent queries:
  - Homepage & Latest Updates: 10 minutes TTL
  - Comic Detail & Search: 30 minutes TTL
  - Chapter Images & Genres: 24 hours TTL
- **Dynamic Domain Management & Auto-Migration Detection**: Domain base URL is never hardcoded. Check target domain health, auto-detect TLD redirection migrations, or update `BASE_URL` dynamically at runtime without restarting the service.
- **Anti-Hotlinking Image Proxy & Dual Mode**:
  - **Server Streaming Proxy** (`/api/v1/image-proxy?url=...`): Streams CDN images with `Referer` and `User-Agent` headers injected, setting `Cache-Control: public, max-age=86400` and `Access-Control-Allow-Origin: *`.
  - **Direct Client Fetching**: Every image object includes `required_headers` (`{"Referer": BASE_URL, "User-Agent": "..."}`) so mobile apps like Flutter can stream directly from CDNs without consuming server bandwidth.
- **Standardized Response Envelope**: Every endpoint returns an envelope containing `status`, `message`, `base_url_used`, `cached`, and `data`.

---

## 📁 Project Architecture

```
komikindo-api/
├── app/
│   ├── main.py                  # FastAPI app entrypoint, CORS & error handling
│   ├── config.py                # Dynamic configuration & runtime BASE_URL store
│   ├── models/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── common.py            # APIResponse wrapper & Pagination
│   │   ├── comic.py             # Comic cards, details, genres, home data
│   │   └── chapter.py           # Chapter details & image pages
│   ├── routers/                 # Modular API route controllers
│   │   ├── __init__.py
│   │   ├── home.py              # GET /api/v1/home, /api/v1/latest & /api/v1/popular
│   │   ├── comic.py             # GET /api/v1/comic/{comic_slug}
│   │   ├── chapter.py           # GET /api/v1/chapter/{chapter_slug}
│   │   ├── search.py            # GET /api/v1/search
│   │   ├── genres.py            # GET /api/v1/genres & /api/v1/genres/{slug}
│   │   ├── proxy.py             # GET /api/v1/image-proxy
│   │   └── config.py            # GET/POST /api/v1/config/domain
│   ├── services/                # Business & scraper logic
│   │   ├── __init__.py
│   │   ├── scraper.py           # Scraper orchestrator with TTL caching
│   │   ├── parser.py            # BeautifulSoup4 lxml DOM parser
│   │   └── domain_service.py    # Target domain migration detector
│   └── utils/                   # Helpers
│       ├── __init__.py
│       ├── http_client.py       # curl_cffi + httpx fallback client
│       ├── cache.py             # Multi-tier TTL cache manager
│       └── url_cleaner.py       # Slug extractor and URL normalizer
├── .env                         # Active configuration
├── .env.example                 # Template configuration
├── requirements.txt             # Python dependencies
├── test_live_api.py             # End-to-end live testing suite
└── README.md
```

---

## 🔍 Live Verified DOM Selectors

| Entity | Selector | Extracted Attributes |
|---|---|---|
| **Popular Comics** | `.mangapopuler .animepost` | Title, slug, thumbnail, type, color, latest chapter |
| **Latest Comics** | `.latestupdate-v2 .animepost` | Title, slug, thumbnail, rating, views, status, chapters |
| **Pagination** | `.pagination` | `a.next.page-numbers`, `a.prev.page-numbers`, page numbers |
| **Comic Detail** | `h1.entry-title`, `.spe span`, `.thumb img`, `[itemprop="ratingValue"]`, `.sinopsis` | Title, Alt title, Status, Author, Illustrator, Type, Rating, Synopsis |
| **Chapters List** | `#chapter_list li` | Chapter title, chapter slug, release date |
| **Chapter Images** | `#chimg-auh img` | `src`, `data-src` (ordered 1-indexed pages) |
| **Navigation** | `.nextprev a[rel="prev"]`, `a[rel="next"]`, `a[href*="/komik/"]` | Previous slug, Next slug, Parent comic slug |
| **Genres** | `/genres-sitemap.xml` | Complete canonical genre slugs & titles |

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual environment (`venv` or `uv`)

### 1. Clone & Setup Virtual Environment
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows Powershell:
.\.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation will be live at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🧪 Running Live Tests

Verify all 11 endpoints against live data from `https://komikindo.ch/`:
```bash
python test_live_api.py
```

---

## 📡 REST API Reference

All responses return the standard envelope:
```json
{
  "status": "success",
  "message": "...",
  "base_url_used": "https://komikindo.ch",
  "cached": false,
  "data": { ... }
}
```

### 1. Home (`GET /api/v1/home`)
Returns popular/trending comics and latest updated comics.
```json
{
  "status": "success",
  "message": "Home comics retrieved successfully",
  "base_url_used": "https://komikindo.ch",
  "cached": true,
  "data": {
    "popular_comics": [
      {
        "title": "Eleceed",
        "comic_slug": "846048-eleceed",
        "thumbnail": "https://komikindo.ch/wp-content/uploads/2020/12/Komik-Eleceed-219x319.jpg",
        "type": "Manhwa",
        "color": "Warna",
        "latest_chapters": [
          {
            "chapter_title": "Ch. 422",
            "chapter_slug": "eleceed-chapter-422",
            "release_date": "2 hari lalu"
          }
        ]
      }
    ],
    "latest_comics": [ ... ]
  }
}
```

### 2. Latest Updates (`GET /api/v1/latest?page={page}`)
Returns a paginated list of comic releases.
```json
{
  "status": "success",
  "message": "Latest updates for page 1 retrieved successfully",
  "base_url_used": "https://komikindo.ch",
  "cached": false,
  "data": {
    "pagination": {
      "current_page": 1,
      "has_next_page": true,
      "next_page": 2,
      "prev_page": null,
      "total_pages": 230
    },
    "comics": [ ... ]
  }
}
```

### 3. Popular Comics (`GET /api/v1/popular?page={page}`)
Returns a paginated list of all-time popular comics (e.g., Solo Leveling, One Piece, Martial Peak).
```json
{
  "status": "success",
  "message": "Popular comics for page 1 retrieved successfully",
  "base_url_used": "https://komikindo.ch",
  "cached": false,
  "data": {
    "pagination": {
      "current_page": 1,
      "has_next_page": true,
      "next_page": 2,
      "prev_page": null,
      "total_pages": 307
    },
    "comics": [ ... ]
  }
}
```

### 4. Search (`GET /api/v1/search?q={query}&page={page}`)
Search comics by keyword with pagination.
```json
{
  "status": "success",
  "message": "Search results for 'solo' on page 1 retrieved successfully",
  "base_url_used": "https://komikindo.ch",
  "cached": false,
  "data": {
    "query": "solo",
    "pagination": { "current_page": 1, "has_next_page": true, "next_page": 2 },
    "comics": [ ... ]
  }
}
```

### 4. Genres (`GET /api/v1/genres` & `GET /api/v1/genres/{slug}?page={page}`)
- `GET /api/v1/genres`: Returns all 50 available comic genres.
- `GET /api/v1/genres/action?page=1`: Returns paginated comics under the specified genre.

### 5. Comic Detail (`GET /api/v1/comic/{comic_slug}`)
Returns full metadata and ordered chapter list.
```json
{
  "status": "success",
  "message": "Comic details for '846048-eleceed' retrieved successfully",
  "base_url_used": "https://komikindo.ch",
  "cached": false,
  "data": {
    "title": "Eleceed",
    "alternative_title": "Элисед, 일렉시드",
    "comic_slug": "846048-eleceed",
    "thumbnail": "https://komikindo.ch/wp-content/uploads/2020/12/Komik-Eleceed-219x319.jpg",
    "rating": "8.89",
    "status": "Berjalan",
    "type": "Manhwa",
    "author": "Son Jae-Ho",
    "illustrator": "ZHENA",
    "synopsis": "...",
    "genres": [
      { "title": "Action", "slug": "action", "endpoint": "/api/v1/genres/action" }
    ],
    "chapters": [
      {
        "chapter_title": "Chapter 422",
        "chapter_slug": "eleceed-chapter-422",
        "release_date": "2 hari yang lalu"
      }
    ]
  }
}
```

### 6. Chapter Reader (`GET /api/v1/chapter/{chapter_slug}`)
Returns all page images and chapter navigation:
```json
{
  "status": "success",
  "message": "Chapter 'eleceed-chapter-422' retrieved successfully with 27 pages",
  "base_url_used": "https://komikindo.ch",
  "cached": false,
  "data": {
    "chapter_title": "Eleceed Chapter 422",
    "chapter_slug": "eleceed-chapter-422",
    "comic_slug": "846048-eleceed",
    "prev_chapter_slug": "eleceed-chapter-421",
    "next_chapter_slug": null,
    "total_images": 27,
    "images": [
      {
        "page_number": 1,
        "original_image_url": "https://amatipolanyatirudesainnya.lol/.../001.webp",
        "proxied_image_url": "http://localhost:8000/api/v1/image-proxy?url=https%3A%2F%2Famatipolanyatirudesainnya.lol%2F...",
        "required_headers": {
          "Referer": "https://komikindo.ch",
          "User-Agent": "Mozilla/5.0 ..."
        }
      }
    ]
  }
}
```

### 7. Image Streaming Proxy (`GET /api/v1/image-proxy?url={encoded_image_url}`)
Streams the image bytes directly with injected anti-hotlink headers and CDN caching headers:
- `Content-Type: image/webp` (or `image/jpeg`)
- `Cache-Control: public, max-age=86400`
- `Access-Control-Allow-Origin: *`

### 8. Target Domain Management (`GET & POST /api/v1/config/domain`)
- `GET /api/v1/config/domain`: Checks current domain health, latency, and whether redirection to a new TLD was detected.
- `POST /api/v1/config/domain`:
  ```json
  {
    "base_url": "https://komikindo.ch",
    "auto_detect": false
  }
  ```
  Updates target URL in memory and clears cache immediately.

---

## 📱 Mobile Client Integration (Flutter / React Native)

### Option A: Direct CDN Fetching (Zero Server Bandwidth)
Mobile clients can load images directly from the comic CDN using `required_headers` returned in the chapter response:
```dart
// Flutter Example with cached_network_image:
CachedNetworkImage(
  imageUrl: imagePage.originalImageUrl,
  httpHeaders: Map<String, String>.from(imagePage.requiredHeaders),
)
```

### Option B: Proxied Fetching
If the CDN blocks certain IP ranges or mobile headers, use the server image proxy:
```dart
CachedNetworkImage(
  imageUrl: imagePage.proxiedImageUrl,
)
```


---

---

## 🚀 Deploying to RamNaym Cloud (https://ramnaymcloud.com/)

RamNaym Cloud provides fast, simplified deployment for Python & FastAPI applications without complex VPS setup.

### Step-by-Step Deployment:
1. Log in to your [RamNaym Cloud Dashboard](https://ramnaymcloud.com/).
2. Click **Create Project** / **New Service**.
3. Select your deployment source:
   - **GitHub**: Connect your repository (`https://github.com/Kurofy/restapi`).
   - **ZIP Upload**: Alternatively, upload the project archive directly.
4. Configure the Project Settings:
   - **Runtime / Language**: `Python`
   - **Entry File / Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2 --proxy-headers
     ```
     *(Or simply `python main.py` or `uvicorn main:app --host 0.0.0.0 --port $PORT` thanks to [main.py](file:///d:/tes/api/main.py))*
   - **Build / Install Command**: `pip install -r requirements.txt` (detected automatically)
5. Add **Environment Variables** in the project Settings:
   - `BASE_URL`: `https://komikindo.ch`
   - `ENVIRONMENT`: `production`
   - `REQUEST_TIMEOUT`: `15`
6. Click **Deploy**. RamNaym Cloud will install the dependencies and boot your API with dynamic port binding.

---

## ☁️ Alternative: Deploying to Render.com

This repository also includes a [render.yaml](file:///d:/tes/api/render.yaml) blueprint specification if you ever want to deploy on Render:
1. Connect your GitHub repository in Render Dashboard.
2. Select Docker or Python environment.
3. Add the `BASE_URL=https://komikindo.ch` environment variable.

