"""
Инструмент для поиска расписания авиарейсов по России.
Использует Yandex Rasp API.
"""

from typing import Dict, Any, Type, List
from datetime import datetime
import httpx

from src.tools.base import Tool, BaseTool
from src.tools.schemas import FlightScheduleTool
from src.tools.airport_registry import AirportRegistry, Airport
from src.tools.date_parser import DateParser
from src.core.config import FlightsToolConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:flights_tool
class FlightsTool(Tool):
    """Инструмент для поиска расписания авиарейсов по России через Yandex Rasp API."""
    
    def __init__(self, config: FlightsToolConfig):
        """
        Инициализация инструмента.
        
        Args:
            config: Конфигурация инструмента.
        """
        self.config = config
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.airport_registry = AirportRegistry(config)
        
        # Инициализируем парсер дат
        self.date_parser = DateParser()
        
        if not self.api_key:
            logger.warning("Yandex Rasp API key not configured")
    
    async def initialize(self) -> None:
        """Инициализировать инструмент (загрузить реестр аэропортов)."""
        await self.airport_registry.ensure_loaded()
    
    @property
    def name(self) -> str:
        return "flight_schedule"
    
    @property
    def description(self) -> str:
        return (
            "Поиск расписания авиарейсов по России. "
            "Позволяет найти рейсы между двумя городами на указанную дату. "
            "Поддерживаются только внутренние рейсы по России."
        )
    
    def get_schema(self) -> Type[BaseTool]:
        return FlightScheduleTool
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        """
        Выполнить поиск расписания.
        
        Args:
            params: Параметры поиска (FlightScheduleTool).
            
        Returns:
            Результат поиска с информацией о рейсах.
        """
        assert isinstance(params, FlightScheduleTool)
        
        if not self.api_key:
            return {
                "success": False,
                "error": "api_key_not_configured",
                "message": "Для использования этого инструмента необходим API ключ Yandex Rasp"
            }
        
        # Убедиться что реестр загружен
        try:
            await self.airport_registry.ensure_loaded()
        except Exception as e:
            logger.error(f"Error loading airport registry: {e}", exc_info=True)
            return {
                "success": False,
                "error": "registry_load_error",
                "message": "Не удалось загрузить справочник аэропортов"
            }
        
        # ANCHOR:date_parsing
        # Парсим дату
        logger.debug(f"Parsing date: {params.date}")
        try:
            parsed_date = self.date_parser.parse(params.date)
        except ValueError as e:
            logger.error(f"Failed to parse date '{params.date}': {e}")
            return {
                "success": False,
                "error": "date_parse_error",
                "message": f"Не удалось распознать дату: {params.date}. {str(e)}"
            }
        
        # Проверяем что это не период
        if parsed_date.is_period:
            return {
                "success": False,
                "error": "period_not_allowed",
                "message": (
                    f"Для поиска авиарейсов укажите конкретную дату вылета, а не период. "
                    f"Вы указали: '{params.date}' (период с {parsed_date.date_from} по {parsed_date.date_to}). "
                    f"Попробуйте указать конкретный день, например: 'завтра', 'понедельник', 'через 3 дня'"
                )
            }
        
        # Валидируем распарсенную дату
        try:
            datetime.strptime(parsed_date.date, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "error": "invalid_date",
                "message": f"Некорректная дата: {parsed_date.date}"
            }
        
        # Используем распарсенную дату для дальнейшей работы
        flight_date = parsed_date.date
        original_date_text = parsed_date.original_text
        logger.info(
            f"Parsed date '{params.date}' as {flight_date} "
            f"(original: '{original_date_text}')"
        )
        # END:date_parsing
        
        logger.info(
            f"Searching flights from {params.from_city} to {params.to_city} on {flight_date}"
        )
        
        # Найти аэропорт отправления
        from_airport = self.airport_registry.find_airport(params.from_city)
        if not from_airport:
            suggestions = self.airport_registry.find_airports(params.from_city, limit=3)
            suggestion_names = [a.settlement for a in suggestions]
            
            return {
                "success": False,
                "error": f"Аэропорт отправления '{params.from_city}' не найден. Возможно вы имели в виду: {', '.join(suggestion_names)}?" if suggestion_names else f"Аэропорт отправления '{params.from_city}' не найден",
                "message": f"Аэропорт отправления '{params.from_city}' не найден. Возможно вы имели в виду: {', '.join(suggestion_names)}?" if suggestion_names else f"Аэропорт отправления '{params.from_city}' не найден",
                "suggestions": suggestion_names
            }
        
        # Найти аэропорт прибытия
        to_airport = self.airport_registry.find_airport(params.to_city)
        if not to_airport:
            suggestions = self.airport_registry.find_airports(params.to_city, limit=3)
            suggestion_names = [a.settlement for a in suggestions]
            
            return {
                "success": False,
                "error": f"Аэропорт прибытия '{params.to_city}' не найден. Возможно вы имели в виду: {', '.join(suggestion_names)}?" if suggestion_names else f"Аэропорт прибытия '{params.to_city}' не найден",
                "message": f"Аэропорт прибытия '{params.to_city}' не найден. Возможно вы имели в виду: {', '.join(suggestion_names)}?" if suggestion_names else f"Аэропорт прибытия '{params.to_city}' не найден",
                "suggestions": suggestion_names
            }
        
        # Проверить что оба аэропорта в России
        if self.config.only_russia:
            error_msg = self._validate_russia_only(from_airport, to_airport)
            if error_msg:
                return {
                    "success": False,
                    "error": error_msg,
                    "message": error_msg,
                    "from": from_airport.settlement,
                    "to": to_airport.settlement
                }
        
        logger.info(
            f"Found airports: {from_airport.settlement} ({from_airport.code}) -> "
            f"{to_airport.settlement} ({to_airport.code})"
        )
        
        try:
            # Формируем запрос к API
            url = f"{self.base_url}/search/"
            
            query_params = {
                "apikey": self.api_key,
                "from": from_airport.code,
                "to": to_airport.code,
                "date": flight_date,  # Используем распарсенную дату в формате YYYY-MM-DD
                "format": "json",
                "lang": "ru_RU",
                "transport_types": "plane"  # Только самолёты
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=query_params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            
            # Обрабатываем результаты
            segments = data.get("segments", [])
            
            if not segments:
                date_text = original_date_text if original_date_text else flight_date
                return {
                    "success": True,
                    "found": False,
                    "message": (
                        f"Прямых авиарейсов из {from_airport.settlement} "
                        f"в {to_airport.settlement} на {date_text} ({flight_date}) не найдено. "
                        f"Попробуйте выбрать другую дату или рассмотрите рейсы с пересадками."
                    ),
                    "from": from_airport.settlement,
                    "to": to_airport.settlement,
                    "date": flight_date,
                    "original_date": original_date_text
                }
            
            # Форматируем результаты
            flights = []
            for segment in segments:
                flight_info = {
                    "departure": segment.get("departure"),
                    "arrival": segment.get("arrival"),
                    "duration": segment.get("duration"),
                    "carrier": segment.get("thread", {}).get("carrier", {}).get("title"),
                    "number": segment.get("thread", {}).get("number"),
                    "title": segment.get("thread", {}).get("title"),
                    "transport_type": segment.get("thread", {}).get("transport_type"),
                    "from_station": segment.get("from", {}).get("title"),
                    "to_station": segment.get("to", {}).get("title")
                }
                flights.append(flight_info)
            
            return {
                "success": True,
                "found": True,
                "count": len(flights),
                "total_found": len(segments),
                "from": from_airport.settlement,
                "from_airport": from_airport.title,
                "to": to_airport.settlement,
                "to_airport": to_airport.title,
                "date": flight_date,  # Распарсенная дата в ISO формате
                "original_date": original_date_text,  # Оригинальный текст даты
                "flights": flights,
                "message": self._format_message(
                    flights, from_airport, to_airport, flight_date, original_date_text
                )
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Yandex Rasp API: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "message": "Ошибка при обращении к API расписаний"
            }
        except Exception as e:
            logger.error(f"Error searching flights: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Произошла ошибка при поиске рейсов"
            }
    
    def _validate_russia_only(self, from_airport: Airport, to_airport: Airport) -> str:
        """
        Проверить что оба аэропорта в России.
        
        Args:
            from_airport: Аэропорт отправления.
            to_airport: Аэропорт прибытия.
            
        Returns:
            Сообщение об ошибке или пустая строка если всё ОК.
        """
        if from_airport.country != "Россия":
            return (
                f"Извините, я знаю расписание только по авиарейсам внутри России. "
                f"{from_airport.settlement} находится в стране: {from_airport.country}"
            )
        
        if to_airport.country != "Россия":
            return (
                f"Извините, я знаю расписание только по авиарейсам внутри России. "
                f"{to_airport.settlement} находится в стране: {to_airport.country}"
            )
        
        return ""
    
    def _format_message(
        self,
        flights: List[Dict],
        from_airport: Airport,
        to_airport: Airport,
        date: str,
        original_date: str = None
    ) -> str:
        """
        Форматировать сообщение с результатами поиска.
        
        Args:
            flights: Список найденных рейсов.
            from_airport: Аэропорт отправления.
            to_airport: Аэропорт прибытия.
            date: Дата вылета (ISO формат).
            original_date: Оригинальный текст даты (например, "завтра").
            
        Returns:
            Отформатированное сообщение.
        """
        # Используем оригинальный текст если доступен, иначе ISO дату
        date_text = original_date if original_date else date
        
        if not flights:
            return (
                f"Авиарейсы из {from_airport.settlement} в {to_airport.settlement} "
                f"на {date_text} не найдены"
            )
        
        message_parts = [
            f"Найдено {len(flights)} авиарейсов из {from_airport.settlement} ({from_airport.title}) "
            f"в {to_airport.settlement} ({to_airport.title}) на {date_text} ({date}):\n"
        ]
        
        for i, flight in enumerate(flights[:5], 1):  # Показываем первые 5
            carrier = flight.get("carrier", "")
            number = flight.get("number", "")
            departure = flight.get("departure", "")
            arrival = flight.get("arrival", "")
            duration = flight.get("duration", 0)
            
            # Форматируем время (убираем дату, оставляем только время)
            dep_time = departure.split("T")[1][:5] if "T" in departure else departure
            arr_time = arrival.split("T")[1][:5] if "T" in arrival else arrival
            
            # Форматируем длительность
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            duration_str = f"{hours:.0f} ч {minutes:.0f} мин" if hours > 0 else f"{minutes:.0f} мин"
            
            message_parts.append(
                f"{i}. {carrier} {number}: вылет {dep_time}, прилёт {arr_time} ({duration_str})"
            )
        
        if len(flights) > 5:
            message_parts.append(f"\n... и ещё {len(flights) - 5} рейсов")
        
        return "\n".join(message_parts)
# END:flights_tool
