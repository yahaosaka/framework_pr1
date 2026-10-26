"""Вспомогательные функции безопасного ввода."""

from datetime import date
from typing import Optional


def input_int(
    prompt: str,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    """Запросить целое число; при ошибке повторить запрос."""
    while True:
        try:
            number = int(input(prompt))
        except ValueError:
            print("Введите целое число.")
            continue
        if minimum is not None and number < minimum:
            print(f"Число должно быть не меньше {minimum}.")
        elif maximum is not None and number > maximum:
            print(f"Число должно быть не больше {maximum}.")
        else:
            return number


def input_date(prompt: str) -> str:
    """Запросить дату ГГГГ-ММ-ДД (пустой ввод – сегодня)."""
    while True:
        value = input(prompt).strip()
        if not value:
            return date.today().isoformat()
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            print("Формат даты: ГГГГ-ММ-ДД.")
