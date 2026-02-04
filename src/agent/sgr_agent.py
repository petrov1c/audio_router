"""
Schema-Guided Reasoning (SGR) Agent.
Агент для планирования и выполнения задач через вызов инструментов.
"""

from typing import Dict, Union, Any
from pydantic import ValidationError

from src.agent.schemas import AgentStep
from src.agent.prompts import get_system_prompt, format_user_message, format_tool_result
from src.llm import LLMProvider
from src.tools import ToolDispatcher
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:sgr_agent
class SGRAgent:
    """Schema-Guided Reasoning Agent для выполнения задач."""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_dispatcher: ToolDispatcher,
        max_steps: int = 10 # ToDo вынести в сonfig
    ):
        """
        Инициализация агента.
        
        Args:
            llm_provider: Провайдер LLM.
            tool_dispatcher: Диспетчер инструментов.
            max_steps: Максимальное количество шагов.
        """
        self.llm = llm_provider
        self.dispatcher = tool_dispatcher
        self.max_steps = max_steps
        self.system_prompt = get_system_prompt()
        
        logger.info("SGR Agent initialized")
    
    async def process_request(self, user_input: Union[str, bytes]) -> Dict[str, Any]:
        """
        Обработать запрос пользователя.
        
        Args:
            user_input: Запрос пользователя.
            
        Returns:
            Результат обработки.
        """
        logger.info(f"Processing request: {user_input if isinstance(user_input, str) else 'голосовой ввод'}")
        
        # Инициализируем историю диалога
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": format_user_message(user_input)}
        ]
        
        steps_history = []
        
        # Выполняем шаги рассуждения
        for step_num in range(self.max_steps):
            logger.info(f"Step {step_num + 1}/{self.max_steps}")
            
            try:
                # Генерируем следующий шаг через LLM
                agent_step = await self.llm.generate_structured(
                    messages=messages,
                    schema=AgentStep,
                )
                
                logger.info(f"Agent step: tool_required={agent_step.tool_required}, "
                           f"task_completed={agent_step.task_completed}")
                
                # Сохраняем шаг в историю
                steps_history.append({
                    "step": step_num + 1,
                    "current_state": agent_step.current_state,
                    "plan": agent_step.plan,
                    "tool": agent_step.next_action.tool,
                    "tool_required": agent_step.tool_required,
                    "task_completed": agent_step.task_completed
                })
                
                # Выполняем инструмент
                tool_result = await self.dispatcher.dispatch(agent_step.next_action)
                
                logger.info(f"Tool result: {tool_result.get('success', False)}")
                
                # Добавляем результат в историю
                result_message = format_tool_result(
                    agent_step.next_action.tool,
                    tool_result
                )
                messages.append({"role": "assistant", "content": result_message})
                
                # Проверяем завершение задачи
                if (agent_step.task_completed
                        or agent_step.next_action.tool in (
                                "task_completion",
                                "no_tool_available",
                                "flight_schedule",
                                "search_music",
                                "create_note",
                                "search_notes",
                                "add_calendar_event",
                        )
                ):
                    logger.info("Task completed")
                    return {
                        "success": True,
                        "result": tool_result.get("result", tool_result.get("message", "")),
                        "steps": steps_history,
                        "total_steps": step_num + 1
                    }
                
                # Добавляем результат как сообщение пользователя для следующего шага
                messages.append({"role": "user", "content": "Продолжай выполнение задачи"})
                
            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                return {
                    "success": False,
                    "error": f"Ошибка валидации: {str(e)}",
                    "steps": steps_history
                }
            except Exception as e:
                logger.error(f"Error in agent step: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "steps": steps_history
                }
        
        # Достигнут лимит шагов
        logger.warning(f"Max steps ({self.max_steps}) reached")
        return {
            "success": False,
            "error": f"Достигнут лимит шагов ({self.max_steps})",
            "steps": steps_history
        }
# END:sgr_agent
