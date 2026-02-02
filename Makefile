.PHONY: lint
lint:
	flake8 *.py src/*/*.py

.PHONY: run_app
run_app:
	python -m src.main

.PHONY: vllm
vllm:
	vllm serve --config 'config/vllm.yml'