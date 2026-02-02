"""
Инструмент для поиска музыки в Яндекс.Музыке.
"""

from typing import Dict, Any, Type, List, Optional
import asyncio

from src.tools.base import Tool, BaseTool
from src.tools.schemas import SearchMusicTool
from src.core.config import MusicToolConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:music_tool
class MusicTool(Tool):
    """Инструмент для поиска музыки в Яндекс.Музыке."""
    
    # ANCHOR:music_tool_init
    def __init__(self, config: MusicToolConfig):
        """
        Инициализация инструмента.
        
        Args:
            config: Конфигурация инструмента.
        """
        self.config = config
        self.api_key = config.api_key
        self._client = None  # Ленивая инициализация
        
        if not self.api_key:
            logger.warning("Yandex Music API token not configured")
    # END:music_tool_init
    
    # ANCHOR:get_client
    def _get_client(self):
        """
        Получить или создать клиент Yandex Music.
        
        Returns:
            Инициализированный клиент Yandex Music.
            
        Raises:
            ValueError: Если токен не настроен.
        """
        if not self.api_key:
            raise ValueError("Yandex Music API token not configured")
        
        if self._client is None:
            from yandex_music import Client
            self._client = Client().init()
            logger.info("Yandex Music client initialized")
        
        return self._client
    # END:get_client
    
    @property
    def name(self) -> str:
        return "search_music"
    
    @property
    def description(self) -> str:
        return "Поиск треков, исполнителей и альбомов в Яндекс.Музыке."
    
    def get_schema(self) -> Type[BaseTool]:
        return SearchMusicTool
    
    # ANCHOR:music_execute
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        """
        Выполнить поиск музыки.
        
        Args:
            params: Параметры поиска (SearchMusicTool).
            
        Returns:
            Результаты поиска с информацией о треках/исполнителях/альбомах.
        """
        assert isinstance(params, SearchMusicTool)
        
        if not self.api_key:
            return {
                "success": False,
                "error": "api_key_not_configured",
                "message": "Для использования этого инструмента необходим токен Яндекс.Музыки"
            }
        
        logger.info(
            f"Searching music: query='{params.query}', "
            f"type={params.search_type}, limit={params.limit}"
        )
        
        try:
            # Получаем клиент
            client = self._get_client()
            
            # Выполняем поиск (синхронный вызов в executor)
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                lambda: client.search(params.query, type_=params.search_type)
            )
            
            # Обрабатываем результаты в зависимости от типа поиска
            if params.search_type == "track":
                return self._format_tracks_result(search_result, params)
            elif params.search_type == "artist":
                return self._format_artists_result(search_result, params)
            elif params.search_type == "album":
                return self._format_albums_result(search_result, params)
            else:
                return {
                    "success": False,
                    "error": "invalid_search_type",
                    "message": f"Неподдерживаемый тип поиска: {params.search_type}"
                }
                
        except Exception as e:
            logger.error(f"Error searching music: {e}", exc_info=True)
            
            # Специфичные ошибки
            error_message = "Произошла ошибка при поиске музыки"
            
            if "Unauthorized" in str(e) or "401" in str(e):
                error_message = "Неверный токен Яндекс.Музыки. Проверьте настройки."
            elif "Network" in str(e) or "Connection" in str(e):
                error_message = "Ошибка сети. Проверьте подключение к интернету."
            elif "timeout" in str(e).lower():
                error_message = "Превышено время ожидания ответа от Яндекс.Музыки."
            
            return {
                "success": False,
                "error": str(e),
                "message": error_message
            }
    # END:music_execute
    
    # ANCHOR:format_tracks
    def _format_tracks_result(
        self, 
        search_result, 
        params: SearchMusicTool
    ) -> Dict[str, Any]:
        """
        Форматировать результаты поиска треков.
        
        Args:
            search_result: Результат поиска от Yandex Music API.
            params: Параметры поиска.
            
        Returns:
            Отформатированный результат.
        """
        if not search_result.tracks or not search_result.tracks.results:
            return {
                "success": True,
                "found": False,
                "message": f"Треки по запросу '{params.query}' не найдены",
                "query": params.query,
                "search_type": params.search_type
            }
        
        # Ограничиваем количество результатов
        tracks = search_result.tracks.results[:params.limit]
        
        # Форматируем информацию о треках
        formatted_tracks = []
        for track in tracks:
            track_info = {
                "id": track.id,
                "title": track.title,
                "artists": [artist.name for artist in track.artists] if track.artists else [],
                "albums": [album.title for album in track.albums] if track.albums else [],
                "duration_ms": track.duration_ms,
                "duration_formatted": self._format_duration(track.duration_ms),
                "available": track.available if hasattr(track, 'available') else True
            }
            formatted_tracks.append(track_info)
        
        return {
            "success": True,
            "found": True,
            "count": len(formatted_tracks),
            "total_found": search_result.tracks.total if search_result.tracks.total else len(tracks),
            "query": params.query,
            "search_type": params.search_type,
            "tracks": formatted_tracks,
            "message": self._format_tracks_message(formatted_tracks, params.query)
        }
    # END:format_tracks
    
    # ANCHOR:format_artists
    def _format_artists_result(
        self, 
        search_result, 
        params: SearchMusicTool
    ) -> Dict[str, Any]:
        """
        Форматировать результаты поиска исполнителей.
        
        Args:
            search_result: Результат поиска от Yandex Music API.
            params: Параметры поиска.
            
        Returns:
            Отформатированный результат.
        """
        if not search_result.artists or not search_result.artists.results:
            return {
                "success": True,
                "found": False,
                "message": f"Исполнители по запросу '{params.query}' не найдены",
                "query": params.query,
                "search_type": params.search_type
            }
        
        # Ограничиваем количество результатов
        artists = search_result.artists.results[:params.limit]
        
        # Форматируем информацию об исполнителях
        formatted_artists = []
        for artist in artists:
            artist_info = {
                "id": artist.id,
                "name": artist.name,
                "genres": artist.genres if hasattr(artist, 'genres') else [],
                "tracks_count": artist.counts.tracks if hasattr(artist, 'counts') and artist.counts else 0,
                "albums_count": artist.counts.also_albums if hasattr(artist, 'counts') and artist.counts else 0
            }
            formatted_artists.append(artist_info)
        
        return {
            "success": True,
            "found": True,
            "count": len(formatted_artists),
            "total_found": search_result.artists.total if search_result.artists.total else len(artists),
            "query": params.query,
            "search_type": params.search_type,
            "artists": formatted_artists,
            "message": self._format_artists_message(formatted_artists, params.query)
        }
    # END:format_artists
    
    # ANCHOR:format_albums
    def _format_albums_result(
        self, 
        search_result, 
        params: SearchMusicTool
    ) -> Dict[str, Any]:
        """
        Форматировать результаты поиска альбомов.
        
        Args:
            search_result: Результат поиска от Yandex Music API.
            params: Параметры поиска.
            
        Returns:
            Отформатированный результат.
        """
        if not search_result.albums or not search_result.albums.results:
            return {
                "success": True,
                "found": False,
                "message": f"Альбомы по запросу '{params.query}' не найдены",
                "query": params.query,
                "search_type": params.search_type
            }
        
        # Ограничиваем количество результатов
        albums = search_result.albums.results[:params.limit]
        
        # Форматируем информацию об альбомах
        formatted_albums = []
        for album in albums:
            album_info = {
                "id": album.id,
                "title": album.title,
                "artists": [artist.name for artist in album.artists] if album.artists else [],
                "year": album.year if hasattr(album, 'year') else None,
                "track_count": album.track_count if hasattr(album, 'track_count') else 0,
                "genre": album.genre if hasattr(album, 'genre') else None
            }
            formatted_albums.append(album_info)
        
        return {
            "success": True,
            "found": True,
            "count": len(formatted_albums),
            "total_found": search_result.albums.total if search_result.albums.total else len(albums),
            "query": params.query,
            "search_type": params.search_type,
            "albums": formatted_albums,
            "message": self._format_albums_message(formatted_albums, params.query)
        }
    # END:format_albums
    
    # ANCHOR:format_duration
    def _format_duration(self, duration_ms: Optional[int]) -> str:
        """
        Форматировать длительность из миллисекунд в читаемый формат.
        
        Args:
            duration_ms: Длительность в миллисекундах.
            
        Returns:
            Отформатированная строка (например, "3:45").
        """
        if not duration_ms:
            return "0:00"
        
        seconds = duration_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        
        return f"{minutes}:{seconds:02d}"
    # END:format_duration
    
    # ANCHOR:format_tracks_message
    def _format_tracks_message(
        self, 
        tracks: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """
        Форматировать сообщение с результатами поиска треков.
        
        Args:
            tracks: Список найденных треков.
            query: Поисковый запрос.
            
        Returns:
            Отформатированное сообщение.
        """
        if not tracks:
            return f"Треки по запросу '{query}' не найдены"
        
        message_parts = [
            f"Найдено {len(tracks)} треков по запросу '{query}':\n"
        ]
        
        for i, track in enumerate(tracks[:5], 1):  # Показываем первые 5
            artists = ", ".join(track["artists"]) if track["artists"] else "Неизвестный исполнитель"
            duration = track["duration_formatted"]
            title = track["title"]
            
            message_parts.append(
                f"{i}. {artists} - {title} ({duration})"
            )
        
        if len(tracks) > 5:
            message_parts.append(f"\n... и ещё {len(tracks) - 5} треков")
        
        return "\n".join(message_parts)
    # END:format_tracks_message
    
    # ANCHOR:format_artists_message
    def _format_artists_message(
        self, 
        artists: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """
        Форматировать сообщение с результатами поиска исполнителей.
        
        Args:
            artists: Список найденных исполнителей.
            query: Поисковый запрос.
            
        Returns:
            Отформатированное сообщение.
        """
        if not artists:
            return f"Исполнители по запросу '{query}' не найдены"
        
        message_parts = [
            f"Найдено {len(artists)} исполнителей по запросу '{query}':\n"
        ]
        
        for i, artist in enumerate(artists[:5], 1):  # Показываем первых 5
            name = artist["name"]
            tracks_count = artist["tracks_count"]
            albums_count = artist["albums_count"]
            
            message_parts.append(
                f"{i}. {name} ({tracks_count} треков, {albums_count} альбомов)"
            )
        
        if len(artists) > 5:
            message_parts.append(f"\n... и ещё {len(artists) - 5} исполнителей")
        
        return "\n".join(message_parts)
    # END:format_artists_message
    
    # ANCHOR:format_albums_message
    def _format_albums_message(
        self, 
        albums: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """
        Форматировать сообщение с результатами поиска альбомов.
        
        Args:
            albums: Список найденных альбомов.
            query: Поисковый запрос.
            
        Returns:
            Отформатированное сообщение.
        """
        if not albums:
            return f"Альбомы по запросу '{query}' не найдены"
        
        message_parts = [
            f"Найдено {len(albums)} альбомов по запросу '{query}':\n"
        ]
        
        for i, album in enumerate(albums[:5], 1):  # Показываем первые 5
            title = album["title"]
            artists = ", ".join(album["artists"]) if album["artists"] else "Неизвестный исполнитель"
            year = album["year"] if album["year"] else "год неизвестен"
            track_count = album["track_count"]
            
            message_parts.append(
                f"{i}. {artists} - {title} ({year}, {track_count} треков)"
            )
        
        if len(albums) > 5:
            message_parts.append(f"\n... и ещё {len(albums) - 5} альбомов")
        
        return "\n".join(message_parts)
    # END:format_albums_message
# END:music_tool
