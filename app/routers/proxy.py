import urllib.parse
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from app.config import get_base_url, settings

router = APIRouter(prefix="/api/v1", tags=["Image Proxy"])


@router.get("/image-proxy")
async def proxy_image(url: str = Query(..., description="Target image URL to stream")):
    """
    Streams image bytes directly from the target CDN while injecting 'Referer' and 'User-Agent',
    bypassing anti-hotlinking protection.
    Sets 'Cache-Control: public, max-age=86400'.
    """
    decoded_url = urllib.parse.unquote(url).strip()
    if not decoded_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid image URL scheme. Must start with http:// or https://")

    target_referer = get_base_url()
    headers = {
        "User-Agent": settings.default_user_agent,
        "Referer": f"{target_referer}/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }

    try:
        client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
        req = client.build_request("GET", decoded_url, headers=headers)
        res = await client.send(req, stream=True)

        if res.status_code != 200:
            await res.aclose()
            await client.aclose()
            raise HTTPException(
                status_code=res.status_code,
                detail=f"CDN returned HTTP {res.status_code} for target image",
            )

        content_type = res.headers.get("content-type", "image/jpeg")

        async def stream_generator():
            try:
                async for chunk in res.aiter_bytes(chunk_size=16384):
                    yield chunk
            finally:
                await res.aclose()
                await client.aclose()

        return StreamingResponse(
            stream_generator(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to stream proxied image: {str(e)}")
