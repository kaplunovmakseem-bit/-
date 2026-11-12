"""
Контроллер задач — посредник между интерфейсом и базой данных.

Все виджеты (карточки, зоны, таблица, профиль) не трогают базу напрямую,
а вызывают методы контроллера. После любого изменения контроллер
испускает сигнал tasks_changed, и все представления перерисовываются.

Здесь же живёт «игровой движок»: при выполнении квеста начисляется опыт,
проверяются новый уровень, ежедневная награда и достижения. Для красивых
уведомлений испускаются отдельные сигналы (xp_gained, level_up, ...).
"""

from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from .. import game
from ..database import Database
from ..models import Task, fit_to_zone
from .task_dialog import TaskDialog

DAILY_GOAL_SETTING = "daily_goal"


class TaskController(QObject):
    tasks_changed = Signal()
    xp_gained = Signal(int, str, str)        # сколько XP, навык, подпись
    xp_lost = Signal(int)                     # отмена выполнения
    level_up = Signal(int, str)               # новый уровень, звание
    achievement_unlocked = Signal(str)        # ключ достижения
    daily_completed = Signal(int)             # бонус XP

    def __init__(self, db: Database, window: QWidget):
        super().__init__(window)
        self.db = db
        self.window = window  # родитель для диалогов

    def _notify(self) -> None:
        # Откладываем перерисовку до возврата в цикл событий. Иначе можно
        # удалить виджет (например, карточку с чекбоксом) прямо внутри его
        # собственного обработчика события — это приводит к падению.
        QTimer.singleShot(0, self.tasks_changed.emit)

    # --- Чтение --------------------------------------------------------------
    def tasks(self) -> list[Task]:
        return self.db.all_tasks()

    def daily_goal(self) -> int:
        return int(self.db.get_setting(DAILY_GOAL_SETTING, str(game.DAILY_GOAL_DEFAULT)))

    def stats(self) -> game.PlayerStats:
        """Собирает всю статистику игрока из журнала опыта."""
        per_day = self.db.quests_per_day()
        counts = self.db.completion_counts()
        return game.PlayerStats(
            total_xp=self.db.total_xp(),
            completed=counts["completed"],
            legendary=counts["legendary"],
            on_time=counts["on_time"],
            today=per_day.get(date.today(), 0),
            streak=game.streak_from_days(set(per_day), date.today()),
            best_day=max(per_day.values(), default=0),
            skill_xp=self.db.xp_by_skill(),
        )

    # --- Игровая логика ------------------------------------------------------
    def _apply_done_change(self, task: Task, was_done: bool) -> None:
        """Вызывается, когда у задачи поменялся статус «выполнена»."""
        if task.done == was_done:
            return
        level_before = self.stats().level

        if task.done:
            today = date.today()
            task.completed_at = datetime.now().replace(microsecond=0)
            xp = game.xp_for_task(task, today)
            on_time = game.is_on_time(task, today)
            self.db.add_xp_event(xp, "quest", task, on_time=on_time)
            label = f"{game.skill_icon(task.skill)} {game.skill_name(task.skill)}"
            if on_time:
                label += " · бонус за срок!"
            self.xp_gained.emit(xp, task.skill, label)

            # Ежедневное задание: N квестов за день → бонус (один раз в день)
            if (self.stats().today >= self.daily_goal()
                    and not self.db.daily_bonus_given(today)):
                self.db.add_xp_event(game.DAILY_BONUS_XP, "daily", note="Ежедневное задание")
                self.daily_completed.emit(game.DAILY_BONUS_XP)
        else:
            # Сняли галочку — забираем опыт, полученный за этот квест
            task.completed_at = None
            net = self.db.task_net_xp(task.id)
            if net > 0:
                self.db.add_xp_event(-net, "revoke", task)
                self.xp_lost.emit(net)

        stats = self.stats()
        if stats.level > level_before:
            self.level_up.emit(stats.level, game.title_for_level(stats.level))
        self.check_achievements(stats)

    def check_achievements(self, stats: game.PlayerStats | None = None, silent: bool = False) -> None:
        """Открывает новые достижения. silent=True — без уведомлений."""
        stats = stats or self.stats()
        unlocked = self.db.unlocked_achievements()
        for ach in game.ACHIEVEMENTS:
            if ach.key not in unlocked and ach.check(stats):
                self.db.unlock_achievement(ach.key)
                if not silent:
                    self.achievement_unlocked.emit(ach.key)

    # --- Действия ------------------------------------------------------------
    def create_task(self) -> None:
        dlg = TaskDialog(parent=self.window)
        if dlg.exec() == TaskDialog.Accepted:
            self.db.add_task(dlg.result_task())
            self._notify()

    def edit_task(self, task_id: int) -> None:
        task = self.db.get_task(task_id)
        if task is None:
            return
        dlg = TaskDialog(task, parent=self.window)
        if dlg.exec() == TaskDialog.Accepted:
            new = dlg.result_task()
            self._apply_done_change(new, was_done=task.done)
            self.db.update_task(new)
            self._notify()

    def set_done(self, task_id: int, done: bool) -> None:
        task = self.db.get_task(task_id)
        if task is None or task.done == done:
            return
        task.done = done
        self._apply_done_change(task, was_done=not done)
        self.db.update_task(task)
        self._notify()

    def delete_task(self, task_id: int) -> None:
        """Удаляет задачу после подтверждения пользователем."""
        task = self.db.get_task(task_id)
        if task is None:
            return
        box = QMessageBox(self.window)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Удаление квеста")
        box.setText(f"Удалить квест «{task.title}»?")
        box.setInformativeText("Это действие нельзя отменить. Заработанный опыт сохранится.")
        yes = box.addButton("Удалить", QMessageBox.DestructiveRole)
        box.addButton("Отмена", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is yes:
            self.db.delete_task(task_id)
            self._notify()

    def move_to_zone(self, task_id: int, zone: str) -> None:
        """Вызывается при перетаскивании карточки в другую зону."""
        task = self.db.get_task(task_id)
        if task is None or task.zone == zone:
            return
        task.importance, task.difficulty = fit_to_zone(task.importance, task.difficulty, zone)
        self.db.update_task(task)
        self._notify()
