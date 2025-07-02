"""User service exceptions."""

from fastapi import status


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
    def __init__(self, message: str = "Access denied", status_code: int = status.HTTP_403_FORBIDDEN):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message) 