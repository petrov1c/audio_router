"""
Интеграционные тесты для инструмента поиска музыки.
Требуют реального токена Яндекс.Музыки.
"""

import pytest
import os
from src.tools.music import MusicTool
from src.tools.schemas import SearchMusicTool
from src.core.config import MusicToolConfig


# ANCHOR:integration_tests
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("YANDEX_MUSIC_TOKEN"),
    reason="YANDEX_MUSIC_TOKEN not set"
)
class TestMusicIntegration:
    """Интеграционные тесты с реальным API."""
    
    @pytest.fixture
    def music_tool(self):
        """Фикстура инструмента с реальной конфигурацией."""
        config = MusicToolConfig()
        return MusicTool(config)
    
    @pytest.mark.asyncio
    async def test_search_popular_track(self, music_tool):
        """Тест поиска популярного трека."""
        params = SearchMusicTool(
            tool="search_music",
            query="Виктор Цой Группа крови",
            search_type="track",
            limit=5
        )
        
        result = await music_tool.execute(params)
        
        assert result["success"] is True
        assert result["found"] is True
        assert result["count"] > 0
        assert "tracks" in result
        
        # Проверяем структуру первого трека
        if result["tracks"]:
            track = result["tracks"][0]
            assert "id" in track
            assert "title" in track
            assert "artists" in track
            assert "duration_formatted" in track
    
    @pytest.mark.asyncio
    async def test_search_artist(self, music_tool):
        """Тест поиска исполнителя."""
        params = SearchMusicTool(
            tool="search_music",
            query="Кино",
            search_type="artist",
            limit=5
        )
        
        result = await music_tool.execute(params)
        
        assert result["success"] is True
        assert result["found"] is True
        assert "artists" in result
        
        # Проверяем структуру первого исполнителя
        if result["artists"]:
            artist = result["artists"][0]
            assert "id" in artist
            assert "name" in artist
            assert "tracks_count" in artist
            assert "albums_count" in artist
    
    @pytest.mark.asyncio
    async def test_search_album(self, music_tool):
        """Тест поиска альбома."""
        params = SearchMusicTool(
            tool="search_music",
            query="Группа крови",
            search_type="album",
            limit=5
        )
        
        result = await music_tool.execute(params)
        
        assert result["success"] is True
        # Может не найти, это нормально
        assert "albums" in result or result["found"] is False
        
        # Если найдены альбомы, проверяем структуру
        if result.get("found") and result.get("albums"):
            album = result["albums"][0]
            assert "id" in album
            assert "title" in album
            assert "artists" in album
    
    @pytest.mark.asyncio
    async def test_search_nonexistent(self, music_tool):
        """Тест поиска несуществующего трека."""
        params = SearchMusicTool(
            tool="search_music",
            query="xyzabc123nonexistent456",
            search_type="track",
            limit=5
        )
        
        result = await music_tool.execute(params)
        
        assert result["success"] is True
        assert result["found"] is False
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_search_with_limit(self, music_tool):
        """Тест поиска с ограничением результатов."""
        params = SearchMusicTool(
            tool="search_music",
            query="Imagine Dragons",
            search_type="track",
            limit=3
        )
        
        result = await music_tool.execute(params)
        
        assert result["success"] is True
        if result["found"]:
            assert result["count"] <= 3
            assert len(result["tracks"]) <= 3
    
    @pytest.mark.asyncio
    async def test_search_english_query(self, music_tool):
        """Тест поиска с английским запросом."""
        params = SearchMusicTool(
            tool="search_music",
            query="The Beatles",
            search_type="artist",
            limit=5
        )
        
        result = await music_tool.execute(params)
        
        assert result["success"] is True
        # Может найти или не найти в зависимости от региона
        assert "artists" in result or result["found"] is False
    
    @pytest.mark.asyncio
    async def test_message_formatting(self, music_tool):
        """Тест форматирования сообщения."""
        params = SearchMusicTool(
            tool="search_music",
            query="Metallica",
            search_type="track",
            limit=5
        )
        
        result = await music_tool.execute(params)
        
        assert result["success"] is True
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0
# END:integration_tests
