## 🚀 Розгортання у Production

### 1. Підготуйте сервер
- Встановіть:
  - Python 3.11+
  - Git
  - PostgreSQL (або використовуйте хмарний інстанс)
  - pip, venv

### Клонування репозиторію
```
git clone https://github.com/KONKKA/diplom_lr.git
cd diplom_lr/proxystorebot
```

### Створіть та активуйте віртуальне середовище
```
python -m venv venv
venv\Scripts\activate  # Windows
# або
source venv/bin/activate  # Linux/macOS
```

### Встановіть залежності
```
pip install -r requirements.txt
```

### Налаштуйте config.py
   - Скопіюйте config.example → config.py
   - Заповніть значення:
     - TELEGRAM_BOT_TOKEN
     - ADMIN_ID
     - DATABASE_URL  
       Формат:
       postgresql+asyncpg://user:password@host:port/dbname?ssl=require

### Створіть базу даних
   - Створіть порожню базу в PostgreSQL.
   - Таблиці створяться автоматично при першому запуску.

### Запуск програми
```
python run.py
```
### Перевірка роботи програми
- Знайдіть бота в Telegram
- Введіть команду */start*