"""
Карточка квеста — строка списка в стиле «Напоминаний» iOS:

    ◯  Название квеста                                   +70 XP
       💪 Сила · Редкий · Завтра
    ──────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QVBoxLayout

from .. import game
from ..models import Task
from . import themes
from .ios import CheckCircle
from .widgets import due_text

# Тип MIME-данных, в которых при перетаскивании передаётся id задачи
TASK_MIME = "application/x-taskmatrix-task-id"


class TaskCard(QFrame):
    """
    Поддерживает:
      - клик — выделение (для удаления клавишей Delete);
      - двойной клик — редактирование;
      - правый клик — контекстное меню;
      - перетаскивание в другую зону.
    """

    clicked = Signal(int)  # id задачи

    def __init__(self, task: Task, controller, selected: bool = False, last: bool = False, parent=None):
        super().__init__(parent)
        self.task = task
        self.controller = controller
        self.last = last
        self._drag_start: QPoint | None = None
        c = themes.colors()

        self.setObjectName("taskCard")
        self.setCursor(Qt.OpenHandCursor)

        # Кружок «выполнено» цвета зоны
        self.check = CheckCircle(themes.zone_color(task.zone), 22)
        self.check.setChecked(task.done)
        self.check.setToolTip("Завершить квест")
        self.check.toggled.connect(lambda v: controller.set_done(task.id, v))

        # Название
        self.title = QLabel(task.title)
        self.title.setObjectName("cardTitle")
        self.title.setWordWrap(True)

        # Награда справа
        xp = game.xp_for_task(task, date.today())
        self.xp = QLabel(f"{xp} XP" if task.done else f"+{xp} XP")
        self.xp.setObjectName("cardXp")
        self.xp.setToolTip("Опыт за выполнение")

        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(self.title, 1)
        top.addWidget(self.xp, 0, Qt.AlignTop)

        # Подзаголовок: навык · редкость · срок (просрочка — красным)
        rarity_name, rarity_color = game.rarity(task.difficulty)
        parts = [f"{game.skill_icon(task.skill)} {game.skill_name(task.skill)}",
                 f"<span style='color:{rarity_color}'>{rarity_name}</span>"]
        due = due_text(task.due_date, task.done)
        if due:
            color = c["danger"] if task.is_overdue else c["muted"]
            parts.append(f"<span style='color:{color}'>{'⏰ ' if not task.done else ''}{due}</span>")
        self.meta = QLabel(" · ".join(parts))
        self.meta.setObjectName("cardMeta")
        self.meta.setToolTip(f"Значимость {task.importance} · Сложность {task.difficulty}")

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        text_col.addLayout(top)
        text_col.addWidget(self.meta)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 9, 12, 9)
        lay.setSpacing(10)
        lay.addWidget(self.check, 0, Qt.AlignTop)
        lay.addLayout(text_col, 1)

        if task.description:
            self.setToolTip(task.description)

        self._apply_style(selected)

    def set_selected(self, selected: bool) -> None:
        """Меняет только оформление, не пересоздавая карточку."""
        self._apply_style(selected)

    def _apply_style(self, selected: bool) -> None:
        c = themes.colors()
        bg = c["selection"] if selected else "transparent"
        hover = c["selection"] if selected else themes.rgba(c["muted"], 0.08)
        sep = "none" if self.last else f"1px solid {c['separator']}"
        self.setStyleSheet(f"""
            QFrame#taskCard {{ background: {bg}; border: none; border-bottom: {sep}; border-radius: 0; }}
            QFrame#taskCard:hover {{ background: {hover}; }}
            QLabel#cardTitle {{ color: {c['muted'] if self.task.done else c['text']}; font-size: 10.5pt; }}
            QLabel#cardMeta {{ color: {c['muted']}; font-size: 8.5pt; }}
            QLabel#cardXp {{ color: {c['muted'] if self.task.done else c['gold']}; font-size: 9pt; font-weight: 700; }}
        """)

    # --- Мышь ----------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
            self.clicked.emit(self.task.id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Начинаем перетаскивание, только если мышь сдвинулась достаточно далеко
        if self._drag_start is None or not (event.buttons() & Qt.LeftButton):
            return
        if (event.position().toPoint() - self._drag_start).manhattanLength() < QApplication.startDragDistance():
            return

        mime = QMimeData()
        mime.setData(TASK_MIME, str(self.task.id).encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())                  # «призрак» карточки под курсором
        drag.setHotSpot(self._drag_start)
        self._drag_start = None
        drag.exec(Qt.MoveAction)
        # Важно: после drag.exec() не обращаемся к self — карточка
        # может быть уже запланирована к удалению при перерисовке.

    def mouseReleaseEvent(self, event):
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.controller.edit_task(self.task.id)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_edit = menu.addAction("Редактировать…")
        act_done = menu.addAction("Вернуть в работу" if self.task.done else "Завершить квест")
        menu.addSeparator()
        act_del = menu.addAction("Удалить…")
        chosen = menu.exec(event.globalPos())
        task_id, done = self.task.id, self.task.done
        if chosen is act_edit:
            self.controller.edit_task(task_id)
        elif chosen is act_done:
            self.controller.set_done(task_id, not done)
        elif chosen is act_del:
            self.controller.delete_task(task_id)
