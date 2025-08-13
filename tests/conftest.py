import pytest
import os
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def clean_env():
    """Clean environment variables before each test"""
    original_env = {}
    keys_to_clean = ["BASIC_AUTH_USER", "BASIC_AUTH_PASS"]
    
    # Store original values
    for key in keys_to_clean:
        if key in os.environ:
            original_env[key] = os.environ[key]
        # Remove from environment
        os.environ.pop(key, None)
    
    yield
    
    # Restore original values
    for key in keys_to_clean:
        os.environ.pop(key, None)
        if key in original_env:
            os.environ[key] = original_env[key]

@pytest.fixture
def mock_litellm():
    """Mock LiteLLM imports for testing"""
    mock_app = MagicMock()
    mock_app.add_middleware = MagicMock()
    
    with patch.dict('sys.modules', {
        'litellm': MagicMock(),
        'litellm.proxy': MagicMock(),
        'litellm.proxy.proxy_server': MagicMock(app=mock_app)
    }):
        yield mock_app