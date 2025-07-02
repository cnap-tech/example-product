"""Exception handling utilities for converting service exceptions to HTTP exceptions."""

from fastapi import HTTPException
from app.services.auth_service import AuthenticationError
from app.services.user_service import UserValidationError, UserNotFoundError, PermissionError


def handle_service_exceptions(func):
    """
    Decorator to handle service exceptions and convert them to HTTP exceptions.
    
    Args:
        func: Route handler function
        
    Returns:
        Wrapped function that handles service exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (AuthenticationError, UserValidationError, UserNotFoundError, PermissionError) as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message,
                headers={"WWW-Authenticate": "Bearer"} if isinstance(e, AuthenticationError) else None
            )
    return wrapper


def convert_service_exception(exception):
    """
    Convert a service exception to an HTTP exception.
    
    Args:
        exception: Service exception to convert
        
    Returns:
        HTTPException: Converted HTTP exception
    """
    if isinstance(exception, (AuthenticationError, UserValidationError, UserNotFoundError, PermissionError)):
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exception, AuthenticationError) else None
        return HTTPException(
            status_code=exception.status_code,
            detail=exception.message,
            headers=headers
        )
    else:
        # For unexpected exceptions
        return HTTPException(
            status_code=500,
            detail="Internal server error"
        ) 