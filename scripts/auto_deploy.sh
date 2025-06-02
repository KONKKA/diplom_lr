#!/bin/bash

REPO_URL="https://github.com/KONKKA/diplom_lr.git"
PROJECT_DIR="diplom_lr"
VENV_DIR="venv"

echo "Клонування репозиторію..."
git clone "$REPO_URL"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "Не знайдено директорії $PROJECT_DIR"
  exit 1
fi

cd "$PROJECT_DIR" || exit

echo "Створення віртуального середовища..."
python3 -m venv "$VENV_DIR"

echo "Активація середовища..."
source "$VENV_DIR/bin/activate"

echo "⬇Встановлення залежностей..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Запуск додатку..."
python run.py
