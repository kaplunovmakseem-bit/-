"""
Контроллер задач — посредник между интерфейсом и базой данных.

Все виджеты (карточки, зоны, таблица) не трогают базу напрямую, а вызывают
методы контроллера. После любого изменения контроллер испускает сигнал
tasks_changed, и все представления перерисовываются из базы. Так данные
в матрице и в таблице всегда согласованы.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from ..database import Database
from ..models import Task, fit_to_zone
from .task_dialog import TaskDialog


class TaskController(QObject):
    tasks_changed = Signal()

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
            self.db.update_task(dlg.result_task())
            self._notify()

    def set_done(self, task_id: int, done: bool) -> None:
        task = self.db.get_task(task_id)
        if task is None or task.done == done:
            return
        task.done = done
        self.db.update_task(task)
        self._notify()

    def delete_task(self, task_id: int) -> None:
        """Удаляет задачу после подтверждения пользователем."""
        task = self.db.get_task(task_id)
        if task is None:
            return
        box = QMessageBox(self.window)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Удаление задачи")
        box.setText(f"Удалить задачу «{task.title}»?")
        box.setInformativeText("Это действие нельзя отменить.")
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
