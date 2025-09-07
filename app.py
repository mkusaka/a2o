"""
a2o - Anthropic to OpenAI Proxy
FastAPI-based proxy server with LiteLLM for format conversion
"""

import json
import os
import time
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import litellm
from litellm import acompletion, ModelResponse
import httpx

app = FastAPI(title="a2o", version="2.0.0")

class Message(BaseModel):
    role: str
    content: str | List[Dict[str, Any]]

class AnthropicRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: int = 1024
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: bool = False
    system: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    stop_sequences: Optional[List[str]] = None

class ProviderConfig:
    """Provider configuration and routing"""
    
    PROVIDER_MAP = {
        # OpenAI models
        "gpt-4o": "openai",
        "gpt-4o-mini": "openai",
        "gpt-4-turbo": "openai",
        "gpt-3.5-turbo": "openai",
        
        # Cerebras models
        "qwen-3-coder-480b": "cerebras",
        "llama3.1-8b": "cerebras",
        "llama3.1-70b": "cerebras",
        
        # Add more model mappings as needed
    }
    
    ENDPOINT_MAP = {
        "openai": "https://api.openai.com/v1",
        "cerebras": "https://api.cerebras.ai/v1",
    }
    
    @classmethod
    def get_provider(cls, model: str, endpoint_header: Optional[str] = None) -> tuple[str, str]:
        """Determine provider and endpoint from model name or header"""
        if endpoint_header:
            # If endpoint header is provided, try to determine provider from it
            for provider, endpoint in cls.ENDPOINT_MAP.items():
                if endpoint in endpoint_header:
                    return provider, endpoint_header
            # Unknown endpoint, use as custom
            return "openai", endpoint_header
        
        # Determine from model name
        provider = cls.PROVIDER_MAP.get(model, "openai")
        endpoint = cls.ENDPOINT_MAP.get(provider, "https://api.openai.com/v1")
        return provider, endpoint

def convert_anthropic_to_openai(request: AnthropicRequest) -> Dict[str, Any]:
    """Convert Anthropic message format to OpenAI format"""
    messages = []
    
    # Add system message if present
    if request.system:
        messages.append({"role": "system", "content": request.system})
    
    # Convert messages
    for msg in request.messages:
        role = msg.role
        content = msg.content
        
        # Handle role mapping
        if role == "assistant":
            role = "assistant"
        elif role == "user":
            role = "user"
        
        messages.append({"role": role, "content": content})
    
    # Build OpenAI request
    openai_request = {
        "model": request.model,
        "messages": messages,
        "max_tokens": request.max_tokens,
        "stream": request.stream,
    }
    
    # Add optional parameters
    if request.temperature is not None:
        openai_request["temperature"] = request.temperature
    if request.top_p is not None:
        openai_request["top_p"] = request.top_p
    if request.stop_sequences:
        openai_request["stop"] = request.stop_sequences
    
    return openai_request

def convert_openai_to_anthropic_response(response: ModelResponse, stream: bool = False) -> Dict[str, Any]:
    """Convert OpenAI response to Anthropic format"""
    if stream:
        # Handle streaming response chunk
        if not response.choices or not response.choices[0].delta:
            return None
        
        delta = response.choices[0].delta
        content = delta.get("content", "")
        
        if not content:
            return None
        
        return {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": content}
        }
    else:
        # Handle non-streaming response
        content = response.choices[0].message.content
        
        return {
            "id": f"msg_{response.id}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": response.model,
            "stop_reason": response.choices[0].finish_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        }

async def stream_anthropic_response(
    response_stream: AsyncGenerator,
    request_id: str,
    model: str
) -> AsyncGenerator[str, None]:
    """Convert OpenAI SSE stream to Anthropic SSE format"""
    # Send initial message_start event
    start_event = {
        "type": "message_start",
        "message": {
            "id": request_id,
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": model,
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }
    }
    yield f"event: message_start\ndata: {json.dumps(start_event)}\n\n"
    
    # Send content_block_start event
    block_start = {
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""}
    }
    yield f"event: content_block_start\ndata: {json.dumps(block_start)}\n\n"
    
    # Stream content deltas
    total_tokens = 0
    async for chunk in response_stream:
        if chunk.choices and chunk.choices[0].delta:
            content = chunk.choices[0].delta.get("content", "")
            if content:
                total_tokens += 1
                delta_event = {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": content}
                }
                yield f"event: content_block_delta\ndata: {json.dumps(delta_event)}\n\n"
    
    # Send content_block_stop event
    yield f'event: content_block_stop\ndata: {{"type": "content_block_stop", "index": 0}}\n\n'
    
    # Send message_delta with usage
    usage_event = {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
        "usage": {"output_tokens": total_tokens}
    }
    yield f"event: message_delta\ndata: {json.dumps(usage_event)}\n\n"
    
    # Send message_stop event
    yield f'event: message_stop\ndata: {{"type": "message_stop"}}\n\n'

def log_event(event_type: str, **kwargs):
    """Log events in structured JSON format"""
    log_entry = {
        "ts": int(time.time() * 1000),
        "event": event_type,
        **kwargs
    }
    print(json.dumps(log_entry))

@app.post("/v1/messages")
async def proxy_messages(
    request: Request,
    anthropic_version: str = Header(None, alias="anthropic-version"),
    authorization: str = Header(None),
    a2o_endpoint: Optional[str] = Header(None, alias="a2o-endpoint"),
):
    """Proxy Anthropic messages to OpenAI-compatible endpoints"""
    
    # Parse request body
    try:
        body = await request.json()
        anthropic_request = AnthropicRequest(**body)
    except Exception as e:
        log_event("proxy.error", error=str(e), path="/v1/messages")
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")
    
    # Extract API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    
    # Determine provider and endpoint
    provider, endpoint = ProviderConfig.get_provider(anthropic_request.model, a2o_endpoint)
    
    log_event(
        "proxy.request",
        path="/v1/messages",
        model=anthropic_request.model,
        provider=provider,
        endpoint=endpoint,
        stream=anthropic_request.stream
    )
    
    # Convert to OpenAI format
    openai_request = convert_anthropic_to_openai(anthropic_request)
    
    # Set up LiteLLM with provider configuration
    if provider == "cerebras":
        os.environ["CEREBRAS_API_KEY"] = api_key
        os.environ["CEREBRAS_API_BASE"] = endpoint
    elif provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
        if endpoint != "https://api.openai.com/v1":
            os.environ["OPENAI_API_BASE"] = endpoint
    
    try:
        if anthropic_request.stream:
            # Handle streaming response
            response_stream = await acompletion(
                **openai_request,
                custom_llm_provider=provider
            )
            
            request_id = f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return StreamingResponse(
                stream_anthropic_response(response_stream, request_id, anthropic_request.model),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        else:
            # Handle non-streaming response
            response = await acompletion(
                **openai_request,
                custom_llm_provider=provider
            )
            
            anthropic_response = convert_openai_to_anthropic_response(response)
            
            log_event(
                "proxy.success",
                path="/v1/messages",
                model=anthropic_request.model,
                provider=provider,
                endpoint=endpoint,
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
            
            return JSONResponse(content=anthropic_response)
            
    except Exception as e:
        log_event(
            "proxy.error",
            path="/v1/messages",
            model=anthropic_request.model,
            provider=provider,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Provider error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)