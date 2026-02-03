"""
Система конфигурации приложения.
Использует OmegaConf для загрузки и валидации конфигурации.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from omegaconf import OmegaConf


# ANCHOR:config_models
@dataclass
class LLMConfig:
    """Конфигурация LLM провайдера (vLLM или OpenRouter)."""
    base_url_env: str = "LLM_BASE_URL"  # Переменная окружения для URL
    api_key_env: str = "LLM_API_KEY"    # Переменная окружения для ключа
    model: str = "Qwen/QWEN2.5-Omni-3B"

    @property
    def base_url(self) -> str:
        """Получить base URL из переменной окружения."""
        url = os.getenv(self.base_url_env)
        if not url:
            raise ValueError(f"LLM base URL not found in environment variable: {self.base_url_env}")
        return url
    
    @property
    def api_key(self) -> str:
        """Получить API ключ из переменной окружения."""
        key = os.getenv(self.api_key_env)
        if not key:
            raise ValueError(f"API key not found in environment variable: {self.api_key_env}")
        return key


@dataclass
class ToolConfig:
    """Базовая конфигурация инструмента."""
    enabled: bool = True


@dataclass
class FlightsToolConfig(ToolConfig):
    """Конфигурация инструмента расписания рейсов."""
    api_key_env: str = "YANDEX_RASP_API_KEY"
    base_url: str = "https://api.rasp.yandex.net/v3.0"
    cache_file: str = "data/airports.json"
    cache_ttl_days: int = 30  # Обновлять кэш раз в 30 дней
    only_russia: bool = True  # Только рейсы по России
    only_planes: bool = True  # Только самолёты
    
    @property
    def api_key(self) -> Optional[str]:
        """Получить API ключ из переменной окружения."""
        return os.getenv(self.api_key_env)


@dataclass
class CalendarToolConfig(ToolConfig):
    """Конфигурация инструмента календаря."""
    file_path: str = "data/calendar.csv"
    
    @property
    def full_path(self) -> Path:
        """Получить полный путь к файлу календаря."""
        return Path(self.file_path)


@dataclass
class MusicToolConfig(ToolConfig):
    """Конфигурация инструмента музыки."""
    api_key_env: str = "YANDEX_MUSIC_TOKEN"
    
    @property
    def api_key(self) -> Optional[str]:
        """Получить API ключ из переменной окружения."""
        return os.getenv(self.api_key_env)


@dataclass
class NotesToolConfig(ToolConfig):
    """Конфигурация инструмента заметок."""
    storage_path: str = "data/notes/"
    
    @property
    def full_path(self) -> Path:
        """Получить полный путь к директории заметок."""
        return Path(self.storage_path)


@dataclass
class ToolsConfig:
    """Конфигурация всех инструментов."""
    flights: FlightsToolConfig = field(default_factory=FlightsToolConfig)
    calendar: CalendarToolConfig = field(default_factory=CalendarToolConfig)
    music: MusicToolConfig = field(default_factory=MusicToolConfig)
    notes: NotesToolConfig = field(default_factory=NotesToolConfig)


@dataclass
class UIConfig:
    """Конфигурация пользовательского интерфейса."""
    host: str = "0.0.0.0"
    port: int = 7860
    share: bool = False
    audio_sample_rate: int = 16000
    server_name: Optional[str] = None


@dataclass
class LoggingConfig:
    """Конфигурация логирования."""
    level: str = "INFO"
    file: str = "data/logs/app.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @property
    def log_file_path(self) -> Path:
        """Получить полный путь к файлу логов."""
        return Path(self.file)


@dataclass
class Config:
    """Главная конфигурация приложения."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
# END:config_models


# ANCHOR:config_loader
class ConfigLoader:
    """Загрузчик конфигурации из YAML файлов."""
    
    DEFAULT_CONFIG_PATH = "config/config.yml"
    
    @staticmethod
    def load(config_path: Optional[str] = None) -> Config:
        """
        Загрузить конфигурацию из файла.
        
        Args:
            config_path: Путь к файлу конфигурации. Если None, используется DEFAULT_CONFIG_PATH.
            
        Returns:
            Объект конфигурации.
        """
        path = config_path or ConfigLoader.DEFAULT_CONFIG_PATH
        
        if not os.path.exists(path):
            # Если файл не существует, создаем конфигурацию по умолчанию
            return Config()
        
        # Загружаем YAML
        omega_conf = OmegaConf.load(path)
        
        # Создаем базовую конфигурацию
        base_config = OmegaConf.structured(Config)
        
        # Мержим с загруженной конфигурацией
        merged = OmegaConf.merge(base_config, omega_conf)
        
        # Конвертируем в объект
        return OmegaConf.to_object(merged)
    
    @staticmethod
    def save(config: Config, config_path: Optional[str] = None) -> None:
        """
        Сохранить конфигурацию в файл.
        
        Args:
            config: Объект конфигурации.
            config_path: Путь к файлу конфигурации.
        """
        path = config_path or ConfigLoader.DEFAULT_CONFIG_PATH
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Конвертируем в OmegaConf и сохраняем
        omega_conf = OmegaConf.structured(config)
        OmegaConf.save(omega_conf, path)
# END:config_loader


# ANCHOR:config_singleton
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None, reload: bool = False) -> Config:
    """
    Получить глобальный экземпляр конфигурации (singleton).
    
    Args:
        config_path: Путь к файлу конфигурации.
        reload: Перезагрузить конфигурацию, даже если она уже загружена.
        
    Returns:
        Объект конфигурации.
    """
    global _config_instance
    
    if _config_instance is None or reload:
        _config_instance = ConfigLoader.load(config_path)
    
    return _config_instance


def set_config(config: Config) -> None:
    """
    Установить глобальный экземпляр конфигурации.
    
    Args:
        config: Объект конфигурации.
    """
    global _config_instance
    _config_instance = config
# END:config_singleton
