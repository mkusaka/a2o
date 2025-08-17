"""
AWS Lambda handler for LiteLLM Proxy with Basic Authentication
"""

import base64
import os
import sys
import asyncio

# Set config path for LiteLLM before importing
CONFIG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config.yaml"
)

# Debug: Print config path and check if file exists
print(f"Config file path: {CONFIG_FILE_PATH}")
if os.path.exists(CONFIG_FILE_PATH):
    print(f"Config file exists at {CONFIG_FILE_PATH}")
    with open(CONFIG_FILE_PATH, 'r') as f:
        print(f"Config file content preview: {f.read()[:200]}...")
else:
    print(f"WARNING: Config file not found at {CONFIG_FILE_PATH}")

# Import LiteLLM proxy server components
from litellm.proxy.proxy_server import (
    app as litellm_app,
    ProxyConfig,
    initialize,
)
from mangum import Mangum
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Create proxy config instance
proxy_config = ProxyConfig()

# Flag to track initialization
_initialized = False
_init_error = None

async def init_litellm():
    """Initialize LiteLLM proxy with config file"""
    global _initialized, _init_error
    if not _initialized:
        try:
            # Load the config file
            await proxy_config.load_config(
                router=None,
                config_file_path=CONFIG_FILE_PATH
            )
            # Initialize the proxy server
            await initialize(
                config=CONFIG_FILE_PATH,
                telemetry=False
            )
            _initialized = True
            print(f"LiteLLM initialized successfully with config: {CONFIG_FILE_PATH}")
        except Exception as e:
            _init_error = str(e)
            print(f"Failed to initialize LiteLLM: {e}")
            raise

# Don't try to initialize during import - let the middleware handle it


class InitializationMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure LiteLLM is initialized before handling requests"""
    
    async def dispatch(self, request, call_next):
        global _initialized
        if not _initialized:
            try:
                await init_litellm()
            except Exception as e:
                return Response(
                    content=f"Failed to initialize LiteLLM: {str(e)}",
                    status_code=500,
                )
        return await call_next(request)


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


# Add middlewares to LiteLLM app
# Order matters: Initialize first, then authenticate
litellm_app.add_middleware(BasicAuthMiddleware)
litellm_app.add_middleware(InitializationMiddleware)


# Note: LiteLLM proxy server already provides /health and other endpoints
# We don't need to override them


# Create Mangum handler for AWS Lambda
handler = Mangum(litellm_app, lifespan="off")
