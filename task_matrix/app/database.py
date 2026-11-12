"""
Работа с базой данных SQLite.

Класс Database инкапсулирует все SQL-запросы. Интерфейс общается с базой
только через его методы и получает/отдаёт объекты Task.

Таблицы:
  tasks         — сами задачи (квесты);
  xp_events     — журнал опыта: каждое выполнение / отмена / бонус — строка.
                  Опыт считается по журналу, поэтому удаление выполненной
                  задачи не отнимает уже заработанный XP;
  achievements  — открытые достижения;
  settings      — настройки «ключ → значение».
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import Task

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT '',
    importance   INTEGER NOT NULL CHECK (importance BETWEEN 1 AND 5),
    difficulty   INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    due_date     TEXT,                       -- ISO-формат 'ГГГГ-ММ-ДД' или NULL
    done         INTEGER NOT NULL DEFAULT 0, -- 0 / 1
    created_at   TEXT    NOT NULL            -- ISO-формат даты и времени
);

CREATE TABLE IF NOT EXISTS xp_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,            -- когда начислено
    amount      INTEGER NOT NULL,            -- может быть отрицательным (отмена)
    kind        TEXT    NOT NULL,            -- 'quest' | 'revoke' | 'daily'
    task_id     INTEGER,                     -- без внешнего ключа: задачу можно удалить
    skill       TEXT,
    difficulty  INTEGER,
    on_time     INTEGER NOT NULL DEFAULT 0,
    note        TEXT    NOT NULL DEFAULT ''  -- название квеста на момент начисления
);

CREATE TABLE IF NOT EXISTS achievements (
    key         TEXT PRIMARY KEY,
    unlocked_at TEXT NOT NULL
);

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
        self._migrate()
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def _migrate(self) -> None:
        """Обновляет базу от первой версии приложения (без игровых полей)."""
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(tasks)")}
        if "skill" not in cols:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN skill TEXT NOT NULL DEFAULT 'other'")
        if "completed_at" not in cols:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
            # Уже выполненные задачи из старой версии засчитываем в опыт
            from .game import xp_for_task  # локальный импорт: game зависит от models
            for row in self.conn.execute("SELECT * FROM tasks WHERE done=1").fetchall():
                task = self._row_to_task(row)
                when = task.created_at
                self.conn.execute("UPDATE tasks SET completed_at=? WHERE id=?",
                                  (when.isoformat(sep=" "), task.id))
                self._insert_event(when, xp_for_task(task, when.date()), "quest", task,
                                   on_time=False)

    # --- Преобразование строки БД <-> Task -----------------------------------
    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        keys = row.keys()
        completed = row["completed_at"] if "completed_at" in keys else None
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            importance=row["importance"],
            difficulty=row["difficulty"],
            due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
            done=bool(row["done"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            skill=row["skill"] if "skill" in keys else "other",
            completed_at=datetime.fromisoformat(completed) if completed else None,
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
            task.skill,
            task.completed_at.isoformat(sep=" ") if task.completed_at else None,
        )

    # --- CRUD задач ----------------------------------------------------------
    def add_task(self, task: Task) -> Task:
        """Сохраняет новую задачу и возвращает её с присвоенным id."""
        if not task.title.strip():
            raise ValueError("Название задачи не может быть пустым")
        cur = self.conn.execute(
            """INSERT INTO tasks (title, description, importance, difficulty,
                                  due_date, done, skill, completed_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                                due_date=?, done=?, skill=?, completed_at=?
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

    # --- Журнал опыта --------------------------------------------------------
    def _insert_event(self, when: datetime, amount: int, kind: str,
                      task: Optional[Task] = None, on_time: bool = False, note: str = "") -> None:
        self.conn.execute(
            """INSERT INTO xp_events (ts, amount, kind, task_id, skill, difficulty, on_time, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (when.replace(microsecond=0).isoformat(sep=" "), amount, kind,
             task.id if task else None, task.skill if task else None,
             task.difficulty if task else None, int(on_time),
             note or (task.title if task else "")),
        )

    def add_xp_event(self, amount: int, kind: str, task: Optional[Task] = None,
                     on_time: bool = False, note: str = "") -> None:
        self._insert_event(datetime.now(), amount, kind, task, on_time, note)
        self.conn.commit()

    def task_net_xp(self, task_id: int) -> int:
        """Сколько XP сейчас «числится» за задачей (начисления минус отмены)."""
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM xp_events "
            "WHERE task_id=? AND kind IN ('quest', 'revoke')", (task_id,)).fetchone()
        return row["s"]

    def total_xp(self) -> int:
        return self.conn.execute("SELECT COALESCE(SUM(amount),0) AS s FROM xp_events").fetchone()["s"]

    def xp_by_skill(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT skill, SUM(amount) AS s FROM xp_events WHERE skill IS NOT NULL GROUP BY skill")
        return {r["skill"]: max(0, r["s"]) for r in rows}

    def completion_counts(self) -> dict[str, int]:
        """Счётчики выполнений с учётом отмен (отмена «гасит» выполнение)."""
        q = lambda sql: self.conn.execute(sql).fetchone()[0] or 0  # noqa: E731
        quests = q("SELECT COUNT(*) FROM xp_events WHERE kind='quest'")
        revokes = q("SELECT COUNT(*) FROM xp_events WHERE kind='revoke'")
        legendary = q("SELECT COUNT(*) FROM xp_events WHERE kind='quest' AND difficulty=5") \
            - q("SELECT COUNT(*) FROM xp_events WHERE kind='revoke' AND difficulty=5")
        on_time = q("SELECT COUNT(*) FROM xp_events WHERE kind='quest' AND on_time=1") \
            - q("SELECT COUNT(*) FROM xp_events WHERE kind='revoke' AND on_time=1")
        return {"completed": max(0, quests - revokes), "legendary": max(0, legendary),
                "on_time": max(0, on_time)}

    def quests_per_day(self) -> dict[date, int]:
        """Число выполненных квестов по дням (отмены вычитаются)."""
        rows = self.conn.execute(
            "SELECT substr(ts,1,10) AS d, "
            "SUM(CASE kind WHEN 'quest' THEN 1 WHEN 'revoke' THEN -1 ELSE 0 END) AS n "
            "FROM xp_events GROUP BY d")
        return {date.fromisoformat(r["d"]): r["n"] for r in rows if r["n"] > 0}

    def xp_per_day(self, days: int) -> list[tuple[date, int]]:
        """XP за последние `days` дней (включая сегодня), по возрастанию даты."""
        start = date.today() - timedelta(days=days - 1)
        rows = self.conn.execute(
            "SELECT substr(ts,1,10) AS d, SUM(amount) AS s FROM xp_events "
            "WHERE substr(ts,1,10) >= ? GROUP BY d", (start.isoformat(),))
        by_day = {r["d"]: r["s"] for r in rows}
        return [(start + timedelta(i), max(0, by_day.get((start + timedelta(i)).isoformat(), 0)))
                for i in range(days)]

    def daily_bonus_given(self, day: date) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM xp_events WHERE kind='daily' AND substr(ts,1,10)=?",
            (day.isoformat(),)).fetchone() is not None

    def recent_events(self, limit: int = 12) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM xp_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    # --- Достижения ----------------------------------------------------------
    def unlocked_achievements(self) -> dict[str, str]:
        return {r["key"]: r["unlocked_at"] for r in self.conn.execute("SELECT * FROM achievements")}

    def unlock_achievement(self, key: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO achievements (key, unlocked_at) VALUES (?, ?)",
                          (key, datetime.now().replace(microsecond=0).isoformat(sep=" ")))
        self.conn.commit()

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
