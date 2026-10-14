import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Make `app` importable when run as `python scripts/seed_db.py` from apps/api (e.g. inside the API container).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.models.client import Client
from app.models.enums import (
    ClientStatus,
    ProjectStatus,
    RepositoryProvider,
    TaskEventType,
    TaskPriority,
    TaskStatus,
)
from app.models.project import Project
from app.models.repository import Repository
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.task_label import TaskLabel
from app.models.user import User


async def seed():
    print("Starting seed script...")
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        # Create user
        result = await db.execute(select(User).filter_by(email="alex@taskmate.dev"))
        user = result.scalars().first()

        if not user:
            print("Creating demo user...")
            user = User(
                id=str(uuid.uuid4()),
                name="Alex Developer",
                email="alex@taskmate.dev",
                password_hash=get_password_hash("password123"),
            )
            db.add(user)
            await db.commit()
            print("Demo user created.")
        else:
            print("Demo user already exists.")

        # Create clients
        print("Checking clients...")
        result = await db.execute(select(Client).filter_by(user_id=user.id))
        clients = result.scalars().all()
        client_map = {c.name: c for c in clients}

        if "Acme Technologies" not in client_map:
            c1 = Client(
                id=str(uuid.uuid4()),
                user_id=user.id,
                name="Acme Technologies",
                company_name="Acme Technologies Inc.",
                email="contact@acme.tech",
                status=ClientStatus.ACTIVE,
            )
            db.add(c1)
            client_map["Acme Technologies"] = c1

        if "ByteForge Labs" not in client_map:
            c2 = Client(
                id=str(uuid.uuid4()),
                user_id=user.id,
                name="ByteForge Labs",
                company_name="ByteForge Labs LLC",
                email="hello@byteforge.io",
                status=ClientStatus.ACTIVE,
            )
            db.add(c2)
            client_map["ByteForge Labs"] = c2

        await db.commit()

        # Create projects
        print("Checking projects...")
        result = await db.execute(select(Project).filter_by(user_id=user.id))
        projects = result.scalars().all()
        project_map = {p.name: p for p in projects}

        today = datetime.now(timezone.utc).date()

        if "Acme SaaS Dashboard" not in project_map:
            p1 = Project(
                id=str(uuid.uuid4()),
                user_id=user.id,
                client_id=client_map["Acme Technologies"].id,
                name="Acme SaaS Dashboard",
                description="Full-stack SaaS dashboard for Acme Technologies",
                status=ProjectStatus.ACTIVE,
                start_date=today - timedelta(days=30),
                deadline=today + timedelta(days=60),
            )
            db.add(p1)
            project_map["Acme SaaS Dashboard"] = p1

        if "Acme Mobile App" not in project_map:
            p2 = Project(
                id=str(uuid.uuid4()),
                user_id=user.id,
                client_id=client_map["Acme Technologies"].id,
                name="Acme Mobile App",
                description="React Native mobile app for Acme",
                status=ProjectStatus.PLANNING,
            )
            db.add(p2)
            project_map["Acme Mobile App"] = p2

        if "ByteForge API" not in project_map:
            p3 = Project(
                id=str(uuid.uuid4()),
                user_id=user.id,
                client_id=client_map["ByteForge Labs"].id,
                name="ByteForge API",
                description="REST API for ByteForge platform",
                status=ProjectStatus.ACTIVE,
                start_date=today - timedelta(days=14),
                deadline=today + timedelta(days=45),
            )
            db.add(p3)
            project_map["ByteForge API"] = p3

        await db.commit()

        # Create repositories
        print("Checking repositories...")
        result = await db.execute(select(Repository))
        repos = result.scalars().all()
        repo_map = {r.name: r for r in repos}

        if "acme-dashboard" not in repo_map:
            r1 = Repository(
                id=str(uuid.uuid4()),
                project_id=project_map["Acme SaaS Dashboard"].id,
                name="acme-dashboard",
                url="https://github.com/acme/acme-dashboard",
                provider=RepositoryProvider.GITHUB,
                default_branch="main",
            )
            db.add(r1)

        if "byteforge-api" not in repo_map:
            r2 = Repository(
                id=str(uuid.uuid4()),
                project_id=project_map["ByteForge API"].id,
                name="byteforge-api",
                url="https://github.com/byteforge/api",
                provider=RepositoryProvider.GITHUB,
                default_branch="main",
            )
            db.add(r2)

        await db.commit()

        # Create labels
        print("Checking labels...")
        result = await db.execute(select(TaskLabel).filter_by(user_id=user.id))
        labels = result.scalars().all()
        label_map = {label.name: label for label in labels}

        label_defs = [
            ("bug", "#ef4444"),
            ("feature", "#3b82f6"),
            ("frontend", "#8b5cf6"),
            ("backend", "#10b981"),
            ("urgent", "#f97316"),
            ("client-request", "#06b6d4"),
        ]
        for ln, lc in label_defs:
            if ln not in label_map:
                lbl = TaskLabel(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    name=ln,
                    color=lc,
                )
                db.add(lbl)
                label_map[ln] = lbl

        await db.commit()

        # Create tasks
        print("Checking tasks...")
        result = await db.execute(select(Task).filter_by(user_id=user.id))
        tasks = result.scalars().all()
        if not tasks:
            print("Creating tasks...")

            task_data = [
                {
                    "title": "Fix authentication bug",
                    "description": "Users are getting logged out unexpectedly after token refresh",
                    "status": TaskStatus.IN_PROGRESS,
                    "priority": TaskPriority.HIGH,
                    "due": today,
                },
                {
                    "title": "Update dashboard API",
                    "description": "Add pagination and filtering to the dashboard endpoints",
                    "status": TaskStatus.TODO,
                    "priority": TaskPriority.MEDIUM,
                    "due": today + timedelta(days=2),
                },
                {
                    "title": "Add password reset",
                    "description": "Implement forgot password flow with email verification",
                    "status": TaskStatus.REVIEW,
                    "priority": TaskPriority.HIGH,
                    "due": today + timedelta(days=1),
                },
                {
                    "title": "Update API documentation",
                    "description": "Bring OpenAPI docs up to date with latest endpoints",
                    "status": TaskStatus.TODO,
                    "priority": TaskPriority.LOW,
                    "due": today - timedelta(days=1),
                },
                {
                    "title": "Fix rate limiting middleware",
                    "description": "Rate limiter not working correctly with async endpoints",
                    "status": TaskStatus.REVIEW,
                    "priority": TaskPriority.HIGH,
                    "due": today - timedelta(days=2),
                },
                {
                    "title": "Client meeting notes",
                    "description": "Document decisions from the Acme quarterly review",
                    "status": TaskStatus.COMPLETED,
                    "priority": TaskPriority.MEDIUM,
                    "due": today - timedelta(days=3),
                },
                {
                    "title": "Server migration planning",
                    "description": "Plan migration from AWS to GCP for ByteForge",
                    "status": TaskStatus.IN_PROGRESS,
                    "priority": TaskPriority.URGENT,
                    "due": today,
                },
                {
                    "title": "Write unit tests for auth module",
                    "description": "Increase test coverage for authentication service",
                    "status": TaskStatus.TODO,
                    "priority": TaskPriority.LOW,
                    "due": today + timedelta(days=5),
                },
                {
                    "title": "Setup CI/CD pipeline",
                    "description": "GitHub Actions CI/CD for the Acme dashboard",
                    "status": TaskStatus.COMPLETED,
                    "priority": TaskPriority.HIGH,
                    "due": today - timedelta(days=10),
                },
                {
                    "title": "Fix memory leak in worker",
                    "description": "Background worker process leaking memory after 24h",
                    "status": TaskStatus.BLOCKED,
                    "priority": TaskPriority.URGENT,
                    "due": today - timedelta(days=1),
                },
            ]

            projects_list = list(project_map.values())
            for i, td in enumerate(task_data):
                proj = projects_list[i % len(projects_list)]
                t = Task(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    project_id=proj.id,
                    client_id=proj.client_id,
                    title=td["title"],
                    description=td["description"],
                    status=td["status"],
                    priority=td["priority"],
                    due_date=td["due"],
                    estimated_minutes=(i + 1) * 30,
                )

                # Add some labels
                if "bug" in td["title"].lower() or "leak" in td["title"].lower() or "fix" in td["title"].lower():
                    t.labels.append(label_map["bug"])
                if td["priority"] == TaskPriority.URGENT:
                    t.labels.append(label_map["urgent"])
                if "api" in td["title"].lower() or "server" in td["title"].lower():
                    t.labels.append(label_map["backend"])

                db.add(t)

                # Add task event
                te = TaskEvent(
                    id=str(uuid.uuid4()),
                    task_id=t.id,
                    user_id=user.id,
                    event_type=TaskEventType.TASK_CREATED,
                )
                db.add(te)

            await db.commit()
            print("Tasks created.")

    print("Seed completed successfully!")
    print()
    print("Demo credentials:")
    print("  Email:    alex@taskmate.dev")
    print("  Password: password123")


if __name__ == "__main__":
    asyncio.run(seed())
