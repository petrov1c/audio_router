"""
Перефразировщик текстов через LLM для исправления грамматических ошибок.
"""

import asyncio
import re
from typing import List, Optional, Dict
from pathlib import Path
import json


# ANCHOR:prompts
REPHRASE_PROMPT = """Ты - эксперт по русскому языку. Твоя задача - исправить грамматические ошибки и сделать текст естественным, сохраняя смысл.

Правила:
1. Исправь все грамматические ошибки (падежи, согласования, предлоги)
2. Сделай текст естественным и разговорным
3. Сохрани все ключевые слова и сущности (города, даты, названия)
4. НЕ добавляй новую информацию
5. НЕ удаляй важные детали
6. Сохрани относительные даты (завтра, послезавтра, через N дней)

Примеры:

Входной текст: "Найди рейсы из Москва в Санкт-Петербург на завтра"
Исправленный: "Найди рейсы из Москвы в Санкт-Петербург на завтра"

Входной текст: "Добавь встречу встреча с командой на понедельник"
Исправленный: "Добавь встречу с командой в понедельник"

Входной текст: "Что у меня запланировано на пятница"
Исправленный: "Что у меня запланировано на пятницу"

Входной текст: "Покажи самолёты из Сочи в Екатеринбург в пятницу"
Исправленный: "Покажи самолёты из Сочи в Екатеринбург в пятницу"

Входной текст: "Найди песню Виктор Цой"
Исправленный: "Найди песню Виктора Цоя"

Теперь исправь этот текст:
{text}

Верни ТОЛЬКО исправленный текст, без объяснений."""
# END:prompts


# ANCHOR:text_rephraser
class TextRephraser:
    """Перефразировщик текстов через LLM."""
    
    def __init__(
        self,
        llm_provider = None,
        cache_file: Optional[str] = None,
        use_cache: bool = True
    ):
        """
        Инициализация перефразировщика.
        
        Args:
            llm_provider: Провайдер LLM (должен иметь метод complete).
            cache_file: Путь к файлу кэша.
            use_cache: Использовать ли кэш.
        """
        self.llm = llm_provider
        self.use_cache = use_cache
        self.cache: Dict[str, str] = {}
        
        if cache_file:
            self.cache_file = Path(cache_file)
            self._load_cache()
        else:
            self.cache_file = None
    
    def _load_cache(self):
        """Загрузить кэш из файла."""
        if self.cache_file and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"✓ Загружен кэш: {len(self.cache)} записей")
            except Exception as e:
                print(f"⚠️  Ошибка загрузки кэша: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Сохранить кэш в файл."""
        if self.cache_file:
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️  Ошибка сохранения кэша: {e}")
    
    async def rephrase(self, text: str) -> str:
        """
        Перефразировать текст через LLM.
        
        Args:
            text: Исходный текст с возможными ошибками.
            
        Returns:
            Исправленный текст.
        """
        # Проверяем кэш
        if self.use_cache and text in self.cache:
            return self.cache[text]
        
        # Если нет LLM провайдера - возвращаем исходный текст
        if not self.llm:
            return text
        
        try:
            prompt = REPHRASE_PROMPT.format(text=text)
            
            # Вызываем LLM
            if hasattr(self.llm, 'complete'):
                response = await self.llm.complete(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.3  # Низкая температура для стабильности
                )
            elif hasattr(self.llm, 'chat'):
                # Альтернативный метод для chat-based API
                response = await self.llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
            else:
                # Fallback
                return text
            
            # Извлекаем текст из ответа
            if isinstance(response, dict):
                rephrased = response.get('text', response.get('content', text))
            else:
                rephrased = str(response)
            
            rephrased = rephrased.strip()
            
            # Сохраняем в кэш
            if self.use_cache:
                self.cache[text] = rephrased
            
            return rephrased
            
        except Exception as e:
            print(f"⚠️  Ошибка перефразирования: {e}")
            # Fallback: возвращаем исходный текст
            return text
    
    async def rephrase_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
        show_progress: bool = True
    ) -> List[str]:
        """
        Перефразировать тексты батчами.
        
        Args:
            texts: Список текстов.
            batch_size: Размер батча.
            show_progress: Показывать прогресс.
            
        Returns:
            Список перефразированных текстов.
        """
        results = []
        total = len(texts)
        
        for i in range(0, total, batch_size):
            batch = texts[i:i+batch_size]
            
            # Параллельная обработка батча
            tasks = [self.rephrase(text) for text in batch]
            batch_results = await asyncio.gather(*tasks)
            
            results.extend(batch_results)
            
            if show_progress:
                print(f"\rПерефразировано: {len(results)}/{total}", end="")
        
        if show_progress:
            print()  # Новая строка
        
        # Сохраняем кэш
        if self.use_cache:
            self._save_cache()
        
        return results
# END:text_rephraser


# ANCHOR:simple_rephraser
class SimpleRephraser:
    """Простой перефразировщик без LLM (правила)."""
    
    def __init__(self):
        """Инициализация."""
        # Словари склонений городов
        self.cities_genitive = {  # Родительный падеж (из кого? чего?)
            "Москва": "Москвы",
            "Санкт-Петербург": "Санкт-Петербурга",
            "Казань": "Казани",
            "Екатеринбург": "Екатеринбурга",
            "Новосибирск": "Новосибирска",
            "Сочи": "Сочи",
            "Владивосток": "Владивостока",
            "Калининград": "Калининграда",
            "Красноярск": "Красноярска",
            "Иркутск": "Иркутска",
            "Хабаровск": "Хабаровска",
            "Краснодар": "Краснодара",
            "Самара": "Самары",
            "Уфа": "Уфы",
            "Челябинск": "Челябинска",
            "Омск": "Омска",
            "Ростов-на-Дону": "Ростова-на-Дону",
            "Нижний Новгород": "Нижнего Новгорода",
            "Пермь": "Перми",
            "Воронеж": "Воронежа"
        }
        
        self.cities_accusative = {  # Винительный падеж (в кого? что?)
            "Москва": "Москву",
            "Санкт-Петербург": "Санкт-Петербург",
            "Казань": "Казань",
            "Екатеринбург": "Екатеринбург",
            "Новосибирск": "Новосибирск",
            "Сочи": "Сочи",
            "Владивосток": "Владивосток",
            "Калининград": "Калининград",
            "Красноярск": "Красноярск",
            "Иркутск": "Иркутск",
            "Хабаровск": "Хабаровск",
            "Краснодар": "Краснодар",
            "Самара": "Самару",
            "Уфа": "Уфу",
            "Челябинск": "Челябинск",
            "Омск": "Омск",
            "Ростов-на-Дону": "Ростов-на-Дону",
            "Нижний Новгород": "Нижний Новгород",
            "Пермь": "Пермь",
            "Воронеж": "Воронеж"
        }
    
    async def rephrase(self, text: str) -> str:
        """
        Перефразировать текст по правилам.
        
        Args:
            text: Исходный текст.
            
        Returns:
            Исправленный текст.
        """
        result = text
        
        # Исправляем города после "из" (родительный падеж)
        for city, genitive in self.cities_genitive.items():
            result = re.sub(
                rf'\bиз {city}\b',
                f'из {genitive}',
                result,
                flags=re.IGNORECASE
            )
        
        # Исправляем города после "в" (винительный падеж)
        for city, accusative in self.cities_accusative.items():
            result = re.sub(
                rf'\bв {city}\b',
                f'в {accusative}',
                result,
                flags=re.IGNORECASE
            )
        
        # Исправляем дни недели
        weekday_corrections = {
            r'\bна понедельник\b': 'в понедельник',
            r'\bна вторник\b': 'во вторник',
            r'\bна среда\b': 'в среду',
            r'\bна четверг\b': 'в четверг',
            r'\bна пятница\b': 'в пятницу',
            r'\bна суббота\b': 'в субботу',
            r'\bна воскресенье\b': 'в воскресенье',
        }
        
        for pattern, replacement in weekday_corrections.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    async def rephrase_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
        show_progress: bool = True
    ) -> List[str]:
        """Перефразировать батч текстов."""
        results = []
        for text in texts:
            results.append(await self.rephrase(text))
        return results
# END:simple_rephraser


# ANCHOR:main
async def main():
    """Тестирование перефразировщика."""
    print("="*60)
    print("ТЕСТИРОВАНИЕ ПЕРЕФРАЗИРОВЩИКА")
    print("="*60)
    
    # Используем простой перефразировщик (без LLM)
    rephraser = SimpleRephraser()
    
    test_texts = [
        "Найди рейсы из Москва в Санкт-Петербург на завтра",
        "Покажи самолёты из Сочи в Екатеринбург на пятница",
        "Добавь встречу на понедельник",
        "Что у меня запланировано на среда",
        "Найди рейсы из Владивосток в Москва через 3 дня",
        "Рейсы из Уфа в Калининград 2026-02-18",
        "Как добраться из Нижний Новгород в Казань завтра"
    ]
    
    print("\nПростой перефразировщик (правила):")
    for text in test_texts:
        rephrased = await rephraser.rephrase(text)
        if text != rephrased:
            print(f"\n  ❌ Исходный:      {text}")
            print(f"  ✅ Исправленный:  {rephrased}")
        else:
            print(f"\n  ✓ Без изменений:  {text}")
    
    print("\n" + "="*60)
    print("Для использования LLM перефразировщика:")
    print("  rephraser = TextRephraser(llm_provider=your_llm)")
    print("  result = await rephraser.rephrase(text)")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
# END:main
