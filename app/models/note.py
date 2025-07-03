from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import field_validator
import sqlalchemy as sa

class NotePrivacy(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"

class NoteAuthor(SQLModel, table=True):
    """
    Association table for many-to-many relationship between Notes and Users (authors).
    """
    # Composite primary key
    note_id: int = Field(foreign_key="note.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    
    # Metadata about authorship
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by_user_id: int = Field(foreign_key="user.id", description="User who added this author to the note")

class Note(SQLModel, table=True):
    """
    Note model for text-based notes with multiple authors.
    
    Features:
    - Multiple authors (many-to-many with User)
    - Privacy control (private/public)
    - Text content
    - Creation/modification tracking
    """
    
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Note content
    title: str = Field(max_length=255, description="Note title", min_length=1)
    content: str = Field(description="Note text content", min_length=1)
    
    # Privacy settings  
    privacy: NotePrivacy = Field(
        default=NotePrivacy.PRIVATE,
        sa_column=sa.Column(sa.Enum(NotePrivacy, values_callable=lambda obj: [e.value for e in obj]))
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Soft delete
    deleted_at: Optional[datetime] = None
    
    # Creator tracking
    created_by_user_id: int = Field(foreign_key="user.id", description="User who created the note")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        if len(v.strip()) > 255:
            raise ValueError("Title must be 255 characters or less")
        return v.strip()
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

# Pydantic models for API requests/responses

class NoteCreate(SQLModel):
    """Model for creating a new note"""
    title: str
    content: str
    privacy: NotePrivacy = NotePrivacy.PRIVATE
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        if len(v.strip()) > 255:
            raise ValueError("Title must be 255 characters or less")
        return v.strip()
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

class NoteUpdate(SQLModel):
    """Model for updating a note"""
    title: Optional[str] = None
    content: Optional[str] = None
    privacy: Optional[NotePrivacy] = None
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Title cannot be empty")
            if len(v.strip()) > 255:
                raise ValueError("Title must be 255 characters or less")
            return v.strip()
        return v
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Content cannot be empty")
            return v.strip()
        return v

class AuthorInfo(SQLModel):
    """Model for author information in note responses"""
    id: int
    username: str
    name: str
    added_at: datetime

class NoteRead(SQLModel):
    """Model for reading note data"""
    id: int
    title: str
    content: str
    privacy: NotePrivacy
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    authors: List[AuthorInfo] = []

class NoteListItem(SQLModel):
    """Model for note list items (without full content)"""
    id: int
    title: str
    privacy: NotePrivacy
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    authors_count: int
    content_preview: str  # First 100 characters of content

class NotesListResponse(SQLModel):
    """Model for paginated notes list"""
    notes: List[NoteListItem]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class AddAuthorRequest(SQLModel):
    """Model for adding an author to a note"""
    user_id: int
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError("User ID must be positive")
        return v

class RemoveAuthorRequest(SQLModel):
    """Model for removing an author from a note"""
    user_id: int
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError("User ID must be positive")
        return v 