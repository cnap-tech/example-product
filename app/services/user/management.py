"""User management services."""

from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from .exceptions import UserValidationError, PermissionError, UserNotFoundError
from datetime import datetime


class UserManagementService:
    """Service class for user management operations."""
    
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
        UserManagementService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user
        from .crud import UserCRUDService
        user = UserCRUDService.get_user_by_id(user_id, session)
        
        # Update role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        return user
    
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
        UserManagementService.check_user_access_permission(user_id, current_user, require_admin=True)
        
        # Get user
        from .crud import UserCRUDService
        user = await UserCRUDService.get_user_by_id_async(user_id, session)
        
        # Update role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        
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