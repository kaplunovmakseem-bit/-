"""
Игровая панель (HUD) в шапке окна:
  аватар · имя · уровень и звание · полоса опыта · серия · ежедневное задание
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget,
)

from .. import game
from . import themes
from .widgets import avatar, chip

NAME_SETTING = "player_name"
AVATAR_SETTING = "player_avatar"


class StatTile(QFrame):
    """Плитка «иконка + значение + подпись», например 🔥 5 · дней подряд."""

    def __init__(self, icon: str, caption: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statTile")
        self.icon = QLabel(icon)
        self.icon.setStyleSheet("font-size: 18px;")
        self.value = QLabel("0")
        self.value.setStyleSheet("font-size: 13pt; font-weight: 800;")
        self.caption = QLabel(caption)
        self.caption.setObjectName("muted")
        self.caption.setStyleSheet("font-size: 8pt;")

        col = QVBoxLayout()
        col.setSpacing(0)
        col.addWidget(self.value)
        col.addWidget(self.caption)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 12, 6)
        lay.setSpacing(8)
        lay.addWidget(self.icon)
        lay.addLayout(col)

        # Мини-полоса (используется у ежедневного задания)
        self.bar: QProgressBar | None = None

    def add_bar(self) -> QProgressBar:
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.layout().itemAt(1).layout().addWidget(self.bar)
        return self.bar


class PlayerHud(QFrame):
    def __init__(self, controller, db, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.setObjectName("panel")

        self.avatar_host = QHBoxLayout()
        self.avatar_host.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel()
        self.name_label.setObjectName("h2")
        self.level_chip_host = QHBoxLayout()
        self.level_chip_host.setContentsMargins(0, 0, 0, 0)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_row.addWidget(self.name_label)
        name_row.addLayout(self.level_chip_host)
        name_row.addStretch(1)

        self.xp_bar = QProgressBar()
        self.xp_bar.setTextVisible(False)
        self.xp_label = QLabel()
        self.xp_label.setObjectName("muted")
        self.xp_label.setStyleSheet("font-size: 8.5pt;")

        info = QVBoxLayout()
        info.setSpacing(4)
        info.addLayout(name_row)
        info.addWidget(self.xp_bar)
        info.addWidget(self.xp_label)

        info_host = QWidget()
        info_host.setLayout(info)
        info_host.setMinimumWidth(260)
        info_host.setMaximumWidth(420)

        self.streak = StatTile("🔥", "дней подряд")
        self.daily = StatTile("🎯", "задание дня")
        self.daily_bar = self.daily.add_bar()
        self.quests = StatTile("⚔️", "квестов пройдено")
        self.trophies = StatTile("🏆", "достижений")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)
        lay.addLayout(self.avatar_host)
        lay.addWidget(info_host, 1)
        for tile in (self.streak, self.daily, self.quests, self.trophies):
            lay.addWidget(tile)

        controller.tasks_changed.connect(self.refresh)

    def _replace(self, layout, widget) -> None:
        """Заменяет единственный виджет внутри layout."""
        while layout.count():
            old = layout.takeAt(0).widget()
            if old:
                old.hide()
                old.deleteLater()
        layout.addWidget(widget)

    def refresh(self) -> None:
        c = themes.colors()
        stats = self.controller.stats()
        level, xp_in, xp_need = game.level_info(stats.total_xp)

        self._replace(self.avatar_host, avatar(self.db.get_setting(AVATAR_SETTING, "🧙"), 60))
        self.name_label.setText(self.db.get_setting(NAME_SETTING, "Игрок"))
        self._replace(self.level_chip_host, chip(f"Ур. {level} · {game.title_for_level(level)}", c["gold"]))

        self.xp_bar.setStyleSheet(themes.progress_style(c["accent"], c["accent2"], 12))
        self.xp_bar.setRange(0, xp_need)
        self.xp_bar.setValue(xp_in)
        self.xp_label.setText(f"{xp_in} / {xp_need} XP до {level + 1} уровня · всего {stats.total_xp} XP")

        goal = self.controller.daily_goal()
        self.streak.value.setText(str(stats.streak))
        self.daily.value.setText(f"{min(stats.today, goal)}/{goal}" + (" ✓" if stats.today >= goal else ""))
        self.daily.setToolTip(f"Выполните {goal} квеста за день — получите +{game.DAILY_BONUS_XP} XP")
        self.daily_bar.setStyleSheet(themes.progress_style(c["gold"], "#fb923c", 5))
        self.daily_bar.setRange(0, goal)
        self.daily_bar.setValue(min(stats.today, goal))
        self.quests.value.setText(str(stats.completed))
        unlocked = len(self.db.unlocked_achievements())
        self.trophies.value.setText(f"{unlocked}/{len(game.ACHIEVEMENTS)}")

        self.setStyleSheet(f"""
            QFrame#statTile {{ background: {c['surface2']}; border-radius: 12px; border: none; }}
        """)
