"""Background task queue using RQ (Redis Queue)"""
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_conn = None
_task_queue = None

# Try to import RQ dependencies, but make them optional
try:
    import redis
    from rq import Queue, Worker, Connection
    from rq.job import Job
    RQ_AVAILABLE = True
except ImportError:
    redis = None
    Queue = None
    Worker = None
    Connection = None
    Job = None
    RQ_AVAILABLE = False
    logger.warning("RQ not available - install redis and rq packages for background tasks")


def get_redis_connection():
    """Get Redis connection for RQ (synchronous)"""
    global _redis_conn
    
    if not RQ_AVAILABLE:
        raise ImportError("RQ packages not installed. Install with: pip install redis rq")
    
    if _redis_conn is None:
        redis_url = settings.RQ_REDIS_URL
        if not redis_url:
            # Build from settings
            password = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
            redis_url = f"redis://{password}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        
        try:
            _redis_conn = redis.from_url(redis_url)
            _redis_conn.ping()
            logger.info(f"Connected to Redis for task queue at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for task queue: {e}")
            raise
    
    return _redis_conn


def get_task_queue():
    """Get or create task queue"""
    global _task_queue
    
    if not RQ_AVAILABLE:
        raise ImportError("RQ not available")
    
    if _task_queue is None:
        redis_conn = get_redis_connection()
        _task_queue = Queue(settings.RQ_QUEUE_NAME, connection=redis_conn)
    
    return _task_queue


def enqueue_task(func, *args, **kwargs):
    """Enqueue a background task"""
    if not RQ_AVAILABLE:
        logger.warning(f"Cannot enqueue task {func.__name__}: RQ not available. Running synchronously.")
        # Fallback: run synchronously
        return func(*args, **kwargs)
    
    queue = get_task_queue()
    job = queue.enqueue(func, *args, **kwargs)
    logger.info(f"Enqueued task {job.id}: {func.__name__}")
    return job


def get_job(job_id: str):
    """Get job by ID"""
    if not RQ_AVAILABLE:
        raise ImportError("RQ not available")
    return Job.fetch(job_id, connection=get_redis_connection())


def get_job_status(job_id: str) -> str:
    """Get job status"""
    if not RQ_AVAILABLE:
        return "unknown"
    
    try:
        job = get_job(job_id)
        return job.get_status()
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return "unknown"

