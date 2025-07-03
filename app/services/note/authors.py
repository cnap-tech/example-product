"""
Note authors management module.

Handles adding, removing, and listing authors for notes.
"""

from datetime import datetime
from typing import List
from sqlmodel import Session, select
from app.models.note import Note, NoteAuthor, AuthorInfo
from app.models.user import User
from app.services.user import UserService
from .exceptions import AuthorNotFoundError, AuthorAlreadyExistsError, NoteValidationError
from .crud import NoteCRUD

class NoteAuthors:
    """Author management for notes."""
    
    @staticmethod
    def add_author(note_id: int, user_id: int, added_by_user: User, session: Session) -> None:
        """
        Add an author to a note.
        
        Args:
            note_id: Note ID to add author to
            user_id: User ID to add as author
            added_by_user: User who is adding the author
            session: Database session
            
        Raises:
            NoteNotFoundError: If note doesn't exist
            UserNotFoundError: If user doesn't exist
            AuthorAlreadyExistsError: If user is already an author
            NoteValidationError: If operation fails
        """
        try:
            # Verify note exists
            note = NoteCRUD.get_note_by_id(note_id, session)
            
            # Verify user exists
            user = UserService.get_user_by_id(user_id, session)
            
            # Check if user is already an author
            existing_author = session.exec(
                select(NoteAuthor).where(
                    NoteAuthor.note_id == note_id,
                    NoteAuthor.user_id == user_id
                )
            ).first()
            
            if existing_author:
                raise AuthorAlreadyExistsError(user_id, note_id)
            
            # Add the author
            note_author = NoteAuthor(
                note_id=note_id,
                user_id=user_id,
                added_by_user_id=added_by_user.id,
                added_at=datetime.utcnow()
            )
            
            session.add(note_author)
            session.commit()
            
        except (AuthorAlreadyExistsError, NoteValidationError):
            raise
        except Exception as e:
            session.rollback()
            raise NoteValidationError(f"Failed to add author: {str(e)}")
    
    @staticmethod
    def remove_author(note_id: int, user_id: int, session: Session) -> None:
        """
        Remove an author from a note.
        
        Args:
            note_id: Note ID to remove author from
            user_id: User ID to remove as author
            session: Database session
            
        Raises:
            NoteNotFoundError: If note doesn't exist
            AuthorNotFoundError: If user is not an author
            NoteValidationError: If operation fails
        """
        try:
            # Verify note exists
            note = NoteCRUD.get_note_by_id(note_id, session)
            
            # Find the author relationship
            author_relationship = session.exec(
                select(NoteAuthor).where(
                    NoteAuthor.note_id == note_id,
                    NoteAuthor.user_id == user_id
                )
            ).first()
            
            if not author_relationship:
                raise AuthorNotFoundError(user_id, note_id)
            
            # Check if this is the last author (creator can't be removed if they're the only author)
            author_count = session.exec(
                select(NoteAuthor).where(NoteAuthor.note_id == note_id)
            ).all()
            
            if len(author_count) == 1:
                raise NoteValidationError("Cannot remove the last author from a note")
            
            # Remove the author
            session.delete(author_relationship)
            session.commit()
            
        except (AuthorNotFoundError, NoteValidationError):
            raise
        except Exception as e:
            session.rollback()
            raise NoteValidationError(f"Failed to remove author: {str(e)}")
    
    @staticmethod
    def get_note_authors(note_id: int, session: Session) -> List[AuthorInfo]:
        """
        Get all authors for a note.
        
        Args:
            note_id: Note ID to get authors for
            session: Database session
            
        Returns:
            List[AuthorInfo]: List of authors with their information
            
        Raises:
            NoteNotFoundError: If note doesn't exist
        """
        # Verify note exists
        note = NoteCRUD.get_note_by_id(note_id, session)
        
        # Get authors with user information
        statement = (
            select(User, NoteAuthor)
            .join(NoteAuthor, User.id == NoteAuthor.user_id)
            .where(NoteAuthor.note_id == note_id)
            .order_by(NoteAuthor.added_at)
        )
        
        results = session.exec(statement).all()
        
        authors = []
        for user, note_author in results:
            author_info = AuthorInfo(
                id=user.id,
                username=user.username,
                name=user.name,
                added_at=note_author.added_at
            )
            authors.append(author_info)
        
        return authors
    
    @staticmethod
    def is_user_author(note_id: int, user_id: int, session: Session) -> bool:
        """
        Check if a user is an author of a note.
        
        Args:
            note_id: Note ID to check
            user_id: User ID to check
            session: Database session
            
        Returns:
            bool: True if user is an author
        """
        author_relationship = session.exec(
            select(NoteAuthor).where(
                NoteAuthor.note_id == note_id,
                NoteAuthor.user_id == user_id
            )
        ).first()
        
        return author_relationship is not None
    
    @staticmethod
    def get_author_count(note_id: int, session: Session) -> int:
        """
        Get the number of authors for a note.
        
        Args:
            note_id: Note ID to count authors for
            session: Database session
            
        Returns:
            int: Number of authors
        """
        from sqlmodel import func
        
        count_statement = select(func.count(NoteAuthor.user_id)).where(NoteAuthor.note_id == note_id)
        return session.exec(count_statement).one()
    
    @staticmethod
    def transfer_ownership(note_id: int, new_creator_id: int, current_user: User, session: Session) -> None:
        """
        Transfer ownership of a note to another author.
        
        Args:
            note_id: Note ID to transfer ownership of
            new_creator_id: User ID of the new creator
            current_user: User performing the transfer (must be current creator or admin)
            session: Database session
            
        Raises:
            NoteNotFoundError: If note doesn't exist
            AuthorNotFoundError: If new creator is not an author
            NoteAccessDeniedError: If current user can't transfer ownership
            NoteValidationError: If operation fails
        """
        try:
            # Get the note
            note = NoteCRUD.get_note_by_id(note_id, session)
            
            # Check if current user can transfer ownership (must be creator or admin)
            from app.models.user import UserRole
            if note.created_by_user_id != current_user.id and current_user.role != UserRole.ADMIN:
                from .exceptions import NoteAccessDeniedError
                raise NoteAccessDeniedError("transfer ownership of")
            
            # Check if new creator is an author
            if not NoteAuthors.is_user_author(note_id, new_creator_id, session):
                raise AuthorNotFoundError(new_creator_id, note_id)
            
            # Transfer ownership
            note.created_by_user_id = new_creator_id
            note.updated_at = datetime.utcnow()
            
            session.add(note)
            session.commit()
            
        except Exception as e:
            session.rollback()
            if isinstance(e, (AuthorNotFoundError, NoteValidationError)):
                raise
            raise NoteValidationError(f"Failed to transfer ownership: {str(e)}") 