"""
Модуль для парсинга относительных и абсолютных дат на русском и английском языках.
Поддерживает естественные выражения типа "завтра"/"tomorrow", "следующий понедельник"/"next monday", "через 3 дня"/"in 3 days".
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.core.logger import get_module_logger


logger = get_module_logger(__name__)


# ANCHOR:parsed_date
@dataclass
class ParsedDate:
    """Результат парсинга даты."""
    
    # Основная дата (для конкретных дат)
    date: Optional[str] = None  # YYYY-MM-DD
    
    # Период (для периодов типа "следующая неделя")
    date_from: Optional[str] = None  # YYYY-MM-DD
    date_to: Optional[str] = None    # YYYY-MM-DD
    
    # Метаданные
    is_period: bool = False
    original_text: str = ""
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if self.is_period:
            if not (self.date_from and self.date_to):
                raise ValueError("Period must have date_from and date_to")
        else:
            if not self.date:
                raise ValueError("Non-period must have date")
# END:parsed_date


# ANCHOR:date_parser
class DateParser:
    """Парсер относительных и абсолютных дат на русском и английском языках."""
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Инициализация парсера.
        
        Args:
            reference_date: Опорная дата (по умолчанию - сегодня).
        """
        self.reference_date = reference_date or datetime.now()
        
        # Словари для парсинга (русский + английский)
        self.weekdays = {
            # Русский
            "понедельник": 0, "пн": 0,
            "вторник": 1, "вт": 1,
            "среда": 2, "среду": 2, "ср": 2,
            "четверг": 3, "чт": 3,
            "пятница": 4, "пятницу": 4, "пт": 4,
            "суббота": 5, "субботу": 5, "сб": 5,
            "воскресенье": 6, "вс": 6,
            # Английский
            "monday": 0, "mon": 0,
            "tuesday": 1, "tue": 1, "tues": 1,
            "wednesday": 2, "wed": 2,
            "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
            "friday": 4, "fri": 4,
            "saturday": 5, "sat": 5,
            "sunday": 6, "sun": 6,
        }
        
        self.months = {
            # Русский
            "января": 1, "февраля": 2, "марта": 3,
            "апреля": 4, "мая": 5, "июня": 6,
            "июля": 7, "августа": 8, "сентября": 9,
            "октября": 10, "ноября": 11, "декабря": 12,
            # Английский
            "january": 1, "jan": 1,
            "february": 2, "feb": 2,
            "march": 3, "mar": 3,
            "april": 4, "apr": 4,
            "may": 5,
            "june": 6, "jun": 6,
            "july": 7, "jul": 7,
            "august": 8, "aug": 8,
            "september": 9, "sep": 9, "sept": 9,
            "october": 10, "oct": 10,
            "november": 11, "nov": 11,
            "december": 12, "dec": 12,
        }
        
        # Компилируем регулярные выражения
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Компилировать регулярные выражения для парсинга."""
        # Простые относительные даты (русский + английский)
        self.simple_relative = {
            # Русский
            re.compile(r"^сегодня$"): 0,
            re.compile(r"^завтра$"): 1,
            re.compile(r"^послезавтра$"): 2,
            re.compile(r"^вчера$"): -1,
            re.compile(r"^позавчера$"): -2,
            # Английский
            re.compile(r"^today$"): 0,
            re.compile(r"^tomorrow$"): 1,
            re.compile(r"^yesterday$"): -1,
        }
        
        # Дни недели (русский + английский)
        self.weekday_pattern = re.compile(
            r"^(следующий\s+|следующую\s+|next\s+|on\s+)?(в\s+)?"
            r"(понедельник|вторник|среда|среду|четверг|пятница|пятницу|суббота|субботу|воскресенье|"
            r"пн|вт|ср|чт|пт|сб|вс|"
            r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)$"
        )
        
        # Периоды недель (русский + английский)
        self.week_period_pattern = re.compile(
            r"^(эта|эту|следующая|следующую|this|next)\s+(недел[яюе]|week)$"
        )
        self.weeks_offset_pattern = re.compile(
            r"^(через|in)\s+(\d+)\s+(недел[иьюя]|weeks?)$"
        )
        self.week_offset_single_pattern = re.compile(
            r"^(через|in)\s+(a\s+)?(недел[юу]|week)$"
        )
        
        # Периоды месяцев (русский + английский)
        self.month_period_pattern = re.compile(
            r"^(этот|следующий|this|next)\s+(месяц|month)$"
        )
        
        # Смещения (русский + английский)
        self.days_offset_pattern = re.compile(
            r"^(через|in)\s+(\d+)\s+(день|дня|дней|days?)$"
        )
        self.months_offset_pattern = re.compile(
            r"^(через|in)\s+(\d+)\s+(месяц[аев]?|months?)$"
        )
        self.month_offset_single_pattern = re.compile(
            r"^(через|in)\s+(a\s+)?(месяц|month)$"
        )
        
        # Абсолютные даты
        self.date_iso_pattern = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
        self.date_dot_pattern = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$")
        self.date_slash_pattern = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$")
        # Русский формат
        self.date_text_ru_pattern = re.compile(
            r"^(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|"
            r"июля|августа|сентября|октября|ноября|декабря)(\s+(\d{4}))?$"
        )
        # Английский формат
        self.date_text_en_pattern = re.compile(
            r"^(january|february|march|april|may|june|july|august|september|october|november|december|"
            r"jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})(st|nd|rd|th)?(,?\s+(\d{4}))?$"
        )
    
    def parse(self, text: str) -> ParsedDate:
        """
        Распарсить дату из текста.
        
        Args:
            text: Текстовое представление даты.
            
        Returns:
            ParsedDate с распарсенной датой или периодом.
            
        Raises:
            ValueError: Если дату не удалось распарсить.
        """
        original_text = text
        text = text.lower().strip()
        
        logger.debug(f"Parsing date: '{text}'")
        
        # Пробуем разные парсеры по очереди
        parsers = [
            self._parse_simple_relative,
            self._parse_weekday,
            self._parse_week_period,
            self._parse_month_period,
            self._parse_offset,
            self._parse_absolute,
        ]
        
        for parser in parsers:
            try:
                result = parser(text)
                if result:
                    result.original_text = original_text
                    logger.debug(f"Parsed '{text}' as {result}")
                    return result
            except Exception as e:
                logger.debug(f"Parser {parser.__name__} failed: {e}")
                continue
        
        raise ValueError(f"Не удалось распарсить дату: {text}")
    
    def _parse_simple_relative(self, text: str) -> Optional[ParsedDate]:
        """
        Парсинг простых относительных дат: сегодня, завтра, послезавтра.
        
        Args:
            text: Текст для парсинга.
            
        Returns:
            ParsedDate или None.
        """
        for pattern, offset in self.simple_relative.items():
            if pattern.match(text):
                target_date = self.reference_date + timedelta(days=offset)
                return ParsedDate(
                    date=target_date.strftime("%Y-%m-%d"),
                    is_period=False
                )
        return None
    
    def _parse_weekday(self, text: str) -> Optional[ParsedDate]:
        """
        Парсинг дней недели: понедельник/monday, следующий вторник/next tuesday, в пятницу/on friday.
        
        Args:
            text: Текст для парсинга.
            
        Returns:
            ParsedDate или None.
        """
        match = self.weekday_pattern.match(text)
        if not match:
            return None
        
        prefix = match.group(1)  # "следующий", "next", "on", etc.
        is_next = prefix and ("следующ" in prefix or "next" in prefix)
        weekday_name = match.group(3)
        
        # Получаем номер дня недели (0 = понедельник)
        target_weekday = self.weekdays.get(weekday_name)
        if target_weekday is None:
            return None
        
        # Текущий день недели
        current_weekday = self.reference_date.weekday()
        
        # Вычисляем смещение
        if is_next:
            # "следующий понедельник" - всегда следующая неделя
            days_ahead = (target_weekday - current_weekday) % 7
            if days_ahead == 0:
                days_ahead = 7
            else:
                # Если день еще не прошел на этой неделе, берем следующую
                days_ahead += 7
        else:
            # "понедельник" или "в понедельник"
            days_ahead = (target_weekday - current_weekday) % 7
            if days_ahead == 0:
                # Если сегодня понедельник и говорят "понедельник" - следующий
                days_ahead = 7
        
        target_date = self.reference_date + timedelta(days=days_ahead)
        return ParsedDate(
            date=target_date.strftime("%Y-%m-%d"),
            is_period=False
        )
    
    def _parse_week_period(self, text: str) -> Optional[ParsedDate]:
        """
        Парсинг периодов недель: эта неделя/this week, следующая неделя/next week.
        
        Args:
            text: Текст для парсинга.
            
        Returns:
            ParsedDate или None.
        """
        # Проверяем "эта/следующая неделя" или "this/next week"
        match = self.week_period_pattern.match(text)
        if match:
            period_type = match.group(1)
            
            # Находим понедельник текущей недели
            current_weekday = self.reference_date.weekday()
            monday_offset = -current_weekday
            current_monday = self.reference_date + timedelta(days=monday_offset)
            
            if period_type in ["эта", "эту", "this"]:
                # Эта неделя: от понедельника до воскресенья
                week_start = current_monday
                week_end = current_monday + timedelta(days=6)
            else:  # "следующая", "следующую", "next"
                # Следующая неделя
                week_start = current_monday + timedelta(days=7)
                week_end = week_start + timedelta(days=6)
            
            return ParsedDate(
                date_from=week_start.strftime("%Y-%m-%d"),
                date_to=week_end.strftime("%Y-%m-%d"),
                is_period=True
            )
        
        # Проверяем "через N недель" или "in N weeks"
        match = self.weeks_offset_pattern.match(text)
        if match:
            weeks = int(match.group(2))
            
            # Находим понедельник через N недель
            current_weekday = self.reference_date.weekday()
            monday_offset = -current_weekday + (weeks * 7)
            week_start = self.reference_date + timedelta(days=monday_offset)
            week_end = week_start + timedelta(days=6)
            
            return ParsedDate(
                date_from=week_start.strftime("%Y-%m-%d"),
                date_to=week_end.strftime("%Y-%m-%d"),
                is_period=True
            )
        
        # Проверяем "через неделю" или "in a week"
        match = self.week_offset_single_pattern.match(text)
        if match:
            # Находим понедельник через 1 неделю
            current_weekday = self.reference_date.weekday()
            monday_offset = -current_weekday + 7
            week_start = self.reference_date + timedelta(days=monday_offset)
            week_end = week_start + timedelta(days=6)
            
            return ParsedDate(
                date_from=week_start.strftime("%Y-%m-%d"),
                date_to=week_end.strftime("%Y-%m-%d"),
                is_period=True
            )
        
        return None
    
    def _parse_month_period(self, text: str) -> Optional[ParsedDate]:
        """
        Парсинг периодов месяцев: этот месяц/this month, следующий месяц/next month.
        
        Args:
            text: Текст для парсинга.
            
        Returns:
            ParsedDate или None.
        """
        match = self.month_period_pattern.match(text)
        if not match:
            return None
        
        period_type = match.group(1)
        
        if period_type in ["этот", "this"]:
            # Этот месяц: с 1-го числа до последнего дня
            year = self.reference_date.year
            month = self.reference_date.month
        else:  # "следующий", "next"
            # Следующий месяц
            if self.reference_date.month == 12:
                year = self.reference_date.year + 1
                month = 1
            else:
                year = self.reference_date.year
                month = self.reference_date.month + 1
        
        # Первый день месяца
        month_start = datetime(year, month, 1)
        
        # Последний день месяца
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        month_end = next_month - timedelta(days=1)
        
        return ParsedDate(
            date_from=month_start.strftime("%Y-%m-%d"),
            date_to=month_end.strftime("%Y-%m-%d"),
            is_period=True
        )
    
    def _parse_offset(self, text: str) -> Optional[ParsedDate]:
        """
        Парсинг смещений: через 3 дня/in 3 days, через 2 недели/in 2 weeks, через месяц/in a month.
        
        Args:
            text: Текст для парсинга.
            
        Returns:
            ParsedDate или None.
        """
        # Через N дней / in N days
        match = self.days_offset_pattern.match(text)
        if match:
            days = int(match.group(2))
            target_date = self.reference_date + timedelta(days=days)
            return ParsedDate(
                date=target_date.strftime("%Y-%m-%d"),
                is_period=False
            )
        
        # Через N месяцев / in N months
        match = self.months_offset_pattern.match(text)
        if match:
            months = int(match.group(2))
            
            # Вычисляем новый месяц и год
            new_month = self.reference_date.month + months
            new_year = self.reference_date.year
            
            while new_month > 12:
                new_month -= 12
                new_year += 1
            
            # Создаем дату (может быть проблема с днем месяца)
            try:
                target_date = datetime(new_year, new_month, self.reference_date.day)
            except ValueError:
                # Если день не существует в новом месяце (например, 31 февраля)
                # Берем последний день месяца
                if new_month == 12:
                    next_month = datetime(new_year + 1, 1, 1)
                else:
                    next_month = datetime(new_year, new_month + 1, 1)
                target_date = next_month - timedelta(days=1)
            
            return ParsedDate(
                date=target_date.strftime("%Y-%m-%d"),
                is_period=False
            )
        
        # Через месяц (единственное число)
        match = self.month_offset_single_pattern.match(text)
        if match:
            # Вычисляем новый месяц и год
            new_month = self.reference_date.month + 1
            new_year = self.reference_date.year
            
            if new_month > 12:
                new_month = 1
                new_year += 1
            
            # Создаем дату (может быть проблема с днем месяца)
            try:
                target_date = datetime(new_year, new_month, self.reference_date.day)
            except ValueError:
                # Если день не существует в новом месяце (например, 31 февраля)
                # Берем последний день месяца
                if new_month == 12:
                    next_month = datetime(new_year + 1, 1, 1)
                else:
                    next_month = datetime(new_year, new_month + 1, 1)
                target_date = next_month - timedelta(days=1)
            
            return ParsedDate(
                date=target_date.strftime("%Y-%m-%d"),
                is_period=False
            )
        
        return None
    
    def _parse_absolute(self, text: str) -> Optional[ParsedDate]:
        """
        Парсинг абсолютных дат: 2026-02-15, 15.02.2026, 15 февраля, February 15.
        
        Args:
            text: Текст для парсинга.
            
        Returns:
            ParsedDate или None.
        """
        # Формат YYYY-MM-DD
        match = self.date_iso_pattern.match(text)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                date = datetime(year, month, day)
                return ParsedDate(
                    date=date.strftime("%Y-%m-%d"),
                    is_period=False
                )
            except ValueError:
                return None
        
        # Формат DD.MM.YYYY или DD.MM.YY
        match = self.date_dot_pattern.match(text)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            
            # Если год двузначный, добавляем 2000
            if year < 100:
                year += 2000
            
            try:
                date = datetime(year, month, day)
                return ParsedDate(
                    date=date.strftime("%Y-%m-%d"),
                    is_period=False
                )
            except ValueError:
                return None
        
        # Формат MM/DD/YYYY или MM/DD/YY (американский)
        match = self.date_slash_pattern.match(text)
        if match:
            month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            
            # Если год двузначный, добавляем 2000
            if year < 100:
                year += 2000
            
            try:
                date = datetime(year, month, day)
                return ParsedDate(
                    date=date.strftime("%Y-%m-%d"),
                    is_period=False
                )
            except ValueError:
                return None
        
        # Формат "15 февраля" или "15 февраля 2026" (русский)
        match = self.date_text_ru_pattern.match(text)
        if match:
            day = int(match.group(1))
            month_name = match.group(2)
            year_str = match.group(4)
            
            month = self.months.get(month_name)
            if month is None:
                return None
            
            # Если год не указан, используем текущий или следующий
            if year_str:
                year = int(year_str)
            else:
                year = self.reference_date.year
                # Если дата уже прошла в этом году, берем следующий год
                try:
                    date = datetime(year, month, day)
                    if date < self.reference_date:
                        year += 1
                except ValueError:
                    pass
            
            try:
                date = datetime(year, month, day)
                return ParsedDate(
                    date=date.strftime("%Y-%m-%d"),
                    is_period=False
                )
            except ValueError:
                return None
        
        # Формат "February 15" или "February 15, 2026" (английский)
        match = self.date_text_en_pattern.match(text)
        if match:
            month_name = match.group(1)
            day = int(match.group(2))
            year_str = match.group(5)
            
            month = self.months.get(month_name)
            if month is None:
                return None
            
            # Если год не указан, используем текущий или следующий
            if year_str:
                year = int(year_str)
            else:
                year = self.reference_date.year
                # Если дата уже прошла в этом году, берем следующий год
                try:
                    date = datetime(year, month, day)
                    if date < self.reference_date:
                        year += 1
                except ValueError:
                    pass
            
            try:
                date = datetime(year, month, day)
                return ParsedDate(
                    date=date.strftime("%Y-%m-%d"),
                    is_period=False
                )
            except ValueError:
                return None
        
        return None
# END:date_parser
