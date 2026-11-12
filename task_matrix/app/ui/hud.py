"""
Карточка героя в шапке (в стиле виджета iOS):

  (🧙) Имя                    ◎  Опыт   120/200 XP   │ 🔥 5  дней подряд
       Уровень 4 · Ученик      ◎  Квесты 2/3          │ 🏆 3  из 14
       ━━━━━━━━━━──── 49/250   ◎  Неделя 4/7 дн.     │
"""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from .. import game
from . import themes
from .ios import ActivityRings, legend_row
from .widgets import avatar

NAME_SETTING = "player_name"
AVATAR_SETTING = "player_avatar"


def clear(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()


class PlayerHud(QFrame):
    def __init__(self, controller, db, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.setObjectName("card")

        self.avatar_host = QHBoxLayout()
        self.avatar_host.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel()
        self.name_label.setObjectName("h2")
        self.level_label = QLabel()
        self.level_label.setObjectName("muted")
        self.xp_bar = QProgressBar()
        self.xp_bar.setTextVisible(False)
        self.xp_label = QLabel()
        self.xp_label.setObjectName("muted")
        self.xp_label.setStyleSheet("font-size: 8.5pt;")

        info = QVBoxLayout()
        info.setSpacing(3)
        info.addWidget(self.name_label)
        info.addWidget(self.level_label)
        info.addSpacing(2)
        info.addWidget(self.xp_bar)
        info.addWidget(self.xp_label)
        info_host = QWidget()
        info_host.setLayout(info)
        info_host.setMinimumWidth(240)
        info_host.setMaximumWidth(380)

        # Мини-кольца активности + легенда
        self.rings = ActivityRings(70)
        self.rings_legend = QVBoxLayout()
        self.rings_legend.setSpacing(4)
        legend_host = QWidget()
        legend_host.setLayout(self.rings_legend)
        legend_host.setFixedWidth(220)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setObjectName("vsep")

        self.streak = QLabel()
        self.trophies = QLabel()
        right = QVBoxLayout()
        right.setSpacing(6)
        right.addStretch(1)
        right.addWidget(self.streak)
        right.addWidget(self.trophies)
        right.addStretch(1)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 18, 12)
        lay.setSpacing(14)
        lay.addLayout(self.avatar_host)
        lay.addWidget(info_host, 1)
        lay.addStretch(1)
        lay.addWidget(self.rings)
        lay.addWidget(legend_host)
        lay.addWidget(sep)
        lay.addLayout(right)

        controller.tasks_changed.connect(self.refresh)

    def refresh(self) -> None:
        c = themes.colors()
        stats = self.controller.stats()
        level, xp_in, xp_need = game.level_info(stats.total_xp)

        clear(self.avatar_host)
        self.avatar_host.addWidget(avatar(self.db.get_setting(AVATAR_SETTING, "🧙"), 58))
        self.name_label.setText(self.db.get_setting(NAME_SETTING, "Игрок"))
        self.level_label.setText(f"Уровень {level} · {game.title_for_level(level)}")
        self.xp_bar.setStyleSheet(themes.progress_style(c["accent"], 6))
        self.xp_bar.setRange(0, xp_need)
        self.xp_bar.setValue(xp_in)
        self.xp_label.setText(f"{xp_in} / {xp_need} XP до уровня {level + 1}")

        # Кольца: опыт за день, квесты дня, активные дни недели
        per_day = self.db.quests_per_day()
        today_xp = self.db.xp_per_day(1)[0][1]
        goal = self.controller.daily_goal()
        week = sum(1 for i in range(7) if per_day.get(date.today() - timedelta(days=i), 0) > 0)
        self.rings.set_rings([(today_xp, game.DAILY_XP_TARGET, c["ring_xp"]),
                              (stats.today, goal, c["ring_quests"]),
                              (week, 7, c["ring_week"])])
        clear(self.rings_legend)
        self.rings_legend.addStretch(1)
        for color, name, value in ((c["ring_xp"], "Опыт", f"{today_xp}/{game.DAILY_XP_TARGET} XP"),
                                   (c["ring_quests"], "Квесты дня", f"{stats.today}/{goal}"),
                                   (c["ring_week"], "Неделя", f"{week}/7 дн.")):
            self.rings_legend.addWidget(legend_row(color, name, value))
        self.rings_legend.addStretch(1)
        self.rings.setToolTip(f"Задание дня: {goal} квеста → +{game.DAILY_BONUS_XP} XP")

        unlocked = len(self.db.unlocked_achievements())
        self.streak.setText(f"🔥 <b style='font-size:13pt'>{stats.streak}</b> "
                            f"<span style='color:{c['muted']}'>дн. подряд</span>")
        self.trophies.setText(f"🏆 <b style='font-size:13pt'>{unlocked}</b> "
                              f"<span style='color:{c['muted']}'>из {len(game.ACHIEVEMENTS)}</span>")
        self.setStyleSheet(f"QFrame#vsep {{ background: {c['separator']}; }}")
