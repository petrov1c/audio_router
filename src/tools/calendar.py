"""
Инструмент для управления календарем.
Использует CSV файл для хранения событий.
Поддерживает относительные даты и периоды.
"""

from typing import Dict, Any, Type, List, Optional
import csv
from datetime import datetime

from src.tools.base import Tool, BaseTool
from src.tools.schemas import AddCalendarEventTool, GetCalendarEventsTool
from src.tools.date_parser import DateParser
from src.core.config import CalendarToolConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:calendar_tool
class CalendarTool(Tool):
    """Базовый класс для инструментов календаря."""
    
    def __init__(self, config: CalendarToolConfig):
        """
        Инициализация инструмента.
        
        Args:
            config: Конфигурация инструмента.
        """
        self.config = config
        self.file_path = config.full_path
        
        # Инициализируем парсер дат
        self.date_parser = DateParser()
        
        # Создаем файл если не существует
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Создать файл календаря если не существует."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'description'])
            logger.info(f"Created calendar file: {self.file_path}")
    
    def _read_events(self) -> List[Dict[str, str]]:
        """
        Прочитать все события из календаря.
        
        Returns:
            Список событий.
        """
        events = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(row)
        return events
    
    def _write_event(self, date: str, description: str):
        """
        Добавить событие в календарь.
        
        Args:
            date: Дата события.
            description: Описание события.
        """
        with open(self.file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([date, description])
# END:calendar_tool


# ANCHOR:add_calendar_event_tool
class AddCalendarEventToolImpl(CalendarTool):
    """Инструмент для добавления события в календарь."""
    
    @property
    def name(self) -> str:
        return "add_calendar_event"
    
    @property
    def description(self) -> str:
        return "Добавить событие в календарь. Сохраняет дату и описание события."
    
    def get_schema(self) -> Type[BaseTool]:
        return AddCalendarEventTool
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        """
        Добавить событие в календарь.
        
        Args:
            params: Параметры события (AddCalendarEventTool).
            
        Returns:
            Результат добавления события.
        """
        assert isinstance(params, AddCalendarEventTool)
        
        logger.info(f"Adding calendar event: {params.date} - {params.description}")
        
        try:
            # Парсим дату
            try:
                parsed = self.date_parser.parse(params.date)
            except ValueError as e:
                return {
                    "success": False,
                    "error": "date_parse_error",
                    "message": f"Не удалось распознать дату: {params.date}. {str(e)}"
                }
            
            # Проверяем что это не период
            if parsed.is_period:
                return {
                    "success": False,
                    "error": "period_not_allowed",
                    "message": (
                        f"Для добавления события укажите конкретную дату, а не период. "
                        f"Вы указали: '{params.date}' (период с {parsed.date_from} по {parsed.date_to})"
                    )
                }
            
            # Валидируем распарсенную дату
            try:
                datetime.strptime(parsed.date, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "error": "invalid_date",
                    "message": f"Некорректная дата: {parsed.date}"
                }
            
            # Добавляем событие
            self._write_event(parsed.date, params.description)
            
            return {
                "success": True,
                "date": parsed.date,
                "original_date": parsed.original_text,
                "description": params.description,
                "message": f"Событие добавлено на {parsed.date}: {params.description}"
            }
            
        except Exception as e:
            logger.error(f"Error adding calendar event: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Произошла ошибка при добавлении события в календарь"
            }
# END:add_calendar_event_tool


# ANCHOR:get_calendar_events_tool
class GetCalendarEventsToolImpl(CalendarTool):
    """Инструмент для получения событий из календаря."""
    
    @property
    def name(self) -> str:
        return "get_calendar_events"
    
    @property
    def description(self) -> str:
        return (
            "Получить события из календаря. Можно фильтровать по дате или периоду."
        )
    
    def get_schema(self) -> Type[BaseTool]:
        return GetCalendarEventsTool
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        """
        Получить события из календаря.
        
        Args:
            params: Параметры фильтрации (GetCalendarEventsTool).
            
        Returns:
            Список событий.
        """
        assert isinstance(params, GetCalendarEventsTool)
        
        logger.info(
            f"Getting calendar events: date={params.date}, "
            f"from={params.date_from}, to={params.date_to}"
        )
        
        try:
            # Сохраняем оригинальные значения для сообщения
            original_date = params.date
            original_date_from = params.date_from
            original_date_to = params.date_to
            
            # Парсим дату если указана
            if params.date:
                try:
                    parsed = self.date_parser.parse(params.date)
                    
                    # Если это период, используем date_from и date_to
                    if parsed.is_period:
                        params.date = None
                        params.date_from = parsed.date_from
                        params.date_to = parsed.date_to
                    else:
                        params.date = parsed.date
                except ValueError as e:
                    return {
                        "success": False,
                        "error": "date_parse_error",
                        "message": f"Не удалось распознать дату: {params.date}. {str(e)}"
                    }
            
            # Парсим date_from если указан
            if params.date_from:
                try:
                    parsed_from = self.date_parser.parse(params.date_from)
                    if parsed_from.is_period:
                        # Если указан период, берем начало
                        params.date_from = parsed_from.date_from
                    else:
                        params.date_from = parsed_from.date
                except ValueError as e:
                    return {
                        "success": False,
                        "error": "date_from_parse_error",
                        "message": f"Не удалось распознать дату начала: {params.date_from}. {str(e)}"
                    }
            
            # Парсим date_to если указан
            if params.date_to:
                try:
                    parsed_to = self.date_parser.parse(params.date_to)
                    if parsed_to.is_period:
                        # Если указан период, берем конец
                        params.date_to = parsed_to.date_to
                    else:
                        params.date_to = parsed_to.date
                except ValueError as e:
                    return {
                        "success": False,
                        "error": "date_to_parse_error",
                        "message": f"Не удалось распознать дату окончания: {params.date_to}. {str(e)}"
                    }
            
            # Читаем все события
            all_events = self._read_events()
            
            # Фильтруем события
            filtered_events = []
            
            for event in all_events:
                event_date = event['date']
                
                # Фильтр по конкретной дате
                if params.date:
                    if event_date == params.date:
                        filtered_events.append(event)
                # Фильтр по периоду
                elif params.date_from and params.date_to:
                    if params.date_from <= event_date <= params.date_to:
                        filtered_events.append(event)
                # Фильтр только по началу периода
                elif params.date_from:
                    if event_date >= params.date_from:
                        filtered_events.append(event)
                # Фильтр только по концу периода
                elif params.date_to:
                    if event_date <= params.date_to:
                        filtered_events.append(event)
                # Без фильтров - все события
                else:
                    filtered_events.append(event)
            
            # Сортируем по дате
            filtered_events.sort(key=lambda x: x['date'])
            
            return {
                "success": True,
                "count": len(filtered_events),
                "events": filtered_events,
                "original_date": original_date,
                "parsed_date": params.date,
                "parsed_date_from": params.date_from,
                "parsed_date_to": params.date_to,
                "message": self._format_message(
                    filtered_events,
                    params,
                    original_date or original_date_from or original_date_to
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar events: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Произошла ошибка при получении событий из календаря"
            }
    
    def _format_message(
        self,
        events: List[Dict],
        params: GetCalendarEventsTool,
        original_text: Optional[str] = None
    ) -> str:
        """
        Форматировать сообщение с событиями.
        
        Args:
            events: Список событий.
            params: Параметры фильтрации.
            original_text: Оригинальный текст запроса (для более понятного сообщения).
            
        Returns:
            Отформатированное сообщение.
        """
        if not events:
            if params.date:
                date_text = original_text if original_text else params.date
                return f"На {date_text} нет запланированных событий"
            elif params.date_from and params.date_to:
                if original_text:
                    return f"В период '{original_text}' нет запланированных событий"
                else:
                    return f"В период с {params.date_from} по {params.date_to} нет запланированных событий"
            else:
                return "В календаре нет событий"
        
        # Формируем заголовок
        if params.date:
            date_text = original_text if original_text else params.date
            message_parts = [f"Найдено событий на {date_text}: {len(events)}\n"]
        elif params.date_from and params.date_to:
            if original_text:
                message_parts = [f"Найдено событий в период '{original_text}': {len(events)}\n"]
            else:
                message_parts = [f"Найдено событий с {params.date_from} по {params.date_to}: {len(events)}\n"]
        else:
            message_parts = [f"Найдено событий: {len(events)}\n"]
        
        for event in events:
            message_parts.append(f"• {event['date']}: {event['description']}")
        
        return "\n".join(message_parts)
# END:get_calendar_events_tool
