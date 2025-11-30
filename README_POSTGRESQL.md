# PostgreSQL Migration Quick Start

## Quick Migration Steps

1. **Install PostgreSQL** (if not already installed)
   ```bash
   # Windows: Download from https://www.postgresql.org/download/windows/
   # Linux: sudo apt-get install postgresql
   # macOS: brew install postgresql
   # Docker: docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres
   ```

2. **Create Database**
   ```bash
   psql -U postgres
   CREATE DATABASE bot_db;
   CREATE USER bot_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE bot_db TO bot_user;
   \q
   ```

3. **Update .env**
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=bot_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=bot_db
   ```

4. **Backup SQLite Database**
   ```bash
   cp bot.db bot.db.backup
   ```

5. **Run Migration**
   ```bash
   python migrate_to_postgresql.py
   ```

6. **Start Bot**
   ```bash
   python main.py
   ```

The bot will automatically detect and use PostgreSQL!

## Verification

Check logs for:
```
INFO: Using PostgreSQL database: localhost:5432/bot_db
INFO: Database initialized successfully
```

## Rollback

If needed, revert to SQLite:
1. Comment out PostgreSQL settings in `.env`
2. Restore backup: `cp bot.db.backup bot.db`
3. Restart bot

For detailed instructions, see `MIGRATION_GUIDE.md`

