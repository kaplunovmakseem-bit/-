"""
Настройки приложения, собранные в одном месте.

Если хотите изменить правила распределения задач по зонам —
меняйте ТОЛЬКО константы в этом файле.
"""

import os
import sys
from pathlib import Path

APP_NAME = "TaskMatrix"
APP_TITLE = "Life RPG — Матрица квестов"

# --- Шкалы значимости и сложности -------------------------------------------
SCALE_MIN = 1
SCALE_MAX = 5

# --- ПОРОГИ РАСПРЕДЕЛЕНИЯ ----------------------------------------------------
# Задача считается «значимой», если importance >= IMPORTANCE_THRESHOLD.
# Задача считается «сложной», если difficulty >= DIFFICULTY_THRESHOLD.
# При значениях 3/3 получаем ровно правила из ТЗ:
#   значимость ≥ 3 и сложность ≤ 2 → «Сделать сейчас» и т. д.
IMPORTANCE_THRESHOLD = 3
DIFFICULTY_THRESHOLD = 3

# --- Зоны --------------------------------------------------------------------
# Ключ зоны — короткий идентификатор, который используется в коде.
ZONE_DO_NOW = "do_now"        # значимая и простая
ZONE_PLAN = "plan"            # значимая и сложная
ZONE_IN_BETWEEN = "between"   # незначимая и простая
ZONE_POSTPONE = "postpone"    # незначимая и сложная

# Порядок зон в матрице 2×2: (строка, столбец)
ZONE_GRID = {
    ZONE_DO_NOW: (0, 0),
    ZONE_PLAN: (0, 1),
    ZONE_IN_BETWEEN: (1, 0),
    ZONE_POSTPONE: (1, 1),
}

ZONE_TITLES = {
    ZONE_DO_NOW: "Сделать сейчас",
    ZONE_PLAN: "Запланировать",
    ZONE_IN_BETWEEN: "Между делом",
    ZONE_POSTPONE: "Отложить",
}

# Иконки зон (эмодзи в заголовке)
ZONE_ICONS = {
    ZONE_DO_NOW: "⚡",
    ZONE_PLAN: "🗺️",
    ZONE_IN_BETWEEN: "🍃",
    ZONE_POSTPONE: "💤",
}

ZONE_HINTS = {
    ZONE_DO_NOW: "Значимо и просто",
    ZONE_PLAN: "Значимо и сложно",
    ZONE_IN_BETWEEN: "Незначимо и просто",
    ZONE_POSTPONE: "Незначимо и сложно",
}

# Акцентные цвета зон (одинаковы для обеих тем; фон подбирается в themes.py)
ZONE_COLORS = {
    ZONE_DO_NOW: "#1fbf75",     # изумрудный
    ZONE_PLAN: "#6d7cff",       # фиолетово-синий
    ZONE_IN_BETWEEN: "#f0a53a", # янтарный
    ZONE_POSTPONE: "#9b8fc0",   # лавандово-серый
}

OVERDUE_COLOR = "#ef4f5f"  # цвет подсветки просроченных задач


def data_dir() -> Path:
    """
    Папка для данных пользователя.

    Windows: %APPDATA%\\TaskMatrix  (например C:\\Users\\Имя\\AppData\\Roaming\\TaskMatrix)
    macOS:   ~/Library/Application Support/TaskMatrix
    Linux:   ~/.local/share/TaskMatrix
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    """Полный путь к файлу базы данных SQLite."""
    # Переменная окружения позволяет подменить базу (удобно для тестов)
    override = os.environ.get("TASKMATRIX_DB")
    if override:
        return Path(override)
    return data_dir() / "tasks.db"
