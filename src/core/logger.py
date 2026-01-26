"""
Система логирования приложения.
Настройка и управление логгерами.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.core.config import get_config, LoggingConfig


# ANCHOR:logger_setup
def setup_logger(
    name: str = "audio_router",
    config: Optional[LoggingConfig] = None
) -> logging.Logger:
    """
    Настроить логгер с заданной конфигурацией.
    
    Args:
        name: Имя логгера.
        config: Конфигурация логирования. Если None, используется из глобальной конфигурации.
        
    Returns:
        Настроенный логгер.
    """
    if config is None:
        config = get_config().logging
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(config.level)
    
    # Удаляем существующие обработчики
    logger.handlers.clear()
    
    # Создаем форматтер
    formatter = logging.Formatter(config.format)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик
    log_file = config.log_file_path
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(config.level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Предотвращаем распространение логов к родительским логгерам
    logger.propagate = False
    
    return logger
# END:logger_setup


# ANCHOR:logger_getter
_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str = "audio_router") -> logging.Logger:
    """
    Получить логгер по имени. Если логгер не существует, создает его.
    
    Args:
        name: Имя логгера.
        
    Returns:
        Логгер.
    """
    if name not in _loggers:
        _loggers[name] = setup_logger(name)
    
    return _loggers[name]
# END:logger_getter


# ANCHOR:module_logger
def get_module_logger(module_name: str) -> logging.Logger:
    """
    Получить логгер для модуля.
    
    Args:
        module_name: Имя модуля (обычно __name__).
        
    Returns:
        Логгер для модуля.
    """
    # Извлекаем имя модуля после 'src.'
    if module_name.startswith('src.'):
        logger_name = module_name
    else:
        logger_name = f"audio_router.{module_name}"
    
    return get_logger(logger_name)
# END:module_logger
