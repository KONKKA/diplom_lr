#!/bin/bash

PROJECT_DIR="diplom_lr"
VENV_DIR="venv"
REPO_URL="https://github.com/KONKKA/diplom_lr.git"

echo "Оновлення проєкту..."

if [ ! -d "$PROJECT_DIR" ]; then
  echo "Проєкт не знайдено. Клонуйте спочатку репозиторій."
  exit 1
fi

cd "$PROJECT_DIR" || exit

echo "Отримання останніх змін з репозиторію..."
git pull origin main || git pull

if [ ! -d "$VENV_DIR" ]; then
  echo "Створення нового віртуального середовища..."
  python3 -m venv "$VENV_DIR"
fi

echo "Активація середовища..."
source "$VENV_DIR/bin/activate"

echo "⬇Оновлення залежностей..."
pip install --upgrade pip
pip install -r requirements.txt --upgrade

echo "Не забудьте перезапустити додаток вручну або через систему менеджменту процесів."

