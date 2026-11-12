"""
Модель данных: класс задачи и логика распределения по зонам.

Этот модуль не зависит ни от Qt, ни от SQLite — это «чистая» логика,
которую легко проверить и переиспользовать.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from . import config


@dataclass
class Task:
    """Одна задача пользователя."""

    title: str                              # Название (обязательно)
    description: str = ""                   # Описание (необязательно)
    importance: int = 3                     # Значимость 1..5
    difficulty: int = 3                     # Сложность 1..5
    due_date: Optional[date] = None         # Срок выполнения (необязательно)
    done: bool = False                      # Выполнена / не выполнена
    created_at: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))
    id: Optional[int] = None                # Присваивается базой данных
    skill: str = "other"                    # Навык, который прокачивает квест (см. game.py)
    completed_at: Optional[datetime] = None # Когда отмечена выполненной

    @property
    def zone(self) -> str:
        """Зона матрицы, в которую попадает задача."""
        return zone_for(self.importance, self.difficulty)

    @property
    def is_overdue(self) -> bool:
        """Просрочена: есть срок, он уже прошёл, а задача не выполнена."""
        return (not self.done) and self.due_date is not None and self.due_date < date.today()


def is_important(importance: int) -> bool:
    return importance >= config.IMPORTANCE_THRESHOLD


def is_hard(difficulty: int) -> bool:
    return difficulty >= config.DIFFICULTY_THRESHOLD


def zone_for(importance: int, difficulty: int) -> str:
    """
    ГЛАВНОЕ ПРАВИЛО распределения.
    Пороги берутся из config.py, здесь только сама логика.
    """
    if is_important(importance):
        return config.ZONE_PLAN if is_hard(difficulty) else config.ZONE_DO_NOW
    return config.ZONE_POSTPONE if is_hard(difficulty) else config.ZONE_IN_BETWEEN


def zone_flags(zone: str) -> tuple[bool, bool]:
    """Для зоны возвращает пару (значимая?, сложная?)."""
    return {
        config.ZONE_DO_NOW: (True, False),
        config.ZONE_PLAN: (True, True),
        config.ZONE_IN_BETWEEN: (False, False),
        config.ZONE_POSTPONE: (False, True),
    }[zone]


def fit_to_zone(importance: int, difficulty: int, zone: str) -> tuple[int, int]:
    """
    Подгоняет значимость и сложность под указанную зону (используется
    при перетаскивании карточки).

    Меняем значения МИНИМАЛЬНО: если параметр уже подходит зоне — он
    остаётся как есть, иначе становится ближайшим допустимым значением
    по другую сторону порога. Например, задача (5, 1) из «Сделать сейчас»,
    брошенная в «Запланировать», станет (5, 3).
    """
    want_important, want_hard = zone_flags(zone)

    if is_important(importance) != want_important:
        importance = config.IMPORTANCE_THRESHOLD if want_important else config.IMPORTANCE_THRESHOLD - 1
    if is_hard(difficulty) != want_hard:
        difficulty = config.DIFFICULTY_THRESHOLD if want_hard else config.DIFFICULTY_THRESHOLD - 1

    # На случай экзотических порогов — не выходим за пределы шкалы
    clamp = lambda v: max(config.SCALE_MIN, min(config.SCALE_MAX, v))  # noqa: E731
    return clamp(importance), clamp(difficulty)


# Подписи для слайдеров и таблицы
IMPORTANCE_LABELS = {
    1: "Совсем неважно",
    2: "Малозначимо",
    3: "Значимо",
    4: "Очень значимо",
    5: "Критически важно",
}

DIFFICULTY_LABELS = {
    1: "Пара минут",
    2: "Легко",
    3: "Средне",
    4: "Сложно",
    5: "Очень сложно",
}
