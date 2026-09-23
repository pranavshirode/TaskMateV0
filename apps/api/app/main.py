from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import health_router, v1_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    # Error handlers
    register_error_handlers(app)

    # Routes
    app.include_router(health_router)
    app.include_router(v1_router)

    return app


app = create_app()
