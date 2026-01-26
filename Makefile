APP_PORT := 1980


.PHONY: lint
lint:
	flake8 *.py src/*/*.py

.PHONY: run_app
run_app:
	python src/main.py

.PHONY: vllm
vllm:
	vllm serve --config 'config/vllm.yml'