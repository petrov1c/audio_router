"""
Unit-тесты для AirportRegistry.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.airport_registry import Airport, AirportRegistry
from src.core.config import FlightsToolConfig


# ANCHOR:fixtures
@pytest.fixture
def config():
    """Конфигурация для тестов."""
    return FlightsToolConfig(
        cache_file="test_airports.json",
        cache_ttl_days=30
    )


@pytest.fixture
def sample_airports():
    """Примеры аэропортов для тестов."""
    return [
        Airport(
            code="s9600820",
            title="Шереметьево",
            settlement="Москва",
            region="Москва и Московская область",
            country="Россия",
            latitude=55.972642,
            longitude=37.414589,
            aliases=["Москва", "Шереметьево", "Москва Шереметьево", "SVO"]
        ),
        Airport(
            code="s9600213",
            title="Пулково",
            settlement="Санкт-Петербург",
            region="Санкт-Петербург и Ленинградская область",
            country="Россия",
            latitude=59.800292,
            longitude=30.262503,
            aliases=["Санкт-Петербург", "Пулково", "LED"]
        ),
        Airport(
            code="s9600366",
            title="Адлер",
            settlement="Сочи",
            region="Краснодарский край",
            country="Россия",
            latitude=43.449928,
            longitude=39.956589,
            aliases=["Сочи", "Адлер", "AER"]
        )
    ]


@pytest.fixture
def registry(config):
    """Реестр аэропортов для тестов."""
    return AirportRegistry(config)


@pytest.fixture
def loaded_registry(registry, sample_airports):
    """Реестр с загруженными данными."""
    registry.airports = sample_airports
    registry._build_indexes()
    registry._loaded = True
    return registry
# END:fixtures


# ANCHOR:test_airport_model
class TestAirport:
    """Тесты для модели Airport."""
    
    def test_matches_exact_settlement(self, sample_airports):
        """Тест точного совпадения по названию города."""
        airport = sample_airports[0]
        assert airport.matches("Москва")
        assert airport.matches("москва")
        assert airport.matches("МОСКВА")
    
    def test_matches_exact_title(self, sample_airports):
        """Тест точного совпадения по названию аэропорта."""
        airport = sample_airports[0]
        assert airport.matches("Шереметьево")
        assert airport.matches("шереметьево")
    
    def test_matches_alias(self, sample_airports):
        """Тест совпадения по алиасу."""
        airport = sample_airports[0]
        assert airport.matches("SVO")
        assert airport.matches("svo")
    
    def test_not_matches(self, sample_airports):
        """Тест несовпадения."""
        airport = sample_airports[0]
        assert not airport.matches("Питер")
        assert not airport.matches("Сочи")
    
    def test_similarity_score_exact(self, sample_airports):
        """Тест оценки для точного совпадения."""
        airport = sample_airports[0]
        assert airport.similarity_score("Москва") == 1.0
        assert airport.similarity_score("Шереметьево") == 1.0
    
    def test_similarity_score_fuzzy(self, sample_airports):
        """Тест оценки для нечёткого совпадения."""
        airport = sample_airports[0]
        # Опечатка в названии
        score = airport.similarity_score("Мосва")
        assert 0.8 < score < 1.0
    
    def test_similarity_score_no_match(self, sample_airports):
        """Тест оценки для несовпадения."""
        airport = sample_airports[0]
        score = airport.similarity_score("Владивосток")
        assert score < 0.5
# END:test_airport_model


# ANCHOR:test_registry_search
class TestAirportRegistrySearch:
    """Тесты для поиска аэропортов."""
    
    def test_find_airport_by_settlement(self, loaded_registry):
        """Тест поиска по названию города."""
        airport = loaded_registry.find_airport("Москва")
        assert airport is not None
        assert airport.settlement == "Москва"
    
    def test_find_airport_by_title(self, loaded_registry):
        """Тест поиска по названию аэропорта."""
        airport = loaded_registry.find_airport("Пулково")
        assert airport is not None
        assert airport.title == "Пулково"
    
    def test_find_airport_by_alias(self, loaded_registry):
        """Тест поиска по алиасу."""
        airport = loaded_registry.find_airport("SVO")
        assert airport is not None
        assert airport.code == "s9600820"
    
    def test_find_airport_case_insensitive(self, loaded_registry):
        """Тест поиска без учёта регистра."""
        airport = loaded_registry.find_airport("москва")
        assert airport is not None
        assert airport.settlement == "Москва"
    
    def test_find_airport_fuzzy(self, loaded_registry):
        """Тест нечёткого поиска."""
        # Опечатка в названии
        airport = loaded_registry.find_airport("Мосва")
        assert airport is not None
        assert airport.settlement == "Москва"
    
    def test_find_airport_not_found(self, loaded_registry):
        """Тест поиска несуществующего аэропорта."""
        airport = loaded_registry.find_airport("Несуществующий")
        assert airport is None
    
    def test_find_airports_multiple(self, loaded_registry):
        """Тест поиска нескольких аэропортов."""
        airports = loaded_registry.find_airports("Москва", limit=5)
        assert len(airports) >= 1
        assert airports[0].settlement == "Москва"
    
    def test_find_airports_limit(self, loaded_registry):
        """Тест ограничения количества результатов."""
        airports = loaded_registry.find_airports("Москва", limit=1)
        assert len(airports) == 1
    
    def test_get_by_code(self, loaded_registry):
        """Тест получения по коду."""
        airport = loaded_registry.get_by_code("s9600820")
        assert airport is not None
        assert airport.settlement == "Москва"
    
    def test_get_by_code_not_found(self, loaded_registry):
        """Тест получения несуществующего кода."""
        airport = loaded_registry.get_by_code("invalid_code")
        assert airport is None
# END:test_registry_search


# ANCHOR:test_registry_cache
class TestAirportRegistryCache:
    """Тесты для кэширования."""
    
    def test_save_and_load_cache(self, loaded_registry, tmp_path):
        """Тест сохранения и загрузки кэша."""
        # Изменяем путь к кэшу на временный
        cache_file = tmp_path / "test_cache.json"
        loaded_registry.config.cache_file = str(cache_file)
        
        # Сохраняем
        loaded_registry.save_to_cache()
        assert cache_file.exists()
        
        # Создаём новый реестр и загружаем
        new_registry = AirportRegistry(loaded_registry.config)
        assert new_registry.load_from_cache()
        assert len(new_registry.airports) == len(loaded_registry.airports)
    
    def test_cache_structure(self, loaded_registry, tmp_path):
        """Тест структуры кэша."""
        cache_file = tmp_path / "test_cache.json"
        loaded_registry.config.cache_file = str(cache_file)
        
        loaded_registry.save_to_cache()
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "version" in data
        assert "updated_at" in data
        assert "airports" in data
        assert len(data["airports"]) == len(loaded_registry.airports)
    
    def test_cache_expiration(self, loaded_registry, tmp_path):
        """Тест истечения срока кэша."""
        cache_file = tmp_path / "test_cache.json"
        loaded_registry.config.cache_file = str(cache_file)
        loaded_registry.config.cache_ttl_days = 1
        
        # Сохраняем кэш с устаревшей датой
        data = {
            "version": "1.0",
            "updated_at": (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z",
            "airports": []
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        # Пытаемся загрузить
        new_registry = AirportRegistry(loaded_registry.config)
        assert not new_registry.load_from_cache()
    
    def test_is_cache_valid(self, loaded_registry, tmp_path):
        """Тест проверки валидности кэша."""
        cache_file = tmp_path / "test_cache.json"
        loaded_registry.config.cache_file = str(cache_file)
        
        # Кэша нет
        assert not loaded_registry.is_cache_valid()
        
        # Сохраняем свежий кэш
        loaded_registry.save_to_cache()
        assert loaded_registry.is_cache_valid()
# END:test_registry_cache


# ANCHOR:test_registry_api
class TestAirportRegistryAPI:
    """Тесты для загрузки из API."""
    
    @pytest.mark.asyncio
    async def test_load_from_api_success(self, registry):
        """Тест успешной загрузки из API."""
        # Мокаем API ответ
        mock_response = {
            "countries": [
                {
                    "title": "Россия",
                    "regions": [
                        {
                            "title": "Москва и Московская область",
                            "settlements": [
                                {
                                    "title": "Москва",
                                    "stations": [
                                        {
                                            "transport_type": "Самолёт",
                                            "codes": {"yandex_code": "s9600820"},
                                            "title": "Шереметьево",
                                            "latitude": 55.972642,
                                            "longitude": 37.414589
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            # Устанавливаем API ключ
            registry.config.api_key_env = "TEST_KEY"
            with patch.dict('os.environ', {'TEST_KEY': 'test_api_key'}):
                await registry.load_from_api()
        
        assert len(registry.airports) == 1
        assert registry.airports[0].settlement == "Москва"
    
    @pytest.mark.asyncio
    async def test_load_from_api_filters_non_planes(self, registry):
        """Тест фильтрации не-самолётов."""
        mock_response = {
            "countries": [
                {
                    "title": "Россия",
                    "regions": [
                        {
                            "title": "Москва и Московская область",
                            "settlements": [
                                {
                                    "title": "Москва",
                                    "stations": [
                                        {
                                            "transport_type": "Поезд",
                                            "codes": {"yandex_code": "s123"},
                                            "title": "Казанский вокзал",
                                            "latitude": 55.0,
                                            "longitude": 37.0
                                        },
                                        {
                                            "transport_type": "Самолёт",
                                            "codes": {"yandex_code": "s9600820"},
                                            "title": "Шереметьево",
                                            "latitude": 55.972642,
                                            "longitude": 37.414589
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            registry.config.api_key_env = "TEST_KEY"
            with patch.dict('os.environ', {'TEST_KEY': 'test_api_key'}):
                await registry.load_from_api()
        
        # Должен быть только аэропорт, вокзал отфильтрован
        assert len(registry.airports) == 1
        assert registry.airports[0].title == "Шереметьево"
    
    @pytest.mark.asyncio
    async def test_ensure_loaded_from_cache(self, loaded_registry, tmp_path):
        """Тест ensure_loaded с кэшем."""
        cache_file = tmp_path / "test_cache.json"
        loaded_registry.config.cache_file = str(cache_file)
        loaded_registry.save_to_cache()
        
        # Создаём новый реестр
        new_registry = AirportRegistry(loaded_registry.config)
        await new_registry.ensure_loaded()
        
        assert new_registry._loaded
        assert len(new_registry.airports) == len(loaded_registry.airports)
    
    @pytest.mark.asyncio
    async def test_ensure_loaded_already_loaded(self, loaded_registry):
        """Тест ensure_loaded когда уже загружено."""
        # Не должно делать повторную загрузку
        await loaded_registry.ensure_loaded()
        assert loaded_registry._loaded
# END:test_registry_api
