"""
LLM провайдер на основе OpenAI клиента.
Работает с vLLM, OpenRouter и другими OpenAI-совместимыми API.
"""

from typing import List, Dict, Any, Type
from pydantic import BaseModel
from openai import AsyncOpenAI

from src.llm.provider import LLMProvider
from src.core.config import LLMConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:openai_llm_provider
class OpenAILLMProvider(LLMProvider):
    """
    LLM провайдер на основе OpenAI клиента.
    Поддерживает vLLM, OpenRouter и другие OpenAI-совместимые API.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Инициализация провайдера.
        
        Args:
            config: Конфигурация LLM.
        """
        self.config = config
        
        # Создаем асинхронный клиент
        self.async_client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key
        )
        
        logger.info(f"OpenAI LLM Provider initialized with base_url: {config.base_url}, model: {config.model}")

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
        """

        logger.info(f"Generating structured output with schema: {schema.__name__}")
        
        try:
            completion = await self.async_client.beta.chat.completions.parse(
                model=self.config.model,
                messages=messages,
                response_format=schema,
                temperature=0,
                top_p=1,
                extra_body={
                    'chat_template_kwargs': {"enable_thinking": False},
                }
            )

            result = completion.choices[0].message.parsed
            logger.info(f"Successfully generated structured output")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating structured output: {e}", exc_info=True)
            raise
# END:openai_llm_provider
