"""
LLM провайдер на основе OpenAI клиента.
Работает с vLLM, OpenRouter и другими OpenAI-совместимыми API.
"""

from typing import List, Dict, Any, Type, Optional
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI

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
        
        # Создаем синхронный и асинхронный клиенты
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key
        )
        
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
        """

        logger.info(f"Generating text response")
        
        try:
            completion = await self.async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=0,
                top_p=1,
                extra_body={
                    'chat_template_kwargs': {"enable_thinking": False},
                }
            )
            
            result = completion.choices[0].message.content
            logger.info(f"Successfully generated text response")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            raise
    
    async def process_audio(
        self,
        audio: bytes,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Обработка аудио запроса через QWEN2.5-Omni.
        Модель напрямую обрабатывает аудио без промежуточного ASR.
        
        Args:
            audio: Аудио данные в байтах (WAV формат).
            messages: Опциональный контекст диалога.
            
        Returns:
            Понимание запроса в текстовом виде.
        """
        import base64
        
        logger.info(f"Processing audio input: {len(audio)} bytes")
        
        try:
            # Кодируем аудио в base64
            audio_b64 = base64.b64encode(audio).decode('utf-8')
            
            # Формируем сообщение с аудио для QWEN2.5-Omni
            audio_message = {
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "audio": audio_b64
                    }
                ]
            }
            
            # Если есть контекст диалога, добавляем его
            if messages:
                full_messages = messages + [audio_message]
            else:
                full_messages = [audio_message]
            
            # Отправляем в модель
            completion = await self.async_client.chat.completions.create(
                model=self.config.model,
                messages=full_messages,
                temperature=0,
                top_p=1,
                extra_body={
                    'chat_template_kwargs': {"enable_thinking": False},
                }
            )
            
            # Извлекаем ответ
            response = completion.choices[0].message.content
            
            logger.info(f"Audio processed successfully, response: {response[:100]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            raise
# END:openai_llm_provider
