# TaskMate AI — API Reference

## Base URL

- Development: `http://localhost:8000`

## API Versioning

All business endpoints are versioned under `/api/v1/`.

Health and operational endpoints are unversioned to ensure they remain stable across API versions.

## Endpoints

### Health & Operations (Unversioned)

#### `GET /health`

Basic liveness check. Returns immediately if the API process is running.

**Response (200):**
```json
{
  "status": "ok",
  "service": "taskmate-api",
  "version": "0.1.0"
}
```

#### `GET /health/ready`

Readiness check. Verifies all required dependencies (database) are available.

**Response (200):**
```json
{
  "status": "ok",
  "service": "taskmate-api",
  "version": "0.1.0",
  "checks": {
    "database": "ok"
  }
}
```

**Response (503 — not ready):**
```json
{
  "status": "degraded",
  "service": "taskmate-api",
  "version": "0.1.0",
  "checks": {
    "database": "error: connection refused"
  }
}
```

### System (v1)

#### `GET /api/v1/system/info`

Returns basic system information. Useful for verifying frontend-backend connectivity.

**Response (200):**
```json
{
  "name": "TaskMate API",
  "version": "0.1.0",
  "environment": "development"
}
```

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "request_id": "uuid-of-the-request"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RESOURCE_NOT_FOUND` | 404 | Requested resource does not exist |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `DATABASE_ERROR` | 503 | Database connectivity issue |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Request Headers

| Header | Description | Required |
|--------|-------------|----------|
| `X-Request-ID` | Correlation ID for request tracing. If not provided, one is generated automatically. | No |

## Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | The request correlation ID (echoed back or auto-generated) |
