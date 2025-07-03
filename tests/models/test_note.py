import pytest
from datetime import datetime
from app.models.note import Note, NoteAuthor, NotePrivacy, NoteCreate, NoteUpdate
from pydantic import ValidationError

def test_note_creation():
    """Test basic note creation."""
    note = Note(
        title="Test Note",
        content="This is a test note content.",
        privacy=NotePrivacy.PRIVATE,
        created_by_user_id=1
    )
    
    assert note.title == "Test Note"
    assert note.content == "This is a test note content."
    assert note.privacy == NotePrivacy.PRIVATE
    assert note.created_by_user_id == 1
    assert note.deleted_at is None

def test_note_validation():
    """Test note validation via Pydantic models."""
    # SQLModel table classes don't enforce validation during instantiation,
    # so we test validation through the API models instead
    
    # Test that the Note can be created with valid data
    note = Note(
        title="Valid Title",
        content="Valid Content",
        created_by_user_id=1
    )
    assert note.title == "Valid Title"
    assert note.content == "Valid Content"
    
    # The actual validation is enforced at the API level through
    # NoteCreate and NoteUpdate models, which are tested separately

def test_note_privacy_enum():
    """Test note privacy enum values."""
    assert NotePrivacy.PRIVATE == "private"
    assert NotePrivacy.PUBLIC == "public"

def test_note_author_creation():
    """Test note author association creation."""
    note_author = NoteAuthor(
        note_id=1,
        user_id=2,
        added_by_user_id=1
    )
    
    assert note_author.note_id == 1
    assert note_author.user_id == 2
    assert note_author.added_by_user_id == 1
    assert isinstance(note_author.added_at, datetime)

def test_note_create_model():
    """Test NoteCreate pydantic model."""
    note_create = NoteCreate(
        title="Test Note",
        content="Test content",
        privacy=NotePrivacy.PUBLIC
    )
    
    assert note_create.title == "Test Note"
    assert note_create.content == "Test content"
    assert note_create.privacy == NotePrivacy.PUBLIC

def test_note_create_validation():
    """Test NoteCreate validation."""
    # Test empty title
    with pytest.raises(ValidationError):
        NoteCreate(
            title="",
            content="Content"
        )
    
    # Test empty content
    with pytest.raises(ValidationError):
        NoteCreate(
            title="Title",
            content=""
        )
    
    # Test whitespace-only title
    with pytest.raises(ValidationError):
        NoteCreate(
            title="   ",
            content="Content"
        )

def test_note_update_model():
    """Test NoteUpdate pydantic model."""
    note_update = NoteUpdate(
        title="Updated Title",
        privacy=NotePrivacy.PUBLIC
    )
    
    assert note_update.title == "Updated Title"
    assert note_update.content is None
    assert note_update.privacy == NotePrivacy.PUBLIC

def test_note_update_validation():
    """Test NoteUpdate validation."""
    # Test empty title (should fail)
    with pytest.raises(ValidationError):
        NoteUpdate(title="")
    
    # Test None values (should be allowed)
    note_update = NoteUpdate()
    assert note_update.title is None
    assert note_update.content is None
    assert note_update.privacy is None

def test_note_title_whitespace_handling():
    """Test that note title whitespace is properly handled."""
    note_create = NoteCreate(
        title="  Test Title  ",
        content="Content"
    )
    
    # Should be stripped
    assert note_create.title == "Test Title"

def test_note_content_whitespace_handling():
    """Test that note content whitespace is properly handled."""
    note_create = NoteCreate(
        title="Title",
        content="  Test Content  "
    )
    
    # Should be stripped
    assert note_create.content == "Test Content" 