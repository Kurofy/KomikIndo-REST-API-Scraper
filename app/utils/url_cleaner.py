import re
from urllib.parse import urlparse, urljoin
from app.config import get_base_url


def clean_slug(url_or_slug: str) -> str:
    """
    Extracts a clean slug from a relative or absolute URL or slug string.
    Examples:
        'https://komikindo.ch/komik/solo-swordmaster/' -> 'solo-swordmaster'
        '/komik/846048-eleceed/' -> '846048-eleceed'
        'solo-swordmaster-chapter-22/' -> 'solo-swordmaster-chapter-22'
        '/genres/action/' -> 'action'
    """
    if not url_or_slug:
        return ""
    
    # Strip URL query and fragment
    parsed = urlparse(url_or_slug)
    path = parsed.path if parsed.path else url_or_slug
    
    # Clean leading and trailing slashes
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return ""
    
    # Return the last path component
    return parts[-1]


def extract_comic_slug(url_or_path: str) -> str:
    """
    Extracts comic slug specifically from URLs like:
        'https://komikindo.ch/komik/solo-swordmaster/' -> 'solo-swordmaster'
        '/komik/846048-eleceed/' -> '846048-eleceed'
    """
    if not url_or_path:
        return ""
    parsed = urlparse(url_or_path)
    path = parsed.path if parsed.path else url_or_path
    match = re.search(r'/komik/([^/]+)/?', path)
    if match:
        return match.group(1).strip()
    return clean_slug(url_or_path)


def extract_chapter_slug(url_or_path: str) -> str:
    """
    Extracts chapter slug specifically from URLs like:
        'https://komikindo.ch/solo-swordmaster-chapter-22/' -> 'solo-swordmaster-chapter-22'
    """
    return clean_slug(url_or_path)


def extract_genre_slug(url_or_path: str) -> str:
    """
    Extracts genre slug specifically from URLs like:
        'https://komikindo.ch/genres/action/' -> 'action'
        '/genres/shounen' -> 'shounen'
    """
    if not url_or_path:
        return ""
    parsed = urlparse(url_or_path)
    path = parsed.path if parsed.path else url_or_path
    match = re.search(r'/genres?/([^/]+)/?', path)
    if match:
        return match.group(1).strip()
    return clean_slug(url_or_path)


def to_absolute_url(url_or_path: str, base_url: str = None) -> str:
    """Converts relative path to absolute URL using the active BASE_URL."""
    if not url_or_path:
        return ""
    if url_or_path.startswith(("http://", "https://")):
        return url_or_path
    base = base_url or get_base_url()
    return urljoin(base, url_or_path)
