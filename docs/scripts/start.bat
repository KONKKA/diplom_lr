@echo off
cd ../..

echo Перевірка і створення віртуального середовища...

if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate

echo Оновлення залежностей...
pip install -r requirements.txt --upgrade

echo Запуск додатку...
python run.py

pause