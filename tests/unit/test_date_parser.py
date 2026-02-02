"""
Тесты для модуля парсинга дат.
"""

import pytest
from datetime import datetime

from src.tools.date_parser import DateParser, ParsedDate


# ANCHOR:test_fixtures
@pytest.fixture
def parser():
    """Создать парсер с фиксированной опорной датой."""
    # Понедельник, 2 февраля 2026
    reference_date = datetime(2026, 2, 2, 12, 0, 0)
    return DateParser(reference_date=reference_date)
# END:test_fixtures


# ANCHOR:test_simple_relative
class TestSimpleRelative:
    """Тесты для простых относительных дат."""
    
    def test_today(self, parser):
        """Тест парсинга 'сегодня'."""
        result = parser.parse("сегодня")
        assert result.date == "2026-02-02"
        assert not result.is_period
    
    def test_tomorrow(self, parser):
        """Тест парсинга 'завтра'."""
        result = parser.parse("завтра")
        assert result.date == "2026-02-03"
        assert not result.is_period
    
    def test_day_after_tomorrow(self, parser):
        """Тест парсинга 'послезавтра'."""
        result = parser.parse("послезавтра")
        assert result.date == "2026-02-04"
        assert not result.is_period
    
    def test_yesterday(self, parser):
        """Тест парсинга 'вчера'."""
        result = parser.parse("вчера")
        assert result.date == "2026-02-01"
        assert not result.is_period
    
    def test_day_before_yesterday(self, parser):
        """Тест парсинга 'позавчера'."""
        result = parser.parse("позавчера")
        assert result.date == "2026-01-31"
        assert not result.is_period
# END:test_simple_relative


# ANCHOR:test_weekdays
class TestWeekdays:
    """Тесты для дней недели."""
    
    def test_monday(self, parser):
        """Тест парсинга 'понедельник' (сегодня понедельник -> следующий)."""
        result = parser.parse("понедельник")
        assert result.date == "2026-02-09"  # Следующий понедельник
        assert not result.is_period
    
    def test_tuesday(self, parser):
        """Тест парсинга 'вторник' (завтра)."""
        result = parser.parse("вторник")
        assert result.date == "2026-02-03"  # Завтра
        assert not result.is_period
    
    def test_wednesday(self, parser):
        """Тест парсинга 'среда'."""
        result = parser.parse("среда")
        assert result.date == "2026-02-04"
        assert not result.is_period
    
    def test_friday_with_preposition(self, parser):
        """Тест парсинга 'в пятницу'."""
        result = parser.parse("в пятницу")
        assert result.date == "2026-02-06"
        assert not result.is_period
    
    def test_next_monday(self, parser):
        """Тест парсинга 'следующий понедельник'."""
        result = parser.parse("следующий понедельник")
        assert result.date == "2026-02-09"
        assert not result.is_period
    
    def test_next_thursday(self, parser):
        """Тест парсинга 'следующий четверг'."""
        result = parser.parse("следующий четверг")
        assert result.date == "2026-02-12"  # Следующая неделя
        assert not result.is_period
    
    def test_saturday(self, parser):
        """Тест парсинга 'суббота'."""
        result = parser.parse("суббота")
        assert result.date == "2026-02-07"
        assert not result.is_period
    
    def test_sunday(self, parser):
        """Тест парсинга 'воскресенье'."""
        result = parser.parse("воскресенье")
        assert result.date == "2026-02-08"
        assert not result.is_period
# END:test_weekdays


# ANCHOR:test_week_periods
class TestWeekPeriods:
    """Тесты для периодов недель."""
    
    def test_this_week(self, parser):
        """Тест парсинга 'эта неделя'."""
        result = parser.parse("эта неделя")
        assert result.is_period
        assert result.date_from == "2026-02-02"  # Понедельник
        assert result.date_to == "2026-02-08"    # Воскресенье
    
    def test_next_week(self, parser):
        """Тест парсинга 'следующая неделя'."""
        result = parser.parse("следующая неделя")
        assert result.is_period
        assert result.date_from == "2026-02-09"
        assert result.date_to == "2026-02-15"
    
    def test_in_2_weeks(self, parser):
        """Тест парсинга 'через 2 недели'."""
        result = parser.parse("через 2 недели")
        assert result.is_period
        assert result.date_from == "2026-02-16"
        assert result.date_to == "2026-02-22"
    
    def test_in_1_week(self, parser):
        """Тест парсинга 'через неделю'."""
        result = parser.parse("через неделю")
        assert result.is_period
        assert result.date_from == "2026-02-09"
        assert result.date_to == "2026-02-15"
# END:test_week_periods


# ANCHOR:test_month_periods
class TestMonthPeriods:
    """Тесты для периодов месяцев."""
    
    def test_this_month(self, parser):
        """Тест парсинга 'этот месяц'."""
        result = parser.parse("этот месяц")
        assert result.is_period
        assert result.date_from == "2026-02-01"
        assert result.date_to == "2026-02-28"
    
    def test_next_month(self, parser):
        """Тест парсинга 'следующий месяц'."""
        result = parser.parse("следующий месяц")
        assert result.is_period
        assert result.date_from == "2026-03-01"
        assert result.date_to == "2026-03-31"
# END:test_month_periods


# ANCHOR:test_offsets
class TestOffsets:
    """Тесты для смещений."""
    
    def test_in_3_days(self, parser):
        """Тест парсинга 'через 3 дня'."""
        result = parser.parse("через 3 дня")
        assert result.date == "2026-02-05"
        assert not result.is_period
    
    def test_in_1_day(self, parser):
        """Тест парсинга 'через 1 день'."""
        result = parser.parse("через 1 день")
        assert result.date == "2026-02-03"
        assert not result.is_period
    
    def test_in_7_days(self, parser):
        """Тест парсинга 'через 7 дней'."""
        result = parser.parse("через 7 дней")
        assert result.date == "2026-02-09"
        assert not result.is_period
    
    def test_in_1_month(self, parser):
        """Тест парсинга 'через месяц'."""
        result = parser.parse("через месяц")
        assert result.date == "2026-03-02"
        assert not result.is_period
    
    def test_in_2_months(self, parser):
        """Тест парсинга 'через 2 месяца'."""
        result = parser.parse("через 2 месяца")
        assert result.date == "2026-04-02"
        assert not result.is_period
# END:test_offsets


# ANCHOR:test_absolute_dates
class TestAbsoluteDates:
    """Тесты для абсолютных дат."""
    
    def test_iso_format(self, parser):
        """Тест парсинга формата YYYY-MM-DD."""
        result = parser.parse("2026-02-15")
        assert result.date == "2026-02-15"
        assert not result.is_period
    
    def test_dot_format(self, parser):
        """Тест парсинга формата DD.MM.YYYY."""
        result = parser.parse("15.02.2026")
        assert result.date == "2026-02-15"
        assert not result.is_period
    
    def test_dot_format_short_year(self, parser):
        """Тест парсинга формата DD.MM.YY."""
        result = parser.parse("15.02.26")
        assert result.date == "2026-02-15"
        assert not result.is_period
    
    def test_text_format(self, parser):
        """Тест парсинга формата 'DD месяц'."""
        result = parser.parse("15 февраля")
        assert result.date == "2026-02-15"
        assert not result.is_period
    
    def test_text_format_with_year(self, parser):
        """Тест парсинга формата 'DD месяц YYYY'."""
        result = parser.parse("15 марта 2026")
        assert result.date == "2026-03-15"
        assert not result.is_period
    
    def test_text_format_past_date_next_year(self, parser):
        """Тест парсинга даты которая уже прошла (должен взять следующий год)."""
        result = parser.parse("1 января")
        # 1 января 2026 уже прошло, должен взять 2027
        assert result.date == "2027-01-01"
        assert not result.is_period
# END:test_absolute_dates


# ANCHOR:test_edge_cases
class TestEdgeCases:
    """Тесты для граничных случаев."""
    
    def test_invalid_date(self, parser):
        """Тест парсинга некорректной даты."""
        with pytest.raises(ValueError):
            parser.parse("32 февраля")
    
    def test_unknown_format(self, parser):
        """Тест парсинга неизвестного формата."""
        with pytest.raises(ValueError):
            parser.parse("на днях")
    
    def test_empty_string(self, parser):
        """Тест парсинга пустой строки."""
        with pytest.raises(ValueError):
            parser.parse("")
    
    def test_case_insensitive(self, parser):
        """Тест что парсинг не зависит от регистра."""
        result1 = parser.parse("ЗАВТРА")
        result2 = parser.parse("Завтра")
        result3 = parser.parse("завтра")
        
        assert result1.date == result2.date == result3.date
    
    def test_whitespace_handling(self, parser):
        """Тест обработки пробелов."""
        result1 = parser.parse("  завтра  ")
        result2 = parser.parse("завтра")
        
        assert result1.date == result2.date
    
    def test_month_overflow(self, parser):
        """Тест смещения на месяц когда день не существует."""
        # 31 января + 1 месяц = 28 февраля (последний день)
        parser_jan = DateParser(reference_date=datetime(2026, 1, 31))
        result = parser_jan.parse("через месяц")
        assert result.date == "2026-02-28"
    
    def test_year_boundary(self, parser):
        """Тест перехода через границу года."""
        parser_dec = DateParser(reference_date=datetime(2025, 12, 31))
        result = parser_dec.parse("завтра")
        assert result.date == "2026-01-01"
# END:test_edge_cases


# ANCHOR:test_original_text
class TestOriginalText:
    """Тесты для сохранения оригинального текста."""
    
    def test_original_text_saved(self, parser):
        """Тест что оригинальный текст сохраняется."""
        result = parser.parse("Завтра")
        assert result.original_text == "Завтра"
    
    def test_original_text_with_period(self, parser):
        """Тест сохранения оригинального текста для периода."""
        result = parser.parse("Следующая неделя")
        assert result.original_text == "Следующая неделя"
# END:test_original_text


# ANCHOR:test_parsed_date_validation
class TestParsedDateValidation:
    """Тесты для валидации ParsedDate."""
    
    def test_period_must_have_dates(self):
        """Тест что период должен иметь date_from и date_to."""
        with pytest.raises(ValueError):
            ParsedDate(is_period=True, date_from="2026-02-01")
    
    def test_non_period_must_have_date(self):
        """Тест что не-период должен иметь date."""
        with pytest.raises(ValueError):
            ParsedDate(is_period=False, date_from="2026-02-01")
    
    def test_valid_period(self):
        """Тест валидного периода."""
        parsed = ParsedDate(
            is_period=True,
            date_from="2026-02-01",
            date_to="2026-02-28"
        )
        assert parsed.is_period
        assert parsed.date_from == "2026-02-01"
        assert parsed.date_to == "2026-02-28"
    
    def test_valid_date(self):
        """Тест валидной даты."""
        parsed = ParsedDate(
            is_period=False,
            date="2026-02-15"
        )
        assert not parsed.is_period
        assert parsed.date == "2026-02-15"
# END:test_parsed_date_validation
