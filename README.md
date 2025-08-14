# LiteLLM Vercel Proxy with Basic Auth

A LiteLLM Proxy implementation with Basic authentication deployed on Vercel. Features dependency management with uv and automatic requirements.txt generation during build.

## Features

- 🔒 Basic authentication protection
- 🌐 Anthropic format → OpenAI compatible conversion
- ⚡ SSE (Server-Sent Events) streaming support
- 🚀 Vercel Fluid Compute support
- 📦 Dependency management with uv
- 🇯🇵 Tokyo region (hnd1) deployment

## Project Structure

```
├── api/
│   └── [...path].py        # ASGI entry point with Basic auth middleware
├── config.yaml             # LiteLLM model configuration
├── pyproject.toml          # uv/pyproject dependency management
└── vercel.json             # installCommand / functions / regions
```

## Setup

### 1. Install Dependencies (Development)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Configure Environment Variables

Set environment variables using Vercel CLI:

```bash
vercel env add BASIC_AUTH_USER         # e.g., demo
vercel env add BASIC_AUTH_PASS         # e.g., demo
vercel env add OPENAI_COMPAT_BASE      # e.g., https://api.openai.com/v1
vercel env add OPENAI_COMPAT_API_KEY   # sk-...
```

### 3. Deploy

```bash
vercel deploy          # Preview deployment
vercel deploy --prod   # Production deployment
```

## Usage

### Anthropic Format (Recommended)

```bash
APP="https://<your-app>.vercel.app"
curl -N "$APP/api/anthropic/v1/messages" \
  -u demo:demo \
  -H "content-type: application/json" \
  -d '{
    "model": "openai-compat",
    "stream": true,
    "messages": [{"role":"user","content":"Hello from Anthropic format"}]
  }'
```

### OpenAI Compatible Format

```bash
curl -N "$APP/api/v1/chat/completions" \
  -u demo:demo \
  -H "content-type: application/json" \
  -d '{
    "model": "openai-compat",
    "stream": true,
    "messages": [{"role":"user","content":"Hello from OpenAI format"}]
  }'
```

## Configuration Customization

### config.yaml

```yaml
model_list:
  - model_name: "custom-model"
    litellm_params:
      model: "gpt-4"
      api_base: "os.environ/CUSTOM_API_BASE"
      api_key: "os.environ/CUSTOM_API_KEY"
```

### vercel.json

```json
{
  "functions": {
    "api/*.py": {
      "memory": 1024,
      "maxDuration": 300  // Extend to 5 minutes
    }
  },
  "regions": ["hnd1", "iad1"]  // Multiple regions
}
```

## Technical Details

### Streaming

- Python/ASGI streaming is enabled by default
- Real-time responses via SSE (Server-Sent Events)

### Security

- Endpoint protection via Basic authentication
- Secure credential management through environment variables
- Health check endpoints bypass authentication

### Performance

- Efficient resource utilization with Fluid Compute
- Low latency in Tokyo region
- Automatic scaling support

## Troubleshooting

### Deployment Errors

```bash
# Check logs
vercel logs

# Inspect function details
vercel functions inspect
```

### Authentication Errors

Verify environment variables are set correctly:

```bash
vercel env ls
```

### Performance Optimization

- Adjust `maxDuration` according to requirements
- Change `memory` size based on load
- Select regions based on user geographic location

## License

MIT