import re
from typing import List, Optional, Tuple
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from app.config import get_base_url, settings
from app.models.common import Pagination
from app.models.comic import (
    ComicCard,
    ChapterSummary,
    HomeData,
    PaginatedComics,
    ComicDetail,
    GenreItem,
)
from app.models.chapter import ChapterDetail, ImagePage
from app.utils.url_cleaner import (
    clean_slug,
    extract_comic_slug,
    extract_chapter_slug,
    extract_genre_slug,
    to_absolute_url,
)


def _clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    # Collapse multiple whitespace
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned if cleaned else None


def _clean_comic_title(title: Optional[str]) -> str:
    cleaned = _clean_text(title) or ""
    # Strip leading "Komik " prefix if it was added by theme
    if cleaned.lower().startswith("komik "):
        cleaned = cleaned[6:].strip()
    return cleaned


def _extract_image_src(img_tag) -> str:
    if not img_tag:
        return ""
    # Check data-src, data-lazy-src, src
    src = (
        img_tag.get("data-src")
        or img_tag.get("data-lazy-src")
        or img_tag.get("data-original")
        or img_tag.get("src")
        or ""
    )
    return to_absolute_url(src.strip())


def _extract_type_from_element(element) -> Optional[str]:
    if not element:
        return None
    # Check typeflag class
    flag = element.select_one(".typeflag")
    if flag:
        for cl in flag.get("class", []):
            if cl.lower() in ("manga", "manhwa", "manhua"):
                return cl.capitalize()
            if cl.lower() not in ("typeflag",):
                return cl
    # Check text inside nginfo-skroep or similar
    for el in element.select(".nginfo-skroep, .type"):
        txt = el.get_text(strip=True).lower()
        if "manhwa" in txt:
            return "Manhwa"
        elif "manhua" in txt:
            return "Manhua"
        elif "manga" in txt:
            return "Manga"
    return None


def _extract_color_from_element(element) -> Optional[str]:
    if not element:
        return None
    warna = element.select_one(".warnalabel, .fa-palette")
    if warna:
        parent_txt = warna.parent.get_text(strip=True) if warna.parent else warna.get_text(strip=True)
        if "warna" in parent_txt.lower():
            return "Warna"
        if "hitam putih" in parent_txt.lower():
            return "Hitam Putih"
        return _clean_text(parent_txt)
    return None


def parse_pagination(soup: BeautifulSoup, current_page: int) -> Pagination:
    pagination_el = soup.select_one(".pagination")
    if not pagination_el:
        return Pagination(current_page=current_page, has_next_page=False)

    next_el = pagination_el.select_one("a.next.page-numbers")
    prev_el = pagination_el.select_one("a.prev.page-numbers")
    
    has_next = next_el is not None
    next_page = current_page + 1 if has_next else None
    prev_page = current_page - 1 if prev_el is not None and current_page > 1 else None

    # Find total pages if available
    total_pages = None
    page_numbers = []
    for a in pagination_el.select("a.page-numbers, span.page-numbers"):
        txt = a.get_text(strip=True)
        if txt.isdigit():
            page_numbers.append(int(txt))
    if page_numbers:
        total_pages = max(page_numbers)

    return Pagination(
        current_page=current_page,
        has_next_page=has_next,
        next_page=next_page,
        prev_page=prev_page,
        total_pages=total_pages,
    )


def parse_homepage(html: str) -> HomeData:
    soup = BeautifulSoup(html, "lxml")
    popular_comics: List[ComicCard] = []
    latest_comics: List[ComicCard] = []

    # 1. Parse Popular Comics
    pop_container = soup.select_one(".mangapopuler, .post-show.mangapopuler")
    if pop_container:
        for item in pop_container.select(".animepost"):
            link_el = item.select_one(".animposx > a") or item.select_one("a")
            if not link_el:
                continue
            href = link_el.get("href", "")
            slug = extract_comic_slug(href)
            if not slug:
                continue

            title_el = item.select_one(".tt h3 a") or item.select_one(".tt h3") or link_el
            title = _clean_comic_title(title_el.get_text(strip=True) if title_el else link_el.get("title"))
            img_tag = item.select_one("img")
            thumbnail = _extract_image_src(img_tag)
            comic_type = _extract_type_from_element(item)
            color = _extract_color_from_element(item)

            latest_chaps: List[ChapterSummary] = []
            ch_a = item.select_one(".adds .lsch a")
            if ch_a:
                ch_title = _clean_text(ch_a.get_text(strip=True)) or "Chapter"
                ch_slug = extract_chapter_slug(ch_a.get("href", ""))
                dt = item.select_one(".adds .lsch .datech")
                ch_date = _clean_text(dt.get_text(strip=True)) if dt else None
                latest_chaps.append(ChapterSummary(
                    chapter_title=ch_title,
                    chapter_slug=ch_slug,
                    release_date=ch_date,
                ))

            popular_comics.append(ComicCard(
                title=title,
                comic_slug=slug,
                thumbnail=thumbnail,
                type=comic_type,
                color=color,
                latest_chapters=latest_chaps,
            ))

    # 2. Parse Latest Updates
    latest_container = soup.select_one(".latestupdate-v2, .listupd.latestupdate-v2")
    if latest_container:
        for item in latest_container.select(".animepost"):
            link_el = item.select_one(".animepostxx-top > a") or item.select_one("a")
            if not link_el:
                continue
            href = link_el.get("href", "")
            slug = extract_comic_slug(href)
            if not slug:
                continue

            title_el = item.select_one(".animepostxx-top-bottom .tt h3") or item.select_one(".animepostxx-top-bottom .tt h4")
            title = _clean_comic_title(title_el.get_text(strip=True) if title_el else link_el.get("title"))
            img_tag = item.select_one("img")
            thumbnail = _extract_image_src(img_tag)
            comic_type = _extract_type_from_element(item)
            color = _extract_color_from_element(item)

            # Rating
            rating_val = None
            star = item.select_one(".fa-star")
            if star and star.parent:
                rating_val = _clean_text(star.parent.get_text(strip=True))

            # Views
            views_val = None
            eye = item.select_one(".fa-eye")
            if eye and eye.parent:
                views_val = _clean_text(eye.parent.get_text(strip=True))

            # Status
            status_val = None
            status_el = item.select_one(".status-skroep")
            if status_el:
                status_val = _clean_text(status_el.get_text(strip=True))

            # Chapters
            latest_chaps: List[ChapterSummary] = []
            for ch in item.select(".list-ch-skroep .lsch a, .lsch a"):
                ch_title = _clean_text(ch.get_text(strip=True)) or "Chapter"
                ch_slug = extract_chapter_slug(ch.get("href", ""))
                latest_chaps.append(ChapterSummary(
                    chapter_title=ch_title,
                    chapter_slug=ch_slug,
                ))

            latest_comics.append(ComicCard(
                title=title,
                comic_slug=slug,
                thumbnail=thumbnail,
                type=comic_type,
                rating=rating_val,
                views=views_val,
                color=color,
                status=status_val,
                latest_chapters=latest_chaps,
            ))

    return HomeData(popular_comics=popular_comics, latest_comics=latest_comics)


def parse_comic_list(html: str, current_page: int) -> PaginatedComics:
    soup = BeautifulSoup(html, "lxml")
    comics: List[ComicCard] = []

    for item in soup.select(".animepost"):
        link_el = item.select_one(".animposx > a") or item.select_one("a")
        if not link_el:
            continue
        href = link_el.get("href", "")
        slug = extract_comic_slug(href)
        if not slug:
            continue

        title_el = (
            item.select_one(".tt h3 a")
            or item.select_one(".tt h4 a")
            or item.select_one(".tt h3")
            or item.select_one(".tt h4")
            or link_el
        )
        title = _clean_comic_title(title_el.get_text(strip=True) if title_el else link_el.get("title"))
        img_tag = item.select_one("img")
        thumbnail = _extract_image_src(img_tag)
        comic_type = _extract_type_from_element(item)
        color = _extract_color_from_element(item)

        # Rating
        rating_val = None
        rating_el = item.select_one(".rating i, [itemprop='ratingValue'], .fa-star")
        if rating_el:
            if rating_el.name == "i" and rating_el.get("class") and "fa-star" in rating_el.get("class"):
                rating_val = _clean_text(rating_el.parent.get_text(strip=True)) if rating_el.parent else None
            else:
                rating_val = _clean_text(rating_el.get_text(strip=True))

        # Chapters
        latest_chaps: List[ChapterSummary] = []
        for lsch in item.select(".adds .lsch, .list-ch-skroep .lsch"):
            ch_a = lsch.select_one("a")
            if ch_a:
                ch_title = _clean_text(ch_a.get_text(strip=True)) or "Chapter"
                ch_slug = extract_chapter_slug(ch_a.get("href", ""))
                dt = lsch.select_one(".datech, .dt")
                ch_date = _clean_text(dt.get_text(strip=True)) if dt else None
                latest_chaps.append(ChapterSummary(
                    chapter_title=ch_title,
                    chapter_slug=ch_slug,
                    release_date=ch_date,
                ))

        comics.append(ComicCard(
            title=title,
            comic_slug=slug,
            thumbnail=thumbnail,
            type=comic_type,
            rating=rating_val,
            color=color,
            latest_chapters=latest_chaps,
        ))

    pagination = parse_pagination(soup, current_page)
    return PaginatedComics(pagination=pagination, comics=comics)


def parse_comic_detail(html: str, comic_slug: str) -> ComicDetail:
    soup = BeautifulSoup(html, "lxml")

    # Title
    title_el = soup.select_one("h1.entry-title") or soup.select_one(".entry-title")
    title = _clean_comic_title(title_el.get_text(strip=True) if title_el else comic_slug)

    # Thumbnail
    thumb_img = soup.select_one(".thumb img")
    thumbnail = _extract_image_src(thumb_img)

    # Rating
    rating_el = (
        soup.select_one('[itemprop="ratingValue"]')
        or soup.select_one(".rating strong")
        or soup.select_one(".archiveanime-rating i")
    )
    rating = _clean_text(rating_el.get_text(strip=True)) if rating_el else None

    # Metadata from .spe spans
    alt_title = None
    status = None
    author = None
    illustrator = None
    comic_type = None

    spe = soup.select_one(".spe")
    if spe:
        for span in spe.find_all("span"):
            txt = span.get_text(strip=True)
            if "Judul Alternatif:" in txt:
                alt_title = _clean_text(txt.split("Judul Alternatif:", 1)[1])
            elif "Status:" in txt:
                status = _clean_text(txt.split("Status:", 1)[1])
            elif "Pengarang:" in txt:
                author = _clean_text(txt.split("Pengarang:", 1)[1])
            elif "Ilustrator:" in txt:
                illustrator = _clean_text(txt.split("Ilustrator:", 1)[1])
            elif "Jenis Komik:" in txt:
                comic_type = _clean_text(txt.split("Jenis Komik:", 1)[1])

    # Synopsis
    synopsis_el = (
        soup.select_one('.entry-content[itemprop="description"]')
        or soup.select_one(".sinopsis")
        or soup.select_one(".entry-content")
    )
    synopsis = _clean_text(synopsis_el.get_text(strip=True)) if synopsis_el else None

    # Genres
    genres: List[GenreItem] = []
    for g in soup.select(".genre-info a"):
        g_title = _clean_text(g.get_text(strip=True))
        g_slug = extract_genre_slug(g.get("href", ""))
        if g_slug and g_title:
            genres.append(GenreItem(
                title=g_title,
                slug=g_slug,
                endpoint=f"/api/v1/genres/{g_slug}",
            ))

    # Chapters list
    chapters: List[ChapterSummary] = []
    chap_items = soup.select("#chapter_list li, .chapter-list li, ul.clstyle li")
    for li in chap_items:
        ch_a = li.select_one(".lchx a") or li.select_one("a")
        if not ch_a:
            continue
        
        # Clean chapter title (e.g. Chapter <chapter>22</chapter>)
        # We can extract text with spaces preserved
        ch_title = " ".join(ch_a.stripped_strings)
        ch_slug = extract_chapter_slug(ch_a.get("href", ""))
        
        dt_el = li.select_one(".dt")
        dt_text = _clean_text(dt_el.get_text(strip=True)) if dt_el else None

        chapters.append(ChapterSummary(
            chapter_title=ch_title,
            chapter_slug=ch_slug,
            release_date=dt_text,
        ))

    return ComicDetail(
        title=title,
        alternative_title=alt_title,
        comic_slug=comic_slug,
        thumbnail=thumbnail,
        rating=rating,
        status=status,
        type=comic_type,
        author=author,
        illustrator=illustrator,
        synopsis=synopsis,
        genres=genres,
        chapters=chapters,
    )


def parse_chapter_detail(
    html: str,
    chapter_slug: str,
    base_api_url: str,
) -> ChapterDetail:
    soup = BeautifulSoup(html, "lxml")

    # Chapter Title
    h1_el = soup.select_one("h1.entry-title") or soup.select_one("h1")
    raw_title = h1_el.get_text(strip=True) if h1_el else chapter_slug
    chapter_title = _clean_comic_title(raw_title)

    # Images from #chimg-auh img
    images: List[ImagePage] = []
    img_elements = soup.select("#chimg-auh img, .reader-area img")
    
    # Required headers for direct CDN access by mobile clients
    current_base_url = get_base_url()
    required_headers = {
        "Referer": current_base_url,
        "User-Agent": settings.default_user_agent,
    }

    page_counter = 1
    for img in img_elements:
        raw_src = (
            img.get("data-src")
            or img.get("src")
            or img.get("data-lazy-src")
            or img.get("data-original")
            or ""
        ).strip()

        # Skip empty or placeholder tracking pixels
        if not raw_src or raw_src.startswith("data:"):
            continue
        
        original_img_url = to_absolute_url(raw_src)
        encoded_url = quote_plus(original_img_url)
        proxied_url = f"{base_api_url.rstrip('/')}/api/v1/image-proxy?url={encoded_url}"

        images.append(ImagePage(
            page_number=page_counter,
            original_image_url=original_img_url,
            proxied_image_url=proxied_url,
            required_headers=required_headers,
        ))
        page_counter += 1

    # Navigation slugs: prev, next, comic
    prev_chapter_slug: Optional[str] = None
    next_chapter_slug: Optional[str] = None
    comic_slug: str = ""

    # Check rel="prev" and rel="next"
    prev_el = soup.select_one('.nextprev a[rel="prev"], a[rel="prev"]')
    if prev_el and prev_el.get("href"):
        prev_chapter_slug = extract_chapter_slug(prev_el["href"])

    next_el = soup.select_one('.nextprev a[rel="next"], a[rel="next"]')
    if next_el and next_el.get("href"):
        next_chapter_slug = extract_chapter_slug(next_el["href"])

    # Parent comic link (often "Daftar Chapter" in .nextprev)
    comic_el = soup.select_one('.nextprev a[href*="/komik/"]') or soup.select_one('a[href*="/komik/"]')
    if comic_el and comic_el.get("href"):
        comic_slug = extract_comic_slug(comic_el["href"])
    else:
        # Fallback: derive comic_slug from chapter_slug (e.g. "solo-swordmaster-chapter-22" -> "solo-swordmaster")
        comic_slug = re.sub(r'-chapter-.*$', '', chapter_slug)

    return ChapterDetail(
        chapter_title=chapter_title,
        chapter_slug=chapter_slug,
        comic_slug=comic_slug,
        prev_chapter_slug=prev_chapter_slug,
        next_chapter_slug=next_chapter_slug,
        total_images=len(images),
        images=images,
    )


def parse_genres_sitemap(xml_content: str) -> List[GenreItem]:
    soup = BeautifulSoup(xml_content, "xml")
    genres: List[GenreItem] = []
    seen = set()

    for loc in soup.select("loc"):
        url = loc.get_text(strip=True)
        if "/genres/" in url:
            slug = extract_genre_slug(url)
            if slug and slug not in seen:
                seen.add(slug)
                # Format friendly title: "action-supernatural" -> "Action Supernatural"
                title = slug.replace("-", " ").title()
                genres.append(GenreItem(
                    title=title,
                    slug=slug,
                    endpoint=f"/api/v1/genres/{slug}",
                ))
    return sorted(genres, key=lambda g: g.title)
