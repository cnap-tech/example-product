"""User CRUD services."""

from typing import List, Dict, Any
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserCreate
from app.utils.auth import get_password_hash
from .validation import UserValidationService
from .exceptions import UserNotFoundError, PermissionError
import secrets
from datetime import datetime


class UserCRUDService:
    """Service class for user CRUD operations."""
    
    @staticmethod
    def create_user(user_create: UserCreate, session: Session) -> User:
        """
        Create a new user.
        
        Args:
            user_create: User creation data
            session: Database session
            
        Returns:
            User: Created user object
            
        Raises:
            UserValidationError: If validation fails
        """
        # Validate uniqueness
        UserValidationService.validate_unique_email(user_create.email, None, session)
        UserValidationService.validate_unique_username(user_create.username, None, session)
        
        # Create user
        user_dict = user_create.model_dump(exclude={"password", "email_verification_token"})
        user = User(
            **user_dict,
            hashed_password=get_password_hash(user_create.password),
            email_verification_token=secrets.token_urlsafe()
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # TODO: Send verification email
        
        return user
    
    @staticmethod
    async def create_user_async(user_create: UserCreate, session: AsyncSession) -> User:
        """
        Create a new user (async version).
        
        Args:
            user_create: User creation data
            session: Async database session
            
        Returns:
            User: Created user object
            
        Raises:
            UserValidationError: If validation fails
        """
        # Validate uniqueness
        await UserValidationService.validate_unique_email_async(user_create.email, None, session)
        await UserValidationService.validate_unique_username_async(user_create.username, None, session)
        
        # Create user
        user_dict = user_create.model_dump(exclude={"password", "email_verification_token"})
        user = User(
            **user_dict,
            hashed_password=get_password_hash(user_create.password),
            email_verification_token=secrets.token_urlsafe()
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # TODO: Send verification email
        
        return user
    
    @staticmethod
    def get_user_by_id(user_id: int, session: Session, include_deleted: bool = False) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            session: Database session
            include_deleted: Whether to include soft-deleted users
            
        Returns:
            User: User object
            
        Raises:
            UserNotFoundError: If user not found
        """
        query = select(User).where(User.id == user_id)
        if not include_deleted:
            query = query.where(User.deleted_at == None)
        
        user = session.exec(query).first()
        if not user:
            raise UserNotFoundError()
        
        return user
    
    @staticmethod
    async def get_user_by_id_async(user_id: int, session: AsyncSession, include_deleted: bool = False) -> User:
        """
        Get user by ID (async version).
        
        Args:
            user_id: User ID
            session: Async database session
            include_deleted: Whether to include soft-deleted users
            
        Returns:
            User: User object
            
        Raises:
            UserNotFoundError: If user not found
        """
        query = select(User).where(User.id == user_id)
        if not include_deleted:
            query = query.where(User.deleted_at == None)
        
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError()
        
        return user
    
    @staticmethod
    def list_users(skip: int, limit: int, session: Session) -> List[User]:
        """
        List users with pagination.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            session: Database session
            
        Returns:
            List[User]: List of users
        """
        query = select(User).where(User.deleted_at == None)
        query = query.offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    async def list_users_async(skip: int, limit: int, session: AsyncSession) -> List[User]:
        """
        List users with pagination (async version).
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            session: Async database session
            
        Returns:
            List[User]: List of users
        """
        query = select(User).where(User.deleted_at == None)
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    def update_user(
        user_id: int, 
        update_data: Dict[str, Any], 
        current_user: User, 
        session: Session
    ) -> User:
        """
        Update user information.
        
        Args:
            user_id: ID of user to update
            update_data: Data to update
            current_user: Current authenticated user
            session: Database session
            
        Returns:
            User: Updated user object
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have permission
            UserValidationError: If validation fails
        """
        from .management import UserManagementService
        
        # Check permissions
        UserManagementService.check_user_access_permission(user_id, current_user)
        
        # Get user
        user = UserCRUDService.get_user_by_id(user_id, session)
        
        # Validate email and username if being updated
        if "email" in update_data:
            UserValidationService.validate_unique_email(update_data["email"], user_id, session)
        
        if "username" in update_data:
            UserValidationService.validate_unique_username(update_data["username"], user_id, session)
        
        # Update user
        for key, value in update_data.items():
            if hasattr(user, key) and key not in ["id", "created_at", "hashed_password"]:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return user
    
    @staticmethod
    async def update_user_async(
        user_id: int, 
        update_data: Dict[str, Any], 
        current_user: User, 
        session: AsyncSession
    ) -> User:
        """
        Update user information (async version).
        
        Args:
            user_id: ID of user to update
            update_data: Data to update
            current_user: Current authenticated user
            session: Async database session
            
        Returns:
            User: Updated user object
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have permission
            UserValidationError: If validation fails
        """
        from .management import UserManagementService
        
        # Check permissions
        UserManagementService.check_user_access_permission(user_id, current_user)
        
        # Get user
        user = await UserCRUDService.get_user_by_id_async(user_id, session)
        
        # Validate email and username if being updated
        if "email" in update_data:
            await UserValidationService.validate_unique_email_async(update_data["email"], user_id, session)
        
        if "username" in update_data:
            await UserValidationService.validate_unique_username_async(update_data["username"], user_id, session)
        
        # Update user
        for key, value in update_data.items():
            if hasattr(user, key) and key not in ["id", "created_at", "hashed_password"]:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    def delete_user(user_id: int, current_user: User, session: Session, permanent: bool = False) -> None:
        """
        Delete user (soft or permanent).
        
        Args:
            user_id: ID of user to delete
            current_user: Current authenticated user
            session: Database session
            permanent: Whether to permanently delete the user
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have permission
        """
        from .management import UserManagementService
        
        # Check permissions (requires admin)
        UserManagementService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user
        user = UserCRUDService.get_user_by_id(user_id, session, include_deleted=True)
        
        if permanent:
            # Hard delete
            session.delete(user)
        else:
            # Soft delete
            user.deleted_at = datetime.utcnow()
            user.is_active = False
            session.add(user)
        
        session.commit()
    
    @staticmethod
    async def delete_user_async(user_id: int, current_user: User, session: AsyncSession, permanent: bool = False) -> None:
        """
        Delete user (soft or permanent) (async version).
        
        Args:
            user_id: ID of user to delete
            current_user: Current authenticated user
            session: Async database session
            permanent: Whether to permanently delete the user
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have permission
        """
        from .management import UserManagementService
        
        # Check permissions (requires admin)
        UserManagementService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user
        user = await UserCRUDService.get_user_by_id_async(user_id, session, include_deleted=True)
        
        if permanent:
            # Hard delete
            await session.delete(user)
        else:
            # Soft delete
            user.deleted_at = datetime.utcnow()
            user.is_active = False
            session.add(user)
        
        await session.commit() 