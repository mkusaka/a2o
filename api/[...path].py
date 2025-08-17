import sys
import os

# Add parent directory to path for middleware import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from litellm.proxy.proxy_server import app as _app  # LiteLLM FastAPI app
from fastapi import Response

try:
    from middleware import BasicAuthMiddleware
except ImportError:
    # Fallback if middleware import fails
    from starlette.middleware.base import BaseHTTPMiddleware
    import base64
    
    class BasicAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path.endswith("/health") or request.url.path == "/":
                return await call_next(request)
            
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
