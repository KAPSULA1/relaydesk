#!/bin/bash

# RelayDesk Development Startup Script
# Starts both backend (Django + Daphne) and frontend (Next.js) in parallel

set -e

echo "🚀 Starting RelayDesk Development Environment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Redis is running
echo -e "${YELLOW}📡 Checking Redis...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis not running. Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
fi
echo -e "${GREEN}✅ Redis is running${NC}"

# Start Backend (Django + Daphne)
echo -e "${BLUE}🔧 Starting Django Backend...${NC}"
cd backend
source venv_relaydesk_pro/bin/activate
export DJANGO_SETTINGS_MODULE=relaydesk.settings.dev
daphne -b 0.0.0.0 -p 8000 relaydesk.asgi:application &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Start Frontend (Next.js)
echo -e "${BLUE}🎨 Starting Next.js Frontend...${NC}"
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait and display URLs
sleep 3
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ RelayDesk is ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${BLUE}🌐 Frontend:${NC} http://localhost:3000"
echo -e "  ${BLUE}🔌 Backend API:${NC} http://localhost:8000/api"
echo -e "  ${BLUE}🔧 Admin:${NC} http://localhost:8000/admin"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Trap SIGINT and cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}
trap cleanup INT

# Keep script running
wait
