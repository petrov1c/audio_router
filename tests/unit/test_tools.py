"""
Тесты для системы инструментов.
"""

import pytest
from typing import Dict, Any, Type
from pydantic import Field
from typing_extensions import Literal

from src.tools.base import Tool, BaseTool
from src.tools.registry import ToolRegistry, get_registry, reset_registry
from src.tools.dispatcher import ToolDispatcher


# ANCHOR:test_tool_implementation
class TestToolSchema(BaseTool):
    """Тестовая схема инструмента."""
    tool: Literal["test_tool"]
    param1: str = Field(description="Тестовый параметр 1")
    param2: int = Field(default=42, description="Тестовый параметр 2")


class TestTool(Tool):
    """Тестовый инструмент."""
    
    @property
    def name(self) -> str:
        return "test_tool"
    
    @property
    def description(self) -> str:
        return "Тестовый инструмент для проверки"
    
    def get_schema(self) -> Type[BaseTool]:
        return TestToolSchema
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        assert isinstance(params, TestToolSchema)
        return {
            "success": True,
            "param1": params.param1,
            "param2": params.param2
        }
# END:test_tool_implementation


# ANCHOR:test_tool_registry
@pytest.fixture
def clean_registry():
    """Фикстура для чистого реестра."""
    reset_registry()
    yield get_registry()
    reset_registry()


def test_registry_register(clean_registry):
    """Тест регистрации инструмента."""
    registry = clean_registry
    tool = TestTool()
    
    registry.register(tool)
    
    assert registry.is_registered("test_tool")
    assert len(registry) == 1
    assert "test_tool" in registry


def test_registry_get(clean_registry):
    """Тест получения инструмента."""
    registry = clean_registry
    tool = TestTool()
    
    registry.register(tool)
    
    retrieved_tool = registry.get("test_tool")
    assert retrieved_tool is tool
    
    # Несуществующий инструмент
    assert registry.get("nonexistent") is None


def test_registry_duplicate_registration(clean_registry):
    """Тест дублирования регистрации."""
    registry = clean_registry
    tool1 = TestTool()
    tool2 = TestTool()
    
    registry.register(tool1)
    
    with pytest.raises(ValueError, match="already registered"):
        registry.register(tool2)


def test_registry_unregister(clean_registry):
    """Тест удаления инструмента."""
    registry = clean_registry
    tool = TestTool()
    
    registry.register(tool)
    assert registry.is_registered("test_tool")
    
    registry.unregister("test_tool")
    assert not registry.is_registered("test_tool")
    
    # Попытка удалить несуществующий инструмент
    with pytest.raises(KeyError):
        registry.unregister("nonexistent")
# END:test_tool_registry


# ANCHOR:test_tool_dispatcher
@pytest.mark.asyncio
async def test_dispatcher_dispatch(clean_registry):
    """Тест диспетчеризации вызова инструмента."""
    registry = clean_registry
    tool = TestTool()
    registry.register(tool)
    
    dispatcher = ToolDispatcher(registry)
    
    # Создаем вызов
    tool_call = TestToolSchema(tool="test_tool", param1="test", param2=100)
    
    result = await dispatcher.dispatch(tool_call)
    
    assert result["success"] is True
    assert result["param1"] == "test"
    assert result["param2"] == 100
# END:test_tool_dispatcher
