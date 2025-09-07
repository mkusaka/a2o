FROM ghcr.io/berriai/litellm:main-latest

WORKDIR /app

COPY config.yaml /app/config.yaml
COPY custom_callbacks.py /app/custom_callbacks.py

EXPOSE 4000

CMD ["--config", "/app/config.yaml", "--port", "4000", "--detailed_debug"]