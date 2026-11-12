"""Окно настроек: выбор темы оформления."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QDialogButtonBox, QGroupBox, QLabel, QRadioButton,
    QVBoxLayout,
)

from . import themes


class SettingsDialog(QDialog):
    def __init__(self, current_theme: str, db_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(380)

        # Переключатель темы: радиокнопки «Светлая» / «Тёмная»
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
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(group)
        lay.addWidget(path_label)
        lay.addWidget(buttons)

    def selected_theme(self) -> str:
        return self._buttons.checkedButton().property("theme_key")
