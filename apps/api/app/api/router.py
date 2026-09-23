from fastapi import APIRouter

from app.api.routes import health, system

api_router = APIRouter()
health_router = APIRouter(tags=["health"])

# Health routes - unversioned
health_router.include_router(health.router)

# V1 routes
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(system.router, prefix="/system", tags=["system"])
