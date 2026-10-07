from typing import AsyncGenerator
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

from app.repositories.conversation import ConversationRepository
from app.services.conversation import ConversationService
from app.ai.providers.factory import get_ai_provider
from app.ai.context.builder import ContextBuilder
from app.ai.context.resolver import EntityResolver
from app.ai.services.orchestrator import AIOrchestrator
from app.ai.errors import AINotConfiguredError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")
settings = get_settings()

async def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)

from app.repositories.client import ClientRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.dashboard import DashboardRepository
from app.repositories.repository import CodeRepository
from app.services.client import ClientService
from app.services.project import ProjectService
from app.services.task import TaskService
from app.services.dashboard import DashboardService
from app.services.repository import RepositoryService

async def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return ClientRepository(session)

async def get_project_repository(session: AsyncSession = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(session)

async def get_task_repository(session: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(session)

async def get_dashboard_repository(session: AsyncSession = Depends(get_db)) -> DashboardRepository:
    return DashboardRepository(session)

async def get_code_repository(session: AsyncSession = Depends(get_db)) -> CodeRepository:
    return CodeRepository(session)

async def get_client_service(repo: ClientRepository = Depends(get_client_repository)) -> ClientService:
    return ClientService(repo)

async def get_project_service(repo: ProjectRepository = Depends(get_project_repository), client_service: ClientService = Depends(get_client_service)) -> ProjectService:
    return ProjectService(repo, client_service)

async def get_task_service(repo: TaskRepository = Depends(get_task_repository), client_service: ClientService = Depends(get_client_service), project_service: ProjectService = Depends(get_project_service)) -> TaskService:
    return TaskService(repo, client_service, project_service)

async def get_dashboard_service(repo: DashboardRepository = Depends(get_dashboard_repository)) -> DashboardService:
    return DashboardService(repo)

async def get_repository_service(repo: CodeRepository = Depends(get_code_repository), project_service: ProjectService = Depends(get_project_service)) -> RepositoryService:
    return RepositoryService(repo, project_service)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_repo.get(uuid.UUID(user_id))
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_conversation_repository(session: AsyncSession = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(session)

async def get_conversation_service(repo: ConversationRepository = Depends(get_conversation_repository)) -> ConversationService:
    return ConversationService(repo)

async def get_ai_orchestrator(
    task_service: TaskService = Depends(get_task_service),
    project_service: ProjectService = Depends(get_project_service),
    client_service: ClientService = Depends(get_client_service),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> AIOrchestrator:
    settings = get_settings()
    try:
        ai_provider = get_ai_provider(settings)
    except (AINotConfiguredError, ValueError) as e:
        raise AINotConfiguredError()

    context_builder = ContextBuilder(
        task_service=task_service,
        project_service=project_service,
        client_service=client_service,
        dashboard_service=dashboard_service,
    )
    entity_resolver = EntityResolver(
        task_service=task_service,
        project_service=project_service,
        client_service=client_service,
    )
    return AIOrchestrator(
        ai_provider=ai_provider,
        context_builder=context_builder,
        entity_resolver=entity_resolver,
        conversation_service=conversation_service,
        task_service=task_service,
        project_service=project_service,
        client_service=client_service,
        dashboard_service=dashboard_service,
    )

from app.repositories.agent_execution import AgentExecutionRepository
from app.services.agent_execution import AgentExecutionService
from app.repositories.github_integration import GitHubIntegrationRepository
from app.services.github_integration import GitHubIntegrationService
from app.agent.tools.registry import ToolRegistry, create_default_registry
from app.agent.permissions import ToolPermissionService
from app.agent.orchestrator import AgentOrchestrator

async def get_agent_execution_repository(session: AsyncSession = Depends(get_db)) -> AgentExecutionRepository:
    return AgentExecutionRepository(session)

async def get_agent_execution_service(repo: AgentExecutionRepository = Depends(get_agent_execution_repository)) -> AgentExecutionService:
    return AgentExecutionService(repo)

async def get_github_integration_repository(session: AsyncSession = Depends(get_db)) -> GitHubIntegrationRepository:
    return GitHubIntegrationRepository(session)

async def get_github_integration_service(repo: GitHubIntegrationRepository = Depends(get_github_integration_repository)) -> GitHubIntegrationService:
    return GitHubIntegrationService(repo)

def get_tool_registry() -> ToolRegistry:
    # Normally this would be a singleton, but for simplicity we can create it
    # We should also register the tools here.
    return create_default_registry()

async def get_tool_permission_service(
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    project_service: ProjectService = Depends(get_project_service),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
    db: AsyncSession = Depends(get_db),
) -> ToolPermissionService:
    settings = get_settings()
    return ToolPermissionService(tool_registry, project_service, github_service, db, settings)

async def get_agent_orchestrator(
    ai_provider = Depends(get_ai_provider),
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    permission_service: ToolPermissionService = Depends(get_tool_permission_service),
    task_service: TaskService = Depends(get_task_service),
    project_service: ProjectService = Depends(get_project_service),
    client_service: ClientService = Depends(get_client_service),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    execution_service: AgentExecutionService = Depends(get_agent_execution_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
    github_service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> AgentOrchestrator:
    settings = get_settings()
    context_builder = ContextBuilder(task_service, project_service, client_service, dashboard_service)
    return AgentOrchestrator(
        ai_provider=ai_provider,
        tool_registry=tool_registry,
        permission_service=permission_service,
        context_builder=context_builder,
        execution_service=execution_service,
        conversation_service=conversation_service,
        settings=settings,
        task_service=task_service,
        project_service=project_service,
        client_service=client_service,
        github_service=github_service,
    )
