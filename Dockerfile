# Multi-stage build for AWS Lambda with uv package manager

# Stage 1: Get uv binary from official image
FROM ghcr.io/astral-sh/uv:0.5.14 AS uv

# Stage 2: Build dependencies
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11 AS builder

# Work directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# Export to requirements.txt and use pip with specific options for problematic packages
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    /usr/local/bin/uv export --frozen --no-emit-workspace --no-dev -o requirements.txt && \
    pip install --no-cache-dir --prefer-binary \
        --only-binary=polars,pandas,numpy,scipy,scikit-learn,tokenizers \
        -r requirements.txt

# Stage 3: Final runtime image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy installed packages from builder
COPY --from=builder /var/lang/lib/python3.11/site-packages /var/lang/lib/python3.11/site-packages

# Copy application files
COPY config.yaml ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Specify Lambda handler
CMD ["lambda_handler.handler"]