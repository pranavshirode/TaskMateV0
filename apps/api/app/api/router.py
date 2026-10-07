from fastapi import APIRouter

from app.api.routes import health, system, auth, users, clients, projects, tasks, dashboard, repositories, ai

api_router = APIRouter()
health_router = APIRouter(tags=["health"])

# Health routes - unversioned
health_router.include_router(health.router)

# V1 routes
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(system.router, prefix="/system", tags=["system"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(users.router, prefix="/users", tags=["users"])
v1_router.include_router(clients.router, prefix="/clients", tags=["clients"])
v1_router.include_router(projects.router, prefix="/projects", tags=["projects"])
v1_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
v1_router.include_router(repositories.router, tags=["repositories"])
v1_router.include_router(ai.router, prefix="/ai", tags=["ai"])
