# custom_callbacks.py
import json, re, time
from typing import Any, Dict
from litellm.integrations.custom_logger import CustomLogger
from litellm import AnthropicConfig

# Allowed pattern for a2o-endpoint (SSRF protection)
ALLOW = re.compile(r"^https://[a-z0-9.-]+(?::\d+)?/v1/?$", re.I)

class AnthropicAdapter(CustomLogger):
    """
    /v1/messages (Anthropic) -> OpenAI-compatible /chat/completions conversion
    - Uses client-provided model / API key / a2o-endpoint as-is
    - Supports both stream and non-stream (LiteLLM handles SSE passthrough)
    """

    def translate_completion_input_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        # Debug: print kwargs structure
        import sys
        print(f"DEBUG: kwargs keys = {list(kwargs.keys())}", file=sys.stderr)
        
        # 1) Anthropic -> OpenAI-compatible body conversion
        oai_kwargs = AnthropicConfig().translate_anthropic_to_openai(
            anthropic_message_request=kwargs
        )

        # 2) Get headers - try proxy_server_request first, then metadata
        headers = kwargs.get("proxy_server_request", {}).get("headers", {})
        headers = headers or kwargs.get("metadata", {}).get("headers", {})
        headers = {k.lower(): v for k, v in headers.items()}
        
        print(f"DEBUG: headers = {list(headers.keys())}", file=sys.stderr)

        # 3) Upstream OpenAI-compatible endpoint (a2o-endpoint)
        api_base = headers["a2o-endpoint"].strip()
        assert ALLOW.match(api_base), f"invalid a2o-endpoint: {api_base}"

        # 4) Client API key (Authorization or x-api-key)
        user_key = headers.get("authorization", headers.get("x-api-key", "")).replace("Bearer ", "").strip()
        assert user_key, "missing upstream api key"
        
        print(f"DEBUG: api_base = {api_base}, api_key = {user_key[:10]}...", file=sys.stderr)

        # 5) Per-request routing to OpenAI-compatible endpoint
        #    api_base / api_key can be specified per-call
        oai_kwargs["custom_llm_provider"] = "openai"
        oai_kwargs["api_base"] = api_base.rstrip("/")
        oai_kwargs["api_key"] = user_key
        # model uses client-specified value as-is (can be overridden if needed)

        return oai_kwargs

    def translate_completion_output_params(self, response: Any) -> Dict[str, Any]:
        # OpenAI-compatible response -> Anthropic format
        return AnthropicConfig().translate_openai_response_to_anthropic(response=response)

anthropic_adapter = AnthropicAdapter()


# Structured logging (JSON to stdout)
class AdapterLogger(CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        meta = (kwargs.get("litellm_params") or {}).get("metadata") or {}
        headers = meta.get("headers") or {}
        body = kwargs
        
        # Convert usage object to dict recursively
        def to_dict(obj):
            if obj is None:
                return None
            if isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, dict):
                return {k: to_dict(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [to_dict(item) for item in obj]
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "__dict__"):
                return to_dict(obj.__dict__)
            return str(obj)
        
        usage = getattr(response_obj, "usage", None) or response_obj.get("usage")
        
        log = {
            "ts": int(time.time() * 1000),
            "event": "proxy.success",
            "path": meta.get("path") or "/v1/messages",
            "endpoint": headers.get("a2o-endpoint"),
            "model": body.get("model"),
            "stream": bool(body.get("stream")),
            "usage": to_dict(usage),
        }
        print(json.dumps(log, ensure_ascii=False))

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        meta = (kwargs.get("litellm_params") or {}).get("metadata") or {}
        headers = meta.get("headers") or {}
        log = {
            "ts": int(time.time() * 1000),
            "event": "proxy.failure",
            "path": meta.get("path") or "/v1/messages",
            "endpoint": headers.get("a2o-endpoint"),
            "model": kwargs.get("model"),
            "error": str(response_obj),
        }
        print(json.dumps(log, ensure_ascii=False))

adapter_logger = AdapterLogger()