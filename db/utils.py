"""Database utility functions for common operations."""

from sqlmodel import Session, select
from typing import Optional, List, Type, TypeVar
from db.database import get_sync_session, get_async_session
from app.models.user import User

# Generic type for model classes
ModelType = TypeVar("ModelType")

class DatabaseUtils:
    """Utility class for common database operations."""
    
    @staticmethod
    def get_user_by_id_sync(user_id: int) -> Optional[User]:
        """Get user by ID using sync session."""
        for session in get_sync_session():
            statement = select(User).where(
                User.id == user_id,
                User.deleted_at == None,
                User.is_active == True
            )
            return session.exec(statement).first()
    
    @staticmethod
    def get_user_by_email_sync(email: str) -> Optional[User]:
        """Get user by email using sync session."""
        for session in get_sync_session():
            statement = select(User).where(
                User.email == email,
                User.deleted_at == None
            )
            return session.exec(statement).first()
    
    @staticmethod
    def get_user_by_username_sync(username: str) -> Optional[User]:
        """Get user by username using sync session."""
        for session in get_sync_session():
            statement = select(User).where(
                User.username == username,
                User.deleted_at == None
            )
            return session.exec(statement).first()
    
    @staticmethod
    async def get_user_by_id_async(user_id: int) -> Optional[User]:
        """Get user by ID using async session."""
        async for session in get_async_session():
            statement = select(User).where(
                User.id == user_id,
                User.deleted_at == None,
                User.is_active == True
            )
            result = await session.execute(statement)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email_async(email: str) -> Optional[User]:
        """Get user by email using async session."""
        async for session in get_async_session():
            statement = select(User).where(
                User.email == email,
                User.deleted_at == None
            )
            result = await session.execute(statement)
            return result.scalar_one_or_none()

# Convenience functions for backward compatibility
def get_user_by_id(user_id: int, use_sync: bool = True) -> Optional[User]:
    """Get user by ID (sync by default for middleware compatibility)."""
    if use_sync:
        return DatabaseUtils.get_user_by_id_sync(user_id)
    else:
        # This would need to be awaited
        return DatabaseUtils.get_user_by_id_async(user_id)

def get_user_by_email(email: str, use_sync: bool = True) -> Optional[User]:
    """Get user by email (sync by default for middleware compatibility)."""
    if use_sync:
        return DatabaseUtils.get_user_by_email_sync(email)
    else:
        # This would need to be awaited
        return DatabaseUtils.get_user_by_email_async(email) 