"""
Конвертер дат в текстовое представление для TTS.
"""

import re
from datetime import datetime


# ANCHOR:date_to_text_converter
class DateToTextConverter:
    """Конвертер дат в текстовое представление для корректного озвучивания."""
    
    # Месяцы в родительном падеже
    MONTHS_GENITIVE = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    
    # Дни месяца в именительном падеже (среднего рода)
    DAYS = {
        1: "первое", 2: "второе", 3: "третье", 4: "четвёртое",
        5: "пятое", 6: "шестое", 7: "седьмое", 8: "восьмое",
        9: "девятое", 10: "десятое", 11: "одиннадцатое",
        12: "двенадцатое", 13: "тринадцатое", 14: "четырнадцатое",
        15: "пятнадцатое", 16: "шестнадцатое", 17: "семнадцатое",
        18: "восемнадцатое", 19: "девятнадцатое", 20: "двадцатое",
        21: "двадцать первое", 22: "двадцать второе",
        23: "двадцать третье", 24: "двадцать четвёртое",
        25: "двадцать пятое", 26: "двадцать шестое",
        27: "двадцать седьмое", 28: "двадцать восьмое",
        29: "двадцать девятое", 30: "тридцатое",
        31: "тридцать первое"
    }
    
    # Числа для конвертации в текст
    NUMBERS = {
        "1": "один", "2": "два", "3": "три", "4": "четыре",
        "5": "пять", "6": "шесть", "7": "семь", "8": "восемь",
        "9": "девять", "10": "десять", "11": "одиннадцать",
        "12": "двенадцать", "13": "тринадцать", "14": "четырнадцать",
        "15": "пятнадцать", "16": "шестнадцать", "17": "семнадцать",
        "18": "восемнадцать", "19": "девятнадцать", "20": "двадцать"
    }
    
    # Годы (для частых случаев)
    YEARS = {
        2026: "две тысячи двадцать шестого года",
        2027: "две тысячи двадцать седьмого года",
        2028: "две тысячи двадцать восьмого года",
        2029: "две тысячи двадцать девятого года",
        2030: "две тысячи тридцатого года"
    }
    
    def convert_date(
        self,
        date_str: str,
        include_year: bool = True,
        context: str = ""
    ) -> str:
        """
        Конвертировать дату в текст.
        
        Args:
            date_str: Дата в формате YYYY-MM-DD.
            include_year: Включать ли год.
            context: Контекст (для определения нужен ли год).
            
        Returns:
            Дата текстом.
        """
        try:
            # Парсим дату
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
            day = self.DAYS.get(date.day, str(date.day))
            month = self.MONTHS_GENITIVE.get(date.month, "")
            
            if include_year:
                year = self._year_to_text(date.year)
                return f"{day} {month} {year}"
            else:
                return f"{day} {month}"
        except Exception as e:
            # Fallback: возвращаем исходную строку
            return date_str
    
    def _year_to_text(self, year: int) -> str:
        """
        Конвертировать год в текст.
        
        Args:
            year: Год (например, 2026).
            
        Returns:
            Год текстом в родительном падеже.
        """
        # Используем предопределённые значения
        if year in self.YEARS:
            return self.YEARS[year]
        
        # Для других годов - упрощённая логика
        if 2020 <= year <= 2099:
            thousands = "две тысячи"
            remainder = year % 100
            
            if remainder == 0:
                return f"{thousands} года"
            elif remainder < 20:
                tens_text = self._number_to_ordinal(remainder)
                return f"{thousands} {tens_text} года"
            else:
                tens = remainder // 10
                ones = remainder % 10
                
                tens_map = {
                    2: "двадцать", 3: "тридцать", 4: "сорок",
                    5: "пятьдесят", 6: "шестьдесят", 7: "семьдесят",
                    8: "восемьдесят", 9: "девяносто"
                }
                
                tens_text = tens_map.get(tens, "")
                
                if ones == 0:
                    return f"{thousands} {tens_text} года"
                else:
                    ones_text = self._number_to_ordinal(ones)
                    return f"{thousands} {tens_text} {ones_text} года"
        
        # Fallback
        return f"{year} года"
    
    def _number_to_ordinal(self, num: int) -> str:
        """
        Конвертировать число в порядковое числительное (родительный падеж).
        
        Args:
            num: Число (1-99).
            
        Returns:
            Порядковое числительное.
        """
        ordinals = {
            1: "первого", 2: "второго", 3: "третьего", 4: "четвёртого",
            5: "пятого", 6: "шестого", 7: "седьмого", 8: "восьмого",
            9: "девятого", 10: "десятого", 11: "одиннадцатого",
            12: "двенадцатого", 13: "тринадцатого", 14: "четырнадцатого",
            15: "пятнадцатого", 16: "шестнадцатого", 17: "семнадцатого",
            18: "восемнадцатого", 19: "девятнадцатого", 20: "двадцатого",
            21: "двадцать первого", 22: "двадцать второго",
            23: "двадцать третьего", 24: "двадцать четвёртого",
            25: "двадцать пятого", 26: "двадцать шестого",
            27: "двадцать седьмого", 28: "двадцать восьмого",
            29: "двадцать девятого", 30: "тридцатого"
        }
        
        return ordinals.get(num, str(num))
    
    def convert_relative_date(self, date_desc: str) -> str:
        """
        Конвертировать относительную дату (заменить числа на слова).
        
        Args:
            date_desc: Описание даты (например, "через 3 дня").
            
        Returns:
            Дата с числами прописью.
        """
        result = date_desc
        
        # Заменяем числа на слова
        for num, word in self.NUMBERS.items():
            # "через 3 дня" -> "через три дня"
            result = re.sub(rf'\bчерез {num}\b', f'через {word}', result)
            result = re.sub(rf'\b{num} день', f'{word} день', result)
            result = re.sub(rf'\b{num} дня', f'{word} дня', result)
            result = re.sub(rf'\b{num} дней', f'{word} дней', result)
            result = re.sub(rf'\b{num} недел', f'{word} недел', result)
            result = re.sub(rf'\b{num} месяц', f'{word} месяц', result)
        
        return result
    
    def is_relative_date(self, date_desc: str) -> bool:
        """
        Проверить, является ли дата относительной.
        
        Args:
            date_desc: Описание даты.
            
        Returns:
            True если относительная дата.
        """
        relative_keywords = [
            "завтра", "послезавтра", "вчера", "сегодня",
            "через", "назад",
            "понедельник", "вторник", "среду", "четверг",
            "пятницу", "субботу", "воскресенье",
            "следующ", "прошл", "этот", "эт"
        ]
        
        date_lower = date_desc.lower()
        return any(keyword in date_lower for keyword in relative_keywords)
    
    def is_iso_date(self, date_desc: str) -> bool:
        """
        Проверить, является ли строка датой в формате ISO.
        
        Args:
            date_desc: Строка с датой.
            
        Returns:
            True если ISO формат.
        """
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_desc))
    
    def is_ddmmyyyy_date(self, date_desc: str) -> bool:
        """
        Проверить, является ли строка датой в формате DD.MM.YYYY.
        
        Args:
            date_desc: Строка с датой.
            
        Returns:
            True если DD.MM.YYYY формат.
        """
        return bool(re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_desc))
    
    def convert_text_for_tts(
        self,
        text: str,
        date_iso: str,
        date_desc: str
    ) -> str:
        """
        Конвертировать текст для TTS (заменить даты на текстовое представление).
        
        Args:
            text: Исходный текст.
            date_iso: Дата в формате ISO (YYYY-MM-DD).
            date_desc: Описание даты в тексте.
            
        Returns:
            Текст для TTS с датами прописью.
        """
        # Если дата относительная - оставляем как есть
        if self.is_relative_date(date_desc):
            # Но заменяем числа на слова
            return text.replace(date_desc, self.convert_relative_date(date_desc))
        
        # Если дата в формате ISO или DD.MM.YYYY - конвертируем
        if self.is_iso_date(date_desc) or self.is_ddmmyyyy_date(date_desc):
            # Определяем нужен ли год (если дата далеко в будущем)
            try:
                date = datetime.strptime(date_iso, "%Y-%m-%d")
                today = datetime.now()
                days_diff = (date - today).days
                
                # Если дата больше чем через месяц - включаем год
                include_year = days_diff > 30
            except:
                include_year = True
            
            date_text = self.convert_date(date_iso, include_year=include_year)
            return text.replace(date_desc, date_text)
        
        return text
# END:date_to_text_converter


# ANCHOR:main
def main():
    """Тестирование конвертера."""
    converter = DateToTextConverter()
    
    print("="*60)
    print("ТЕСТИРОВАНИЕ КОНВЕРТЕРА ДАТ")
    print("="*60)
    
    # Тест 1: Абсолютные даты
    print("\n1. Абсолютные даты:")
    test_dates = [
        "2026-02-03",
        "2026-12-31",
        "2027-01-01",
        "2026-05-15"
    ]
    
    for date in test_dates:
        result_with_year = converter.convert_date(date, include_year=True)
        result_without_year = converter.convert_date(date, include_year=False)
        print(f"  {date}")
        print(f"    С годом:  {result_with_year}")
        print(f"    Без года: {result_without_year}")
    
    # Тест 2: Относительные даты
    print("\n2. Относительные даты:")
    relative_dates = [
        "через 3 дня",
        "через 5 дней",
        "через 1 неделю",
        "через 2 недели"
    ]
    
    for date in relative_dates:
        result = converter.convert_relative_date(date)
        print(f"  {date:20s} -> {result}")
    
    # Тест 3: Конвертация текста для TTS
    print("\n3. Конвертация текста для TTS:")
    test_cases = [
        ("Найди рейсы на 2026-02-03", "2026-02-03", "2026-02-03"),
        ("Найди рейсы на завтра", "2026-02-03", "завтра"),
        ("Найди рейсы через 3 дня", "2026-02-05", "через 3 дня"),
    ]
    
    for text, date_iso, date_desc in test_cases:
        result = converter.convert_text_for_tts(text, date_iso, date_desc)
        print(f"  Исходный: {text}")
        print(f"  Для TTS:  {result}")
        print()


if __name__ == "__main__":
    main()
# END:main
