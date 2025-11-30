# Implementation Guide - Bot Improvements

This guide documents the implementation of the 8 major improvements to the PrimeLingo Bot.

## Overview

The improvements are being implemented in phases to ensure stability and testability.

## Phase 1: Foundation (✅ Completed)

### 1. Database Migration to PostgreSQL
- ✅ Configuration updated to support PostgreSQL
- ✅ Connection pooling implemented
- ✅ Automatic fallback to SQLite if PostgreSQL not configured
- ✅ Database URL builder with component-based configuration

**Configuration:**
```env
# For PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=bot_db
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Or use full URL
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
```

**Migration Steps:**
1. Install PostgreSQL and create database
2. Update `.env` with PostgreSQL credentials
3. Run migrations: `alembic upgrade head`
4. Data migration from SQLite (if needed)

### 2. Redis Integration
- ✅ Redis client for FSM storage
- ✅ Redis connection for task queue
- ✅ Automatic fallback to MemoryStorage if Redis unavailable

**Configuration:**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional
REDIS_URL=redis://localhost:6379/0  # Or use full URL
```

### 3. Task Queue Infrastructure
- ✅ RQ (Redis Queue) integration
- ✅ Task enqueueing utilities
- ✅ Job status tracking

**Dependencies Added:**
- `redis==5.0.1`
- `hiredis==2.2.3`
- `rq==1.15.1`
- `aioredis==2.0.1`

### 4. Retry & Timeout Utilities
- ✅ Exponential backoff retry logic
- ✅ Async timeout decorators
- ✅ Configurable retry attempts and backoff

### 5. Monitoring Infrastructure
- ✅ Metrics collector
- ✅ Error tracking context manager
- ✅ Execution time logging

## Phase 2: Core Improvements (In Progress)

### 6. FSM Persistence
- ✅ Redis storage integration
- ✅ Automatic upgrade on startup
- ⏳ Testing and validation needed

### 7. Background File Processing
- ✅ Task functions created
- ⏳ Upload handler integration
- ⏳ Worker process setup

### 8. Broadcast Optimization
- ⏳ Parallel batch processing
- ⏳ Rate limit awareness
- ⏳ Improved error handling

## Phase 3: Advanced Features (Pending)

### 9. Timeout Implementation
- ⏳ Request timeouts for all async operations
- ⏳ File download timeouts
- ⏳ Database query timeouts

### 10. Search & Statistics Optimization
- ⏳ Query optimization
- ⏳ Indexing improvements
- ⏳ Caching layer

### 11. Large File Handling
- ⏳ Streaming support
- ⏳ Memory optimization
- ⏳ Concurrent upload limits

### 12. Monitoring Dashboard
- ⏳ Metrics API endpoint
- ⏳ Health check integration
- ⏳ Alerting system

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup PostgreSQL (Optional)
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb bot_db
sudo -u postgres createuser bot_user

# Update .env
POSTGRES_HOST=localhost
POSTGRES_USER=bot_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=bot_db
```

### 3. Setup Redis
```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis

# Update .env (optional, defaults work)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Run Database Migrations
```bash
# If using Alembic
alembic upgrade head

# Or let the bot create tables on startup
python main.py
```

### 5. Start RQ Worker (for background tasks)
```bash
# In a separate terminal
rq worker --url redis://localhost:6379/0 default
```

### 6. Start Bot
```bash
python main.py
```

## Testing

### Test PostgreSQL Connection
```python
from app.core.database import get_database_url
print(get_database_url())
```

### Test Redis Connection
```python
from app.core.redis_client import get_redis_client
import asyncio
asyncio.run(get_redis_client())
```

### Test Task Queue
```python
from app.core.tasks import enqueue_task
from app.tasks.file_processing import process_file_sync
job = enqueue_task(process_file_sync, file_id=1, file_telegram_id="...", file_name="test.pdf", title="Test")
print(f"Job ID: {job.id}")
```

## Configuration Reference

All new settings are in `app/core/config.py`:

- **Database**: `POSTGRES_*` settings
- **Redis**: `REDIS_*` settings
- **Task Queue**: `RQ_*` settings
- **Timeouts**: `REQUEST_TIMEOUT`, `FILE_DOWNLOAD_TIMEOUT`
- **Retries**: `MAX_RETRIES`, `RETRY_BACKOFF_BASE`
- **Broadcast**: `BROADCAST_BATCH_SIZE`, `BROADCAST_DELAY`

## Next Steps

1. Complete upload handler integration with background tasks
2. Implement parallel broadcast processing
3. Add timeouts to all async operations
4. Optimize search queries with proper indexing
5. Implement monitoring dashboard
6. Add comprehensive error tracking

## Notes

- All improvements are backward compatible
- SQLite remains the default if PostgreSQL not configured
- MemoryStorage used if Redis unavailable
- Tasks can run synchronously if RQ not available (with warning)

