#!/bin/bash

# FastAPI-based a2o proxy runner

# Default values
PORT="${PORT:-4000}"
HOST="${HOST:-0.0.0.0}"

# Ensure virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "No virtual environment found. Please run 'uv venv' first."
        exit 1
    fi
fi

echo "Starting a2o FastAPI proxy on $HOST:$PORT"
echo "Using:"
echo "  - OpenAI API: ${OPENAI_API_KEY:+[SET]}"
echo "  - Cerebras API: ${CEREBRAS_API_KEY:+[SET]}"

# Run the FastAPI app
uvicorn app:app --host "$HOST" --port "$PORT" --reload