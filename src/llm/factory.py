"""
Фабрика для создания LLM провайдеров.
"""

from src.llm.provider import LLMProvider
from src.llm.openai_provider import OpenAILLMProvider
from src.llm.local_provider import LocalLLMProvider
from src.core.config import LLMConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:llm_provider_factory
def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Создать LLM провайдер на основе конфигурации.
    
    Args:
        config: Конфигурация LLM.
        
    Returns:
        Экземпляр LLM провайдера.
        
    Raises:
        ValueError: Если указан неизвестный тип провайдера.
    """
    provider_type = config.provider.lower()
    
    if provider_type == "openai":
        logger.info(f"Creating OpenAI LLM provider with model: {config.model}")
        return OpenAILLMProvider(config)
    elif provider_type == "local":
        logger.info(f"Creating Local LLM provider with model: {config.model}")
        return LocalLLMProvider(config)
    else:
        raise ValueError(
            f"Unknown LLM provider type: {provider_type}. "
            f"Supported types: 'openai', 'local'"
        )
# END:llm_provider_factory
