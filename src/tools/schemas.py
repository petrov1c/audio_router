"""
Pydantic схемы для всех инструментов.
"""

from typing import Optional
from typing_extensions import Literal
from pydantic import Field

from src.tools.base import BaseTool


# ANCHOR:flight_schedule_schema
class FlightScheduleTool(BaseTool):
    """Схема инструмента поиска расписания рейсов."""
    tool: Literal["flight_schedule"]
    from_station: str = Field(description="Код или название станции отправления")
    to_station: str = Field(description="Код или название станции прибытия")
    date: str = Field(description="Дата в формате YYYY-MM-DD")
    transport_type: Optional[str] = Field(
        default="plane",
        description="Тип транспорта: plane, train, bus, suburban"
    )
# END:flight_schedule_schema


# ANCHOR:calendar_schemas
class AddCalendarEventTool(BaseTool):
    """Схема инструмента добавления события в календарь."""
    tool: Literal["add_calendar_event"]
    date: str = Field(description="Дата события в формате YYYY-MM-DD")
    description: str = Field(description="Описание события")


class GetCalendarEventsTool(BaseTool):
    """Схема инструмента получения событий из календаря."""
    tool: Literal["get_calendar_events"]
    date: Optional[str] = Field(
        default=None,
        description="Дата для фильтрации в формате YYYY-MM-DD. Если None, возвращает все события"
    )
    date_from: Optional[str] = Field(
        default=None,
        description="Начало периода в формате YYYY-MM-DD"
    )
    date_to: Optional[str] = Field(
        default=None,
        description="Конец периода в формате YYYY-MM-DD"
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
