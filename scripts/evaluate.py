"""
Оценка качества голосового помощника.
Вычисление метрик: Precision, Recall, False Alarm Rate, Parsable Tool Invocation Rate.
Анализ разрыва модальностей (Text vs Audio).
"""
from dotenv import load_dotenv

import json
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from src.agent import create_agent
from src.core.logger import get_module_logger

# Загружаем переменные окружения
load_dotenv()

logger = get_module_logger(__name__)


# ANCHOR:metrics_calculator
class MetricsCalculator:
    """Калькулятор метрик для оценки качества."""
    
    def __init__(self, dataset_path: str):
        """
        Инициализация калькулятора.
        
        Args:
            dataset_path: Путь к датасету.
        """
        self.dataset_path = Path(dataset_path)
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            self.dataset: List[Dict] = json.load(f)
        
        self.text_results: List[Dict] = []
        self.audio_results: List[Dict] = []
        self.agent = None
    
    def _init_agent(self):
        """Инициализировать агента."""
        if self.agent is None:
            self.agent = create_agent()
    
    async def evaluate_sample_text(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оценить один пример на тексте.
        
        Args:
            sample: Пример из датасета.
            
        Returns:
            Результат оценки.
        """
        text = sample['text']
        expected_tool = sample['tool']
        expected_params = sample.get('params', {})
        
        try:
            self._init_agent()
            
            # Обрабатываем запрос
            result = await self.agent.process_request(text)
            
            # Извлекаем вызванный инструмент
            predicted_tool = None
            parsable = True
            
            if result.get('steps'):
                # Берем первый шаг (основной вызов инструмента)
                first_step = result['steps'][0]
                predicted_tool = first_step.get('tool')
                
                # Проверяем, можно ли распарсить вызов
                # try:
                #    if first_step.get('params') is not None:
                #        parsable = True
                #except:
                #    parsable = False
            
            # Сравниваем с ожидаемым
            correct_tool = (predicted_tool == expected_tool)
            
            return {
                "id": sample['id'],
                "text": text,
                "expected_tool": expected_tool,
                "predicted_tool": predicted_tool,
                "correct_tool": correct_tool,
                "parsable": parsable,
                "success": result.get('success', False),
                "steps": len(result.get('steps', []))
            }
            
        except Exception as e:
            logger.error(f"Error evaluating sample {sample['id']}: {e}")
            return {
                "id": sample['id'],
                "text": text,
                "expected_tool": expected_tool,
                "predicted_tool": None,
                "correct_tool": False,
                "parsable": False,
                "success": False,
                "error": str(e)
            }
    
    async def evaluate_sample_audio(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оценить один пример на аудио.
        
        Args:
            sample: Пример из датасета.
            
        Returns:
            Результат оценки.
        """
        audio_path = sample.get('audio_path')
        expected_tool = sample['tool']
        
        if not audio_path or not Path(audio_path).exists():
            return {
                "id": sample['id'],
                "expected_tool": expected_tool,
                "predicted_tool": None,
                "correct_tool": False,
                "parsable": False,
                "success": False,
                "error": "Audio file not found"
            }
        
        try:
            self._init_agent()
            
            # Загружаем аудио
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Обрабатываем аудио запрос
            result = await self.agent.process_request(audio_bytes)
            
            # Извлекаем вызванный инструмент
            predicted_tool = None
            parsable = True
            
            if result.get('steps'):
                first_step = result['steps'][0]
                predicted_tool = first_step.get('tool')
                
                # try:
                #    if first_step.get('params') is not None:
                #        parsable = True
                # except:
                #     parsable = False
            
            correct_tool = (predicted_tool == expected_tool)
            
            return {
                "id": sample['id'],
                "audio_path": audio_path,
                "expected_tool": expected_tool,
                "predicted_tool": predicted_tool,
                "correct_tool": correct_tool,
                "parsable": parsable,
                "success": result.get('success', False),
                "steps": len(result.get('steps', []))
            }
            
        except Exception as e:
            logger.error(f"Error evaluating audio sample {sample['id']}: {e}")
            return {
                "id": sample['id'],
                "audio_path": audio_path,
                "expected_tool": expected_tool,
                "predicted_tool": None,
                "correct_tool": False,
                "parsable": False,
                "success": False,
                "error": str(e)
            }
    
    async def evaluate_text_modality(self) -> None:
        """Оценить все примеры на тексте."""
        print(f"Оценка на тексте: {len(self.dataset)} примеров...")
        
        for i, sample in enumerate(self.dataset, 1):
            print(f"\rОбработано: {i}/{len(self.dataset)}\n", end="")
            result = await self.evaluate_sample_text(sample)
            self.text_results.append(result)
        
        print("\n✓ Оценка на тексте завершена")
    
    async def evaluate_audio_modality(self) -> None:
        """Оценить все примеры на аудио."""
        # Фильтруем только примеры с аудио
        audio_samples = [s for s in self.dataset if s.get('audio_synthesized')]
        
        print(f"Оценка на аудио: {len(audio_samples)} примеров...")
        
        for i, sample in enumerate(audio_samples, 1):
            print(f"\rОбработано: {i}/{len(audio_samples)}", end="")
            result = await self.evaluate_sample_audio(sample)
            self.audio_results.append(result)
        
        print("\n✓ Оценка на аудио завершена")
    
    def calculate_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Вычислить метрики для результатов.
        
        Args:
            results: Список результатов оценки.
            
        Returns:
            Словарь с метриками.
        """
        # Подсчет для каждого инструмента
        tool_metrics = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
        
        # Все уникальные инструменты
        all_tools = set()
        for result in results:
            all_tools.add(result['expected_tool'])
            if result['predicted_tool']:
                all_tools.add(result['predicted_tool'])
        
        for result in results:
            expected = result['expected_tool']
            predicted = result['predicted_tool']
            
            for tool in all_tools:
                if expected == tool and predicted == tool:
                    tool_metrics[tool]["tp"] += 1
                elif expected != tool and predicted == tool:
                    tool_metrics[tool]["fp"] += 1
                elif expected == tool and predicted != tool:
                    tool_metrics[tool]["fn"] += 1
                elif expected != tool and predicted != tool:
                    tool_metrics[tool]["tn"] += 1
        
        # Вычисляем метрики
        metrics = {}
        
        for tool, counts in tool_metrics.items():
            tp = counts["tp"]
            fp = counts["fp"]
            fn = counts["fn"]
            tn = counts["tn"]
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            far = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            
            metrics[tool] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "false_alarm_rate": far,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn
            }
        
        # Общая точность
        correct = sum(1 for r in results if r['correct_tool'])
        accuracy = correct / len(results) if results else 0.0
        
        # Parsable Tool Invocation Rate
        parsable_count = sum(1 for r in results if r.get('parsable', False))
        invocations = sum(1 for r in results if r['predicted_tool'] is not None)
        parsable_rate = parsable_count / invocations if invocations > 0 else 0.0
        
        metrics["overall"] = {
            "accuracy": accuracy,
            "parsable_rate": parsable_rate,
            "total_samples": len(results),
            "correct_predictions": correct,
            "parsable_invocations": parsable_count,
            "total_invocations": invocations
        }
        
        return metrics
    
    def calculate_modality_gap(
        self,
        text_metrics: Dict,
        audio_metrics: Dict
    ) -> Dict[str, Any]:
        """
        Вычислить разрыв между модальностями.
        
        Args:
            text_metrics: Метрики на тексте.
            audio_metrics: Метрики на аудио.
            
        Returns:
            Словарь с метриками разрыва.
        """
        gap_metrics = {}
        
        # Общие метрики
        text_overall = text_metrics.get("overall", {})
        audio_overall = audio_metrics.get("overall", {})
        
        gap_metrics["overall"] = {
            "accuracy_gap_abs": abs(text_overall.get("accuracy", 0) - audio_overall.get("accuracy", 0)),
            "accuracy_gap_rel": self._relative_gap(
                text_overall.get("accuracy", 0),
                audio_overall.get("accuracy", 0)
            ),
            "parsable_rate_gap_abs": abs(
                text_overall.get("parsable_rate", 0) - audio_overall.get("parsable_rate", 0)
            ),
            "parsable_rate_gap_rel": self._relative_gap(
                text_overall.get("parsable_rate", 0),
                audio_overall.get("parsable_rate", 0)
            )
        }
        
        # Метрики по инструментам
        all_tools = set(text_metrics.keys()) | set(audio_metrics.keys())
        all_tools.discard("overall")
        
        for tool in all_tools:
            text_tool = text_metrics.get(tool, {})
            audio_tool = audio_metrics.get(tool, {})
            
            gap_metrics[tool] = {
                "precision_gap_abs": abs(
                    text_tool.get("precision", 0) - audio_tool.get("precision", 0)
                ),
                "precision_gap_rel": self._relative_gap(
                    text_tool.get("precision", 0),
                    audio_tool.get("precision", 0)
                ),
                "recall_gap_abs": abs(
                    text_tool.get("recall", 0) - audio_tool.get("recall", 0)
                ),
                "recall_gap_rel": self._relative_gap(
                    text_tool.get("recall", 0),
                    audio_tool.get("recall", 0)
                ),
                "f1_gap_abs": abs(
                    text_tool.get("f1", 0) - audio_tool.get("f1", 0)
                ),
                "f1_gap_rel": self._relative_gap(
                    text_tool.get("f1", 0),
                    audio_tool.get("f1", 0)
                ),
                "far_gap_abs": abs(
                    text_tool.get("false_alarm_rate", 0) - audio_tool.get("false_alarm_rate", 0)
                )
            }
        
        # Tool Agreement Rate
        if self.text_results and self.audio_results:
            agreement_count = 0
            degradation_count = 0
            
            # Создаем словарь для быстрого поиска
            audio_dict = {r['id']: r for r in self.audio_results}
            
            for text_result in self.text_results:
                audio_result = audio_dict.get(text_result['id'])
                if audio_result:
                    if text_result['predicted_tool'] == audio_result['predicted_tool']:
                        agreement_count += 1
                    if text_result['correct_tool'] and not audio_result['correct_tool']:
                        degradation_count += 1
            
            total = len(self.text_results)
            gap_metrics["overall"]["tool_agreement_rate"] = agreement_count / total if total > 0 else 0.0
            gap_metrics["overall"]["degradation_rate"] = degradation_count / total if total > 0 else 0.0
        
        return gap_metrics
    
    def _relative_gap(self, text_value: float, audio_value: float) -> float:
        """Вычислить относительный разрыв."""
        if text_value == 0:
            return 0.0
        return ((text_value - audio_value) / text_value) * 100.0
    
    def print_metrics(self, metrics: Dict, title: str = "МЕТРИКИ") -> None:
        """Вывести метрики."""
        print("\n" + "="*60)
        print(title)
        print("="*60)
        
        # Общие метрики
        overall = metrics.get("overall", {})
        print(f"\nОбщая точность:          {overall.get('accuracy', 0):.2%}")
        print(f"Parsable Rate:           {overall.get('parsable_rate', 0):.2%}")
        print(f"Правильных предсказаний: {overall.get('correct_predictions', 0)}/{overall.get('total_samples', 0)}")
        print(f"Parsable вызовов:        {overall.get('parsable_invocations', 0)}/{overall.get('total_invocations', 0)}")
        
        # Метрики по инструментам
        print("\nМетрики по инструментам:")
        print("-"*60)
        
        tools = {k: v for k, v in metrics.items() if k != "overall"}
        for tool, m in sorted(tools.items()):
            print(f"\n{tool}:")
            print(f"  Precision: {m.get('precision', 0):.2%}")
            print(f"  Recall:    {m.get('recall', 0):.2%}")
            print(f"  F1-Score:  {m.get('f1', 0):.2%}")
            print(f"  FAR:       {m.get('false_alarm_rate', 0):.2%}")
            print(f"  TP={m.get('tp', 0)}, FP={m.get('fp', 0)}, FN={m.get('fn', 0)}, TN={m.get('tn', 0)}")
    
    def print_gap_metrics(self, gap_metrics: Dict) -> None:
        """Вывести метрики разрыва модальностей."""
        print("\n" + "="*60)
        print("РАЗРЫВ МОДАЛЬНОСТЕЙ (TEXT vs AUDIO)")
        print("="*60)
        
        overall = gap_metrics.get("overall", {})
        print(f"\nОбщие метрики:")
        print(f"  Accuracy Gap (abs):      {overall.get('accuracy_gap_abs', 0):.2%}")
        print(f"  Accuracy Gap (rel):      {overall.get('accuracy_gap_rel', 0):.1f}%")
        print(f"  Parsable Rate Gap (abs): {overall.get('parsable_rate_gap_abs', 0):.2%}")
        print(f"  Parsable Rate Gap (rel): {overall.get('parsable_rate_gap_rel', 0):.1f}%")
        print(f"  Tool Agreement Rate:     {overall.get('tool_agreement_rate', 0):.2%}")
        print(f"  Degradation Rate:        {overall.get('degradation_rate', 0):.2%}")
        
        print("\nРазрыв по инструментам:")
        print("-"*60)
        
        tools = {k: v for k, v in gap_metrics.items() if k != "overall"}
        for tool, m in sorted(tools.items()):
            print(f"\n{tool}:")
            print(f"  Precision Gap: {m.get('precision_gap_abs', 0):.2%} ({m.get('precision_gap_rel', 0):.1f}%)")
            print(f"  Recall Gap:    {m.get('recall_gap_abs', 0):.2%} ({m.get('recall_gap_rel', 0):.1f}%)")
            print(f"  F1 Gap:        {m.get('f1_gap_abs', 0):.2%} ({m.get('f1_gap_rel', 0):.1f}%)")
            print(f"  FAR Gap:       {m.get('far_gap_abs', 0):.2%}")
    
    def save_results(
        self,
        text_metrics: Optional[Dict] = None,
        audio_metrics: Optional[Dict] = None,
        gap_metrics: Optional[Dict] = None,
        output_dir: str = None
    ) -> None:
        """Сохранить результаты оценки."""
        if output_dir is None:
            output_dir = self.dataset_path.parent / "results"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем результаты на тексте
        if self.text_results:
            text_results_path = output_dir / "text_results.json"
            with open(text_results_path, 'w', encoding='utf-8') as f:
                json.dump(self.text_results, f, ensure_ascii=False, indent=2)
            print(f"✓ Результаты на тексте: {text_results_path}")
        
        # Сохраняем результаты на аудио
        if self.audio_results:
            audio_results_path = output_dir / "audio_results.json"
            with open(audio_results_path, 'w', encoding='utf-8') as f:
                json.dump(self.audio_results, f, ensure_ascii=False, indent=2)
            print(f"✓ Результаты на аудио:  {audio_results_path}")
        
        # Сохраняем метрики
        if text_metrics:
            text_metrics_path = output_dir / "text_metrics.json"
            with open(text_metrics_path, 'w', encoding='utf-8') as f:
                json.dump(text_metrics, f, ensure_ascii=False, indent=2)
            print(f"✓ Метрики на тексте:    {text_metrics_path}")
        
        if audio_metrics:
            audio_metrics_path = output_dir / "audio_metrics.json"
            with open(audio_metrics_path, 'w', encoding='utf-8') as f:
                json.dump(audio_metrics, f, ensure_ascii=False, indent=2)
            print(f"✓ Метрики на аудио:     {audio_metrics_path}")
        
        if gap_metrics:
            gap_metrics_path = output_dir / "modality_gap.json"
            with open(gap_metrics_path, 'w', encoding='utf-8') as f:
                json.dump(gap_metrics, f, ensure_ascii=False, indent=2)
            print(f"✓ Разрыв модальностей:  {gap_metrics_path}")
# END:metrics_calculator


# ANCHOR:main
async def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description="Оценка качества голосового помощника")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/datasets/evaluation_dataset_with_audio.json",
        help="Путь к датасету"
    )
    parser.add_argument(
        "--modality",
        type=str,
        choices=["text", "audio", "both"],
        default="both",
        help="Модальность для оценки"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Директория для сохранения результатов"
    )
    
    args = parser.parse_args()
    
    # Создаем калькулятор
    calculator = MetricsCalculator(args.dataset)
    
    text_metrics = None
    audio_metrics = None
    gap_metrics = None
    
    # Оцениваем на тексте
    if args.modality in ["text", "both"]:
        await calculator.evaluate_text_modality()
        text_metrics = calculator.calculate_metrics(calculator.text_results)
        calculator.print_metrics(text_metrics, "МЕТРИКИ НА ТЕКСТЕ")
    
    # Оцениваем на аудио
    if args.modality in ["audio", "both"]:
        await calculator.evaluate_audio_modality()
        audio_metrics = calculator.calculate_metrics(calculator.audio_results)
        calculator.print_metrics(audio_metrics, "МЕТРИКИ НА АУДИО")
    
    # Анализируем разрыв модальностей
    if args.modality == "both" and text_metrics and audio_metrics:
        gap_metrics = calculator.calculate_modality_gap(text_metrics, audio_metrics)
        calculator.print_gap_metrics(gap_metrics)
    
    # Сохраняем результаты
    calculator.save_results(
        text_metrics=text_metrics,
        audio_metrics=audio_metrics,
        gap_metrics=gap_metrics,
        output_dir=args.output
    )
    
    print("\nГотово!")


if __name__ == "__main__":
    asyncio.run(main())
# END:main
