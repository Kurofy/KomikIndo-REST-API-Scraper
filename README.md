# 📖 KomikIndo REST API Scraper

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

Sebuah **REST API scraper** yang *production-ready*, *resilient*, dan modular untuk [https://komikindo.ch/](https://komikindo.ch/). Dirancang khusus untuk menjadi *backend* yang andal bagi aplikasi *mobile comic reader* (Flutter, React Native) maupun *web frontend*.

---

## 🚀 Fitur Utama (Key Features)

- **Anti-Bot & TLS Fingerprint Impersonation**: Menggunakan `curl_cffi` dengan `impersonate="chrome120"` serta mekanisme *automated fallback* ke `httpx` menggunakan *browser headers* yang realistis untuk melewati proteksi Cloudflare/WAF *challenge blocks*.
- **In-Memory TTL Multi-Tier Caching**: Ditenagai oleh `cachetools` untuk memangkas *response time* hingga di bawah `50ms` pada *query* yang sering diakses:
  - *Homepage & Latest Updates*: `10 minutes` TTL
  - *Comic Detail & Search*: `30 minutes` TTL
  - *Chapter Images & Genres*: `24 hours` TTL
- **Dynamic Domain Management & Auto-Migration Detection**: `BASE_URL` domain tidak pernah di-*hardcode*. Sistem dapat mengecek *health* dari domain target, mendeteksi *TLD redirection migration* secara otomatis, atau meng-*update* `BASE_URL` secara dinamis saat *runtime* tanpa perlu me-*restart* *service*.
- **Anti-Hotlinking Image Proxy & Dual Mode**:
  - **Server Streaming Proxy** (`/api/v1/image-proxy?url=...`): Melakukan *streaming* gambar dari CDN dengan menginjeksi *header* `Referer` dan `User-Agent`, serta mengatur `Cache-Control: public, max-age=86400` dan `Access-Control-Allow-Origin: *`.
  - **Direct Client Fetching**: Setiap *image object* menyertakan `required_headers` (`{"Referer": BASE_URL, "User-Agent": "..."}`) sehingga aplikasi *mobile* seperti Flutter dapat melakukan *streaming* langsung dari CDN tanpa membebani *server bandwidth*.
- **Standardized Response Envelope**: Setiap *endpoint* mengembalikan *response envelope* yang konsisten mencakup `status`, `message`, `base_url_used`, `cached`, dan `data`.

---

## 📁 Arsitektur Proyek (Project Architecture)

```text
komikindo-api/
├── app/
│   ├── main.py                  # Entrypoint aplikasi FastAPI, CORS & error handling
│   ├── config.py                # Konfigurasi dinamis & penyimpanan runtime BASE_URL
│   ├── models/                  # Skema Pydantic (Data Validation)
│   │   ├── __init__.py
│   │   ├── common.py            # Wrapper APIResponse & Pagination
│   │   ├── comic.py             # Skema comic cards, details, genres, home data
│   │   └── chapter.py           # Skema chapter details & image pages
│   ├── routers/                 # Controller route API modular
│   │   ├── __init__.py
│   │   ├── home.py              # GET /api/v1/home, /api/v1/latest & /api/v1/popular
│   │   ├── comic.py             # GET /api/v1/comic/{comic_slug}
│   │   ├── chapter.py           # GET /api/v1/chapter/{chapter_slug}
│   │   ├── search.py            # GET /api/v1/search
│   │   ├── genres.py            # GET /api/v1/genres & /api/v1/genres/{slug}
│   │   ├── proxy.py             # GET /api/v1/image-proxy
│   │   └── config.py            # GET/POST /api/v1/config/domain
│   ├── services/                # Business logic & scraper engine
│   │   ├── __init__.py
│   │   ├── scraper.py           # Scraper orchestrator dengan TTL caching
│   │   ├── parser.py            # DOM parser menggunakan BeautifulSoup4 lxml
│   │   └── domain_service.py    # Detector untuk migrasi domain target
│   └── utils/                   # Modul helper & utilitas
│       ├── __init__.py
│       ├── http_client.py       # HTTP client (curl_cffi + httpx fallback)
│       ├── cache.py             # Manajer multi-tier TTL cache
│       └── url_cleaner.py       # Slug extractor dan URL normalizer
├── .env                         # Konfigurasi environment aktif
├── .env.example                 # Template konfigurasi environment
├── requirements.txt             # Daftar dependencies Python
├── test_live_api.py             # Suite untuk end-to-end live testing
└── README.md
```

---

## 🔍 Live Verified DOM Selectors

Tabel di bawah ini merinci *CSS Selectors* yang digunakan oleh *parser* untuk mengekstrak data dari DOM KomikIndo:

| Entity | Selector | Extracted Attributes |
|---|---|---|
| **Popular Comics** | `.mangapopuler .animepost` | Title, slug, thumbnail, type, color, latest chapter |
| **Latest Comics** | `.latestupdate-v2 .animepost` | Title, slug, thumbnail, rating, views, status, chapters |
| **Pagination** | `.pagination` | `a.next.page-numbers`, `a.prev.page-numbers`, page numbers |
| **Comic Detail** | `h1.entry-title`, `.spe span`, `.thumb img`, `[itemprop="ratingValue"]`, `.sinopsis` | Title, Alt title, Status, Author, Illustrator, Type, Rating, Synopsis |
| **Chapters List** | `#chapter_list li` | Chapter title, chapter slug, release date |
| **Chapter Images** | `#chimg-auh img` | `src`, `data-src` (diurutkan berdasarkan halaman *1-indexed*) |
| **Navigation** | `.nextprev a[rel="prev"]`, `a[rel="next"]`, `a[href*="/komik/"]` | Previous slug, Next slug, Parent comic slug |
| **Genres** | `/genres-sitemap.xml` | Daftar lengkap *canonical genre slugs* & judulnya |

---

## 🛠️ Instalasi & Persiapan (Installation & Setup)

### Prasyarat (Prerequisites)
- Python 3.11+
- Virtual environment (`venv` atau `uv`)

### 1. Clone & Setup Virtual Environment
```bash
# Buat dan aktifkan virtual environment
python -m venv .venv

# Untuk pengguna Windows PowerShell:
.\.venv\Scripts\activate

# Untuk pengguna Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment Variables
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```

| Variable | Default Value | Deskripsi |
|---|---|---|
| `BASE_URL` | `https://komikindo.ch` | Domain utama target *scraping* |
| `PORT` | `8000` | Port tempat *server* dijalankan |
| `PROXY_BASE_URL` | `http://localhost:8000` | Host URL yang digunakan untuk meng-generate `proxied_image_url` |

### 4. Jalankan Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Dokumentasi API interaktif dapat diakses secara langsung di:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🧪 Menjalankan Live Tests

Untuk memverifikasi bahwa ke-11 *endpoint* berjalan lancar mengambil *live data* dari `https://komikindo.ch/`, jalankan perintah berikut:
```bash
python test_live_api.py
```

---

## 📡 Dokumentasi Lengkap REST API (Endpoint Reference)

### Standar Response Envelope
Seluruh *endpoint* (kecuali *image streaming proxy*) mengembalikan struktur JSON *envelope* standar berikut:

```json
{
  "status": "success",
  "message": "Deskripsi status eksekusi",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
  "cached": false,
  "data": { ... }
}
```

### Ringkasan Endpoint

| Method | Endpoint | Deskripsi Singkat | Cache TTL |
|---|---|---|---|
| `GET` | `/api/v1/home` | Mengambil komik populer dan rilis terbaru di halaman utama | 10 Menit |
| `GET` | `/api/v1/latest` | Mengambil daftar komik terbaru dengan *pagination* | 10 Menit |
| `GET` | `/api/v1/search` | Mencari komik berdasarkan *keyword* | 30 Menit |
| `GET` | `/api/v1/genres` | Mengambil semua daftar genre yang tersedia | 24 Jam |
| `GET` | `/api/v1/genres/{slug}` | Mengambil daftar komik berdasarkan *genre slug* | 30 Menit |
| `GET` | `/api/v1/comic/{comic_slug}` | Mengambil detail metadata komik dan daftar *chapter* | 30 Menit |
| `GET` | `/api/v1/chapter/{chapter_slug}` | Mengambil daftar gambar per halaman untuk *chapter reader* | 24 Jam |
| `GET` | `/api/v1/image-proxy` | *Streaming proxy* untuk mem-bypass *anti-hotlinking* CDN | 24 Jam (HTTP) |
| `GET` | `/api/v1/config/domain` | Mengecek status kesehatan domain aktif & deteksi *redirect* | *No Cache* |
| `POST` | `/api/v1/config/domain` | Mengubah `BASE_URL` secara dinamis saat *runtime* | *No Cache* |

---

### 1. Home (`GET /api/v1/home`)
Mengambil daftar komik yang sedang populer/*trending* beserta *update* komik terbaru dari halaman utama.

- **Parameters**: *Tidak ada*
- **Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Home comics retrieved successfully",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
  "cached": true,
  "data": {
    "popular_comics": [
      {
        "title": "Eleceed",
        "comic_slug": "846048-eleceed",
        "thumbnail": "[https://komikindo.ch/wp-content/uploads/2020/12/Komik-Eleceed-219x319.jpg](https://komikindo.ch/wp-content/uploads/2020/12/Komik-Eleceed-219x319.jpg)",
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

---

### 2. Latest Updates (`GET /api/v1/latest`)
Mengambil daftar komik yang baru diperbarui lengkap dengan dukungan *pagination*.

- **Query Parameters**:
  | Parameter | Tipe | Wajib | Default | Deskripsi |
  |---|---|---|---|---|
  | `page` | `integer` | Tidak | `1` | Nomor halaman yang ingin diambil |

- **Contoh Request**: `GET /api/v1/latest?page=1`
- **Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Latest updates for page 1 retrieved successfully",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
  "cached": false,
  "data": {
    "pagination": {
      "current_page": 1,
      "has_next_page": true,
      "next_page": 2,
      "prev_page": null,
      "total_pages": 230
    },
    "comics": [
      {
        "title": "Solo Leveling: Ragnarok",
        "comic_slug": "solo-leveling-ragnarok",
        "thumbnail": "[https://komikindo.ch/wp-content/uploads/](https://komikindo.ch/wp-content/uploads/)...",
        "type": "Manhwa",
        "rating": "8.95",
        "status": "Berjalan",
        "latest_chapters": [ ... ]
      }
    ]
  }
}
```

<<<<<<< HEAD
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
=======
---

### 3. Search (`GET /api/v1/search`)
Mencari komik berdasarkan kata kunci (*keyword*) dengan dukungan *pagination*.

- **Query Parameters**:
  | Parameter | Tipe | Wajib | Default | Deskripsi |
  |---|---|---|---|---|
  | `q` | `string` | **Ya** | - | Kata kunci judul komik yang dicari |
  | `page` | `integer` | Tidak | `1` | Nomor halaman hasil pencarian |

- **Contoh Request**: `GET /api/v1/search?q=solo&page=1`
- **Response (`200 OK`)**:
>>>>>>> 1324027183efc11f3663affb3af4d3284f7f10aa
```json
{
  "status": "success",
  "message": "Search results for 'solo' on page 1 retrieved successfully",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
  "cached": false,
  "data": {
    "query": "solo",
    "pagination": {
      "current_page": 1,
      "has_next_page": true,
      "next_page": 2,
      "prev_page": null,
      "total_pages": 3
    },
    "comics": [ ... ]
  }
}
```

---

### 4. Genres (`GET /api/v1/genres` & `GET /api/v1/genres/{slug}`)

#### A. Daftar Semua Genre (`GET /api/v1/genres`)
Mengambil seluruh daftar genre komik kanonikal yang tersedia (sekitar 50+ genre).
- **Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Genres retrieved successfully",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
  "cached": true,
  "data": {
    "total_genres": 50,
    "genres": [
      {
        "title": "Action",
        "slug": "action",
        "endpoint": "/api/v1/genres/action"
      },
      {
        "title": "Adventure",
        "slug": "adventure",
        "endpoint": "/api/v1/genres/adventure"
      }
    ]
  }
}
```

#### B. Komik Berdasarkan Genre (`GET /api/v1/genres/{slug}`)
Mengambil daftar komik pada genre tertentu dengan *pagination*.
- **Path Parameters**:
  - `slug` (`string`, **Wajib**): *Identifier* genre (contoh: `action`, `fantasy`, `isekai`).
- **Query Parameters**:
  - `page` (`integer`, Opsional, Default: `1`): Nomor halaman.
- **Contoh Request**: `GET /api/v1/genres/action?page=1`

---

### 5. Comic Detail (`GET /api/v1/comic/{comic_slug}`)
Mengambil informasi metadata lengkap dari sebuah komik beserta daftar seluruh *chapter*-nya yang telah diurutkan.

- **Path Parameters**:
  | Parameter | Tipe | Wajib | Deskripsi |
  |---|---|---|---|
  | `comic_slug` | `string` | **Ya** | *Slug* unik dari komik (contoh: `846048-eleceed`) |

- **Contoh Request**: `GET /api/v1/comic/846048-eleceed`
- **Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Comic details for '846048-eleceed' retrieved successfully",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
  "cached": false,
  "data": {
    "title": "Eleceed",
    "alternative_title": "Элисед, 일렉시드",
    "comic_slug": "846048-eleceed",
    "thumbnail": "[https://komikindo.ch/wp-content/uploads/2020/12/Komik-Eleceed-219x319.jpg](https://komikindo.ch/wp-content/uploads/2020/12/Komik-Eleceed-219x319.jpg)",
    "rating": "8.89",
    "status": "Berjalan",
    "type": "Manhwa",
    "author": "Son Jae-Ho",
    "illustrator": "ZHENA",
    "synopsis": "Kaiden adalah pengguna kemampuan misterius yang bersembunyi di dalam tubuh kucing jalanan...",
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

---

### 6. Chapter Reader (`GET /api/v1/chapter/{chapter_slug}`)
Mengambil seluruh *array* URL gambar halaman komik beserta *slug* navigasi (*previous* / *next chapter* dan induk komiknya).

- **Path Parameters**:
  | Parameter | Tipe | Wajib | Deskripsi |
  |---|---|---|---|
  | `chapter_slug` | `string` | **Ya** | *Slug* unik dari chapter (contoh: `eleceed-chapter-422`) |

- **Contoh Request**: `GET /api/v1/chapter/eleceed-chapter-422`
- **Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Chapter 'eleceed-chapter-422' retrieved successfully with 27 pages",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
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
        "original_image_url": "[https://amatipolanyatirudesainnya.lol/.../001.webp](https://amatipolanyatirudesainnya.lol/.../001.webp)",
        "proxied_image_url": "http://localhost:8000/api/v1/image-proxy?url=https%3A%2F%2Famatipolanyatirudesainnya.lol%2F...",
        "required_headers": {
          "Referer": "[https://komikindo.ch](https://komikindo.ch)",
          "User-Agent": "Mozilla/5.0 ..."
        }
      }
    ]
  }
}
```

---

### 7. Image Streaming Proxy (`GET /api/v1/image-proxy`)
Melakukan *streaming binary image bytes* secara langsung dengan menyuntikkan *anti-hotlink headers* serta *CDN caching headers*. Sangat berguna untuk *web frontend* atau jaringan yang memblokir CDN komik.

- **Query Parameters**:
  | Parameter | Tipe | Wajib | Deskripsi |
  |---|---|---|---|
  | `url` | `string` | **Ya** | URL gambar asli dari CDN yang sudah di-*URL-encode* |

- **Response Headers**:
  - `Content-Type`: `image/webp` (atau `image/jpeg`, `image/png` menyesuaikan sumber)
  - `Cache-Control`: `public, max-age=86400`
  - `Access-Control-Allow-Origin`: `*`

---

### 8. Target Domain Management (`GET & POST /api/v1/config/domain`)

#### A. Cek Status & Kesehatan Domain (`GET /api/v1/config/domain`)
Mengecek *health* dari domain yang sedang digunakan saat ini, mengukur *latency*, dan mendeteksi apakah terjadi *redirection* ke TLD baru.

- **Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Domain status checked successfully",
  "base_url_used": "[https://komikindo.ch](https://komikindo.ch)",
  "cached": false,
  "data": {
    "configured_base_url": "[https://komikindo.ch](https://komikindo.ch)",
    "resolved_url": "[https://komikindo.ch/](https://komikindo.ch/)",
    "is_redirected": false,
    "status_code": 200,
    "latency_ms": 142.5
  }
}
```

#### B. Update Domain Saat Runtime (`POST /api/v1/config/domain`)
Mengubah `BASE_URL` target di dalam *in-memory store* secara instan dan langsung melakukan *flush/clear* pada seluruh *cache* tanpa perlu me-*restart server*. Jika `auto_detect` bernilai `true`, sistem akan otomatis melacak *redirect* dari domain lama dan menerapkan domain baru yang ditemukan.

- **Request Body (`application/json`)**:
```json
{
  "base_url": "[https://komikindo.ch](https://komikindo.ch)",
  "auto_detect": false
}
```

---

### ⚠️ Kode Status & Penanganan Error (Error Handling)

Jika terjadi kegagalan saat memproses permintaan, API akan mengembalikan kode HTTP yang sesuai dengan detail pesan *error*:

| Status Code | Kondisi | Solusi / Penanganan |
|---|---|---|
| `200 OK` | Request berhasil diproses | - |
| `400 Bad Request` | Parameter tidak valid (misal: `q` kosong pada *search* atau URL *proxy* rusak) | Periksa kembali *query parameter* yang dikirim |
| `404 Not Found` | *Slug* komik, *chapter*, atau *genre* tidak ditemukan di KomikIndo | Pastikan `slug` yang dikirim sudah benar |
| `502 Bad Gateway` | Target domain KomikIndo sedang *down*, terblokir WAF, atau pindah domain | Cek endpoint `/api/v1/config/domain` dan perbarui `base_url` |
| `504 Gateway Timeout` | Koneksi ke *server* KomikIndo melebihi batas waktu (*timeout*) | Coba ulangi *request* beberapa saat lagi |

---

## 📱 Integrasi Mobile Client (Flutter / React Native)

### Opsi A: Direct CDN Fetching (Zero Server Bandwidth - Direkomendasikan)
Aplikasi *mobile* dapat memuat gambar langsung dari CDN komik dengan menyertakan `required_headers` yang didapat dari *response* endpoint *chapter*:

```dart
// Contoh implementasi di Flutter menggunakan cached_network_image:
CachedNetworkImage(
  imageUrl: imagePage.originalImageUrl,
  httpHeaders: Map<String, String>.from(imagePage.requiredHeaders),
  placeholder: (context, url) => const Center(child: CircularProgressIndicator()),
  errorWidget: (context, url, error) => const Icon(Icons.broken_image),
)
```

### Opsi B: Proxied Fetching (Fallback & Web Frontend)
Jika ISP pengguna atau CDN memblokir *IP range* tertentu maupun *mobile headers*, gunakan URL dari *server image proxy*:

```dart
CachedNetworkImage(
  imageUrl: imagePage.proxiedImageUrl,
  placeholder: (context, url) => const Center(child: CircularProgressIndicator()),
  errorWidget: (context, url, error) => const Icon(Icons.broken_image),
)
```
