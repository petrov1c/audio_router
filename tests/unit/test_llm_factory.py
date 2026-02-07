"""
Тесты для фабрики LLM провайдеров.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.llm.factory import create_llm_provider
from src.llm.openai_provider import OpenAILLMProvider
from src.llm.local_provider import LocalLLMProvider
from src.core.config import LLMConfig


# ANCHOR:test_openai_provider_creation
@patch.dict('os.environ', {'LLM_BASE_URL': 'http://test.com', 'LLM_API_KEY': 'test_key'})
def test_create_openai_provider():
    """Тест создания OpenAI провайдера."""
    config = LLMConfig(
        provider="openai",
        model="test-model"
    )
    
    provider = create_llm_provider(config)
    
    assert isinstance(provider, OpenAILLMProvider)
    assert provider.config.model == "test-model"
# END:test_openai_provider_creation


# ANCHOR:test_local_provider_creation
@patch('src.llm.local_provider.Qwen2_5OmniProcessor')
@patch('src.llm.local_provider.Qwen2_5OmniForConditionalGeneration')
@patch('src.llm.local_provider.AutoTokenizer')
@patch('src.llm.local_provider.xgr')
def test_create_local_provider(mock_xgr, mock_tokenizer, mock_model, mock_processor):
    """Тест создания локального провайдера."""
    # Настройка моков
    mock_processor_instance = MagicMock()
    mock_processor.from_pretrained.return_value = mock_processor_instance
    
    mock_model_instance = MagicMock()
    mock_model_instance.config.thinker_config.text_config.vocab_size = 151936
    mock_model.from_pretrained.return_value = mock_model_instance
    
    mock_tokenizer_instance = MagicMock()
    mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
    
    mock_tokenizer_info = MagicMock()
    mock_xgr.TokenizerInfo.from_huggingface.return_value = mock_tokenizer_info
    
    mock_grammar_compiler = MagicMock()
    mock_xgr.GrammarCompiler.return_value = mock_grammar_compiler
    
    config = LLMConfig(
        provider="local",
        model="test-model"
    )
    
    provider = create_llm_provider(config)
    
    assert isinstance(provider, LocalLLMProvider)
    assert provider.config.model == "test-model"
# END:test_local_provider_creation


# ANCHOR:test_unknown_provider
def test_create_unknown_provider():
    """Тест обработки неизвестного провайдера."""
    config = LLMConfig(
        provider="unknown",
        model="test-model"
    )
    
    with pytest.raises(ValueError, match="Unknown LLM provider type"):
        create_llm_provider(config)
# END:test_unknown_provider


# ANCHOR:test_case_insensitive
@patch('src.llm.local_provider.Qwen2_5OmniProcessor')
@patch('src.llm.local_provider.Qwen2_5OmniForConditionalGeneration')
@patch('src.llm.local_provider.AutoTokenizer')
@patch('src.llm.local_provider.xgr')
def test_provider_type_case_insensitive(mock_xgr, mock_tokenizer, mock_model, mock_processor):
    """Тест нечувствительности к регистру типа провайдера."""
    # Настройка моков
    mock_processor_instance = MagicMock()
    mock_processor.from_pretrained.return_value = mock_processor_instance
    
    mock_model_instance = MagicMock()
    mock_model_instance.config.thinker_config.text_config.vocab_size = 151936
    mock_model.from_pretrained.return_value = mock_model_instance
    
    mock_tokenizer_instance = MagicMock()
    mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
    
    mock_tokenizer_info = MagicMock()
    mock_xgr.TokenizerInfo.from_huggingface.return_value = mock_tokenizer_info
    
    mock_grammar_compiler = MagicMock()
    mock_xgr.GrammarCompiler.return_value = mock_grammar_compiler
    
    config = LLMConfig(
        provider="LOCAL",
        model="test-model"
    )
    
    provider = create_llm_provider(config)
    
    assert isinstance(provider, LocalLLMProvider)
# END:test_case_insensitive


# ANCHOR:test_openai_provider_uppercase
@patch.dict('os.environ', {'LLM_BASE_URL': 'http://test.com', 'LLM_API_KEY': 'test_key'})
def test_openai_provider_uppercase():
    """Тест создания OpenAI провайдера с uppercase."""
    config = LLMConfig(
        provider="OPENAI",
        model="test-model"
    )
    
    provider = create_llm_provider(config)
    
    assert isinstance(provider, OpenAILLMProvider)
# END:test_openai_provider_uppercase
