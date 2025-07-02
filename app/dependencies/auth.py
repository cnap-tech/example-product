"""Authentication dependencies for FastAPI routes."""

from fastapi import HTTPException, status, Request, Depends
from sqlmodel import Session
from typing import Optional
from app.models.user import User, UserRole
from app.middleware.auth import get_current_user
from db.database import get_session_for_services


async def get_current_user_dep(request: Request) -> Optional[User]:
    """Dependency to get current user (optional)."""
    return get_current_user(request)


async def require_auth(request: Request) -> User:
    """Dependency that requires authentication."""
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication required"
        )
    return current_user


async def require_admin(request: Request) -> User:
    """Dependency that requires admin privileges."""
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication required"
        )
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def require_user_access(target_user_id: int):
    """Dependency factory for user access permission."""
    async def check_access(
        request: Request,
        session: Session = Depends(get_session_for_services)
    ) -> User:
        current_user = await require_auth(request)
        
        # Users can access their own data, admins can access any data
        if target_user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return current_user
    
    return check_access 