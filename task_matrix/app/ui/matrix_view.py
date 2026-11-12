"""
Главная вкладка: матрица 2×2 из четырёх зон.

MatrixView
 └── ZoneWidget × 4
      ├── ZoneHeader (название, подсказка, счётчик; двойной клик — раскрыть)
      └── QScrollArea со списком TaskCard
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from .. import config, game
from ..models import Task
from . import themes
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
        self.icon_label.setFixedSize(38, 38)
        self.title_label = QLabel(config.ZONE_TITLES[zone])
        self.title_label.setObjectName("zoneTitle")
        self.hint_label = QLabel(config.ZONE_HINTS[zone])
        self.hint_label.setObjectName("muted")
        self.count_label = QLabel("0")
        self.count_label.setObjectName("zoneCount")
        self.count_label.setAlignment(Qt.AlignCenter)

        self.expand_btn = QPushButton("⤢")
        self.expand_btn.setObjectName("expandBtn")
        self.expand_btn.setFixedSize(28, 28)
        self.expand_btn.setToolTip("Раскрыть/свернуть зону")
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.clicked.connect(lambda: self.expand_toggled.emit(self.zone))

        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(self.title_label)
        titles.addWidget(self.hint_label)

        h = QHBoxLayout(self.header)
        h.setContentsMargins(12, 10, 10, 10)
        h.setSpacing(10)
        h.addWidget(self.icon_label)
        h.addLayout(titles, 1)
        h.addWidget(self.count_label)
        h.addWidget(self.expand_btn)

        # --- Список карточек (с прокруткой) ---
        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(10, 8, 10, 12)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)

        self.empty_label = QLabel("Здесь пока пусто\nПеретащите сюда квест")
        self.empty_label.setObjectName("muted")
        self.empty_label.setAlignment(Qt.AlignCenter)

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
        accent = config.ZONE_COLORS[self.zone]
        bg = themes.zone_background(accent)
        border = themes.rgba(accent, 0.35)
        if self._drag_over:
            bg = themes.mix(bg, accent, 0.18)  # подсветка при наведении карточки
            border = accent
        self.setStyleSheet(f"""
            QFrame#zone {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {themes.mix(bg, accent, 0.06)}, stop:1 {bg});
                border: {2 if self._drag_over else 1}px solid {border};
                border-radius: 18px;
            }}
            QFrame#zoneHeader {{ background: transparent; border: none; }}
            QLabel#zoneIcon {{
                background: {themes.rgba(accent, 0.18)}; border-radius: 12px; font-size: 17px;
            }}
            QLabel#zoneTitle {{ font-size: 13pt; font-weight: 800; color: {c['text']}; }}
            QLabel#zoneCount {{
                background: {accent}; color: white; font-weight: bold;
                border-radius: 12px; min-width: 24px; min-height: 24px; padding: 0 7px;
            }}
            QPushButton#expandBtn {{
                background: transparent; border: none; font-size: 14pt; color: {c['muted']}; padding: 0;
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
            card = TaskCard(task, self.controller, selected=(task.id == selected_id))
            card.clicked.connect(self.card_clicked)
            self.list_layout.insertWidget(i, card)

        active = [t for t in tasks if not t.done]
        done = len(tasks) - len(active)
        self.count_label.setText(str(len(active)))
        self.count_label.setToolTip(f"Активных: {len(active)}, выполнено: {done}")
        # В подзаголовке — сколько опыта «лежит» в зоне
        loot = sum(game.xp_for_task(t, date.today()) for t in active)
        hint = config.ZONE_HINTS[self.zone]
        self.hint_label.setText(f"{hint} · 🪙 {loot} XP" if loot else hint)

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
        self.controller = controller
        self.selected_id: Optional[int] = None
        self.expanded_zone: Optional[str] = None

        self.show_done = QCheckBox("Показывать выполненные")
        self.show_done.setChecked(True)
        self.show_done.toggled.connect(self.refresh)

        hint = QLabel("Перетаскивайте квесты между зонами · двойной клик по заголовку раскрывает зону")
        hint.setObjectName("muted")

        top = QHBoxLayout()
        top.addWidget(hint, 1)
        top.addWidget(self.show_done)

        self.grid = QGridLayout()
        self.grid.setSpacing(14)
        self.zones: dict[str, ZoneWidget] = {}
        for zone, (row, col) in config.ZONE_GRID.items():
            w = ZoneWidget(zone, controller)
            w.expand_toggled.connect(self.toggle_expand)
            w.card_clicked.connect(self._on_card_clicked)
            self.grid.addWidget(w, row, col)
            self.zones[zone] = w
        self._reset_stretch()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 6, 14, 14)
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
        # Только перекрашиваем рамки: пересоздавать карточки здесь нельзя,
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
