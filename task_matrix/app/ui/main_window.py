"""Главное окно: игровая панель, вкладки, меню, горячие клавиши, уведомления."""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLineEdit, QMainWindow, QPlainTextEdit,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from .. import config, game
from ..database import Database
from . import themes
from .controller import DAILY_GOAL_SETTING, TaskController
from .hud import AVATAR_SETTING, NAME_SETTING, PlayerHud
from .matrix_view import MatrixView
from .profile_view import ProfileView
from .settings_dialog import SettingsDialog
from .task_table import TaskTableView
from .toast import ToastManager

THEME_SETTING = "theme"
SHOW_DONE_SETTING = "matrix_show_done"


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.controller = TaskController(db, self)

        self.setWindowTitle(config.APP_TITLE)
        self.resize(1240, 820)
        self.setMinimumSize(980, 640)

        # --- Шапка: игровая панель + кнопки ---
        self.hud = PlayerHud(self.controller, db)

        self.new_btn = QPushButton("＋  Новый квест")
        self.new_btn.setObjectName("primary")
        self.new_btn.setToolTip("Ctrl+N")
        self.new_btn.clicked.connect(self.controller.create_task)

        settings_btn = QPushButton("⚙")
        settings_btn.setToolTip("Настройки")
        settings_btn.setFixedSize(42, 40)
        settings_btn.setStyleSheet("font-size: 15pt; padding: 0;")
        settings_btn.clicked.connect(self.open_settings)

        buttons = QVBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.new_btn)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(settings_btn)
        buttons.addLayout(row)

        top = QHBoxLayout()
        top.setContentsMargins(14, 12, 14, 4)
        top.setSpacing(12)
        top.addWidget(self.hud, 1)
        top.addLayout(buttons)

        # --- Вкладки ---
        self.matrix = MatrixView(self.controller)
        self.table = TaskTableView(self.controller)
        self.profile = ProfileView(self.controller, db)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setDrawBase(False)  # без линии под вкладками
        self.tabs.addTab(self.matrix, "🗺️  Карта квестов")
        self.tabs.addTab(self.table, "📜  Все квесты")
        self.tabs.addTab(self.profile, "🧙  Персонаж")

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(top)
        lay.addWidget(self.tabs, 1)
        self.setCentralWidget(central)

        self._build_menu()
        self._build_shortcuts()

        # --- Уведомления об опыте, уровнях и достижениях ---
        self.toasts = ToastManager(central)
        self.controller.xp_gained.connect(self._on_xp)
        self.controller.xp_lost.connect(
            lambda xp: self.toasts.show("↩️", f"−{xp} XP", "Квест возвращён в работу", "#ef4f5f"))
        self.controller.level_up.connect(
            lambda lvl, title: self.toasts.show("🎉", f"НОВЫЙ УРОВЕНЬ {lvl}!",
                                                f"Звание: {title}", themes.colors()["gold"],
                                                big=True, duration_ms=4500))
        self.controller.achievement_unlocked.connect(self._on_achievement)
        self.controller.daily_completed.connect(
            lambda xp: self.toasts.show("🎯", "Задание дня выполнено!", f"Бонус +{xp} XP",
                                        "#fb923c", duration_ms=4000))

        # Восстанавливаем настройку «Показывать выполненные»
        self.matrix.show_done.setChecked(db.get_setting(SHOW_DONE_SETTING, "1") == "1")
        self.matrix.show_done.toggled.connect(
            lambda v: db.set_setting(SHOW_DONE_SETTING, "1" if v else "0")
        )

        # Достижения, заработанные в старой версии, открываем молча
        self.controller.check_achievements(silent=True)
        self.refresh_all()

    def refresh_all(self) -> None:
        self.hud.refresh()
        self.matrix.refresh()
        self.table.refresh()
        self.profile.refresh()

    # --- Уведомления ---------------------------------------------------------
    def _on_xp(self, xp: int, skill: str, label: str) -> None:
        self.toasts.show("✨", f"+{xp} XP", label, game.skill_color(skill))

    def _on_achievement(self, key: str) -> None:
        ach = game.ACHIEVEMENTS_BY_KEY[key]
        self.toasts.show(ach.icon, f"Достижение: {ach.title}", ach.description,
                         themes.colors()["gold"], big=True, duration_ms=4500)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toasts"):
            self.toasts.reposition()

    # --- Меню и горячие клавиши ---------------------------------------------
    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("Файл")

        act_new = QAction("Новый квест", self)
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
        """Delete удаляет выделенный квест на текущей вкладке."""
        # Если курсор в текстовом поле, Delete должен удалять символ, а не задачу
        if isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit)):
            return
        if self.tabs.currentWidget() is self.matrix:
            task_id = self.matrix.selected_task_id()
        elif self.tabs.currentWidget() is self.table:
            task_id = self.table.selected_task_id()
        else:
            task_id = None
        if task_id is not None:
            self.controller.delete_task(task_id)

    # --- Настройки ----------------------------------------------------------
    def open_settings(self) -> None:
        dlg = SettingsDialog(
            themes.current(),
            self.db.get_setting(NAME_SETTING, "Игрок"),
            self.db.get_setting(AVATAR_SETTING, "🧙"),
            self.controller.daily_goal(),
            str(self.db.path),
            self,
        )
        if dlg.exec() != SettingsDialog.Accepted:
            return
        self.db.set_setting(NAME_SETTING, dlg.player_name())
        self.db.set_setting(AVATAR_SETTING, dlg.avatar())
        self.db.set_setting(DAILY_GOAL_SETTING, str(dlg.daily_goal()))
        theme = dlg.selected_theme()
        self.db.set_setting(THEME_SETTING, theme)
        themes.apply_theme(QApplication.instance(), theme)
        # Зоны, карточки и профиль раскрашены индивидуально — перерисовываем
        self.matrix.restyle()
        self.refresh_all()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
