"""Monitoring and observability utilities"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crud import log_health_check

logger = logging.getLogger(__name__)


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


@asynccontextmanager
async def track_error(db: AsyncSession, handler_name: str, user_id: int = None):
    """Context manager to track errors in health check system"""
    try:
        yield
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_message = str(e)
        stack_trace = traceback.format_exc()
        
        try:
            await log_health_check(
                db=db,
                check_type="error",
                error_message=error_message,
                error_type=error_type,
                user_id=user_id,
                handler_name=handler_name,
                stack_trace=stack_trace
            )
        except Exception as log_error:
            logger.error(f"Failed to log health check: {log_error}")
        
        raise


class MetricsCollector:
    """Simple metrics collector for basic statistics"""
    
    def __init__(self):
        self.counters = {}
        self.timings = {}
    
    def increment(self, metric_name: str, value: int = 1):
        """Increment a counter metric"""
        self.counters[metric_name] = self.counters.get(metric_name, 0) + value
    
    def record_timing(self, metric_name: str, duration: float):
        """Record a timing metric"""
        if metric_name not in self.timings:
            self.timings[metric_name] = []
        self.timings[metric_name].append(duration)
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        stats = {
            "counters": self.counters.copy(),
            "timings": {}
        }
        
        for metric_name, timings in self.timings.items():
            if timings:
                stats["timings"][metric_name] = {
                    "count": len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "avg": sum(timings) / len(timings)
                }
        
        return stats
    
    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.timings.clear()


# Global metrics collector instance
metrics = MetricsCollector()

