"""Диалог создания и редактирования задачи."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QSlider, QVBoxLayout, QWidget,
)

from .. import config
from ..models import DIFFICULTY_LABELS, IMPORTANCE_LABELS, Task, zone_for


class LabeledSlider(QWidget):
    """Слайдер 1..5 с подписью текущего значения справа («4 — Очень значимо»)."""

    def __init__(self, labels: dict[int, str], value: int, parent=None):
        super().__init__(parent)
        self._labels = labels

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(config.SCALE_MIN, config.SCALE_MAX)
        self.slider.setPageStep(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.setValue(value)

        self.caption = QLabel()
        self.caption.setMinimumWidth(170)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.slider, 1)
        lay.addWidget(self.caption)

        self.slider.valueChanged.connect(self._update_caption)
        self._update_caption(value)

    def _update_caption(self, v: int) -> None:
        self.caption.setText(f"<b>{v}</b> — {self._labels.get(v, '')}")

    def value(self) -> int:
        return self.slider.value()


class TaskDialog(QDialog):
    """
    Если task=None — создаём новую задачу, иначе редактируем копию переданной.
    Результат забирается через result_task() после exec() == Accepted.
    """

    def __init__(self, task: Optional[Task] = None, parent=None):
        super().__init__(parent)
        self._is_new = task is None
        # Работаем с копией, чтобы «Отмена» не меняла исходный объект
        self._task = replace(task) if task else Task(title="")

        self.setWindowTitle("Новая задача" if self._is_new else "Редактирование задачи")
        self.setMinimumWidth(480)

        # --- Поля ---
        self.title_edit = QLineEdit(self._task.title)
        self.title_edit.setPlaceholderText("Что нужно сделать?")

        self.desc_edit = QPlainTextEdit(self._task.description)
        self.desc_edit.setPlaceholderText("Подробности (необязательно)")
        self.desc_edit.setFixedHeight(90)

        self.importance = LabeledSlider(IMPORTANCE_LABELS, self._task.importance)
        self.difficulty = LabeledSlider(DIFFICULTY_LABELS, self._task.difficulty)

        # Срок: чекбокс включает выбор даты через всплывающий календарь
        self.due_check = QCheckBox("Указать срок")
        self.due_edit = QDateEdit()
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("dd.MM.yyyy")
        if self._task.due_date:
            self.due_check.setChecked(True)
            self.due_edit.setDate(QDate(self._task.due_date))
        else:
            self.due_edit.setDate(QDate.currentDate())
        self.due_edit.setEnabled(self.due_check.isChecked())
        self.due_check.toggled.connect(self.due_edit.setEnabled)

        due_row = QHBoxLayout()
        due_row.addWidget(self.due_check)
        due_row.addWidget(self.due_edit, 1)

        self.done_check = QCheckBox("Задача выполнена")
        self.done_check.setChecked(self._task.done)

        # Подсказка: в какую зону попадёт задача с текущими значениями
        self.zone_hint = QLabel()
        self.zone_hint.setObjectName("muted")
        self.importance.slider.valueChanged.connect(self._update_zone_hint)
        self.difficulty.slider.valueChanged.connect(self._update_zone_hint)
        self._update_zone_hint()

        form = QFormLayout()
        form.addRow("Название*:", self.title_edit)
        form.addRow("Описание:", self.desc_edit)
        form.addRow("Значимость:", self.importance)
        form.addRow("Сложность:", self.difficulty)
        form.addRow("Срок:", due_row)
        if not self._is_new:
            form.addRow("", self.done_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.Save).setObjectName("primary")
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(self.zone_hint)
        root.addWidget(buttons)

        self.title_edit.setFocus()

    def _update_zone_hint(self) -> None:
        zone = zone_for(self.importance.value(), self.difficulty.value())
        color = config.ZONE_COLORS[zone]
        self.zone_hint.setText(
            f"Зона: <b style='color:{color}'>{config.ZONE_TITLES[zone]}</b>"
        )

    def _on_accept(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Нет названия", "Введите название задачи.")
            self.title_edit.setFocus()
            return

        t = self._task
        t.title = title
        t.description = self.desc_edit.toPlainText().strip()
        t.importance = self.importance.value()
        t.difficulty = self.difficulty.value()
        t.due_date = self.due_edit.date().toPython() if self.due_check.isChecked() else None
        t.done = self.done_check.isChecked()
        self.accept()

    def result_task(self) -> Task:
        return self._task
