import base64
import os
from unittest.mock import patch
import pytest
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.testclient import TestClient
from starlette.routing import Route

# Import the middleware
from middleware import BasicAuthMiddleware


# Create a simple test app
def hello_endpoint(request):
    return Response("Hello World", status_code=200)

def health_endpoint(request):
    return Response("OK", status_code=200)

app = Starlette(routes=[
    Route("/", hello_endpoint),
    Route("/api/health", health_endpoint),
])


class TestBasicAuthMiddleware:
    """Test cases for Basic Authentication Middleware"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Clear environment variables
        os.environ.pop("BASIC_AUTH_USER", None)
        os.environ.pop("BASIC_AUTH_PASS", None)
    
    def create_auth_header(self, username: str, password: str) -> str:
        """Create Basic auth header"""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_valid_authentication(self):
        """Test successful authentication with valid credentials"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        auth_header = self.create_auth_header("testuser", "testpass")
        response = client.get("/", headers={"authorization": auth_header})
        
        assert response.status_code == 200
        assert response.text == "Hello World"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_invalid_username(self):
        """Test authentication failure with wrong username"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        auth_header = self.create_auth_header("wronguser", "testpass")
        response = client.get("/", headers={"authorization": auth_header})
        
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"
        assert response.text == "Unauthorized"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_invalid_password(self):
        """Test authentication failure with wrong password"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        auth_header = self.create_auth_header("testuser", "wrongpass")
        response = client.get("/", headers={"authorization": auth_header})
        
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"
        assert response.text == "Unauthorized"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_no_authorization_header(self):
        """Test authentication failure with no authorization header"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        response = client.get("/")
        
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"
        assert response.text == "Unauthorized"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_invalid_auth_header_format(self):
        """Test authentication failure with invalid header format"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        response = client.get("/", headers={"authorization": "Bearer token123"})
        
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"
        assert response.text == "Unauthorized"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_malformed_basic_auth(self):
        """Test authentication failure with malformed Basic auth"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        # Invalid base64
        response = client.get("/", headers={"authorization": "Basic invalid_base64"})
        
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"
        assert response.text == "Unauthorized"
    
    def test_missing_environment_variables(self):
        """Test server error when environment variables are not set"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        auth_header = self.create_auth_header("user", "pass")
        response = client.get("/", headers={"authorization": auth_header})
        
        assert response.status_code == 500
        assert response.text == "Basic auth not configured"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_health_endpoint_bypass(self):
        """Test that health check endpoints bypass authentication"""
        test_app = Starlette(routes=[Route("/api/health", health_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        # No authorization header should still work for health endpoint
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.text == "OK"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_health_endpoint_with_auth(self):
        """Test that health check endpoints work with authentication too"""
        test_app = Starlette(routes=[Route("/api/health", health_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        auth_header = self.create_auth_header("testuser", "testpass")
        response = client.get("/api/health", headers={"authorization": auth_header})
        
        assert response.status_code == 200
        assert response.text == "OK"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "", "BASIC_AUTH_PASS": "testpass"})
    def test_empty_username_env(self):
        """Test server error when username environment variable is empty"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        auth_header = self.create_auth_header("user", "pass")
        response = client.get("/", headers={"authorization": auth_header})
        
        assert response.status_code == 500
        assert response.text == "Basic auth not configured"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": ""})
    def test_empty_password_env(self):
        """Test server error when password environment variable is empty"""
        test_app = Starlette(routes=[Route("/", hello_endpoint)])
        test_app.add_middleware(BasicAuthMiddleware)
        client = TestClient(test_app)
        
        auth_header = self.create_auth_header("testuser", "testpass")
        response = client.get("/", headers={"authorization": auth_header})
        
        assert response.status_code == 500
        assert response.text == "Basic auth not configured"