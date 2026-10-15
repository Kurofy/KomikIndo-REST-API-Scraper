from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.config import get_base_url
from app.models.common import APIResponse
from app.services.domain_service import domain_service

router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])


class DomainUpdateRequest(BaseModel):
    base_url: Optional[str] = Field(default=None, description="New target base URL (e.g. 'https://komikindo.ch')")
    auto_detect: bool = Field(default=False, description="If true, auto-detects redirect to new domain from current domain")


@router.get("/domain", response_model=APIResponse[dict])
def get_domain_status():
    """
    Checks the current active target domain, latency, and whether a new TLD/migration redirect is detected.
    """
    try:
        status_info = domain_service.check_domain()
        return APIResponse(
            status="success",
            message="Target domain status checked",
            base_url_used=get_base_url(),
            cached=False,
            data=status_info,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check domain status: {str(e)}")


@router.post("/domain", response_model=APIResponse[dict])
def update_domain(payload: DomainUpdateRequest):
    """
    Manually updates the active target BASE_URL at runtime or auto-detects redirected TLD without restarting the server.
    Clears all in-memory caches upon successful domain update.
    """
    try:
        if not payload.auto_detect and not payload.base_url:
            raise HTTPException(
                status_code=400,
                detail="Either 'base_url' must be provided or 'auto_detect' must be set to True",
            )
        result = domain_service.update_base_url(
            new_url=payload.base_url or "",
            auto_detect=payload.auto_detect,
        )
        return APIResponse(
            status="success",
            message=result["message"],
            base_url_used=get_base_url(),
            cached=False,
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update domain: {str(e)}")
