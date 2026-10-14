import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(404, code, message)


class ValidationError(AppError):
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(422, code, message)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(409, code, message)


class DatabaseError(AppError):
    def __init__(self, message: str, code: str = "DATABASE_ERROR"):
        super().__init__(503, code, message)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Not authorized", code: str = "AUTHORIZATION_ERROR"):
        super().__init__(401, code, message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN"):
        super().__init__(403, code, message)


def register_error_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    request_id=request_id,
                )
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        return internal_error_response(request, exc)


def internal_error_response(request: Request, exc: Exception) -> JSONResponse:
    """Log an unexpected exception and build the generic 500 body (no internals leaked)."""
    request_id = getattr(request.state, "request_id", None)
    logger.error("Unhandled exception", exc_info=exc, extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred.",
                request_id=request_id,
            )
        ).model_dump(),
    )
