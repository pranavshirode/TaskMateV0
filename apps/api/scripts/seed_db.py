import asyncio
import logging
from app.db.session import async_session_factory, init_db, close_db
from app.schemas.user import UserCreate
from app.schemas.client import ClientCreate
from app.schemas.project import ProjectCreate
from app.schemas.repository import RepositoryCreate
from app.schemas.task import TaskCreate, TaskStatusUpdate, TaskPriorityUpdate
from app.repositories.user import UserRepository
from app.repositories.client import ClientRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.repository import CodeRepository
from app.services.client import ClientService
from app.services.project import ProjectService
from app.services.task import TaskService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed():
    await init_db()

    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        client_repo = ClientRepository(session)
        project_repo = ProjectRepository(session)
        task_repo = TaskRepository(session)
        code_repo = CodeRepository(session)

        client_service = ClientService(client_repo)
        project_service = ProjectService(project_repo, client_service)
        task_service = TaskService(task_repo, client_service, project_service)

        # 1. Create Developer
        user_in = UserCreate(name="Alex Developer", email="alex@example.com", password="password123")
        user = await user_repo.get_by_email("alex@example.com")
        if not user:
            user = await user_repo.create(user_in)
            logger.info(f"Created user: {user.email}")

        # 2. Create Client
        client_in = ClientCreate(name="Acme Technologies", company_name="Acme Tech", email="contact@acme.com")
        clients = await client_repo.list(user.id, search="Acme Technologies")
        if not clients:
            client = await client_service.create_client(user, client_in)
            logger.info(f"Created client: {client.name}")
        else:
            client = clients[0]

        # 3. Create Project
        project_in = ProjectCreate(name="Acme SaaS Dashboard", client_id=client.id)
        projects = await project_repo.list(user.id, search="Acme SaaS Dashboard")
        if not projects:
            project = await project_service.create_project(user, project_in)
            logger.info(f"Created project: {project.name}")
        else:
            project = projects[0]

        # 4. Create Repository
        repo_in = RepositoryCreate(name="acme-dashboard", provider="GITHUB", url="https://github.com/acme/acme-dashboard", project_id=project.id)
        repos = await code_repo.list_by_project(project.id)
        if not repos:
            repo = await code_repo.create(repo_in)
            logger.info(f"Created repository: {repo.name}")

        # 5. Create Tasks
        tasks_data = [
            ("Fix authentication bug", "HIGH", "IN_PROGRESS"),
            ("Update dashboard API", "MEDIUM", "TODO"),
            ("Add password reset", "HIGH", "REVIEW"),
            ("Update API documentation", "LOW", "COMPLETED"),
        ]

        for idx, (title, priority, status) in enumerate(tasks_data):
            tasks, _ = await task_service.list_tasks(user, search=title)
            if not tasks:
                from datetime import datetime, timezone
                task_in = TaskCreate(title=title, project_id=project.id, client_id=client.id, priority=priority, status="TODO")
                task = await task_service.create_task(user, task_in)
                await task_service.change_status(task.id, user, status)
                logger.info(f"Created task: {task.title}")

    await close_db()

if __name__ == "__main__":
    asyncio.run(seed())
