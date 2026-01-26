"""
Специальные инструменты для управления диалогом.
"""

from typing import Dict, Any, Type

from src.tools.base import Tool, BaseTool
from src.tools.schemas import NoToolAvailable, TaskCompletion
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:no_tool_available
class NoToolAvailableTool(Tool):
    """Инструмент для случая, когда нет подходящего инструмента."""
    
    def __init__(self):
        """Инициализация инструмента."""
        pass
    
    @property
    def name(self) -> str:
        return "no_tool_available"
    
    @property
    def description(self) -> str:
        return "Использовать когда запрос пользователя не может быть выполнен доступными инструментами."
    
    def get_schema(self) -> Type[BaseTool]:
        return NoToolAvailable
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        assert isinstance(params, NoToolAvailable)
        logger.info(f"No tool available: {params.reason}")
        return {
            "success": True,
            "message": params.user_message,
            "reason": params.reason
        }
# END:no_tool_available


# ANCHOR:task_completion
class TaskCompletionTool(Tool):
    """Инструмент для завершения задачи."""
    
    def __init__(self):
        """Инициализация инструмента."""
        pass
    
    @property
    def name(self) -> str:
        return "task_completion"
    
    @property
    def description(self) -> str:
        return "Использовать для завершения задачи и отчета о результате."
    
    def get_schema(self) -> Type[BaseTool]:
        return TaskCompletion
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        assert isinstance(params, TaskCompletion)
        logger.info(f"Task completed: {params.status}")
        return {
            "success": True,
            "status": params.status,
            "result": params.result,
            "message": params.result
        }
# END:task_completion
