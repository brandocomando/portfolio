#!/usr/bin/env bash
# ==============================================================================
# Local Development Runner for Brandon Foster's Portfolio
# Starts FastAPI backend (port 8080) and Vite React SPA (port 5173) concurrently.
# ==============================================================================

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Ensure modern node is on PATH if installed via NVM
if [ -d "$HOME/.nvm/versions/node/v20.20.2/bin" ]; then
    export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"
fi

# Locate Python environment
if [ -f "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
    UVICORN="$REPO_ROOT/.venv/bin/uvicorn"
else
    PYTHON="python3"
    UVICORN="uvicorn"
fi

echo "=========================================================="
echo "🚀 Starting Brandon Foster Portfolio (Local Dev Mode)"
echo "=========================================================="
echo "• Backend:  http://127.0.0.1:8080 (FastAPI + Uvicorn + RAG)"
echo "• API Docs: http://127.0.0.1:8080/docs"
echo "• Frontend: http://localhost:5173 (Vite + React SPA)"
echo "• Proxy:    /api/* -> http://127.0.0.1:8080"
echo "=========================================================="

# Trap SIGINT/SIGTERM to gracefully terminate background workers
cleanup() {
    echo ""
    echo "🛑 Shutting down local development servers..."
    if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
    if [ -n "$FRONTEND_PID" ]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start Backend
export ENV="development"
export PORT="8080"
export PYTHONPATH="$REPO_ROOT"

echo "Starting FastAPI backend on port 8080..."
"$UVICORN" backend.app.main:app --host 127.0.0.1 --port 8080 --reload &
BACKEND_PID=$!

# Wait for backend healthz
until curl -s http://127.0.0.1:8080/healthz >/dev/null 2>&1; do
    sleep 0.5
done
echo "✓ Backend is healthy at http://127.0.0.1:8080/healthz"

# Start Frontend
echo "Starting Vite frontend on port 5173..."
cd "$REPO_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Full stack running! Press Ctrl+C to stop."
wait "$BACKEND_PID" "$FRONTEND_PID"
