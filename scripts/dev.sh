#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Start the backend:"
echo "  cd \"$ROOT_DIR/backend\""
echo "  python -m venv .venv"
echo "  source .venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  uvicorn app.main:app --reload --port 8000"
echo
echo "Start the frontend:"
echo "  cd \"$ROOT_DIR/frontend\""
echo "  npm install"
echo "  npm run dev"

