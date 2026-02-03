# Линтер
.PHONY: lint
lint:
	flake8 *.py src/*/*.py

# Запуск приложения
.PHONY: run_app
run_app:
	python -m src.main

.PHONY: vllm
vllm:
	vllm serve --config 'config/vllm.yml'


# Оценка качества
.PHONY: eval-quick
eval-quick:
	@echo "🚀 Быстрая оценка (только текст)..."
	python -m scripts.generate_dataset --count 100 --filename test_dataset.json
	python -m scripts.evaluate --dataset data/datasets/test_dataset.json --modality text
	python -m scripts.analyze_results --text-metrics data/results/text_metrics.json
	@echo "✓ Готово! Откройте data/results/report.html"

.PHONY: eval-full
eval-full:
	@echo "🚀 Полная оценка (текст + аудио)..."
	python -m scripts.generate_dataset --count 600 --seed 42
	python -m scripts.synthesize_audio --input data/datasets/evaluation_dataset.json --device cuda
	python -m scripts.evaluate --dataset data/datasets/evaluation_dataset_with_audio.json --modality both
	python -m scripts.analyze_results.py \
		--text-metrics data/results/text_metrics.json \
		--audio-metrics data/results/audio_metrics.json \
		--gap-metrics data/results/modality_gap.json
	@echo "✓ Готово! Откройте data/results/report.html"