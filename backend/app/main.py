"""
FastAPI application entrypoint.

Run locally with:
    uv run python -m uvicorn app.main:app --reload
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.me import router as me_router
from app.config import settings

app = FastAPI(title="Document Copilot")
app.include_router(me_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Vite may pick 5174+ when 5173 is busy — allow any local dev port.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check — used by Railway and local dev."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
