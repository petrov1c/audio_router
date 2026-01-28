"""
Скрипт для загрузки списка всех аэропортов России из API Яндекс.Расписаний.

Использование:
    python scripts/download_airports.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.core.config import FlightsToolConfig
from src.tools.airport_registry import AirportRegistry


# ANCHOR:main
async def main():
    """Главная функция скрипта."""
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаём конфигурацию
    config = FlightsToolConfig()
    
    # Проверяем наличие API ключа
    if not config.api_key:
        print("❌ Ошибка: YANDEX_RASP_API_KEY не установлен в .env")
        print("Пожалуйста, добавьте ключ в файл .env:")
        print("YANDEX_RASP_API_KEY=your_api_key_here")
        return 1
    
    # Создаём реестр
    registry = AirportRegistry(config)
    
    print("📡 Загрузка списка станций из API Яндекс.Расписаний...")
    print(f"   URL: {config.base_url}/stations_list/")
    
    try:
        await registry.load_from_api()
    except Exception as e:
        print(f"❌ Ошибка при загрузке данных: {e}")
        return 1
    
    print(f"✅ Загружено аэропортов: {len(registry.airports)}")
    
    # Показываем примеры
    print("\n📋 Примеры аэропортов:")
    for airport in registry.airports[:5]:
        print(f"   • {airport.settlement} - {airport.title} ({airport.code})")
    
    # Сохраняем в кэш
    print(f"\n💾 Сохранение данных в {config.cache_file}...")
    registry.save_to_cache()
    
    # Проверяем размер файла
    cache_path = Path(config.cache_file)
    if cache_path.exists():
        size_mb = cache_path.stat().st_size / (1024 * 1024)
        print(f"✅ Данные сохранены ({size_mb:.2f} МБ)")
    
    print("\n🎉 Готово! Теперь можно использовать инструмент поиска авиарейсов.")
    return 0
# END:main


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
