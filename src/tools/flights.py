"""
Инструмент для поиска расписания авиарейсов и поездов.
Использует Yandex Rasp API.
"""

from typing import Dict, Any, Type, List
import httpx
from datetime import datetime

from src.tools.base import Tool, BaseTool
from src.tools.schemas import FlightScheduleTool
from src.core.config import FlightsToolConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:flights_tool
class FlightsTool(Tool):
    """Инструмент для поиска расписания рейсов через Yandex Rasp API."""
    
    def __init__(self, config: FlightsToolConfig):
        """
        Инициализация инструмента.
        
        Args:
            config: Конфигурация инструмента.
        """
        self.config = config
        self.base_url = config.base_url
        self.api_key = config.api_key
        
        if not self.api_key:
            logger.warning("Yandex Rasp API key not configured")
    
    @property
    def name(self) -> str:
        return "flight_schedule"
    
    @property
    def description(self) -> str:
        return (
            "Поиск расписания авиарейсов, поездов, автобусов и электричек. "
            "Позволяет найти рейсы между двумя станциями на указанную дату."
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
                "error": "Yandex Rasp API key not configured",
                "message": "Для использования этого инструмента необходим API ключ Yandex Rasp"
            }
        
        logger.info(
            f"Searching flights from {params.from_station} to {params.to_station} "
            f"on {params.date}, transport: {params.transport_type}"
        )
        
        try:
            # Формируем запрос к API
            url = f"{self.base_url}/search/"
            
            query_params = {
                "apikey": self.api_key,
                "from": params.from_station,
                "to": params.to_station,
                "date": params.date,
                "format": "json",
                "lang": "ru_RU"
            }
            
            if params.transport_type:
                query_params["transport_types"] = params.transport_type
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=query_params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            
            # Обрабатываем результаты
            segments = data.get("segments", [])
            
            if not segments:
                return {
                    "success": True,
                    "found": False,
                    "message": f"Рейсы из {params.from_station} в {params.to_station} на {params.date} не найдены",
                    "from": params.from_station,
                    "to": params.to_station,
                    "date": params.date
                }
            
            # Форматируем результаты
            flights = []
            for segment in segments[:10]:  # Берем первые 10 рейсов
                flight_info = {
                    "departure": segment.get("departure"),
                    "arrival": segment.get("arrival"),
                    "duration": segment.get("duration"),
                    "carrier": segment.get("thread", {}).get("carrier", {}).get("title"),
                    "number": segment.get("thread", {}).get("number"),
                    "title": segment.get("thread", {}).get("title"),
                    "transport_type": segment.get("thread", {}).get("transport_type")
                }
                flights.append(flight_info)
            
            return {
                "success": True,
                "found": True,
                "count": len(flights),
                "total_found": len(segments),
                "from": params.from_station,
                "to": params.to_station,
                "date": params.date,
                "flights": flights,
                "message": self._format_message(flights, params)
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
    
    def _format_message(self, flights: List[Dict], params: FlightScheduleTool) -> str:
        """
        Форматировать сообщение с результатами поиска.
        
        Args:
            flights: Список найденных рейсов.
            params: Параметры поиска.
            
        Returns:
            Отформатированное сообщение.
        """
        if not flights:
            return f"Рейсы из {params.from_station} в {params.to_station} на {params.date} не найдены"
        
        message_parts = [
            f"Найдено {len(flights)} рейсов из {params.from_station} в {params.to_station} на {params.date}:\n"
        ]
        
        for i, flight in enumerate(flights[:5], 1):  # Показываем первые 5
            carrier = flight.get("carrier", "")
            number = flight.get("number", "")
            departure = flight.get("departure", "")
            arrival = flight.get("arrival", "")
            duration = flight.get("duration", 0)
            
            # Форматируем время
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            duration_str = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
            
            message_parts.append(
                f"{i}. {carrier} {number}: {departure} → {arrival} ({duration_str})"
            )
        
        if len(flights) > 5:
            message_parts.append(f"\n... и еще {len(flights) - 5} рейсов")
        
        return "\n".join(message_parts)
# END:flights_tool
