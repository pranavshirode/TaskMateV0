#!/bin/bash
# TaskMate AI — Development Setup Script
set -e

echo "🚀 TaskMate AI — Development Setup"
echo "==================================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }

echo "✅ Prerequisites found"

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
else
    echo "ℹ️  .env already exists, skipping"
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd apps/api
pip install -e ".[dev]"
cd ../..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd apps/web
npm install
cd ../..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and update .env with your settings"
echo "  2. Start services:  make up"
echo "  3. Run migrations:  make migrate"
echo "  4. Open frontend:   http://localhost:3000"
echo "  5. API health:      http://localhost:8000/health"
