"""
Игровая механика: опыт (XP), уровни, навыки, редкость квестов и достижения.

Модуль «чистый» — не зависит от Qt и SQLite. Все числа баланса собраны
здесь, их можно смело крутить.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable

from .models import Task

# --- Навыки (характеристики персонажа) ---------------------------------------
# Каждый квест прокачивает один навык.
# key -> (название, эмодзи, цвет в светлой теме, цвет в тёмной теме)
# Цвета — системная палитра iOS. Порядок важен: соседние цвета в диаграммах
# проверены валидатором на различимость (в т. ч. при дальтонизме).
SKILLS = {
    "body":     ("Сила",        "💪", "#FF3B30", "#FF453A"),
    "mind":     ("Интеллект",   "🧠", "#007AFF", "#0A84FF"),
    "career":   ("Карьера",     "💼", "#FF9500", "#D27C08"),
    "creative": ("Творчество",  "🎨", "#AF52DE", "#BF5AF2"),
    "home":     ("Быт",         "🏠", "#34C759", "#28B04B"),
    "social":   ("Харизма",     "🗣️", "#30B0C7", "#169DB8"),
    "health":   ("Здоровье",    "❤️", "#FF2D55", "#FF375F"),
    "other":    ("Разное",      "✨", "#5856D6", "#6E6CF0"),
}
DEFAULT_SKILL = "other"


def skill_name(key: str) -> str:
    return SKILLS.get(key, SKILLS[DEFAULT_SKILL])[0]


def skill_icon(key: str) -> str:
    return SKILLS.get(key, SKILLS[DEFAULT_SKILL])[1]


def skill_color(key: str, dark: bool = False) -> str:
    entry = SKILLS.get(key, SKILLS[DEFAULT_SKILL])
    return entry[3] if dark else entry[2]


# --- Редкость квеста = его сложность -----------------------------------------
RARITIES = {
    1: ("Обычный",     "#8E8E93"),
    2: ("Необычный",   "#34C759"),
    3: ("Редкий",      "#007AFF"),
    4: ("Эпический",   "#AF52DE"),
    5: ("Легендарный", "#FF9500"),
}


def rarity(difficulty: int) -> tuple[str, str]:
    """(название, цвет) редкости."""
    return RARITIES.get(difficulty, RARITIES[1])


# --- Опыт за квест -----------------------------------------------------------
XP_BASE = 10
XP_PER_IMPORTANCE = 8
XP_PER_DIFFICULTY = 12
ON_TIME_BONUS = 0.2          # +20 %, если квест выполнен до срока

DAILY_GOAL_DEFAULT = 3       # сколько квестов в день нужно для ежедневной награды
DAILY_BONUS_XP = 50
DAILY_XP_TARGET = 200        # цель кольца «Опыт за день»


def base_xp(task: Task) -> int:
    """Награда без бонусов: от 30 XP (1/1) до 110 XP (5/5)."""
    return XP_BASE + task.importance * XP_PER_IMPORTANCE + task.difficulty * XP_PER_DIFFICULTY


def is_on_time(task: Task, completed_on: date) -> bool:
    return task.due_date is not None and completed_on <= task.due_date


def xp_for_task(task: Task, completed_on: date) -> int:
    """Итоговая награда с учётом бонуса за выполнение в срок."""
    xp = base_xp(task)
    if is_on_time(task, completed_on):
        xp = round(xp * (1 + ON_TIME_BONUS))
    return xp


# --- Уровни ------------------------------------------------------------------
def xp_to_next(level: int) -> int:
    """Сколько XP нужно, чтобы с уровня level перейти на level+1."""
    return 100 + (level - 1) * 50


def level_info(total_xp: int) -> tuple[int, int, int]:
    """
    По общему опыту возвращает (уровень, XP внутри уровня, XP до следующего).
    Пример: 130 XP → (2, 30, 150).
    """
    level, xp = 1, max(0, total_xp)
    while xp >= xp_to_next(level):
        xp -= xp_to_next(level)
        level += 1
    return level, xp, xp_to_next(level)


def skill_level_info(skill_xp: int) -> tuple[int, int, int]:
    """Навыки качаются быстрее персонажа: 80, 120, 160, … XP на уровень."""
    level, xp = 1, max(0, skill_xp)
    while xp >= 40 + level * 40:
        xp -= 40 + level * 40
        level += 1
    return level, xp, 40 + level * 40


TITLES = [  # (минимальный уровень, звание)
    (1, "Новичок"), (3, "Ученик"), (5, "Искатель приключений"), (8, "Боец"),
    (12, "Ветеран"), (16, "Мастер"), (20, "Герой"), (30, "Легенда"),
]


def title_for_level(level: int) -> str:
    title = TITLES[0][1]
    for min_level, name in TITLES:
        if level >= min_level:
            title = name
    return title


# --- Статистика игрока -------------------------------------------------------
@dataclass
class PlayerStats:
    total_xp: int = 0
    completed: int = 0                 # выполнено квестов (за всё время)
    legendary: int = 0                 # выполнено квестов сложности 5
    on_time: int = 0                   # выполнено в срок
    today: int = 0                     # выполнено сегодня
    streak: int = 0                    # дней подряд с выполненными квестами
    best_day: int = 0                  # рекорд квестов за день
    skill_xp: dict = field(default_factory=dict)

    @property
    def level(self) -> int:
        return level_info(self.total_xp)[0]

    def skill_level(self, key: str) -> int:
        return skill_level_info(self.skill_xp.get(key, 0))[0]


def streak_from_days(days: set[date], today: date) -> int:
    """Серия: сколько дней подряд (заканчивая сегодня или вчера) были выполнения."""
    from datetime import timedelta
    day = today if today in days else today - timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


# --- Достижения --------------------------------------------------------------
@dataclass(frozen=True)
class Achievement:
    key: str
    icon: str
    title: str
    description: str
    check: Callable[[PlayerStats], bool]


ACHIEVEMENTS: list[Achievement] = [
    Achievement("first_quest", "🎯", "Первый шаг", "Выполнить первый квест", lambda s: s.completed >= 1),
    Achievement("quests_10", "⚔️", "Охотник", "Выполнить 10 квестов", lambda s: s.completed >= 10),
    Achievement("quests_50", "🛡️", "Ветеран квестов", "Выполнить 50 квестов", lambda s: s.completed >= 50),
    Achievement("quests_100", "👑", "Сотня", "Выполнить 100 квестов", lambda s: s.completed >= 100),
    Achievement("legendary", "🐉", "Победитель дракона", "Выполнить легендарный квест", lambda s: s.legendary >= 1),
    Achievement("on_time_10", "⏰", "Пунктуальный", "10 квестов выполнены в срок", lambda s: s.on_time >= 10),
    Achievement("combo_5", "🔥", "Комбо", "5 квестов за один день", lambda s: s.best_day >= 5),
    Achievement("streak_3", "📅", "Разогрев", "Серия 3 дня подряд", lambda s: s.streak >= 3),
    Achievement("streak_7", "🌟", "Неделя силы", "Серия 7 дней подряд", lambda s: s.streak >= 7),
    Achievement("streak_30", "💎", "Несгибаемый", "Серия 30 дней подряд", lambda s: s.streak >= 30),
    Achievement("level_5", "🚀", "На взлёте", "Достичь 5 уровня", lambda s: s.level >= 5),
    Achievement("level_10", "🏆", "Десятка", "Достичь 10 уровня", lambda s: s.level >= 10),
    Achievement("skill_5", "📈", "Специалист", "Прокачать любой навык до 5 уровня",
                lambda s: any(s.skill_level(k) >= 5 for k in SKILLS)),
    Achievement("all_round", "🌈", "Разносторонний", "Получить опыт в 5 разных навыках",
                lambda s: sum(1 for v in s.skill_xp.values() if v > 0) >= 5),
]

ACHIEVEMENTS_BY_KEY = {a.key: a for a in ACHIEVEMENTS}

AVATARS = ["🧙", "🦸", "🧝", "🥷", "🧑‍🚀", "🦊", "🐉", "🤖", "👾", "🐱", "🦁", "🧛"]
