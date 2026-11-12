"""
Вкладка «Статистика»: все диаграммы в одном месте.

  [Кольца активности сегодня]      [Итоги: всего XP, квесты, серия, среднее]
  [Опыт по дням — столбцы, переключатель 7 / 14 / 30 дней               ]
  [Накопленный опыт — линия]       [Опыт по навыкам — кольцевая диаграмма]
  [Навыки персонажа — «паутина»]   [Активные квесты по зонам — полосы    ]
  [Календарь активности за 20 недель                                    ]
"""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from .. import config, game
from . import themes
from .charts import BarChart, DonutChart, HBarChart, Heatmap, LineChart, RadarChart
from .ios import ActivityRings, Segmented, card, legend_row


def clear(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


class StatsView(QScrollArea):
    def __init__(self, controller, db, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.setWidgetResizable(True)
        self.days = 14

        host = QWidget()
        host.setObjectName("page")
        grid = QGridLayout(host)
        grid.setContentsMargins(20, 4, 20, 20)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        # --- Кольца активности ---
        rings_card, lay = card("Активность сегодня", "Закройте все три кольца")
        row = QHBoxLayout()
        row.setSpacing(18)
        self.rings = ActivityRings(150)
        row.addWidget(self.rings)
        self.rings_legend = QVBoxLayout()
        self.rings_legend.setSpacing(10)
        row.addLayout(self.rings_legend, 1)
        lay.addLayout(row)
        grid.addWidget(rings_card, 0, 0)

        # --- Итоги ---
        totals_card, lay = card("Итоги")
        self.totals = QGridLayout()
        self.totals.setSpacing(10)
        lay.addLayout(self.totals)
        lay.addStretch(1)
        grid.addWidget(totals_card, 0, 1)

        # --- Опыт по дням ---
        bars_card, lay = card()
        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(0)
        t = QLabel("Опыт по дням")
        t.setObjectName("h2")
        self.bars_sub = QLabel()
        self.bars_sub.setObjectName("muted")
        titles.addWidget(t)
        titles.addWidget(self.bars_sub)
        head.addLayout(titles, 1)
        self.period = Segmented([("7 дн.", 7), ("14 дн.", 14), ("30 дн.", 30)])
        self.period.set_value(self.days)
        self.period.changed.connect(self._set_days)
        head.addWidget(self.period, 0, Qt.AlignTop)
        lay.addLayout(head)
        self.bars = BarChart("accent")
        lay.addWidget(self.bars)
        grid.addWidget(bars_card, 1, 0, 1, 2)

        # --- Накопленный опыт ---
        line_card, lay = card("Накопленный опыт", "Общий XP за 30 дней")
        self.line = LineChart("ring_xp")
        lay.addWidget(self.line)
        grid.addWidget(line_card, 2, 0)

        # --- Опыт по навыкам ---
        donut_card, lay = card("Опыт по навыкам")
        row = QHBoxLayout()
        self.donut = DonutChart("XP всего")
        self.donut.setMinimumSize(200, 200)
        row.addWidget(self.donut, 1)
        self.donut_legend = QVBoxLayout()
        self.donut_legend.setSpacing(6)
        row.addLayout(self.donut_legend, 1)
        lay.addLayout(row)
        grid.addWidget(donut_card, 2, 1)

        # --- Навыки персонажа ---
        radar_card, lay = card("Навыки персонажа", "Уровень каждого навыка")
        self.radar = RadarChart("accent")
        lay.addWidget(self.radar)
        grid.addWidget(radar_card, 3, 0)

        # --- Квесты по зонам ---
        zones_card, lay = card("Активные квесты по зонам")
        self.zones = HBarChart()
        lay.addWidget(self.zones)
        self.zones_note = QLabel()
        self.zones_note.setObjectName("muted")
        self.zones_note.setWordWrap(True)
        lay.addWidget(self.zones_note)
        lay.addStretch(1)
        grid.addWidget(zones_card, 3, 1)

        # --- Календарь ---
        heat_card, lay = card("Календарь активности", "Сколько квестов выполнено в каждый день")
        self.heat = Heatmap()
        lay.addWidget(self.heat)
        grid.addWidget(heat_card, 4, 0, 1, 2)

        self.setWidget(host)
        controller.tasks_changed.connect(self.refresh)

    def _set_days(self, days: int) -> None:
        self.days = days
        self.refresh()

    # --- Заполнение ----------------------------------------------------------
    def refresh(self) -> None:
        c = themes.colors()
        stats = self.controller.stats()
        per_day = self.db.quests_per_day()
        today_xp = self.db.xp_per_day(1)[0][1]
        goal = self.controller.daily_goal()
        week_days = sum(1 for i in range(7) if per_day.get(date.today() - timedelta(days=i), 0) > 0)

        # Кольца + легенда со значениями (цвет не единственный носитель смысла)
        rings = [
            (today_xp, game.DAILY_XP_TARGET, c["ring_xp"], "Опыт", f"{today_xp}/{game.DAILY_XP_TARGET} XP"),
            (stats.today, goal, c["ring_quests"], "Квесты", f"{stats.today}/{goal}"),
            (week_days, 7, c["ring_week"], "Неделя", f"{week_days}/7 дн."),
        ]
        self.rings.set_rings([(v, g, col) for v, g, col, _, _ in rings])
        clear(self.rings_legend)
        self.rings_legend.addStretch(1)
        for _, _, col, name, value in rings:
            self.rings_legend.addWidget(legend_row(col, name, value))
        self.rings_legend.addStretch(1)

        # Итоги
        clear(self.totals)
        xp_window = self.db.xp_per_day(30)
        avg = round(sum(v for _, v in xp_window) / 30)
        tiles = [("Всего опыта", f"{stats.total_xp}", "XP"), ("Квестов", f"{stats.completed}", "выполнено"),
                 ("Серия", f"{stats.streak}", "дн. подряд"), ("В среднем", f"{avg}", "XP в день")]
        for i, (title, value, unit) in enumerate(tiles):
            self.totals.addWidget(self._tile(title, value, unit), i // 2, i % 2)

        # Опыт по дням
        data = self.db.xp_per_day(self.days)
        total = sum(v for _, v in data)
        self.bars_sub.setText(f"{total} XP за {self.days} дн. · в среднем {round(total / self.days)} XP в день")
        self.bars.set_data(data)

        # Накопленный опыт: всё, что было до окна, + нарастающий итог
        base = stats.total_xp - sum(v for _, v in xp_window)
        running, cumulative = base, []
        for d, v in xp_window:
            running += v
            cumulative.append((d, max(0, running)))
        self.line.set_data(cumulative)

        # Опыт по навыкам (порядок цветов фиксирован порядком SKILLS)
        segments = []
        for key, (name, icon, _, _) in game.SKILLS.items():
            segments.append((f"{icon} {name}", stats.skill_xp.get(key, 0), themes.skill_color(key)))
        self.donut.set_data(segments)
        clear(self.donut_legend)
        total_xp = sum(v for _, v, _ in segments) or 1
        self.donut_legend.addStretch(1)
        for name, v, col in segments:
            if v > 0:
                self.donut_legend.addWidget(legend_row(col, name, f"{round(100 * v / total_xp)}%"))
        if not any(v for _, v, _ in segments):
            empty = QLabel("Пока нет опыта —\nзавершите первый квест")
            empty.setObjectName("muted")
            self.donut_legend.addWidget(empty)
        self.donut_legend.addStretch(1)

        # «Паутина» навыков
        axes = []
        for key, (name, icon, _, _) in game.SKILLS.items():
            xp = stats.skill_xp.get(key, 0)
            level = game.skill_level_info(xp)[0]
            axes.append((f"{icon} {name}", level, f"Уровень {level} · {xp} XP"))
        self.radar.set_data(axes)

        # Квесты по зонам
        tasks = self.controller.tasks()
        rows = []
        for zone in config.ZONE_GRID:
            active = sum(1 for t in tasks if t.zone == zone and not t.done)
            done = sum(1 for t in tasks if t.zone == zone and t.done)
            rows.append((f"{config.ZONE_ICONS[zone]} {config.ZONE_TITLES[zone]}", active,
                         themes.zone_color(zone), f"<b>{config.ZONE_TITLES[zone]}</b><br>"
                                                  f"Активных: {active}<br>Выполнено: {done}"))
        self.zones.set_data(rows)
        overdue = sum(1 for t in tasks if t.is_overdue)
        self.zones_note.setText(f"Просрочено: {overdue}" if overdue else "Просроченных квестов нет 👍")

        self.heat.set_data(per_day)

    @staticmethod
    def _tile(title: str, value: str, unit: str):
        from PySide6.QtWidgets import QFrame
        tile = QFrame()
        tile.setObjectName("tile")
        lay = QVBoxLayout(tile)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(0)
        cap = QLabel(title)
        cap.setObjectName("caption")
        val = QLabel(f"<span style='font-size:20pt; font-weight:800'>{value}</span>"
                     f" <span style='font-size:9pt'>{unit}</span>")
        lay.addWidget(cap)
        lay.addWidget(val)
        return tile

    def restyle(self) -> None:
        self.period.restyle()
        self.refresh()
