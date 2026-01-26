"""
Модуль инструментов для голосового помощника.
"""

from src.tools.base import Tool, BaseTool
from src.tools.registry import ToolRegistry, get_registry
from src.tools.dispatcher import ToolDispatcher
from src.tools.flights import FlightsTool
from src.tools.calendar import AddCalendarEventToolImpl, GetCalendarEventsToolImpl
from src.tools.music import MusicTool
from src.tools.notes import CreateNoteToolImpl, SearchNotesToolImpl
from src.tools.special import NoToolAvailableTool, TaskCompletionTool
from src.core.config import get_config


def register_all_tools(registry: ToolRegistry = None) -> ToolRegistry:
    """
    Зарегистрировать все доступные инструменты.
    
    Args:
        registry: Реестр инструментов. Если None, используется глобальный.
        
    Returns:
        Реестр с зарегистрированными инструментами.
    """
    if registry is None:
        registry = get_registry()
    
    config = get_config()
    
    # Регистрируем инструменты если они включены
    # ToDo Вынести инструменты в config.
    if config.tools.flights.enabled:
        registry.register(FlightsTool(config.tools.flights))
    
    if config.tools.calendar.enabled:
        registry.register(AddCalendarEventToolImpl(config.tools.calendar))
        registry.register(GetCalendarEventsToolImpl(config.tools.calendar))
    
    if config.tools.music.enabled:
        registry.register(MusicTool(config.tools.music))
    
    if config.tools.notes.enabled:
        registry.register(CreateNoteToolImpl(config.tools.notes))
        registry.register(SearchNotesToolImpl(config.tools.notes))
    
    # Специальные инструменты всегда доступны
    registry.register(NoToolAvailableTool())
    registry.register(TaskCompletionTool())
    
    return registry


__all__ = [
    "Tool",
    "BaseTool",
    "ToolRegistry",
    "get_registry",
    "ToolDispatcher",
    "register_all_tools",
]
