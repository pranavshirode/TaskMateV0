from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    auth_service = AuthService(db)
    try:
        user = await auth_service.get_current_user(user_id)
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        ) from None


from app.repositories.agent_execution import AgentExecutionRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.github_integration import GitHubIntegrationRepository
from app.repositories.google_integration import GoogleIntegrationRepository
from app.services.agent_execution import AgentExecutionService
from app.services.conversation import ConversationService
from app.services.github_integration import GitHubIntegrationService
from app.services.google_integration import GoogleIntegrationService


async def get_github_integration_service(
    db: AsyncSession = Depends(get_db),
) -> GitHubIntegrationService:
    repo = GitHubIntegrationRepository(db)
    return GitHubIntegrationService(repo)


async def get_agent_execution_service(
    db: AsyncSession = Depends(get_db),
) -> AgentExecutionService:
    repo = AgentExecutionRepository(db)
    return AgentExecutionService(repo)


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    repo = ConversationRepository(db)
    return ConversationService(repo)


from app.agent.orchestrator import AgentOrchestrator
from app.agent.permissions import ToolPermissionService
from app.agent.tools.registry import create_default_registry
from app.ai.context.builder import ContextBuilder
from app.ai.providers import get_ai_provider
from app.core.config import get_settings
from app.services.client import ClientService
from app.services.project import ProjectService
from app.services.task import TaskService


async def get_agent_orchestrator(
    db: AsyncSession = Depends(get_db),
) -> AgentOrchestrator:
    settings = get_settings()
    tool_registry = create_default_registry()
    github_service = GitHubIntegrationService(GitHubIntegrationRepository(db))
    google_service = GoogleIntegrationService(GoogleIntegrationRepository(db))
    project_service = ProjectService(db)
    permission_service = ToolPermissionService(tool_registry, project_service, github_service, db, settings)
    ai_provider = get_ai_provider()
    context_builder = ContextBuilder(db)
    execution_service = AgentExecutionService(AgentExecutionRepository(db))
    conversation_service = ConversationService(ConversationRepository(db))
    task_service = TaskService(db)
    client_service = ClientService(db)
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
        google_service=google_service,
    )


from app.services.client_request import ClientRequestService
from app.services.project_context import ProjectContextService
from app.services.requirements_pipeline import RequirementsService
from app.services.workflow_automation import WorkflowAutomationService


async def get_requirements_service(
    db: AsyncSession = Depends(get_db),
) -> RequirementsService:
    ai_provider = get_ai_provider()
    task_service = TaskService(db)
    return RequirementsService(db, ai_provider, task_service)


async def get_project_context_service(
    db: AsyncSession = Depends(get_db),
) -> ProjectContextService:
    return ProjectContextService(db)


async def get_client_request_service(
    db: AsyncSession = Depends(get_db),
) -> ClientRequestService:
    ai_provider = get_ai_provider()
    return ClientRequestService(db, ai_provider)


async def get_workflow_automation_service(
    db: AsyncSession = Depends(get_db),
) -> WorkflowAutomationService:
    return WorkflowAutomationService(db)


async def get_google_integration_service(db: AsyncSession = Depends(get_db)) -> GoogleIntegrationService:
    return GoogleIntegrationService(GoogleIntegrationRepository(db))
