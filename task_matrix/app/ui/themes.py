"""
Светлая и тёмная темы в «игровом» стиле.

Тема = набор цветов (словарь THEMES) + таблица стилей QSS, которая
строится из этих цветов. Переключение темы заново применяет палитру и
стиль ко всему приложению; виджеты с индивидуальной раскраской (карточки,
зоны, профиль) берут цвета через colors().
"""

from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

LIGHT = "light"
DARK = "dark"

THEME_NAMES = {DARK: "🌙 Тёмная (игровая)", LIGHT: "☀️ Светлая"}

THEMES = {
    DARK: {
        "window": "#0e1120",      # фон окна (верх градиента)
        "window2": "#151a30",     # фон окна (низ градиента)
        "surface": "#1b2038",     # карточки, поля ввода
        "surface2": "#242a48",    # приподнятые элементы, чипы
        "text": "#eceefe",
        "muted": "#8d93b8",
        "border": "#2d3458",
        "accent": "#8b5cf6",      # фиолетовый
        "accent2": "#22d3ee",     # бирюзовый (второй цвет градиента)
        "accent_text": "#ffffff",
        "gold": "#fbbf24",
        "zone_tint": 0.10,        # насколько цвет зоны окрашивает её фон
    },
    LIGHT: {
        "window": "#f5f3ff",
        "window2": "#eef4ff",
        "surface": "#ffffff",
        "surface2": "#f0edfb",
        "text": "#1f1d3d",
        "muted": "#6f6a93",
        "border": "#e3def5",
        "accent": "#7c4dff",
        "accent2": "#0ea5e9",
        "accent_text": "#ffffff",
        "gold": "#e59e0b",
        "zone_tint": 0.08,
    },
}

_current = DARK


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


def rgba(color: str, alpha: float) -> str:
    """Цвет с прозрачностью в формате QSS: rgba(r, g, b, a)."""
    c = QColor(color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {int(alpha * 255)})"


def zone_background(accent: str) -> str:
    """Фон зоны: поверхность, слегка окрашенная акцентным цветом зоны."""
    c = colors()
    return mix(c["window2"], accent, c["zone_tint"])


def gradient(c1: str, c2: str) -> str:
    """Горизонтальный градиент для QSS."""
    return f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c1}, stop:1 {c2})"


def progress_style(c1: str, c2: str, height: int = 10) -> str:
    """Стиль прогресс-бара с градиентной заливкой (полоса опыта)."""
    c = colors()
    return f"""
        QProgressBar {{
            background: {c['surface2']}; border: none; border-radius: {height // 2}px;
            min-height: {height}px; max-height: {height}px; text-align: center;
        }}
        QProgressBar::chunk {{ background: {gradient(c1, c2)}; border-radius: {height // 2}px; }}
    """


def _stylesheet(c: dict) -> str:
    return f"""
    QWidget {{ color: {c['text']}; font-size: 10pt; }}
    QMainWindow, QDialog {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c['window']}, stop:1 {c['window2']});
    }}
    QMenuBar {{ background: transparent; }}
    QMenuBar::item:selected {{ background: {c['surface2']}; border-radius: 4px; }}
    QMenu {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 8px; padding: 4px; }}
    QMenu::item {{ padding: 6px 18px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {c['accent']}; color: {c['accent_text']}; }}
    QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 8px; }}

    QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QComboBox, QSpinBox {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 6px 10px;
        selection-background-color: {c['accent']};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus,
    QComboBox:focus, QSpinBox:focus {{ border: 1px solid {c['accent']}; }}
    QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background: {c['surface']}; border: 1px solid {c['border']};
        selection-background-color: {c['accent']}; outline: none;
    }}

    QPushButton {{
        background: {c['surface2']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{ border-color: {c['accent']}; }}
    QPushButton:pressed {{ background: {c['border']}; }}
    QPushButton#primary {{
        background: {gradient(c['accent'], c['accent2'])};
        color: {c['accent_text']};
        border: none;
        font-weight: bold;
        padding: 9px 18px;
    }}
    QPushButton#primary:hover {{ background: {gradient(mix(c['accent'], '#ffffff', 0.12), mix(c['accent2'], '#ffffff', 0.12))}; }}

    /* Круглые «игровые» чекбоксы */
    QCheckBox {{ spacing: 8px; background: transparent; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px; border-radius: 10px;
        border: 2px solid {c['muted']}; background: transparent;
    }}
    QCheckBox::indicator:hover {{ border-color: {c['accent']}; }}
    QCheckBox::indicator:checked {{
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
                                    stop:0 {c['accent2']}, stop:0.55 {c['accent']}, stop:0.6 {c['accent']});
        border-color: {c['accent']};
    }}
    QRadioButton {{ spacing: 8px; background: transparent; }}
    QRadioButton::indicator {{
        width: 14px; height: 14px; border-radius: 9px;
        border: 2px solid {c['muted']}; background: transparent;
    }}
    QRadioButton::indicator:checked {{
        border: 2px solid {c['accent']};
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
                                    stop:0 {c['accent']}, stop:0.5 {c['accent']}, stop:0.6 transparent);
    }}
    QTableView::indicator {{
        width: 16px; height: 16px; border-radius: 9px;
        border: 2px solid {c['muted']}; background: transparent;
    }}
    QTableView::indicator:checked {{ background: {c['accent']}; border-color: {c['accent']}; }}

    QTabWidget::pane {{ border: none; }}
    QTabWidget::tab-bar {{ left: 14px; }}
    QTabBar::tab {{
        background: transparent;
        padding: 8px 18px;
        margin-right: 4px;
        border-radius: 10px;
        color: {c['muted']};
        font-weight: bold;
    }}
    QTabBar::tab:hover {{ color: {c['text']}; }}
    QTabBar::tab:selected {{ color: {c['accent_text']}; background: {gradient(c['accent'], c['accent2'])}; }}

    QTableView {{
        background: {c['surface']};
        alternate-background-color: {mix(c['surface'], c['surface2'], 0.5)};
        border: 1px solid {c['border']};
        border-radius: 12px;
        gridline-color: transparent;
        selection-background-color: {rgba(c['accent'], 0.35)};
        selection-color: {c['text']};
    }}
    QTableView::item {{ padding: 4px; }}
    QHeaderView::section {{
        background: {c['surface']};
        color: {c['muted']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 8px 6px;
        font-weight: bold;
    }}

    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 3px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
    QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {c['border']}; border-radius: 3px; min-width: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    QSlider::groove:horizontal {{ height: 6px; background: {c['surface2']}; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{ background: {gradient(c['accent'], c['accent2'])}; border-radius: 3px; }}
    QSlider::handle:horizontal {{
        background: {c['accent_text']}; border: 3px solid {c['accent']};
        width: 12px; height: 12px; margin: -6px 0; border-radius: 9px;
    }}

    QGroupBox {{
        border: 1px solid {c['border']}; border-radius: 12px; margin-top: 14px; padding: 10px;
        background: {c['surface']};
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; color: {c['muted']}; }}

    QLabel {{ background: transparent; }}
    QLabel#muted {{ color: {c['muted']}; }}
    QLabel#h1 {{ font-size: 18pt; font-weight: 800; }}
    QLabel#h2 {{ font-size: 13pt; font-weight: bold; }}

    QFrame#panel {{
        background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 16px;
    }}

    QToolTip {{
        background: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 4px;
    }}
    """


def apply_theme(app: QApplication, name: str) -> None:
    """Применяет тему ко всему приложению."""
    global _current
    _current = name if name in THEMES else DARK
    c = THEMES[_current]

    # Шрифт: на Windows — Segoe UI (современный и хорошо читаемый)
    if sys.platform == "win32":
        app.setFont(QFont("Segoe UI", 10))

    # Палитра нужна для стандартных элементов (календарь, меню, диалоги)
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(c["window"]))
    pal.setColor(QPalette.WindowText, QColor(c["text"]))
    pal.setColor(QPalette.Base, QColor(c["surface"]))
    pal.setColor(QPalette.AlternateBase, QColor(c["surface2"]))
    pal.setColor(QPalette.Text, QColor(c["text"]))
    pal.setColor(QPalette.Button, QColor(c["surface2"]))
    pal.setColor(QPalette.ButtonText, QColor(c["text"]))
    pal.setColor(QPalette.Highlight, QColor(c["accent"]))
    pal.setColor(QPalette.HighlightedText, QColor(c["accent_text"]))
    pal.setColor(QPalette.ToolTipBase, QColor(c["surface"]))
    pal.setColor(QPalette.ToolTipText, QColor(c["text"]))
    pal.setColor(QPalette.PlaceholderText, QColor(c["muted"]))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor(c["muted"]))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c["muted"]))
    app.setPalette(pal)
    app.setStyleSheet(_stylesheet(c))
