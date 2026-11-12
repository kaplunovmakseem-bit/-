"""
Диалог создания и редактирования квеста — в стиле «листа» iOS:

  Отмена            Новый квест            Готово
  ┌ Название                                    ┐
  │ Описание                                    │
  ├ Навык                              💪 Сила ▾┤
  │ Значимость   ━━━━●───────   4 · Очень значимо│
  │ Сложность    ━━●─────────   2 · Легко        │
  ├ Срок                          [дата]   (⬤ ) ┤
  │ Выполнен                               (  ⬤)│
  └ Зона · Редкость · Награда                   ┘
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSlider, QVBoxLayout,
    QWidget,
)

from .. import config, game
from ..models import DIFFICULTY_LABELS, IMPORTANCE_LABELS, Task, zone_for
from . import themes
from .ios import IOSSwitch


def sheet_header(dialog: QDialog, title: str, done_text: str = "Готово"):
    """Верхняя строка листа: «Отмена» — заголовок — «Готово». Возвращает (layout, кнопка готово)."""
    cancel = QPushButton("Отмена")
    cancel.setObjectName("plain")
    cancel.setCursor(Qt.PointingHandCursor)
    cancel.clicked.connect(dialog.reject)
    done = QPushButton(done_text)
    done.setObjectName("plainBold")
    done.setCursor(Qt.PointingHandCursor)
    done.setDefault(True)
    label = QLabel(title)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("font-weight: 700; font-size: 11pt;")
    row = QHBoxLayout()
    row.addWidget(cancel)
    row.addWidget(label, 1)
    row.addWidget(done)
    # Невидимый «близнец» слева, чтобы заголовок был точно по центру
    cancel.setMinimumWidth(done.sizeHint().width())
    done.setMinimumWidth(cancel.sizeHint().width())
    return row, done


def section() -> tuple[QFrame, QVBoxLayout]:
    """Белая скруглённая группа строк."""
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 6, 14, 6)
    lay.setSpacing(0)
    return frame, lay


def separator() -> QFrame:
    line = QFrame()
    line.setObjectName("separator")
    return line


def row(label: str, *widgets, stretch_first: bool = False) -> QWidget:
    """Строка группы: подпись слева, элементы управления справа."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 8, 0, 8)
    lay.setSpacing(10)
    lab = QLabel(label)
    lab.setMinimumWidth(100)
    lay.addWidget(lab)
    if not stretch_first:
        lay.addStretch(1)
    for x in widgets:
        lay.addWidget(x, 1 if stretch_first else 0)
    return w


class LabeledSlider(QWidget):
    """Слайдер 1..5 с подписью текущего значения справа («4 · Очень значимо»)."""

    def __init__(self, labels: dict[int, str], value: int, parent=None):
        super().__init__(parent)
        self._labels = labels

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(config.SCALE_MIN, config.SCALE_MAX)
        self.slider.setPageStep(1)
        self.slider.setValue(value)
        self.slider.setCursor(Qt.PointingHandCursor)

        self.caption = QLabel()
        self.caption.setMinimumWidth(150)
        self.caption.setObjectName("muted")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.slider, 1)
        lay.addWidget(self.caption)

        self.slider.valueChanged.connect(self._update_caption)
        self._update_caption(value)

    def _update_caption(self, v: int) -> None:
        self.caption.setText(f"{v} · {self._labels.get(v, '')}")

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

        self.setWindowTitle("Новый квест" if self._is_new else "Редактирование квеста")
        self.setMinimumWidth(560)

        header, done_btn = sheet_header(self, "Новый квест" if self._is_new else "Квест",
                                        "Добавить" if self._is_new else "Готово")
        done_btn.clicked.connect(self._on_accept)

        # --- Группа 1: название и описание ---
        self.title_edit = QLineEdit(self._task.title)
        self.title_edit.setPlaceholderText("Название")
        self.title_edit.setStyleSheet("QLineEdit, QLineEdit:focus { background: transparent; border: none;"
                                      " font-size: 11pt; padding: 8px 0; }")
        self.desc_edit = QPlainTextEdit(self._task.description)
        self.desc_edit.setPlaceholderText("Заметки")
        self.desc_edit.setFixedHeight(70)
        self.desc_edit.setStyleSheet("QPlainTextEdit, QPlainTextEdit:focus { background: transparent; border: none;"
                                     " padding: 4px 0; }")
        g1, l1 = section()
        l1.addWidget(self.title_edit)
        l1.addWidget(separator())
        l1.addWidget(self.desc_edit)

        # --- Группа 2: навык, значимость, сложность ---
        self.skill_combo = QComboBox()
        for key, (name, icon, _light, _dark) in game.SKILLS.items():
            self.skill_combo.addItem(f"{icon}  {name}", key)
        self.skill_combo.setCurrentIndex(max(0, self.skill_combo.findData(self._task.skill)))
        self.skill_combo.setMinimumWidth(180)
        self.importance = LabeledSlider(IMPORTANCE_LABELS, self._task.importance)
        self.difficulty = LabeledSlider(DIFFICULTY_LABELS, self._task.difficulty)
        g2, l2 = section()
        l2.addWidget(row("Навык", self.skill_combo))
        l2.addWidget(separator())
        l2.addWidget(row("Значимость", self.importance, stretch_first=True))
        l2.addWidget(separator())
        l2.addWidget(row("Сложность", self.difficulty, stretch_first=True))

        # --- Группа 3: срок и статус (тумблеры iOS) ---
        self.due_switch = IOSSwitch()
        self.due_edit = QDateEdit()
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("dd.MM.yyyy")
        if self._task.due_date:
            self.due_switch.setChecked(True)
            self.due_edit.setDate(QDate(self._task.due_date))
        else:
            self.due_edit.setDate(QDate.currentDate())
        self.due_edit.setVisible(self.due_switch.isChecked())
        self.due_switch.toggled.connect(self.due_edit.setVisible)

        self.done_switch = IOSSwitch()
        self.done_switch.setChecked(self._task.done)
        g3, l3 = section()
        l3.addWidget(row("Срок", self.due_edit, self.due_switch))
        if not self._is_new:
            l3.addWidget(separator())
            l3.addWidget(row("Выполнен", self.done_switch))

        # --- Итог: зона, редкость, награда ---
        self.zone_value = QLabel()
        self.rarity_value = QLabel()
        self.xp_value = QLabel()
        summary = QGridLayout()
        summary.setHorizontalSpacing(10)
        for i, (cap, val) in enumerate((("ЗОНА", self.zone_value), ("РЕДКОСТЬ", self.rarity_value),
                                        ("НАГРАДА", self.xp_value))):
            tile = QFrame()
            tile.setObjectName("card")
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(12, 8, 12, 8)
            tl.setSpacing(0)
            c = QLabel(cap)
            c.setObjectName("caption")
            val.setStyleSheet("font-weight: 700; font-size: 10.5pt;")
            tl.addWidget(c)
            tl.addWidget(val)
            summary.addWidget(tile, 0, i)

        self.importance.slider.valueChanged.connect(self._update_summary)
        self.difficulty.slider.valueChanged.connect(self._update_summary)
        self.due_switch.toggled.connect(self._update_summary)
        self.due_edit.dateChanged.connect(self._update_summary)
        self._update_summary()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 18)
        root.setSpacing(14)
        root.addLayout(header)
        root.addWidget(g1)
        root.addWidget(g2)
        root.addWidget(g3)
        root.addLayout(summary)

        self.title_edit.setFocus()

    def _update_summary(self) -> None:
        """Зона, редкость и награда за квест с текущими значениями."""
        c = themes.colors()
        imp, diff = self.importance.value(), self.difficulty.value()
        zone = zone_for(imp, diff)
        preview = Task(title="", importance=imp, difficulty=diff,
                       due_date=self.due_edit.date().toPython() if self.due_switch.isChecked() else None)
        xp = game.xp_for_task(preview, date.today())
        rarity_name, rarity_color = game.rarity(diff)
        self.zone_value.setText(f"{config.ZONE_ICONS[zone]} {config.ZONE_TITLES[zone]}")
        self.rarity_value.setText(f"<span style='color:{rarity_color}'>●</span> {rarity_name}")
        bonus = " <span style='font-size:8pt; font-weight:400'>с бонусом</span>" \
            if game.is_on_time(preview, date.today()) else ""
        self.xp_value.setText(f"<span style='color:{c['gold']}'>+{xp} XP</span>{bonus}")

    def _on_accept(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Нет названия", "Введите название квеста.")
            self.title_edit.setFocus()
            return

        t = self._task
        t.title = title
        t.description = self.desc_edit.toPlainText().strip()
        t.importance = self.importance.value()
        t.difficulty = self.difficulty.value()
        t.due_date = self.due_edit.date().toPython() if self.due_switch.isChecked() else None
        t.done = self.done_switch.isChecked()
        t.skill = self.skill_combo.currentData()
        self.accept()

    def result_task(self) -> Task:
        return self._task
