from litellm.proxy.proxy_server import app as _app  # LiteLLM FastAPI app
from fastapi import Response

from middleware import BasicAuthMiddleware

app = _app
app.add_middleware(BasicAuthMiddleware)

# Add simple health check endpoint (relative to /api/ base path)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "litellm-vercel-proxy"}

@app.get("/")
async def root():
    return {"message": "LiteLLM Vercel Proxy", "health": "/api/health", "docs": "/api/docs"}
