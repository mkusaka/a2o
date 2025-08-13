# app.py
import os
import json
import base64
import httpx
from typing import List, Dict, Any, AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

BASIC_USER = os.getenv("BASIC_AUTH_USER", "")
BASIC_PASS = os.getenv("BASIC_AUTH_PASS", "")
READINESS_PATH = os.getenv("AWS_LWA_READINESS_CHECK_PATH", "/health")
UPSTREAM_API_BASE = os.getenv("UPSTREAM_API_BASE", "https://api.openai.com/v1")
UPSTREAM_API_KEY = os.getenv("UPSTREAM_API_KEY", "")
UPSTREAM_MODEL = os.getenv("UPSTREAM_MODEL", "gpt-4o-mini")

app = FastAPI(title="Message API Proxy", description="Converts message API to OpenAI compatible API")

# Models for message API
class Message(BaseModel):
    role: str
    content: str

class MessageAPIRequest(BaseModel):
    messages: List[Message]
    stream: bool = False
    model: str = ""
    max_tokens: int = None
    temperature: float = None

# Basic Auth Middleware
class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Allow LWA health checks to pass through
        if request.url.path == READINESS_PATH:
            return await call_next(request)

        if not BASIC_USER or not BASIC_PASS:
            return Response(status_code=500, content="Basic auth not configured")

        auth = request.headers.get("authorization")
        if not auth or not auth.startswith("Basic "):
            return Response(
                status_code=401, 
                headers={"WWW-Authenticate": "Basic"},
                content="Unauthorized"
            )

        try:
            raw = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
            user, password = raw.split(":", 1)
        except Exception:
            return Response(
                status_code=401, 
                headers={"WWW-Authenticate": "Basic"},
                content="Unauthorized"
            )

        if user != BASIC_USER or password != BASIC_PASS:
            return Response(
                status_code=401, 
                headers={"WWW-Authenticate": "Basic"},
                content="Unauthorized"
            )

        return await call_next(request)

app.add_middleware(BasicAuthMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def convert_to_openai_format(message_request: MessageAPIRequest) -> Dict[str, Any]:
    """Convert message API format to OpenAI compatible format"""
    openai_request = {
        "model": UPSTREAM_MODEL,
        "messages": [{"role": msg.role, "content": msg.content} for msg in message_request.messages],
        "stream": message_request.stream
    }
    
    if message_request.max_tokens:
        openai_request["max_tokens"] = message_request.max_tokens
    if message_request.temperature is not None:
        openai_request["temperature"] = message_request.temperature
        
    return openai_request

async def stream_openai_response(response: httpx.Response) -> AsyncGenerator[str, None]:
    """Stream OpenAI API response chunks"""
    async for chunk in response.aiter_text():
        if chunk:
            yield chunk

@app.post("/v1/chat/completions")
async def chat_completions(request: MessageAPIRequest):
    """Message API endpoint that proxies to OpenAI compatible API"""
    
    if not UPSTREAM_API_BASE or not UPSTREAM_API_KEY:
        raise HTTPException(status_code=500, detail="Upstream API not configured")
    
    # Convert message API format to OpenAI format
    openai_request = convert_to_openai_format(request)
    
    headers = {
        "Authorization": f"Bearer {UPSTREAM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            if request.stream:
                # Handle streaming response
                response = await client.post(
                    f"{UPSTREAM_API_BASE}/chat/completions",
                    json=openai_request,
                    headers=headers,
                    timeout=300.0
                )
                response.raise_for_status()
                
                return StreamingResponse(
                    stream_openai_response(response),
                    media_type="text/plain",
                    headers={"Cache-Control": "no-cache"}
                )
            else:
                # Handle non-streaming response
                response = await client.post(
                    f"{UPSTREAM_API_BASE}/chat/completions",
                    json=openai_request,
                    headers=headers,
                    timeout=300.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@app.post("/chat/completions")
async def message_api_endpoint(request: MessageAPIRequest):
    """Direct message API endpoint (alternative path)"""
    return await chat_completions(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)