"""
Тесты для системы конфигурации.
"""

import pytest
from pathlib import Path

from src.core.config import (
    Config,
    LLMConfig,
    ToolsConfig,
    UIConfig,
    LoggingConfig,
    ConfigLoader,
    get_config,
    set_config
)


# ANCHOR:test_default_config
def test_default_config():
    """Тест создания конфигурации по умолчанию."""
    config = Config()
    
    assert config.llm is not None
    assert config.tools is not None
    assert config.ui is not None
    assert config.logging is not None
    
    # Проверяем значения по умолчанию
    assert config.llm.provider == "local"
    assert config.llm.model == "Qwen/QWEN2.5-Omni-3B"

    assert config.ui.host == "0.0.0.0"
    assert config.ui.port == 7860
    
    assert config.logging.level == "INFO"
# END:test_default_config


# ANCHOR:test_llm_config
def test_llm_config(monkeypatch):
    """Тест конфигурации LLM для OpenAI провайдера."""
    # Устанавливаем переменные окружения для теста
    monkeypatch.setenv("TEST_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("TEST_API_KEY", "test-key-123")
    
    llm_config = LLMConfig(
        provider="openai",
        base_url_env="TEST_BASE_URL",
        api_key_env="TEST_API_KEY",
        model="test-model",
    )
    
    assert llm_config.base_url == "https://api.example.com/v1"
    assert llm_config.api_key == "test-key-123"
    assert llm_config.model == "test-model"
# END:test_llm_config


# ANCHOR:test_tools_config
def test_tools_config():
    """Тест конфигурации инструментов."""
    tools_config = ToolsConfig()
    
    assert tools_config.flights.enabled is True
    assert tools_config.calendar.enabled is True
    assert tools_config.music.enabled is True
    assert tools_config.notes.enabled is True
    
    # Проверяем пути
    assert isinstance(tools_config.calendar.full_path, Path)
    assert isinstance(tools_config.notes.full_path, Path)
# END:test_tools_config


# ANCHOR:test_config_singleton
def test_config_singleton():
    """Тест singleton паттерна для конфигурации."""
    config1 = get_config()
    config2 = get_config()
    
    # Должны быть одним и тем же объектом
    assert config1 is config2
    
    # Тест установки новой конфигурации
    new_config = Config()
    set_config(new_config)
    
    config3 = get_config()
    assert config3 is new_config
# END:test_config_singleton


# ANCHOR:test_llm_config_provider
def test_llm_config_default_provider():
    """Тест значения по умолчанию для provider."""
    config = LLMConfig()
    assert config.provider == "local"


def test_llm_config_openai_provider(monkeypatch):
    """Тест конфигурации для OpenAI провайдера."""
    monkeypatch.setenv("LLM_BASE_URL", "http://test.com")
    monkeypatch.setenv("LLM_API_KEY", "test_key")
    
    config = LLMConfig(provider="openai")
    assert config.provider == "openai"
    assert config.base_url == "http://test.com"
    assert config.api_key == "test_key"


def test_llm_config_local_provider_no_env():
    """Тест что локальный провайдер не требует env переменных."""
    config = LLMConfig(provider="local")
    assert config.provider == "local"
    assert config.base_url is None
    assert config.api_key is None


def test_llm_config_openai_missing_base_url(monkeypatch):
    """Тест ошибки при отсутствии base_url для OpenAI провайдера."""
    monkeypatch.setenv("LLM_API_KEY", "test_key")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    
    config = LLMConfig(provider="openai")
    
    with pytest.raises(ValueError, match="LLM base URL required for openai provider"):
        _ = config.base_url


def test_llm_config_openai_missing_api_key(monkeypatch):
    """Тест ошибки при отсутствии API ключа для OpenAI провайдера."""
    monkeypatch.setenv("LLM_BASE_URL", "http://test.com")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    
    config = LLMConfig(provider="openai")
    
    with pytest.raises(ValueError, match="API key required for openai provider"):
        _ = config.api_key
# END:test_llm_config_provider
