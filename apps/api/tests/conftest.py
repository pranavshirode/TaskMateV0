import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set env vars for testing before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["APP_ENV"] = "testing"
# Pin AI settings so a developer's local .env (which pydantic-settings also reads) cannot change test behaviour.
os.environ["AI_PROVIDER"] = "mock"
os.environ["AI_API_KEY"] = ""

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.client import Client
from app.models.enums import ClientStatus, ProjectStatus, TaskPriority, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(app, db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def create_test_user(db_session):
    async def _create_test_user(email="test@test.com", password="testpass123"):
        user = User(
            id=str(uuid.uuid4()),
            name="Test User",
            email=email,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        token = create_access_token({"sub": user.id})
        return user, token

    return _create_test_user


@pytest.fixture
async def auth_client(client, create_test_user):
    user, token = await create_test_user()
    client.headers["Authorization"] = f"Bearer {token}"
    client._test_user = user
    return client


@pytest.fixture
async def create_test_client_entity(db_session):
    async def _create(user_id, name="Test Client"):
        c = Client(id=str(uuid.uuid4()), user_id=user_id, name=name, status=ClientStatus.ACTIVE)
        db_session.add(c)
        await db_session.commit()
        return c

    return _create


@pytest.fixture
async def create_test_client(create_test_client_entity):
    return create_test_client_entity


@pytest.fixture
async def create_test_project(db_session):
    async def _create(user_id, client_id=None, name="Test Project"):
        p = Project(id=str(uuid.uuid4()), user_id=user_id, client_id=client_id, name=name, status=ProjectStatus.ACTIVE)
        db_session.add(p)
        await db_session.commit()
        return p

    return _create


@pytest.fixture
async def create_test_task(db_session):
    async def _create(
        user_id,
        project_id=None,
        client_id=None,
        title="Test Task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=None,
    ):
        t = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            project_id=project_id,
            client_id=client_id,
            title=title,
            status=status,
            priority=priority,
            due_date=due_date,
        )
        db_session.add(t)
        await db_session.commit()
        return t

    return _create
