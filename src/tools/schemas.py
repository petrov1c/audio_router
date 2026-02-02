"""
Pydantic схемы для всех инструментов.
"""

from typing import Optional
from typing_extensions import Literal
from pydantic import Field

from src.tools.base import BaseTool


# ANCHOR:flight_schedule_schema
class FlightScheduleTool(BaseTool):
    """Схема инструмента поиска расписания авиарейсов по России."""
    tool: Literal["flight_schedule"]
    from_city: str = Field(
        description="Город или аэропорт отправления (например: Москва, Санкт-Петербург, Шереметьево)"
    )
    to_city: str = Field(
        description="Город или аэропорт прибытия (например: Сочи, Владивосток, Пулково)"
    )
    date: str = Field(
        description="Дата вылета в формате YYYY-MM-DD"
    )
# END:flight_schedule_schema


# ANCHOR:calendar_schemas
class AddCalendarEventTool(BaseTool):
    """Схема инструмента добавления события в календарь."""
    tool: Literal["add_calendar_event"]
    date: str = Field(
        description=(
            "Дата события. Поддерживаются форматы:\n"
            "- Абсолютные: YYYY-MM-DD, DD.MM.YYYY, 15 февраля\n"
            "- Относительные: завтра, послезавтра, вчера\n"
            "- Дни недели: понедельник, следующий вторник, в пятницу\n"
            "- Смещения: через 3 дня, через неделю, через месяц\n"
            "Примеры: '2026-02-15', 'завтра', 'следующий понедельник', 'через 3 дня'"
        )
    )
    description: str = Field(description="Описание события")


class GetCalendarEventsTool(BaseTool):
    """Схема инструмента получения событий из календаря."""
    tool: Literal["get_calendar_events"]
    date: Optional[str] = Field(
        default=None,
        description=(
            "Дата или период для фильтрации. Поддерживаются:\n"
            "- Конкретная дата: 'завтра', '2026-02-15', 'понедельник', 'через 3 дня'\n"
            "- Период: 'следующая неделя', 'этот месяц', 'через 2 недели'\n"
            "Если указан период, автоматически вычисляются date_from и date_to.\n"
            "Если None, возвращает все события"
        )
    )
    date_from: Optional[str] = Field(
        default=None,
        description=(
            "Начало периода. Поддерживает те же форматы что и date.\n"
            "Автоматически вычисляется если date содержит период"
        )
    )
    date_to: Optional[str] = Field(
        default=None,
        description=(
            "Конец периода. Поддерживает те же форматы что и date.\n"
            "Автоматически вычисляется если date содержит период"
        )
    )
# END:calendar_schemas


# ANCHOR:music_schema
class SearchMusicTool(BaseTool):
    """Схема инструмента поиска музыки."""
    tool: Literal["search_music"]
    query: str = Field(description="Поисковый запрос: название трека, исполнитель, альбом")
    search_type: Optional[str] = Field(
        default="track",
        description="Тип поиска: track (трек), artist (исполнитель), album (альбом)"
    )
    limit: Optional[int] = Field(
        default=10,
        description="Максимальное количество результатов"
    )
# END:music_schema


# ANCHOR:notes_schema
class CreateNoteTool(BaseTool):
    """Схема инструмента создания заметки."""
    tool: Literal["create_note"]
    title: str = Field(description="Заголовок заметки")
    content: str = Field(description="Содержимое заметки")


class SearchNotesTool(BaseTool):
    """Схема инструмента поиска заметок."""
    tool: Literal["search_notes"]
    query: str = Field(description="Поисковый запрос по заголовку или содержимому")
# END:notes_schema


# ANCHOR:special_tools_schemas
class NoToolAvailable(BaseTool):
    """Схема для случая, когда нет подходящего инструмента."""
    tool: Literal["no_tool_available"]
    reason: str = Field(description="Причина отказа (для логирования)")
    user_message: str = Field(description="Сообщение пользователю о том, что запрос не может быть выполнен")


class TaskCompletion(BaseTool):
    """Схема завершения задачи."""
    tool: Literal["task_completion"]
    result: str = Field(description="Результат выполнения задачи")
    status: Literal["success", "failed"] = Field(description="Статус выполнения")
# END:special_tools_schemas
