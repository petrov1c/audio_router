"""
Базовые классы для инструментов.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type
from pydantic import BaseModel

from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:base_tool_schema
class BaseTool(BaseModel):
    """Базовая Pydantic схема для всех инструментов."""
    tool: str
    
    model_config = {"extra": "forbid"}  # Запрещаем дополнительные поля
# END:base_tool_schema


# ANCHOR:tool_interface
class Tool(ABC):
    """Абстрактный базовый класс для всех инструментов."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Имя инструмента (уникальный идентификатор).
        
        Returns:
            Имя инструмента.
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Описание инструмента для LLM.
        
        Returns:
            Описание инструмента.
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Type[BaseTool]:
        """
        Получить Pydantic схему инструмента.
        
        Returns:
            Класс Pydantic схемы.
        """
        pass
    
    @abstractmethod
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        """
        Выполнить инструмент с заданными параметрами.
        
        Args:
            params: Параметры вызова инструмента (Pydantic модель).
            
        Returns:
            Результат выполнения инструмента.
            
        Raises:
            Exception: При ошибке выполнения.
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> BaseTool:
        """
        Валидировать параметры инструмента.
        
        Args:
            params: Словарь с параметрами.
            
        Returns:
            Валидированная Pydantic модель.
            
        Raises:
            ValidationError: При ошибке валидации.
        """
        schema = self.get_schema()
        return schema(**params)
    
    async def safe_execute(self, params: BaseTool) -> Dict[str, Any]:
        """
        Безопасное выполнение инструмента с обработкой ошибок.
        
        Args:
            params: Параметры вызова инструмента.
            
        Returns:
            Результат выполнения или информация об ошибке.
        """
        try:
            logger.info(f"Executing tool: {self.name} with params: {params}")
            result = await self.execute(params)
            logger.info(f"Tool {self.name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tool": self.name
            }
# END:tool_interface
