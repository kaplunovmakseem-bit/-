"""
Работа с базой данных SQLite.

Класс Database инкапсулирует все SQL-запросы. Интерфейс общается с базой
только через его методы и получает/отдаёт объекты Task.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .models import Task

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    importance  INTEGER NOT NULL CHECK (importance BETWEEN 1 AND 5),
    difficulty  INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    due_date    TEXT,                       -- ISO-формат 'ГГГГ-ММ-ДД' или NULL
    done        INTEGER NOT NULL DEFAULT 0, -- 0 / 1
    created_at  TEXT    NOT NULL            -- ISO-формат даты и времени
);

-- Простое хранилище настроек «ключ → значение» (например, тема)
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row  # доступ к колонкам по имени
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # --- Преобразование строки БД <-> Task -----------------------------------
    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            importance=row["importance"],
            difficulty=row["difficulty"],
            due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
            done=bool(row["done"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _task_params(task: Task) -> tuple:
        return (
            task.title.strip(),
            task.description,
            task.importance,
            task.difficulty,
            task.due_date.isoformat() if task.due_date else None,
            int(task.done),
        )

    # --- CRUD ----------------------------------------------------------------
    def add_task(self, task: Task) -> Task:
        """Сохраняет новую задачу и возвращает её с присвоенным id."""
        if not task.title.strip():
            raise ValueError("Название задачи не может быть пустым")
        cur = self.conn.execute(
            """INSERT INTO tasks (title, description, importance, difficulty,
                                  due_date, done, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            self._task_params(task) + (task.created_at.isoformat(sep=" "),),
        )
        self.conn.commit()
        task.id = cur.lastrowid
        return task

    def update_task(self, task: Task) -> None:
        if task.id is None:
            raise ValueError("Нельзя обновить задачу без id")
        if not task.title.strip():
            raise ValueError("Название задачи не может быть пустым")
        self.conn.execute(
            """UPDATE tasks SET title=?, description=?, importance=?, difficulty=?,
                                due_date=?, done=?
               WHERE id=?""",
            self._task_params(task) + (task.id,),
        )
        self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def get_task(self, task_id: int) -> Optional[Task]:
        row = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def all_tasks(self) -> list[Task]:
        """
        Все задачи. Порядок: сначала невыполненные, затем по сроку
        (задачи без срока — в конце), затем по значимости.
        """
        rows = self.conn.execute(
            """SELECT * FROM tasks
               ORDER BY done ASC,
                        due_date IS NULL, due_date ASC,
                        importance DESC, id ASC"""
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    # --- Настройки -----------------------------------------------------------
    def get_setting(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()
