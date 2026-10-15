#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/share/mise/installs/node/26.8.2/bin:$PATH"

echo "=== Starting TaskMate AI Development Environment ==="
echo "Project Root: $PROJECT_ROOT"

# Ensure .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Creating .env from defaults..."
    cat << 'EOF' > "$PROJECT_ROOT/.env"
APP_ENV=development
APP_NAME=TaskMate API
APP_VERSION=0.1.0
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DATABASE_URL=sqlite+aiosqlite:////run/media/pranav/Work/SoloProjects/my own ideas/TaskMateV0/taskmate.db
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
LOG_LEVEL=INFO
NEXT_PUBLIC_API_URL=http://localhost:8000
SECRET_KEY=development-only-change-me
AI_PROVIDER=mock
AI_MODEL=gpt-4o-mini
AI_API_KEY=mock-key
AGENT_MAX_STEPS=10
AGENT_MAX_TOOL_CALLS=10
AGENT_MAX_EXECUTION_TIME=120
AGENT_REQUIRE_APPROVAL_FOR_WRITES=true
EOF
fi

# Resolve Python interpreter
if [ -f "$PROJECT_ROOT/apps/api/.venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/apps/api/.venv/bin/python"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON="python3"
fi

# Ensure database exists and is seeded
if [ ! -f "$PROJECT_ROOT/taskmate.db" ]; then
    echo "Initializing database & demo seed data..."
    "$PYTHON" "$PROJECT_ROOT/scripts/seed.py"
fi

# Start Backend API in background
echo "Starting FastAPI Backend on http://localhost:8000 (Docs: http://localhost:8000/docs)..."
cd "$PROJECT_ROOT/apps/api"
"$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Trap signals to cleanup processes
cleanup() {
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start Next.js Frontend
echo "Starting Next.js Frontend on http://localhost:3000..."
cd "$PROJECT_ROOT/apps/web"
npm run dev &
FRONTEND_PID=$!

echo "=========================================================="
echo "  TaskMate AI is running!"
echo "  - Web App:      http://localhost:3000"
echo "  - API Backend:  http://localhost:8000"
echo "  - Swagger Docs: http://localhost:8000/docs"
echo "  - Demo User:    alex@taskmate.dev / password123"
echo "=========================================================="

wait

