"""
Реестр аэропортов для поиска расписания авиарейсов.
Загружает список аэропортов из API Яндекс.Расписаний и кэширует локально.
"""

import json
import httpx
from typing import List, Optional, Dict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from rapidfuzz import fuzz

from src.core.config import FlightsToolConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:airport_model
@dataclass
class Airport:
    """Модель аэропорта."""
    code: str
    title: str
    settlement: str
    region: str
    country: str
    latitude: float
    longitude: float
    aliases: List[str] = field(default_factory=list)
    
    def matches(self, query: str) -> bool:
        """
        Проверить соответствие запросу.
        
        Args:
            query: Поисковый запрос.
            
        Returns:
            True если аэропорт соответствует запросу.
        """
        query_lower = query.lower().strip()
        
        # Точное совпадение
        if query_lower == self.settlement.lower():
            return True
        if query_lower == self.title.lower():
            return True
        
        # Проверка алиасов
        for alias in self.aliases:
            if query_lower == alias.lower():
                return True
        
        return False
    
    def similarity_score(self, query: str) -> float:
        """
        Вычислить степень соответствия запросу (0.0 - 1.0).
        
        Args:
            query: Поисковый запрос.
            
        Returns:
            Оценка соответствия от 0.0 до 1.0.
        """
        query_lower = query.lower().strip()
        
        # Точное совпадение - максимальный балл
        if self.matches(query):
            return 1.0
        
        # Вычисляем нечёткое соответствие для разных полей
        scores = [
            fuzz.ratio(query_lower, self.settlement.lower()) / 100.0,
            fuzz.ratio(query_lower, self.title.lower()) / 100.0,
        ]
        
        # Добавляем оценки для алиасов
        for alias in self.aliases:
            scores.append(fuzz.ratio(query_lower, alias.lower()) / 100.0)
        
        # Возвращаем максимальную оценку
        return max(scores)
# END:airport_model


# ANCHOR:airport_registry
class AirportRegistry:
    """Реестр аэропортов России."""
    
    def __init__(self, config: FlightsToolConfig):
        """
        Инициализация реестра.
        
        Args:
            config: Конфигурация инструмента.
        """
        self.config = config
        self.airports: List[Airport] = []
        self._by_code: Dict[str, Airport] = {}
        self._by_settlement: Dict[str, List[Airport]] = {}
        self._by_title: Dict[str, Airport] = {}
        self._loaded = False
    
    async def load_from_api(self) -> None:
        """Загрузить список станций из API Яндекс.Расписаний."""
        if not self.config.api_key:
            raise ValueError("Yandex Rasp API key not configured")
        
        logger.info("Loading stations from Yandex Rasp API...")
        
        url = f"{self.config.base_url}/stations_list/"
        params = {
            "apikey": self.config.api_key,
            "lang": "ru_RU",
            "format": "json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Парсим ответ и фильтруем только аэропорты России
        airports = []
        countries = data.get("countries", [])
        
        for country in countries:
            country_title = country.get("title", "")

            regions = country.get("regions", [])
            for region in regions:
                region_title = region.get("title", "")
                settlements = region.get("settlements", [])
                
                for settlement in settlements:
                    settlement_title = settlement.get("title", "")
                    stations = settlement.get("stations", [])
                    
                    for station in stations:
                        # Фильтруем только аэропорты (самолёты)
                        transport_type = station.get("transport_type", "")
                        if transport_type not in ("plane", "Самолёт"):
                            continue
                        
                        codes = station.get("codes", {})
                        yandex_code = codes.get("yandex_code")
                        
                        if not yandex_code:
                            continue
                        
                        # Создаём алиасы
                        station_title = station.get("title", "")
                        aliases = [settlement_title]
                        if station_title != settlement_title:
                            aliases.append(station_title)
                            aliases.append(f"{settlement_title} {station_title}")
                        
                        # Добавляем IATA код если есть
                        iata_code = codes.get("iata")
                        if iata_code:
                            aliases.append(iata_code)
                        
                        airport = Airport(
                            code=yandex_code,
                            title=station_title,
                            settlement=settlement_title,
                            region=region_title,
                            country=country_title,
                            latitude=station.get("latitude", 0.0),
                            longitude=station.get("longitude", 0.0),
                            aliases=aliases
                        )
                        airports.append(airport)
        
        self.airports = airports
        self._build_indexes()
        self._loaded = True
        
        logger.info(f"Loaded {len(self.airports)} airports from API")
    
    def load_from_cache(self) -> bool:
        """
        Загрузить из локального кэша.
        
        Returns:
            True если загрузка успешна, False если кэш не найден или невалиден.
        """
        cache_path = Path(self.config.cache_file)
        
        if not cache_path.exists():
            logger.info(f"Cache file not found: {cache_path}")
            return False
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Проверяем версию
            version = data.get("version", "1.0")
            if version != "1.0":
                logger.warning(f"Unsupported cache version: {version}")
                return False
            
            # Проверяем актуальность
            updated_at_str = data.get("updated_at")
            if updated_at_str:
                updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                age_days = (datetime.now(updated_at.tzinfo) - updated_at).days
                
                if age_days > self.config.cache_ttl_days:
                    logger.info(f"Cache is too old: {age_days} days > {self.config.cache_ttl_days} days")
                    return False
            
            # Загружаем аэропорты
            airports_data = data.get("airports", [])
            self.airports = [
                Airport(**airport_data) for airport_data in airports_data
            ]
            
            self._build_indexes()
            self._loaded = True
            
            logger.info(f"Loaded {len(self.airports)} airports from cache")
            return True
            
        except Exception as e:
            logger.error(f"Error loading cache: {e}", exc_info=True)
            return False
    
    def save_to_cache(self) -> None:
        """Сохранить в локальный кэш."""
        cache_path = Path(self.config.cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "airports": [asdict(airport) for airport in self.airports]
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(self.airports)} airports to cache: {cache_path}")
    
    def is_cache_valid(self) -> bool:
        """
        Проверить актуальность кэша.
        
        Returns:
            True если кэш существует и актуален.
        """
        cache_path = Path(self.config.cache_file)
        
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            updated_at_str = data.get("updated_at")
            if not updated_at_str:
                return False
            
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            age_days = (datetime.now(updated_at.tzinfo) - updated_at).days
            
            return age_days <= self.config.cache_ttl_days
            
        except Exception:
            return False
    
    async def ensure_loaded(self) -> None:
        """Убедиться что данные загружены (из кэша или API)."""
        if self._loaded:
            return
        
        # Пытаемся загрузить из кэша
        if self.load_from_cache():
            return
        
        # Если кэш не найден или невалиден - загружаем из API
        await self.load_from_api()
        
        # Сохраняем в кэш
        self.save_to_cache()
    
    def find_airport(self, query: str, prefer_main: bool = True) -> Optional[Airport]:
        """
        Найти аэропорт по названию города или аэропорта.
        
        Args:
            query: Название города или аэропорта.
            prefer_main: Если True и найдено несколько - выбрать первый.
            
        Returns:
            Найденный аэропорт или None.
        """
        airports = self.find_airports(query, limit=1)
        return airports[0] if airports else None
    
    def find_airports(self, query: str, limit: int = 5) -> List[Airport]:
        """
        Найти несколько подходящих аэропортов.
        
        Args:
            query: Название города или аэропорта.
            limit: Максимальное количество результатов.
            
        Returns:
            Список найденных аэропортов, отсортированных по релевантности.
        """
        if not self._loaded:
            logger.warning("Airport registry not loaded")
            return []
        
        query_lower = query.lower().strip()
        
        # 1. Точное совпадение по названию города
        if query_lower in self._by_settlement:
            return self._by_settlement[query_lower][:limit]
        
        # 2. Точное совпадение по названию аэропорта
        if query_lower in self._by_title:
            return [self._by_title[query_lower]]
        
        # 3. Поиск по алиасам и частичному совпадению
        matches = []
        for airport in self.airports:
            if airport.matches(query):
                matches.append((airport, 1.0))
        
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return [airport for airport, _ in matches[:limit]]
        
        # 4. Нечёткий поиск
        scored_airports = [
            (airport, airport.similarity_score(query))
            for airport in self.airports
        ]
        
        # Фильтруем по порогу и сортируем
        threshold = 0.6
        scored_airports = [
            (airport, score) for airport, score in scored_airports
            if score >= threshold
        ]
        scored_airports.sort(key=lambda x: x[1], reverse=True)
        
        return [airport for airport, _ in scored_airports[:limit]]
    
    def get_by_code(self, code: str) -> Optional[Airport]:
        """
        Получить аэропорт по коду.
        
        Args:
            code: Код аэропорта (yandex_code).
            
        Returns:
            Найденный аэропорт или None.
        """
        return self._by_code.get(code)
    
    def _build_indexes(self) -> None:
        """Построить индексы для быстрого поиска."""
        self._by_code = {}
        self._by_settlement = {}
        self._by_title = {}
        
        for airport in self.airports:
            # Индекс по коду
            self._by_code[airport.code] = airport
            
            # Индекс по названию города
            settlement_lower = airport.settlement.lower()
            if settlement_lower not in self._by_settlement:
                self._by_settlement[settlement_lower] = []
            self._by_settlement[settlement_lower].append(airport)
            
            # Индекс по названию аэропорта
            title_lower = airport.title.lower()
            if title_lower not in self._by_title:
                self._by_title[title_lower] = airport
# END:airport_registry
