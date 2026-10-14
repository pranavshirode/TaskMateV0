#!/usr/bin/env bash
# hitme.sh: one command to set up and run TaskMate AI locally (backend + frontend).
#
#   ./hitme.sh               install what's missing, migrate, seed demo data, start both servers
#   ./hitme.sh --setup       do the setup only, don't start the servers
#   ./hitme.sh --no-seed     skip the demo data
#   ./hitme.sh --api-port 8010 --web-port 3010
#
# Safe to run repeatedly: it only installs when dependencies changed, never overwrites your .env files,
# and backs up an existing SQLite database before migrating it. Press Ctrl+C to stop both servers.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API="$ROOT/apps/api"
WEB="$ROOT/apps/web"
VENV="$API/.venv"
PY="$VENV/bin/python"

API_PORT=8000
WEB_PORT=3000
START=1
SEED=1

bold() { printf '\035[1m%s\033[0m\n' "$*"; }
step() { printf '\n\033[1;34m==>\033[0m \033[1m%s\033[0m\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '\033[1;33m    ! %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --setup) START=0 ;;
    --no-seed) SEED=0 ;;
    --api-port) API_PORT="${2:?--api-port needs a number}"; shift ;;
    --web-port) WEB_PORT="${2:?--web-port needs a number}"; shift ;;
    -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "Unknown option: $1 (see ./hitme.sh --help)" ;;
  esac
  shift
done

# ---------------------------------------------------------------- prerequisites
step "Checking prerequisites"
command -v python3 >/dev/null || die "python3 not found. Install Python 3.10+."
command -v node >/dev/null || die "node not found. Install Node.js 18+."
command -v npm >/dev/null || die "npm not found. Install Node.js 18+ (includes npm)."
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || die "Python 3.10+ required (found $(python3 -V))."
node -e 'process.exit(parseInt(process.versions.node) < 18 ? 1 : 0)' || die "Node.js 18+ required (found $(node -v))."
info "$(python3 -V), node $(node -v)"

# Prints the first free TCP port at or after $1 (free = nothing listening and we can bind it).
free_port() {
  python3 - "$1" <<'EOF'
import socket, sys
port = int(sys.argv[1])
while port < 65535:
    in_use = socket.socket().connect_ex(("127.0.0.1", port)) == 0
    if not in_use:
        try:
            with socket.socket() as s:
                s.bind(("0.0.0.0", port))
            print(port)
            sys.exit(0)
        except OSError:
            pass
    port += 1
sys.exit(1)
EOF
}

# ---------------------------------------------------------------- backend deps
step "Backend: Python environment"
if [[ ! -x "$PY" ]]; then
  info "Creating virtualenv at apps/api/.venv"
  python3 -m venv "$VENV"
fi
STAMP="$VENV/.hitme-installed"
if [[ ! -f "$STAMP" || "$API/pyproject.toml" -nt "$STAMP" ]]; then
  info "Installing backend dependencies (first run takes a minute)..."
  "$PY" -m pip install --quiet --upgrade pip
  (cd "$API" && "$PY" -m pip install --quiet -e ".[dev]")
  touch "$STAMP"
else
  info "Dependencies up to date"
fi

# ---------------------------------------------------------------- backend config
step "Backend: configuration"
if [[ ! -f "$API/.env" ]]; then
  SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  cat > "$API/.env" <<EOF
# Created by hitme.sh. Edit freely; hitme.sh never overwrites this file.
APP_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./taskmate.db
SECRET_KEY=$SECRET
# AI: "mock" works offline with limited understanding. For the real assistant set:
#   AI_PROVIDER=openai
#   AI_API_KEY=sk-...
AI_PROVIDER=mock
AI_MODEL=gpt-4o-mini
AGENT_REQUIRE_APPROVAL_FOR_WRITES=true
EOF
  info "Created apps/api/.env (SQLite, offline AI, random SECRET_KEY)"
else
  info "Using existing apps/api/.env"
fi
AI_MODE="$(cd "$API" && "$PY" -c 'from app.core.config import get_settings as g; s=g(); print(s.AI_PROVIDER.lower() + ("" if s.AI_API_KEY else ":nokey"))')"
case "$AI_MODE" in
  mock*) warn "AI_PROVIDER=mock: offline demo mode. Set AI_PROVIDER=openai and AI_API_KEY in apps/api/.env for the full assistant." ;;
  *:nokey) warn "AI_PROVIDER is set but AI_API_KEY is empty, so the app will fall back to offline mock answers." ;;
  *) info "AI provider: ${AI_MODE}" ;;
esac

# ---------------------------------------------------------------- database
step "Database: migrations"
# Classifies the configured database: FRESH (no tables), STAMPED (managed by Alembic),
# or UNSTAMPED:<sqlite path>:<revision it matches> (tables created by the app without migrations).
DB_STATE="$(cd "$API" && "$PY" - <<'EOF'
import sqlite3
from pathlib import Path
from app.core.config import get_settings

url = get_settings().DATABASE_URL
if not url.startswith("sqlite"):
    print("STAMPED")  # server databases are only ever created through migrations
    raise SystemExit
path = Path(url.split(":///", 1)[1])
if not path.exists():
    print("FRESH")
    raise SystemExit
con = sqlite3.connect(path)
tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
stamped = "alembic_version" in tables and con.execute("select count(*) from alembic_version").fetchone()[0] > 0
if stamped or "users" not in tables:
    print("STAMPED" if stamped else "FRESH")
else:
    req_cols = {r[1] for r in con.execute("pragma table_info(requirements)")} if "requirements" in tables else set()
    print(f"UNSTAMPED:{path.resolve()}:{'head' if 'source' in req_cols else '006_sprint4_indexes'}")
EOF
)"

if [[ "$DB_STATE" == UNSTAMPED:* ]]; then
  DB_FILE="$(echo "$DB_STATE" | cut -d: -f2)"
  DB_REV="$(echo "$DB_STATE" | cut -d: -f3)"
  BACKUP="${DB_FILE%.db}.backup-$(date +%Y%m%d-%H%M%S).db"
  cp "$DB_FILE" "$BACKUP"
  info "Existing database was created without migrations. Backed it up to:"
  info "  ${BACKUP#"$ROOT"/}"
  info "Marking it as revision $DB_REV, then applying newer migrations (your data is kept)."
  (cd "$API" && "$VENV/bin/alembic" stamp "$DB_REV" >/dev/null 2>&1)
fi
if ! MIGRATE_OUT="$(cd "$API" && "$VENV/bin/alembic" upgrade head 2>&1)"; then
  printf '%s\n' "$MIGRATE_OUT" | tail -15 >&2
  die "Database migration failed (output above). Your data was not changed by hitme.sh beyond the backup."
fi
printf '%s\n' "$MIGRATE_OUT" | grep -E "Running upgrade" | sed 's/^INFO  \[alembic.runtime.migration\] /    /' || true
# Only missing tables/columns matter. Older SQLite files can differ in VARCHAR lengths or optional
# constraints, which SQLite does not enforce, so those are not reported.
DRIFT="$(cd "$API" && "$VENV/bin/alembic" check 2>&1 || true)"
if grep -qE "Detected added (table|column)" <<<"$DRIFT"; then
  warn "The database is missing tables or columns the code needs:"
  grep -E "Detected added (table|column)" <<<"$DRIFT" | sed -E "s/.*(Detected .*)/      \1/" | head -10 >&2
  warn "Fix: move the database file aside and run ./hitme.sh again (a fresh one with demo data is created)."
else
  info "Schema is up to date ($(cd "$API" && "$VENV/bin/alembic" current 2>/dev/null | tail -1))"
fi

if [[ $SEED -eq 1 ]]; then
  step "Database: demo data"
  (cd "$API" && "$PY" scripts/seed_db.py 2>&1 | grep -E "created|exists|Seed|Email|Password" | sed 's/^/    /' || true)
fi

# ---------------------------------------------------------------- frontend deps
step "Frontend: dependencies"
if [[ ! -d "$WEB/node_modules" || "$WEB/package-lock.json" -nt "$WEB/node_modules/.package-lock.json" ]]; then
  info "Installing frontend dependencies (first run takes a minute)..."
  (cd "$WEB" && npm ci --no-audit --no-fund --loglevel=error)
else
  info "Dependencies up to date"
fi

if [[ $START -eq 0 ]]; then
  bold $'\nSetup complete. Run ./hitme.sh to start the app.'
  exit 0
fi

# ---------------------------------------------------------------- start servers
step "Starting servers"
REQ_API_PORT=$API_PORT
REQ_WEB_PORT=$WEB_PORT
API_PORT="$(free_port "$API_PORT")" || die "No free port found for the API."
WEB_PORT="$(free_port "$WEB_PORT")" || die "No free port found for the web app."
[[ "$API_PORT" != "$REQ_API_PORT" ]] && warn "Port $REQ_API_PORT is busy, so the API uses port $API_PORT."
[[ "$WEB_PORT" != "$REQ_WEB_PORT" ]] && warn "Port $REQ_WEB_PORT is busy, so the web app uses port $WEB_PORT."

# Environment variables override the .env files, so the two servers always point at each other.
export CORS_ORIGINS="[\"http://localhost:$WEB_PORT\",\"http://127.0.0.1:$WEB_PORT\"]"
export NEXT_PUBLIC_API_URL="http://localhost:$API_PORT"

set -m  # each background job gets its own process group, so Ctrl+C stops everything it started
PIDS=()
cleanup() {
  trap - INT TERM EXIT
  printf '\n'
  info "Stopping servers..."
  for pid in "${PIDS[@]}"; do kill -- "-$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
  info "Stopped."
}
trap cleanup INT TERM EXIT

(cd "$API" && exec "$VENV/bin/uvicorn" app.main:app --reload --host 127.0.0.1 --port "$API_PORT" 2>&1 | sed -u 's/^/[api] /') &
PIDS+=("$!")

info "Waiting for the API on port $API_PORT..."
for _ in $(seq 1 60); do
  if python3 -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:$API_PORT/health', timeout=1)" 2>/dev/null; then
    break
  fi
  sleep 1
done
python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$API_PORT/health', timeout=2)" 2>/dev/null \
  || die "The API did not start. Check the [api] messages above."

(cd "$WEB" && exec npm run dev -- --port "$WEB_PORT" 2>&1 | sed -u 's/^/[web] /') &
PIDS+=("$!")

cat <<EOF

$(bold "TaskMate AI is starting")
    App        http://localhost:$WEB_PORT
    API docs   http://localhost:$API_PORT/docs
    Demo login alex@taskmate.dev / password123  (or "Use demo account" on the login page)
    Stop       Ctrl+C

EOF

wait -n || true
