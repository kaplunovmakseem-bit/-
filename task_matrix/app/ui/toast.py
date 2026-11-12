"""
Всплывающие уведомления в стиле баннеров iOS («+78 XP», «Новый уровень!»).

Баннер появляется сверху по центру окна, плавно «выезжает» вниз и через
несколько секунд исчезает. Несколько баннеров складываются стопкой.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QParallelAnimationGroup, QPropertyAnimation,
    QSequentialAnimationGroup, Qt, QVariantAnimation,
)

from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout,
    QLabel, QVBoxLayout, QWidget,
)

from . import themes

TOP = 14
GAP = 8


class Toast(QFrame):
    def __init__(self, parent: QWidget, icon: str, title: str, subtitle: str, color: str):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # не мешает кликам
        c = themes.colors()

        # Иконка «приложения» — цветной скруглённый квадрат
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(38, 38)
        icon_label.setStyleSheet(f"background: {color}; border-radius: 9px; font-size: 19px;")

        app_line = QLabel("LIFE RPG · сейчас")
        app_line.setStyleSheet(f"color: {c['muted']}; font-size: 7.5pt; font-weight: 600;")
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {c['text']}; font-weight: 700; font-size: 10.5pt;")
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet(f"color: {c['text']}; font-size: 9.5pt;")
        sub_label.setVisible(bool(subtitle))

        col = QVBoxLayout()
        col.setSpacing(0)
        col.addWidget(app_line)
        col.addWidget(title_label)
        col.addWidget(sub_label)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 22, 10)
        lay.setSpacing(12)
        lay.addWidget(icon_label)
        lay.addLayout(col)

        self.setStyleSheet(f"""
            QFrame#toast {{
                background: {themes.rgba(c['surface2'] if themes.is_dark() else c['surface'], 0.97)};
                border: 1px solid {c['separator']};
                border-radius: 18px;
            }}
            QLabel {{ background: transparent; }}
        """)
        self.setMinimumWidth(340)
        self.opacity = QGraphicsOpacityEffect(self)
        self.opacity.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity)
        self.adjustSize()


class ToastManager:
    """
    Показывает баннеры и раскладывает их стопкой сверху вниз.

    Сдвиг анимируем через toast.offset (QVariantAnimation), а не через
    свойство pos: Qt останавливает предыдущую анимацию того же свойства,
    и при одновременных уведомлениях они бы «застревали».
    """

    MAX_VISIBLE = 4

    def __init__(self, host: QWidget):
        self.host = host
        self.toasts: list[Toast] = []
        self._anims = []  # держим ссылки, чтобы анимации не удалил сборщик мусора

    def show(self, icon: str, title: str, subtitle: str = "", color: str = "#007AFF",
             big: bool = False, duration_ms: int = 3200) -> None:
        toast = Toast(self.host, icon, title, subtitle, color)
        toast.offset = -30  # стартует чуть выше и «выезжает» вниз
        self.toasts.append(toast)
        while len(self.toasts) > self.MAX_VISIBLE:
            self._discard(self.toasts[0])
        toast.show()
        toast.raise_()
        self.reposition()

        fade_in = QPropertyAnimation(toast.opacity, b"opacity")
        fade_in.setDuration(220)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)

        slide = QVariantAnimation()
        slide.setDuration(420)
        slide.setStartValue(-30)
        slide.setEndValue(0)
        slide.setEasingCurve(QEasingCurve.OutBack)
        slide.valueChanged.connect(lambda v, t=toast: self._set_offset(t, v))

        appear = QParallelAnimationGroup()
        appear.addAnimation(fade_in)
        appear.addAnimation(slide)

        fade_out = QPropertyAnimation(toast.opacity, b"opacity")
        fade_out.setDuration(350)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        seq = QSequentialAnimationGroup()
        seq.addAnimation(appear)
        seq.addPause(duration_ms + (1200 if big else 0))
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
        """Баннеры по центру сверху, новые — ниже предыдущих."""
        y = TOP
        for t in self.toasts:
            t.move((self.host.width() - t.width()) // 2, y + getattr(t, "offset", 0))
            y += t.height() + GAP
