"""
Вкладка «Персонаж»: профиль игрока.

  ┌ Герой: аватар, имя, уровень, полоса опыта, ключевые цифры ┐
  ├ Активность за 14 дней (столбики XP)                       ┤
  ├ Навыки (уровень и прогресс каждого)  │  Журнал опыта       ┤
  └ Достижения (сетка плиток, закрытые — серые)               ┘
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QScrollArea,
    QVBoxLayout, QWidget,
)

from .. import game
from . import themes
from .hud import AVATAR_SETTING, NAME_SETTING
from .widgets import avatar, chip

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def panel(title: str) -> tuple[QFrame, QVBoxLayout]:
    """Скруглённая панель с заголовком; возвращает (рамка, layout для содержимого)."""
    frame = QFrame()
    frame.setObjectName("panel")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 14, 18, 16)
    lay.setSpacing(10)
    head = QLabel(title)
    head.setObjectName("h2")
    lay.addWidget(head)
    return frame, lay


def clear(layout) -> None:
    """Удаляет все виджеты и вложенные layout'ы."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


class ActivityChart(QWidget):
    """Столбчатая диаграмма опыта по дням, рисуется вручную через QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: list[tuple[date, int]] = []
        self.setMinimumHeight(150)

    def set_data(self, data: list[tuple[date, int]]) -> None:
        self.data = data
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return
        c = themes.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        label_h, value_h = 20, 16
        chart_h = h - label_h - value_h
        n = len(self.data)
        slot = w / n
        bar_w = min(30.0, slot * 0.6)
        peak = max((v for _, v in self.data), default=0) or 1

        small = QFont(self.font())
        small.setPointSizeF(8)
        p.setFont(small)
        for i, (day, xp) in enumerate(self.data):
            x = i * slot + (slot - bar_w) / 2
            bar_h = max(4.0, chart_h * xp / peak) if xp else 4.0
            y = value_h + chart_h - bar_h
            rect = QRectF(x, y, bar_w, bar_h)
            path = QPainterPath()
            path.addRoundedRect(rect, 6, 6)
            if xp:
                grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                grad.setColorAt(0, QColor(c["accent2"]))
                grad.setColorAt(1, QColor(c["accent"]))
                p.fillPath(path, grad)
                p.setPen(QColor(c["text"]))
                p.drawText(QRectF(i * slot, y - value_h, slot, value_h), Qt.AlignCenter, str(xp))
            else:
                p.fillPath(path, QColor(c["surface2"]))
            is_today = day == date.today()
            p.setPen(QColor(c["accent"] if is_today else c["muted"]))
            text = "сегодня" if is_today else f"{WEEKDAYS[day.weekday()]} {day.day}"
            p.drawText(QRectF(i * slot, h - label_h, slot, label_h), Qt.AlignCenter, text)
        p.end()


class ProfileView(QScrollArea):
    def __init__(self, controller, db, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.setWidgetResizable(True)

        host = QWidget()
        root = QVBoxLayout(host)
        root.setContentsMargins(14, 10, 14, 14)
        root.setSpacing(14)

        # Герой
        self.hero, hero_lay = panel("🧙 Персонаж")
        self.hero_body = QHBoxLayout()
        self.hero_body.setSpacing(18)
        hero_lay.addLayout(self.hero_body)
        root.addWidget(self.hero)

        # Активность
        act, act_lay = panel("📊 Опыт за 14 дней")
        self.chart = ActivityChart()
        act_lay.addWidget(self.chart)
        root.addWidget(act)

        # Навыки + журнал в одну строку
        row = QHBoxLayout()
        row.setSpacing(14)
        skills, skills_lay = panel("⚡ Навыки")
        self.skills_grid = QGridLayout()
        self.skills_grid.setHorizontalSpacing(12)
        self.skills_grid.setVerticalSpacing(10)
        skills_lay.addLayout(self.skills_grid)
        skills_lay.addStretch(1)
        log, log_lay = panel("📜 Журнал")
        self.log_box = QVBoxLayout()
        self.log_box.setSpacing(6)
        log_lay.addLayout(self.log_box)
        log_lay.addStretch(1)
        row.addWidget(skills, 3)
        row.addWidget(log, 2)
        root.addLayout(row)

        # Достижения
        ach, ach_lay = panel("🏆 Достижения")
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
        self.chart.set_data(self.db.xp_per_day(14))
        self._fill_skills(stats, c)
        self._fill_log(c)
        self._fill_achievements(c)

    def _fill_hero(self, stats: game.PlayerStats, c: dict) -> None:
        clear(self.hero_body)
        level, xp_in, xp_need = game.level_info(stats.total_xp)
        self.hero_body.addWidget(avatar(self.db.get_setting(AVATAR_SETTING, "🧙"), 104))

        col = QVBoxLayout()
        col.setSpacing(6)
        name = QLabel(self.db.get_setting(NAME_SETTING, "Игрок"))
        name.setObjectName("h1")
        title = QLabel(f"Уровень {level} · {game.title_for_level(level)}")
        title.setStyleSheet(f"color: {c['gold']}; font-weight: bold; font-size: 11pt;")
        bar = QProgressBar()
        bar.setTextVisible(False)
        bar.setStyleSheet(themes.progress_style(c["accent"], c["accent2"], 14))
        bar.setRange(0, xp_need)
        bar.setValue(xp_in)
        hint = QLabel(f"{xp_in} / {xp_need} XP до следующего уровня")
        hint.setObjectName("muted")
        col.addWidget(name)
        col.addWidget(title)
        col.addWidget(bar)
        col.addWidget(hint)
        col.addStretch(1)
        self.hero_body.addLayout(col, 1)

        numbers = QGridLayout()
        numbers.setSpacing(8)
        tiles = [
            ("✨", str(stats.total_xp), "всего опыта"),
            ("⚔️", str(stats.completed), "квестов пройдено"),
            ("🐉", str(stats.legendary), "легендарных"),
            ("🔥", str(stats.streak), "дней подряд"),
            ("⏰", str(stats.on_time), "в срок"),
            ("💥", str(stats.best_day), "рекорд за день"),
        ]
        for i, (icon, value, caption) in enumerate(tiles):
            numbers.addWidget(self._number_tile(icon, value, caption, c), i // 3, i % 3)
        self.hero_body.addLayout(numbers)

    @staticmethod
    def _number_tile(icon: str, value: str, caption: str, c: dict) -> QFrame:
        tile = QFrame()
        tile.setStyleSheet(f"QFrame {{ background: {c['surface2']}; border-radius: 12px; }}")
        tile.setMinimumWidth(118)
        lay = QVBoxLayout(tile)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(0)
        top = QLabel(f"{icon}  <b style='font-size:15pt'>{value}</b>")
        cap = QLabel(caption)
        cap.setStyleSheet(f"color: {c['muted']}; font-size: 8pt;")
        lay.addWidget(top)
        lay.addWidget(cap)
        return tile

    def _fill_skills(self, stats: game.PlayerStats, c: dict) -> None:
        clear(self.skills_grid)
        for row, (key, (name, icon, color)) in enumerate(game.SKILLS.items()):
            xp = stats.skill_xp.get(key, 0)
            level, xp_in, xp_need = game.skill_level_info(xp)
            label = QLabel(f"{icon}  {name}")
            label.setStyleSheet("font-weight: 600;")
            label.setMinimumWidth(130)
            bar = QProgressBar()
            bar.setTextVisible(False)
            bar.setStyleSheet(themes.progress_style(color, themes.mix(color, "#ffffff", 0.35), 9))
            bar.setRange(0, xp_need)
            bar.setValue(xp_in)
            bar.setToolTip(f"{xp_in} / {xp_need} XP до следующего уровня навыка")
            lvl = chip(f"Ур. {level}", color)
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
        for e in events:
            amount = e["amount"]
            color = c["gold"] if amount > 0 else "#ef4f5f"
            icon = {"quest": game.skill_icon(e["skill"] or "other"), "daily": "🎯", "revoke": "↩️"}.get(e["kind"], "✨")
            line = QHBoxLayout()
            text = QLabel(f"{icon}  {e['note']}")
            text.setToolTip(e["ts"])
            text.setMinimumWidth(10)
            value = QLabel(f"{'+' if amount > 0 else ''}{amount} XP")
            value.setStyleSheet(f"color: {color}; font-weight: bold;")
            line.addWidget(text, 1)
            line.addWidget(value)
            self.log_box.addLayout(line)

    def _fill_achievements(self, c: dict) -> None:
        clear(self.ach_grid)
        unlocked = self.db.unlocked_achievements()
        columns = 4
        for i, ach in enumerate(game.ACHIEVEMENTS):
            got = ach.key in unlocked
            tile = QFrame()
            border = c["gold"] if got else c["border"]
            bg = themes.mix(c["surface2"], c["gold"], 0.10) if got else c["surface2"]
            tile.setStyleSheet(f"QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 12px; }}"
                               f" QLabel {{ border: none; background: transparent; }}")
            lay = QHBoxLayout(tile)
            lay.setContentsMargins(10, 8, 10, 8)
            icon = QLabel(ach.icon if got else "🔒")
            icon.setStyleSheet("font-size: 22px;")
            text_col = QVBoxLayout()
            text_col.setSpacing(0)
            name = QLabel(ach.title)
            name.setStyleSheet(f"font-weight: bold; color: {c['text'] if got else c['muted']};")
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
