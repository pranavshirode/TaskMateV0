from fastapi import APIRouter

from app.api.routes import health, system

api_router = APIRouter()
health_router = APIRouter(tags=["health"])

# Health routes - unversioned
health_router.include_router(health.router)

# V1 routes
from app.api.routes import auth, clients, projects, repositories, tasks, dashboard, labels, ai

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(system.router, prefix="/system", tags=["system"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(clients.router, prefix="/clients", tags=["clients"])
v1_router.include_router(projects.router, prefix="/projects", tags=["projects"])
v1_router.include_router(repositories.project_router, prefix="/projects", tags=["repositories"])
v1_router.include_router(repositories.repo_router, prefix="/repositories", tags=["repositories"])
v1_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
v1_router.include_router(labels.router, prefix="/labels", tags=["labels"])
v1_router.include_router(ai.router, prefix="/ai", tags=["ai"])
