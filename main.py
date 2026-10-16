"""
Root application entrypoint.
Enables plug-and-play execution across PaaS hosting platforms like RamNaym Cloud,
allowing deployment via `python main.py`, `uvicorn main:app`, or `uvicorn app.main:app`.
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=2,
        proxy_headers=True,
    )
