import os
import base64
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Basic Authentication Middleware for protecting endpoints"""
    
    async def dispatch(self, request, call_next):
        # Allow health checks and similar endpoints to pass through
        if request.url.path.endswith("/health"):
            return await call_next(request)

        # Read environment variables dynamically for testing
        basic_user = os.getenv("BASIC_AUTH_USER", "")
        basic_pass = os.getenv("BASIC_AUTH_PASS", "")
        
        if not basic_user or not basic_pass:
            return Response(status_code=500, content="Basic auth not configured")

        auth = request.headers.get("authorization")
        if not auth or not auth.startswith("Basic "):
            return Response(status_code=401, headers={"WWW-Authenticate":"Basic"}, content="Unauthorized")
        
        try:
            user, pw = base64.b64decode(auth.split(" ",1)[1]).decode().split(":",1)
        except Exception:
            return Response(status_code=401, headers={"WWW-Authenticate":"Basic"}, content="Unauthorized")
        
        if user != basic_user or pw != basic_pass:
            return Response(status_code=401, headers={"WWW-Authenticate":"Basic"}, content="Unauthorized")
        
        return await call_next(request)