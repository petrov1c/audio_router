"""
Unit-тесты для инструмента поиска музыки.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.tools.music import MusicTool
from src.tools.schemas import SearchMusicTool
from src.core.config import MusicToolConfig


# ANCHOR:test_music_tool_init
@pytest.fixture
def music_config():
    """Фикстура конфигурации."""
    config = MusicToolConfig()
    return config


@pytest.fixture
def music_tool(music_config):
    """Фикстура инструмента."""
    return MusicTool(music_config)


def test_music_tool_name(music_tool):
    """Тест имени инструмента."""
    assert music_tool.name == "search_music"


def test_music_tool_description(music_tool):
    """Тест описания инструмента."""
    assert "Поиск треков" in music_tool.description or "поиск" in music_tool.description.lower()


def test_music_tool_schema(music_tool):
    """Тест схемы инструмента."""
    schema = music_tool.get_schema()
    assert schema == SearchMusicTool
# END:test_music_tool_init


# ANCHOR:test_music_search_tracks
@pytest.mark.asyncio
async def test_search_tracks_success(music_tool):
    """Тест успешного поиска треков."""
    # Mock клиента
    mock_track = Mock()
    mock_track.id = "123"
    mock_track.title = "Test Track"
    mock_track.artists = [Mock(name="Test Artist")]
    mock_track.albums = [Mock(title="Test Album")]
    mock_track.duration_ms = 180000
    mock_track.available = True
    
    mock_search_result = Mock()
    mock_search_result.tracks = Mock()
    mock_search_result.tracks.results = [mock_track]
    mock_search_result.tracks.total = 1
    
    with patch.object(music_tool, '_get_client') as mock_get_client:
        mock_client = Mock()
        mock_client.search.return_value = mock_search_result
        mock_get_client.return_value = mock_client
        
        # Mock asyncio.get_event_loop().run_in_executor
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_search_result)
            
            params = SearchMusicTool(
                tool="search_music",
                query="test",
                search_type="track",
                limit=10
            )
            
            result = await music_tool.execute(params)
            
            assert result["success"] is True
            assert result["found"] is True
            assert result["count"] == 1
            assert len(result["tracks"]) == 1
            assert result["tracks"][0]["title"] == "Test Track"


@pytest.mark.asyncio
async def test_search_tracks_no_results(music_tool):
    """Тест поиска треков без результатов."""
    mock_search_result = Mock()
    mock_search_result.tracks = None
    
    with patch.object(music_tool, '_get_client') as mock_get_client:
        mock_client = Mock()
        mock_client.search.return_value = mock_search_result
        mock_get_client.return_value = mock_client
        
        # Mock asyncio.get_event_loop().run_in_executor
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_search_result)
            
            params = SearchMusicTool(
                tool="search_music",
                query="nonexistent",
                search_type="track",
                limit=10
            )
            
            result = await music_tool.execute(params)
            
            assert result["success"] is True
            assert result["found"] is False


@pytest.mark.asyncio
async def test_search_tracks_multiple_results(music_tool):
    """Тест поиска треков с несколькими результатами."""
    # Mock треков
    mock_tracks = []
    for i in range(3):
        mock_track = Mock()
        mock_track.id = f"track_{i}"
        mock_track.title = f"Track {i}"
        mock_track.artists = [Mock(name=f"Artist {i}")]
        mock_track.albums = [Mock(title=f"Album {i}")]
        mock_track.duration_ms = 180000 + i * 1000
        mock_track.available = True
        mock_tracks.append(mock_track)
    
    mock_search_result = Mock()
    mock_search_result.tracks = Mock()
    mock_search_result.tracks.results = mock_tracks
    mock_search_result.tracks.total = 3
    
    with patch.object(music_tool, '_get_client') as mock_get_client:
        mock_client = Mock()
        mock_client.search.return_value = mock_search_result
        mock_get_client.return_value = mock_client
        
        # Mock asyncio.get_event_loop().run_in_executor
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_search_result)
            
            params = SearchMusicTool(
                tool="search_music",
                query="test",
                search_type="track",
                limit=10
            )
            
            result = await music_tool.execute(params)
            
            assert result["success"] is True
            assert result["found"] is True
            assert result["count"] == 3
            assert len(result["tracks"]) == 3
# END:test_music_search_tracks


# ANCHOR:test_music_search_artists
@pytest.mark.asyncio
async def test_search_artists_success(music_tool):
    """Тест успешного поиска исполнителей."""
    # Mock исполнителя
    mock_artist = Mock()
    mock_artist.id = "artist_123"
    mock_artist.name = "Test Artist"
    mock_artist.genres = ["Rock", "Pop"]
    mock_artist.counts = Mock()
    mock_artist.counts.tracks = 100
    mock_artist.counts.albums = 10
    
    mock_search_result = Mock()
    mock_search_result.artists = Mock()
    mock_search_result.artists.results = [mock_artist]
    mock_search_result.artists.total = 1
    mock_search_result.tracks = None
    mock_search_result.albums = None
    
    with patch.object(music_tool, '_get_client') as mock_get_client:
        mock_client = Mock()
        mock_client.search.return_value = mock_search_result
        mock_get_client.return_value = mock_client
        
        # Mock asyncio.get_event_loop().run_in_executor
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_search_result)
            
            params = SearchMusicTool(
                tool="search_music",
                query="test artist",
                search_type="artist",
                limit=10
            )
            
            result = await music_tool.execute(params)
            
            assert result["success"] is True
            assert result["found"] is True
            assert result["count"] == 1
            assert len(result["artists"]) == 1
            assert result["artists"][0]["name"] == "Test Artist"
            assert result["artists"][0]["tracks_count"] == 100


@pytest.mark.asyncio
async def test_search_artists_no_results(music_tool):
    """Тест поиска исполнителей без результатов."""
    mock_search_result = Mock()
    mock_search_result.artists = None
    
    with patch.object(music_tool, '_get_client') as mock_get_client:
        mock_client = Mock()
        mock_client.search.return_value = mock_search_result
        mock_get_client.return_value = mock_client
        
        # Mock asyncio.get_event_loop().run_in_executor
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_search_result)
            
            params = SearchMusicTool(
                tool="search_music",
                query="nonexistent artist",
                search_type="artist",
                limit=10
            )
            
            result = await music_tool.execute(params)
            
            assert result["success"] is True
            assert result["found"] is False
# END:test_music_search_artists


# ANCHOR:test_music_search_albums
@pytest.mark.asyncio
async def test_search_albums_success(music_tool):
    """Тест успешного поиска альбомов."""
    # Mock альбома
    mock_album = Mock()
    mock_album.id = "album_123"
    mock_album.title = "Test Album"
    mock_album.artists = [Mock(name="Test Artist")]
    mock_album.year = 2020
    mock_album.track_count = 12
    mock_album.genre = "Rock"
    
    mock_search_result = Mock()
    mock_search_result.albums = Mock()
    mock_search_result.albums.results = [mock_album]
    mock_search_result.albums.total = 1
    mock_search_result.tracks = None
    mock_search_result.artists = None
    
    with patch.object(music_tool, '_get_client') as mock_get_client:
        mock_client = Mock()
        mock_client.search.return_value = mock_search_result
        mock_get_client.return_value = mock_client
        
        # Mock asyncio.get_event_loop().run_in_executor
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_search_result)
            
            params = SearchMusicTool(
                tool="search_music",
                query="test album",
                search_type="album",
                limit=10
            )
            
            result = await music_tool.execute(params)
            
            assert result["success"] is True
            assert result["found"] is True
            assert result["count"] == 1
            assert len(result["albums"]) == 1
            assert result["albums"][0]["title"] == "Test Album"
            assert result["albums"][0]["year"] == 2020
# END:test_music_search_albums


# ANCHOR:test_music_no_token
@pytest.mark.asyncio
async def test_search_without_token():
    """Тест поиска без токена."""
    config = MusicToolConfig()
    tool = MusicTool(config)
    
    with patch.dict('os.environ', {}, clear=True):
        # Пересоздаем инструмент без токена
        config = MusicToolConfig()
        tool = MusicTool(config)
        tool.api_key = None
        
        params = SearchMusicTool(
            tool="search_music",
            query="test",
            search_type="track",
            limit=10
        )
        
        result = await tool.execute(params)
        
        assert result["success"] is False
        assert "token" in result["message"].lower() or "токен" in result["message"].lower()
# END:test_music_no_token


# ANCHOR:test_format_duration
def test_format_duration(music_tool):
    """Тест форматирования длительности."""
    # 3 минуты 45 секунд
    assert music_tool._format_duration(225000) == "3:45"
    
    # 0 секунд
    assert music_tool._format_duration(0) == "0:00"
    
    # None
    assert music_tool._format_duration(None) == "0:00"
    
    # 1 минута 5 секунд
    assert music_tool._format_duration(65000) == "1:05"
    
    # 10 минут 0 секунд
    assert music_tool._format_duration(600000) == "10:00"
# END:test_format_duration


# ANCHOR:test_format_messages
def test_format_tracks_message(music_tool):
    """Тест форматирования сообщения о треках."""
    tracks = [
        {
            "title": "Track 1",
            "artists": ["Artist 1"],
            "duration_formatted": "3:45"
        },
        {
            "title": "Track 2",
            "artists": ["Artist 2", "Artist 3"],
            "duration_formatted": "4:20"
        }
    ]
    
    message = music_tool._format_tracks_message(tracks, "test query")
    
    assert "Найдено 2 треков" in message
    assert "test query" in message
    assert "Artist 1 - Track 1 (3:45)" in message
    assert "Artist 2, Artist 3 - Track 2 (4:20)" in message


def test_format_artists_message(music_tool):
    """Тест форматирования сообщения об исполнителях."""
    artists = [
        {
            "name": "Artist 1",
            "tracks_count": 100,
            "albums_count": 10
        },
        {
            "name": "Artist 2",
            "tracks_count": 50,
            "albums_count": 5
        }
    ]
    
    message = music_tool._format_artists_message(artists, "test query")
    
    assert "Найдено 2 исполнителей" in message
    assert "test query" in message
    assert "Artist 1 (100 треков, 10 альбомов)" in message
    assert "Artist 2 (50 треков, 5 альбомов)" in message


def test_format_albums_message(music_tool):
    """Тест форматирования сообщения об альбомах."""
    albums = [
        {
            "title": "Album 1",
            "artists": ["Artist 1"],
            "year": 2020,
            "track_count": 12
        },
        {
            "title": "Album 2",
            "artists": ["Artist 2"],
            "year": None,
            "track_count": 10
        }
    ]
    
    message = music_tool._format_albums_message(albums, "test query")
    
    assert "Найдено 2 альбомов" in message
    assert "test query" in message
    assert "Artist 1 - Album 1 (2020, 12 треков)" in message
    assert "Artist 2 - Album 2 (год неизвестен, 10 треков)" in message
# END:test_format_messages


# ANCHOR:test_invalid_search_type
@pytest.mark.asyncio
async def test_invalid_search_type(music_tool):
    """Тест с неподдерживаемым типом поиска."""
    mock_search_result = Mock()
    
    with patch.object(music_tool, '_get_client') as mock_get_client:
        mock_client = Mock()
        mock_client.search.return_value = mock_search_result
        mock_get_client.return_value = mock_client
        
        # Mock asyncio.get_event_loop().run_in_executor
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_search_result)
            
            params = SearchMusicTool(
                tool="search_music",
                query="test",
                search_type="invalid_type",
                limit=10
            )
            
            result = await music_tool.execute(params)
            
            assert result["success"] is False
            assert "invalid_search_type" in result["error"]
# END:test_invalid_search_type
