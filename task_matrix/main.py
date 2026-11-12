"""
Точка входа в приложение «Матрица задач».

Запуск:  python main.py
"""

import sys

from PySide6.QtCore import QLocale, QLibraryInfo, QTranslator
from PySide6.QtWidgets import QApplication

from app import config
from app.database import Database
from app.ui import themes
from app.ui.main_window import MainWindow, THEME_SETTING


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_TITLE)
    app.setStyle("Fusion")  # одинаковый вид на всех системах, хорошо дружит с тёмной темой

    # Русская локаль: названия месяцев и дней недели в календаре
    QLocale.setDefault(QLocale(QLocale.Russian, QLocale.Russia))
    # Перевод стандартных строк Qt (кнопки диалогов, меню полей ввода) на русский
    translator = QTranslator(app)
    if translator.load(QLocale(QLocale.Russian), "qtbase", "_",
                       QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)

    db = Database(config.db_path())
    themes.apply_theme(app, db.get_setting(THEME_SETTING, themes.DARK))

    window = MainWindow(db)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
