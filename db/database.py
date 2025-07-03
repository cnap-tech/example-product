from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
import os
from typing import AsyncGenerator, Generator

# Environment configuration
class DatabaseConfig:
    """Database configuration management."""
    
    @staticmethod
    def get_database_url(async_driver: bool = True) -> str:
        """Get database URL based on environment and driver type."""
        if os.getenv("TESTING") == "true":
            # For tests, use test database URL
            base_url = os.getenv("TEST_DATABASE_URL")
            if not base_url:
                raise ValueError("TEST_DATABASE_URL environment variable is required when TESTING=true")
        else:
            # For production/Docker, require DATABASE_URL to be set
            base_url = os.getenv("DATABASE_URL")
            if not base_url:
                raise ValueError("DATABASE_URL environment variable is required")
        
        # Clean the URL first (remove existing drivers)
        clean_url = base_url.replace("+asyncpg", "").replace("+psycopg2", "")
        
        # Add appropriate driver
        if async_driver:
            return clean_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            return clean_url.replace("postgresql://", "postgresql+psycopg2://")
        
        return clean_url

# Global engine instances (lazy initialization)
_async_engine = None
_sync_engine = None

def _get_async_engine():
    """Get or create the async engine."""
    global _async_engine
    if _async_engine is None:
        async_database_url = DatabaseConfig.get_database_url(async_driver=True)
        _async_engine = create_async_engine(
            async_database_url,
            echo=False,  # Set to True for SQL debugging
            future=True,
            pool_pre_ping=True
        )
    return _async_engine

def _get_sync_engine():
    """Get or create the sync engine."""
    global _sync_engine
    if _sync_engine is None:
        sync_database_url = DatabaseConfig.get_database_url(async_driver=False)
        _sync_engine = create_engine(
            sync_database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True
        )
    return _sync_engine

# Database initialization
async def init_db():
    """Initialize the database tables."""
    async with _get_async_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

def init_db_sync():
    """Initialize the database tables (sync version)."""
    SQLModel.metadata.create_all(_get_sync_engine())

# Session generators
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with AsyncSession(_get_async_engine()) as session:
        yield session

def get_sync_session() -> Generator[Session, None, None]:
    """Get a sync database session."""
    with Session(_get_sync_engine()) as session:
        yield session

# Convenience function for backward compatibility
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session (async by default for backward compatibility)."""
    async for session in get_async_session():
        yield session

# New: Async session that converts to sync for service compatibility
async def get_session_for_services() -> AsyncGenerator[Session, None]:
    """Get a sync session from async context for service compatibility."""
    # Use sync session generator
    for session in get_sync_session():
        yield session

# Engine getters for external use (like middleware)
def get_sync_engine():
    """Get the sync engine instance."""
    return _get_sync_engine()

def get_async_engine():
    """Get the async engine instance."""
    return _get_async_engine() 