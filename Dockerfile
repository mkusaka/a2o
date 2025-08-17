# Multi-stage build for AWS Lambda with uv package manager

# Stage 1: Get uv binary from official image
FROM ghcr.io/astral-sh/uv:0.5.14 AS uv

# Stage 2: Build dependencies
FROM public.ecr.aws/lambda/python:3.11 AS builder

# Environment variables for uv optimization
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy

# Work directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (mounted from stage 1)
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    /usr/local/bin/uv export --frozen --no-emit-workspace --no-dev -o requirements.txt && \
    /usr/local/bin/uv pip install -r requirements.txt --system --no-cache

# Stage 3: Final runtime image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy installed packages from builder
COPY --from=builder /var/lang/lib/python3.11/site-packages /var/lang/lib/python3.11/site-packages

# Copy application files
COPY config.yaml ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Specify Lambda handler
CMD ["lambda_handler.handler"]