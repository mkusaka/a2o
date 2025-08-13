import json
import os
from unittest.mock import MagicMock, patch
import pytest
import responses
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from starlette.testclient import TestClient

from middleware import BasicAuthMiddleware


# Mock LiteLLM responses
OPENAI_CHAT_COMPLETION_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I assist you today?"
            },
            "logprobs": None,
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 13,
        "completion_tokens": 7,
        "total_tokens": 20
    }
}

OPENAI_STREAMING_RESPONSE = [
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":""},"logprobs":null,"finish_reason":null}]}\n\n',
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":"Hello"},"logprobs":null,"finish_reason":null}]}\n\n',
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":"! How can I assist you today?"},"logprobs":null,"finish_reason":null}]}\n\n',
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{},"logprobs":null,"finish_reason":"stop"}]}\n\n',
    'data: [DONE]\n\n'
]

ANTHROPIC_MESSAGE_RESPONSE = {
    "id": "msg_013Zva2CMHLNnXjNJJKqJ2EF",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": "Hello! How can I assist you today?"
        }
    ],
    "model": "claude-3-sonnet-20240229",
    "stop_reason": "end_turn",
    "stop_sequence": None,
    "usage": {
        "input_tokens": 13,
        "output_tokens": 7
    }
}

ANTHROPIC_STREAMING_RESPONSE = [
    'event: message_start\ndata: {"type":"message_start","message":{"id":"msg_013Zva2CMHLNnXjNJJKqJ2EF","type":"message","role":"assistant","content":[],"model":"claude-3-sonnet-20240229","stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":13,"output_tokens":0}}}\n\n',
    'event: content_block_start\ndata: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}\n\n',
    'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello"}}\n\n',
    'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"! How can I assist you today?"}}\n\n',
    'event: content_block_stop\ndata: {"type":"content_block_stop","index":0}\n\n',
    'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null},"usage":{"output_tokens":7}}\n\n',
    'event: message_stop\ndata: {"type":"message_stop"}\n\n'
]


def create_mock_litellm_app():
    """Create a mock FastAPI app that simulates LiteLLM endpoints"""
    from fastapi import Body
    from typing import Dict, Any
    
    app = FastAPI()
    
    @app.post("/v1/chat/completions")
    async def mock_openai_chat_completions(request_data: Dict[Any, Any] = Body(...)):
        if request_data.get("stream", False):
            def generate():
                for chunk in OPENAI_STREAMING_RESPONSE:
                    yield chunk
            return StreamingResponse(generate(), media_type="text/plain")
        else:
            return OPENAI_CHAT_COMPLETION_RESPONSE
    
    @app.post("/anthropic/v1/messages")
    async def mock_anthropic_messages(request_data: Dict[Any, Any] = Body(...)):
        if request_data.get("stream", False):
            def generate():
                for chunk in ANTHROPIC_STREAMING_RESPONSE:
                    yield chunk
            return StreamingResponse(generate(), media_type="text/plain")
        else:
            return ANTHROPIC_MESSAGE_RESPONSE
    
    @app.get("/api/health")
    async def health():
        return {"status": "ok"}
    
    return app


class TestLiteLLMIntegration:
    """Integration tests for LiteLLM proxy endpoints"""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock LiteLLM app with Basic auth"""
        app = create_mock_litellm_app()
        app.add_middleware(BasicAuthMiddleware)
        return app
    
    @pytest.fixture  
    def client(self, mock_app):
        """Create test client"""
        return TestClient(mock_app)
    
    @pytest.fixture
    def auth_headers(self):
        """Basic auth headers for testing"""
        import base64
        credentials = base64.b64encode(b"testuser:testpass").decode()
        return {"authorization": f"Basic {credentials}"}
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_openai_chat_completions_non_streaming(self, client, auth_headers, snapshot):
        """Test OpenAI compatible endpoint without streaming"""
        payload = {
            "model": "openai-compat",
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": False
        }
        
        response = client.post("/v1/chat/completions", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        snapshot.assert_match(json.dumps(response_data, indent=2), "openai_chat_completion.json")
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_openai_chat_completions_streaming(self, client, auth_headers, snapshot):
        """Test OpenAI compatible endpoint with streaming"""
        payload = {
            "model": "openai-compat", 
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": True
        }
        
        response = client.post("/v1/chat/completions", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Collect streaming response
        streaming_content = response.text
        snapshot.assert_match(streaming_content, "openai_streaming_response.txt")
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_anthropic_messages_non_streaming(self, client, auth_headers, snapshot):
        """Test Anthropic endpoint without streaming"""
        payload = {
            "model": "openai-compat",
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": False
        }
        
        response = client.post("/anthropic/v1/messages", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        snapshot.assert_match(json.dumps(response_data, indent=2), "anthropic_message.json")
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_anthropic_messages_streaming(self, client, auth_headers, snapshot):
        """Test Anthropic endpoint with streaming"""
        payload = {
            "model": "openai-compat",
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": True
        }
        
        response = client.post("/anthropic/v1/messages", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Collect streaming response
        streaming_content = response.text
        snapshot.assert_match(streaming_content, "anthropic_streaming_response.txt")
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_openai_endpoint_without_auth(self, client):
        """Test OpenAI endpoint returns 401 without auth"""
        payload = {
            "model": "openai-compat",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post("/v1/chat/completions", json=payload)
        
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_anthropic_endpoint_without_auth(self, client):
        """Test Anthropic endpoint returns 401 without auth"""
        payload = {
            "model": "openai-compat", 
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post("/anthropic/v1/messages", json=payload)
        
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic"
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_health_endpoint_bypasses_auth(self, client):
        """Test health endpoint bypasses authentication"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_openai_endpoint_valid_request(self, client, auth_headers):
        """Test OpenAI endpoint with valid request structure"""
        payload = {
            "model": "openai-compat",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post("/v1/chat/completions", json=payload, headers=auth_headers)
        # Should succeed because our mock accepts any dictionary
        assert response.status_code == 200
    
    @patch.dict(os.environ, {"BASIC_AUTH_USER": "testuser", "BASIC_AUTH_PASS": "testpass"})
    def test_anthropic_endpoint_valid_request(self, client, auth_headers):
        """Test Anthropic endpoint with valid request structure"""
        payload = {
            "model": "openai-compat",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post("/anthropic/v1/messages", json=payload, headers=auth_headers)
        # Should succeed because our mock accepts any dictionary
        assert response.status_code == 200