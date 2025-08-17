"""
AWS Lambda handler for LiteLLM Proxy with Basic Authentication
"""

import base64
import os

from litellm.proxy.proxy_server import app as litellm_app
from mangum import Mangum
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Basic Authentication middleware for the proxy"""

    def __init__(self, app):
        super().__init__(app)
        self.username = os.getenv("BASIC_AUTH_USERNAME", "admin")
        self.password = os.getenv("BASIC_AUTH_PASSWORD", "password")

    async def dispatch(self, request, call_next):
        # Health check endpoints bypass authentication
        if request.url.path in ["/", "/health", "/health/", "/api/health"]:
            return await call_next(request)

        # Check authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return Response(
                content="Authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="LiteLLM Proxy"'},
            )

        # Validate credentials
        try:
            scheme, credentials = auth_header.split()
            if scheme.lower() != "basic":
                return Response(
                    content="Invalid authentication scheme",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="LiteLLM Proxy"'},
                )

            decoded = base64.b64decode(credentials).decode("utf-8")
            provided_username, provided_password = decoded.split(":", 1)

            if provided_username != self.username or provided_password != self.password:
                return Response(
                    content="Invalid credentials",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="LiteLLM Proxy"'},
                )
        except Exception:
            return Response(
                content="Invalid authentication format",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="LiteLLM Proxy"'},
            )

        # Authentication successful, proceed with request
        return await call_next(request)


# Add Basic Auth middleware to LiteLLM app
litellm_app.add_middleware(BasicAuthMiddleware)


# Add root endpoint
@litellm_app.get("/")
async def root():
    return {
        "message": "LiteLLM Proxy on AWS Lambda",
        "health": "/health",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# Add health check endpoint
@litellm_app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "litellm-proxy-lambda",
        "environment": "aws-lambda",
    }


# Create Mangum handler for AWS Lambda
handler = Mangum(litellm_app, lifespan="off")
