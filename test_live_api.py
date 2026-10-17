import sys
import urllib.parse
from fastapi.testclient import TestClient
from app.main import app

sys.stdout.reconfigure(encoding='utf-8')
client = TestClient(app)

def run_tests():
    print("==================================================")
    print("   RUNNING KOMIKINDO REST API TEST SUITE")
    print("==================================================")

    # 1. Test Root
    print("\n[TEST 1] GET / (Root health check)")
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.status_code}"
    print("PASS: Root status 200:", res.json()["service"])

    # 2. Test Home
    print("\n[TEST 2] GET /api/v1/home")
    res = client.get("/api/v1/home")
    assert res.status_code == 200, f"Home failed: {res.status_code} - {res.text}"
    body = res.json()
    assert body["status"] == "success"
    popular = body["data"]["popular_comics"]
    latest = body["data"]["latest_comics"]
    print(f"PASS: Popular comics: {len(popular)}, Latest comics: {len(latest)}")
    assert len(popular) > 0, "No popular comics extracted"
    assert len(latest) > 0, "No latest comics extracted"
    print(f"Sample Popular: '{popular[0]['title']}' (slug: {popular[0]['comic_slug']})")
    sample_comic_slug = popular[0]["comic_slug"]

    # Test cache hit on home
    res_cached = client.get("/api/v1/home")
    assert res_cached.json()["cached"] is True, "Home cache failed to register"
    print("PASS: In-memory TTL cache hit verified for /api/v1/home")

    # 3. Test Latest Updates (Paginated)
    print("\n[TEST 3] GET /api/v1/latest?page=1")
    res = client.get("/api/v1/latest?page=1")
    assert res.status_code == 200, f"Latest failed: {res.status_code}"
    body = res.json()
    comics = body["data"]["comics"]
    pagination = body["data"]["pagination"]
    print(f"PASS: Latest page 1 count: {len(comics)}, has_next: {pagination['has_next_page']}")
    assert len(comics) > 0

    # 3b. Test Popular Comics (Paginated)
    print("\n[TEST 3b] GET /api/v1/popular?page=1")
    res = client.get("/api/v1/popular?page=1")
    assert res.status_code == 200, f"Popular failed: {res.status_code}"
    body = res.json()
    pop_comics = body["data"]["comics"]
    pop_pagination = body["data"]["pagination"]
    print(f"PASS: Popular page 1 count: {len(pop_comics)}, total_pages: {pop_pagination['total_pages']}, has_next: {pop_pagination['has_next_page']}")
    assert len(pop_comics) > 0
    assert pop_pagination["total_pages"] is not None and pop_pagination["total_pages"] > 1
    print(f"Sample Popular item: {pop_comics[0]['title']} ({pop_comics[0]['comic_slug']})")

    # Test cache hit on popular
    res_cached = client.get("/api/v1/popular?page=1")
    assert res_cached.json()["cached"] is True, "Popular cache hit failed"
    print("PASS: In-memory TTL cache hit verified for /api/v1/popular?page=1")

    # 4. Test Search
    print("\n[TEST 4] GET /api/v1/search?q=solo&page=1")
    res = client.get("/api/v1/search?q=solo&page=1")
    assert res.status_code == 200, f"Search failed: {res.status_code}"
    body = res.json()
    search_results = body["data"]["comics"]
    print(f"PASS: Search for 'solo' returned {len(search_results)} comics")
    assert len(search_results) > 0

    # 5. Test Genres List
    print("\n[TEST 5] GET /api/v1/genres")
    res = client.get("/api/v1/genres")
    assert res.status_code == 200, f"Genres failed: {res.status_code}"
    genres = res.json()["data"]
    print(f"PASS: Genres count: {len(genres)}")
    assert len(genres) > 0
    sample_genre = genres[0]["slug"]
    print(f"Sample genre: {genres[0]['title']} (slug: {sample_genre})")

    # 6. Test Comics by Genre
    print(f"\n[TEST 6] GET /api/v1/genres/{sample_genre}?page=1")
    res = client.get(f"/api/v1/genres/{sample_genre}?page=1")
    assert res.status_code == 200, f"Genre comics failed: {res.status_code}"
    body = res.json()
    genre_comics = body["data"]["comics"]
    print(f"PASS: Genre '{sample_genre}' returned {len(genre_comics)} comics")
    assert len(genre_comics) > 0

    # 7. Test Comic Detail
    print(f"\n[TEST 7] GET /api/v1/comic/{sample_comic_slug}")
    res = client.get(f"/api/v1/comic/{sample_comic_slug}")
    assert res.status_code == 200, f"Comic detail failed: {res.status_code}"
    detail = res.json()["data"]
    print(f"PASS: Title: '{detail['title']}'")
    print(f"      Alt Title: {detail['alternative_title']}")
    print(f"      Status: {detail['status']}, Type: {detail['type']}, Rating: {detail['rating']}")
    print(f"      Genres count: {len(detail['genres'])}, Chapters count: {len(detail['chapters'])}")
    assert len(detail["chapters"]) > 0, "No chapters found in comic detail"
    sample_chapter_slug = detail["chapters"][0]["chapter_slug"]

    # 8. Test Chapter Detail & Reader Images
    print(f"\n[TEST 8] GET /api/v1/chapter/{sample_chapter_slug}")
    res = client.get(f"/api/v1/chapter/{sample_chapter_slug}")
    assert res.status_code == 200, f"Chapter detail failed: {res.status_code}"
    ch_data = res.json()["data"]
    print(f"PASS: Chapter Title: '{ch_data['chapter_title']}'")
    print(f"      Parent comic: {ch_data['comic_slug']}")
    print(f"      Prev slug: {ch_data['prev_chapter_slug']}, Next slug: {ch_data['next_chapter_slug']}")
    print(f"      Total page images: {ch_data['total_images']}")
    assert ch_data["total_images"] > 0, "No chapter page images extracted"
    first_image = ch_data["images"][0]
    print(f"      First page original URL: {first_image['original_image_url'][:80]}...")
    print(f"      First page proxied URL: {first_image['proxied_image_url'][:80]}...")
    print(f"      Required headers: {first_image['required_headers']}")

    # 9. Test Image Proxy
    print("\n[TEST 9] GET /api/v1/image-proxy?url=...")
    encoded_url = urllib.parse.quote_plus(first_image["original_image_url"])
    res = client.get(f"/api/v1/image-proxy?url={encoded_url}")
    assert res.status_code == 200, f"Image proxy failed: {res.status_code}"
    content_type = res.headers.get("content-type")
    content_len = len(res.content)
    cache_ctrl = res.headers.get("cache-control")
    print(f"PASS: Image proxy status 200, Content-Type: {content_type}, Bytes: {content_len}, Cache-Control: {cache_ctrl}")
    assert content_len > 0, "Image proxy returned 0 bytes"
    assert "image" in content_type.lower(), f"Unexpected content-type: {content_type}"

    # 10. Test Domain Config GET
    print("\n[TEST 10] GET /api/v1/config/domain")
    res = client.get("/api/v1/config/domain")
    assert res.status_code == 200, f"Domain status failed: {res.status_code}"
    domain_data = res.json()["data"]
    print(f"PASS: Current base URL: {domain_data['current_base_url']}")
    print(f"      Health: {domain_data['is_healthy']}, Response time: {domain_data['response_time_ms']}ms")

    # 11. Test Domain Config POST (Runtime Update)
    print("\n[TEST 11] POST /api/v1/config/domain")
    res = client.post("/api/v1/config/domain", json={"base_url": "https://komikindo.ch"})
    assert res.status_code == 200, f"Domain update failed: {res.status_code}"
    body = res.json()
    assert body["status"] == "success"
    print(f"PASS: Domain update result: {body['data']['message']}")

    print("\n==================================================")
    print("   ALL 11 TESTS PASSED SUCCESSFULLY ON LIVE DATA! ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
