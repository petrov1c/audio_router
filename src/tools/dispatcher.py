"""
Диспетчер инструментов.
Маршрутизация вызовов к соответствующим инструментам.
"""

from typing import Dict, Any, Optional

from src.tools.base import BaseTool
from src.tools.registry import ToolRegistry, get_registry
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:tool_dispatcher
class ToolDispatcher:
    """Диспетчер для маршрутизации вызовов инструментов."""
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        """
        Инициализация диспетчера.
        
        Args:
            registry: Реестр инструментов. Если None, используется глобальный.
        """
        self.registry = registry or get_registry()
        logger.info("Tool dispatcher initialized")
    
    async def dispatch(self, tool_call: BaseTool) -> Dict[str, Any]:
        """
        Выполнить вызов инструмента.
        
        Args:
            tool_call: Pydantic модель с параметрами вызова.
            
        Returns:
            Результат выполнения инструмента.
        """
        tool_name = tool_call.tool
        
        logger.info(f"Dispatching tool call: {tool_name}")
        
        # Получаем инструмент из реестра
        tool = self.registry.get(tool_name)
        
        if tool is None:
            error_msg = f"Tool '{tool_name}' not found in registry"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "tool": tool_name,
                "available_tools": self.registry.get_names()
            }
        
        # Выполняем инструмент
        result = await tool.safe_execute(tool_call)

        return result

    def get_available_tools(self) -> Dict[str, str]:
        """
        Получить список доступных инструментов с описаниями.
        
        Returns:
            Словарь {имя: описание}.
        """
        return self.registry.get_descriptions()
# END:tool_dispatcher
