# Long Polling Optimization Guide

## Overview

This document explains the optimized long polling configuration implemented to prevent timeout errors and improve bot stability.

## Configuration Parameters

### Polling Settings

```python
POLLING_TIMEOUT: int = 20  # Seconds to wait for updates
POLLING_LIMIT: int = 100   # Max updates per request (1-100)
POLLING_CLOSE_TIMEOUT: int = 10  # Graceful shutdown timeout
```

**Why These Settings Help:**

1. **POLLING_TIMEOUT = 20 seconds**
   - **Default**: 0 (returns immediately if no updates)
   - **Our Setting**: 20 seconds
   - **Benefit**: Reduces number of requests to Telegram API
   - **Prevents**: Rate limiting and connection overhead
   - **Trade-off**: Slight delay in receiving updates (acceptable for most bots)

2. **POLLING_LIMIT = 100**
   - **Default**: 100 (maximum allowed)
   - **Benefit**: Gets maximum updates per request, reducing API calls
   - **Prevents**: Missing updates during high traffic

3. **POLLING_CLOSE_TIMEOUT = 10 seconds**
   - **Benefit**: Allows graceful shutdown, prevents data loss
   - **Prevents**: Abrupt disconnections during shutdown

### API Request Settings

```python
API_REQUEST_TIMEOUT: int = 30    # Total request timeout
API_CONNECT_TIMEOUT: int = 10    # Connection establishment timeout
API_READ_TIMEOUT: int = 30       # Data reading timeout
```

**Why These Settings Help:**

1. **API_REQUEST_TIMEOUT = 30 seconds**
   - **Purpose**: Maximum time for entire request (connect + read + process)
   - **Prevents**: Requests hanging indefinitely
   - **Benefit**: Fails fast, allows retry

2. **API_CONNECT_TIMEOUT = 10 seconds**
   - **Purpose**: Time to establish TCP connection
   - **Prevents**: Hanging on slow networks
   - **Benefit**: Quick failure detection

3. **API_READ_TIMEOUT = 30 seconds**
   - **Purpose**: Time to read response data
   - **Prevents**: Hanging on slow responses
   - **Benefit**: Handles network congestion gracefully

### Connection Pool Settings

```python
limit=100              # Total connection pool size
limit_per_host=30      # Connections to Telegram API
ttl_dns_cache=300      # DNS cache for 5 minutes
keepalive_timeout=30   # Keep connections alive
```

**Why These Settings Help:**

1. **Connection Pooling**
   - **Benefit**: Reuses connections, reduces overhead
   - **Prevents**: Connection establishment delays
   - **Improves**: Response time for subsequent requests

2. **DNS Caching (5 minutes)**
   - **Benefit**: Faster connection establishment
   - **Prevents**: DNS lookup delays
   - **Improves**: Overall request speed

3. **Keep-Alive (30 seconds)**
   - **Benefit**: Maintains connections between requests
   - **Prevents**: Connection overhead on each request
   - **Improves**: Throughput and reduces latency

### Reconnection Settings

```python
POLLING_RECONNECT_DELAY: float = 5.0        # Initial reconnect delay
POLLING_MAX_RECONNECT_DELAY: float = 60.0   # Maximum delay
POLLING_BACKOFF_MULTIPLIER: float = 2.0     # Exponential backoff
```

**Why These Settings Help:**

1. **Exponential Backoff**
   - **Initial**: 5 seconds
   - **After 1st failure**: 10 seconds
   - **After 2nd failure**: 20 seconds
   - **After 3rd failure**: 40 seconds
   - **Maximum**: 60 seconds
   - **Benefit**: Prevents overwhelming server during outages
   - **Prevents**: Rapid reconnection attempts that fail

2. **Automatic Reconnection**
   - **Network Errors**: Retry with backoff
   - **Server Errors**: Retry with shorter delay (usually temporary)
   - **Benefit**: Bot recovers automatically from transient failures

## Error Handling

### Network Errors (TelegramNetworkError)

**Handled By:**
- Automatic reconnection with exponential backoff
- Logging for monitoring
- No user impact (transparent recovery)

**Example:**
```
WARNING: Network error during polling: Request timeout. 
         Reconnecting in 5.0s...
```

### Server Errors (TelegramServerError)

**Handled By:**
- Immediate retry with shorter delay
- Reset backoff (server errors are usually temporary)
- Logging for monitoring

**Example:**
```
WARNING: Telegram server error: Internal server error. 
         Reconnecting in 5.0s...
```

### Unexpected Errors

**Handled By:**
- Logging with full stack trace
- Retry with exponential backoff
- Prevents bot crash

## Webhook Fallback

If polling fails repeatedly, the bot can automatically fall back to webhooks:

```python
# Configure in .env
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
```

**When Activated:**
- After repeated polling failures
- Automatically switches to webhook mode
- Bot continues receiving updates

**Requirements:**
- Public HTTPS URL
- SSL certificate (Let's Encrypt recommended)
- Webhook endpoint handler

## Performance Improvements

### Before Optimization

- **Timeout Errors**: Frequent `TelegramNetworkError: Request timeout`
- **Reconnection**: Manual restart required
- **Request Overhead**: High (many short-lived connections)
- **Stability**: Occasional disconnections

### After Optimization

- **Timeout Errors**: Rare (handled gracefully)
- **Reconnection**: Automatic with backoff
- **Request Overhead**: Low (connection pooling)
- **Stability**: High (automatic recovery)

## Monitoring

### Log Messages to Watch

**Normal Operation:**
```
INFO: Starting optimized long polling...
INFO: Polling timeout: 20s, Limit: 100, API timeout: 30s
```

**Reconnection:**
```
WARNING: Network error during polling: Request timeout. 
         Reconnecting in 5.0s...
```

**Success:**
```
INFO: Polling stopped normally
```

### Metrics to Track

1. **Reconnection Frequency**: How often reconnection occurs
2. **Average Reconnect Delay**: Time between failures
3. **Timeout Errors**: Count of timeout errors
4. **Successful Polls**: Number of successful update fetches

## Troubleshooting

### Issue: Still Getting Timeout Errors

**Solution:**
1. Increase `POLLING_TIMEOUT` to 30-40 seconds
2. Increase `API_REQUEST_TIMEOUT` to 60 seconds
3. Check network stability
4. Consider webhook mode for production

### Issue: Bot Not Reconnecting

**Solution:**
1. Check logs for error messages
2. Verify network connectivity
3. Check Telegram API status
4. Review reconnection delay settings

### Issue: Slow Update Processing

**Solution:**
1. Reduce `POLLING_LIMIT` if processing is slow
2. Optimize handler performance
3. Consider background task queue for heavy operations

## Best Practices

1. **Production**: Use webhooks for better reliability
2. **Development**: Use long polling (easier setup)
3. **Monitoring**: Track reconnection frequency
4. **Scaling**: Consider multiple bot instances with webhooks
5. **Error Handling**: Always log errors for debugging

## Configuration Reference

All settings are in `app/core/config.py` and can be overridden via `.env`:

```env
# Polling Configuration
POLLING_TIMEOUT=20
POLLING_LIMIT=100
POLLING_CLOSE_TIMEOUT=10

# API Timeouts
API_REQUEST_TIMEOUT=30
API_CONNECT_TIMEOUT=10
API_READ_TIMEOUT=30

# Reconnection
POLLING_RECONNECT_DELAY=5.0
POLLING_MAX_RECONNECT_DELAY=60.0
POLLING_BACKOFF_MULTIPLIER=2.0

# Webhook Fallback (optional)
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
```

## Technical Details

### How Long Polling Works

1. Bot sends `getUpdates` request to Telegram API
2. Telegram holds request open for up to `POLLING_TIMEOUT` seconds
3. If updates arrive, Telegram responds immediately
4. If timeout reached, Telegram responds with empty array
5. Bot immediately sends new `getUpdates` request
6. Process repeats

### Why Timeout Errors Occur

1. **Network Issues**: Slow/unstable connection
2. **Telegram API**: Temporary overload or maintenance
3. **Firewall/Proxy**: Interfering with long connections
4. **Default Settings**: Too aggressive (timeout=0)

### How Our Optimization Prevents Them

1. **Longer Timeout**: Reduces request frequency
2. **Connection Pooling**: Reuses connections
3. **Automatic Retry**: Handles transient failures
4. **Exponential Backoff**: Prevents overwhelming server
5. **Graceful Handling**: Logs errors, continues operation

---

**Last Updated**: 2024
**Version**: 1.0

