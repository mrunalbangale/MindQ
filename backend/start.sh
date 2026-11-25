#!/bin/bash
set -e

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  echo "🐍 Activating Python virtual environment..."
  source .venv/bin/activate 2>/dev/null || true
fi

# Attempt background ollama if available
if command -v ollama >/dev/null 2>&1; then
  echo "🤖 Starting local Ollama model (llama3.1)..."
  ollama run llama3.1 >/dev/null 2>&1 &
fi

echo "🚀 Starting MindQ FastAPI backend on http://0.0.0.0:8000..."
if command -v uvicorn >/dev/null 2>&1; then
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
elif [ -f "/Users/revatigaikwad/Library/Python/3.14/bin/uvicorn" ]; then
  /Users/revatigaikwad/Library/Python/3.14/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
