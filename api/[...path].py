from litellm.proxy.proxy_server import app as _app  # LiteLLM FastAPI app
from middleware import BasicAuthMiddleware

app = _app
app.add_middleware(BasicAuthMiddleware)