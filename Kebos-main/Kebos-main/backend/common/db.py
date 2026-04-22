# Sample SQLAlchemy DB setup for PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Validate required environment variables
required_env_vars = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD", 
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

DB_URL = os.getenv("DATABASE_URL") or (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# Async database URL (replace postgresql:// with postgresql+asyncpg://)
ASYNC_DB_URL = os.getenv("ASYNC_DATABASE_URL") or DB_URL.replace("postgresql://", "postgresql+asyncpg://")

# Synchronous engine and session
engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine and session
async_engine = create_async_engine(ASYNC_DB_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Dependency for DB session
def get_db():
    """
    FastAPI dependency that provides a database session.
    Ensures proper session management with automatic cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Async dependency for DB session
async def get_async_session():
    """
    FastAPI dependency that provides an async database session.
    Ensures proper session management with automatic cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
