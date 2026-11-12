"""Карточка задачи внутри зоны матрицы."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QMenu, QVBoxLayout,
)

from .. import config
from ..models import Task
from . import themes

# Тип MIME-данных, в которых при перетаскивании передаётся id задачи
TASK_MIME = "application/x-taskmatrix-task-id"


class TaskCard(QFrame):
    """
    Показывает одну задачу: чекбокс «выполнено», название, значимость,
    сложность и срок. Поддерживает:
      - клик — выделение (для удаления клавишей Delete);
      - двойной клик — редактирование;
      - правый клик — контекстное меню;
      - перетаскивание в другую зону.
    """

    clicked = Signal(int)  # id задачи

    def __init__(self, task: Task, controller, selected: bool = False, parent=None):
        super().__init__(parent)
        self.task = task
        self.controller = controller
        self._drag_start: QPoint | None = None

        self.setObjectName("taskCard")
        self.setCursor(Qt.OpenHandCursor)

        # Чекбокс «выполнено»
        self.check = QCheckBox()
        self.check.setChecked(task.done)
        self.check.setCursor(Qt.PointingHandCursor)
        self.check.setToolTip("Отметить выполненной")
        self.check.toggled.connect(lambda v: controller.set_done(task.id, v))

        # Название (зачёркнуто, если выполнено)
        self.title = QLabel(task.title)
        self.title.setWordWrap(True)
        font = self.title.font()
        font.setStrikeOut(task.done)
        font.setBold(not task.done)
        self.title.setFont(font)

        # Строка с параметрами
        meta = f"Значимость {task.importance} · Сложность {task.difficulty}"
        if task.due_date:
            meta += f" · до {task.due_date.strftime('%d.%m.%Y')}"
        if task.is_overdue:
            meta += " · просрочено!"
        self.meta = QLabel(meta)
        self.meta.setObjectName("muted")

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(self.title)
        text_col.addWidget(self.meta)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
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
        zone_color = config.ZONE_COLORS[self.task.zone]
        # Цвет левой полосы: красный для просроченных, иначе цвет зоны
        stripe = config.OVERDUE_COLOR if self.task.is_overdue else zone_color
        border = c["highlight"] if selected else c["border"]
        bg = c["surface"]
        if self.task.is_overdue:
            bg = themes.mix(c["surface"], config.OVERDUE_COLOR, 0.12)
        opacity_text = c["muted"] if self.task.done else c["text"]
        meta_color = config.OVERDUE_COLOR if self.task.is_overdue else c["muted"]

        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background: {bg};
                border: {2 if selected else 1}px solid {border};
                border-left: 4px solid {stripe};
                border-radius: 6px;
            }}
            QFrame#taskCard QLabel {{ background: transparent; border: none; color: {opacity_text}; }}
            QFrame#taskCard QLabel#muted {{ color: {meta_color}; font-size: 8.5pt; }}
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
        act_done = menu.addAction("Отметить невыполненной" if self.task.done else "Отметить выполненной")
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
