import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from tests.conftest import create_test_user, TestUserFactory
from app.models.note import NotePrivacy
from app.utils.auth import create_access_token

# Test client
client = TestClient(app)

def test_create_note(session: Session):
    """Test note creation."""
    user = create_test_user(session, "test@example.com", "testuser", "Test User")
    
    # Login to get token
    login_response = client.post("/api/v1/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Create note
    note_data = {
        "title": "Test Note",
        "content": "This is a test note content.",
        "privacy": "private"
    }
    
    response = client.post("/api/v1/notes", 
                         json=note_data,
                         headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    note = response.json()
    assert note["title"] == "Test Note"
    assert note["content"] == "This is a test note content."
    assert note["privacy"] == "private"
    assert note["created_by_user_id"] == user.id
    assert len(note["authors"]) == 1
    assert note["authors"][0]["id"] == user.id

def test_create_note_unauthorized():
    """Test note creation without authentication."""
    note_data = {
        "title": "Test Note",
        "content": "This is a test note content."
    }
    
    response = client.post("/api/v1/notes", json=note_data)
    assert response.status_code == 401

def test_create_note_validation_error(session: Session):
    """Test note creation with validation errors."""
    user = create_test_user(session, "test2@example.com", "testuser2", "Test User 2")
    
    # Login to get token
    login_response = client.post("/api/v1/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    token = login_response.json()["access_token"]
    
    # Test empty title
    response = client.post("/api/v1/notes", 
                         json={"title": "", "content": "Content"},
                         headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422

def test_list_notes_public(session: Session):
    """Test listing public notes without authentication."""
    # Create a public note first
    user = create_test_user(session, "test3@example.com", "testuser3", "Test User 3")
    
    # Login to get token
    login_response = client.post("/api/v1/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    token = login_response.json()["access_token"]
    
    # Create public note
    note_data = {
        "title": "Public Note",
        "content": "This is a public note.",
        "privacy": "public"
    }
    
    create_response = client.post("/api/v1/notes", 
                                 json=note_data,
                                 headers={"Authorization": f"Bearer {token}"})
    assert create_response.status_code == 200
    
    # List notes without authentication (should only see public notes)
    response = client.get("/api/v1/notes")
    assert response.status_code == 200
    
    notes_data = response.json()
    assert "notes" in notes_data
    # Should contain at least the public note we created
    public_notes = [note for note in notes_data["notes"] if note["privacy"] == "public"]
    assert len(public_notes) >= 1

def test_get_note_access_control(session: Session):
    """Test note access control for get endpoint."""
    user = create_test_user(session, "test4@example.com", "testuser4", "Test User 4")
    
    # Login to get token
    login_response = client.post("/api/v1/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    token = login_response.json()["access_token"]
    
    # Create private note
    note_data = {
        "title": "Private Note",
        "content": "This is a private note.",
        "privacy": "private"
    }
    
    create_response = client.post("/api/v1/notes", 
                                 json=note_data,
                                 headers={"Authorization": f"Bearer {token}"})
    note_id = create_response.json()["id"]
    
    # Access as author (should work)
    response = client.get(f"/api/v1/notes/{note_id}",
                         headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Access without authentication (should fail for private note)
    response = client.get(f"/api/v1/notes/{note_id}")
    assert response.status_code == 403

def test_update_note(session: Session):
    """Test note update."""
    user = create_test_user(session, "test5@example.com", "testuser5", "Test User 5")
    
    # Login to get token
    login_response = client.post("/api/v1/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    token = login_response.json()["access_token"]
    
    # Create note
    note_data = {
        "title": "Original Title",
        "content": "Original content.",
        "privacy": "private"
    }
    
    create_response = client.post("/api/v1/notes", 
                                 json=note_data,
                                 headers={"Authorization": f"Bearer {token}"})
    note_id = create_response.json()["id"]
    
    # Update note
    update_data = {
        "title": "Updated Title",
        "privacy": "public"
    }
    
    response = client.put(f"/api/v1/notes/{note_id}",
                         json=update_data,
                         headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    updated_note = response.json()
    assert updated_note["title"] == "Updated Title"
    assert updated_note["content"] == "Original content."  # Should remain unchanged
    assert updated_note["privacy"] == "public"

def test_delete_note(session: Session):
    """Test note deletion."""
    user = create_test_user(session, "test6@example.com", "testuser6", "Test User 6")
    
    # Login to get token
    login_response = client.post("/api/v1/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    token = login_response.json()["access_token"]
    
    # Create note
    note_data = {
        "title": "Note to Delete",
        "content": "This note will be deleted.",
        "privacy": "private"
    }
    
    create_response = client.post("/api/v1/notes", 
                                 json=note_data,
                                 headers={"Authorization": f"Bearer {token}"})
    note_id = create_response.json()["id"]
    
    # Delete note
    response = client.delete(f"/api/v1/notes/{note_id}",
                            headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    assert response.json()["detail"] == "Note deleted successfully"
    
    # Try to access deleted note (should fail)
    response = client.get(f"/api/v1/notes/{note_id}",
                         headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_list_my_notes(session: Session):
    """Test listing user's own notes."""
    user = create_test_user(session, "test7@example.com", "testuser7", "Test User 7")
    
    # Login to get token
    login_response = client.post("/api/v1/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    token = login_response.json()["access_token"]
    
    # Create a note
    note_data = {
        "title": "My Note",
        "content": "This is my note.",
        "privacy": "private"
    }
    
    client.post("/api/v1/notes", 
               json=note_data,
               headers={"Authorization": f"Bearer {token}"})
    
    # List my notes
    response = client.get("/api/v1/notes/my",
                         headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    notes_data = response.json()
    assert "notes" in notes_data
    assert len(notes_data["notes"]) >= 1
    # Should contain the note we just created
    note_titles = [note["title"] for note in notes_data["notes"]]
    assert "My Note" in note_titles


class TestConcurrentAccess:
    """Test concurrent access scenarios that could cause data corruption."""
    
    def test_concurrent_note_editing(self, session: Session):
        """Test multiple users editing same note simultaneously."""
        # Setup: Create note with multiple authors
        user1 = TestUserFactory.create_test_user(session, "concurrent1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "concurrent2@test.com", "user2")
        
        # Create tokens
        token1 = create_access_token(data={"sub": str(user1.id)})
        token2 = create_access_token(data={"sub": str(user2.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create note by user1
        note_data = {
            "title": "Concurrent Test Note",
            "content": "Initial content",
            "privacy": "private"
        }
        response = client.post("/api/v1/notes", json=note_data, headers=headers1)
        assert response.status_code == 200
        note_id = response.json()["id"]
        
        # Add user2 as author
        response = client.post(f"/api/v1/notes/{note_id}/authors",
                             json={"user_id": user2.id},
                             headers=headers1)
        assert response.status_code == 200
        
        # Define concurrent edit functions
        def edit_note_user1():
            return client.put(f"/api/v1/notes/{note_id}",
                            json={"content": "User 1 edited this content"},
                            headers=headers1)
        
        def edit_note_user2():
            return client.put(f"/api/v1/notes/{note_id}",
                            json={"content": "User 2 edited this content"},
                            headers=headers2)
        
        # Execute concurrent edits
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(edit_note_user1)
            future2 = executor.submit(edit_note_user2)
            
            response1 = future1.result()
            response2 = future2.result()
        
        # Both requests should succeed (last write wins)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify final state is consistent
        final_response = client.get(f"/api/v1/notes/{note_id}", headers=headers1)
        assert final_response.status_code == 200
        final_note = final_response.json()
        
        # Content should be from one of the users (last write wins)
        assert final_note["content"] in ["User 1 edited this content", "User 2 edited this content"]
    
    def test_concurrent_author_management(self, session: Session):
        """Test adding/removing authors while note is being edited."""
        # Setup users
        owner = TestUserFactory.create_test_user(session, "owner@test.com", "owner")
        user1 = TestUserFactory.create_test_user(session, "author1@test.com", "author1")
        user2 = TestUserFactory.create_test_user(session, "author2@test.com", "author2")
        
        owner_token = create_access_token(data={"sub": str(owner.id)})
        user1_token = create_access_token(data={"sub": str(user1.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # Create note
        note_data = {"title": "Author Management Test", "content": "Initial", "privacy": "private"}
        response = client.post("/api/v1/notes", json=note_data, headers=owner_headers)
        note_id = response.json()["id"]
        
        # Add user1 as author initially
        response = client.post(f"/api/v1/notes/{note_id}/authors",
                             json={"user_id": user1.id}, headers=owner_headers)
        assert response.status_code == 200
        
        # Define concurrent operations
        def add_author():
            return client.post(f"/api/v1/notes/{note_id}/authors",
                             json={"user_id": user2.id}, headers=owner_headers)
        
        def edit_note():
            return client.put(f"/api/v1/notes/{note_id}",
                            json={"content": "Edited during author management"},
                            headers=user1_headers)
        
        def remove_author():
            # Small delay to ensure add happens first
            time.sleep(0.1)
            return client.delete(f"/api/v1/notes/{note_id}/authors/{user2.id}",
                               headers=owner_headers)
        
        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(add_author),
                executor.submit(edit_note),
                executor.submit(remove_author)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        # Verify system remains consistent
        final_response = client.get(f"/api/v1/notes/{note_id}", headers=owner_headers)
        assert final_response.status_code == 200
        
        # Check authors list is consistent
        authors_response = client.get(f"/api/v1/notes/{note_id}/authors", headers=owner_headers)
        assert authors_response.status_code == 200
        authors = authors_response.json()
        
        # Should have at least owner and user1
        author_ids = [author["id"] for author in authors]
        assert owner.id in author_ids
        assert user1.id in author_ids


class TestLargeDataHandling:
    """Test handling of large data that could cause memory or performance issues."""
    
    def test_large_note_content(self, session: Session):
        """Test notes with very large content (>1MB)."""
        user = TestUserFactory.create_test_user(session, "largedata@test.com", "largeuser")
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create large content (1MB+)
        large_content = "A" * (1024 * 1024 + 1000)  # ~1MB
        
        note_data = {
            "title": "Large Content Test",
            "content": large_content,
            "privacy": "private"
        }
        
        # This should either succeed or fail gracefully with proper error
        response = client.post("/api/v1/notes", json=note_data, headers=headers)
        
        if response.status_code == 200:
            # If it succeeds, verify we can retrieve it
            note_id = response.json()["id"]
            get_response = client.get(f"/api/v1/notes/{note_id}", headers=headers)
            assert get_response.status_code == 200
            retrieved_note = get_response.json()
            assert len(retrieved_note["content"]) > 1000000
        elif response.status_code == 413:
            # Content too large - acceptable response
            assert "too large" in response.json().get("detail", "").lower()
        elif response.status_code == 422:
            # Validation error - acceptable if there are size limits
            assert True
        else:
            # Should not return 500 or other error codes
            assert False, f"Unexpected status code: {response.status_code}"
    
    def test_many_authors_on_note(self, session: Session):
        """Test note with many authors (50+)."""
        # Create owner
        owner = TestUserFactory.create_test_user(session, "manyauthors@test.com", "owner")
        owner_token = create_access_token(data={"sub": str(owner.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Create note
        note_data = {"title": "Many Authors Test", "content": "Content", "privacy": "private"}
        response = client.post("/api/v1/notes", json=note_data, headers=owner_headers)
        assert response.status_code == 200
        note_id = response.json()["id"]
        
        # Create 50 users and add them as authors
        author_ids = []
        for i in range(50):
            user = TestUserFactory.create_test_user(session, f"author{i}@test.com", f"author{i}")
            author_ids.append(user.id)
            
            # Add as author
            response = client.post(f"/api/v1/notes/{note_id}/authors",
                                 json={"user_id": user.id},
                                 headers=owner_headers)
            
            # Should succeed or fail gracefully
            assert response.status_code in [200, 400, 413, 422], \
                f"Unexpected status for author {i}: {response.status_code}"
            
            if response.status_code != 200:
                # If it fails, it should be due to limits, not crashes
                break
        
        # Verify we can still retrieve the note and authors
        note_response = client.get(f"/api/v1/notes/{note_id}", headers=owner_headers)
        assert note_response.status_code == 200
        
        authors_response = client.get(f"/api/v1/notes/{note_id}/authors", headers=owner_headers)
        assert authors_response.status_code == 200
        authors = authors_response.json()
        
        # Should have at least the owner
        assert len(authors) >= 1 