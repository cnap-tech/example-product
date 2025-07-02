from fastapi import APIRouter, Depends
from typing import List
from app.models.user import (
    User, UserCreate, UserRead, UserRole, UserUpdate
)
from app.services import UserService
from app.utils.exceptions import handle_service_exception
from app.dependencies.auth import require_auth, require_admin, get_current_user_dep
from app.dependencies.database import DBSession

router = APIRouter()

@router.post("/users", response_model=UserRead)
async def create_user(
    user_create: UserCreate,
    session = DBSession
):
    """
    Create a new user account.
    
    Args:
        user_create: User creation data
        session: Database session
        
    Returns:
        UserRead: Created user data
        
    Raises:
        HTTPException: If validation fails or user already exists
    """
    try:
        user = UserService.create_user(user_create, session)
        return user
    except Exception as e:
        handle_service_exception(e)

@router.get("/users", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    List users with pagination. Requires authentication.
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        List[UserRead]: List of users
    """
    users = UserService.list_users(skip, limit, session)
    return users

@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Get user by ID. Users can only access their own profile unless they're admin.
    
    Args:
        user_id: ID of user to retrieve
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        UserRead: User data
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        # Check permissions first
        UserService.check_user_access_permission(user_id, current_user)
        
        # Get user
        user = UserService.get_user_by_id(user_id, session)
        return user
    except Exception as e:
        handle_service_exception(e)

@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Update user information. Users can only update their own profile unless they're admin.
    
    Args:
        user_id: ID of user to update
        user_update: User update data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        UserRead: Updated user data
        
    Raises:
        HTTPException: If user not found, access denied, or validation fails
    """
    try:
        # Convert to dict and filter None values
        update_data = user_update.model_dump(exclude_unset=True)
        
        user = UserService.update_user(user_id, update_data, current_user, session)
        return user
    except Exception as e:
        handle_service_exception(e)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    permanent: bool = False,
    current_user: User = Depends(require_admin),
    session = DBSession
):
    """
    Delete user (soft or permanent). Requires admin privileges.
    
    Args:
        user_id: ID of user to delete
        permanent: Whether to permanently delete the user
        current_user: Current authenticated user (admin)
        session: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        UserService.delete_user(user_id, current_user, session, permanent)
        return {"detail": "User deleted successfully"}
    except Exception as e:
        handle_service_exception(e)

@router.post("/users/verify-email/{token}")
async def verify_email(
    token: str,
    session = DBSession
):
    """
    Verify user email with verification token.
    
    Args:
        token: Email verification token
        session: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        UserService.verify_email(token, session)
        return {"detail": "Email verified successfully"}
    except Exception as e:
        handle_service_exception(e)

@router.post("/users/{user_id}/role", response_model=UserRead)
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(require_admin),
    session = DBSession
):
    """
    Update user role. Requires admin privileges.
    
    Args:
        user_id: ID of user to update
        role: New role to assign
        current_user: Current authenticated user (admin)
        session: Database session
        
    Returns:
        UserRead: Updated user data
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        user = UserService.update_user_role(user_id, role, current_user, session)
        return user
    except Exception as e:
        handle_service_exception(e) 