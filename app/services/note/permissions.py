"""
Note permissions module.

Handles access control for notes based on privacy settings and authorship.
"""

from typing import Optional
from sqlmodel import Session, select
from app.models.note import Note, NoteAuthor, NotePrivacy
from app.models.user import User, UserRole
from .exceptions import NoteAccessDeniedError
from .crud import NoteCRUD

class NotePermissions:
    """Permission checking for note operations."""
    
    @staticmethod
    def can_view_note(note: Note, user: Optional[User], session: Session) -> bool:
        """
        Check if a user can view a note.
        
        Rules:
        - Public notes: Anyone can view (even without authentication)
        - Private notes: Only authors can view
        - Admins: Can view any note
        
        Args:
            note: Note to check access for
            user: User requesting access (can be None for public access)
            session: Database session
            
        Returns:
            bool: True if user can view the note
        """
        # Public notes can be viewed by anyone
        if note.privacy == NotePrivacy.PUBLIC:
            return True
        
        # Private notes require authentication
        if not user:
            return False
        
        # Admins can view any note
        if user.role == UserRole.ADMIN:
            return True
        
        # Check if user is an author of the note
        author_statement = select(NoteAuthor).where(
            NoteAuthor.note_id == note.id,
            NoteAuthor.user_id == user.id
        )
        is_author = session.exec(author_statement).first() is not None
        
        return is_author
    
    @staticmethod
    def can_edit_note(note: Note, user: User, session: Session) -> bool:
        """
        Check if a user can edit a note.
        
        Rules:
        - Only authors can edit notes
        - Admins can edit any note
        
        Args:
            note: Note to check access for
            user: User requesting access
            session: Database session
            
        Returns:
            bool: True if user can edit the note
        """
        # Admins can edit any note
        if user.role == UserRole.ADMIN:
            return True
        
        # Check if user is an author of the note
        author_statement = select(NoteAuthor).where(
            NoteAuthor.note_id == note.id,
            NoteAuthor.user_id == user.id
        )
        is_author = session.exec(author_statement).first() is not None
        
        return is_author
    
    @staticmethod
    def can_delete_note(note: Note, user: User, session: Session) -> bool:
        """
        Check if a user can delete a note.
        
        Rules:
        - Only the creator can delete notes
        - Admins can delete any note
        
        Args:
            note: Note to check access for
            user: User requesting access
            session: Database session
            
        Returns:
            bool: True if user can delete the note
        """
        # Admins can delete any note
        if user.role == UserRole.ADMIN:
            return True
        
        # Only the creator can delete the note
        return note.created_by_user_id == user.id
    
    @staticmethod
    def can_manage_authors(note: Note, user: User, session: Session) -> bool:
        """
        Check if a user can add or remove authors from a note.
        
        Rules:
        - Only authors can manage other authors
        - Admins can manage authors on any note
        
        Args:
            note: Note to check access for
            user: User requesting access
            session: Database session
            
        Returns:
            bool: True if user can manage authors
        """
        # Admins can manage authors on any note
        if user.role == UserRole.ADMIN:
            return True
        
        # Check if user is an author of the note
        author_statement = select(NoteAuthor).where(
            NoteAuthor.note_id == note.id,
            NoteAuthor.user_id == user.id
        )
        is_author = session.exec(author_statement).first() is not None
        
        return is_author
    
    @staticmethod
    def check_note_access(note_id: int, user: Optional[User], action: str, session: Session) -> Note:
        """
        Check note access and return the note if access is granted.
        
        Args:
            note_id: Note ID to check access for
            user: User requesting access
            action: Action being performed ('view', 'edit', 'delete', 'manage_authors')
            session: Database session
            
        Returns:
            Note: Note instance if access is granted
            
        Raises:
            NoteNotFoundError: If note doesn't exist
            NoteAccessDeniedError: If access is denied
        """
        # Get the note
        note = NoteCRUD.get_note_by_id(note_id, session)
        
        # Check permissions based on action
        can_access = False
        
        if action == "view":
            can_access = NotePermissions.can_view_note(note, user, session)
        elif action == "edit":
            if not user:
                can_access = False
            else:
                can_access = NotePermissions.can_edit_note(note, user, session)
        elif action == "delete":
            if not user:
                can_access = False
            else:
                can_access = NotePermissions.can_delete_note(note, user, session)
        elif action == "manage_authors":
            if not user:
                can_access = False
            else:
                can_access = NotePermissions.can_manage_authors(note, user, session)
        else:
            raise ValueError(f"Unknown action: {action}")
        
        if not can_access:
            raise NoteAccessDeniedError(action)
        
        return note 