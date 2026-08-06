"""FastAPI app factory + Uvicorn entry for the gateway service."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from _common.env import get_settings
from gateway.routers import chat_router
from gateway.services.ratelimit import limiter, rate_limit_exceeded_handler


def create_app() -> FastAPI:
    """Build and configure the gateway FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="agent-chat API Gateway",
        version="0.1.0",
        summary="REST boundary between the frontend chat and the MCP orchestrator.",
    )
    # Rate limiting (R1, PLAN D1): the app's own envelope on a 429, never slowapi's
    # default JSON shape (RK1) — registered before CORS so CORS still wraps a 429.
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat_router)
    return app


app = create_app()


def main() -> None:
    """Uvicorn entry point (console script / ``python -m gateway.main``)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
