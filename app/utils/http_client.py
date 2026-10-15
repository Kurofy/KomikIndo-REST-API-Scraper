import logging
from typing import Optional, Dict
import httpx
from curl_cffi import requests as curl_requests
from app.config import settings, get_base_url

logger = logging.getLogger(__name__)


class HttpClient:
    """
    Resilient HTTP Client with TLS fingerprint impersonation (curl_cffi)
    and fallback to httpx with realistic browser headers.
    """

    def __init__(self):
        self.default_headers = {
            "User-Agent": settings.default_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

    def _get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = self.default_headers.copy()
        headers["Referer"] = get_base_url()
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def get(
        self,
        url: str,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        allow_redirects: bool = True,
    ) -> str:
        """
        Synchronous GET request.
        Attempts curl_cffi with Chrome 120 impersonation first.
        Falls back to httpx if curl_cffi encounters an error.
        """
        req_timeout = timeout or settings.request_timeout
        headers = self._get_headers(custom_headers)

        # 1. Primary: curl_cffi with impersonate="chrome120"
        try:
            response = curl_requests.get(
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=req_timeout,
                allow_redirects=allow_redirects,
            )
            if response.status_code == 200:
                return response.text
            elif response.status_code in (301, 302, 307, 308) and allow_redirects:
                # Handle manual redirect if needed
                redirect_url = response.headers.get("Location")
                if redirect_url:
                    return self.get(redirect_url, custom_headers=custom_headers, timeout=req_timeout)
            logger.warning("curl_cffi returned status code %s for %s", response.status_code, url)
            # If 404 or other standard HTTP code, return text or let fallback try
            if response.status_code != 403:
                return response.text
        except Exception as e:
            logger.warning("curl_cffi failed for %s: %s. Attempting httpx fallback.", url, str(e))

        # 2. Fallback: httpx
        try:
            with httpx.Client(
                headers=headers,
                timeout=req_timeout,
                follow_redirects=allow_redirects,
            ) as client:
                res = client.get(url)
                return res.text
        except Exception as fallback_err:
            logger.error("HTTP request completely failed for %s: %s", url, str(fallback_err))
            raise RuntimeError(f"Failed to fetch content from {url}: {fallback_err}") from fallback_err


http_client = HttpClient()
