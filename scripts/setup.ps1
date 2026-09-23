# TaskMate AI - Development Setup Script (Windows)
Write-Host "🚀 TaskMate AI — Development Setup" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Check prerequisites
$missing = @()
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { $missing += "Docker" }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { $missing += "Node.js" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $missing += "Python" }

if ($missing.Count -gt 0) {
    Write-Host "❌ Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites found" -ForegroundColor Green

# Create .env from example if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "ℹ️  .env already exists, skipping" -ForegroundColor Yellow
}

# Install backend dependencies
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Cyan
Push-Location apps/api
pip install -e ".[dev]"
Pop-Location

# Install frontend dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location apps/web
npm install
Pop-Location

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review and update .env with your settings"
Write-Host "  2. Start services:  docker compose up --build -d"
Write-Host "  3. Run migrations:  cd apps/api; alembic upgrade head"
Write-Host "  4. Open frontend:   http://localhost:3000"
Write-Host "  5. API health:      http://localhost:8000/health"
