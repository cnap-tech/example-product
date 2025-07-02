"""User validation services."""

from typing import Optional
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from .exceptions import UserValidationError


class UserValidationService:
    """Service class for user validation operations."""
    
    @staticmethod
    def validate_unique_email(email: str, exclude_user_id: Optional[int], session: Session) -> None:
        """
        Validate that email is unique.
        
        Args:
            email: Email to validate
            exclude_user_id: User ID to exclude from check (for updates)
            session: Database session
            
        Raises:
            UserValidationError: If email already exists
        """
        query = select(User).where(User.email == email)
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        existing_user = session.exec(query).first()
        if existing_user:
            raise UserValidationError("Email already registered")
    
    @staticmethod
    async def validate_unique_email_async(email: str, exclude_user_id: Optional[int], session: AsyncSession) -> None:
        """
        Validate that email is unique (async version).
        
        Args:
            email: Email to validate
            exclude_user_id: User ID to exclude from check (for updates)
            session: Async database session
            
        Raises:
            UserValidationError: If email already exists
        """
        query = select(User).where(User.email == email)
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise UserValidationError("Email already registered")
    
    @staticmethod
    def validate_unique_username(username: str, exclude_user_id: Optional[int], session: Session) -> None:
        """
        Validate that username is unique.
        
        Args:
            username: Username to validate
            exclude_user_id: User ID to exclude from check (for updates)
            session: Database session
            
        Raises:
            UserValidationError: If username already exists
        """
        query = select(User).where(User.username == username)
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        existing_user = session.exec(query).first()
        if existing_user:
            raise UserValidationError("Username already taken")
    
    @staticmethod
    async def validate_unique_username_async(username: str, exclude_user_id: Optional[int], session: AsyncSession) -> None:
        """
        Validate that username is unique (async version).
        
        Args:
            username: Username to validate
            exclude_user_id: User ID to exclude from check (for updates)
            session: Async database session
            
        Raises:
            UserValidationError: If username already exists
        """
        query = select(User).where(User.username == username)
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise UserValidationError("Username already taken") 