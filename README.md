# LiteLLM Proxy on AWS Lambda

A serverless LiteLLM Proxy deployment on AWS Lambda with Basic Authentication, using Docker images for unlimited package size.

## Features

- 🚀 **Serverless deployment** on AWS Lambda with Docker images
- 🔐 **Basic Authentication** for API protection
- 🤖 **Multi-provider support** (Anthropic, OpenAI, etc.)
- 📦 **No package size limits** (Docker images up to 10GB)
- 🔄 **OpenAI-compatible API** for easy integration
- ⚡ **Auto-scaling** with AWS Lambda

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Docker installed and running
- Node.js 18+ and pnpm:
  ```bash
  npm install -g pnpm@9.6.0
  ```

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/mkusaka/a2o.git
cd a2o
pnpm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Required
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your-secure-password
ANTHROPIC_API_KEY=sk-ant-...

# Optional
OPENAI_API_KEY=sk-...
AWS_REGION=us-east-1
```

### 3. Deploy

```bash
pnpm deploy
```

After deployment, you'll get an API endpoint:
```
https://xxxxxx.execute-api.us-east-1.amazonaws.com/
```

## Usage

### Test the API

```bash
# Health check (no auth)
curl https://your-api.amazonaws.com/health

# List models (with auth)
curl -H "Authorization: Basic $(echo -n 'admin:password' | base64)" \
     https://your-api.amazonaws.com/v1/models
```

### Chat completion

```bash
curl -X POST https://your-api.amazonaws.com/v1/chat/completions \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Use with OpenAI SDK

```python
from openai import OpenAI
import base64

auth = base64.b64encode(b"admin:your-password").decode("utf-8")

client = OpenAI(
    base_url="https://your-api.amazonaws.com/v1",
    api_key="dummy",  # Required by SDK but not used
    default_headers={"Authorization": f"Basic {auth}"}
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Available Commands

```bash
pnpm deploy         # Full deployment
pnpm deploy:function # Update function only
pnpm logs          # View Lambda logs
pnpm info          # Show deployment info
pnpm remove        # Remove all resources
```

## Project Structure

```
.
├── Dockerfile           # Lambda container image
├── lambda_handler.py    # Lambda handler with auth
├── serverless.yml       # Serverless Framework config
├── config.yaml         # LiteLLM configuration
├── package.json        # Node.js dependencies
└── .env               # Environment variables (create from .env.example)
```

## Configuration

### Lambda Settings

Edit `serverless.yml` to adjust:
- `memorySize`: 128-10240 MB (default: 1024)
- `timeout`: 1-900 seconds (default: 30)
- `reservedConcurrency`: Max concurrent executions (default: 10)

### Supported Models

Configure models in `config.yaml`. Default support for:
- Anthropic Claude models
- OpenAI GPT models
- Any LiteLLM-supported provider

## Monitoring

```bash
# View real-time logs
pnpm logs

# Check metrics
pnpm sls metrics -f proxy
```

## Cost Optimization

- Lambda charges per request and duration
- Use reserved concurrency to control costs
- Monitor with CloudWatch
- Consider Lambda Power Tuning for optimal memory config

## Troubleshooting

### Docker build fails
- Ensure Docker daemon is running
- Check available disk space

### Deployment fails
- Verify AWS credentials: `aws sts get-caller-identity`
- Check IAM permissions for Lambda, ECR, API Gateway

### Authentication issues
- Verify Basic Auth credentials in `.env`
- Check Authorization header format: `Basic base64(username:password)`

## Development

### Local testing

```bash
docker build -t litellm-proxy .
docker run -p 8000:8080 \
  -e BASIC_AUTH_USERNAME=admin \
  -e BASIC_AUTH_PASSWORD=password \
  -e ANTHROPIC_API_KEY=your-key \
  litellm-proxy
```

### Update dependencies

```bash
# Update package.json dependencies
pnpm update

# Rebuild and deploy
pnpm deploy
```

## Security

- Basic Authentication protects all endpoints except `/health`
- API keys stored as Lambda environment variables
- Use AWS Secrets Manager for production deployments
- Enable CloudWatch logging for audit trails

## License

MIT

## Contributing

Pull requests welcome! Please ensure:
- Tests pass
- Documentation updated
- Follows existing code style

## Support

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs)

---

Built with ❤️ using [LiteLLM](https://github.com/BerriAI/litellm) and [Serverless Framework](https://www.serverless.com/)