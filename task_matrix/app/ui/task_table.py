"""
Вкладка «Все задачи»: таблица с сортировкой, фильтром и поиском.

Используется классическая схема Qt «модель — прокси — представление»:
  TaskTableModel   — отдаёт данные задач в виде строк и столбцов;
  TaskFilterProxy  — фильтрует (статус, поиск) и сортирует;
  QTableView       — рисует таблицу.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMenu, QTableView, QVBoxLayout, QWidget,
)

from .. import config, game
from ..models import Task

# Номера столбцов
COL_DONE, COL_TITLE, COL_SKILL, COL_ZONE, COL_IMP, COL_DIFF, COL_XP, COL_DUE, COL_CREATED = range(9)
HEADERS = ["✓", "Квест", "Навык", "Зона", "Значимость", "Сложность", "Награда", "Срок", "Создан"]

# Значения фильтра по статусу
FILTER_ACTIVE, FILTER_DONE, FILTER_ALL = "active", "done", "all"


class TaskTableModel(QAbstractTableModel):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.tasks: list[Task] = []

    def set_tasks(self, tasks: list[Task]) -> None:
        self.beginResetModel()
        self.tasks = tasks
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.tasks)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return HEADERS[section]
        return None

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == COL_DONE:
            f |= Qt.ItemIsUserCheckable
        return f

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        t = self.tasks[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == COL_TITLE:
                return t.title
            if col == COL_SKILL:
                return f"{game.skill_icon(t.skill)} {game.skill_name(t.skill)}"
            if col == COL_ZONE:
                return f"{config.ZONE_ICONS[t.zone]} {config.ZONE_TITLES[t.zone]}"
            if col == COL_XP:
                return f"{game.xp_for_task(t, date.today())} XP"
            if col == COL_IMP:
                return t.importance
            if col == COL_DIFF:
                return t.difficulty
            if col == COL_DUE:
                return t.due_date.strftime("%d.%m.%Y") if t.due_date else "—"
            if col == COL_CREATED:
                return t.created_at.strftime("%d.%m.%Y %H:%M")

        # Значения для сортировки (Qt.UserRole): «сырые» данные, а не текст
        if role == Qt.UserRole:
            if col == COL_DONE:
                return int(t.done)
            if col == COL_TITLE:
                return t.title.lower()
            if col == COL_SKILL:
                return game.skill_name(t.skill)
            if col == COL_XP:
                return game.xp_for_task(t, date.today())
            if col == COL_ZONE:
                return list(config.ZONE_GRID).index(t.zone)
            if col == COL_IMP:
                return t.importance
            if col == COL_DIFF:
                return t.difficulty
            if col == COL_DUE:
                # задачи без срока при сортировке по возрастанию идут в конец
                return (t.due_date or date.max).toordinal()
            if col == COL_CREATED:
                return t.created_at.timestamp()

        if role == Qt.CheckStateRole and col == COL_DONE:
            return Qt.Checked if t.done else Qt.Unchecked

        if role == Qt.TextAlignmentRole and col in (COL_IMP, COL_DIFF, COL_XP, COL_DUE, COL_CREATED):
            return int(Qt.AlignCenter)

        # Просроченные — красным, выполненные — зачёркнуты
        if role == Qt.ForegroundRole:
            if col == COL_ZONE:
                return QColor(config.ZONE_COLORS[t.zone])
            if col == COL_SKILL:
                return QColor(game.skill_color(t.skill))
            if col == COL_XP:
                return QColor("#f5b83d")
            if col == COL_DIFF:
                return QColor(game.rarity(t.difficulty)[1])
            if t.is_overdue:
                return QColor(config.OVERDUE_COLOR)
        if role == Qt.FontRole:
            font = QFont()
            if t.done and col == COL_TITLE:
                font.setStrikeOut(True)
            if (t.is_overdue and col in (COL_TITLE, COL_DUE)) or col == COL_XP:
                font.setBold(True)
            return font
        if role == Qt.ToolTipRole:
            if t.is_overdue:
                return "Квест просрочен"
            return t.description or None
        return None

    def setData(self, index, value, role=Qt.EditRole):
        # Клик по чекбоксу в первом столбце
        if role == Qt.CheckStateRole and index.column() == COL_DONE:
            done = Qt.CheckState(value) == Qt.Checked
            self.controller.set_done(self.tasks[index.row()].id, done)
            return True
        return False

    def task_at(self, row: int) -> Task:
        return self.tasks[row]


class TaskFilterProxy(QSortFilterProxyModel):
    """Фильтр по статусу и строке поиска + сортировка по Qt.UserRole."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = FILTER_ACTIVE
        self.search = ""
        self.setSortRole(Qt.UserRole)

    def set_status(self, status: str) -> None:
        self.status = status
        self.invalidateFilter()

    def set_search(self, text: str) -> None:
        self.search = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        task: Task = self.sourceModel().task_at(source_row)
        if self.status == FILTER_ACTIVE and task.done:
            return False
        if self.status == FILTER_DONE and not task.done:
            return False
        if self.search and self.search not in task.title.lower():
            return False
        return True


class TaskTableView(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller

        # --- Панель фильтров ---
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Поиск по названию…  (Ctrl+F)")
        self.search_edit.setClearButtonEnabled(True)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Активные", FILTER_ACTIVE)
        self.status_combo.addItem("Выполненные", FILTER_DONE)
        self.status_combo.addItem("Все", FILTER_ALL)

        self.count_label = QLabel()
        self.count_label.setObjectName("muted")

        bar = QHBoxLayout()
        bar.addWidget(self.search_edit, 1)
        bar.addWidget(QLabel("Показать:"))
        bar.addWidget(self.status_combo)
        bar.addWidget(self.count_label)

        # --- Таблица ---
        self.model = TaskTableModel(controller, self)
        self.proxy = TaskFilterProxy(self)
        self.proxy.setSourceModel(self.model)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)            # сортировка по клику на заголовок
        self.table.sortByColumn(COL_DUE, Qt.AscendingOrder)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_TITLE, QHeaderView.Stretch)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 14)
        lay.setSpacing(10)
        lay.addLayout(bar)
        lay.addWidget(self.table, 1)

        # --- Сигналы ---
        self.search_edit.textChanged.connect(self._on_filter_changed)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        controller.tasks_changed.connect(self.refresh)

    def _on_filter_changed(self) -> None:
        self.proxy.set_status(self.status_combo.currentData())
        self.proxy.set_search(self.search_edit.text())
        self._update_count()

    def _update_count(self) -> None:
        self.count_label.setText(f"Квестов: {self.proxy.rowCount()}")

    def _task_id_at(self, proxy_index) -> Optional[int]:
        if not proxy_index.isValid():
            return None
        src = self.proxy.mapToSource(proxy_index)
        return self.model.task_at(src.row()).id

    def _on_double_click(self, index) -> None:
        if index.column() == COL_DONE:
            return  # двойной клик по чекбоксу — не открываем редактор
        task_id = self._task_id_at(index)
        if task_id is not None:
            self.controller.edit_task(task_id)

    def _on_context_menu(self, pos) -> None:
        task_id = self._task_id_at(self.table.indexAt(pos))
        if task_id is None:
            return
        menu = QMenu(self)
        act_edit = menu.addAction("✏️  Редактировать…")
        menu.addSeparator()
        act_del = menu.addAction("🗑️  Удалить…")
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen is act_edit:
            self.controller.edit_task(task_id)
        elif chosen is act_del:
            self.controller.delete_task(task_id)

    def selected_task_id(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        return self._task_id_at(rows[0]) if rows else None

    def focus_search(self) -> None:
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def refresh(self) -> None:
        # Запоминаем выделенную задачу, чтобы восстановить выделение после обновления
        selected = self.selected_task_id()
        self.model.set_tasks(self.controller.tasks())
        self._update_count()
        if selected is not None:
            for row in range(self.proxy.rowCount()):
                if self._task_id_at(self.proxy.index(row, 0)) == selected:
                    self.table.selectRow(row)
                    break
