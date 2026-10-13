from app.api.routes.auth import router as auth_router
from app.api.routes.clients import router as clients_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.labels import router as labels_router
from app.api.routes.projects import router as projects_router
from app.api.routes.repositories import project_router as repos_project_router
from app.api.routes.repositories import repo_router as repos_router
from app.api.routes.tasks import router as tasks_router

__all__ = [
    "auth_router",
    "clients_router",
    "projects_router",
    "repos_project_router",
    "repos_router",
    "tasks_router",
    "dashboard_router",
    "labels_router",
]
