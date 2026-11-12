"""
Светлая и тёмная темы.

Тема = набор цветов (словарь THEMES) + таблица стилей QSS, которая
строится из этих цветов. Переключение темы просто заново применяет
палитру и стиль ко всему приложению.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

LIGHT = "light"
DARK = "dark"

THEME_NAMES = {LIGHT: "Светлая", DARK: "Тёмная"}

THEMES = {
    LIGHT: {
        "window": "#f3f4f7",
        "surface": "#ffffff",     # фон карточек, полей ввода
        "text": "#1f2329",
        "muted": "#6b7280",       # второстепенный текст
        "border": "#d9dce3",
        "highlight": "#3a7bd5",
        "highlight_text": "#ffffff",
        "zone_tint": 0.10,        # насколько сильно цвет зоны окрашивает её фон
    },
    DARK: {
        "window": "#1e1f24",
        "surface": "#2a2c33",
        "text": "#e6e7ea",
        "muted": "#9aa0aa",
        "border": "#3b3e47",
        "highlight": "#4c8ce6",
        "highlight_text": "#ffffff",
        "zone_tint": 0.16,
    },
}

# Текущая тема хранится здесь, чтобы виджеты могли спросить свои цвета
_current = LIGHT


def current() -> str:
    return _current


def colors() -> dict:
    return THEMES[_current]


def mix(color_a: str, color_b: str, ratio: float) -> str:
    """Смешивает два цвета: ratio=0 → color_a, ratio=1 → color_b."""
    a, b = QColor(color_a), QColor(color_b)
    r = a.red() + (b.red() - a.red()) * ratio
    g = a.green() + (b.green() - a.green()) * ratio
    bl = a.blue() + (b.blue() - a.blue()) * ratio
    return QColor(int(r), int(g), int(bl)).name()


def zone_background(accent: str) -> str:
    """Фон зоны: цвет окна, слегка окрашенный акцентным цветом зоны."""
    c = colors()
    return mix(c["window"], accent, c["zone_tint"])


def _stylesheet(c: dict) -> str:
    return f"""
    QWidget {{ color: {c['text']}; font-size: 10pt; }}
    QMainWindow, QDialog {{ background: {c['window']}; }}

    QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QComboBox {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 4px 6px;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus {{
        border: 1px solid {c['highlight']};
    }}

    QPushButton {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 12px;
    }}
    QPushButton:hover {{ border-color: {c['highlight']}; }}
    QPushButton#primary {{
        background: {c['highlight']};
        color: {c['highlight_text']};
        border: none;
        font-weight: bold;
    }}

    QTabWidget::pane {{ border: none; }}
    QTabBar::tab {{
        background: transparent;
        padding: 8px 16px;
        border-bottom: 2px solid transparent;
        color: {c['muted']};
    }}
    QTabBar::tab:selected {{
        color: {c['text']};
        border-bottom: 2px solid {c['highlight']};
    }}

    QTableView {{
        background: {c['surface']};
        alternate-background-color: {mix(c['surface'], c['window'], 0.6)};
        border: 1px solid {c['border']};
        border-radius: 6px;
        gridline-color: {c['border']};
        selection-background-color: {c['highlight']};
        selection-color: {c['highlight_text']};
    }}
    QHeaderView::section {{
        background: {c['window']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 6px;
        font-weight: bold;
    }}

    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}

    QLabel#muted {{ color: {c['muted']}; }}

    QToolTip {{
        background: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
    }}
    """


def apply_theme(app: QApplication, name: str) -> None:
    """Применяет тему ко всему приложению."""
    global _current
    _current = name if name in THEMES else LIGHT
    c = THEMES[_current]

    # Палитра нужна для стандартных элементов (календарь, меню, чекбоксы)
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(c["window"]))
    pal.setColor(QPalette.WindowText, QColor(c["text"]))
    pal.setColor(QPalette.Base, QColor(c["surface"]))
    pal.setColor(QPalette.AlternateBase, QColor(c["window"]))
    pal.setColor(QPalette.Text, QColor(c["text"]))
    pal.setColor(QPalette.Button, QColor(c["surface"]))
    pal.setColor(QPalette.ButtonText, QColor(c["text"]))
    pal.setColor(QPalette.Highlight, QColor(c["highlight"]))
    pal.setColor(QPalette.HighlightedText, QColor(c["highlight_text"]))
    pal.setColor(QPalette.ToolTipBase, QColor(c["surface"]))
    pal.setColor(QPalette.ToolTipText, QColor(c["text"]))
    pal.setColor(QPalette.PlaceholderText, QColor(c["muted"]))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor(c["muted"]))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c["muted"]))
    app.setPalette(pal)
    app.setStyleSheet(_stylesheet(c))
