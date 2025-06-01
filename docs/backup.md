## 📦 Резервне копіювання

### 1. Бекап коду
```
tar -czf backup_code_$(date +%F).tar.gz .
```

### 2. Бекап бази PostgreSQL

**Для хмарної БД (наприклад, Aiven):**
```
pg_dump "postgresql+asyncpg://user:pass@host:port/dbname?sslmode=require" > backup.sql
```
**Для локальної:**
```
pg_dump -U postgres -d proxystore > backup.sql
```

### 3. Бекап конфігу
- Скопіюйте файл *config.py*

### 4. Перевірка бекапу
```
pg_restore -l backup.sql
```

### 5. Відновлення з бекапу
```
psql -U postgres -d proxystore < backup.sql
```