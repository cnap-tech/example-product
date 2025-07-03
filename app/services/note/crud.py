"""
Note CRUD operations module.

Provides basic create, read, update, delete operations for notes.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_, or_, func
from app.models.note import Note, NoteAuthor, NotePrivacy, NoteListItem, NotesListResponse, AuthorInfo
from app.models.user import User
from .exceptions import NoteNotFoundError, NoteValidationError

class NoteCRUD:
    """CRUD operations for notes."""
    
    @staticmethod
    def create_note(note_data: Dict[str, Any], creator: User, session: Session) -> Note:
        """
        Create a new note with the creator as the first author.
        
        Args:
            note_data: Dictionary containing note creation data
            creator: User creating the note
            session: Database session
            
        Returns:
            Note: Created note instance
            
        Raises:
            NoteValidationError: If note data is invalid
        """
        try:
            # Create the note
            note = Note(
                title=note_data["title"],
                content=note_data["content"],
                privacy=note_data.get("privacy", NotePrivacy.PRIVATE),
                created_by_user_id=creator.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(note)
            session.flush()  # Get the note ID
            
            # Add creator as the first author
            note_author = NoteAuthor(
                note_id=note.id,
                user_id=creator.id,
                added_by_user_id=creator.id,
                added_at=datetime.utcnow()
            )
            
            session.add(note_author)
            session.commit()
            session.refresh(note)
            
            return note
            
        except Exception as e:
            session.rollback()
            raise NoteValidationError(f"Failed to create note: {str(e)}")
    
    @staticmethod
    def get_note_by_id(note_id: int, session: Session, include_deleted: bool = False) -> Note:
        """
        Get a note by its ID.
        
        Args:
            note_id: Note ID to retrieve
            session: Database session
            include_deleted: Whether to include soft-deleted notes
            
        Returns:
            Note: Note instance
            
        Raises:
            NoteNotFoundError: If note doesn't exist
        """
        conditions = [Note.id == note_id]
        if not include_deleted:
            conditions.append(Note.deleted_at.is_(None))
        
        statement = select(Note).where(and_(*conditions))
        note = session.exec(statement).first()
        
        if not note:
            raise NoteNotFoundError(note_id)
        
        return note
    
    @staticmethod
    def list_notes(
        skip: int = 0,
        limit: int = 10,
        privacy_filter: Optional[NotePrivacy] = None,
        creator_id: Optional[int] = None,
        session: Session = None
    ) -> NotesListResponse:
        """
        List notes with pagination and filtering.
        
        Args:
            skip: Number of notes to skip
            limit: Maximum number of notes to return
            privacy_filter: Filter by privacy setting
            creator_id: Filter by creator ID
            session: Database session
            
        Returns:
            NotesListResponse: Paginated list of notes
        """
        conditions = [Note.deleted_at.is_(None)]
        
        if privacy_filter:
            conditions.append(Note.privacy == privacy_filter)
        
        if creator_id:
            conditions.append(Note.created_by_user_id == creator_id)
        
        # Get total count
        count_statement = select(func.count(Note.id)).where(and_(*conditions))
        total = session.exec(count_statement).one()
        
        # Get notes with pagination
        statement = (
            select(Note)
            .where(and_(*conditions))
            .order_by(Note.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        notes = session.exec(statement).all()
        
        # Convert to list items with author count
        note_items = []
        for note in notes:
            # Count authors for this note
            author_count_stmt = select(func.count(NoteAuthor.user_id)).where(NoteAuthor.note_id == note.id)
            authors_count = session.exec(author_count_stmt).one()
            
            note_item = NoteListItem(
                id=note.id,
                title=note.title,
                privacy=note.privacy,
                created_at=note.created_at,
                updated_at=note.updated_at,
                created_by_user_id=note.created_by_user_id,
                authors_count=authors_count,
                content_preview=note.content[:100] + "..." if len(note.content) > 100 else note.content
            )
            note_items.append(note_item)
        
        page = (skip // limit) + 1
        per_page = limit
        has_next = skip + limit < total
        has_prev = skip > 0
        
        return NotesListResponse(
            notes=note_items,
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
    
    @staticmethod
    def list_user_notes(
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        privacy_filter: Optional[NotePrivacy] = None,
        session: Session = None
    ) -> NotesListResponse:
        """
        List notes where the user is an author.
        
        Args:
            user_id: User ID to filter by
            skip: Number of notes to skip
            limit: Maximum number of notes to return
            privacy_filter: Filter by privacy setting
            session: Database session
            
        Returns:
            NotesListResponse: Paginated list of user's notes
        """
        # Join Note with NoteAuthor to find notes where user is an author
        conditions = [
            Note.deleted_at.is_(None),
            NoteAuthor.user_id == user_id
        ]
        
        if privacy_filter:
            conditions.append(Note.privacy == privacy_filter)
        
        # Get total count
        count_statement = (
            select(func.count(Note.id.distinct()))
            .select_from(Note)
            .join(NoteAuthor, Note.id == NoteAuthor.note_id)
            .where(and_(*conditions))
        )
        total = session.exec(count_statement).one()
        
        # Get notes with pagination
        statement = (
            select(Note)
            .join(NoteAuthor, Note.id == NoteAuthor.note_id)
            .where(and_(*conditions))
            .order_by(Note.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        notes = session.exec(statement).all()
        
        # Convert to list items with author count
        note_items = []
        for note in notes:
            # Count authors for this note
            author_count_stmt = select(func.count(NoteAuthor.user_id)).where(NoteAuthor.note_id == note.id)
            authors_count = session.exec(author_count_stmt).one()
            
            note_item = NoteListItem(
                id=note.id,
                title=note.title,
                privacy=note.privacy,
                created_at=note.created_at,
                updated_at=note.updated_at,
                created_by_user_id=note.created_by_user_id,
                authors_count=authors_count,
                content_preview=note.content[:100] + "..." if len(note.content) > 100 else note.content
            )
            note_items.append(note_item)
        
        page = (skip // limit) + 1
        per_page = limit
        has_next = skip + limit < total
        has_prev = skip > 0
        
        return NotesListResponse(
            notes=note_items,
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
    
    @staticmethod
    def update_note(note_id: int, update_data: Dict[str, Any], session: Session) -> Note:
        """
        Update an existing note.
        
        Args:
            note_id: Note ID to update
            update_data: Dictionary containing update data
            session: Database session
            
        Returns:
            Note: Updated note instance
            
        Raises:
            NoteNotFoundError: If note doesn't exist
            NoteValidationError: If update data is invalid
        """
        try:
            note = NoteCRUD.get_note_by_id(note_id, session)
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(note, field) and value is not None:
                    setattr(note, field, value)
            
            note.updated_at = datetime.utcnow()
            
            session.add(note)
            session.commit()
            session.refresh(note)
            
            return note
            
        except NoteNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            raise NoteValidationError(f"Failed to update note: {str(e)}")
    
    @staticmethod
    def delete_note(note_id: int, session: Session, permanent: bool = False) -> None:
        """
        Delete a note (soft or permanent).
        
        Args:
            note_id: Note ID to delete
            session: Database session
            permanent: Whether to permanently delete the note
            
        Raises:
            NoteNotFoundError: If note doesn't exist
        """
        try:
            note = NoteCRUD.get_note_by_id(note_id, session)
            
            if permanent:
                # Delete all note_author relationships first
                delete_authors_stmt = select(NoteAuthor).where(NoteAuthor.note_id == note_id)
                note_authors = session.exec(delete_authors_stmt).all()
                for author in note_authors:
                    session.delete(author)
                
                # Delete the note
                session.delete(note)
            else:
                # Soft delete
                note.deleted_at = datetime.utcnow()
                session.add(note)
            
            session.commit()
            
        except NoteNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            raise NoteValidationError(f"Failed to delete note: {str(e)}") 