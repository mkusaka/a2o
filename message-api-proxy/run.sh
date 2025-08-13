#!/usr/bin/env bash
set -e
export PORT="${PORT:-8080}"
# Start Message API proxy with Basic auth middleware
exec python -m uvicorn app:app --host 0.0.0.0 --port "$PORT"