#!/bin/bash
cd ../../

echo "Перевірка і створення віртуального середовища..."

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate

echo "Оновлення залежностей..."
pip install -r requirements.txt --upgrade

echo "Запуск додатку..."
python run.py
