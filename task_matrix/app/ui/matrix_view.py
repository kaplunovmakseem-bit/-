"""
Вкладка «Квесты»: матрица 2×2 из четырёх зон.

Каждая зона оформлена как список в «Напоминаниях» iOS:

  ┌──────────────────────────────────┐
  │ (⚡)                        3  ⤢ │  цветной круг с иконкой, число активных
  │ Сделать сейчас                   │
  │ Значимо и просто · 240 XP        │
  │ ◯ Квест …                 +70 XP │  строки-карточки с тонкими разделителями
  └──────────────────────────────────┘

MatrixView
 └── ZoneWidget × 4
      ├── ZoneHeader (двойной клик — раскрыть зону)
      └── QScrollArea со списком TaskCard
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from .. import config, game
from ..models import Task
from . import themes
from .ios import IOSSwitch
from .task_card import TASK_MIME, TaskCard


class ZoneHeader(QFrame):
    """Заголовок зоны. Двойной клик по нему раскрывает зону на всё окно."""

    double_clicked = Signal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit()


class ZoneWidget(QFrame):
    """Одна зона матрицы. Принимает перетаскиваемые карточки."""

    expand_toggled = Signal(str)   # ключ зоны
    card_clicked = Signal(int)     # id задачи

    def __init__(self, zone: str, controller, parent=None):
        super().__init__(parent)
        self.zone = zone
        self.controller = controller
        self.setObjectName("zone")
        self.setAcceptDrops(True)  # зона — цель для drag & drop
        self._drag_over = False

        # --- Заголовок ---
        self.header = ZoneHeader()
        self.header.setObjectName("zoneHeader")
        self.header.setToolTip("Двойной клик — раскрыть/свернуть зону")
        self.header.double_clicked.connect(lambda: self.expand_toggled.emit(self.zone))

        self.icon_label = QLabel(config.ZONE_ICONS[zone])
        self.icon_label.setObjectName("zoneIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(34, 34)

        self.count_label = QLabel("0")
        self.count_label.setObjectName("zoneCount")

        self.expand_btn = QPushButton("⤢")
        self.expand_btn.setObjectName("expandBtn")
        self.expand_btn.setFixedSize(26, 26)
        self.expand_btn.setToolTip("Раскрыть/свернуть зону")
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.clicked.connect(lambda: self.expand_toggled.emit(self.zone))

        top_row = QHBoxLayout()
        top_row.addWidget(self.icon_label)
        top_row.addStretch(1)
        top_row.addWidget(self.count_label)
        top_row.addWidget(self.expand_btn, 0, Qt.AlignTop)

        self.title_label = QLabel(config.ZONE_TITLES[zone])
        self.title_label.setObjectName("zoneTitle")
        self.hint_label = QLabel(config.ZONE_HINTS[zone])
        self.hint_label.setObjectName("zoneHint")

        h = QVBoxLayout(self.header)
        h.setContentsMargins(14, 12, 10, 8)
        h.setSpacing(2)
        h.addLayout(top_row)
        h.addSpacing(4)
        h.addWidget(self.title_label)
        h.addWidget(self.hint_label)

        # --- Список карточек (с прокруткой) ---
        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(6, 0, 6, 8)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch(1)

        self.empty_label = QLabel("Нет квестов\nПеретащите сюда карточку")
        self.empty_label.setObjectName("muted")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setMinimumHeight(70)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_host)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.header)
        lay.addWidget(scroll, 1)

        self.apply_style()

    # --- Оформление ----------------------------------------------------------
    def apply_style(self) -> None:
        c = themes.colors()
        accent = themes.zone_color(self.zone)
        border = f"2px solid {accent}" if self._drag_over else "2px solid transparent"
        bg = themes.mix(c["surface"], accent, 0.06) if self._drag_over else c["surface"]
        self.setStyleSheet(f"""
            QFrame#zone {{ background: {bg}; border: {border}; border-radius: 18px; }}
            QFrame#zoneHeader {{ background: transparent; border: none; }}
            QLabel#zoneIcon {{ background: {accent}; border-radius: 17px; font-size: 15px; }}
            QLabel#zoneTitle {{ font-size: 12pt; font-weight: 700; color: {c['text']}; }}
            QLabel#zoneHint {{ font-size: 8.5pt; color: {c['muted']}; }}
            QLabel#zoneCount {{ font-size: 22pt; font-weight: 800; color: {c['text']}; }}
            QPushButton#expandBtn {{
                background: transparent; border: none; font-size: 12pt; color: {c['faint']}; padding: 0;
            }}
            QPushButton#expandBtn:hover {{ color: {accent}; }}
        """)

    # --- Заполнение ----------------------------------------------------------
    def set_tasks(self, tasks: list[Task], selected_id: Optional[int]) -> None:
        # Удаляем старые карточки (deleteLater безопасен даже во время drag & drop)
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None and w is not self.empty_label:
                w.hide()          # прячем сразу, удалится чуть позже
                w.deleteLater()
        self.empty_label.setParent(None)

        if not tasks:
            self.list_layout.insertWidget(0, self.empty_label)
        for i, task in enumerate(tasks):
            card = TaskCard(task, self.controller, selected=(task.id == selected_id),
                            last=(i == len(tasks) - 1))
            card.clicked.connect(self.card_clicked)
            self.list_layout.insertWidget(i, card)

        active = [t for t in tasks if not t.done]
        done = len(tasks) - len(active)
        self.count_label.setText(str(len(active)))
        self.count_label.setToolTip(f"Активных: {len(active)}, выполнено: {done}")
        # В подзаголовке — сколько опыта «лежит» в зоне
        loot = sum(game.xp_for_task(t, date.today()) for t in active)
        hint = config.ZONE_HINTS[self.zone]
        self.hint_label.setText(f"{hint} · {loot} XP" if loot else hint)

    # --- Drag & drop ---------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(TASK_MIME):
            event.acceptProposedAction()
            self._drag_over = True
            self.apply_style()

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self.apply_style()

    def dropEvent(self, event):
        self._drag_over = False
        self.apply_style()
        if not event.mimeData().hasFormat(TASK_MIME):
            return
        task_id = int(bytes(event.mimeData().data(TASK_MIME)).decode())
        event.acceptProposedAction()
        self.controller.move_to_zone(task_id, self.zone)


class MatrixView(QWidget):
    """Вкладка с матрицей 2×2."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self.controller = controller
        self.selected_id: Optional[int] = None
        self.expanded_zone: Optional[str] = None

        # Тумблер iOS «Показывать выполненные»
        self.show_done = IOSSwitch()
        self.show_done.setChecked(True)
        self.show_done.toggled.connect(self.refresh)
        show_label = QLabel("Выполненные")
        show_label.setObjectName("muted")

        hint = QLabel("Перетаскивайте квесты между зонами · двойной клик по заголовку раскрывает зону")
        hint.setObjectName("muted")
        hint.setStyleSheet("font-size: 9pt;")

        top = QHBoxLayout()
        top.addWidget(hint, 1)
        top.addWidget(show_label)
        top.addWidget(self.show_done)

        self.grid = QGridLayout()
        self.grid.setSpacing(16)
        self.zones: dict[str, ZoneWidget] = {}
        for zone, (row, col) in config.ZONE_GRID.items():
            w = ZoneWidget(zone, controller)
            w.expand_toggled.connect(self.toggle_expand)
            w.card_clicked.connect(self._on_card_clicked)
            self.grid.addWidget(w, row, col)
            self.zones[zone] = w
        self._reset_stretch()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 16)
        lay.setSpacing(10)
        lay.addLayout(top)
        lay.addLayout(self.grid, 1)

        controller.tasks_changed.connect(self.refresh)

    def _reset_stretch(self) -> None:
        for i in range(2):
            self.grid.setRowStretch(i, 1)
            self.grid.setColumnStretch(i, 1)

    def toggle_expand(self, zone: str) -> None:
        """
        Раскрывает зону на всё окно или возвращает обычную матрицу.
        Остальные зоны прячутся, а их строке/столбцу ставится нулевой
        коэффициент растяжения, поэтому оставшаяся зона занимает всё место.
        """
        if self.expanded_zone == zone:
            self.expanded_zone = None
            for w in self.zones.values():
                w.show()
            self._reset_stretch()
            return

        self.expanded_zone = zone
        row, col = config.ZONE_GRID[zone]
        for z, w in self.zones.items():
            w.setVisible(z == zone)
        for i in range(2):
            self.grid.setRowStretch(i, 1 if i == row else 0)
            self.grid.setColumnStretch(i, 1 if i == col else 0)

    def _on_card_clicked(self, task_id: int) -> None:
        # Только перекрашиваем фон: пересоздавать карточки здесь нельзя,
        # иначе пропадёт карточка, которую пользователь начинает тащить.
        self.selected_id = task_id
        for zone in self.zones.values():
            for card in zone.findChildren(TaskCard):
                card.set_selected(card.task.id == task_id)

    def selected_task_id(self) -> Optional[int]:
        return self.selected_id

    def refresh(self) -> None:
        """Перерисовывает все зоны по актуальным данным из базы."""
        tasks = self.controller.tasks()
        if not self.show_done.isChecked():
            tasks = [t for t in tasks if not t.done]
        if self.selected_id is not None and all(t.id != self.selected_id for t in tasks):
            self.selected_id = None

        by_zone: dict[str, list[Task]] = {z: [] for z in self.zones}
        for t in tasks:
            by_zone[t.zone].append(t)
        for zone, widget in self.zones.items():
            widget.set_tasks(by_zone[zone], self.selected_id)

    def restyle(self) -> None:
        """Вызывается после смены темы."""
        for w in self.zones.values():
            w.apply_style()
        self.refresh()
