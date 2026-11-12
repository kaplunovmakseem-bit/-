"""
Всплывающие уведомления («+78 XP», «Новый уровень!», «Достижение!»).

Каждое уведомление — QFrame поверх главного окна в правом нижнем углу.
Появляется с плавным выездом и исчезает через несколько секунд.
Несколько уведомлений складываются стопкой.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QParallelAnimationGroup, QPropertyAnimation,
    QSequentialAnimationGroup, Qt, QVariantAnimation,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from . import themes

MARGIN = 18
GAP = 10


class Toast(QFrame):
    def __init__(self, parent: QWidget, icon: str, title: str, subtitle: str,
                 color: str, big: bool = False):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # не мешает кликам
        c = themes.colors()

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_size = 52 if big else 40
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setStyleSheet(
            f"background: {themes.rgba(color, 0.22)}; border-radius: {icon_size // 3}px;"
            f" font-size: {int(icon_size * 0.5)}px;")

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {color}; font-weight: 800; font-size: {15 if big else 11.5}pt;")
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet(f"color: {c['text']}; font-size: 9pt;")
        sub_label.setVisible(bool(subtitle))

        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(title_label)
        col.addWidget(sub_label)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 18, 10)
        lay.setSpacing(12)
        lay.addWidget(icon_label)
        lay.addLayout(col)

        self.setStyleSheet(f"""
            QFrame#toast {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {themes.mix(c['surface'], color, 0.18)}, stop:1 {c['surface']});
                border: 1px solid {themes.rgba(color, 0.7)};
                border-radius: 14px;
            }}
            QLabel {{ background: transparent; }}
        """)
        self.opacity = QGraphicsOpacityEffect(self)
        self.opacity.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity)
        self.adjustSize()


class ToastManager:
    """
    Показывает уведомления и раскладывает их стопкой снизу вверх.

    Позицию анимируем не через QPropertyAnimation(b"pos"), а через смещение
    toast.offset: Qt останавливает предыдущую анимацию того же свойства,
    и при одновременных уведомлениях они бы «застревали».
    """

    MAX_VISIBLE = 4

    def __init__(self, host: QWidget):
        self.host = host
        self.toasts: list[Toast] = []
        self._anims = []  # держим ссылки, чтобы анимации не удалил сборщик мусора

    def show(self, icon: str, title: str, subtitle: str = "", color: str = "#8b5cf6",
             big: bool = False, duration_ms: int = 3200) -> None:
        toast = Toast(self.host, icon, title, subtitle, color, big)
        toast.offset = 24  # стартует чуть ниже и «выезжает» вверх
        self.toasts.insert(0, toast)
        # Слишком много уведомлений — самое старое убираем сразу
        while len(self.toasts) > self.MAX_VISIBLE:
            self._discard(self.toasts[-1])
        toast.show()
        toast.raise_()
        self.reposition()

        fade_in = QPropertyAnimation(toast.opacity, b"opacity")
        fade_in.setDuration(260)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)

        slide = QVariantAnimation()
        slide.setDuration(380)
        slide.setStartValue(24)
        slide.setEndValue(0)
        slide.setEasingCurve(QEasingCurve.OutBack)
        slide.valueChanged.connect(lambda v, t=toast: self._set_offset(t, v))

        appear = QParallelAnimationGroup()
        appear.addAnimation(fade_in)
        appear.addAnimation(slide)

        fade_out = QPropertyAnimation(toast.opacity, b"opacity")
        fade_out.setDuration(400)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        seq = QSequentialAnimationGroup()
        seq.addAnimation(appear)
        seq.addPause(duration_ms)
        seq.addAnimation(fade_out)
        seq.finished.connect(lambda t=toast: self._discard(t))
        toast.anim = seq
        self._anims.append(seq)
        seq.start()

    def _set_offset(self, toast: Toast, value) -> None:
        if toast in self.toasts:
            toast.offset = int(value)
            self.reposition()

    def _discard(self, toast: Toast) -> None:
        if toast in self.toasts:
            self.toasts.remove(toast)
        anim = getattr(toast, "anim", None)
        if anim in self._anims:
            self._anims.remove(anim)
            anim.stop()
        toast.hide()
        toast.deleteLater()
        self.reposition()

    def reposition(self) -> None:
        """Ставит уведомления в правый нижний угол, новые — снизу."""
        y = self.host.height() - MARGIN
        for t in self.toasts:
            y -= t.height()
            t.move(self.host.width() - t.width() - MARGIN, y + getattr(t, "offset", 0))
            y -= GAP
