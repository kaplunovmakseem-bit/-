"""Окно настроек: персонаж (имя, аватар), тема оформления, цель дня."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QDialogButtonBox, QFormLayout, QGridLayout, QGroupBox,
    QComboBox, QLabel, QLineEdit, QPushButton, QRadioButton, QVBoxLayout,
)

from .. import game
from . import themes


class SettingsDialog(QDialog):
    def __init__(self, current_theme: str, name: str, avatar_emoji: str,
                 daily_goal: int, db_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(440)
        self._avatar = avatar_emoji

        # --- Персонаж ---
        hero = QGroupBox("Персонаж")
        form = QFormLayout(hero)
        self.name_edit = QLineEdit(name)
        self.name_edit.setMaxLength(24)
        self.name_edit.setPlaceholderText("Имя героя")
        form.addRow("Имя:", self.name_edit)

        # Сетка кнопок-аватаров: выбранный подсвечивается
        grid = QGridLayout()
        grid.setSpacing(6)
        self._avatar_buttons = QButtonGroup(self)
        self._avatar_buttons.setExclusive(True)
        for i, emoji in enumerate(game.AVATARS):
            btn = QPushButton(emoji)
            btn.setCheckable(True)
            btn.setChecked(emoji == avatar_emoji)
            btn.setFixedSize(44, 44)
            btn.setStyleSheet(
                "QPushButton { font-size: 20px; padding: 0; border-radius: 22px; }"
                f"QPushButton:checked {{ border: 2px solid {themes.colors()['accent']};"
                f" background: {themes.rgba(themes.colors()['accent'], 0.25)}; }}")
            btn.clicked.connect(lambda _=False, e=emoji: setattr(self, "_avatar", e))
            self._avatar_buttons.addButton(btn)
            grid.addWidget(btn, i // 6, i % 6)
        form.addRow("Аватар:", grid)

        self.goal_spin = QComboBox()
        for n in range(1, 11):
            self.goal_spin.addItem(f"{n} в день", n)
        self.goal_spin.setCurrentIndex(max(0, self.goal_spin.findData(daily_goal)))
        form.addRow("Квестов для\nзадания дня:", self.goal_spin)

        # --- Тема: радиокнопки ---
        group = QGroupBox("Тема оформления")
        g = QVBoxLayout(group)
        self._buttons = QButtonGroup(self)
        for key, title in themes.THEME_NAMES.items():
            rb = QRadioButton(title)
            rb.setProperty("theme_key", key)
            rb.setChecked(key == current_theme)
            self._buttons.addButton(rb)
            g.addWidget(rb)

        path_label = QLabel(f"База данных:<br><small>{db_path}</small>")
        path_label.setObjectName("muted")
        path_label.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Применить")
        buttons.button(QDialogButtonBox.Ok).setObjectName("primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.addWidget(hero)
        lay.addWidget(group)
        lay.addWidget(path_label)
        lay.addWidget(buttons)

    def selected_theme(self) -> str:
        return self._buttons.checkedButton().property("theme_key")

    def player_name(self) -> str:
        return self.name_edit.text().strip() or "Игрок"

    def avatar(self) -> str:
        return self._avatar

    def daily_goal(self) -> int:
        return self.goal_spin.currentData()
