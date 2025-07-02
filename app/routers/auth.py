from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import TokenResponse, TokenRefresh
from app.services import AuthService
from app.utils.exceptions import handle_service_exception
from app.dependencies.database import DBSession

router = APIRouter()

@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session = DBSession
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
    except Exception as e:
        handle_service_exception(e)

@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token_data: TokenRefresh,
    session = DBSession
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
    except Exception as e:
        handle_service_exception(e) 