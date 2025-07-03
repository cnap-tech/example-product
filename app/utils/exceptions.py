"""Exception handling utilities for converting service exceptions to HTTP exceptions."""

from fastapi import HTTPException
from app.services.auth_service import AuthenticationError
from app.services.user.exceptions import UserValidationError, UserNotFoundError, PermissionError
# Note: Note exceptions inherit from HTTPException and don't need special handling


class FriendshipValidationError(Exception):
    """Exception raised for friendship validation errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FriendshipNotFoundError(Exception):
    """Exception raised when friendship is not found."""
    def __init__(self, message: str = "Friendship not found", status_code: int = 404):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# List of all service exceptions (non-HTTPException types only)
SERVICE_EXCEPTIONS = (
    AuthenticationError, 
    UserValidationError, 
    UserNotFoundError, 
    PermissionError,
    FriendshipValidationError, 
    FriendshipNotFoundError
    # Note: Note exceptions inherit from HTTPException and are handled directly by FastAPI
)


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
        except SERVICE_EXCEPTIONS as e:
            # Handle HTTPExceptions specially
            if isinstance(e, HTTPException):
                raise e
            # Use getattr to handle both message and detail attributes
            detail = getattr(e, 'message', getattr(e, 'detail', str(e)))
            raise HTTPException(
                status_code=e.status_code,
                detail=detail,
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
    # Note exceptions are already HTTPException instances, just return them
    if isinstance(exception, HTTPException):
        return exception
    elif isinstance(exception, SERVICE_EXCEPTIONS):
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exception, AuthenticationError) else None
        # Use getattr to handle both message and detail attributes
        detail = getattr(exception, 'message', getattr(exception, 'detail', str(exception)))
        return HTTPException(
            status_code=exception.status_code,
            detail=detail,
            headers=headers
        )
    else:
        # For unexpected exceptions
        return HTTPException(
            status_code=500,
            detail="Internal server error"
        )


def handle_service_exception_simple(exception):
    """
    Simple handler that directly raises HTTPException from service exception.
    
    Args:
        exception: Service exception to convert and raise
        
    Raises:
        HTTPException: Converted HTTP exception
    """
    # Note exceptions are already HTTPException instances, just re-raise them
    if isinstance(exception, HTTPException):
        raise exception
    elif isinstance(exception, SERVICE_EXCEPTIONS):
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exception, AuthenticationError) else None
        # Use getattr to handle both message and detail attributes
        detail = getattr(exception, 'message', getattr(exception, 'detail', str(exception)))
        raise HTTPException(
            status_code=exception.status_code,
            detail=detail,
            headers=headers
        )
    else:
        # For unexpected exceptions
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# Unified exception handler for all routers
def handle_service_exception(exception):
    """
    Unified exception handler for all routers.
    Raises HTTPException with proper status code and message.
    
    Args:
        exception: Service exception to handle
        
    Raises:
        HTTPException: Converted HTTP exception
    """
    handle_service_exception_simple(exception) 