.PHONY: install run clean stop test

install:
	uv venv
	uv pip install -e .

run:
	export LITELLM_MASTER_KEY=$${LITELLM_MASTER_KEY:-dev-local} && \
	export OPENAI_API_KEY=$${OPENAI_API_KEY} && \
	litellm --config config.yaml --port 4000 --detailed_debug

test:
	curl -N http://localhost:4000/v1/messages \
		-H 'content-type: application/json' \
		-H 'anthropic-version: 2023-06-01' \
		-H "authorization: Bearer $${OPENAI_API_KEY}" \
		-H "a2o-endpoint: $${OPENAI_BASE_URL:-https://api.openai.com/v1}" \
		-d '{ \
			"model": "'$${OPENAI_MODEL:-gpt-4o-mini}'", \
			"max_tokens": 100, \
			"messages": [{"role":"user","content":"Say hello"}], \
			"stream": true \
		}'

stop:
	pkill -f "litellm --config config.yaml" || true

clean:
	rm -rf .venv __pycache__ *.egg-info