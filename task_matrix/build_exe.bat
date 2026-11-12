@echo off
rem Сборка приложения в один .exe файл. Результат: dist\TaskMatrix.exe
chcp 65001 >nul
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed --name TaskMatrix main.py
echo.
echo Готово! Файл: dist\TaskMatrix.exe
pause
