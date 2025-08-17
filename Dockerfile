# AWS Lambda用のPython 3.11ベースイメージ
FROM public.ecr.aws/lambda/python:3.11

# 作業ディレクトリ設定
WORKDIR ${LAMBDA_TASK_ROOT}

# システムパッケージのインストール
RUN yum update -y && \
    yum install -y gcc gcc-c++ make && \
    yum clean all

# Python依存関係のインストール
# litellm[proxy]でproxy機能を含む完全インストール
RUN pip install --no-cache-dir \
    litellm[proxy]>=1.42.0 \
    mangum>=0.17.0 \
    uvloop>=0.19.0

# 設定ファイルのコピー
COPY config.yaml ${LAMBDA_TASK_ROOT}/

# Lambda handler用のPythonファイルをコピー
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Lambdaハンドラーの指定
CMD ["lambda_handler.handler"]