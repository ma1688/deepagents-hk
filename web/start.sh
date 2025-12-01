#!/bin/bash

# HKEX Agent Web Startup Script

set -e

echo "🚀 Starting HKEX Agent Web..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start PostgreSQL
echo -e "${BLUE}📦 Starting PostgreSQL...${NC}"
docker-compose up -d

# Wait for PostgreSQL to be ready
echo -e "${BLUE}⏳ Waiting for PostgreSQL...${NC}"
sleep 3

# Check if Python venv exists
if [ ! -d "../.venv" ]; then
    echo "❌ Python virtual environment not found. Please run 'uv sync' first."
    exit 1
fi

# Activate virtual environment
source ../.venv/bin/activate

# Install web dependencies if needed
if ! pip show fastapi > /dev/null 2>&1; then
    echo -e "${BLUE}📥 Installing backend dependencies...${NC}"
    pip install -r requirements.txt
fi

# Initialize database
echo -e "${BLUE}🗄️ Initializing database...${NC}"
cd "$SCRIPT_DIR"
python -c "
import asyncio
from backend.db.database import init_db
asyncio.run(init_db())
print('✅ Database initialized')
"

# Start backend in background
echo -e "${BLUE}🔧 Starting backend server...${NC}"
cd "$SCRIPT_DIR/.."
uvicorn web.backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    kill $BACKEND_PID
    exit 1
fi

# Install frontend dependencies if needed
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📥 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend
echo -e "${BLUE}🌐 Starting frontend server...${NC}"
npm run dev &
FRONTEND_PID=$!

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🎉 HKEX Agent Web is running!                               ║"
echo "║                                                                ║"
echo "║   Frontend: http://localhost:5173                             ║"
echo "║   Backend:  http://localhost:8000                             ║"
echo "║   API Docs: http://localhost:8000/docs                        ║"
echo "║                                                                ║"
echo "║   Press Ctrl+C to stop all services                           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Handle shutdown
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker-compose stop; exit 0" SIGINT SIGTERM

# Wait for processes
wait

