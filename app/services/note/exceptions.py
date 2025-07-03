"""
Note-specific exceptions for the note service.

These exceptions provide specific error handling for note operations
and follow the same pattern as user service exceptions.
"""

from fastapi import HTTPException, status

class NoteNotFoundError(HTTPException):
    """Raised when a note is not found."""
    def __init__(self, note_id: int = None):
        if note_id:
            detail = f"Note with ID {note_id} not found"
        else:
            detail = "Note not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class NoteAccessDeniedError(HTTPException):
    """Raised when a user doesn't have permission to access a note."""
    def __init__(self, action: str = "access"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to {action} this note"
        )

class NoteValidationError(HTTPException):
    """Raised when note data validation fails."""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Note validation error: {message}"
        )

class AuthorNotFoundError(HTTPException):
    """Raised when trying to remove an author that doesn't exist on the note."""
    def __init__(self, user_id: int, note_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} is not an author of note {note_id}"
        )

class AuthorAlreadyExistsError(HTTPException):
    """Raised when trying to add an author that already exists on the note."""
    def __init__(self, user_id: int, note_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {user_id} is already an author of note {note_id}"
        )

class NoteOperationError(HTTPException):
    """Raised when a note operation fails for business logic reasons."""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        ) 