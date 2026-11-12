"""Небольшие переиспользуемые виджеты оформления."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from . import themes


def chip(text: str, color: str, filled: bool = False) -> QLabel:
    """
    «Чип» — маленькая скруглённая плашка с текстом (уровень, награда).
    filled=False: полупрозрачный фон цвета color и цветной текст.
    filled=True:  сплошная заливка и белый текст.
    """
    label = QLabel(text)
    bg = color if filled else themes.rgba(color, 0.14)
    fg = "#ffffff" if filled else color
    label.setStyleSheet(
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 6px;"
        f" padding: 2px 7px; font-size: 8.5pt; font-weight: 600; }}"
    )
    return label


def avatar(emoji: str, size: int) -> QLabel:
    """Круглый аватар с эмодзи на мягком фоне (как фото контакта в iOS)."""
    c = themes.colors()
    label = QLabel(emoji)
    label.setAlignment(Qt.AlignCenter)
    label.setFixedSize(size, size)
    label.setStyleSheet(
        f"QLabel {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
        f" stop:0 {themes.mix(c['surface2'], c['accent'], 0.10)},"
        f" stop:1 {themes.mix(c['surface2'], c['accent'], 0.28)});"
        f" border-radius: {size // 2}px; font-size: {int(size * 0.5)}px; }}"
    )
    return label


def due_text(due: date | None, done: bool) -> str:
    """Человеческое описание срока: «Сегодня», «Завтра», «Просрочено на 2 дн.»."""
    if due is None:
        return ""
    delta = (due - date.today()).days
    if done or delta > 1:
        return due.strftime("%d.%m.%Y")
    if delta < 0:
        return f"Просрочено на {-delta} дн."
    if delta == 0:
        return "Сегодня"
    return "Завтра"
