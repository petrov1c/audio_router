* По совету Рината, когда надо сделать любое изменение, проси агента написать детальный план в markdown, положив файл в plans/001-feature-name.md

* [schema-guided-reasoning.py](schema-guided-reasoning.py) - оригинальная версия Рината
* [llm_sgr_agent.py](llm_sgr_agent.py) - версия с красивым выводом
* [sgr_assistant.py](sgr_assistant.py) - версия от ребят из Сбера на маленькой модели
* https://github.com/vakovalskii/sgr-deep-research/tree/master - реализация агента


Модели
* Gemma-3n https://huggingface.co/google/gemma-3n-E4B-it
https://huggingface.co/unsloth/gemma-3n-E4B-it
* LFM2.5-Audio https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B
* QWEN2.5-Omni-3B https://huggingface.co/Qwen/Qwen2.5-Omni-3B
* Qwen/Qwen3-Omni-30B-A3B-Instruct https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct


* t-one (ASR) https://github.com/voicekit-team/T-one/blob/main/README.ru.md

Инструменты
*   Калькулятор
*   Поиск рецептов
*   Включить музыку
*   Описание навыков и отказ от пустой болтовни

Выбранные компоненты
модель 
*   QWEN2.5-Omni-3B. Хорошо понимает русский текст. Генерация русской речи отсутствует. 
*   Qwen/Qwen3-Omni-30B-A3B-Instruct если будет возможность
*   qwen3-tts-flash-2025-11-27. Её нет в открытом доступе, надо попробовать tts выковырять из Qwen/Qwen3-Omni-30B-A3B-Instruct

Интерфейс
*   Gradio - интерфейс. Здесь https://huggingface.co/spaces/Qwen/Qwen3-Omni-Demo рабочий пример

Бекенд
*   провайдер
*   vllm

ToDo
*   Из большого qwen достать audio-decoder. Посмотреть как он на русском. Ему на вход подается текст (наверно). Тогда совпадение словарей неважно