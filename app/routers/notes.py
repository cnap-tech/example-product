from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.models.note import (
    NoteCreate, NoteRead, NoteUpdate, NotePrivacy, NotesListResponse,
    AddAuthorRequest, RemoveAuthorRequest, AuthorInfo
)
from app.models.user import User
from app.services import NoteService
from app.utils.exceptions import handle_service_exception
from app.dependencies.auth import require_auth, get_current_user_dep
from app.dependencies.database import DBSession

router = APIRouter()

@router.post("/notes", response_model=NoteRead)
async def create_note(
    note_create: NoteCreate,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Create a new note. The creator automatically becomes the first author.
    
    Args:
        note_create: Note creation data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        NoteRead: Created note with authors
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Convert to dict and create note
        note_data = note_create.model_dump()
        note = NoteService.create_note(note_data, current_user, session)
        
        # Get authors for the response
        authors = NoteService.get_note_authors(note.id, session)
        
        return NoteRead(
            id=note.id,
            title=note.title,
            content=note.content,
            privacy=note.privacy,
            created_at=note.created_at,
            updated_at=note.updated_at,
            created_by_user_id=note.created_by_user_id,
            authors=authors
        )
    except Exception as e:
        handle_service_exception(e)

@router.get("/notes", response_model=NotesListResponse)
async def list_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of notes to return"),
    privacy: Optional[NotePrivacy] = Query(None, description="Filter by privacy setting"),
    creator_id: Optional[int] = Query(None, description="Filter by creator ID"),
    current_user: Optional[User] = Depends(get_current_user_dep),
    session = DBSession
):
    """
    List notes with pagination and filtering.
    
    Public notes are visible to everyone, private notes only to authors.
    
    Args:
        skip: Number of notes to skip
        limit: Maximum number of notes to return
        privacy: Filter by privacy setting
        creator_id: Filter by creator ID
        current_user: Current authenticated user (optional)
        session: Database session
        
    Returns:
        NotesListResponse: Paginated list of notes
    """
    try:
        # If filtering by private and no user is authenticated, return empty result
        if privacy == NotePrivacy.PRIVATE and not current_user:
            return NotesListResponse(
                notes=[],
                total=0,
                page=1,
                per_page=limit,
                has_next=False,
                has_prev=False
            )
        
        notes_response = NoteService.list_notes(
            skip=skip,
            limit=limit,
            privacy_filter=privacy,
            creator_id=creator_id,
            session=session
        )
        
        # Filter out private notes that the user can't see
        if not current_user:
            # Only show public notes for unauthenticated users
            filtered_notes = [note for note in notes_response.notes if note.privacy == NotePrivacy.PUBLIC]
            notes_response.notes = filtered_notes
            notes_response.total = len(filtered_notes)
        
        return notes_response
    except Exception as e:
        handle_service_exception(e)

@router.get("/notes/my", response_model=NotesListResponse)
async def list_my_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of notes to return"),
    privacy: Optional[NotePrivacy] = Query(None, description="Filter by privacy setting"),
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    List notes where the current user is an author.
    
    Args:
        skip: Number of notes to skip
        limit: Maximum number of notes to return
        privacy: Filter by privacy setting
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        NotesListResponse: Paginated list of user's notes
    """
    try:
        return NoteService.list_user_notes(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            privacy_filter=privacy,
            session=session
        )
    except Exception as e:
        handle_service_exception(e)

@router.get("/notes/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: int,
    current_user: Optional[User] = Depends(get_current_user_dep),
    session = DBSession
):
    """
    Get a note by ID with access control.
    
    Args:
        note_id: ID of note to retrieve
        current_user: Current authenticated user (optional)
        session: Database session
        
    Returns:
        NoteRead: Note data with authors
        
    Raises:
        HTTPException: If note not found or access denied
    """
    try:
        # Check access and get note
        note = NoteService.check_note_access(note_id, current_user, "view", session)
        
        # Get authors for the response
        authors = NoteService.get_note_authors(note.id, session)
        
        return NoteRead(
            id=note.id,
            title=note.title,
            content=note.content,
            privacy=note.privacy,
            created_at=note.created_at,
            updated_at=note.updated_at,
            created_by_user_id=note.created_by_user_id,
            authors=authors
        )
    except Exception as e:
        handle_service_exception(e)

@router.put("/notes/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int,
    note_update: NoteUpdate,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Update a note. Only authors can edit notes.
    
    Args:
        note_id: ID of note to update
        note_update: Note update data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        NoteRead: Updated note data
        
    Raises:
        HTTPException: If note not found, access denied, or validation fails
    """
    try:
        # Check edit access
        NoteService.check_note_access(note_id, current_user, "edit", session)
        
        # Convert to dict and filter None values
        update_data = note_update.model_dump(exclude_unset=True)
        
        # Update note
        note = NoteService.update_note(note_id, update_data, session)
        
        # Get authors for the response
        authors = NoteService.get_note_authors(note.id, session)
        
        return NoteRead(
            id=note.id,
            title=note.title,
            content=note.content,
            privacy=note.privacy,
            created_at=note.created_at,
            updated_at=note.updated_at,
            created_by_user_id=note.created_by_user_id,
            authors=authors
        )
    except Exception as e:
        handle_service_exception(e)

@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    permanent: bool = Query(False, description="Whether to permanently delete the note"),
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Delete a note. Only the creator can delete notes.
    
    Args:
        note_id: ID of note to delete
        permanent: Whether to permanently delete the note
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If note not found or access denied
    """
    try:
        # Check delete access
        NoteService.check_note_access(note_id, current_user, "delete", session)
        
        # Delete note
        NoteService.delete_note(note_id, session, permanent)
        
        return {"detail": "Note deleted successfully"}
    except Exception as e:
        handle_service_exception(e)

@router.get("/notes/{note_id}/authors", response_model=List[AuthorInfo])
async def get_note_authors(
    note_id: int,
    current_user: Optional[User] = Depends(get_current_user_dep),
    session = DBSession
):
    """
    Get all authors of a note.
    
    Args:
        note_id: ID of note to get authors for
        current_user: Current authenticated user (optional)
        session: Database session
        
    Returns:
        List[AuthorInfo]: List of note authors
        
    Raises:
        HTTPException: If note not found or access denied
    """
    try:
        # Check view access
        NoteService.check_note_access(note_id, current_user, "view", session)
        
        # Get authors
        return NoteService.get_note_authors(note_id, session)
    except Exception as e:
        handle_service_exception(e)

@router.post("/notes/{note_id}/authors")
async def add_note_author(
    note_id: int,
    author_request: AddAuthorRequest,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Add an author to a note. Only existing authors can add new authors.
    
    Args:
        note_id: ID of note to add author to
        author_request: Author addition request
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If note not found, access denied, or user already an author
    """
    try:
        # Check author management access
        NoteService.check_note_access(note_id, current_user, "manage_authors", session)
        
        # Add author
        NoteService.add_author(note_id, author_request.user_id, current_user, session)
        
        return {"detail": "Author added successfully"}
    except Exception as e:
        handle_service_exception(e)

@router.delete("/notes/{note_id}/authors")
async def remove_note_author(
    note_id: int,
    author_request: RemoveAuthorRequest,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Remove an author from a note. Only existing authors can remove authors.
    
    Args:
        note_id: ID of note to remove author from
        author_request: Author removal request
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If note not found, access denied, or user not an author
    """
    try:
        # Check author management access
        NoteService.check_note_access(note_id, current_user, "manage_authors", session)
        
        # Remove author
        NoteService.remove_author(note_id, author_request.user_id, session)
        
        return {"detail": "Author removed successfully"}
    except Exception as e:
        handle_service_exception(e) 