"""
Элементы интерфейса в стиле iOS, нарисованные вручную через QPainter:

  CheckCircle   — круглая отметка «выполнено», как в «Напоминаниях»;
  IOSSwitch     — зелёный тумблер;
  Segmented     — сегментированный переключатель «А | Б | В»;
  ActivityRings — кольца активности, как в «Фитнесе»;
  card()        — белая скруглённая карточка с заголовком.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, Signal,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractButton, QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from . import themes


class CheckCircle(QAbstractButton):
    """Пустой кружок → при нажатии заливается цветом и показывает галочку."""

    def __init__(self, color: str, size: int = 22, parent=None):
        super().__init__(parent)
        self._color = color
        self._size = size
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(size + 4, size + 4)

    def sizeHint(self) -> QSize:
        return QSize(self._size + 4, self._size + 4)

    def paintEvent(self, event):
        c = themes.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(2, 2, self._size, self._size)
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(self._color))
            p.drawEllipse(r)
            # Галочка белым
            pen = QPen(QColor("#FFFFFF"), max(2.0, self._size / 10))
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            p.setPen(pen)
            s = self._size
            path = QPainterPath(QPointF(2 + s * 0.28, 2 + s * 0.52))
            path.lineTo(2 + s * 0.44, 2 + s * 0.67)
            path.lineTo(2 + s * 0.73, 2 + s * 0.35)
            p.drawPath(path)
        else:
            hover = self.underMouse()
            p.setPen(QPen(QColor(self._color if hover else c["faint"]), 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(r.adjusted(1, 1, -1, -1))
        p.end()

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()


class IOSSwitch(QAbstractButton):
    """Тумблер iOS с плавной анимацией ручки."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(46, 28)
        self._pos = 0.0  # 0 — выключено, 1 — включено
        self._anim = QPropertyAnimation(self, b"knob")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._animate)

    def _animate(self, on: bool) -> None:
        self._anim.stop()
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def setChecked(self, on: bool) -> None:  # без анимации при программной установке
        super().setChecked(on)
        self._anim.stop()
        self._pos = 1.0 if on else 0.0
        self.update()

    def _get_knob(self) -> float:
        return self._pos

    def _set_knob(self, v: float) -> None:
        self._pos = v
        self.update()

    knob = Property(float, _get_knob, _set_knob)

    def paintEvent(self, event):
        c = themes.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track = QColor(themes.mix(c["fill"], c["success"], self._pos))
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, 0, 46, 28), 14, 14)
        x = 2 + self._pos * 18
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawEllipse(QRectF(x, 3, 24, 24))           # мягкая тень
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(x, 2, 24, 24))
        p.end()


class Segmented(QFrame):
    """
    Сегментированный переключатель: серая «капсула», выбранный сегмент — белый.
    options: список (подпись, значение). Сигнал changed(значение).
    """

    changed = Signal(object)

    def __init__(self, options: list[tuple[str, object]], parent=None):
        super().__init__(parent)
        self.setObjectName("segmented")
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._values = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(2)
        for i, (text, value) in enumerate(options):
            b = QPushButton(text)
            b.setCheckable(True)
            b.setObjectName("segment")
            b.setCursor(Qt.PointingHandCursor)
            self._group.addButton(b, i)
            self._values.append(value)
            lay.addWidget(b)
        self._group.button(0).setChecked(True)
        self._group.idClicked.connect(lambda i: self.changed.emit(self._values[i]))
        self.restyle()

    def value(self):
        return self._values[self._group.checkedId()]

    def set_value(self, value) -> None:
        if value in self._values:
            self._group.button(self._values.index(value)).setChecked(True)

    def restyle(self) -> None:
        c = themes.colors()
        selected = c["fill"] if themes.is_dark() else "#FFFFFF"
        track = c["surface2"] if themes.is_dark() else c["fill"]
        self.setStyleSheet(f"""
            QFrame#segmented {{ background: {track}; border-radius: 9px; }}
            QPushButton#segment {{
                background: transparent; border: none; border-radius: 7px;
                padding: 5px 14px; font-weight: 600; font-size: 9pt; color: {c['text']};
            }}
            QPushButton#segment:hover {{ background: {themes.rgba(c['muted'], 0.12)}; }}
            QPushButton#segment:checked {{ background: {selected}; }}
        """)


class ActivityRings(QWidget):
    """
    Кольца активности (как в приложении «Фитнес»).
    rings: список (значение, цель, цвет); первое кольцо — внешнее.
    Если значение больше цели, кольцо идёт на второй круг.
    """

    def __init__(self, size: int = 120, thickness: float | None = None, parent=None):
        super().__init__(parent)
        self._size = size
        self._thick = thickness or size / 9
        self.rings: list[tuple[float, float, str]] = []
        self.setFixedSize(size, size)

    def set_rings(self, rings: list[tuple[float, float, str]]) -> None:
        self.rings = rings
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self._thick
        gap = t * 0.18
        for i, (value, goal, color) in enumerate(self.rings):
            inset = t / 2 + i * (t + gap)
            rect = QRectF(inset, inset, self._size - 2 * inset, self._size - 2 * inset)
            # Трек — тот же цвет, приглушённый
            pen = QPen(themes.qcolor(color, 0.22), t)
            pen.setCapStyle(Qt.FlatCap)
            p.setPen(pen)
            p.drawEllipse(rect)
            frac = (value / goal) if goal else 0
            if frac <= 0:
                continue
            pen = QPen(QColor(color), t)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            # Углы в Qt — в 1/16 градуса; минус — по часовой стрелке от «12 часов»
            p.drawArc(rect, 90 * 16, -int(min(frac, 1.0) * 360 * 16))
            if frac > 1:  # перевыполнение — дорисовываем второй круг поверх
                p.drawArc(rect, 90 * 16, -int(min(frac - 1, 1.0) * 360 * 16))
        p.end()


def card(title: str = "", subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    """Белая скруглённая карточка; возвращает (рамка, layout для содержимого)."""
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 16)
    lay.setSpacing(10)
    if title:
        head = QVBoxLayout()
        head.setSpacing(0)
        t = QLabel(title)
        t.setObjectName("h2")
        head.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("muted")
            s.setStyleSheet("font-size: 9pt;")
            head.addWidget(s)
        lay.addLayout(head)
    return frame, lay


def legend_row(color: str, name: str, value: str = "") -> QWidget:
    """Строка легенды: цветная точка · название (обычный текст) · значение справа."""
    c = themes.colors()
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    dot = QLabel()
    dot.setFixedSize(10, 10)
    dot.setStyleSheet(f"background: {color}; border-radius: 5px;")
    lay.addWidget(dot)
    lay.addWidget(QLabel(name), 1)
    if value:
        v = QLabel(value)
        v.setStyleSheet(f"color: {c['muted']}; font-weight: 600;")
        lay.addWidget(v)
    w.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    return w
