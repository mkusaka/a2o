# a2o - Anthropic to OpenAI Proxy

A proxy server that translates Anthropic's `/v1/messages` format to OpenAI-compatible API format, built with LiteLLM.

## Features

- 🔄 **Format Translation**: Converts Anthropic message format to OpenAI chat completion format
- 🌐 **Dynamic Routing**: Route requests to different OpenAI-compatible endpoints via headers
- 📊 **Structured Logging**: JSON-formatted logs for monitoring and debugging
- 🚀 **Multiple Providers**: Supports OpenAI, Cerebras, and other LiteLLM-compatible providers
- 🔌 **Streaming Support**: Full SSE streaming support for real-time responses
- 🐳 **Docker & Local**: Run with Docker or locally with uv package manager

## Quick Start

### Using Docker

```bash
# Build and run
docker build -t a2o-proxy .
docker run --rm -p 4000:4000 \
  -e LITELLM_MASTER_KEY=dev-local \
  -e OPENAI_API_KEY=your-api-key \
  a2o-proxy
```

### Local Installation with uv

```bash
# Install dependencies
uv venv
source .venv/bin/activate
uv pip install 'litellm[proxy]'

# Set environment variables
export LITELLM_MASTER_KEY=dev-local
export OPENAI_API_KEY=your-api-key

# Run the proxy
litellm --config config.yaml --port 4000
```

### Using Makefile

```bash
make install  # First time setup
make run      # Start the proxy
make test     # Run test request
make stop     # Stop the proxy
```

## Usage

Send requests to the proxy using Anthropic's message format:

### OpenAI Example
```bash
curl -N http://localhost:4000/v1/messages \
  -H 'content-type: application/json' \
  -H 'anthropic-version: 2023-06-01' \
  -H "authorization: Bearer $OPENAI_API_KEY" \
  -H "a2o-endpoint: https://api.openai.com/v1" \
  -d '{
    "model": "gpt-4o-mini",
    "max_tokens": 100,
    "messages": [{"role":"user","content":"Hello!"}],
    "stream": true
  }'
```

### Cerebras Example
```bash
curl -N http://localhost:4000/v1/messages \
  -H 'content-type: application/json' \
  -H 'anthropic-version: 2023-06-01' \
  -H "authorization: Bearer $CEREBRAS_API_KEY" \
  -H "a2o-endpoint: https://api.cerebras.ai/v1" \
  -d '{
    "model": "qwen-3-coder-480b",
    "max_tokens": 100,
    "messages": [{"role":"user","content":"Tell a one-line joke"}],
    "stream": true
  }'
```

### Claude Code Integration

Use a2o proxy with Claude Code to access OpenAI-compatible models through Anthropic's API format:

#### Method 1: Environment Variables
```bash
# Start a2o proxy first
make run  # or docker run command

# Configure Claude Code
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_AUTH_TOKEN=your-openai-api-key
export ANTHROPIC_MODEL=gpt-4o-mini

# Start Claude Code
claude
```

#### Method 2: Settings File
Configure `~/.claude/settings.json`:
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "your-openai-api-key",
    "ANTHROPIC_MODEL": "gpt-4o-mini",
    "ANTHROPIC_SMALL_FAST_MODEL": "gpt-4o-mini"
  }
}
```

#### Using Different Providers
```bash
# For OpenAI models
export ANTHROPIC_AUTH_TOKEN=$OPENAI_API_KEY
export ANTHROPIC_MODEL=gpt-4o-mini

# For Cerebras models (configure a2o-endpoint header)
export ANTHROPIC_AUTH_TOKEN=$CEREBRAS_API_KEY
export ANTHROPIC_MODEL=qwen-3-coder-480b
# Note: You'll need to modify the proxy to set default endpoint headers

# Check model status in Claude Code
/status
```

## Configuration

### Model Configuration

Edit `config.yaml` to add supported models:

```yaml
model_list:
  - model_name: "gpt-4o-mini"
    litellm_params:
      model: "gpt-4o-mini"
      custom_llm_provider: "openai"
  - model_name: "qwen-3-coder-480b"
    litellm_params:
      model: "qwen-3-coder-480b"
      custom_llm_provider: "cerebras"
```

### Supported Providers

The proxy supports all LiteLLM providers including:
- OpenAI
- Azure OpenAI
- Anthropic
- Cerebras
- Groq
- Together AI
- Replicate
- And many more...

## Headers

| Header | Description | Required |
|--------|-------------|----------|
| `content-type` | Must be `application/json` | Yes |
| `anthropic-version` | Anthropic API version (e.g., `2023-06-01`) | Yes |
| `authorization` | Bearer token with API key | Yes |
| `a2o-endpoint` | Target OpenAI-compatible endpoint URL | Optional |

## Response Format

The proxy returns responses in Anthropic's message format, including:
- Non-streaming: Standard JSON response
- Streaming: Server-Sent Events (SSE) with Anthropic event types

## Structured Logging

The proxy outputs structured JSON logs to stdout:

```json
{
  "ts": 1757264955992,
  "event": "proxy.success",
  "path": "/v1/messages",
  "endpoint": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "stream": true,
  "usage": {
    "completion_tokens": 14,
    "prompt_tokens": 13,
    "total_tokens": 27
  }
}
```

## Development

### Project Structure

```
.
├── config.yaml           # LiteLLM configuration
├── custom_callbacks.py   # Custom adapter and logging
├── Dockerfile           # Docker container definition
├── Makefile            # Build and run commands
├── pyproject.toml      # Python package configuration
└── run.sh              # Local run script
```

### Custom Adapter

The `custom_callbacks.py` file contains:
- `AnthropicAdapter`: Handles format conversion between Anthropic and OpenAI
- `AdapterLogger`: Provides structured JSON logging

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LITELLM_MASTER_KEY` | Master key for LiteLLM proxy | `dev-local` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_BASE_URL` | OpenAI-compatible base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Default model to use | `gpt-4o-mini` |

## License

MIT