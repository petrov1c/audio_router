"""
Gradio интерфейс для голосового помощника.
"""

import gradio as gr
from typing import List, Tuple

from src.agent import create_agent
from src.core.config import get_config
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:gradio_app
class GradioApp:
    """Gradio приложение для голосового помощника."""
    
    def __init__(self):
        """Инициализация приложения."""
        self.config = get_config()
        self.agent = create_agent()
        logger.info("Gradio app initialized")
    
    async def process_message(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Обработать сообщение пользователя.
        
        Args:
            message: Сообщение пользователя.
            history: История диалога.
            
        Returns:
            Кортеж (пустая строка, обновленная история).
        """
        if not message.strip():
            return "", history
        
        logger.info(f"Processing message: {message}")
        
        try:
            # Обрабатываем запрос через агента
            result = await self.agent.process_request(message)
            
            # Формируем ответ
            if result.get("success"):
                response = result.get("result", "Задача выполнена")
                
                # Добавляем информацию о шагах если есть
                if result.get("steps"):
                    steps_info = f"\n\n_Выполнено шагов: {result.get('total_steps', 0)}_"
                    response += steps_info
            else:
                error = result.get("error", "Неизвестная ошибка")
                response = f"❌ Ошибка: {error}"
            
            # Обновляем историю
            history.append((message, response))
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            response = f"❌ Произошла ошибка: {str(e)}"
            history.append((message, response))
        
        return "", history
    
    async def process_audio(
        self,
        audio_path: str,
        history: List[Tuple[str, str]]
    ) -> Tuple[None, List[Tuple[str, str]]]:
        """
        Обработать аудио сообщение.
        
        Args:
            audio_path: Путь к записанному аудио файлу.
            history: История диалога.
            
        Returns:
            Кортеж (None, обновленная история).
        """
        if audio_path is None:
            logger.warning("Audio path is None - recording may not have started")
            history.append((
                "🎤 [Голосовое сообщение]",
                "❌ Не удалось записать аудио. Проверьте:\n"
                "1. Разрешения микрофона в браузере\n"
                "2. Доступ через HTTPS или localhost"
            ))
            return None, history
        
        logger.info(f"Processing audio from: {audio_path}")
        
        try:
            # Читаем аудио файл
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Обрабатываем через агента
            result = await self.agent.process_audio_request(audio_bytes)
            
            # Формируем ответ
            if result.get("success"):
                response = result.get("result", "Задача выполнена")
                
                if result.get("steps"):
                    steps_info = f"\n\n_Выполнено шагов: {result.get('total_steps', 0)}_"
                    response += steps_info
            else:
                error = result.get("error", "Неизвестная ошибка")
                response = f"❌ Ошибка: {error}"
            
            # Добавляем в историю с пометкой о голосовом вводе
            history.append(("🎤 [Голосовое сообщение]", response))
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            response = f"❌ Ошибка обработки аудио: {str(e)}"
            history.append(("🎤 [Голосовое сообщение]", response))
        
        return None, history
    
    def create_interface(self) -> gr.Blocks:
        """
        Создать Gradio интерфейс.
        
        Returns:
            Gradio Blocks интерфейс.
        """
        with gr.Blocks(title="Audio Router - Голосовой помощник") as demo:
            gr.Markdown("# 🎤 Audio Router - Голосовой помощник")
            gr.Markdown(
                "Голосовой помощник с поддержкой инструментов: "
                "расписание рейсов, календарь, музыка, заметки"
            )
            
            chatbot = gr.Chatbot(
                label="Диалог",
                height=500,
                show_label=True
            )
            
            # Вкладки для текста и голоса
            with gr.Tabs():
                # Текстовый ввод
                with gr.Tab("💬 Текст"):
                    with gr.Row():
                        text_input = gr.Textbox(
                            label="Ваше сообщение",
                            placeholder="Например: Найди рейсы из Москвы в Питер на завтра",
                            scale=4
                        )
                        text_submit = gr.Button("Отправить", scale=1, variant="primary")
                
                # Голосовой ввод
                with gr.Tab("🎤 Голос"):
                    gr.Markdown("Нажмите на микрофон и произнесите ваш запрос")
                    
                    audio_input = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="Запись с микрофона",
                        format="wav",
                        recording=False
                    )
                    
                    audio_submit = gr.Button(
                        "🎤 Отправить голосовое сообщение",
                        variant="primary",
                        size="lg"
                    )
            
            gr.Markdown("### Примеры запросов:")
            gr.Examples(
                examples=[
                    "Найди рейсы из Москвы в Санкт-Петербург на завтра",
                    "Добавь встречу с командой на 25 января",
                    "Что у меня запланировано на эту неделю?",
                    "Найди песни Виктора Цоя",
                    "Создай заметку: купить молоко",
                ],
                inputs=text_input
            )
            
            gr.Markdown("### Доступные инструменты:")
            gr.Markdown(
                "- 🛫 **Расписание рейсов** - поиск авиарейсов и поездов\n"
                "- 📅 **Календарь** - управление событиями\n"
                "- 🎵 **Музыка** - поиск в Яндекс.Музыке\n"
                "- 📝 **Заметки** - создание и поиск заметок"
            )
            
            # Обработчики событий
            text_submit.click(
                fn=self.process_message,
                inputs=[text_input, chatbot],
                outputs=[text_input, chatbot]
            )
            
            text_input.submit(
                fn=self.process_message,
                inputs=[text_input, chatbot],
                outputs=[text_input, chatbot]
            )
            
            audio_submit.click(
                fn=self.process_audio,
                inputs=[audio_input, chatbot],
                outputs=[audio_input, chatbot]
            )
        
        return demo
    
    def launch(self):
        """Запустить Gradio приложение."""
        demo = self.create_interface()
        
        # ВАЖНО: Для работы микрофона требуется HTTPS или localhost
        # Если доступ идет по IP адресу, используйте share=True для HTTPS
        # или настройте SSL сертификаты через ssl_certfile/ssl_keyfile
        demo.launch(
            server_name=self.config.ui.host,
            server_port=self.config.ui.port,
            share=self.config.ui.share
        )
# END:gradio_app


# ANCHOR:create_app
def create_app() -> GradioApp:
    """
    Создать Gradio приложение.
    
    Returns:
        Экземпляр GradioApp.
    """
    return GradioApp()
# END:create_app
