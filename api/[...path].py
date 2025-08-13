import os, base64
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from litellm.proxy.proxy_server import app as _app  # LiteLLM FastAPI app

BASIC_USER = os.getenv("BASIC_AUTH_USER", "")
BASIC_PASS = os.getenv("BASIC_AUTH_PASS", "")

class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Allow health checks and similar endpoints to pass through
        if request.url.path.endswith("/health"):
            return await call_next(request)

        if not BASIC_USER or not BASIC_PASS:
            return Response(status_code=500, content="Basic auth not configured")

        auth = request.headers.get("authorization")
        if not auth or not auth.startswith("Basic "):
            return Response(status_code=401, headers={"WWW-Authenticate":"Basic"}, content="Unauthorized")
        try:
            user, pw = base64.b64decode(auth.split(" ",1)[1]).decode().split(":",1)
        except Exception:
            return Response(status_code=401, headers={"WWW-Authenticate":"Basic"}, content="Unauthorized")
        if user != BASIC_USER or pw != BASIC_PASS:
            return Response(status_code=401, headers={"WWW-Authenticate":"Basic"}, content="Unauthorized")
        return await call_next(request)

app = _app
app.add_middleware(BasicAuthMiddleware)