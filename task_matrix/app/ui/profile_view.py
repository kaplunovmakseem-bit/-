"""
Вкладка «Профиль» в стиле страницы Apple ID:

        (  🧙  )
         Максим
   Уровень 4 · Ученик
   ━━━━━━━──────────  49 / 250 XP
  [всего XP] [квестов] [легендарных] [серия] [в срок] [рекорд]

  НАВЫКИ                         ЖУРНАЛ
  💪 Сила   ━━━──  ур. 2          ✨ Сдать отчёт        +103 XP
  …                               …
  ДОСТИЖЕНИЯ
  [🎯 Первый шаг] [⚔️ Охотник] …
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QScrollArea,
    QVBoxLayout, QWidget,
)

from .. import game
from . import themes
from .hud import AVATAR_SETTING, NAME_SETTING
from .ios import card
from .settings_dialog import section_title
from .widgets import avatar


def clear(layout) -> None:
    """Удаляет все виджеты и вложенные layout'ы."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


class ProfileView(QScrollArea):
    def __init__(self, controller, db, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.setWidgetResizable(True)

        host = QWidget()
        host.setObjectName("page")
        root = QVBoxLayout(host)
        root.setContentsMargins(20, 4, 20, 20)
        root.setSpacing(8)

        # Герой (по центру)
        self.hero, hero_lay = card()
        self.hero_body = QVBoxLayout()
        self.hero_body.setSpacing(6)
        hero_lay.addLayout(self.hero_body)
        root.addWidget(self.hero)
        root.addSpacing(10)

        # Навыки + журнал
        row = QHBoxLayout()
        row.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(6)
        left.addWidget(section_title("Навыки"))
        skills, skills_lay = card()
        self.skills_grid = QGridLayout()
        self.skills_grid.setHorizontalSpacing(12)
        self.skills_grid.setVerticalSpacing(12)
        skills_lay.addLayout(self.skills_grid)
        left.addWidget(skills)
        left.addStretch(1)
        right = QVBoxLayout()
        right.setSpacing(6)
        right.addWidget(section_title("Журнал"))
        log, log_lay = card()
        self.log_box = QVBoxLayout()
        self.log_box.setSpacing(0)
        log_lay.addLayout(self.log_box)
        right.addWidget(log)
        right.addStretch(1)
        row.addLayout(left, 3)
        row.addLayout(right, 2)
        root.addLayout(row)
        root.addSpacing(10)

        # Достижения
        self.ach_title = section_title("Достижения")
        root.addWidget(self.ach_title)
        ach, ach_lay = card()
        self.ach_grid = QGridLayout()
        self.ach_grid.setSpacing(10)
        ach_lay.addLayout(self.ach_grid)
        root.addWidget(ach)
        root.addStretch(1)

        self.setWidget(host)
        controller.tasks_changed.connect(self.refresh)

    # --- Заполнение ----------------------------------------------------------
    def refresh(self) -> None:
        c = themes.colors()
        stats = self.controller.stats()
        self._fill_hero(stats, c)
        self._fill_skills(stats, c)
        self._fill_log(c)
        self._fill_achievements(c)

    def _fill_hero(self, stats: game.PlayerStats, c: dict) -> None:
        clear(self.hero_body)
        level, xp_in, xp_need = game.level_info(stats.total_xp)

        av = avatar(self.db.get_setting(AVATAR_SETTING, "🧙"), 96)
        self.hero_body.addWidget(av, 0, Qt.AlignHCenter)
        name = QLabel(self.db.get_setting(NAME_SETTING, "Игрок"))
        name.setObjectName("h1")
        name.setAlignment(Qt.AlignCenter)
        title = QLabel(f"Уровень {level} · {game.title_for_level(level)}")
        title.setObjectName("muted")
        title.setAlignment(Qt.AlignCenter)
        self.hero_body.addWidget(name)
        self.hero_body.addWidget(title)

        bar = QProgressBar()
        bar.setTextVisible(False)
        bar.setStyleSheet(themes.progress_style(c["accent"], 8))
        bar.setRange(0, xp_need)
        bar.setValue(xp_in)
        bar.setFixedWidth(360)
        hint = QLabel(f"{xp_in} / {xp_need} XP до уровня {level + 1}")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 8.5pt;")
        self.hero_body.addSpacing(4)
        self.hero_body.addWidget(bar, 0, Qt.AlignHCenter)
        self.hero_body.addWidget(hint)
        self.hero_body.addSpacing(10)

        numbers = QHBoxLayout()
        numbers.setSpacing(10)
        tiles = [
            (str(stats.total_xp), "всего XP"),
            (str(stats.completed), "квестов"),
            (str(stats.legendary), "легендарных"),
            (str(stats.streak), "дн. подряд"),
            (str(stats.on_time), "в срок"),
            (str(stats.best_day), "рекорд за день"),
        ]
        for value, caption in tiles:
            numbers.addWidget(self._number_tile(value, caption))
        self.hero_body.addLayout(numbers)

    @staticmethod
    def _number_tile(value: str, caption: str) -> QFrame:
        tile = QFrame()
        tile.setObjectName("tile")
        lay = QVBoxLayout(tile)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(0)
        top = QLabel(value)
        top.setAlignment(Qt.AlignCenter)
        top.setStyleSheet("font-size: 17pt; font-weight: 800;")
        cap = QLabel(caption)
        cap.setAlignment(Qt.AlignCenter)
        cap.setObjectName("caption")
        lay.addWidget(top)
        lay.addWidget(cap)
        return tile

    def _fill_skills(self, stats: game.PlayerStats, c: dict) -> None:
        clear(self.skills_grid)
        for row, (key, (name, icon, _, _)) in enumerate(game.SKILLS.items()):
            color = themes.skill_color(key)
            xp = stats.skill_xp.get(key, 0)
            level, xp_in, xp_need = game.skill_level_info(xp)
            label = QLabel(f"{icon}  {name}")
            label.setMinimumWidth(130)
            bar = QProgressBar()
            bar.setTextVisible(False)
            bar.setStyleSheet(themes.progress_style(color, 6))
            bar.setRange(0, xp_need)
            bar.setValue(xp_in)
            bar.setToolTip(f"{xp_in} / {xp_need} XP до следующего уровня навыка")
            lvl = QLabel(f"ур. {level}")
            lvl.setObjectName("muted")
            lvl.setMinimumWidth(42)
            lvl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.skills_grid.addWidget(label, row, 0)
            self.skills_grid.addWidget(bar, row, 1)
            self.skills_grid.addWidget(lvl, row, 2)
        self.skills_grid.setColumnStretch(1, 1)

    def _fill_log(self, c: dict) -> None:
        clear(self.log_box)
        events = self.db.recent_events(10)
        if not events:
            empty = QLabel("Пока пусто. Завершите первый квест!")
            empty.setObjectName("muted")
            self.log_box.addWidget(empty)
            return
        for i, e in enumerate(events):
            amount = e["amount"]
            icon = {"quest": game.skill_icon(e["skill"] or "other"), "daily": "🎯", "revoke": "↩️"}.get(e["kind"], "✨")
            line = QHBoxLayout()
            line.setContentsMargins(0, 7, 0, 7)
            text = QLabel(f"{icon}  {e['note']}")
            text.setToolTip(e["ts"])
            text.setMinimumWidth(10)
            value = QLabel(f"{'+' if amount > 0 else ''}{amount} XP")
            value.setStyleSheet(f"color: {c['gold'] if amount > 0 else c['danger']}; font-weight: 700;")
            line.addWidget(text, 1)
            line.addWidget(value)
            self.log_box.addLayout(line)
            if i < len(events) - 1:
                sep = QFrame()
                sep.setObjectName("separator")
                self.log_box.addWidget(sep)

    def _fill_achievements(self, c: dict) -> None:
        clear(self.ach_grid)
        unlocked = self.db.unlocked_achievements()
        self.ach_title.setText(f"ДОСТИЖЕНИЯ · {len(unlocked)} ИЗ {len(game.ACHIEVEMENTS)}")
        columns = 4
        for i, ach in enumerate(game.ACHIEVEMENTS):
            got = ach.key in unlocked
            tile = QFrame()
            tile.setObjectName("tile")
            lay = QHBoxLayout(tile)
            lay.setContentsMargins(10, 10, 10, 10)
            icon = QLabel(ach.icon if got else "🔒")
            icon.setAlignment(Qt.AlignCenter)
            icon.setFixedSize(40, 40)
            bg = themes.rgba(c["gold"], 0.18) if got else c["fill"]
            icon.setStyleSheet(f"background: {bg}; border-radius: 20px; font-size: 20px;")
            text_col = QVBoxLayout()
            text_col.setSpacing(0)
            name = QLabel(ach.title)
            name.setStyleSheet(f"font-weight: 700; color: {c['text'] if got else c['muted']};")
            desc = QLabel(ach.description)
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {c['muted']}; font-size: 8pt;")
            text_col.addWidget(name)
            text_col.addWidget(desc)
            lay.addWidget(icon)
            lay.addLayout(text_col, 1)
            if got:
                tile.setToolTip(f"Получено: {unlocked[ach.key]}")
            self.ach_grid.addWidget(tile, i // columns, i % columns)
        for col in range(columns):
            self.ach_grid.setColumnStretch(col, 1)
