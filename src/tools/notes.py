"""
Инструмент для работы с заметками.
"""

from typing import Dict, Any, Type, List
from pathlib import Path
import json
from datetime import datetime

from src.tools.base import Tool, BaseTool
from src.tools.schemas import CreateNoteTool, SearchNotesTool
from src.core.config import NotesToolConfig
from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:notes_base
class NotesBaseTool(Tool):
    """Базовый класс для инструментов заметок."""
    
    def __init__(self, config: NotesToolConfig):
        self.config = config
        self.storage_path = config.full_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_note_path(self, note_id: str) -> Path:
        return self.storage_path / f"{note_id}.json"
    
    def _save_note(self, title: str, content: str) -> str:
        note_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        with open(self._get_note_path(note_id), 'w', encoding='utf-8') as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
        return note_id
    
    def _search_notes(self, query: str) -> List[Dict]:
        results = []
        for note_file in self.storage_path.glob("*.json"):
            with open(note_file, 'r', encoding='utf-8') as f:
                note = json.load(f)
                if query.lower() in note['title'].lower() or query.lower() in note['content'].lower():
                    results.append(note)
        return results
# END:notes_base


# ANCHOR:create_note_tool
class CreateNoteToolImpl(NotesBaseTool):
    @property
    def name(self) -> str:
        return "create_note"
    
    @property
    def description(self) -> str:
        return "Создать текстовую заметку с заголовком и содержимым."
    
    def get_schema(self) -> Type[BaseTool]:
        return CreateNoteTool
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        assert isinstance(params, CreateNoteTool)
        try:
            note_id = self._save_note(params.title, params.content)
            return {
                "success": True,
                "note_id": note_id,
                "message": f"Заметка '{params.title}' создана"
            }
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return {"success": False, "error": str(e)}
# END:create_note_tool


# ANCHOR:search_notes_tool
class SearchNotesToolImpl(NotesBaseTool):
    @property
    def name(self) -> str:
        return "search_notes"
    
    @property
    def description(self) -> str:
        return "Поиск заметок по заголовку или содержимому."
    
    def get_schema(self) -> Type[BaseTool]:
        return SearchNotesTool
    
    async def execute(self, params: BaseTool) -> Dict[str, Any]:
        assert isinstance(params, SearchNotesTool)
        try:
            results = self._search_notes(params.query)
            return {
                "success": True,
                "count": len(results),
                "notes": results,
                "message": f"Найдено заметок: {len(results)}"
            }
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return {"success": False, "error": str(e)}
# END:search_notes_tool
