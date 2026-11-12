"""
Диаграммы, нарисованные вручную через QPainter (без сторонних библиотек).

Общие правила оформления (одинаковы для всех диаграмм):
  - тонкие элементы, скруглённые концы столбцов, линии толщиной 2 px;
  - сетка и оси приглушены (цвет разделителя), подписи — цветом текста,
    а не цветом серии;
  - числа подписаны выборочно (максимум / сегодня), остальное — в подсказке;
  - у каждой диаграммы есть подсказка при наведении мыши.

Классы:
  BarChart     — столбцы (опыт по дням) + пунктир среднего;
  LineChart    — линия с заливкой (накопленный опыт) + перекрестие;
  DonutChart   — кольцевая диаграмма (опыт по навыкам);
  RadarChart   — «паутина» навыков персонажа;
  HBarChart    — горизонтальные полосы (квесты по зонам);
  Heatmap      — календарь активности по дням.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QToolTip, QWidget

from . import themes

MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
              "августа", "сентября", "октября", "ноября", "декабря"]
MONTHS_SHORT = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def fmt_day(d: date) -> str:
    """«Чт, 12 ноября»."""
    return f"{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS_GEN[d.month - 1]}"


def nice_max(value: float) -> float:
    """Округляет максимум шкалы вверх до «красивого» числа (10, 20, 50, 100, …)."""
    if value <= 0:
        return 10
    exp = 10 ** math.floor(math.log10(value))
    for m in (1, 2, 2.5, 5, 10):
        if value <= m * exp:
            return m * exp
    return 10 * exp


def rounded_top_bar(rect: QRectF, radius: float) -> QPainterPath:
    """Столбец со скруглённым верхом и прямым низом (привязан к оси)."""
    r = min(radius, rect.width() / 2, rect.height())
    path = QPainterPath()
    path.moveTo(rect.left(), rect.bottom())
    path.lineTo(rect.left(), rect.top() + r)
    path.quadTo(rect.left(), rect.top(), rect.left() + r, rect.top())
    path.lineTo(rect.right() - r, rect.top())
    path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + r)
    path.lineTo(rect.right(), rect.bottom())
    path.closeSubpath()
    return path


class ChartBase(QWidget):
    """Общее: отслеживание мыши, подсказка, шрифты и цвета темы."""

    def __init__(self, min_height: int = 180, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(min_height)
        self.hover = None

    def small_font(self, size: float = 8, bold: bool = False):
        f = themes.ui_font(size)
        f.setBold(bold)
        return f

    def show_tip(self, pos: QPointF, text: str) -> None:
        QToolTip.showText(self.mapToGlobal(QPoint(int(pos.x()) + 12, int(pos.y()) + 12)), text, self)

    def set_hover(self, value) -> None:
        if value != self.hover:
            self.hover = value
            self.update()

    def leaveEvent(self, event):
        self.set_hover(None)
        QToolTip.hideText()

    def draw_y_grid(self, p: QPainter, plot: QRectF, top_value: float, suffix: str = "") -> None:
        """Три приглушённые линии сетки с подписями справа (как в «Здоровье»)."""
        c = themes.colors()
        p.setFont(self.small_font(7.5))
        for i in range(3):
            v = top_value * i / 2
            y = plot.bottom() - plot.height() * i / 2
            p.setPen(QPen(QColor(c["separator"]), 1, Qt.SolidLine if i == 0 else Qt.DotLine))
            p.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            p.setPen(QColor(c["muted"]))
            p.drawText(QRectF(plot.right() + 6, y - 8, 44, 16), Qt.AlignLeft | Qt.AlignVCenter,
                       f"{int(v)}{suffix}")


class BarChart(ChartBase):
    """Столбцы по дням. data: список (дата, значение)."""

    def __init__(self, color_key: str = "accent", unit: str = "XP", parent=None):
        super().__init__(200, parent)
        self.data: list[tuple[date, int]] = []
        self.color_key = color_key
        self.unit = unit

    def set_data(self, data: list[tuple[date, int]]) -> None:
        self.data = data
        self.hover = None
        self.update()

    def _plot(self) -> QRectF:
        return QRectF(4, 22, self.width() - 54, self.height() - 22 - 24)

    def _slot(self, plot: QRectF) -> float:
        return plot.width() / max(1, len(self.data))

    def paintEvent(self, event):
        if not self.data:
            return
        c = themes.colors()
        color = QColor(c[self.color_key])
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        plot = self._plot()
        values = [v for _, v in self.data]
        top = nice_max(max(values))
        self.draw_y_grid(p, plot, top)

        slot = self._slot(plot)
        bar_w = max(3.0, min(22.0, slot * 0.58))
        max_i = values.index(max(values)) if max(values) > 0 else -1
        n = len(self.data)
        label_every = 1 if n <= 14 else 5

        for i, (day, v) in enumerate(self.data):
            x = plot.left() + i * slot + (slot - bar_w) / 2
            h = plot.height() * v / top
            faded = self.hover is not None and self.hover != i
            if v > 0:
                col = QColor(color)
                col.setAlphaF(0.35 if faded else 1.0)
                p.fillPath(rounded_top_bar(QRectF(x, plot.bottom() - h, bar_w, h), 4), col)
            # Выборочная подпись значения: только у максимума (или у наведённого)
            if v > 0 and (i == max_i and self.hover is None or i == self.hover):
                p.setPen(QColor(c["text"]))
                p.setFont(self.small_font(8, True))
                p.drawText(QRectF(x - 30, plot.bottom() - h - 18, bar_w + 60, 16), Qt.AlignCenter, str(v))
            # Подписи по оси X — не у каждого столбца, если их много
            is_today = day == date.today()
            if i % label_every == 0 or is_today:
                p.setFont(self.small_font(7.5, is_today))
                p.setPen(QColor(c["text"] if is_today else c["muted"]))
                text = WEEKDAYS[day.weekday()] if n <= 7 else str(day.day)
                p.drawText(QRectF(plot.left() + i * slot - 10, plot.bottom() + 4, slot + 20, 16),
                           Qt.AlignCenter, text)

        # Пунктир среднего значения (как «сред.» в «Экранном времени»)
        avg = sum(values) / len(values)
        if avg > 0:
            y = plot.bottom() - plot.height() * avg / top
            p.setPen(QPen(QColor(c["success"]), 1.5, Qt.DashLine))
            p.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            p.setPen(QColor(c["muted"]))
            p.setFont(self.small_font(7.5, True))
            p.drawText(QRectF(plot.right() + 6, y - 8, 48, 16), Qt.AlignLeft | Qt.AlignVCenter, "сред.")
        p.end()

    def mouseMoveEvent(self, event):
        if not self.data:
            return
        plot = self._plot()
        i = int((event.position().x() - plot.left()) // self._slot(plot))
        if 0 <= i < len(self.data):
            self.set_hover(i)
            day, v = self.data[i]
            self.show_tip(event.position(), f"<b>{fmt_day(day)}</b><br>{v} {self.unit}")
        else:
            self.set_hover(None)


class LineChart(ChartBase):
    """Линия с заливкой под ней. data: список (дата, значение)."""

    def __init__(self, color_key: str = "accent", unit: str = "XP", parent=None):
        super().__init__(200, parent)
        self.data: list[tuple[date, int]] = []
        self.color_key = color_key
        self.unit = unit

    def set_data(self, data: list[tuple[date, int]]) -> None:
        self.data = data
        self.hover = None
        self.update()

    def _plot(self) -> QRectF:
        return QRectF(4, 14, self.width() - 54, self.height() - 14 - 24)

    def _points(self, plot: QRectF, top: float) -> list[QPointF]:
        n = len(self.data)
        step = plot.width() / max(1, n - 1)
        return [QPointF(plot.left() + i * step, plot.bottom() - plot.height() * v / top)
                for i, (_, v) in enumerate(self.data)]

    def paintEvent(self, event):
        if len(self.data) < 2:
            return
        c = themes.colors()
        color = QColor(c[self.color_key])
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        plot = self._plot()
        top = nice_max(max(v for _, v in self.data))
        self.draw_y_grid(p, plot, top)
        pts = self._points(plot, top)

        # Заливка: цвет линии, прозрачность сверху вниз 25% → 0%
        area = QPainterPath(QPointF(pts[0].x(), plot.bottom()))
        for pt in pts:
            area.lineTo(pt)
        area.lineTo(pts[-1].x(), plot.bottom())
        area.closeSubpath()
        grad = QLinearGradient(0, plot.top(), 0, plot.bottom())
        grad.setColorAt(0, themes.qcolor(c[self.color_key], 0.28))
        grad.setColorAt(1, themes.qcolor(c[self.color_key], 0.0))
        p.fillPath(area, QBrush(grad))

        line = QPainterPath(pts[0])
        for pt in pts[1:]:
            line.lineTo(pt)
        pen = QPen(color, 2)
        pen.setJoinStyle(Qt.RoundJoin)
        p.strokePath(line, pen)

        # Подписи оси X: первая, середина, последняя
        p.setFont(self.small_font(7.5))
        p.setPen(QColor(c["muted"]))
        for i, align in ((0, Qt.AlignLeft), (len(self.data) // 2, Qt.AlignHCenter),
                         (len(self.data) - 1, Qt.AlignRight)):
            d = self.data[i][0]
            # Крайние подписи прижимаем к краям, чтобы они не обрезались
            x = pts[i].x() if align == Qt.AlignLeft else pts[i].x() - (80 if align == Qt.AlignRight else 40)
            p.drawText(QRectF(x, plot.bottom() + 4, 80, 16), align | Qt.AlignVCenter,
                       f"{d.day} {MONTHS_SHORT[d.month - 1]}")

        # Перекрестие и точка на наведённом дне
        if self.hover is not None:
            pt = pts[self.hover]
            p.setPen(QPen(QColor(c["muted"]), 1))
            p.drawLine(QPointF(pt.x(), plot.top()), QPointF(pt.x(), plot.bottom()))
            self._dot(p, pt, color, c["surface"])
        else:
            self._dot(p, pts[-1], color, c["surface"])
        p.end()

    @staticmethod
    def _dot(p: QPainter, pt: QPointF, color: QColor, ring: str) -> None:
        """Маркер 8 px с кольцом цвета фона — не сливается с линией."""
        p.setPen(QPen(QColor(ring), 2))
        p.setBrush(color)
        p.drawEllipse(pt, 5, 5)

    def mouseMoveEvent(self, event):
        if len(self.data) < 2:
            return
        plot = self._plot()
        step = plot.width() / (len(self.data) - 1)
        i = round((event.position().x() - plot.left()) / step)
        i = max(0, min(len(self.data) - 1, i))
        self.set_hover(i)
        day, v = self.data[i]
        self.show_tip(event.position(), f"<b>{fmt_day(day)}</b><br>Всего: {v} {self.unit}")


class DonutChart(ChartBase):
    """Кольцевая диаграмма. segments: список (название, значение, цвет)."""

    def __init__(self, center_caption: str = "XP", parent=None):
        super().__init__(200, parent)
        self.segments: list[tuple[str, int, str]] = []
        self.caption = center_caption
        self.setMinimumWidth(200)

    def set_data(self, segments: list[tuple[str, int, str]]) -> None:
        self.segments = [s for s in segments if s[1] > 0]
        self.hover = None
        self.update()

    def _geometry(self):
        side = min(self.width(), self.height()) - 16
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        return rect, side * 0.13  # прямоугольник, толщина кольца

    def paintEvent(self, event):
        c = themes.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect, thick = self._geometry()
        ring = rect.adjusted(thick / 2, thick / 2, -thick / 2, -thick / 2)
        total = sum(v for _, v, _ in self.segments)

        if not total:
            p.setPen(QPen(QColor(c["fill"]), thick))
            p.drawEllipse(ring)
        else:
            start = 90.0
            gap = 1.6 if len(self.segments) > 1 else 0  # зазор 2 px между сегментами
            for i, (name, v, color) in enumerate(self.segments):
                span = 360.0 * v / total
                w = thick * (1.18 if self.hover == i else 1.0)
                col = themes.qcolor(color, 0.4 if (self.hover is not None and self.hover != i) else 1.0)
                p.setPen(QPen(col, w, Qt.SolidLine, Qt.FlatCap))
                p.drawArc(ring, int((start - gap / 2) * 16), int(-(span - gap) * 16))
                start -= span

        # Итог в центре
        p.setPen(QColor(c["text"]))
        p.setFont(self.small_font(18, True))
        value = total
        caption = self.caption
        if self.hover is not None and self.segments:
            name, value, _ = self.segments[self.hover]
            caption = name
        p.drawText(QRectF(rect.left(), rect.center().y() - 22, rect.width(), 28), Qt.AlignCenter, str(value))
        p.setPen(QColor(c["muted"]))
        p.setFont(self.small_font(8.5, True))
        p.drawText(QRectF(rect.left(), rect.center().y() + 6, rect.width(), 18), Qt.AlignCenter, caption)
        p.end()

    def mouseMoveEvent(self, event):
        if not self.segments:
            return
        rect, thick = self._geometry()
        center = rect.center()
        dx, dy = event.position().x() - center.x(), event.position().y() - center.y()
        r = math.hypot(dx, dy)
        if not (rect.width() / 2 - thick * 1.6 <= r <= rect.width() / 2 + 4):
            self.set_hover(None)
            QToolTip.hideText()
            return
        # Угол от «12 часов» по часовой стрелке
        angle = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
        total = sum(v for _, v, _ in self.segments)
        acc = 0.0
        for i, (name, v, _) in enumerate(self.segments):
            acc += 360.0 * v / total
            if angle <= acc:
                self.set_hover(i)
                self.show_tip(event.position(), f"<b>{name}</b><br>{v} XP · {round(100 * v / total)}%")
                return


class RadarChart(ChartBase):
    """«Паутина» навыков. axes: список (подпись, значение, подробность для подсказки)."""

    def __init__(self, color_key: str = "accent", parent=None):
        super().__init__(280, parent)
        self.axes: list[tuple[str, float, str]] = []
        self.color_key = color_key

    def set_data(self, axes: list[tuple[str, float, str]]) -> None:
        self.axes = axes
        self.hover = None
        self.update()

    def _geometry(self):
        radius = min(self.width(), self.height()) / 2 - 46
        return QPointF(self.width() / 2, self.height() / 2 + 4), max(20.0, radius)

    def _point(self, center: QPointF, radius: float, i: int, frac: float) -> QPointF:
        angle = -math.pi / 2 + 2 * math.pi * i / len(self.axes)
        return QPointF(center.x() + math.cos(angle) * radius * frac,
                       center.y() + math.sin(angle) * radius * frac)

    def paintEvent(self, event):
        if len(self.axes) < 3:
            return
        c = themes.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        center, radius = self._geometry()
        top = max(5.0, nice_max(max(v for _, v, _ in self.axes)))
        n = len(self.axes)

        # Сетка: 4 концентрических многоугольника и лучи
        p.setPen(QPen(QColor(c["separator"]), 1))
        p.setBrush(Qt.NoBrush)
        for k in range(1, 5):
            p.drawPolygon(QPolygonF([self._point(center, radius, i, k / 4) for i in range(n)]))
        for i in range(n):
            p.drawLine(center, self._point(center, radius, i, 1))

        # Фигура навыков
        pts = [self._point(center, radius, i, v / top) for i, (_, v, _) in enumerate(self.axes)]
        color = QColor(c[self.color_key])
        p.setBrush(themes.qcolor(c[self.color_key], 0.18))
        pen = QPen(color, 2)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawPolygon(QPolygonF(pts))
        for i, pt in enumerate(pts):
            p.setPen(QPen(QColor(c["surface"]), 2))
            p.setBrush(color)
            p.drawEllipse(pt, 6 if self.hover == i else 4.5, 6 if self.hover == i else 4.5)

        # Подписи осей
        p.setFont(self.small_font(8.5, True))
        for i, (label, v, _) in enumerate(self.axes):
            lp = self._point(center, radius + 26, i, 1)
            p.setPen(QColor(c["text"] if self.hover == i else c["muted"]))
            p.drawText(QRectF(lp.x() - 60, lp.y() - 10, 120, 20), Qt.AlignCenter, label)
        p.end()

    def mouseMoveEvent(self, event):
        if len(self.axes) < 3:
            return
        center, radius = self._geometry()
        pos = event.position()
        dx, dy = pos.x() - center.x(), pos.y() - center.y()
        if math.hypot(dx, dy) > radius + 40:
            self.set_hover(None)
            QToolTip.hideText()
            return
        angle = (math.atan2(dy, dx) + math.pi / 2) % (2 * math.pi)
        i = round(angle / (2 * math.pi / len(self.axes))) % len(self.axes)
        self.set_hover(i)
        label, v, detail = self.axes[i]
        self.show_tip(pos, f"<b>{label}</b><br>{detail}")


class HBarChart(ChartBase):
    """Горизонтальные полосы. rows: список (подпись, значение, цвет, подсказка)."""

    ROW_H = 34

    def __init__(self, parent=None):
        super().__init__(120, parent)
        self.rows: list[tuple[str, int, str, str]] = []

    def set_data(self, rows: list[tuple[str, int, str, str]]) -> None:
        self.rows = rows
        self.setMinimumHeight(self.ROW_H * len(rows) + 8)
        self.hover = None
        self.update()

    def paintEvent(self, event):
        if not self.rows:
            return
        c = themes.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        label_w = 150
        bar_left = label_w + 8
        bar_max = self.width() - bar_left - 44
        top = max(1, max(v for _, v, _, _ in self.rows))
        for i, (label, v, color, _) in enumerate(self.rows):
            y = 4 + i * self.ROW_H
            p.setFont(self.small_font(9, self.hover == i))
            p.setPen(QColor(c["text"]))
            p.drawText(QRectF(0, y, label_w, self.ROW_H - 8), Qt.AlignLeft | Qt.AlignVCenter, label)
            # Трек и полоса толщиной 10 px со скруглёнными концами
            track = QRectF(bar_left, y + (self.ROW_H - 8) / 2 - 5, bar_max, 10)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(c["fill"]))
            p.drawRoundedRect(track, 5, 5)
            if v:
                w = max(10.0, bar_max * v / top)
                p.setBrush(themes.qcolor(color, 0.45 if (self.hover is not None and self.hover != i) else 1))
                p.drawRoundedRect(QRectF(track.left(), track.top(), w, 10), 5, 5)
            p.setPen(QColor(c["muted"]))
            p.setFont(self.small_font(9, True))
            p.drawText(QRectF(track.right() + 6, y, 40, self.ROW_H - 8), Qt.AlignLeft | Qt.AlignVCenter, str(v))
        p.end()

    def mouseMoveEvent(self, event):
        i = int((event.position().y() - 4) // self.ROW_H)
        if 0 <= i < len(self.rows):
            self.set_hover(i)
            self.show_tip(event.position(), self.rows[i][3])
        else:
            self.set_hover(None)


class Heatmap(ChartBase):
    """
    Календарь активности: столбцы — недели, строки — дни недели.
    Цвет — одна шкала (от фона к акцентному цвету): чем темнее, тем больше квестов.
    """

    MAX_WEEKS = 53          # не больше года
    LEVELS = [0.0, 0.3, 0.55, 0.8, 1.0]  # доля акцентного цвета для уровней 0..4

    def __init__(self, parent=None):
        super().__init__(200, parent)
        self.per_day: dict[date, int] = {}
        self.weeks = 20

    def set_data(self, per_day: dict[date, int]) -> None:
        self.per_day = per_day
        self.update()

    def _grid(self):
        # Сколько недель влезает по ширине при ячейке ~17 px (но не больше года)
        left, top = 28, 20
        self.weeks = max(8, min(self.MAX_WEEKS, int((self.width() - left - 4) // 20)))
        cell = min(20.0, (self.width() - left - 4) / self.weeks - 3)
        today = date.today()
        start = today - timedelta(days=today.weekday()) - timedelta(weeks=self.weeks - 1)
        return start, left, top, cell, cell + 3

    def _level(self, n: int, peak: int) -> int:
        if n <= 0:
            return 0
        return min(4, 1 + int(3 * (n - 1) / max(1, peak - 1))) if peak > 1 else 4

    def _color(self, level: int) -> QColor:
        c = themes.colors()
        if level == 0:
            return QColor(c["fill"])
        return QColor(themes.mix(c["surface"], c["accent"], self.LEVELS[level]))

    def paintEvent(self, event):
        c = themes.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        start, left, top, cell, step = self._grid()
        today = date.today()
        peak = max(self.per_day.values(), default=0)

        p.setFont(self.small_font(7.5))
        p.setPen(QColor(c["muted"]))
        for row, name in ((0, "Пн"), (2, "Ср"), (4, "Пт"), (6, "Вс")):
            p.drawText(QRectF(0, top + row * step, left - 6, cell), Qt.AlignRight | Qt.AlignVCenter, name)

        last_month, last_x = None, -100.0
        for w in range(self.weeks):
            monday = start + timedelta(weeks=w)
            x_label = left + w * step
            # Подпись месяца над первой неделей месяца (если не налезает на предыдущую)
            if monday.month != last_month and x_label - last_x > 34:
                last_month, last_x = monday.month, x_label
                p.setPen(QColor(c["muted"]))
                p.drawText(QRectF(left + w * step, 0, 40, 16), Qt.AlignLeft | Qt.AlignVCenter,
                           MONTHS_SHORT[monday.month - 1])
            for d in range(7):
                day = monday + timedelta(days=d)
                if day > today:
                    continue
                rect = QRectF(left + w * step, top + d * step, cell, cell)
                p.setPen(Qt.NoPen)
                p.setBrush(self._color(self._level(self.per_day.get(day, 0), peak)))
                p.drawRoundedRect(rect, 4, 4)
                if day == today or day == self.hover:
                    p.setPen(QPen(QColor(c["text"]), 1.5))
                    p.setBrush(Qt.NoBrush)
                    p.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 5, 5)

        # Легенда: «Меньше ▢▢▢▢▢ Больше»
        y = top + 7 * step + 6
        x = self.width() - 5 * (cell * 0.75 + 3) - 60
        p.setPen(QColor(c["muted"]))
        p.drawText(QRectF(x - 56, y, 52, cell * 0.75), Qt.AlignRight | Qt.AlignVCenter, "Меньше")
        for lvl in range(5):
            p.setPen(Qt.NoPen)
            p.setBrush(self._color(lvl))
            p.drawRoundedRect(QRectF(x + lvl * (cell * 0.75 + 3), y, cell * 0.75, cell * 0.75), 3, 3)
        p.setPen(QColor(c["muted"]))
        p.drawText(QRectF(x + 5 * (cell * 0.75 + 3) + 2, y, 60, cell * 0.75), Qt.AlignLeft | Qt.AlignVCenter, "Больше")
        p.end()

    def mouseMoveEvent(self, event):
        start, left, top, cell, step = self._grid()
        pos = event.position()
        w = int((pos.x() - left) // step)
        d = int((pos.y() - top) // step)
        if 0 <= w < self.weeks and 0 <= d < 7:
            day = start + timedelta(weeks=w, days=d)
            if day <= date.today():
                self.set_hover(day)
                n = self.per_day.get(day, 0)
                self.show_tip(pos, f"<b>{fmt_day(day)}</b><br>Квестов: {n}")
                return
        self.set_hover(None)
        QToolTip.hideText()
