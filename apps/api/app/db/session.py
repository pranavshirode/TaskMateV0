import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)

engine = None
async_session_factory = None


async def init_db():
    global engine, async_session_factory
    settings = get_settings()
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        engine = create_async_engine(db_url, echo=settings.SQL_ECHO)
    else:
        engine = create_async_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=settings.SQL_ECHO,
        )
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    if db_url.startswith("sqlite"):
        import app.models  # noqa: F401
        from app.db.base import Base

        async with engine.begin() as conn:
            # Zero-config convenience for brand-new SQLite files only. Once Alembic manages the schema,
            # creating tables here would race the migrations (a new model + a reloading dev server would
            # create its table, and the next `alembic upgrade` would then fail with "table already exists").
            if await conn.run_sync(_is_migration_managed):
                logger.info("Schema managed by Alembic migrations; skipping create_all")
            else:
                await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


def _is_migration_managed(sync_conn) -> bool:
    from sqlalchemy import inspect, text

    if not inspect(sync_conn).has_table("alembic_version"):
        return False
    return sync_conn.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar() > 0


async def close_db():
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


async def get_db():
    if not async_session_factory:
        raise RuntimeError("Database not initialized")
    async with async_session_factory() as session:
        yield session
