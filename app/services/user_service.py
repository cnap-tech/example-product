"""User service for handling user-related business logic."""

from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.user import User, UserCreate, UserRead, UserRole
from app.utils.auth import get_password_hash
from db.utils import DatabaseUtils
from datetime import datetime
import secrets


class UserValidationError(Exception):
    """Custom exception for user validation errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFoundError(Exception):
    """Custom exception for user not found errors."""
    def __init__(self, message: str = "User not found", status_code: int = status.HTTP_404_NOT_FOUND):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class PermissionError(Exception):
    """Custom exception for permission errors."""
    def __init__(self, message: str = "Not enough permissions", status_code: int = status.HTTP_403_FORBIDDEN):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserService:
    """Service class for user operations."""
    
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
        UserService.validate_unique_email(user_create.email, None, session)
        UserService.validate_unique_username(user_create.username, None, session)
        
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
        await UserService.validate_unique_email_async(user_create.email, None, session)
        await UserService.validate_unique_username_async(user_create.username, None, session)
        
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
    def check_user_access_permission(
        target_user_id: int, 
        current_user: User, 
        require_admin: bool = False
    ) -> None:
        """
        Check if current user has permission to access target user.
        
        Args:
            target_user_id: ID of user being accessed
            current_user: Current authenticated user
            require_admin: Whether admin privileges are required
            
        Raises:
            PermissionError: If user doesn't have permission
        """
        if require_admin and current_user.role != UserRole.ADMIN:
            raise PermissionError()
        
        if not require_admin:
            # Allow access to own profile or if user is admin
            if target_user_id != current_user.id and current_user.role != UserRole.ADMIN:
                raise PermissionError()
    
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
        # Check permissions
        UserService.check_user_access_permission(user_id, current_user)
        
        # Get user
        user = UserService.get_user_by_id(user_id, session)
        
        # Filter out None values
        filtered_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Validate uniqueness for email and username if being updated
        if "email" in filtered_data:
            UserService.validate_unique_email(filtered_data["email"], user_id, session)
        
        if "username" in filtered_data:
            UserService.validate_unique_username(filtered_data["username"], user_id, session)
        
        # Update user fields
        for key, value in filtered_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        return user
    
    @staticmethod
    def delete_user(user_id: int, current_user: User, session: Session, permanent: bool = False) -> None:
        """
        Delete user (soft or permanent).
        
        Args:
            user_id: ID of user to delete
            current_user: Current authenticated user (must be admin)
            session: Database session
            permanent: Whether to permanently delete
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have admin permission
        """
        # Check admin permission
        UserService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user (include deleted for potential permanent deletion)
        user = UserService.get_user_by_id(user_id, session, include_deleted=True)
        
        if permanent:
            # Permanent deletion
            session.delete(user)
        else:
            # Soft deletion
            user.deleted_at = datetime.utcnow()
            user.is_active = False
        
        session.commit()
    
    @staticmethod
    def update_user_role(user_id: int, new_role: UserRole, current_user: User, session: Session) -> User:
        """
        Update user role (admin only).
        
        Args:
            user_id: ID of user to update
            new_role: New role to assign
            current_user: Current authenticated user (must be admin)
            session: Database session
            
        Returns:
            User: Updated user object
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have admin permission
        """
        # Check admin permission
        UserService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user
        user = UserService.get_user_by_id(user_id, session)
        
        # Update role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        return user
    
    @staticmethod
    def verify_email(token: str, session: Session) -> None:
        """
        Verify user email with token.
        
        Args:
            token: Email verification token
            session: Database session
            
        Raises:
            UserValidationError: If token is invalid
        """
        statement = select(User).where(User.email_verification_token == token)
        user = session.exec(statement).first()
        
        if not user:
            raise UserValidationError("Invalid verification token")
        
        user.is_email_verified = True
        user.email_verification_token = None
        session.commit()
    
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
        # Check permissions
        UserService.check_user_access_permission(user_id, current_user)
        
        # Get user
        user = await UserService.get_user_by_id_async(user_id, session)
        
        # Filter out None values
        filtered_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Validate uniqueness for email and username if being updated
        if "email" in filtered_data:
            await UserService.validate_unique_email_async(filtered_data["email"], user_id, session)
        
        if "username" in filtered_data:
            await UserService.validate_unique_username_async(filtered_data["username"], user_id, session)
        
        # Update user fields
        for key, value in filtered_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def delete_user_async(user_id: int, current_user: User, session: AsyncSession, permanent: bool = False) -> None:
        """
        Delete user (soft or permanent) (async version).
        
        Args:
            user_id: ID of user to delete
            current_user: Current authenticated user (must be admin)
            session: Async database session
            permanent: Whether to permanently delete
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have admin permission
        """
        # Check admin permission
        UserService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user (include deleted for potential permanent deletion)
        user = await UserService.get_user_by_id_async(user_id, session, include_deleted=True)
        
        if permanent:
            # Permanent deletion
            await session.delete(user)
        else:
            # Soft deletion
            user.deleted_at = datetime.utcnow()
            user.is_active = False
        
        await session.commit()
    
    @staticmethod
    async def update_user_role_async(user_id: int, new_role: UserRole, current_user: User, session: AsyncSession) -> User:
        """
        Update user role (admin only) (async version).
        
        Args:
            user_id: ID of user to update
            new_role: New role to assign
            current_user: Current authenticated user (must be admin)
            session: Async database session
            
        Returns:
            User: Updated user object
            
        Raises:
            UserNotFoundError: If user not found
            PermissionError: If user doesn't have admin permission
        """
        # Check admin permission
        UserService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user
        user = await UserService.get_user_by_id_async(user_id, session)
        
        # Update role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def verify_email_async(token: str, session: AsyncSession) -> None:
        """
        Verify user email with token (async version).
        
        Args:
            token: Email verification token
            session: Async database session
            
        Raises:
            UserValidationError: If token is invalid
        """
        statement = select(User).where(User.email_verification_token == token)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserValidationError("Invalid verification token")
        
        user.is_email_verified = True
        user.email_verification_token = None
        await session.commit() 