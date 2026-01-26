"""
Реестр инструментов.
Управление регистрацией и получением инструментов.
"""

from typing import Dict, Optional, List, Type
from pydantic import BaseModel

from src.tools.base import Tool, BaseTool
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:tool_registry
class ToolRegistry:
    """Реестр всех доступных инструментов."""
    
    def __init__(self):
        """Инициализация реестра."""
        self._tools: Dict[str, Tool] = {}
        logger.info("Tool registry initialized")
    
    def register(self, tool: Tool) -> None:
        """
        Зарегистрировать инструмент.
        
        Args:
            tool: Экземпляр инструмента.
            
        Raises:
            ValueError: Если инструмент с таким именем уже зарегистрирован.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, tool_name: str) -> None:
        """
        Удалить инструмент из реестра.
        
        Args:
            tool_name: Имя инструмента.
            
        Raises:
            KeyError: Если инструмент не найден.
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not found in registry")
        
        del self._tools[tool_name]
        logger.info(f"Unregistered tool: {tool_name}")
    
    def get(self, tool_name: str) -> Optional[Tool]:
        """
        Получить инструмент по имени.
        
        Args:
            tool_name: Имя инструмента.
            
        Returns:
            Экземпляр инструмента или None, если не найден.
        """
        return self._tools.get(tool_name)
    
    def get_all(self) -> Dict[str, Tool]:
        """
        Получить все зарегистрированные инструменты.
        
        Returns:
            Словарь инструментов {имя: экземпляр}.
        """
        return self._tools.copy()
    
    def get_names(self) -> List[str]:
        """
        Получить имена всех зарегистрированных инструментов.
        
        Returns:
            Список имен инструментов.
        """
        return list(self._tools.keys())
    
    def get_schemas(self) -> Dict[str, Type[BaseTool]]:
        """
        Получить схемы всех инструментов.
        
        Returns:
            Словарь {имя: схема Pydantic}.
        """
        return {name: tool.get_schema() for name, tool in self._tools.items()}
    
    def get_descriptions(self) -> Dict[str, str]:
        """
        Получить описания всех инструментов.
        
        Returns:
            Словарь {имя: описание}.
        """
        return {name: tool.description for name, tool in self._tools.items()}
    
    def is_registered(self, tool_name: str) -> bool:
        """
        Проверить, зарегистрирован ли инструмент.
        
        Args:
            tool_name: Имя инструмента.
            
        Returns:
            True, если инструмент зарегистрирован.
        """
        return tool_name in self._tools
    
    def clear(self) -> None:
        """Очистить реестр (удалить все инструменты)."""
        self._tools.clear()
        logger.info("Tool registry cleared")
    
    def __len__(self) -> int:
        """Получить количество зарегистрированных инструментов."""
        return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        """Проверить наличие инструмента в реестре."""
        return tool_name in self._tools
# END:tool_registry


# ANCHOR:registry_singleton
_registry_instance: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    Получить глобальный экземпляр реестра инструментов (singleton).
    
    Returns:
        Экземпляр реестра инструментов.
    """
    global _registry_instance
    
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    
    return _registry_instance


def reset_registry() -> None:
    """Сбросить глобальный экземпляр реестра (для тестирования)."""
    global _registry_instance
    _registry_instance = None
# END:registry_singleton
