"""Небольшие переиспользуемые виджеты оформления."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from . import themes


def chip(text: str, color: str, filled: bool = False) -> QLabel:
    """
    «Чип» — маленькая скруглённая плашка с текстом (навык, редкость, XP).
    filled=False: полупрозрачный фон цвета color и цветной текст.
    filled=True:  сплошная заливка и белый текст.
    """
    label = QLabel(text)
    bg = color if filled else themes.rgba(color, 0.16)
    fg = "#ffffff" if filled else color
    label.setStyleSheet(
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 8px;"
        f" padding: 2px 8px; font-size: 8.5pt; font-weight: bold; }}"
    )
    return label


def avatar(emoji: str, size: int) -> QLabel:
    """Круглый аватар с эмодзи на градиентном фоне."""
    c = themes.colors()
    label = QLabel(emoji)
    label.setAlignment(Qt.AlignCenter)
    label.setFixedSize(size, size)
    label.setStyleSheet(
        f"QLabel {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
        f" stop:0 {c['accent']}, stop:1 {c['accent2']});"
        f" border-radius: {size // 2}px; font-size: {int(size * 0.42)}px; }}"
    )
    return label


def due_text(due: date | None, done: bool) -> str:
    """Человеческое описание срока: «сегодня», «завтра», «просрочено 2 дн.»."""
    if due is None:
        return ""
    delta = (due - date.today()).days
    if done:
        return f"📅 {due.strftime('%d.%m')}"
    if delta < 0:
        return f"⏰ просрочено {-delta} дн."
    if delta == 0:
        return "⏰ сегодня"
    if delta == 1:
        return "⏰ завтра"
    return f"📅 {due.strftime('%d.%m.%Y')}"
