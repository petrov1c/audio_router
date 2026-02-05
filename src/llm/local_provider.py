"""
LLM провайдер на основе transformers.
Работает с vLLM, OpenRouter и другими OpenAI-совместимыми API.
"""

import json
from typing import List, Dict, Any, Type

from pydantic import BaseModel

from transformers import (
    AutoTokenizer,
    LogitsProcessorList,
    Qwen2_5OmniProcessor,
    Qwen2_5OmniForConditionalGeneration
)
from qwen_omni_utils import process_mm_info
import xgrammar as xgr
import torch

from src.llm.provider import LLMProvider
from src.core.config import LLMConfig
from src.core.logger import get_module_logger
from src.agent.schemas import AgentStep


logger = get_module_logger(__name__)


# ANCHOR:local_llm_provider
class LocalLLMProvider(LLMProvider):
    """
    LLM провайдер на основе transformers.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Инициализация провайдера.
        
        Args:
            config: Конфигурация LLM.
        """
        self.config = config
        
        self.processor = Qwen2_5OmniProcessor.from_pretrained(config.model)

        self.model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            config.model,
            max_length=8192,
            trust_remote_code=True,
            dtype="auto",
            device_map="auto"
        )
        self.model.eval()

        tokenizer = AutoTokenizer.from_pretrained(config.model, trust_remote_code=True)
        tokenizer_info = xgr.TokenizerInfo.from_huggingface(
            tokenizer,
            vocab_size=self.model.config.thinker_config.text_config.vocab_size
        )
        self.grammar_compiler = xgr.GrammarCompiler(tokenizer_info)

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
            compiled_grammar = self.grammar_compiler.compile_json_schema(schema)
            logits_processor = LogitsProcessorList([xgr.contrib.hf.LogitsProcessor(compiled_grammar)])

            USE_AUDIO_IN_VIDEO = True

            qwen_messages = []
            for message in messages:
                qwen_message = {"role": message["role"]}
                if isinstance(message["content"], str):
                    qwen_message["content"] = [{
                        "type": "text",
                        "text": message["content"],
                    }]
                else:
                    qwen_message["content"] = []
                    for ele in message["content"]:
                        qwen_message["content"].append(
                            {'type': 'audio', 'audio': ele['audio_url']['url']}
                        )

                qwen_messages.append(qwen_message)

            text = self.processor.apply_chat_template(
                qwen_messages,
                add_generation_prompt=True,
                tokenize=False,
                enable_thinking=False
            )

            audios, images, videos = process_mm_info(qwen_messages, use_audio_in_video=USE_AUDIO_IN_VIDEO)
            inputs = self.processor(
                text=text,
                audio=audios,
                images=images,
                videos=videos,
                return_tensors="pt",
                padding=True,
                use_audio_in_video=USE_AUDIO_IN_VIDEO,
            )
            inputs = inputs.to(self.model.device).to(self.model.dtype)

            with torch.no_grad():
                text_ids = self.model.generate(
                    **inputs,
                    use_audio_in_video=USE_AUDIO_IN_VIDEO,
                    do_sample = False,
                    temperature = None,
                    top_p = None,
                    top_k = None,
                    return_audio = False,
                    logits_processor = logits_processor,
                )

            prompt_tokens = len(inputs.input_ids[0])
            choice = self.processor.decode(text_ids[0][prompt_tokens:], skip_special_tokens=True)

            result = AgentStep.model_validate_json(choice)
            logger.info(f"Successfully generated structured output")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating structured output: {e}", exc_info=True)
            raise
# END:local_llm_provider
