import time
from urllib.parse import urlparse
import httpx
from curl_cffi import requests as curl_requests
from app.config import get_base_url, set_base_url, settings
from app.utils.cache import cache_manager


class DomainService:
    @staticmethod
    def check_domain() -> dict:
        current_base = get_base_url()
        start_time = time.time()
        redirected_url = None
        status_code = None
        is_healthy = False
        message = ""

        try:
            # Check with curl_cffi or httpx
            resp = curl_requests.get(
                current_base,
                headers={"User-Agent": settings.default_user_agent},
                impersonate="chrome120",
                timeout=10,
                allow_redirects=True,
            )
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            status_code = resp.status_code
            final_url = resp.url.rstrip("/") if hasattr(resp, "url") and resp.url else current_base

            # Check if domain changed
            current_netloc = urlparse(current_base).netloc
            final_netloc = urlparse(final_url).netloc

            if current_netloc != final_netloc:
                redirected_url = f"{urlparse(final_url).scheme}://{final_netloc}"
                message = f"Domain has migrated from {current_base} to {redirected_url}"
            else:
                message = "Domain is active and responding without migration redirects"

            is_healthy = status_code == 200
        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            message = f"Error checking domain: {str(e)}"

        return {
            "current_base_url": current_base,
            "status_code": status_code,
            "is_healthy": is_healthy,
            "response_time_ms": elapsed_ms,
            "detected_redirect_url": redirected_url,
            "migration_detected": redirected_url is not None,
            "message": message,
        }

    @staticmethod
    def update_base_url(new_url: str, auto_detect: bool = False) -> dict:
        if auto_detect:
            status = DomainService.check_domain()
            if status.get("detected_redirect_url"):
                target_url = status["detected_redirect_url"]
            else:
                target_url = status["current_base_url"]
        else:
            target_url = new_url

        old_url = get_base_url()
        updated_url = set_base_url(target_url)

        # Invalidate cache since domain has changed
        cache_manager.clear()

        return {
            "previous_base_url": old_url,
            "active_base_url": updated_url,
            "cache_cleared": True,
            "message": f"Active base URL successfully updated to {updated_url}",
        }


domain_service = DomainService()
