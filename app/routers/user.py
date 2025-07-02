from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlmodel import Session
from typing import List
from app.models.user import (
    User, UserCreate, UserRead, UserRole, UserUpdate
)
from app.services import (
    UserService, UserValidationError, UserNotFoundError, PermissionError
)
from db.database import get_session_for_services
from app.middleware.auth import get_current_user, get_admin_user

router = APIRouter()

def _handle_user_service_exception(e):
    """Helper function to convert service exceptions to HTTP exceptions."""
    raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/users", response_model=UserRead)
async def create_user(
    user_create: UserCreate,
    session: Session = Depends(get_session_for_services)
):
    """
    Create a new user account.
    
    Args:
        user_create: User creation data
        session: Async database session
        
    Returns:
        UserRead: Created user data
        
    Raises:
        HTTPException: If validation fails or user already exists
    """
    try:
        user = UserService.create_user(user_create, session)
        return user
    except UserValidationError as e:
        _handle_user_service_exception(e)

@router.get("/users", response_model=List[UserRead])
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session_for_services)
):
    """
    List users with pagination. Requires authentication.
    
    Args:
        request: HTTP request object (for authentication)
        skip: Number of users to skip
        limit: Maximum number of users to return
        session: Async database session
        
    Returns:
        List[UserRead]: List of users
    """
    # Verify user is authenticated
    current_user = get_current_user(request)
    
    users = UserService.list_users(skip, limit, session)
    return users

@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    request: Request,
    user_id: int,
    session: Session = Depends(get_session_for_services)
):
    """
    Get user by ID. Users can only access their own profile unless they're admin.
    
    Args:
        request: HTTP request object (for authentication)
        user_id: ID of user to retrieve
        session: Async database session
        
    Returns:
        UserRead: User data
        
    Raises:
        HTTPException: If user not found or access denied
    """
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    
    try:
        # Check permissions first
        UserService.check_user_access_permission(user_id, current_user)
        
        # Get user
        user = UserService.get_user_by_id(user_id, session)
        return user
    except (UserNotFoundError, PermissionError) as e:
        _handle_user_service_exception(e)

@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session_for_services)
):
    """
    Update user information. Users can only update their own profile unless they're admin.
    
    Args:
        request: HTTP request object (for authentication)
        user_id: ID of user to update
        user_update: User update data
        session: Async database session
        
    Returns:
        UserRead: Updated user data
        
    Raises:
        HTTPException: If user not found, access denied, or validation fails
    """
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    
    try:
        # Convert to dict and filter None values
        update_data = user_update.model_dump(exclude_unset=True)
        
        user = UserService.update_user(user_id, update_data, current_user, session)
        return user
    except (UserNotFoundError, PermissionError, UserValidationError) as e:
        _handle_user_service_exception(e)

@router.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    permanent: bool = False,
    session: Session = Depends(get_session_for_services)
):
    """
    Delete user (soft or permanent). Requires admin privileges.
    
    Args:
        request: HTTP request object (for authentication)
        user_id: ID of user to delete
        permanent: Whether to permanently delete the user
        session: Async database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found or access denied
    """
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    
    try:
        UserService.delete_user(user_id, current_user, session, permanent)
        return {"detail": "User deleted successfully"}
    except (UserNotFoundError, PermissionError) as e:
        _handle_user_service_exception(e)

@router.post("/users/verify-email/{token}")
async def verify_email(
    token: str,
    session: Session = Depends(get_session_for_services)
):
    """
    Verify user email with verification token.
    
    Args:
        token: Email verification token
        session: Async database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        UserService.verify_email(token, session)
        return {"detail": "Email verified successfully"}
    except UserValidationError as e:
        _handle_user_service_exception(e)

@router.post("/users/{user_id}/role", response_model=UserRead)
async def update_user_role(
    request: Request,
    user_id: int,
    role: UserRole,
    session: Session = Depends(get_session_for_services)
):
    """
    Update user role. Requires admin privileges.
    
    Args:
        request: HTTP request object (for authentication)
        user_id: ID of user to update
        role: New role to assign
        session: Async database session
        
    Returns:
        UserRead: Updated user data
        
    Raises:
        HTTPException: If user not found or access denied
    """
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    
    try:
        user = UserService.update_user_role(user_id, role, current_user, session)
        return user
    except (UserNotFoundError, PermissionError) as e:
        _handle_user_service_exception(e) 