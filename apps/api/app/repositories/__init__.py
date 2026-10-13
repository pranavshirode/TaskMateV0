from app.repositories.base import BaseRepository
from app.repositories.client import ClientRepository
from app.repositories.client_request import AutomationExecutionRepository, ClientRequestRepository
from app.repositories.project import ProjectRepository
from app.repositories.project_context import ProjectContextNoteRepository
from app.repositories.repository import RepositoryRepository
from app.repositories.requirements import (
    AnalysisRevisionRepository,
    ClarificationQuestionRepository,
    RequirementRepository,
    RequirementsAnalysisRepository,
    RequirementTaskLinkRepository,
)
from app.repositories.task import TaskRepository
from app.repositories.task_event import TaskEventRepository
from app.repositories.task_label import TaskLabelRepository
from app.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ClientRepository",
    "ProjectRepository",
    "RepositoryRepository",
    "TaskRepository",
    "TaskEventRepository",
    "TaskLabelRepository",
    "RequirementsAnalysisRepository",
    "RequirementRepository",
    "ClarificationQuestionRepository",
    "RequirementTaskLinkRepository",
    "AnalysisRevisionRepository",
    "ProjectContextNoteRepository",
    "ClientRequestRepository",
    "AutomationExecutionRepository",
]
