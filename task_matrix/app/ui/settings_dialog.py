"""Настройки в стиле iOS: персонаж (имя, аватар), задание дня, тема."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QGridLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout,
)

from .. import game
from . import themes
from .ios import Segmented
from .task_dialog import row, section, separator, sheet_header


def section_title(text: str) -> QLabel:
    """Подпись группы заглавными буквами, как в «Настройках» iOS."""
    label = QLabel(text.upper())
    label.setObjectName("sectionHeader")
    return label


class SettingsDialog(QDialog):
    def __init__(self, current_theme: str, name: str, avatar_emoji: str,
                 daily_goal: int, db_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(480)
        self._avatar = avatar_emoji
        c = themes.colors()

        header, done_btn = sheet_header(self, "Настройки")
        done_btn.clicked.connect(self.accept)

        # --- Персонаж ---
        self.name_edit = QLineEdit(name)
        self.name_edit.setMaxLength(24)
        self.name_edit.setPlaceholderText("Имя героя")
        self.name_edit.setAlignment(Qt.AlignRight)
        self.name_edit.setStyleSheet("QLineEdit, QLineEdit:focus { background: transparent; border: none; }")

        # Сетка кнопок-аватаров: выбранный обведён синим
        grid = QGridLayout()
        grid.setSpacing(8)
        self._avatar_buttons = QButtonGroup(self)
        self._avatar_buttons.setExclusive(True)
        for i, emoji in enumerate(game.AVATARS):
            btn = QPushButton(emoji)
            btn.setCheckable(True)
            btn.setChecked(emoji == avatar_emoji)
            btn.setFixedSize(46, 46)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ font-size: 22px; padding: 0; border-radius: 23px; background: {c['surface2']}; }}"
                f"QPushButton:checked {{ border: 2px solid {c['accent']}; background: {themes.rgba(c['accent'], 0.15)}; }}")
            btn.clicked.connect(lambda _=False, e=emoji: setattr(self, "_avatar", e))
            self._avatar_buttons.addButton(btn)
            grid.addWidget(btn, i // 6, i % 6)

        hero, hl = section()
        hl.addWidget(row("Имя", self.name_edit, stretch_first=True))
        hl.addWidget(separator())
        avatar_title = QLabel("Аватар")
        avatar_title.setContentsMargins(0, 8, 0, 6)
        hl.addWidget(avatar_title)
        hl.addLayout(grid)
        hl.addSpacing(8)

        # --- Задание дня ---
        self.goal_combo = QComboBox()
        for n in range(1, 11):
            self.goal_combo.addItem(f"{n}", n)
        self.goal_combo.setCurrentIndex(max(0, self.goal_combo.findData(daily_goal)))
        goal, gl = section()
        gl.addWidget(row("Квестов в день", self.goal_combo))
        goal_hint = QLabel(f"Выполните столько квестов за день — получите +{game.DAILY_BONUS_XP} XP.")
        goal_hint.setObjectName("sectionHeader")
        goal_hint.setWordWrap(True)

        # --- Оформление ---
        self.theme = Segmented([(title, key) for key, title in themes.THEME_NAMES.items()])
        self.theme.set_value(current_theme)
        look, ll = section()
        ll.addWidget(row("Тема", self.theme))

        path_label = QLabel(f"База данных: {db_path}")
        path_label.setObjectName("sectionHeader")
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 18)
        lay.setSpacing(6)
        lay.addLayout(header)
        lay.addSpacing(8)
        lay.addWidget(section_title("Персонаж"))
        lay.addWidget(hero)
        lay.addSpacing(10)
        lay.addWidget(section_title("Задание дня"))
        lay.addWidget(goal)
        lay.addWidget(goal_hint)
        lay.addSpacing(10)
        lay.addWidget(section_title("Оформление"))
        lay.addWidget(look)
        lay.addSpacing(10)
        lay.addWidget(path_label)

    def selected_theme(self) -> str:
        return self.theme.value()

    def player_name(self) -> str:
        return self.name_edit.text().strip() or "Игрок"

    def avatar(self) -> str:
        return self._avatar

    def daily_goal(self) -> int:
        return self.goal_combo.currentData()
