"""
Integration-тесты для FlightsTool.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.flights import FlightsTool
from src.tools.schemas import FlightScheduleTool
from src.tools.airport_registry import Airport
from src.core.config import FlightsToolConfig


# ANCHOR:fixtures
@pytest.fixture
def config():
    """Конфигурация для тестов."""
    return FlightsToolConfig(
        cache_file="test_airports.json",
        cache_ttl_days=30,
        only_russia=True,
        only_planes=True
    )


@pytest.fixture
def tool(config):
    """Инструмент для тестов."""
    with patch.dict('os.environ', {'YANDEX_RASP_API_KEY': 'test_api_key'}):
        return FlightsTool(config)


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
            aliases=["Москва", "Шереметьево", "SVO"]
        ),
        Airport(
            code="s9600213",
            title="Пулково",
            settlement="Санкт-Петербург",
            region="Санкт-Петербург и Ленинградская область",
            country="Россия",
            latitude=59.800292,
            longitude=30.262503,
            aliases=["Санкт-Петербург", "Пулково", "Питер", "LED"]
        )
    ]
# END:fixtures


# ANCHOR:test_tool_basic
class TestFlightsToolBasic:
    """Базовые тесты инструмента."""
    
    def test_tool_name(self, tool):
        """Тест имени инструмента."""
        assert tool.name == "flight_schedule"
    
    def test_tool_description(self, tool):
        """Тест описания инструмента."""
        assert "авиарейсов" in tool.description.lower()
        assert "россии" in tool.description.lower()
    
    def test_tool_schema(self, tool):
        """Тест схемы инструмента."""
        schema = tool.get_schema()
        assert schema == FlightScheduleTool
# END:test_tool_basic


# ANCHOR:test_tool_execute
class TestFlightsToolExecute:
    """Тесты выполнения поиска."""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, tool, sample_airports):
        """Тест успешного поиска рейсов."""
        # Мокаем реестр аэропортов
        tool.airport_registry.airports = sample_airports
        tool.airport_registry._build_indexes()
        tool.airport_registry._loaded = True
        
        # Мокаем API ответ
        mock_api_response = {
            "segments": [
                {
                    "departure": "2026-02-01T10:00:00+03:00",
                    "arrival": "2026-02-01T11:30:00+03:00",
                    "duration": 5400,
                    "thread": {
                        "carrier": {"title": "Аэрофлот"},
                        "number": "SU1234",
                        "title": "Москва — Санкт-Петербург",
                        "transport_type": "plane"
                    },
                    "from": {"title": "Шереметьево"},
                    "to": {"title": "Пулково"}
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.json.return_value = mock_api_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="2026-02-01"
            )
            
            result = await tool.execute(params)
        
        assert result["success"] is True
        assert result["found"] is True
        assert result["count"] == 1
        assert len(result["flights"]) == 1
        assert "Аэрофлот" in result["message"]
    
    @pytest.mark.asyncio
    async def test_execute_airport_not_found(self, tool, sample_airports):
        """Тест поиска с несуществующим аэропортом."""
        tool.airport_registry.airports = sample_airports
        tool.airport_registry._build_indexes()
        tool.airport_registry._loaded = True
        
        params = FlightScheduleTool(
            tool="flight_schedule",
            from_city="Несуществующий",
            to_city="Санкт-Петербург",
            date="2026-02-01"
        )
        
        result = await tool.execute(params)
        
        assert result["success"] is False
        assert result["error"] == "airport_not_found"
        assert "не найден" in result["message"]
    
    @pytest.mark.asyncio
    async def test_execute_no_flights_found(self, tool, sample_airports):
        """Тест когда рейсы не найдены."""
        tool.airport_registry.airports = sample_airports
        tool.airport_registry._build_indexes()
        tool.airport_registry._loaded = True
        
        # Мокаем API ответ без рейсов
        mock_api_response = {"segments": []}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.json.return_value = mock_api_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="2026-02-01"
            )
            
            result = await tool.execute(params)
        
        assert result["success"] is True
        assert result["found"] is False
        assert "не найдено" in result["message"]
    
    @pytest.mark.asyncio
    async def test_execute_with_alias(self, tool, sample_airports):
        """Тест поиска с использованием алиаса."""
        tool.airport_registry.airports = sample_airports
        tool.airport_registry._build_indexes()
        tool.airport_registry._loaded = True
        
        mock_api_response = {
            "segments": [
                {
                    "departure": "2026-02-01T10:00:00+03:00",
                    "arrival": "2026-02-01T11:30:00+03:00",
                    "duration": 5400,
                    "thread": {
                        "carrier": {"title": "Аэрофлот"},
                        "number": "SU1234",
                        "title": "Москва — Санкт-Петербург",
                        "transport_type": "plane"
                    },
                    "from": {"title": "Шереметьево"},
                    "to": {"title": "Пулково"}
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.json.return_value = mock_api_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            # Используем алиас "Питер" вместо "Санкт-Петербург"
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Питер",
                date="2026-02-01"
            )
            
            result = await tool.execute(params)
        
        assert result["success"] is True
        assert result["found"] is True
# END:test_tool_execute


# ANCHOR:test_tool_validation
class TestFlightsToolValidation:
    """Тесты валидации."""
    
    @pytest.mark.asyncio
    async def test_validate_russia_only(self, tool):
        """Тест ограничения только на Россию."""
        # Добавляем международный аэропорт
        international_airport = Airport(
            code="s123",
            title="Charles de Gaulle",
            settlement="Париж",
            region="Île-de-France",
            country="Франция",
            latitude=49.0,
            longitude=2.5,
            aliases=["Париж", "CDG"]
        )
        
        russian_airport = Airport(
            code="s9600820",
            title="Шереметьево",
            settlement="Москва",
            region="Москва и Московская область",
            country="Россия",
            latitude=55.972642,
            longitude=37.414589,
            aliases=["Москва", "SVO"]
        )
        
        tool.airport_registry.airports = [russian_airport, international_airport]
        tool.airport_registry._build_indexes()
        tool.airport_registry._loaded = True
        
        params = FlightScheduleTool(
            tool="flight_schedule",
            from_city="Москва",
            to_city="Париж",
            date="2026-02-01"
        )
        
        result = await tool.execute(params)
        
        assert result["success"] is False
        assert result["error"] == "international_not_supported"
        assert "только по России" in result["message"]
    
    @pytest.mark.asyncio
    async def test_no_api_key(self):
        """Тест без API ключа."""
        config = FlightsToolConfig()
        tool = FlightsTool(config)
        
        params = FlightScheduleTool(
            tool="flight_schedule",
            from_city="Москва",
            to_city="Санкт-Петербург",
            date="2026-02-01"
        )
        
        result = await tool.execute(params)
        
        assert result["success"] is False
        assert "api_key" in result["error"].lower()
# END:test_validation


# ANCHOR:test_tool_formatting
class TestFlightsToolFormatting:
    """Тесты форматирования результатов."""
    
    def test_format_message_with_flights(self, tool, sample_airports):
        """Тест форматирования сообщения с рейсами."""
        flights = [
            {
                "carrier": "Аэрофлот",
                "number": "SU1234",
                "departure": "2026-02-01T10:00:00+03:00",
                "arrival": "2026-02-01T11:30:00+03:00",
                "duration": 5400
            }
        ]
        
        message = tool._format_message(
            flights,
            sample_airports[0],
            sample_airports[1],
            "2026-02-01"
        )
        
        assert "Найдено 1 авиарейсов" in message
        assert "Москва" in message
        assert "Санкт-Петербург" in message
        assert "Аэрофлот" in message
        assert "SU1234" in message
    
    def test_format_message_no_flights(self, tool, sample_airports):
        """Тест форматирования сообщения без рейсов."""
        message = tool._format_message(
            [],
            sample_airports[0],
            sample_airports[1],
            "2026-02-01"
        )
        
        assert "не найдены" in message
        assert "Москва" in message
        assert "Санкт-Петербург" in message
    
    def test_format_message_many_flights(self, tool, sample_airports):
        """Тест форматирования с большим количеством рейсов."""
        flights = [
            {
                "carrier": f"Авиакомпания {i}",
                "number": f"FL{i:04d}",
                "departure": "2026-02-01T10:00:00+03:00",
                "arrival": "2026-02-01T11:30:00+03:00",
                "duration": 5400
            }
            for i in range(10)
        ]
        
        message = tool._format_message(
            flights,
            sample_airports[0],
            sample_airports[1],
            "2026-02-01"
        )
        
        # Должны показываться только первые 5
        assert "Авиакомпания 0" in message
        assert "Авиакомпания 4" in message
        assert "и ещё 5 рейсов" in message
# END:test_tool_formatting
