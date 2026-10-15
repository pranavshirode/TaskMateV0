from fastapi import APIRouter

from app.api.routes import health, system

api_router = APIRouter()
health_router = APIRouter(tags=["health"])

# Health routes - unversioned
health_router.include_router(health.router)

# V1 routes
from app.api.routes import (
    agent,
    ai,
    auth,
    automations,
    client_requests,
    clients,
    dashboard,
    integrations,
    labels,
    milestones,
    project_context,
    projects,
    proposals,
    repositories,
    requirements,
    tasks,
)

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
v1_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
v1_router.include_router(agent.router, prefix="/agent", tags=["agent"])
v1_router.include_router(requirements.router, prefix="/requirements", tags=["requirements"])
v1_router.include_router(project_context.router, tags=["project-context"])
v1_router.include_router(client_requests.router, tags=["client-requests"])
v1_router.include_router(automations.router, prefix="/automations", tags=["automations"])
v1_router.include_router(proposals.router, prefix="", tags=["proposals"])
v1_router.include_router(milestones.router, prefix="", tags=["milestones"])
