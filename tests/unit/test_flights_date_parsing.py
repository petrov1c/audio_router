"""
Тесты для парсинга дат в инструменте поиска авиарейсов.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.flights import FlightsTool
from src.tools.schemas import FlightScheduleTool
from src.tools.airport_registry import Airport
from src.core.config import FlightsToolConfig


# ANCHOR:test_fixtures
@pytest.fixture
def mock_config():
    """Мок конфигурации."""
    config = MagicMock(spec=FlightsToolConfig)
    config.base_url = "https://api.rasp.yandex.net/v3.0"
    config.api_key = "test_key"
    config.only_russia = True
    return config


@pytest.fixture
def flights_tool(mock_config):
    """Создать инструмент с моком."""
    tool = FlightsTool(mock_config)
    # Мокаем airport_registry
    tool.airport_registry = MagicMock()
    tool.airport_registry.ensure_loaded = AsyncMock()
    
    # Мокаем аэропорты
    mock_airport_from = Airport(
        code="SVO",
        title="Шереметьево",
        settlement="Москва",
        region="Москва и Московская область",
        country="Россия",
        latitude=55.972642,
        longitude=37.414589
    )
    mock_airport_to = Airport(
        code="LED",
        title="Пулково",
        settlement="Санкт-Петербург",
        region="Санкт-Петербург и Ленинградская область",
        country="Россия",
        latitude=59.800292,
        longitude=30.262503
    )
    
    def find_airport_side_effect(city):
        if "москв" in city.lower():
            return mock_airport_from
        elif "петербург" in city.lower() or "питер" in city.lower():
            return mock_airport_to
        return None
    
    tool.airport_registry.find_airport = MagicMock(side_effect=find_airport_side_effect)
    
    return tool


@pytest.fixture
def mock_http_response():
    """Мок HTTP ответа от API."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "segments": [
            {
                "departure": "2026-02-03T10:00:00+03:00",
                "arrival": "2026-02-03T11:30:00+03:00",
                "duration": 5400,
                "thread": {
                    "carrier": {"title": "Аэрофлот"},
                    "number": "SU26",
                    "title": "Москва — Санкт-Петербург",
                    "transport_type": "plane"
                },
                "from": {"title": "Шереметьево"},
                "to": {"title": "Пулково"}
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    return mock_response
# END:test_fixtures


# ANCHOR:test_date_parsing
class TestDateParsing:
    """Тесты парсинга дат."""
    
    @pytest.mark.asyncio
    async def test_parse_tomorrow_russian(self, flights_tool, mock_http_response):
        """Тест парсинга 'завтра'."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_http_response
            )
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="завтра"
            )
            
            result = await flights_tool.execute(params)
            
            # Проверяем что дата распарсена
            assert result["success"] is True
            assert "date" in result
            assert result["date"].startswith("2026-")
            assert "original_date" in result
            assert result["original_date"] == "завтра"
    
    @pytest.mark.asyncio
    async def test_parse_tomorrow_english(self, flights_tool, mock_http_response):
        """Тест парсинга 'tomorrow'."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_http_response
            )
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="tomorrow"
            )
            
            result = await flights_tool.execute(params)
            
            assert result["success"] is True
            assert "date" in result
            assert result["date"].startswith("2026-")
            assert result["original_date"] == "tomorrow"
    
    @pytest.mark.asyncio
    async def test_parse_next_monday(self, flights_tool, mock_http_response):
        """Тест парсинга 'следующий понедельник'."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_http_response
            )
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="следующий понедельник"
            )
            
            result = await flights_tool.execute(params)
            
            assert result["success"] is True
            assert "original_date" in result
            assert result["original_date"] == "следующий понедельник"
    
    @pytest.mark.asyncio
    async def test_parse_in_3_days(self, flights_tool, mock_http_response):
        """Тест парсинга 'через 3 дня'."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_http_response
            )
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="через 3 дня"
            )
            
            result = await flights_tool.execute(params)
            
            assert result["success"] is True
            assert "original_date" in result
            assert result["original_date"] == "через 3 дня"
    
    @pytest.mark.asyncio
    async def test_absolute_date_still_works(self, flights_tool, mock_http_response):
        """Тест что абсолютные даты продолжают работать."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_http_response
            )
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="2026-02-15"
            )
            
            result = await flights_tool.execute(params)
            
            assert result["success"] is True
            assert result["date"] == "2026-02-15"
            assert result["original_date"] == "2026-02-15"
# END:test_date_parsing


# ANCHOR:test_error_handling
class TestErrorHandling:
    """Тесты обработки ошибок."""
    
    @pytest.mark.asyncio
    async def test_period_not_allowed(self, flights_tool):
        """Тест что периоды не поддерживаются."""
        params = FlightScheduleTool(
            tool="flight_schedule",
            from_city="Москва",
            to_city="Санкт-Петербург",
            date="следующая неделя"
        )
        
        result = await flights_tool.execute(params)
        
        assert result["success"] is False
        assert result["error"] == "period_not_allowed"
        assert "период" in result["message"].lower()
        assert "следующая неделя" in result["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_date(self, flights_tool):
        """Тест обработки некорректной даты."""
        params = FlightScheduleTool(
            tool="flight_schedule",
            from_city="Москва",
            to_city="Санкт-Петербург",
            date="32 февраля"
        )
        
        result = await flights_tool.execute(params)
        
        assert result["success"] is False
        assert result["error"] == "date_parse_error"
        assert "32 февраля" in result["message"]
    
    @pytest.mark.asyncio
    async def test_unknown_date_format(self, flights_tool):
        """Тест обработки неизвестного формата даты."""
        params = FlightScheduleTool(
            tool="flight_schedule",
            from_city="Москва",
            to_city="Санкт-Петербург",
            date="на днях"
        )
        
        result = await flights_tool.execute(params)
        
        assert result["success"] is False
        assert result["error"] == "date_parse_error"
# END:test_error_handling


# ANCHOR:test_message_formatting
class TestMessageFormatting:
    """Тесты форматирования сообщений."""
    
    @pytest.mark.asyncio
    async def test_message_includes_original_date(self, flights_tool, mock_http_response):
        """Тест что сообщение включает оригинальную дату."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_http_response
            )
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="завтра"
            )
            
            result = await flights_tool.execute(params)
            
            assert result["success"] is True
            assert "message" in result
            # Сообщение должно содержать и оригинальную дату, и ISO формат
            assert "завтра" in result["message"]
            assert "2026-" in result["message"]
    
    @pytest.mark.asyncio
    async def test_no_flights_message_with_relative_date(self, flights_tool):
        """Тест сообщения когда рейсы не найдены с относительной датой."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"segments": []}
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            params = FlightScheduleTool(
                tool="flight_schedule",
                from_city="Москва",
                to_city="Санкт-Петербург",
                date="послезавтра"
            )
            
            result = await flights_tool.execute(params)
            
            assert result["success"] is True
            assert result["found"] is False
            assert "послезавтра" in result["message"]
            assert "original_date" in result
            assert result["original_date"] == "послезавтра"
# END:test_message_formatting
