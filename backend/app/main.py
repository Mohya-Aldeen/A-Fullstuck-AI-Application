"""
FastAPI application entrypoint.

Run locally with:
    uv run python -m uvicorn app.main:app --reload

Railway starts this module so it binds the platform PORT:
    uv run python -m app.main
"""

import time

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.me import router as me_router
from app.config import settings

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

log = structlog.get_logger("http")

app = FastAPI(title="Document Copilot")
app.include_router(me_router)
app.include_router(chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Vite may pick 5174+ when 5173 is busy — allow any local dev port.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("request_failed", method=request.method, path=request.url.path)
        raise
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check — used by Railway and local dev."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT)
