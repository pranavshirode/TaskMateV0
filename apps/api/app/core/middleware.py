import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import internal_error_response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.time()
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "event": "request_start",
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            # Handle it here, inside CORSMiddleware, so the browser can read the 500 response.
            # Starlette would otherwise answer from its outermost error middleware, without CORS headers.
            response = internal_error_response(request, exc)

        duration = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "event": "request_complete",
            },
        )

        return response
