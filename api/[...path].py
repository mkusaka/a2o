import base64
import os

from litellm.proxy.proxy_server import app as _app  # LiteLLM FastAPI app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Basic Authentication Middleware for protecting endpoints"""
    
    async def dispatch(self, request, call_next):
        # Allow health checks and root endpoint to pass through
        if request.url.path.endswith("/health") or request.url.path == "/":
            return await call_next(request)
        
        # Read environment variables dynamically for testing
        basic_user = os.getenv("BASIC_AUTH_USER", "")
        basic_pass = os.getenv("BASIC_AUTH_PASS", "")
        
        if not basic_user or not basic_pass:
            return Response(status_code=500, content="Basic auth not configured")
        
        auth = request.headers.get("authorization")
        if not auth or not auth.startswith("Basic "):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": "Basic"},
                content="Unauthorized",
            )
        
        try:
            user, pw = base64.b64decode(auth.split(" ", 1)[1]).decode().split(":", 1)
        except Exception:
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": "Basic"},
                content="Unauthorized",
            )
        
        if user != basic_user or pw != basic_pass:
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": "Basic"},
                content="Unauthorized",
            )
        
        return await call_next(request)

# Configure the LiteLLM app
app = _app
app.add_middleware(BasicAuthMiddleware)

# Add simple health check endpoint (relative to /api/ base path)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "litellm-vercel-proxy"}

@app.get("/")
async def root():
    return {"message": "LiteLLM Vercel Proxy", "health": "/api/health", "docs": "/api/docs"}
