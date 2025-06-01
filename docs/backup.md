## 📦 Резервне копіювання

### 1. Бекап коду
iii
tar -czf backup_code_$(date +%F).tar.gz .
iii

### 2. Бекап бази PostgreSQL

**Для хмарної БД (наприклад, Aiven):**
iii
pg_dump "postgresql+asyncpg://user:pass@host:port/dbname?sslmode=require" > backup.sql
iii

**Для локальної:**
iii
pg_dump -U postgres -d proxystore > backup.sql
iii

### 3. Бекап конфігу
- Скопіюйте файл *config.py*

### 4. Перевірка бекапу
iii
pg_restore -l backup.sql
iii

### 5. Відновлення з бекапу
iii
psql -U postgres -d proxystore < backup.sql
iii