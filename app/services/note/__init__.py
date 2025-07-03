"""
Note service package providing unified interface for note operations.

This package follows the modular pattern established in the user service,
providing separate modules for different concerns while maintaining
backward compatibility through a unified service class.
"""

from .crud import NoteCRUD
from .permissions import NotePermissions
from .authors import NoteAuthors
from .exceptions import (
    NoteNotFoundError, NoteAccessDeniedError, NoteValidationError,
    AuthorNotFoundError, AuthorAlreadyExistsError
)

class NoteService:
    """
    Unified note service providing all note-related operations.
    
    This class combines functionality from multiple specialized modules:
    - CRUD operations (create, read, update, delete)
    - Permission checking and access control
    - Author management (add, remove, list)
    - Validation and business logic
    """
    
    # CRUD Operations
    create_note = staticmethod(NoteCRUD.create_note)
    get_note_by_id = staticmethod(NoteCRUD.get_note_by_id)
    list_notes = staticmethod(NoteCRUD.list_notes)
    list_user_notes = staticmethod(NoteCRUD.list_user_notes)
    update_note = staticmethod(NoteCRUD.update_note)
    delete_note = staticmethod(NoteCRUD.delete_note)
    
    # Permission Operations
    check_note_access = staticmethod(NotePermissions.check_note_access)
    can_view_note = staticmethod(NotePermissions.can_view_note)
    can_edit_note = staticmethod(NotePermissions.can_edit_note)
    can_delete_note = staticmethod(NotePermissions.can_delete_note)
    
    # Author Management
    add_author = staticmethod(NoteAuthors.add_author)
    remove_author = staticmethod(NoteAuthors.remove_author)
    get_note_authors = staticmethod(NoteAuthors.get_note_authors)
    is_user_author = staticmethod(NoteAuthors.is_user_author)

# Export everything for backward compatibility and convenience
__all__ = [
    'NoteService',
    'NoteCRUD',
    'NotePermissions', 
    'NoteAuthors',
    'NoteNotFoundError',
    'NoteAccessDeniedError',
    'NoteValidationError',
    'AuthorNotFoundError',
    'AuthorAlreadyExistsError'
] 