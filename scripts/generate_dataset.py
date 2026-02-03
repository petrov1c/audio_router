"""
Генерация тестового датасета для голосового помощника.
Расширенная версия с 50-100 шаблонами и 500-700 примерами.
С поддержкой LLM перефразирования и двух текстов (text и text_for_tts).
"""

import json
import random
import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Добавляем путь к скриптам
sys.path.insert(0, str(Path(__file__).parent))

from date_converter import DateToTextConverter
from text_rephraser import SimpleRephraser, TextRephraser


# ANCHOR:templates
# Шаблоны для расписания рейсов (20 шаблонов)
FLIGHT_TEMPLATES = [
    # Базовые
    "Найди рейсы из {from_city} в {to_city} на {date}",
    "Покажи расписание из {from_city} в {to_city} {date}",
    "Когда летит самолет из {from_city} в {to_city} {date}",
    "Как добраться из {from_city} в {to_city} {date}",
    "Есть ли рейсы {from_city} - {to_city} на {date}",
    # Разговорные
    "Хочу полететь из {from_city} в {to_city} {date}",
    "Мне нужно в {to_city} из {from_city} {date}",
    "Поищи билеты из {from_city} в {to_city} на {date}",
    "Какие самолёты летают из {from_city} в {to_city} {date}",
    "Покажи авиарейсы {from_city} - {to_city} {date}",
    # Сложные
    "Мне надо срочно в {to_city} из {from_city}, что есть на {date}",
    "Посмотри пожалуйста рейсы из {from_city} в {to_city} на {date}",
    "Когда можно улететь из {from_city} в {to_city}, интересует {date}",
    "Проверь расписание самолётов {from_city} - {to_city} на {date}",
    "Найди авиабилеты из {from_city} в {to_city} на дату {date}",
    # С вариациями
    "Покажи самолёты из {from_city} в {to_city} {date}",
    "Когда летят из {from_city} в {to_city} {date}",
    "Рейсы из {from_city} в {to_city} {date}",
    "Самолёты из {from_city} в {to_city} {date}",
    "Что есть из {from_city} в {to_city} на {date}",
]

# Шаблоны для календаря - добавление (12 шаблонов)
CALENDAR_ADD_TEMPLATES = [
    # Базовые
    "Добавь встречу {description} на {date}",
    "Запиши в календарь {description} {date}",
    "Создай событие {description} на {date}",
    "Поставь напоминание {description} {date}",
    # Разговорные
    "Запланируй {description} на {date}",
    "Мне нужно {description} {date}, добавь в календарь",
    "Создай событие: {description}, дата {date}",
    "Напомни мне про {description} {date}",
    # Сложные
    "У меня будет {description} {date}, запиши пожалуйста",
    "Добавь в расписание {description} на {date}",
    "Поставь в календарь {description}, это будет {date}",
    "Зафиксируй событие {description} на дату {date}",
]

# Шаблоны для календаря - получение (12 шаблонов)
CALENDAR_GET_TEMPLATES = [
    # Базовые
    "Что у меня запланировано на {date}",
    "Покажи события на {date}",
    "Какие встречи у меня {date}",
    "Что в календаре на {date}",
    # Разговорные
    "Что у меня {date}",
    "Какие планы на {date}",
    "Покажи расписание на {date}",
    "Что запланировано {date}",
    # Сложные
    "Посмотри что у меня в календаре на {date}",
    "Какие события у меня намечены на {date}",
    "Проверь мои встречи на {date}",
    "Что у меня по расписанию {date}",
]

# Шаблоны для музыки (12 шаблонов)
MUSIC_TEMPLATES = [
    # Базовые
    "Найди песню {query}",
    "Поищи трек {query}",
    "Включи {query}",
    "Найди музыку {query}",
    # Разговорные
    "Хочу послушать {query}",
    "Поставь {query}",
    "Найди мне {query}",
    "Поиск песни {query}",
    # Сложные
    "Найди в Яндекс Музыке {query}",
    "Поищи трек под названием {query}",
    "Мне нужна песня {query}",
    "Найди композицию {query}",
]

# Шаблоны для заметок - создание (10 шаблонов)
NOTE_CREATE_TEMPLATES = [
    # Базовые
    "Создай заметку: {content}",
    "Запиши заметку {content}",
    "Сохрани заметку: {content}",
    "Добавь заметку {content}",
    # Разговорные
    "Запиши: {content}",
    "Сделай заметку {content}",
    "Сохрани: {content}",
    "Заметка: {content}",
    # Сложные
    "Мне нужно запомнить: {content}",
    "Создай новую заметку с текстом {content}",
]

# Шаблоны для заметок - поиск (8 шаблонов)
NOTE_SEARCH_TEMPLATES = [
    # Базовые
    "Найди заметку про {query}",
    "Поищи заметку {query}",
    "Покажи заметки про {query}",
    "Где заметка про {query}",
    # Разговорные
    "Найди мою заметку {query}",
    "Поиск заметки {query}",
    "Покажи заметку {query}",
    # Сложные
    "Найди все заметки связанные с {query}",
]

# Шаблоны без инструмента (15 шаблонов)
NO_TOOL_TEMPLATES = [
    # Приветствия
    "Привет",
    "Здравствуй",
    "Добрый день",
    "Как дела?",
    # Общие вопросы
    "Что ты умеешь?",
    "Помоги мне",
    "Кто ты?",
    "Расскажи о себе",
    # Не относящиеся к инструментам
    "Какая погода сегодня?",
    "Сколько будет 2 + 2?",
    "Расскажи анекдот",
    "Спасибо",
    "Пока",
    # Некорректные запросы
    "Найди поезд из Москвы в Питер",  # только самолёты
    "Покажи рейсы в Париж",  # только Россия
]

# Данные для генерации
CITIES = [
    "Москва", "Санкт-Петербург", "Казань", "Екатеринбург",
    "Новосибирск", "Сочи", "Владивосток", "Калининград",
    "Красноярск", "Иркутск", "Хабаровск", "Краснодар",
    "Самара", "Уфа", "Челябинск", "Омск",
    "Ростов-на-Дону", "Нижний Новгород", "Пермь", "Воронеж"
]

MEETING_DESCRIPTIONS = [
    "встреча с командой", "презентация проекта", "звонок с клиентом",
    "планерка", "обед с партнерами", "собеседование",
    "совещание", "тренинг", "вебинар", "конференция",
    "встреча с инвестором", "демо продукта", "ревью кода",
    "стендап", "ретроспектива", "планирование спринта"
]

MUSIC_QUERIES = [
    "Виктор Цой", "Кино - Группа крови", "Земфира",
    "ДДТ", "Сплин", "Би-2", "Мумий Тролль",
    "Nautilus Pompilius", "Агата Кристи", "Алиса",
    "Аквариум", "Ария", "Король и Шут",
    "Звери", "Сплин - Выхода нет", "Земфира - Искала"
]

NOTE_CONTENTS = [
    "купить молоко", "позвонить маме", "оплатить счета",
    "забрать посылку", "записаться к врачу", "сделать презентацию",
    "подготовить отчет", "купить подарок", "забронировать отель",
    "проверить почту", "обновить резюме", "написать статью"
]
# END:templates


# ANCHOR:dataset_generator
class DatasetGenerator:
    """Генератор тестового датасета с LLM перефразированием."""
    
    def __init__(
        self,
        output_dir: str = "data/datasets",
        seed: int = None,
        llm_provider = None,
        use_llm_rephrase: bool = False
    ):
        """
        Инициализация генератора.
        
        Args:
            output_dir: Директория для сохранения датасета.
            seed: Seed для воспроизводимости.
            llm_provider: Провайдер LLM для перефразирования.
            use_llm_rephrase: Использовать ли LLM для перефразирования.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset: List[Dict[str, Any]] = []
        
        if seed is not None:
            random.seed(seed)
        
        # Инициализируем перефразировщик
        self.use_llm_rephrase = use_llm_rephrase
        if use_llm_rephrase and llm_provider:
            self.rephraser = TextRephraser(
                llm_provider=llm_provider,
                cache_file="data/datasets/.rephrase_cache.json"
            )
        else:
            # Используем простой перефразировщик (правила)
            self.rephraser = SimpleRephraser()
        
        # Инициализируем конвертер дат
        self.date_converter = DateToTextConverter()
    
    def _get_random_date(self, days_ahead: int = 30) -> str:
        """Получить случайную дату в будущем."""
        days = random.randint(1, days_ahead)
        date = datetime.now() + timedelta(days=days)
        return date.strftime("%Y-%m-%d")
    
    def _get_date_description(self, date_str: str) -> str:
        """Получить описание даты (завтра, послезавтра, конкретная дата)."""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().date()
        delta = (date.date() - today).days
        
        if delta == 1:
            return "завтра"
        elif delta == 2:
            return "послезавтра"
        elif delta <= 7:
            # Используем день недели
            weekdays = ["понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"]
            return f"в {weekdays[date.weekday()]}"
        else:
            return date_str
    
    def _get_complexity(self, template: str) -> str:
        """Определить сложность шаблона."""
        if len(template.split()) <= 7:
            return "simple"
        elif len(template.split()) <= 12:
            return "medium"
        else:
            return "complex"
    
    def _create_tts_text(
        self,
        text: str,
        date_iso: str,
        date_desc: str
    ) -> str:
        """
        Создать текст для TTS с датами прописью.
        
        Args:
            text: Исходный текст.
            date_iso: Дата в формате ISO (YYYY-MM-DD).
            date_desc: Описание даты в тексте.
            
        Returns:
            Текст для TTS.
        """
        return self.date_converter.convert_text_for_tts(text, date_iso, date_desc)
    
    def _rephrase_sync(self, text: str) -> str:
        """Синхронная обёртка для перефразирования."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.rephraser.rephrase(text))
    
    def generate_flight_samples(self, count: int = 200) -> None:
        """Генерировать примеры для расписания рейсов."""
        for i in range(count):
            template = random.choice(FLIGHT_TEMPLATES)
            from_city = random.choice(CITIES)
            to_city = random.choice([c for c in CITIES if c != from_city])
            date = self._get_random_date()
            
            # Используем разные варианты дат
            if random.random() < 0.7:  # 70% - описательные даты
                date_desc = self._get_date_description(date)
            else:  # 30% - конкретные даты
                date_desc = date
            
            # Генерируем базовый текст
            base_text = template.format(
                from_city=from_city,
                to_city=to_city,
                date=date_desc
            )
            
            # Перефразируем
            text = self._rephrase_sync(base_text)
            
            # Создаём текст для TTS
            text_for_tts = self._create_tts_text(text, date, date_desc)
            
            self.dataset.append({
                "id": f"flight_{i+1:03d}",
                "text": text,
                "text_for_tts": text_for_tts,
                "tool": "flight_schedule",
                "params": {
                    "from_city": from_city,
                    "to_city": to_city,
                    "date": date
                },
                "metadata": {
                    "template_id": f"flight_template_{FLIGHT_TEMPLATES.index(template)+1:02d}",
                    "complexity": self._get_complexity(template),
                    "language": "ru",
                    "llm_rephrased": self.use_llm_rephrase
                }
            })
    
    def generate_calendar_samples(self, count: int = 200) -> None:
        """Генерировать примеры для календаря."""
        # Добавление событий
        for i in range(count // 2):
            template = random.choice(CALENDAR_ADD_TEMPLATES)
            description = random.choice(MEETING_DESCRIPTIONS)
            date = self._get_random_date()
            
            if random.random() < 0.7:
                date_desc = self._get_date_description(date)
            else:
                date_desc = date
            
            base_text = template.format(
                description=description,
                date=date_desc
            )
            
            # Перефразируем
            text = self._rephrase_sync(base_text)
            
            # Создаём текст для TTS
            text_for_tts = self._create_tts_text(text, date, date_desc)
            
            self.dataset.append({
                "id": f"calendar_add_{i+1:03d}",
                "text": text,
                "text_for_tts": text_for_tts,
                "tool": "add_calendar_event",
                "params": {
                    "date": date,
                    "description": description
                },
                "metadata": {
                    "template_id": f"calendar_add_template_{CALENDAR_ADD_TEMPLATES.index(template)+1:02d}",
                    "complexity": self._get_complexity(template),
                    "language": "ru",
                    "llm_rephrased": self.use_llm_rephrase
                }
            })
        
        # Получение событий
        for i in range(count // 2):
            template = random.choice(CALENDAR_GET_TEMPLATES)
            date = self._get_random_date()
            
            if random.random() < 0.7:
                date_desc = self._get_date_description(date)
            else:
                date_desc = date
            
            base_text = template.format(date=date_desc)
            
            # Перефразируем
            text = self._rephrase_sync(base_text)
            
            # Создаём текст для TTS
            text_for_tts = self._create_tts_text(text, date, date_desc)
            
            self.dataset.append({
                "id": f"calendar_get_{i+1:03d}",
                "text": text,
                "text_for_tts": text_for_tts,
                "tool": "get_calendar_events",
                "params": {
                    "date": date
                },
                "metadata": {
                    "template_id": f"calendar_get_template_{CALENDAR_GET_TEMPLATES.index(template)+1:02d}",
                    "complexity": self._get_complexity(template),
                    "language": "ru",
                    "llm_rephrased": self.use_llm_rephrase
                }
            })
    
    def generate_music_samples(self, count: int = 100) -> None:
        """Генерировать примеры для поиска музыки."""
        for i in range(count):
            template = random.choice(MUSIC_TEMPLATES)
            query = random.choice(MUSIC_QUERIES)
            
            base_text = template.format(query=query)
            
            # Перефразируем
            text = self._rephrase_sync(base_text)
            
            # Для музыки text_for_tts = text (нет дат)
            text_for_tts = text
            
            # Определяем тип поиска
            if " - " in query:
                search_type = "track"
            elif any(word in query.lower() for word in ["альбом", "album"]):
                search_type = "album"
            else:
                search_type = random.choice(["track", "artist"])
            
            self.dataset.append({
                "id": f"music_{i+1:03d}",
                "text": text,
                "text_for_tts": text_for_tts,
                "tool": "search_music",
                "params": {
                    "query": query,
                    "search_type": search_type
                },
                "metadata": {
                    "template_id": f"music_template_{MUSIC_TEMPLATES.index(template)+1:02d}",
                    "complexity": self._get_complexity(template),
                    "language": "ru",
                    "llm_rephrased": self.use_llm_rephrase
                }
            })
    
    def generate_notes_samples(self, count: int = 100) -> None:
        """Генерировать примеры для заметок."""
        # Создание заметок
        for i in range(count // 2):
            template = random.choice(NOTE_CREATE_TEMPLATES)
            content = random.choice(NOTE_CONTENTS)
            
            base_text = template.format(content=content)
            
            # Перефразируем
            text = self._rephrase_sync(base_text)
            
            # Для заметок text_for_tts = text (нет дат)
            text_for_tts = text
            
            self.dataset.append({
                "id": f"note_create_{i+1:03d}",
                "text": text,
                "text_for_tts": text_for_tts,
                "tool": "create_note",
                "params": {
                    "title": content.split()[0],
                    "content": content
                },
                "metadata": {
                    "template_id": f"note_create_template_{NOTE_CREATE_TEMPLATES.index(template)+1:02d}",
                    "complexity": self._get_complexity(template),
                    "language": "ru",
                    "llm_rephrased": self.use_llm_rephrase
                }
            })
        
        # Поиск заметок
        for i in range(count // 2):
            template = random.choice(NOTE_SEARCH_TEMPLATES)
            query = random.choice(NOTE_CONTENTS).split()[0]
            
            base_text = template.format(query=query)
            
            # Перефразируем
            text = self._rephrase_sync(base_text)
            
            # Для заметок text_for_tts = text (нет дат)
            text_for_tts = text
            
            self.dataset.append({
                "id": f"note_search_{i+1:03d}",
                "text": text,
                "text_for_tts": text_for_tts,
                "tool": "search_notes",
                "params": {
                    "query": query
                },
                "metadata": {
                    "template_id": f"note_search_template_{NOTE_SEARCH_TEMPLATES.index(template)+1:02d}",
                    "complexity": self._get_complexity(template),
                    "language": "ru",
                    "llm_rephrased": self.use_llm_rephrase
                }
            })
    
    def generate_no_tool_samples(self, count: int = 100) -> None:
        """Генерировать примеры без инструмента."""
        for i in range(count):
            text = random.choice(NO_TOOL_TEMPLATES)
            
            # Для примеров без инструмента text_for_tts = text
            text_for_tts = text
            
            # Определяем причину
            if any(word in text.lower() for word in ["поезд", "автобус", "электричка"]):
                reason = "Поддерживаются только авиарейсы"
            elif any(word in text.lower() for word in ["париж", "лондон", "берлин"]):
                reason = "Поддерживаются только рейсы по России"
            else:
                reason = "Запрос не требует вызова инструмента"
            
            self.dataset.append({
                "id": f"no_tool_{i+1:03d}",
                "text": text,
                "text_for_tts": text_for_tts,
                "tool": "no_tool_available",
                "params": {
                    "reason": reason,
                    "user_message": "Извините, я не могу помочь с этим запросом"
                },
                "metadata": {
                    "template_id": f"no_tool_template_{NO_TOOL_TEMPLATES.index(text)+1:02d}",
                    "complexity": "simple",
                    "language": "ru",
                    "llm_rephrased": False
                }
            })
    
    def generate_full_dataset(
        self,
        flights: int = 200,
        calendar: int = 200,
        music: int = 100,
        notes: int = 100,
        no_tool: int = 100
    ) -> None:
        """
        Генерировать полный датасет.
        
        Args:
            flights: Количество примеров для рейсов.
            calendar: Количество примеров для календаря.
            music: Количество примеров для музыки.
            notes: Количество примеров для заметок.
            no_tool: Количество примеров без инструмента.
        """
        print("Генерация расширенного датасета...")
        if self.use_llm_rephrase:
            print("⚠️  LLM перефразирование включено (может занять время)")
        else:
            print("✓ Используется простой перефразировщик (правила)")
        print()
        
        self.generate_flight_samples(flights)
        print(f"✓ Сгенерировано {flights} примеров для рейсов")
        
        self.generate_calendar_samples(calendar)
        print(f"✓ Сгенерировано {calendar} примеров для календаря")
        
        self.generate_music_samples(music)
        print(f"✓ Сгенерировано {music} примеров для музыки")
        
        self.generate_notes_samples(notes)
        print(f"✓ Сгенерировано {notes} примеров для заметок")
        
        self.generate_no_tool_samples(no_tool)
        print(f"✓ Сгенерировано {no_tool} примеров без инструмента")
        
        # Перемешиваем датасет
        random.shuffle(self.dataset)
        
        print(f"\nВсего примеров: {len(self.dataset)}")
    
    def save_dataset(self, filename: str = "evaluation_dataset.json") -> None:
        """
        Сохранить датасет в JSON файл.
        
        Args:
            filename: Имя файла.
        """
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Датасет сохранен в {output_path}")
    
    def print_statistics(self) -> None:
        """Вывести статистику датасета."""
        tool_counts = {}
        complexity_counts = {}
        
        for item in self.dataset:
            tool = item['tool']
            complexity = item['metadata']['complexity']
            
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        print("\n" + "="*60)
        print("СТАТИСТИКА ДАТАСЕТА")
        print("="*60)
        
        print("\nРаспределение по инструментам:")
        for tool, count in sorted(tool_counts.items()):
            percentage = (count / len(self.dataset)) * 100
            print(f"  {tool:30s}: {count:4d} ({percentage:5.1f}%)")
        
        print("\nРаспределение по сложности:")
        for complexity, count in sorted(complexity_counts.items()):
            percentage = (count / len(self.dataset)) * 100
            print(f"  {complexity:10s}: {count:4d} ({percentage:5.1f}%)")
        
        print(f"\nВсего шаблонов:")
        print(f"  Рейсы:    {len(FLIGHT_TEMPLATES)}")
        print(f"  Календарь (добавление): {len(CALENDAR_ADD_TEMPLATES)}")
        print(f"  Календарь (получение):  {len(CALENDAR_GET_TEMPLATES)}")
        print(f"  Музыка:   {len(MUSIC_TEMPLATES)}")
        print(f"  Заметки (создание):     {len(NOTE_CREATE_TEMPLATES)}")
        print(f"  Заметки (поиск):        {len(NOTE_SEARCH_TEMPLATES)}")
        print(f"  Без инструмента:        {len(NO_TOOL_TEMPLATES)}")
        total_templates = (
            len(FLIGHT_TEMPLATES) + len(CALENDAR_ADD_TEMPLATES) + 
            len(CALENDAR_GET_TEMPLATES) + len(MUSIC_TEMPLATES) +
            len(NOTE_CREATE_TEMPLATES) + len(NOTE_SEARCH_TEMPLATES) +
            len(NO_TOOL_TEMPLATES)
        )
        print(f"  ИТОГО:    {total_templates}")
# END:dataset_generator


# ANCHOR:main
def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description="Генерация расширенного датасета")
    parser.add_argument(
        "--output",
        type=str,
        default="data/datasets",
        help="Директория для сохранения датасета"
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="evaluation_dataset.json",
        help="Имя файла датасета"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=600,
        help="Общее количество примеров (будет распределено по инструментам)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed для воспроизводимости"
    )
    parser.add_argument(
        "--use-llm-rephrase",
        action="store_true",
        help="Использовать LLM для перефразирования (требует настройки LLM провайдера)"
    )
    
    args = parser.parse_args()
    
    # Распределяем примеры по инструментам
    total = args.count
    flights = int(total * 0.30)      # 30%
    calendar = int(total * 0.30)     # 30%
    music = int(total * 0.15)        # 15%
    notes = int(total * 0.14)        # 14%
    no_tool = total - flights - calendar - music - notes  # остаток (~11%)
    
    print(f"Генерация {total} примеров:")
    print(f"  Рейсы:    {flights}")
    print(f"  Календарь: {calendar}")
    print(f"  Музыка:   {music}")
    print(f"  Заметки:  {notes}")
    print(f"  Без инструмента: {no_tool}")
    print()
    
    # Создаем генератор
    generator = DatasetGenerator(
        output_dir=args.output,
        seed=args.seed,
        llm_provider=None,  # TODO: добавить поддержку LLM провайдера
        use_llm_rephrase=args.use_llm_rephrase
    )
    
    # Генерируем датасет
    generator.generate_full_dataset(
        flights=flights,
        calendar=calendar,
        music=music,
        notes=notes,
        no_tool=no_tool
    )
    
    # Выводим статистику
    generator.print_statistics()
    
    # Сохраняем
    generator.save_dataset(args.filename)
    
    print("\nГотово! Датасет создан.")


if __name__ == "__main__":
    main()
# END:main
