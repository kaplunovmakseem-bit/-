"""Карточка квеста внутри зоны матрицы."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QMenu, QVBoxLayout,
)
from PySide6.QtGui import QColor

from .. import config, game
from ..models import Task
from . import themes
from .widgets import chip, due_text

# Тип MIME-данных, в которых при перетаскивании передаётся id задачи
TASK_MIME = "application/x-taskmatrix-task-id"


class TaskCard(QFrame):
    """
    Показывает один квест:
        ○  Название                                   +78 XP
           [💪 Сила] [Эпический] [⏰ завтра]
    Поддерживает:
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
        self.check.setToolTip("Завершить квест")
        self.check.toggled.connect(lambda v: controller.set_done(task.id, v))

        # Название (зачёркнуто, если выполнено)
        self.title = QLabel(task.title)
        self.title.setObjectName("cardTitle")
        self.title.setWordWrap(True)
        font = self.title.font()
        font.setStrikeOut(task.done)
        self.title.setFont(font)

        # Награда в правом верхнем углу
        c = themes.colors()
        xp = game.xp_for_task(task, date.today())
        self.xp = chip(f"{'✔ ' if task.done else '+'}{xp} XP", c["gold"])
        self.xp.setToolTip("Опыт за выполнение" + (" (с бонусом за срок)" if task.due_date and not task.is_overdue else ""))

        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(self.title, 1)
        top.addWidget(self.xp, 0, Qt.AlignTop)

        # Нижняя строка чипов: навык, редкость, срок
        chips = QHBoxLayout()
        chips.setSpacing(4)
        chips.addWidget(chip(f"{game.skill_icon(task.skill)} {game.skill_name(task.skill)}",
                             game.skill_color(task.skill)))
        rarity_name, rarity_color = game.rarity(task.difficulty)
        rarity_chip = chip(rarity_name, rarity_color)
        rarity_chip.setToolTip(f"Значимость {task.importance} · Сложность {task.difficulty}")
        chips.addWidget(rarity_chip)
        due = due_text(task.due_date, task.done)
        if due:
            chips.addWidget(chip(due, config.OVERDUE_COLOR if task.is_overdue else c["muted"],
                                 filled=task.is_overdue))
        chips.addStretch(1)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.addLayout(top)
        text_col.addLayout(chips)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 10, 10)
        lay.setSpacing(10)
        lay.addWidget(self.check, 0, Qt.AlignTop)
        lay.addLayout(text_col, 1)

        if task.description:
            self.setToolTip(task.description)

        # Мягкая тень под карточкой
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 70 if themes.current() == themes.DARK else 28))
        self.setGraphicsEffect(shadow)

        self._apply_style(selected)

    def set_selected(self, selected: bool) -> None:
        """Меняет только оформление, не пересоздавая карточку."""
        self._apply_style(selected)

    def _apply_style(self, selected: bool) -> None:
        c = themes.colors()
        zone_color = config.ZONE_COLORS[self.task.zone]
        # Цвет левой полосы: красный для просроченных, иначе цвет зоны
        stripe = config.OVERDUE_COLOR if self.task.is_overdue else zone_color
        border = c["accent"] if selected else c["border"]
        bg = c["surface"]
        if self.task.is_overdue:
            bg = themes.mix(c["surface"], config.OVERDUE_COLOR, 0.10)
        title_color = c["muted"] if self.task.done else c["text"]

        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background: {bg};
                border: {2 if selected else 1}px solid {border};
                border-left: 4px solid {stripe};
                border-radius: 12px;
            }}
            QFrame#taskCard:hover {{ border-color: {c['accent'] if selected else themes.mix(c['border'], zone_color, 0.6)}; border-left: 4px solid {stripe}; }}
            QLabel#cardTitle {{ color: {title_color}; font-weight: 600; font-size: 10.5pt; }}
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
        act_edit = menu.addAction("✏️  Редактировать…")
        act_done = menu.addAction("↩️  Вернуть в работу" if self.task.done else "✅  Завершить квест")
        menu.addSeparator()
        act_del = menu.addAction("🗑️  Удалить…")
        chosen = menu.exec(event.globalPos())
        task_id, done = self.task.id, self.task.done
        if chosen is act_edit:
            self.controller.edit_task(task_id)
        elif chosen is act_done:
            self.controller.set_done(task_id, not done)
        elif chosen is act_del:
            self.controller.delete_task(task_id)
