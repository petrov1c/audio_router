"""
Анализ и визуализация результатов оценки.
Генерация графиков и HTML отчетов.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI


# ANCHOR:visualizer
class ResultsVisualizer:
    """Визуализатор результатов оценки."""
    
    def __init__(
        self,
        text_metrics_path: str,
        audio_metrics_path: str = None,
        gap_metrics_path: str = None,
        output_dir: str = "data/results/plots"
    ):
        """
        Инициализация визуализатора.
        
        Args:
            text_metrics_path: Путь к метрикам на тексте.
            audio_metrics_path: Путь к метрикам на аудио.
            gap_metrics_path: Путь к метрикам разрыва.
            output_dir: Директория для сохранения графиков.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем метрики
        with open(text_metrics_path, 'r', encoding='utf-8') as f:
            self.text_metrics = json.load(f)
        
        self.audio_metrics = None
        if audio_metrics_path and Path(audio_metrics_path).exists():
            with open(audio_metrics_path, 'r', encoding='utf-8') as f:
                self.audio_metrics = json.load(f)
        
        self.gap_metrics = None
        if gap_metrics_path and Path(gap_metrics_path).exists():
            with open(gap_metrics_path, 'r', encoding='utf-8') as f:
                self.gap_metrics = json.load(f)
    
    def plot_metrics_comparison(self) -> None:
        """Построить сравнение метрик Text vs Audio."""
        if not self.audio_metrics:
            print("⚠️  Метрики на аудио не найдены, пропускаем сравнение")
            return
        
        # Получаем инструменты
        tools = [k for k in self.text_metrics.keys() if k != "overall"]
        
        # Метрики для сравнения
        metrics_to_plot = ['precision', 'recall', 'f1', 'false_alarm_rate']
        metric_names = ['Precision', 'Recall', 'F1-Score', 'False Alarm Rate']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Сравнение метрик: Text vs Audio', fontsize=16, fontweight='bold')
        
        for idx, (metric, name) in enumerate(zip(metrics_to_plot, metric_names)):
            ax = axes[idx // 2, idx % 2]
            
            text_values = [self.text_metrics.get(tool, {}).get(metric, 0) for tool in tools]
            audio_values = [self.audio_metrics.get(tool, {}).get(metric, 0) for tool in tools]
            
            x = range(len(tools))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], text_values, width, label='Text', alpha=0.8)
            ax.bar([i + width/2 for i in x], audio_values, width, label='Audio', alpha=0.8)
            
            ax.set_xlabel('Инструмент')
            ax.set_ylabel(name)
            ax.set_title(name)
            ax.set_xticks(x)
            ax.set_xticklabels(tools, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / 'metrics_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ График сравнения метрик: {output_path}")
    
    def plot_modality_gap(self) -> None:
        """Построить график разрыва модальностей."""
        if not self.gap_metrics:
            print("⚠️  Метрики разрыва не найдены, пропускаем")
            return
        
        tools = [k for k in self.gap_metrics.keys() if k != "overall"]
        
        # Абсолютные разрывы
        precision_gaps = [self.gap_metrics.get(tool, {}).get('precision_gap_abs', 0) for tool in tools]
        recall_gaps = [self.gap_metrics.get(tool, {}).get('recall_gap_abs', 0) for tool in tools]
        f1_gaps = [self.gap_metrics.get(tool, {}).get('f1_gap_abs', 0) for tool in tools]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(tools))
        width = 0.25
        
        ax.bar([i - width for i in x], precision_gaps, width, label='Precision Gap', alpha=0.8)
        ax.bar(x, recall_gaps, width, label='Recall Gap', alpha=0.8)
        ax.bar([i + width for i in x], f1_gaps, width, label='F1 Gap', alpha=0.8)
        
        ax.set_xlabel('Инструмент')
        ax.set_ylabel('Абсолютный разрыв')
        ax.set_title('Разрыв модальностей по инструментам', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tools, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / 'modality_gap.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ График разрыва модальностей: {output_path}")
    
    def plot_per_tool_performance(self) -> None:
        """Построить график производительности по инструментам."""
        tools = [k for k in self.text_metrics.keys() if k != "overall"]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        precision = [self.text_metrics.get(tool, {}).get('precision', 0) for tool in tools]
        recall = [self.text_metrics.get(tool, {}).get('recall', 0) for tool in tools]
        f1 = [self.text_metrics.get(tool, {}).get('f1', 0) for tool in tools]
        
        x = range(len(tools))
        width = 0.25
        
        ax.bar([i - width for i in x], precision, width, label='Precision', alpha=0.8)
        ax.bar(x, recall, width, label='Recall', alpha=0.8)
        ax.bar([i + width for i in x], f1, width, label='F1-Score', alpha=0.8)
        
        ax.set_xlabel('Инструмент')
        ax.set_ylabel('Значение метрики')
        ax.set_title('Производительность по инструментам (Text)', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tools, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1.1])
        
        plt.tight_layout()
        output_path = self.output_dir / 'per_tool_performance.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ График производительности: {output_path}")
    
    def plot_overall_comparison(self) -> None:
        """Построить общее сравнение."""
        if not self.audio_metrics:
            return
        
        text_overall = self.text_metrics.get('overall', {})
        audio_overall = self.audio_metrics.get('overall', {})
        
        metrics = ['accuracy', 'parsable_rate']
        metric_names = ['Accuracy', 'Parsable Rate']
        
        text_values = [text_overall.get(m, 0) for m in metrics]
        audio_values = [audio_overall.get(m, 0) for m in metrics]
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        x = range(len(metrics))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], text_values, width, label='Text', alpha=0.8)
        ax.bar([i + width/2 for i in x], audio_values, width, label='Audio', alpha=0.8)
        
        ax.set_ylabel('Значение')
        ax.set_title('Общие метрики: Text vs Audio', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(metric_names)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1.1])
        
        plt.tight_layout()
        output_path = self.output_dir / 'overall_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ График общего сравнения: {output_path}")
    
    def generate_all_plots(self) -> None:
        """Сгенерировать все графики."""
        print("Генерация графиков...")
        
        self.plot_per_tool_performance()
        self.plot_metrics_comparison()
        self.plot_modality_gap()
        self.plot_overall_comparison()
        
        print(f"\n✓ Все графики сохранены в {self.output_dir}")
# END:visualizer


# ANCHOR:html_reporter
class HTMLReporter:
    """Генератор HTML отчетов."""
    
    def __init__(
        self,
        text_metrics: Dict,
        audio_metrics: Dict = None,
        gap_metrics: Dict = None,
        plots_dir: Path = None
    ):
        """
        Инициализация генератора отчетов.
        
        Args:
            text_metrics: Метрики на тексте.
            audio_metrics: Метрики на аудио.
            gap_metrics: Метрики разрыва.
            plots_dir: Директория с графиками.
        """
        self.text_metrics = text_metrics
        self.audio_metrics = audio_metrics
        self.gap_metrics = gap_metrics
        self.plots_dir = plots_dir
    
    def generate_report(self, output_path: str) -> None:
        """
        Сгенерировать HTML отчет.
        
        Args:
            output_path: Путь для сохранения отчета.
        """
        html = self._generate_html()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ HTML отчет: {output_path}")
    
    def _generate_html(self) -> str:
        """Сгенерировать HTML код."""
        html = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет оценки голосового помощника</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .good {
            color: #4CAF50;
            font-weight: bold;
        }
        .warning {
            color: #FF9800;
            font-weight: bold;
        }
        .bad {
            color: #F44336;
            font-weight: bold;
        }
        .plot {
            text-align: center;
            margin: 20px 0;
        }
        .plot img {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .summary h2 {
            color: white;
            border-bottom: 2px solid rgba(255,255,255,0.3);
        }
    </style>
</head>
<body>
    <h1>📊 Отчет оценки голосового помощника Audio Router</h1>
    
    <div class="summary">
        <h2>Краткая сводка</h2>
"""
        
        # Добавляем общие метрики
        text_overall = self.text_metrics.get('overall', {})
        html += f"""
        <p><strong>Общая точность (Text):</strong> {text_overall.get('accuracy', 0):.2%}</p>
        <p><strong>Parsable Rate (Text):</strong> {text_overall.get('parsable_rate', 0):.2%}</p>
        <p><strong>Всего примеров:</strong> {text_overall.get('total_samples', 0)}</p>
"""
        
        if self.audio_metrics:
            audio_overall = self.audio_metrics.get('overall', {})
            html += f"""
        <p><strong>Общая точность (Audio):</strong> {audio_overall.get('accuracy', 0):.2%}</p>
        <p><strong>Parsable Rate (Audio):</strong> {audio_overall.get('parsable_rate', 0):.2%}</p>
"""
        
        if self.gap_metrics:
            gap_overall = self.gap_metrics.get('overall', {})
            html += f"""
        <p><strong>Tool Agreement Rate:</strong> {gap_overall.get('tool_agreement_rate', 0):.2%}</p>
        <p><strong>Degradation Rate:</strong> {gap_overall.get('degradation_rate', 0):.2%}</p>
"""
        
        html += """
    </div>
"""
        
        # Добавляем графики
        if self.plots_dir:
            html += """
    <h2>📈 Визуализация</h2>
"""
            plots = [
                ('overall_comparison.png', 'Общее сравнение'),
                ('per_tool_performance.png', 'Производительность по инструментам'),
                ('metrics_comparison.png', 'Сравнение метрик'),
                ('modality_gap.png', 'Разрыв модальностей')
            ]
            
            for plot_file, plot_title in plots:
                plot_path = self.plots_dir / plot_file
                if plot_path.exists():
                    html += f"""
    <div class="plot">
        <h3>{plot_title}</h3>
        <img src="plots/{plot_file}" alt="{plot_title}">
    </div>
"""
        
        # Таблица метрик на тексте
        html += """
    <h2>📝 Метрики на тексте</h2>
    <div class="metric-card">
        <table>
            <tr>
                <th>Инструмент</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1-Score</th>
                <th>FAR</th>
            </tr>
"""
        
        tools = {k: v for k, v in self.text_metrics.items() if k != 'overall'}
        for tool, metrics in sorted(tools.items()):
            precision = metrics.get('precision', 0)
            recall = metrics.get('recall', 0)
            f1 = metrics.get('f1', 0)
            far = metrics.get('false_alarm_rate', 0)
            
            precision_class = self._get_metric_class(precision)
            recall_class = self._get_metric_class(recall)
            f1_class = self._get_metric_class(f1)
            far_class = self._get_metric_class(1 - far)  # Инвертируем для FAR
            
            html += f"""
            <tr>
                <td>{tool}</td>
                <td class="{precision_class}">{precision:.2%}</td>
                <td class="{recall_class}">{recall:.2%}</td>
                <td class="{f1_class}">{f1:.2%}</td>
                <td class="{far_class}">{far:.2%}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
"""
        
        # Таблица метрик на аудио
        if self.audio_metrics:
            html += """
    <h2>🎤 Метрики на аудио</h2>
    <div class="metric-card">
        <table>
            <tr>
                <th>Инструмент</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1-Score</th>
                <th>FAR</th>
            </tr>
"""
            
            tools = {k: v for k, v in self.audio_metrics.items() if k != 'overall'}
            for tool, metrics in sorted(tools.items()):
                precision = metrics.get('precision', 0)
                recall = metrics.get('recall', 0)
                f1 = metrics.get('f1', 0)
                far = metrics.get('false_alarm_rate', 0)
                
                precision_class = self._get_metric_class(precision)
                recall_class = self._get_metric_class(recall)
                f1_class = self._get_metric_class(f1)
                far_class = self._get_metric_class(1 - far)
                
                html += f"""
            <tr>
                <td>{tool}</td>
                <td class="{precision_class}">{precision:.2%}</td>
                <td class="{recall_class}">{recall:.2%}</td>
                <td class="{f1_class}">{f1:.2%}</td>
                <td class="{far_class}">{far:.2%}</td>
            </tr>
"""
            
            html += """
        </table>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _get_metric_class(self, value: float) -> str:
        """Получить CSS класс для метрики."""
        if value >= 0.9:
            return "good"
        elif value >= 0.7:
            return "warning"
        else:
            return "bad"
# END:html_reporter


# ANCHOR:main
def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description="Анализ и визуализация результатов")
    parser.add_argument(
        "--text-metrics",
        type=str,
        required=True,
        help="Путь к метрикам на тексте"
    )
    parser.add_argument(
        "--audio-metrics",
        type=str,
        default=None,
        help="Путь к метрикам на аудио"
    )
    parser.add_argument(
        "--gap-metrics",
        type=str,
        default=None,
        help="Путь к метрикам разрыва"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results",
        help="Директория для сохранения результатов"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    plots_dir = output_dir / "plots"
    
    # Создаем визуализатор
    visualizer = ResultsVisualizer(
        text_metrics_path=args.text_metrics,
        audio_metrics_path=args.audio_metrics,
        gap_metrics_path=args.gap_metrics,
        output_dir=str(plots_dir)
    )
    
    # Генерируем графики
    visualizer.generate_all_plots()
    
    # Генерируем HTML отчет
    with open(args.text_metrics, 'r', encoding='utf-8') as f:
        text_metrics = json.load(f)
    
    audio_metrics = None
    if args.audio_metrics and Path(args.audio_metrics).exists():
        with open(args.audio_metrics, 'r', encoding='utf-8') as f:
            audio_metrics = json.load(f)
    
    gap_metrics = None
    if args.gap_metrics and Path(args.gap_metrics).exists():
        with open(args.gap_metrics, 'r', encoding='utf-8') as f:
            gap_metrics = json.load(f)
    
    reporter = HTMLReporter(
        text_metrics=text_metrics,
        audio_metrics=audio_metrics,
        gap_metrics=gap_metrics,
        plots_dir=plots_dir
    )
    
    report_path = output_dir / "report.html"
    reporter.generate_report(str(report_path))
    
    print(f"\n{'='*60}")
    print("АНАЛИЗ ЗАВЕРШЕН")
    print(f"{'='*60}")
    print(f"Графики:     {plots_dir}")
    print(f"HTML отчет:  {report_path}")
    print("\nГотово!")


if __name__ == "__main__":
    main()
# END:main
