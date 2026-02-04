"""
Базовый интерфейс LLM провайдера.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type
from pydantic import BaseModel

from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:llm_provider_interface
class LLMProvider(ABC):
    """Абстрактный базовый класс для LLM провайдеров."""
    
    @abstractmethod
    async def generate_structured(
        self,
        messages: List[Dict[str, Any]],
        schema: Type[BaseModel],
    ) -> BaseModel:
        """
        Генерация структурированного ответа согласно Pydantic схеме.
        
        Args:
            messages: Список сообщений в формате OpenAI.
            schema: Pydantic схема для структурированного вывода.

        Returns:
            Экземпляр Pydantic модели с результатом.
            
        Raises:
            Exception: При ошибке генерации.
        """
        pass

# END:llm_provider_interface
