"""
Pydantic схемы для SGR агента.
"""

from typing import Union, List
from typing_extensions import Annotated
from annotated_types import MinLen, MaxLen
from pydantic import BaseModel, Field

from src.tools.schemas import (
    FlightScheduleTool,
    AddCalendarEventTool,
    GetCalendarEventsTool,
    SearchMusicTool,
    CreateNoteTool,
    SearchNotesTool,
    NoToolAvailable,
    TaskCompletion
)


# ANCHOR:agent_step_schema
class AgentStep(BaseModel):
    """
    Схема для одного шага рассуждения агента (Schema-Guided Reasoning).
    """
    
    # Анализ текущей ситуации
    current_state: str = Field(
        description="Текущее состояние и понимание запроса пользователя",
        max_length=1_000,
    )
    
    # Требуется ли инструмент
    tool_required: bool = Field(
        description="Требуется ли вызов инструмента для выполнения запроса"
    )
    
    # План действий (1-3 шага)
    plan: Annotated[List[str], MinLen(1), MaxLen(3)] = Field(
        description="Краткий план оставшихся шагов для выполнения задачи"
    )
    
    # Задача завершена?
    task_completed: bool = Field(
        description="Завершена ли задача полностью"
    )
    
    # Следующее действие (вызов инструмента)
    next_action: Union[
        FlightScheduleTool,
        AddCalendarEventTool,
        GetCalendarEventsTool,
        SearchMusicTool,
        CreateNoteTool,
        SearchNotesTool,
        NoToolAvailable,
        TaskCompletion
    ] = Field(
        description="Следующее действие для выполнения (вызов инструмента)"
    )
# END:agent_step_schema
