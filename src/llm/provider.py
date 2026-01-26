"""
Базовый интерфейс LLM провайдера.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, Optional
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
    
    @abstractmethod
    async def generate_text(
        self,
        messages: List[Dict[str, Any]],
    ) -> str:
        """
        Генерация текстового ответа.
        
        Args:
            messages: Список сообщений в формате OpenAI.

        Returns:
            Сгенерированный текст.
            
        Raises:
            Exception: При ошибке генерации.
        """
        pass
    
    @abstractmethod
    async def process_audio(
        self,
        audio: bytes,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Обработка аудио запроса.
        
        Args:
            audio: Аудио данные в байтах.
            messages: Опциональный контекст диалога.
            
        Returns:
            Распознанный текст или ответ модели.
            
        Raises:
            Exception: При ошибке обработки.
        """
        pass
# END:llm_provider_interface
