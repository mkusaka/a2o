# LiteLLM Proxy on AWS Lambda

Docker image-based deployment of LiteLLM Proxy with Basic Authentication on AWS Lambda.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured (`aws configure`)
3. Docker installed and running
4. Node.js and npm installed
5. Serverless Framework installed:
   ```bash
   npm install -g serverless
   ```

## Setup

### 1. Install Serverless Framework and plugins

```bash
npm init -y
npm install --save-dev serverless serverless-python-requirements
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

Edit `.env` with your API keys and credentials:
- `BASIC_AUTH_USERNAME`: Username for Basic Auth
- `BASIC_AUTH_PASSWORD`: Password for Basic Auth
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `OPENAI_API_KEY`: Your OpenAI API key (optional)

### 3. Configure AWS ECR

Create an ECR repository for your Docker image:

```bash
aws ecr create-repository --repository-name litellm-proxy-lambda --region us-east-1
```

Get the repository URI from the output and update `serverless.yml` if needed.

### 4. Build and test locally (optional)

```bash
docker build -t litellm-proxy-lambda .
docker run -p 8000:8080 \
  -e BASIC_AUTH_USERNAME=admin \
  -e BASIC_AUTH_PASSWORD=password \
  -e ANTHROPIC_API_KEY=your-key \
  litellm-proxy-lambda
```

## Deployment

### Deploy to AWS Lambda

```bash
# Load environment variables
export $(cat .env | xargs)

# Deploy using Serverless Framework
serverless deploy --verbose
```

The deployment will:
1. Build the Docker image
2. Push it to ECR
3. Create Lambda function with the image
4. Set up API Gateway
5. Configure environment variables

### Get the endpoint URL

After deployment, you'll see the API Gateway endpoint URL in the output:

```
endpoints:
  ANY - https://xxxxxx.execute-api.us-east-1.amazonaws.com/
```

## Usage

### Test the deployment

```bash
# Health check (no auth required)
curl https://your-api-gateway-url.amazonaws.com/health

# Test with Basic Auth
curl -H "Authorization: Basic $(echo -n 'admin:your-password' | base64)" \
     https://your-api-gateway-url.amazonaws.com/v1/models

# Make a chat completion request
curl -X POST https://your-api-gateway-url.amazonaws.com/v1/chat/completions \
  -H "Authorization: Basic $(echo -n 'admin:your-password' | base64)" \
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

# Create Basic Auth header
auth = base64.b64encode(b"admin:your-password").decode("utf-8")

client = OpenAI(
    base_url="https://your-api-gateway-url.amazonaws.com/v1",
    api_key="dummy",  # Not used but required by SDK
    default_headers={"Authorization": f"Basic {auth}"}
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Monitoring

### View Lambda logs

```bash
serverless logs -f proxy --tail
```

### View metrics

```bash
serverless metrics -f proxy
```

## Update and Redeploy

After making changes:

```bash
serverless deploy function -f proxy
```

For full redeploy:

```bash
serverless deploy
```

## Cleanup

To remove all resources:

```bash
serverless remove
```

This will delete:
- Lambda function
- API Gateway
- ECR images
- CloudFormation stack

## Configuration

### Memory and Timeout

Edit `serverless.yml` to adjust:
- `memorySize`: Lambda memory (128-10240 MB)
- `timeout`: Maximum execution time (1-900 seconds)
- `reservedConcurrency`: Max concurrent executions

### Environment Variables

All environment variables are configured in `serverless.yml` and sourced from your `.env` file.

## Troubleshooting

### Docker build fails
- Ensure Docker daemon is running
- Check disk space for Docker images

### Deployment fails
- Verify AWS credentials: `aws sts get-caller-identity`
- Check IAM permissions for Lambda, ECR, and API Gateway

### Function timeouts
- Increase timeout in `serverless.yml`
- Consider using Lambda with more memory

### Authentication issues
- Verify Basic Auth credentials in environment variables
- Check the Authorization header format

## Cost Optimization

- Use reserved concurrency to control costs
- Monitor with AWS CloudWatch
- Consider using Lambda@Edge for global distribution
- Use AWS Lambda Power Tuning to find optimal memory configuration