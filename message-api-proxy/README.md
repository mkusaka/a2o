# Message API Proxy

A Lambda-based proxy service that converts message API format to OpenAI compatible API format with Basic authentication.

## Features

- **Message API to OpenAI API conversion**: Converts simple message format to OpenAI chat completions API
- **Basic Authentication**: Secure access using Basic auth middleware  
- **Streaming Support**: Supports both streaming and non-streaming responses
- **Lambda Web Adapter**: Runs on AWS Lambda with Function URL and response streaming
- **Easy Deployment**: Deploy with lambroll using minimal configuration

## Directory Structure

```
message-api-proxy/
├─ app.py                 # FastAPI app with Basic auth middleware
├─ run.sh                 # Lambda Web Adapter startup script
├─ pyproject.toml         # Python dependencies (uv managed)
├─ function.json          # Lambda function configuration (lambroll)
├─ function_url.json      # Function URL configuration (lambroll)
├─ .lambdaignore          # Files to exclude from deployment
└─ scripts/
   └─ vendor.sh           # Dependency vendor script (uv)
```

## Prerequisites

- [uv](https://github.com/astral-sh/uv) - Python package manager
- [lambroll](https://github.com/fujiwara/lambroll) - Lambda deployment tool
- AWS CLI configured with appropriate permissions
- Lambda execution role with basic permissions

## Configuration

### Environment Variables

Update `function.json` with your configuration:

```json
{
  "Environment": {
    "Variables": {
      // Basic Authentication
      "BASIC_AUTH_USER": "your-username",
      "BASIC_AUTH_PASS": "your-password",
      
      // Upstream API Configuration  
      "UPSTREAM_API_BASE": "https://api.openai.com/v1",
      "UPSTREAM_API_KEY": "sk-your-openai-api-key",
      "UPSTREAM_MODEL": "gpt-4o-mini",
      
      // Lambda Web Adapter (don't change)
      "AWS_LAMBDA_EXEC_WRAPPER": "/opt/bootstrap",
      "AWS_LWA_INVOKE_MODE": "response_stream",
      "AWS_LWA_PORT": "8080",
      "AWS_LWA_READINESS_CHECK_PATH": "/health",
      "PORT": "8080"
    }
  }
}
```

### Lambda Role

Update the `Role` field in `function.json` with your Lambda execution role ARN:

```json
{
  "Role": "arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE"
}
```

## Deployment

### 1. Install Dependencies

```bash
# Vendor dependencies to zip root
bash scripts/vendor.sh
```

### 2. Deploy with lambroll

```bash
# Deploy to Tokyo region (ap-northeast-1)
lambroll deploy --region ap-northeast-1 --function-url=function_url.json

# Deploy to other regions
lambroll deploy --region us-east-1 --function-url=function_url.json
```

### 3. Get Function URL

After deployment, lambroll will output the Function URL:

```
Function URL: https://your-function-id.lambda-url.ap-northeast-1.on.aws/
```

## Usage

### API Format

The proxy accepts simple message API format and converts it to OpenAI compatible format.

**Input Format (Message API):**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "stream": true,
  "max_tokens": 100,
  "temperature": 0.7
}
```

**Converted to OpenAI Format:**
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "stream": true,
  "max_tokens": 100,
  "temperature": 0.7
}
```

### Example Requests

#### Non-streaming Request

```bash
FUNC_URL="https://your-function-id.lambda-url.ap-northeast-1.on.aws"

curl "$FUNC_URL/v1/chat/completions" \
  -u demo:demo \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"Hello from Message API Proxy"}],
    "stream": false,
    "max_tokens": 50
  }'
```

#### Streaming Request

```bash
curl -N "$FUNC_URL/v1/chat/completions" \
  -u demo:demo \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"Tell me a story"}],
    "stream": true,
    "max_tokens": 100
  }'
```

#### Alternative Endpoint

You can also use the direct message API endpoint:

```bash
curl "$FUNC_URL/chat/completions" \
  -u demo:demo \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"Hello"}],
    "stream": false
  }'
```

### Health Check

```bash
curl "$FUNC_URL/health"
# Returns: {"status":"healthy"}
```

## Development

### Local Testing

```bash
# Install dependencies
uv sync

# Run locally
uv run uvicorn app:app --host 0.0.0.0 --port 8080

# Test local endpoint
curl http://localhost:8080/v1/chat/completions \
  -u demo:demo \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"Hello local"}],
    "stream": false
  }'
```

### Updating Dependencies

```bash
# Update dependencies
uv add package-name
uv lock

# Re-vendor for deployment
bash scripts/vendor.sh
```

## Architecture

- **FastAPI**: Web framework with automatic request validation
- **Basic Auth Middleware**: Custom middleware for authentication
- **httpx**: Async HTTP client for upstream API calls  
- **Lambda Web Adapter**: Runs web applications on Lambda
- **Function URL**: Direct HTTPS endpoint with streaming support
- **Response Streaming**: Real-time streaming via Function URL

## Security Notes

- Basic authentication credentials are in environment variables
- For production, consider using AWS IAM authentication (`AuthType: "AWS_IAM"`)
- Function URL allows public access with CORS enabled - adjust as needed
- Consider adding CloudFront for additional security and caching

## Troubleshooting

### Common Issues

1. **Function timeout**: Increase `Timeout` in `function.json`
2. **Memory issues**: Increase `MemorySize` in `function.json`  
3. **Dependency issues**: Re-run `scripts/vendor.sh` after updates
4. **Auth failures**: Check `BASIC_AUTH_USER` and `BASIC_AUTH_PASS` env vars

### Logs

Check CloudWatch logs for detailed error information:

```bash
# View logs with AWS CLI
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/message-api-proxy"
```

## License

MIT License