from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings
from app.models.base import Base
import logging

logger = logging.getLogger(__name__)

# Determine database URL - use PostgreSQL if configured, otherwise SQLite
def get_database_url() -> str:
    """Get database URL based on configuration"""
    # Check if DATABASE_URL is explicitly set to PostgreSQL
    if settings.DATABASE_URL.startswith(("postgresql", "postgresql+asyncpg")):
        logger.info(f"Using PostgreSQL from DATABASE_URL")
        return settings.DATABASE_URL
    
    # Check if PostgreSQL components are configured
    # Use PostgreSQL if POSTGRES_HOST, POSTGRES_USER, and POSTGRES_DB are set
    # AND DATABASE_URL is still SQLite (not already PostgreSQL)
    postgres_host = getattr(settings, 'POSTGRES_HOST', None)
    postgres_user = getattr(settings, 'POSTGRES_USER', None)
    postgres_db = getattr(settings, 'POSTGRES_DB', None)
    postgres_port = getattr(settings, 'POSTGRES_PORT', 5432)
    postgres_password = getattr(settings, 'POSTGRES_PASSWORD', '')
    
    # Check if PostgreSQL is explicitly configured (all required fields present)
    if (postgres_host and postgres_user and postgres_db and 
        settings.DATABASE_URL.startswith("sqlite")):
        # Build PostgreSQL URL from components
        password_part = f":{postgres_password}" if postgres_password else ""
        db_url = f"postgresql+asyncpg://{postgres_user}{password_part}@{postgres_host}:{postgres_port}/{postgres_db}"
        logger.info(f"Using PostgreSQL database: {postgres_host}:{postgres_port}/{postgres_db}")
        return db_url
    
    # Default to SQLite
    logger.info("Using SQLite database (default)")
    return settings.DATABASE_URL

# Create engine with connection pooling for PostgreSQL
database_url = get_database_url()
if database_url.startswith("postgresql+asyncpg"):
    # PostgreSQL with connection pooling
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        poolclass=QueuePool,
        pool_size=getattr(settings, 'POSTGRES_POOL_SIZE', 10),
        max_overflow=getattr(settings, 'POSTGRES_MAX_OVERFLOW', 20),
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
else:
    # SQLite (no pooling needed)
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        poolclass=NullPool,  # SQLite doesn't need connection pooling
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")
