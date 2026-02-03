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
.PHONY: eval
eval-quick:
	@echo "🚀 Быстрая оценка (только текст)..."
	python -m scripts.generate_dataset --count 100 --filename test_dataset.json
	python -m scripts.evaluate --dataset data/datasets/test_dataset.json --modality text
	python -m scripts.analyze_results --text-metrics data/datasets/results/text_metrics.json
	@echo "✓ Готово! Откройте data/results/report.html"

eval-full:
	@echo "🚀 Полная оценка (текст + аудио)..."
	python -m scripts.generate_dataset --count 600 --seed 42
	python -m scripts.synthesize_audio --input data/datasets/evaluation_dataset.json --device cuda
	python -m scripts.evaluate --dataset data/datasets/evaluation_dataset_with_audio.json --modality both
	python -m scripts.analyze_results \
		--text-metrics data/datasets/results/text_metrics.json \
		--audio-metrics data/datasets/results/audio_metrics.json \
		--gap-metrics data/datasets/results/modality_gap.json
	@echo "✓ Готово! Откройте data/results/report.html"


# Синтезирование датасета
.PHONY: generate-dataset
generate-dataset:
	python scripts/generate_dataset.py --count 600 --seed 42

# Синтез аудио
.PHONY: synthesize-audio
synthesize-audio:
	python -m scripts.synthesize_audio \
		--input data/datasets/evaluation_dataset.json \
		--output data/datasets/audio \
		--device cuda

# Оценка качества
.PHONY: evaluate
evaluate:
	python -m scripts.evaluate \
		--dataset data/datasets/evaluation_dataset_with_audio.json \
		--modality both \
		--output data/results

# Анализ результатов
.PHONY: analyze
analyze:
	python -m scripts.analyze_results \
		--text-metrics data/datasets/results/text_metrics.json \
		--audio-metrics data/datasets/results/audio_metrics.json \
		--gap-metrics data/datasets/results/modality_gap.json \
		--output data/results

# Полный пайплайн
.PHONY: full-evaluation
full-evaluation: generate-dataset synthesize-audio evaluate analyze
	@echo "✓ Полная оценка завершена!"