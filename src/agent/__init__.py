"""
Модуль SGR агента.
"""

from src.agent.sgr_agent import SGRAgent
from src.agent.schemas import AgentStep
from src.agent.prompts import get_system_prompt
from src.llm import OpenAILLMProvider, LocalLLMProvider
from src.tools import ToolDispatcher, register_all_tools
from src.core.config import get_config


def create_agent() -> SGRAgent:
    """
    Создать и инициализировать SGR агента со всеми зависимостями.
    
    Returns:
        Инициализированный SGR агент.
    """
    # Загружаем конфигурацию
    config = get_config()
    
    # Создаем LLM провайдер
    llm_provider = LocalLLMProvider(config.llm)
    
    # Регистрируем все инструменты
    registry = register_all_tools()
    
    # Создаем диспетчер инструментов
    dispatcher = ToolDispatcher(registry)
    
    # Создаем агента
    agent = SGRAgent(
        llm_provider=llm_provider,
        tool_dispatcher=dispatcher,
        router_mode=config.llm.router_mode,
        max_steps=config.llm.max_steps,
    )
    
    return agent


__all__ = [
    "SGRAgent",
    "AgentStep",
    "get_system_prompt",
    "create_agent",
]
