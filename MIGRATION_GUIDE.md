# Database Migration Guide: SQLite to PostgreSQL

This guide will help you migrate your bot's database from SQLite to PostgreSQL for better performance, concurrency, and scalability.

## Prerequisites

1. **PostgreSQL installed and running**
   - Download from: https://www.postgresql.org/download/
   - Or use Docker: `docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres`

2. **Python packages installed**
   ```bash
   pip install -r requirements.txt
   ```

## Step 1: Install PostgreSQL

### Windows
1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
2. Run installer and follow instructions
3. Remember the password you set for the `postgres` user

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Docker (All Platforms)
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=bot_db \
  -p 5432:5432 \
  postgres:latest
```

## Step 2: Create PostgreSQL Database

### Using psql (Command Line)
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE bot_db;
CREATE USER bot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bot_db TO bot_user;

# Exit psql
\q
```

### Using pgAdmin (GUI)
1. Open pgAdmin
2. Right-click on "Databases" → "Create" → "Database"
3. Name: `bot_db`
4. Click "Save"

## Step 3: Configure Environment Variables

Update your `.env` file with PostgreSQL credentials:

```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=bot_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=bot_db

# Connection Pooling (optional, defaults shown)
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# OR use full DATABASE_URL (overrides above)
# DATABASE_URL=postgresql+asyncpg://bot_user:your_password@localhost:5432/bot_db
```

## Step 4: Backup SQLite Database

**IMPORTANT**: Always backup before migration!

```bash
# Copy the SQLite database
cp bot.db bot.db.backup

# Or on Windows
copy bot.db bot.db.backup
```

## Step 5: Run Migration Script

The migration script will:
1. Connect to both SQLite and PostgreSQL
2. Create all tables in PostgreSQL
3. Copy all data from SQLite to PostgreSQL
4. Preserve all relationships and foreign keys

```bash
python migrate_to_postgresql.py
```

### Expected Output
```
============================================================
SQLite to PostgreSQL Migration
============================================================
✅ PostgreSQL connection successful
✅ SQLite database found

Creating PostgreSQL tables...
✅ PostgreSQL tables created

============================================================
Starting data migration...
============================================================

Migrating 150 records from users...
✅ Migrated 150/150 records from users

Migrating 45 records from files...
✅ Migrated 45/45 records from files

Migrating 320 records from downloads...
✅ Migrated 320/320 records from downloads

Migrating 12 records from saved_list...
✅ Migrated 12/12 records from saved_list

Migrating 5 settings...
✅ Migrated 5 settings

============================================================
✅ Migration completed! Total records migrated: 532
============================================================
```

## Step 6: Verify Migration

### Check PostgreSQL Data
```bash
# Connect to PostgreSQL
psql -U bot_user -d bot_db

# Check table counts
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'files', COUNT(*) FROM files
UNION ALL
SELECT 'downloads', COUNT(*) FROM downloads;

# Exit
\q
```

### Test Bot with PostgreSQL
```bash
# Start the bot
python main.py

# Check logs for:
# "Using PostgreSQL database: localhost:5432/bot_db"
```

## Step 7: Update Bot Configuration

The bot will automatically detect PostgreSQL if configured. Verify in logs:

```
INFO: Using PostgreSQL database: localhost:5432/bot_db
INFO: Database initialized successfully
```

## Troubleshooting

### Connection Errors

**Error: "connection refused"**
- Check PostgreSQL is running: `sudo systemctl status postgresql` (Linux) or check Services (Windows)
- Verify host/port in `.env`

**Error: "authentication failed"**
- Check username/password in `.env`
- Verify user has permissions: `GRANT ALL PRIVILEGES ON DATABASE bot_db TO bot_user;`

**Error: "database does not exist"**
- Create database: `CREATE DATABASE bot_db;`

### Migration Errors

**Error: "table already exists"**
- Drop existing tables: `DROP TABLE IF EXISTS users, files, downloads, saved_list, settings CASCADE;`
- Or use a fresh database

**Error: "foreign key constraint fails"**
- Migration script handles this by migrating in order
- If issues persist, check data integrity in SQLite first

### Performance Issues

**Slow queries after migration**
- Add indexes (see below)
- Check connection pooling settings
- Monitor PostgreSQL logs

## Post-Migration Optimization

### Add Indexes for Better Performance

```sql
-- Connect to PostgreSQL
psql -U bot_user -d bot_db

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
CREATE INDEX IF NOT EXISTS idx_files_title ON files(title);
CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_downloads_file_id ON downloads(file_id);
CREATE INDEX IF NOT EXISTS idx_downloads_downloaded_at ON downloads(downloaded_at);
CREATE INDEX IF NOT EXISTS idx_saved_list_user_id ON saved_list(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_list_file_id ON saved_list(file_id);

-- Analyze tables for query optimization
ANALYZE users;
ANALYZE files;
ANALYZE downloads;
ANALYZE saved_list;
```

### Connection Pooling

The bot automatically uses connection pooling:
- **Pool Size**: 10 connections (configurable via `POSTGRES_POOL_SIZE`)
- **Max Overflow**: 20 additional connections (configurable via `POSTGRES_MAX_OVERFLOW`)
- **Connection Health**: Automatic ping before use (`pool_pre_ping=True`)
- **Connection Recycling**: Connections recycled after 1 hour

## Rollback Plan

If you need to rollback to SQLite:

1. **Stop the bot**
2. **Update `.env`**:
   ```env
   # Comment out PostgreSQL settings
   # POSTGRES_HOST=localhost
   
   # Use SQLite
   DATABASE_URL=sqlite+aiosqlite:///./bot.db
   ```
3. **Restore backup** (if needed):
   ```bash
   cp bot.db.backup bot.db
   ```
4. **Restart bot**

## Benefits of PostgreSQL

✅ **Better Concurrency**: Handles multiple simultaneous connections  
✅ **ACID Compliance**: Better data integrity  
✅ **Advanced Features**: Full-text search, JSON support, etc.  
✅ **Scalability**: Can handle much larger datasets  
✅ **Replication**: Can set up read replicas for scaling  
✅ **Performance**: Better query optimizer than SQLite  

## Monitoring

### Check Connection Pool Status
```python
from app.core.database import engine
print(f"Pool size: {engine.pool.size()}")
print(f"Checked out: {engine.pool.checkedout()}")
```

### Monitor Database Performance
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size('bot_db'));

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Next Steps

After successful migration:
1. ✅ Monitor bot performance
2. ✅ Verify all features work correctly
3. ✅ Keep SQLite backup for 1-2 weeks
4. ✅ Consider setting up PostgreSQL backups
5. ✅ Update documentation with PostgreSQL setup

---

**Need Help?** Check the logs or review `BOT_ARCHITECTURE.md` for more details.

