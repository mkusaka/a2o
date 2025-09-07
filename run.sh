#!/bin/bash

# Install dependencies with uv
echo "Installing dependencies with uv..."
uv pip install -e .

# Export environment variables
export LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY:-dev-local}

# Run LiteLLM proxy
echo "Starting a2o-proxy on port 4000..."
litellm --config config.yaml --port 4000 --detailed_debug