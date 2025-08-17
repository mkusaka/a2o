import base64
import os
from unittest.mock import patch

from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

# Import the middleware from lambda_handler
from lambda_handler import BasicAuthMiddleware


# Create a simple test app
def hello_endpoint(request):
    return Response("Hello World", status_code=200)


def health_endpoint(request):
    return Response("OK", status_code=200)


def protected_endpoint(request):
    return Response("Protected content", status_code=200)


app = Starlette(
    routes=[
        Route("/", hello_endpoint),
        Route("/api/health", health_endpoint),
        Route("/api/protected", protected_endpoint),
    ]
)


class TestBasicAuthMiddleware:
    """Test cases for Basic Authentication Middleware"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Clear environment variables
        os.environ.pop("BASIC_AUTH_USERNAME", None)
        os.environ.pop("BASIC_AUTH_PASSWORD", None)

    def create_auth_header(self, username: str, password: str) -> str:
        """Create Basic auth header"""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_valid_authentication(self):
        """Test successful authentication with valid credentials"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        auth_header = self.create_auth_header("testuser", "testpass")
        response = client.get("/api/protected", headers={"authorization": auth_header})

        assert response.status_code == 200
        assert response.text == "Protected content"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_invalid_username(self):
        """Test authentication failure with wrong username"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        auth_header = self.create_auth_header("wronguser", "testpass")
        response = client.get("/api/protected", headers={"authorization": auth_header})

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Basic realm="LiteLLM Proxy"'
        assert response.text == "Invalid credentials"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_invalid_password(self):
        """Test authentication failure with wrong password"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        auth_header = self.create_auth_header("testuser", "wrongpass")
        response = client.get("/api/protected", headers={"authorization": auth_header})

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Basic realm="LiteLLM Proxy"'
        assert response.text == "Invalid credentials"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_no_authorization_header(self):
        """Test authentication failure with no authorization header"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        response = client.get("/api/protected")

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Basic realm="LiteLLM Proxy"'
        assert response.text == "Authentication required"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_invalid_auth_header_format(self):
        """Test authentication failure with invalid header format"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        response = client.get(
            "/api/protected", headers={"authorization": "Bearer token123"}
        )

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Basic realm="LiteLLM Proxy"'
        assert response.text == "Invalid authentication scheme"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_malformed_basic_auth(self):
        """Test authentication failure with malformed Basic auth"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        # Invalid base64
        response = client.get(
            "/api/protected", headers={"authorization": "Basic invalid_base64"}
        )

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Basic realm="LiteLLM Proxy"'
        assert response.text == "Invalid authentication format"

    def test_missing_environment_variables(self):
        """Test that default credentials are used when environment variables are not set"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        # The middleware uses default credentials "admin" and "password"
        auth_header = self.create_auth_header("admin", "password")
        response = client.get("/api/protected", headers={"authorization": auth_header})

        assert response.status_code == 200
        assert response.text == "Protected content"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_health_endpoint_bypass(self):
        """Test that health check endpoints bypass authentication"""
        test_app = Starlette(routes=[Route("/api/health", health_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        # No authorization header should still work for health endpoint
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.text == "OK"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_health_endpoint_with_auth(self):
        """Test that health check endpoints work with authentication too"""
        test_app = Starlette(routes=[Route("/api/health", health_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        auth_header = self.create_auth_header("testuser", "testpass")
        response = client.get("/api/health", headers={"authorization": auth_header})

        assert response.status_code == 200
        assert response.text == "OK"

    @patch.dict(
        os.environ, {"BASIC_AUTH_USERNAME": "", "BASIC_AUTH_PASSWORD": "testpass"}
    )
    def test_empty_username_env(self):
        """Test that empty username environment variable is used literally (not default)"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        # Empty username means auth will fail regardless of password
        auth_header = self.create_auth_header("admin", "password")
        response = client.get("/api/protected", headers={"authorization": auth_header})

        assert response.status_code == 401
        assert response.text == "Invalid credentials"

    @patch.dict(
        os.environ, {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": ""}
    )
    def test_empty_password_env(self):
        """Test that empty password environment variable is used literally (not default)"""
        test_app = Starlette(routes=[Route("/api/protected", protected_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        # Empty password means auth will fail regardless of username
        auth_header = self.create_auth_header("testuser", "password")
        response = client.get("/api/protected", headers={"authorization": auth_header})

        assert response.status_code == 401
        assert response.text == "Invalid credentials"

    @patch.dict(
        os.environ,
        {"BASIC_AUTH_USERNAME": "testuser", "BASIC_AUTH_PASSWORD": "testpass"},
    )
    def test_root_endpoint_bypass(self):
        """Test that root endpoint bypasses authentication"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)

        # No authorization header should still work for root endpoint
        response = client.get("/")

        assert response.status_code == 200
        assert response.text == "Hello World"
