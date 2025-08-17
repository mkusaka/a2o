# Python 3.11 base image for AWS Lambda
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Install system packages
RUN yum update -y && \
    yum install -y gcc gcc-c++ make tar gzip && \
    yum clean all

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml uv.lock ${LAMBDA_TASK_ROOT}/

# Install dependencies from lockfile using uv
# --system flag installs to system Python
RUN uv sync --frozen --no-dev --system

# Copy configuration file
COPY config.yaml ${LAMBDA_TASK_ROOT}/

# Copy Lambda handler Python file
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Specify Lambda handler
CMD ["lambda_handler.handler"]