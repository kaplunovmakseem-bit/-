"""Главное окно: вкладки, кнопки, меню и горячие клавиши."""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPlainTextEdit,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from .. import config
from ..database import Database
from . import themes
from .controller import TaskController
from .matrix_view import MatrixView
from .settings_dialog import SettingsDialog
from .task_table import TaskTableView

THEME_SETTING = "theme"
SHOW_DONE_SETTING = "matrix_show_done"


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.controller = TaskController(db, self)

        self.setWindowTitle(config.APP_TITLE)
        self.resize(1100, 720)

        # --- Верхняя панель: заголовок + кнопки ---
        title = QLabel(config.APP_TITLE)
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")

        self.new_btn = QPushButton("+ Новая задача")
        self.new_btn.setObjectName("primary")
        self.new_btn.setToolTip("Ctrl+N")
        self.new_btn.clicked.connect(self.controller.create_task)

        settings_btn = QPushButton("⚙ Настройки")
        settings_btn.clicked.connect(self.open_settings)

        top = QHBoxLayout()
        top.setContentsMargins(12, 10, 12, 0)
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(settings_btn)
        top.addWidget(self.new_btn)

        # --- Вкладки ---
        self.matrix = MatrixView(self.controller)
        self.table = TaskTableView(self.controller)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.matrix, "Матрица")
        self.tabs.addTab(self.table, "Все задачи")

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(top)
        lay.addWidget(self.tabs, 1)
        self.setCentralWidget(central)

        self._build_menu()
        self._build_shortcuts()

        # Восстанавливаем настройку «Показывать выполненные»
        self.matrix.show_done.setChecked(db.get_setting(SHOW_DONE_SETTING, "1") == "1")
        self.matrix.show_done.toggled.connect(
            lambda v: db.set_setting(SHOW_DONE_SETTING, "1" if v else "0")
        )

        # Первичная загрузка данных
        self.matrix.refresh()
        self.table.refresh()

    # --- Меню и горячие клавиши ---------------------------------------------
    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("Файл")

        act_new = QAction("Новая задача", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self.controller.create_task)
        menu.addAction(act_new)

        act_settings = QAction("Настройки…", self)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)

        menu.addSeparator()
        act_quit = QAction("Выход", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        menu.addAction(act_quit)

    def _build_shortcuts(self) -> None:
        # Ctrl+N уже задан через пункт меню. Здесь — Delete и Ctrl+F.
        QShortcut(QKeySequence(QKeySequence.Delete), self, activated=self.delete_selected)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.focus_search)

    def focus_search(self) -> None:
        self.tabs.setCurrentWidget(self.table)
        self.table.focus_search()

    def delete_selected(self) -> None:
        """Delete удаляет выделенную задачу на текущей вкладке."""
        # Если курсор в текстовом поле, Delete должен удалять символ, а не задачу
        if isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit)):
            return
        if self.tabs.currentWidget() is self.matrix:
            task_id = self.matrix.selected_task_id()
        else:
            task_id = self.table.selected_task_id()
        if task_id is not None:
            self.controller.delete_task(task_id)

    # --- Настройки ----------------------------------------------------------
    def open_settings(self) -> None:
        dlg = SettingsDialog(themes.current(), str(self.db.path), self)
        if dlg.exec() == SettingsDialog.Accepted:
            theme = dlg.selected_theme()
            self.db.set_setting(THEME_SETTING, theme)
            themes.apply_theme(QApplication.instance(), theme)
            # Карточки и зоны раскрашены индивидуально — перерисовываем их
            self.matrix.restyle()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
