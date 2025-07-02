from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.models.user import TokenResponse, TokenRefresh
from app.services import AuthService, AuthenticationError
from db.database import get_session_for_services

router = APIRouter()

@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session_for_services)
):
    """
    Authenticate user and return access and refresh tokens.
    
    Args:
        form_data: OAuth2 form data containing username (email) and password
        session: Database session
        
    Returns:
        TokenResponse: Object containing access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        return AuthService.login_user(
            email=form_data.username,
            password=form_data.password,
            session=session
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token_data: TokenRefresh,
    session: Session = Depends(get_session_for_services)
):
    """
    Refresh access and refresh tokens using a valid refresh token.
    
    Args:
        refresh_token_data: Object containing the refresh token
        session: Database session
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        return AuthService.refresh_user_tokens(
            refresh_token=refresh_token_data.refresh_token,
            session=session
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        ) 