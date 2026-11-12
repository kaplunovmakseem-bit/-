"""
Главное окно в стиле iOS:

  ЧЕТВЕРГ, 12 НОЯБРЯ                                   (🧙)  (+)
  Квесты                                         ← крупный заголовок
  [ карточка героя: уровень, опыт, кольца активности ]
  [ содержимое вкладки ]
  ───────────────────────────────────────────────────────────────
     ▦ Квесты     ☰ Все квесты     ▮▮ Статистика     👤 Профиль   ← панель вкладок
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QAction, QColor, QFont, QKeySequence, QPainter, QPainterPath, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractButton, QApplication, QButtonGroup, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPlainTextEdit, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from .. import config, game
from ..database import Database
from . import themes
from .charts import MONTHS_GEN
from .controller import DAILY_GOAL_SETTING, TaskController
from .hud import AVATAR_SETTING, NAME_SETTING, PlayerHud
from .matrix_view import MatrixView
from .profile_view import ProfileView
from .settings_dialog import SettingsDialog
from .stats_view import StatsView
from .task_table import TaskTableView
from .toast import ToastManager

THEME_SETTING = "theme"
SHOW_DONE_SETTING = "matrix_show_done"
WEEKDAYS_FULL = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]


class TabButton(QAbstractButton):
    """Кнопка нижней панели: нарисованная иконка + подпись, выбранная — синяя."""

    def __init__(self, kind: str, text: str, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(110, 50)

    def sizeHint(self) -> QSize:
        return QSize(120, 52)

    def paintEvent(self, event):
        c = themes.colors()
        color = QColor(c["accent"] if self.isChecked() else c["muted"])
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, top = self.width() / 2, 6
        self._icon(p, QRectF(cx - 11, top, 22, 22), color)
        p.setPen(color)
        p.setFont(themes.ui_font(8, QFont.DemiBold))
        p.drawText(QRectF(0, top + 25, self.width(), 18), Qt.AlignCenter, self.text())
        p.end()

    def _icon(self, p: QPainter, r: QRectF, color: QColor) -> None:
        """Простые иконки в духе SF Symbols, нарисованные линиями и фигурами."""
        filled = self.isChecked()
        pen = QPen(color, 1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(color if filled else Qt.NoBrush)
        if self.kind == "grid":          # 4 скруглённых квадрата
            s = r.width() / 2 - 2
            for dx in (0, s + 4):
                for dy in (0, s + 4):
                    p.drawRoundedRect(QRectF(r.left() + dx, r.top() + dy, s, s), 3, 3)
        elif self.kind == "list":        # точки + строки
            for i in range(3):
                y = r.top() + 4 + i * 7
                p.drawEllipse(QPointF(r.left() + 3, y), 1.8, 1.8)
                p.drawLine(QPointF(r.left() + 8, y), QPointF(r.right(), y))
        elif self.kind == "chart":       # три столбца
            for i, h in enumerate((0.45, 0.8, 0.6)):
                w = 5
                x = r.left() + 1 + i * 7.5
                p.drawRoundedRect(QRectF(x, r.bottom() - r.height() * h, w, r.height() * h), 2, 2)
        elif self.kind == "person":      # голова + плечи
            p.drawEllipse(QPointF(r.center().x(), r.top() + 6), 5, 5)
            path = QPainterPath(QPointF(r.left() + 2, r.bottom()))
            path.cubicTo(QPointF(r.left() + 2, r.top() + 12), QPointF(r.right() - 2, r.top() + 12),
                         QPointF(r.right() - 2, r.bottom()))
            if filled:
                path.closeSubpath()
            p.drawPath(path)


class MainWindow(QMainWindow):
    PAGES = [("grid", "Квесты"), ("list", "Все квесты"), ("chart", "Статистика"), ("person", "Профиль")]

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.controller = TaskController(db, self)

        self.setWindowTitle(config.APP_TITLE)
        self.resize(1280, 860)
        self.setMinimumSize(1000, 680)

        # --- Шапка: дата, крупный заголовок, кнопки ---
        self.date_label = QLabel()
        self.date_label.setObjectName("caption")
        self.title_label = QLabel()
        self.title_label.setObjectName("largeTitle")
        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(self.date_label)
        titles.addWidget(self.title_label)

        self.profile_btn = QPushButton()
        self.profile_btn.setFixedSize(36, 36)
        self.profile_btn.setToolTip("Настройки")
        self.profile_btn.setCursor(Qt.PointingHandCursor)
        self.profile_btn.clicked.connect(self.open_settings)

        self.new_btn = QPushButton("+")
        self.new_btn.setObjectName("round")
        self.new_btn.setFixedSize(36, 36)
        self.new_btn.setToolTip("Новый квест (Ctrl+N)")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.clicked.connect(self.controller.create_task)

        head = QHBoxLayout()
        head.setContentsMargins(22, 14, 22, 6)
        head.addLayout(titles, 1)
        head.addWidget(self.profile_btn, 0, Qt.AlignBottom)
        head.addSpacing(6)
        head.addWidget(self.new_btn, 0, Qt.AlignBottom)

        self.hud = PlayerHud(self.controller, db)
        hud_row = QHBoxLayout()
        hud_row.setContentsMargins(20, 4, 20, 12)
        hud_row.addWidget(self.hud)
        self.hud_host = QWidget()
        self.hud_host.setLayout(hud_row)

        # --- Страницы ---
        self.matrix = MatrixView(self.controller)
        self.table = TaskTableView(self.controller)
        self.stats = StatsView(self.controller, db)
        self.profile = ProfileView(self.controller, db)
        self.pages = QStackedWidget()
        self.pages.setObjectName("pages")
        for w in (self.matrix, self.table, self.stats, self.profile):
            self.pages.addWidget(w)

        # --- Нижняя панель вкладок ---
        tab_bar = QFrame()
        tab_bar.setObjectName("tabBar")
        tabs_lay = QHBoxLayout(tab_bar)
        tabs_lay.setContentsMargins(0, 2, 0, 4)
        tabs_lay.addStretch(1)
        self.tab_group = QButtonGroup(self)
        for i, (kind, text) in enumerate(self.PAGES):
            b = TabButton(kind, text)
            self.tab_group.addButton(b, i)
            tabs_lay.addWidget(b)
        tabs_lay.addStretch(1)
        self.tab_group.idClicked.connect(self.set_page)

        central = QWidget()
        central.setObjectName("page")
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addLayout(head)
        lay.addWidget(self.hud_host)
        lay.addWidget(self.pages, 1)
        lay.addWidget(tab_bar)
        self.setCentralWidget(central)

        self._build_actions()

        # --- Уведомления об опыте, уровнях и достижениях ---
        self.toasts = ToastManager(central)
        self.controller.xp_gained.connect(self._on_xp)
        self.controller.xp_lost.connect(
            lambda xp: self.toasts.show("↩️", f"−{xp} XP", "Квест возвращён в работу",
                                        themes.colors()["danger"]))
        self.controller.level_up.connect(
            lambda lvl, title: self.toasts.show("🎉", f"Новый уровень — {lvl}!",
                                                f"Теперь вы: {title}", themes.colors()["gold"], big=True))
        self.controller.achievement_unlocked.connect(self._on_achievement)
        self.controller.daily_completed.connect(
            lambda xp: self.toasts.show("🎯", "Задание дня выполнено", f"Бонус +{xp} XP",
                                        themes.colors()["ring_quests"]))

        # Восстанавливаем настройку «Показывать выполненные»
        self.matrix.show_done.setChecked(db.get_setting(SHOW_DONE_SETTING, "1") == "1")
        self.matrix.show_done.toggled.connect(
            lambda v: db.set_setting(SHOW_DONE_SETTING, "1" if v else "0"))

        # Достижения, заработанные раньше, открываем молча
        self.controller.check_achievements(silent=True)
        self.set_page(0)
        self.refresh_all()

    # --- Навигация -----------------------------------------------------------
    def set_page(self, index: int) -> None:
        self.tab_group.button(index).setChecked(True)
        self.pages.setCurrentIndex(index)
        self.title_label.setText(self.PAGES[index][1])
        # Карточка героя нужна на списках квестов; в статистике и профиле она дублировала бы данные
        self.hud_host.setVisible(index in (0, 1))
        for b in self.tab_group.buttons():
            b.update()

    def refresh_all(self) -> None:
        d = date.today()
        self.date_label.setText(f"{WEEKDAYS_FULL[d.weekday()]}, {d.day} {MONTHS_GEN[d.month - 1]}".upper())
        self.profile_btn.setText(self.db.get_setting(AVATAR_SETTING, "🧙"))
        c = themes.colors()
        self.profile_btn.setStyleSheet(
            f"QPushButton {{ background: {c['fill']}; border-radius: 18px; padding: 0; font-size: 17px; }}")
        self.hud.refresh()
        self.matrix.refresh()
        self.table.refresh()
        self.stats.refresh()
        self.profile.refresh()

    # --- Уведомления ---------------------------------------------------------
    def _on_xp(self, xp: int, skill: str, label: str) -> None:
        self.toasts.show(game.skill_icon(skill), f"+{xp} XP", label, themes.skill_color(skill))

    def _on_achievement(self, key: str) -> None:
        ach = game.ACHIEVEMENTS_BY_KEY[key]
        self.toasts.show(ach.icon, f"Достижение: {ach.title}", ach.description,
                         themes.colors()["gold"], big=True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toasts"):
            self.toasts.reposition()

    # --- Горячие клавиши -----------------------------------------------------
    def _build_actions(self) -> None:
        for keys, handler in (("Ctrl+N", self.controller.create_task),
                              ("Ctrl+F", self.focus_search),
                              ("Ctrl+Q", self.close),
                              ("Ctrl+,", self.open_settings)):
            act = QAction(self)
            act.setShortcut(QKeySequence(keys))
            act.triggered.connect(handler)
            self.addAction(act)
        QShortcut(QKeySequence(QKeySequence.Delete), self, activated=self.delete_selected)
        # Ctrl+1…4 — переключение вкладок
        for i in range(len(self.PAGES)):
            QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self, activated=lambda i=i: self.set_page(i))

    def focus_search(self) -> None:
        self.set_page(1)
        self.table.focus_search()

    def delete_selected(self) -> None:
        """Delete удаляет выделенный квест на текущей вкладке."""
        # Если курсор в текстовом поле, Delete должен удалять символ, а не задачу
        if isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit)):
            return
        page = self.pages.currentWidget()
        if page is self.matrix:
            task_id = self.matrix.selected_task_id()
        elif page is self.table:
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
        # Зоны, карточки и диаграммы раскрашены индивидуально — перерисовываем
        self.matrix.restyle()
        self.table.restyle()
        self.stats.restyle()
        self.refresh_all()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
