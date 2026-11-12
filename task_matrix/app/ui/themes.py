"""
Темы в стиле iOS: светлая и тёмная.

Цвета взяты из системной палитры Apple (systemBlue, systemGreen, …) и
«сгруппированных» фонов iOS: серый фон окна + белые скруглённые карточки
(в тёмной теме — чёрный фон + тёмно-серые карточки).

Тема = набор цветов (THEMES) + таблица стилей QSS, построенная из них.
Виджеты, которые рисуются вручную (диаграммы, кольца, переключатели),
берут цвета через colors().
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

from .. import config, game

LIGHT = "light"
DARK = "dark"

THEME_NAMES = {LIGHT: "Светлая", DARK: "Тёмная"}

THEMES = {
    LIGHT: {
        "window": "#F2F2F7",      # systemGroupedBackground
        "surface": "#FFFFFF",     # карточки (secondarySystemGroupedBackground)
        "surface2": "#F2F2F7",    # поля ввода и плитки внутри карточек
        "fill": "#E5E5EA",        # треки слайдеров, сегментированный контрол
        "separator": "#D8D8DC",   # тонкие разделители
        "text": "#000000",        # label
        "muted": "#8A8A8E",       # secondaryLabel
        "faint": "#C7C7CC",       # tertiaryLabel, пустые кружки
        "accent": "#007AFF",      # systemBlue
        "accent_text": "#FFFFFF",
        "gold": "#FF9500",        # опыт (systemOrange)
        "danger": "#FF3B30",
        "success": "#34C759",
        "selection": "#E8F1FF",   # фон выделенной строки
        # Кольца активности (как в «Фитнесе»)
        "ring_xp": "#FF2D55", "ring_quests": "#34C759", "ring_week": "#32ADE6",
    },
    DARK: {
        "window": "#000000",
        "surface": "#1C1C1E",
        "surface2": "#2C2C2E",
        "fill": "#3A3A3C",
        "separator": "#38383A",
        "text": "#FFFFFF",
        "muted": "#98989F",
        "faint": "#48484A",
        "accent": "#0A84FF",
        "accent_text": "#FFFFFF",
        "gold": "#FF9F0A",
        "danger": "#FF453A",
        "success": "#30D158",
        "selection": "#1A2B45",
        "ring_xp": "#FA114F", "ring_quests": "#92E82A", "ring_week": "#1EEAEF",
    },
}

_current = LIGHT


def current() -> str:
    return _current


def is_dark() -> bool:
    return _current == DARK


def colors() -> dict:
    return THEMES[_current]


# --- Цвета сущностей с учётом темы -------------------------------------------
def zone_color(zone: str) -> str:
    return (config.ZONE_COLORS_DARK if is_dark() else config.ZONE_COLORS)[zone]


def skill_color(skill: str) -> str:
    return game.skill_color(skill, dark=is_dark())


def overdue_color() -> str:
    return colors()["danger"]


# --- Утилиты для цветов ------------------------------------------------------
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


def qcolor(color: str, alpha: float = 1.0) -> QColor:
    c = QColor(color)
    c.setAlphaF(alpha)
    return c


def progress_style(color: str, height: int = 6) -> str:
    """Тонкий iOS-прогресс-бар: серый трек и цветная заливка."""
    c = colors()
    return f"""
        QProgressBar {{
            background: {c['fill']}; border: none; border-radius: {height // 2}px;
            min-height: {height}px; max-height: {height}px;
        }}
        QProgressBar::chunk {{ background: {color}; border-radius: {height // 2}px; }}
    """


def ui_font(size: float = 10, weight: QFont.Weight = QFont.Normal) -> QFont:
    """
    Шрифт интерфейса. Оригинальный шрифт iOS (SF Pro) на Windows обычно
    не установлен, поэтому берём ближайшие по духу: Segoe UI Variable
    (Windows 11), затем Segoe UI. Если SF Pro установлен — возьмётся он.
    """
    f = QFont()
    f.setFamilies(["SF Pro Display", "SF Pro Text", "Segoe UI Variable Display",
                   "Segoe UI Variable Text", "Segoe UI", "Helvetica Neue", "Inter"])
    f.setPointSizeF(size)
    f.setWeight(weight)
    return f


def _stylesheet(c: dict) -> str:
    return f"""
    QWidget {{ color: {c['text']}; font-size: 10pt; }}
    QMainWindow, QDialog, QStackedWidget#pages, QWidget#page {{ background: {c['window']}; }}

    QMenu {{ background: {c['surface']}; border: 1px solid {c['separator']}; border-radius: 12px; padding: 6px; }}
    QMenu::item {{ padding: 7px 22px 7px 12px; border-radius: 8px; }}
    QMenu::item:selected {{ background: {c['accent']}; color: {c['accent_text']}; }}
    QMenu::separator {{ height: 1px; background: {c['separator']}; margin: 4px 6px; }}

    /* Поля ввода в стиле iOS: серая заливка, без рамки */
    QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QComboBox {{
        background: {c['surface2']};
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 7px 10px;
        selection-background-color: {c['accent']};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus, QComboBox:focus {{
        border: 1px solid {c['accent']};
    }}
    QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background: {c['surface']}; border: 1px solid {c['separator']}; border-radius: 10px;
        selection-background-color: {c['accent']}; outline: none; padding: 4px;
    }}
    QCalendarWidget QWidget {{ alternate-background-color: {c['surface2']}; }}
    QCalendarWidget QToolButton {{ color: {c['text']}; background: transparent; border: none; padding: 4px 8px; }}
    QCalendarWidget QAbstractItemView {{ selection-background-color: {c['accent']}; selection-color: white; }}

    /* Кнопки: «серая» по умолчанию, «заполненная» — #primary, «текстовая» — #plain */
    QPushButton {{
        background: {c['fill']};
        color: {c['text']};
        border: none;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background: {mix(c['fill'], c['text'], 0.06)}; }}
    QPushButton:pressed {{ background: {mix(c['fill'], c['text'], 0.14)}; }}
    QPushButton#primary {{ background: {c['accent']}; color: {c['accent_text']}; }}
    QPushButton#primary:hover {{ background: {mix(c['accent'], '#ffffff', 0.12)}; }}
    QPushButton#primary:pressed {{ background: {mix(c['accent'], '#000000', 0.15)}; }}
    QPushButton#plain {{ background: transparent; color: {c['accent']}; padding: 6px 8px; font-weight: normal; }}
    QPushButton#plain:hover {{ color: {mix(c['accent'], c['text'], 0.25)}; }}
    QPushButton#plainBold {{ background: transparent; color: {c['accent']}; padding: 6px 8px; font-weight: bold; }}
    QPushButton#round {{
        background: {c['accent']}; color: white; border-radius: 18px; padding: 0;
        font-size: 18pt; font-weight: 400;
    }}
    QPushButton#round:hover {{ background: {mix(c['accent'], '#ffffff', 0.12)}; }}

    QCheckBox {{ spacing: 8px; background: transparent; }}

    /* Ползунки как в iOS: тонкий трек, белая круглая ручка */
    QSlider::groove:horizontal {{ height: 4px; background: {c['fill']}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: #FFFFFF; border: 1px solid {c['faint']};
        width: 22px; height: 22px; margin: -10px 0; border-radius: 12px;
    }}

    QTableView {{
        background: {c['surface']};
        border: none;
        border-radius: 14px;
        gridline-color: transparent;
        selection-background-color: {c['selection']};
        selection-color: {c['text']};
        outline: none;
    }}
    QTableView::item {{ border-bottom: 1px solid {c['separator']}; padding: 4px 6px; }}
    QTableView::item:selected {{ background: {c['selection']}; }}
    QTableView::indicator {{
        width: 18px; height: 18px; border-radius: 10px;
        border: 2px solid {c['faint']}; background: transparent;
    }}
    QTableView::indicator:checked {{ background: {c['accent']}; border-color: {c['accent']}; }}
    QHeaderView {{ background: transparent; }}
    QHeaderView::section {{
        background: {c['surface']};
        color: {c['muted']};
        border: none;
        border-bottom: 1px solid {c['separator']};
        padding: 10px 6px;
        font-size: 8.5pt;
        font-weight: 600;
    }}
    QTableCornerButton::section {{ background: {c['surface']}; border: none; }}

    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 3px 1px; }}
    QScrollBar::handle:vertical {{ background: {rgba(c['muted'], 0.45)}; border-radius: 3px; min-height: 30px; }}
    QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 1px 3px; }}
    QScrollBar::handle:horizontal {{ background: {rgba(c['muted'], 0.45)}; border-radius: 3px; min-width: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    QLabel {{ background: transparent; }}
    QLabel#muted {{ color: {c['muted']}; }}
    QLabel#largeTitle {{ font-size: 24pt; font-weight: 800; }}
    QLabel#h1 {{ font-size: 18pt; font-weight: 800; }}
    QLabel#h2 {{ font-size: 13pt; font-weight: 700; }}
    QLabel#caption {{ color: {c['muted']}; font-size: 8.5pt; font-weight: 600; }}
    QLabel#sectionHeader {{ color: {c['muted']}; font-size: 8.5pt; font-weight: 600; padding-left: 14px; }}

    /* Карточка iOS — белый скруглённый блок */
    QFrame#card {{ background: {c['surface']}; border: none; border-radius: 16px; }}
    QFrame#tile {{ background: {c['surface2']}; border: none; border-radius: 12px; }}
    QFrame#separator {{ background: {c['separator']}; border: none; max-height: 1px; min-height: 1px; }}

    /* Нижняя панель вкладок */
    QFrame#tabBar {{ background: {rgba(c['surface'], 0.96)}; border: none; border-top: 1px solid {c['separator']}; }}
    QPushButton#tabButton {{
        background: transparent; color: {c['muted']}; border: none; border-radius: 10px;
        padding: 4px 18px; font-size: 8.5pt; font-weight: 600;
    }}
    QPushButton#tabButton:hover {{ background: {rgba(c['muted'], 0.10)}; }}
    QPushButton#tabButton:checked {{ color: {c['accent']}; }}

    QToolTip {{
        background: {c['surface']}; color: {c['text']};
        border: 1px solid {c['separator']}; border-radius: 8px; padding: 6px 8px;
    }}
    """


def apply_theme(app: QApplication, name: str) -> None:
    """Применяет тему ко всему приложению."""
    global _current
    _current = name if name in THEMES else LIGHT
    c = THEMES[_current]
    app.setFont(ui_font(10))

    # Палитра нужна для стандартных элементов (календарь, меню, диалоги)
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(c["window"]))
    pal.setColor(QPalette.WindowText, QColor(c["text"]))
    pal.setColor(QPalette.Base, QColor(c["surface"]))
    pal.setColor(QPalette.AlternateBase, QColor(c["surface2"]))
    pal.setColor(QPalette.Text, QColor(c["text"]))
    pal.setColor(QPalette.Button, QColor(c["fill"]))
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
