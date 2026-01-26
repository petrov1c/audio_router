"""
Главный файл приложения Audio Router.
"""

import asyncio
import argparse
from dotenv import load_dotenv

from src.ui.gradio_app import create_app
from src.core.logger import setup_logger, get_logger
from src.core.config import get_config


# Загружаем переменные окружения
load_dotenv()


# ANCHOR:main
def main():
    """Главная функция приложения."""
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description="Audio Router - Голосовой помощник")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Путь к файлу конфигурации"
    )
    args = parser.parse_args()
    
    # Загружаем конфигурацию
    config = get_config(args.config)
    
    # Настраиваем логирование
    logger = setup_logger("audio_router", config.logging)
    logger.info("Starting Audio Router application")
    logger.info(f"LLM Base URL: {config.llm.base_url}")
    logger.info(f"LLM Model: {config.llm.model}")
    
    # Создаем и запускаем Gradio приложение
    try:
        app = create_app()
        logger.info(f"Launching Gradio UI on {config.ui.host}:{config.ui.port}")
        app.launch()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Error running application: {e}", exc_info=True)
        raise
# END:main


if __name__ == "__main__":
    main()
