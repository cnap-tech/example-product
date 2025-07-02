"""Authentication service for handling auth-related business logic."""

from typing import Optional, Tuple
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.user import User, TokenResponse
from app.utils.auth import verify_password, create_access_token, create_refresh_token, verify_token
from db.utils import DatabaseUtils


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthService:
    """Service class for authentication operations."""
    
    @staticmethod
    def authenticate_user(email: str, password: str, session: Session) -> User:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            session: Database session
            
        Returns:
            User: Authenticated user object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Find user by email
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if not user:
            raise AuthenticationError("Incorrect email or password")
        
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
            
        return user
    
    @staticmethod
    async def authenticate_user_async(email: str, password: str, session: AsyncSession) -> User:
        """
        Authenticate user with email and password (async version).
        
        Args:
            email: User's email address
            password: Plain text password
            session: Async database session
            
        Returns:
            User: Authenticated user object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Find user by email
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("Incorrect email or password")
        
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
            
        return user
    
    @staticmethod
    def create_user_tokens(user: User) -> TokenResponse:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user: User object
            
        Returns:
            TokenResponse: Object containing access and refresh tokens
        """
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    @staticmethod
    def refresh_user_tokens(refresh_token: str, session: Session) -> TokenResponse:
        """
        Refresh user tokens using a valid refresh token.
        
        Args:
            refresh_token: The refresh token string
            session: Database session
            
        Returns:
            TokenResponse: New access and refresh tokens
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if payload is None:
            raise AuthenticationError("Invalid refresh token")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid refresh token")
        
        # Find user and validate status
        statement = select(User).where(User.id == int(user_id))
        user = session.exec(statement).first()
        
        if not user or not user.is_active:
            raise AuthenticationError("User is inactive or deleted")
        
        # Create new tokens
        return AuthService.create_user_tokens(user)
    
    @staticmethod
    async def refresh_user_tokens_async(refresh_token: str, session: AsyncSession) -> TokenResponse:
        """
        Refresh user tokens using a valid refresh token (async version).
        
        Args:
            refresh_token: The refresh token string
            session: Async database session
            
        Returns:
            TokenResponse: New access and refresh tokens
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if payload is None:
            raise AuthenticationError("Invalid refresh token")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid refresh token")
        
        # Find user and validate status
        statement = select(User).where(User.id == int(user_id))
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise AuthenticationError("User is inactive or deleted")
        
        # Create new tokens
        return AuthService.create_user_tokens(user)
    
    @staticmethod
    def login_user(email: str, password: str, session: Session) -> TokenResponse:
        """
        Complete login flow: authenticate user and return tokens.
        
        Args:
            email: User's email address
            password: Plain text password
            session: Database session
            
        Returns:
            TokenResponse: Object containing access and refresh tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        user = AuthService.authenticate_user(email, password, session)
        return AuthService.create_user_tokens(user)
    
    @staticmethod
    async def login_user_async(email: str, password: str, session: AsyncSession) -> TokenResponse:
        """
        Complete login flow: authenticate user and return tokens (async version).
        
        Args:
            email: User's email address
            password: Plain text password
            session: Async database session
            
        Returns:
            TokenResponse: Object containing access and refresh tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        user = await AuthService.authenticate_user_async(email, password, session)
        return AuthService.create_user_tokens(user) 