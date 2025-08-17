# AWS Lambda用のPython 3.11ベースイメージ
FROM public.ecr.aws/lambda/python:3.11

# 作業ディレクトリ設定
WORKDIR ${LAMBDA_TASK_ROOT}

# システムパッケージのインストール
RUN yum update -y && \
    yum install -y gcc gcc-c++ make && \
    yum clean all

# uvのインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 依存関係ファイルのコピー
COPY pyproject.toml uv.lock ${LAMBDA_TASK_ROOT}/

# uvを使用してlockfileから依存関係をインストール
# --systemフラグでシステムPythonにインストール
RUN uv sync --frozen --no-dev --system

# 設定ファイルのコピー
COPY config.yaml ${LAMBDA_TASK_ROOT}/

# Lambda handler用のPythonファイルをコピー
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Lambdaハンドラーの指定
CMD ["lambda_handler.handler"]