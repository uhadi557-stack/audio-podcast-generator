"""
app/main.py

Purpose
-------
This is the entrypoint of the whole backend. Run it with:

    uvicorn app.main:app --reload

What it does:
1. Creates the FastAPI `app` object.
2. Configures logging once at startup.
3. Adds CORS middleware — controls who is allowed to call *this* backend
   (your React app on localhost:3000). This is unrelated to your backend
   calling Fish Audio — server-to-server requests are never subject to
   CORS, since CORS is a browser security mechanism only.
4. Registers a `/health` route so you can confirm the server is alive.
5. Registers the podcast router (research/analyze/script endpoints).
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import podcast
from app.core.config import get_settings
from app.core.exceptions import UpstreamAPIError
from app.core.logging_config import configure_logging

configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Deep Research Podcaster API",
    description="Python/FastAPI backend for the Deep Research Podcaster pipeline.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health_check() -> dict:
    return {"status": "ok", "environment": settings.app_env}


@app.exception_handler(UpstreamAPIError)
async def upstream_api_error_handler(request: Request, exc: UpstreamAPIError) -> JSONResponse:
    logger.error("Upstream API error from %s: %s", exc.service, exc)
    return JSONResponse(
        status_code=502,
        content={
            "error": "upstream_api_error",
            "service": exc.service,
            "message": str(exc),
        },
    )


app.include_router(podcast.router, prefix="/api", tags=["podcast"])