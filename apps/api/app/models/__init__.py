from app.db.base import Base  # noqa: F401
from app.models.agent_execution import AgentExecution, AgentExecutionStep  # noqa: F401
from app.models.ai import AIRequestLog, Conversation, ConversationMessage  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.client_communication import ClientCommunication  # noqa: F401
from app.models.enums import (  # noqa: F401
    AnalysisStatus,
    AutomationType,
    ClarificationStatus,
    ClientRequestStatus,
    ClientRequestType,
    ClientStatus,
    ContextCategory,
    ProjectStatus,
    RepositoryProvider,
    RequirementCategory,
    RequirementStatus,
    TaskEventType,
    TaskPriority,
    TaskStatus,
)
from app.models.github_integration import GitHubIntegration  # noqa: F401
from app.models.google_integration import GoogleIntegration  # noqa: F401
from app.models.milestone import Milestone, TaskDependency  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.proposal import Proposal, ProposalVersion  # noqa: F401
from app.models.repository import Repository  # noqa: F401
from app.models.requirements import (  # noqa: F401
    AnalysisRevision,
    AutomationExecution,
    ClarificationQuestion,
    ClientRequest,
    ProjectContextNote,
    Requirement,
    RequirementAssumption,
    RequirementRisk,
    RequirementsAnalysis,
    RequirementTaskLink,
)
from app.models.task import Task  # noqa: F401
from app.models.task_event import TaskEvent  # noqa: F401
from app.models.task_label import TaskLabel, task_label_associations  # noqa: F401
from app.models.user import User  # noqa: F401
