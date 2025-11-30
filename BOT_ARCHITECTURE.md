# PrimeLingo Bot - Architecture & Operations Documentation

## Table of Contents
1. [File Upload, Storage, and Serving](#1-file-upload-storage-and-serving)
2. [Update Handling & Async Operations](#2-update-handling--async-operations)
3. [Multi-User Processing & Broadcasts](#3-multi-user-processing--broadcasts)
4. [Error Handling, Retries, Logging, and Timeouts](#4-error-handling-retries-logging-and-timeouts)
5. [Large File Management & Stability](#5-large-file-management--stability)
6. [Limitations & Bottlenecks](#6-limitations--bottlenecks)
7. [Performance, Reliability & Scalability](#7-performance-reliability--scalability)

---

## 1. File Upload, Storage, and Serving

### 1.1 File Upload Process

**Upload Flow:**
1. Admin sends `/upload` command
2. Bot enters FSM (Finite State Machine) state: `waiting_for_file`
3. Admin sends file (document, audio, or video)
4. Bot extracts `file_id` from Telegram message
5. Bot enters state: `waiting_for_title`
6. Admin provides title (auto-appends " - PrimeLingoBot")
7. Bot enters state: `waiting_for_tags`
8. Admin provides tags (or `/skip`)

### 1.2 File Processing & Storage

**Pre-processing During Upload:**
- When a file is uploaded, the bot attempts to pre-process it:
  1. Downloads the original file from Telegram using `file_id`
  2. Downloads the default thumbnail (if configured)
  3. Renames file to include " - PrimeLingoBot" suffix
  4. Re-uploads the file with thumbnail attached
  5. Stores the new `processed_file_id` in the database

**Database Storage:**
- **File Model** (`app/models/base.py`):
  - `file_id`: Original Telegram `file_id` (unique, required)
  - `processed_file_id`: Pre-processed file with thumbnail and renamed (nullable)
  - `file_name`: Original filename
  - `title`: Display title (indexed for search)
  - `type`: Content type (document, audio, video)
  - `thumbnail_id`: Individual file thumbnail (currently unused, defaults used)
  - `tags`: Comma-separated tags for search
  - `downloads_count`: Counter for popularity

**Key Points:**
- Files are **NOT stored locally** - only `file_id` references are stored
- Telegram handles actual file storage
- `file_id` is a unique identifier that allows direct file access without re-uploading

### 1.3 File Serving (Download)

**Download Flow:**
1. User clicks "yuklab olish" (download) button
2. Bot checks if `processed_file_id` exists:
   - **If exists**: Sends pre-processed file instantly (no processing needed)
   - **If missing**: Falls back to on-the-fly processing:
     - Downloads original file
     - Downloads default thumbnail
     - Renames and re-uploads
     - Sends to user
3. Records download in database
4. Increments download counter
5. Deletes "downloading" message and button message

**Performance Optimization:**
- Pre-processed files (`processed_file_id`) are sent **instantly** - no download/re-upload needed
- Only files without `processed_file_id` require on-the-fly processing
- Thumbnails are only applied to files ≤20MB (Telegram limitation)

### 1.4 Thumbnails & Previews

**Thumbnail System:**
- **Default Thumbnail**: Set via `/set_thumb` command, stored in settings
- **File-Specific Thumbnails**: Currently not used (all files use default)
- **Size Limit**: Thumbnails only applied to files ≤20MB
- **Processing**: Thumbnails are attached during pre-processing or on-the-fly

**Preview Generation:**
- Telegram automatically generates previews for PDFs and images
- Bot doesn't generate custom previews - relies on Telegram's built-in preview system

---

## 2. Update Handling & Async Operations

### 2.1 Update Method: Long Polling

**Current Implementation:**
- Uses **Long Polling** (not webhooks)
- Implemented via `dp.start_polling()` in `app/bot/main.py`
- Configuration: `handle_signals=False` (parent process handles signals)

**Code Location:**
```python
# cloud-bot/main.py:35
await dp.start_polling(
    bot, 
    allowed_updates=dp.resolve_used_updates(),
    handle_signals=False
)
```

**Why Long Polling:**
- Simpler setup (no webhook URL/SSL required)
- Better for development/testing
- Works behind firewalls/NAT
- No need for public IP/domain

**Webhook Support:**
- Configuration exists (`WEBHOOK_URL`, `WEBHOOK_PATH`) but not implemented
- Can be added by replacing `start_polling()` with `set_webhook()`

### 2.2 Async Architecture

**Framework:**
- Built on **aiogram 3.x** (async-first Telegram Bot framework)
- Uses Python's `asyncio` for concurrent operations
- SQLAlchemy with `aiosqlite` for async database operations

**Concurrent Tasks:**
- Bot polling runs in one async task
- FastAPI admin panel runs in another async task
- Both tasks run concurrently via `asyncio.gather()`

**Code:**
```python
# cloud-bot/main.py:106-108
bot_task = asyncio.create_task(run_bot(), name="bot")
api_task = asyncio.create_task(run_api(), name="api")
tasks = [bot_task, api_task]
```

### 2.3 Background Tasks

**Current Implementation:**
- **No dedicated background task queue** (e.g., Celery, RQ)
- All operations are request-response based
- File processing happens synchronously during upload/download

**Potential Improvements:**
- Large file processing could be moved to background tasks
- Broadcast operations could use task queues for better rate limit handling

---

## 3. Multi-User Processing & Broadcasts

### 3.1 Request Handling

**Middleware Stack:**
1. **UserCheckMiddleware**: Creates/retrieves user, checks if blocked
2. **LanguageMiddleware**: Determines user language preference
3. **FSubCheckMiddleware**: Enforces force channel subscription
4. **AdminCheckMiddleware**: Validates admin permissions (for admin commands)

**Concurrency:**
- Each update is processed independently
- No shared state between requests (except database)
- FSM state stored in memory (`MemoryStorage`)

### 3.2 Broadcast Implementation

**Broadcast Flow:**
1. Admin sends `/broadcast <message>`
2. Bot fetches all non-blocked users from database
3. Iterates through users sequentially
4. Sends message to each user with error handling
5. Tracks success/failure counts
6. Updates status message with results

**Code Location:** `cloud-bot/app/bot/handlers/admin/broadcast.py`

**Rate Limiting:**
- **Current**: 50ms delay between messages (`await asyncio.sleep(0.05)`)
- **Limitation**: Sequential processing (one user at a time)
- **Telegram Limits**: ~30 messages/second per bot

**Error Handling:**
- `TelegramForbiddenError`: User blocked bot → counted, skipped
- `TelegramBadRequest`: Invalid chat → counted, skipped
- `TelegramAPIError`: Other API errors → logged, counted
- All errors are caught and logged, broadcast continues

**Performance:**
- For 1000 users: ~50 seconds (50ms × 1000)
- For 10,000 users: ~8.3 minutes
- **Bottleneck**: Sequential processing, no batching

---

## 4. Error Handling, Retries, Logging, and Timeouts

### 4.1 Error Handling Strategy

**Error Types Handled:**
1. **Telegram API Errors**:
   - `TelegramBadRequest`: Invalid requests, HTML parsing errors
   - `TelegramForbiddenError`: User blocked bot
   - `TelegramAPIError`: General API errors

2. **Database Errors**:
   - `IntegrityError`: Duplicate file_id (caught during upload)
   - Connection errors (handled by SQLAlchemy)

3. **File Processing Errors**:
   - Download failures → fallback to original file
   - Upload failures → log error, continue without processing

**Error Handling Pattern:**
```python
try:
    # Operation
except SpecificError as e:
    # Handle specific error
    logger.warning(f"Specific error: {e}")
    # Fallback action
except Exception as e:
    # Catch-all for unexpected errors
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

### 4.2 Retry Logic

**Current Implementation:**
- **No automatic retries** for failed operations
- Manual retry: User can click button again
- Broadcast: Failed users are skipped, no retry

**Retry Opportunities:**
- File download failures → fallback to original file (one retry attempt)
- Broadcast failures → logged but not retried

### 4.3 Logging

**Logging Configuration:**
- Uses Python's `logging` module
- Level: `INFO` (configurable via `DEBUG` setting)
- Loggers: Module-specific (`logger = logging.getLogger(__name__)`)

**Log Locations:**
- Console output (stdout)
- No file logging configured
- No log rotation

**Log Levels Used:**
- `logger.info()`: Normal operations, startup/shutdown
- `logger.warning()`: Recoverable errors, rate limits
- `logger.error()`: Critical errors with stack traces
- `logger.debug()`: Detailed debugging (rarely used)

### 4.4 Timeouts

**Current Timeouts:**
- **Shutdown timeout**: 10 seconds (`cloud-bot/main.py:88-90`)
- **No request timeouts**: Operations can hang indefinitely
- **No database query timeouts**: SQLAlchemy default (usually 30s)

**Potential Issues:**
- File downloads can hang if Telegram is slow
- Broadcast operations have no timeout (could hang on slow network)

**Health Check System:**
- `HealthCheck` model exists for error tracking
- `log_health_check()` function available
- **Not actively used** - needs middleware integration

---

## 5. Large File Management & Stability

### 5.1 File Size Handling

**Telegram Limits:**
- Maximum file size: **2GB** (Telegram Bot API limit)
- Thumbnail limit: Only files ≤20MB get thumbnails
- No chunking/streaming implemented

**Current Implementation:**
- Files are downloaded entirely to memory/temp files
- No streaming or chunked uploads
- Large files may cause memory issues

**Code:**
```python
# cloud-bot/app/bot/handlers/admin/upload.py:128
await _bot_instance.download_file(doc_file.file_path, doc_path)
```

### 5.2 Memory Management

**Temporary Files:**
- Created during file processing
- Stored in system temp directory
- Cleaned up after processing (with error handling)

**Memory Storage:**
- FSM state stored in memory (`MemoryStorage`)
- **Limitation**: State lost on restart
- No persistence for FSM states

**Database:**
- SQLite with async operations
- Connection pooling via `AsyncSessionLocal`
- No explicit connection limits

### 5.3 Stability Measures

**Graceful Shutdown:**
- Signal handlers for SIGINT/SIGTERM
- 10-second timeout for task cancellation
- Cleanup of temp files and database connections

**Error Recovery:**
- Fallback mechanisms for file processing
- Database transactions for data integrity
- User-friendly error messages

**Concurrency Safety:**
- Each request handled independently
- Database sessions are request-scoped
- No shared mutable state

---

## 6. Limitations & Bottlenecks

### 6.1 Identified Limitations

1. **Sequential Broadcast Processing**
   - **Issue**: Broadcasts process users one-by-one
   - **Impact**: Slow for large user bases (8+ minutes for 10k users)
   - **Solution**: Implement batching or async batch processing

2. **No Request Timeouts**
   - **Issue**: Operations can hang indefinitely
   - **Impact**: Bot may become unresponsive
   - **Solution**: Add timeouts to all async operations

3. **Memory-Based FSM Storage**
   - **Issue**: State lost on restart
   - **Impact**: Users lose progress in multi-step operations
   - **Solution**: Use Redis or database-backed storage

4. **No Retry Logic**
   - **Issue**: Failed operations not automatically retried
   - **Impact**: Manual intervention required
   - **Solution**: Implement exponential backoff retries

5. **File Processing Blocking**
   - **Issue**: Large file processing blocks request handling
   - **Impact**: Slow response times during uploads
   - **Solution**: Move to background task queue

6. **SQLite Database**
   - **Issue**: Single-file database, no replication
   - **Impact**: Potential bottleneck under high load
   - **Solution**: Migrate to PostgreSQL for production

7. **No Rate Limit Handling**
   - **Issue**: Broadcast uses fixed 50ms delay
   - **Impact**: May still hit Telegram rate limits
   - **Solution**: Implement dynamic rate limiting with backoff

8. **Health Check Not Integrated**
   - **Issue**: Health check model exists but not used
   - **Impact**: No error tracking/monitoring
   - **Solution**: Add error logging middleware

### 6.2 Scalability Bottlenecks

1. **Database Connection Pool**
   - Current: Single SQLite connection
   - Limit: ~1000 concurrent operations
   - Solution: Connection pooling, read replicas

2. **File Processing**
   - Current: Synchronous, blocks request
   - Limit: One file at a time per bot instance
   - Solution: Background workers, multiple instances

3. **Broadcast Operations**
   - Current: Sequential, single-threaded
   - Limit: ~20 messages/second (with 50ms delay)
   - Solution: Parallel processing with rate limit awareness

4. **Memory Usage**
   - Current: All files downloaded to temp storage
   - Limit: Server RAM capacity
   - Solution: Streaming, chunked processing

---

## 7. Performance, Reliability & Scalability

### 7.1 Performance Characteristics

**Response Times:**
- Pre-processed file download: **<1 second** (instant)
- On-the-fly processing: **5-30 seconds** (depends on file size)
- Search queries: **<500ms** (SQLite indexed queries)
- Broadcast per user: **~50ms** (with delay)

**Throughput:**
- Concurrent users: Limited by SQLite (~100-1000)
- File downloads: ~1 per second (sequential processing)
- Broadcasts: ~20 messages/second

### 7.2 Reliability Features

**Data Integrity:**
- Database transactions for critical operations
- Unique constraints prevent duplicate files
- Foreign key relationships maintain referential integrity

**Error Recovery:**
- Fallback mechanisms for file processing
- Graceful degradation (send original file if processing fails)
- User-friendly error messages

**State Management:**
- FSM for multi-step operations (upload, search)
- State cleared on completion or cancellation
- No state persistence (lost on restart)

### 7.3 Scalability Considerations

**Horizontal Scaling:**
- **Current**: Single bot instance
- **Challenge**: FSM state in memory (not shareable)
- **Solution**: Use Redis for shared state storage

**Database Scaling:**
- **Current**: SQLite (single file)
- **Limitation**: Write contention, no replication
- **Solution**: PostgreSQL with read replicas

**File Processing Scaling:**
- **Current**: Synchronous processing
- **Solution**: Background task queue (Celery, RQ)
- **Benefit**: Multiple workers can process files in parallel

**Load Distribution:**
- **Current**: All requests to single instance
- **Solution**: Multiple bot instances with shared database
- **Requirement**: Redis for FSM state, message deduplication

### 7.4 Monitoring & Observability

**Current State:**
- Basic logging to console
- No metrics collection
- No alerting system
- Health check model exists but unused

**Recommended Additions:**
1. **Error Tracking**: Integrate health check logging
2. **Metrics**: Request counts, response times, error rates
3. **Alerting**: Notify on high error rates or downtime
4. **Dashboard**: Real-time monitoring of bot health

### 7.5 Security Considerations

**Current Security:**
- Admin authentication via JWT tokens
- Password hashing (bcrypt)
- Role-based permissions system
- Force subscribe channel validation

**Potential Improvements:**
1. Rate limiting per user (prevent abuse)
2. Input validation and sanitization
3. SQL injection prevention (SQLAlchemy handles this)
4. File type validation (currently accepts any file type)

---

## Summary

### Strengths
✅ Pre-processed files enable instant downloads  
✅ Async architecture supports concurrent operations  
✅ Graceful error handling with fallbacks  
✅ Role-based admin permissions  
✅ Multi-language support  

### Areas for Improvement
⚠️ Sequential broadcast processing (slow for large user bases)  
⚠️ No request timeouts (operations can hang)  
⚠️ Memory-based FSM storage (state lost on restart)  
⚠️ No automatic retry logic  
⚠️ SQLite database (not ideal for production scale)  
⚠️ No health check integration  
⚠️ No metrics/monitoring  

### Recommended Next Steps
1. Implement Redis for FSM state persistence
2. Add request timeouts to all async operations
3. Implement background task queue for file processing
4. Add health check middleware for error tracking
5. Migrate to PostgreSQL for production
6. Implement parallel broadcast processing with rate limiting
7. Add metrics collection and monitoring dashboard

