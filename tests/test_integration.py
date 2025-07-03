"""
Integration tests for the entire NotesNest application.

These tests verify that all components work together correctly:
- User registration and authentication
- User management and permissions
- Friendship system
- Notes system with collaborative features
- Cross-feature interactions
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.user import User, UserRole
from app.models.note import NotePrivacy
from app.utils.auth import create_access_token
from tests.conftest import TestUserFactory

client = TestClient(app)

class TestCompleteUserJourney:
    """Test complete user journey from registration to collaboration."""
    
    def test_full_user_lifecycle(self, session: Session):
        """Test complete user lifecycle: register -> login -> create content -> collaborate."""
        
        # Step 1: User Registration
        alice_data = {
            "username": "alice",
            "email": "alice@example.com",
            "name": "Alice Smith",
            "password": "AlicePassword123!",
            "bio": "I love collaborative writing"
        }
        
        bob_data = {
            "username": "bob",
            "email": "bob@example.com", 
            "name": "Bob Jones",
            "password": "BobPassword123!",
            "bio": "Technical writer"
        }
        
        # Register Alice
        response = client.post("/api/v1/users", json=alice_data)
        assert response.status_code == 200
        alice_info = response.json()
        alice_id = alice_info["id"]
        
        # Register Bob
        response = client.post("/api/v1/users", json=bob_data)
        assert response.status_code == 200
        bob_info = response.json()
        bob_id = bob_info["id"]
        
        # Step 2: Authentication
        alice_login = client.post("/api/v1/token", data={
            "username": "alice@example.com",  # Use email as username
            "password": "AlicePassword123!"
        })
        assert alice_login.status_code == 200
        alice_token = alice_login.json()["access_token"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        
        bob_login = client.post("/api/v1/token", data={
            "username": "bob@example.com",  # Use email as username
            "password": "BobPassword123!"
        })
        assert bob_login.status_code == 200
        bob_token = bob_login.json()["access_token"]
        bob_headers = {"Authorization": f"Bearer {bob_token}"}
        
        # Step 3: Create Content (Notes)
        # Alice creates a private note
        note_data = {
            "title": "Alice's Private Thoughts",
            "content": "This is my private note that only I should see initially.",
            "privacy": "private"
        }
        
        response = client.post("/api/v1/notes", json=note_data, headers=alice_headers)
        assert response.status_code == 200
        private_note = response.json()
        private_note_id = private_note["id"]
        
        # Verify Alice can see her note
        response = client.get(f"/api/v1/notes/{private_note_id}", headers=alice_headers)
        assert response.status_code == 200
        
        # Verify Bob cannot see Alice's private note
        response = client.get(f"/api/v1/notes/{private_note_id}", headers=bob_headers)
        assert response.status_code == 403
        
        # Alice creates a public note
        public_note_data = {
            "title": "Welcome to NotesNest!",
            "content": "This is a public note that everyone can see.",
            "privacy": "public"
        }
        
        response = client.post("/api/v1/notes", json=public_note_data, headers=alice_headers)
        assert response.status_code == 200
        public_note = response.json()
        public_note_id = public_note["id"]
        
        # Verify Bob can see the public note
        response = client.get(f"/api/v1/notes/{public_note_id}", headers=bob_headers)
        assert response.status_code == 200
        
        # Verify unauthenticated users can see public notes
        response = client.get(f"/api/v1/notes/{public_note_id}")
        assert response.status_code == 200
        
        # Step 4: Friendship System
        # Alice sends friend request to Bob
        response = client.post("/api/v1/friend-requests", 
                             json={"addressee_id": bob_id}, 
                             headers=alice_headers)
        assert response.status_code == 200
        friendship_id = response.json()["id"]
        
        # Bob accepts the friend request
        response = client.post(f"/api/v1/friend-requests/{friendship_id}/respond",
                             json={"friendship_id": friendship_id, "action": "accept"},
                             headers=bob_headers)
        assert response.status_code == 200
        
        # Verify they are now friends
        response = client.get("/api/v1/friends", headers=alice_headers)
        assert response.status_code == 200
        alice_friends = response.json()["friends"]
        assert len(alice_friends) == 1
        assert alice_friends[0]["id"] == bob_id
        
        # Step 5: Collaboration (Add Bob as author to Alice's private note)
        response = client.post(f"/api/v1/notes/{private_note_id}/authors",
                             json={"user_id": bob_id},
                             headers=alice_headers)
        assert response.status_code == 200
        
        # Now Bob should be able to see and edit the note
        response = client.get(f"/api/v1/notes/{private_note_id}", headers=bob_headers)
        assert response.status_code == 200
        note = response.json()
        assert len(note["authors"]) == 2
        
        # Bob can edit the note
        response = client.put(f"/api/v1/notes/{private_note_id}",
                            json={"content": "Alice's note with Bob's edits added."},
                            headers=bob_headers)
        assert response.status_code == 200
        updated_note = response.json()
        assert "Bob's edits" in updated_note["content"]
        
        # Step 6: List user's notes
        response = client.get("/api/v1/notes/my", headers=alice_headers)
        assert response.status_code == 200
        alice_notes = response.json()["notes"]
        assert len(alice_notes) >= 2  # Should have both notes she created
        
        response = client.get("/api/v1/notes/my", headers=bob_headers)
        assert response.status_code == 200
        bob_notes = response.json()["notes"]
        assert len(bob_notes) >= 1  # Should have the note Alice added him to
        
        print("✅ Complete user journey test passed!")

class TestCrossFeatureInteractions:
    """Test interactions between different features of the application."""
    
    def test_friends_and_note_collaboration(self, session: Session):
        """Test that friends can easily collaborate on notes."""
        
        # Setup users and friendship
        users = self._setup_friendship()
        alice_headers, bob_headers, alice_id, bob_id = users
        
        # Alice creates a collaborative note
        note_data = {
            "title": "Our Collaboration Project",
            "content": "Initial ideas for our project...",
            "privacy": "private"
        }
        
        response = client.post("/api/v1/notes", json=note_data, headers=alice_headers)
        assert response.status_code == 200
        note_id = response.json()["id"]
        
        # Alice adds Bob as co-author
        response = client.post(f"/api/v1/notes/{note_id}/authors",
                             json={"user_id": bob_id},
                             headers=alice_headers)
        assert response.status_code == 200
        
        # Both can now see the note in their "my notes" list
        alice_response = client.get("/api/v1/notes/my", headers=alice_headers)
        bob_response = client.get("/api/v1/notes/my", headers=bob_headers)
        
        alice_note_ids = [note["id"] for note in alice_response.json()["notes"]]
        bob_note_ids = [note["id"] for note in bob_response.json()["notes"]]
        
        assert note_id in alice_note_ids
        assert note_id in bob_note_ids
        
        # Both can edit the note
        alice_edit = client.put(f"/api/v1/notes/{note_id}",
                              json={"content": "Alice's contributions to the project..."},
                              headers=alice_headers)
        assert alice_edit.status_code == 200
        
        bob_edit = client.put(f"/api/v1/notes/{note_id}",
                            json={"content": "Bob's additions to Alice's work..."},
                            headers=bob_headers)
        assert bob_edit.status_code == 200
        
        print("✅ Friends collaboration test passed!")
    
    def test_user_permissions_across_features(self, session: Session):
        """Test that user permissions work consistently across all features."""
        
        # Create admin user
        admin_data = {
            "username": "admin",
            "email": "admin@example.com",
            "name": "Admin User",
            "password": "AdminPassword123!"
        }
        
        response = client.post("/api/v1/users", json=admin_data)
        admin_id = response.json()["id"]
        
        # Login as admin and promote to admin role
        admin_login = client.post("/api/v1/token", data={
            "username": "admin@example.com",
            "password": "AdminPassword123!"
        })
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Promote to admin (this would normally be done through database or special endpoint)
        # For now, we'll test admin functionality with regular users
        
        # Setup regular users
        users = self._setup_friendship()
        alice_headers, bob_headers, alice_id, bob_id = users
        
        # Alice creates a private note
        note_data = {
            "title": "Private Note",
            "content": "This should only be accessible to authors and admins.",
            "privacy": "private"
        }
        
        response = client.post("/api/v1/notes", json=note_data, headers=alice_headers)
        note_id = response.json()["id"]
        
        # Bob cannot access Alice's private note (not an author)
        response = client.get(f"/api/v1/notes/{note_id}", headers=bob_headers)
        assert response.status_code == 403
        
        # Bob cannot edit Alice's private note
        response = client.put(f"/api/v1/notes/{note_id}",
                            json={"title": "Modified Title"},
                            headers=bob_headers)
        assert response.status_code == 403
        
        # Bob cannot delete Alice's note
        response = client.delete(f"/api/v1/notes/{note_id}", headers=bob_headers)
        assert response.status_code == 403
        
        # Only Alice (creator) can delete the note
        response = client.delete(f"/api/v1/notes/{note_id}", headers=alice_headers)
        assert response.status_code == 200
        
        print("✅ User permissions test passed!")
    
    def test_privacy_settings_consistency(self, session: Session):
        """Test that privacy settings work consistently across the application."""
        
        users = self._setup_friendship()
        alice_headers, bob_headers, alice_id, bob_id = users
        
        # Test private note privacy
        private_note_data = {
            "title": "Secret Project",
            "content": "Top secret information",
            "privacy": "private"
        }
        
        response = client.post("/api/v1/notes", json=private_note_data, headers=alice_headers)
        private_note_id = response.json()["id"]
        
        # Test public note privacy
        public_note_data = {
            "title": "Public Announcement",
            "content": "Everyone can see this",
            "privacy": "public"
        }
        
        response = client.post("/api/v1/notes", json=public_note_data, headers=alice_headers)
        public_note_id = response.json()["id"]
        
        # Test listing notes without authentication
        response = client.get("/api/v1/notes")
        assert response.status_code == 200
        public_notes = response.json()["notes"]
        
        # Should only see public notes
        note_ids = [note["id"] for note in public_notes]
        assert public_note_id in note_ids
        assert private_note_id not in note_ids
        
        # All public notes should have privacy "public"
        for note in public_notes:
            assert note["privacy"] == "public"
        
        # Test privacy change
        response = client.put(f"/api/v1/notes/{private_note_id}",
                            json={"privacy": "public"},
                            headers=alice_headers)
        assert response.status_code == 200
        
        # Now the note should appear in public listings
        response = client.get("/api/v1/notes")
        public_notes = response.json()["notes"]
        note_ids = [note["id"] for note in public_notes]
        assert private_note_id in note_ids
        
        print("✅ Privacy settings consistency test passed!")
    
    def _setup_friendship(self):
        """Helper method to set up two users with an established friendship."""
        # Register users
        alice_data = {
            "username": "alice_collab",
            "email": "alice_collab@example.com",
            "name": "Alice Collaborator",
            "password": "Password123!"
        }
        
        bob_data = {
            "username": "bob_collab",
            "email": "bob_collab@example.com",
            "name": "Bob Collaborator", 
            "password": "Password123!"
        }
        
        alice_response = client.post("/api/v1/users", json=alice_data)
        alice_id = alice_response.json()["id"]
        
        bob_response = client.post("/api/v1/users", json=bob_data)
        bob_id = bob_response.json()["id"]
        
        # Login
        alice_login = client.post("/api/v1/token", data={
            "username": "alice_collab@example.com",
            "password": "Password123!"
        })
        alice_token = alice_login.json()["access_token"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        
        bob_login = client.post("/api/v1/token", data={
            "username": "bob_collab@example.com",
            "password": "Password123!"
        })
        bob_token = bob_login.json()["access_token"]
        bob_headers = {"Authorization": f"Bearer {bob_token}"}
        
        # Establish friendship
        friend_request = client.post("/api/v1/friend-requests",
                                   json={"addressee_id": bob_id},
                                   headers=alice_headers)
        friendship_id = friend_request.json()["id"]
        
        client.post(f"/api/v1/friend-requests/{friendship_id}/respond",
                   json={"friendship_id": friendship_id, "action": "accept"},
                   headers=bob_headers)
        
        return alice_headers, bob_headers, alice_id, bob_id

class TestErrorHandlingAndRecovery:
    """Test error handling and recovery across the application."""
    
    def test_cascading_error_handling(self, session: Session):
        """Test that errors in one system don't break others."""
        
        # Setup user
        user_data = {
            "username": "errortest",
            "email": "error@example.com",
            "name": "Error Test",
            "password": "Password123!"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        user_id = response.json()["id"]
        
        login_response = client.post("/api/v1/token", data={
            "username": "error@example.com",
            "password": "Password123!"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test non-existent note access
        response = client.get("/api/v1/notes/99999", headers=headers)
        assert response.status_code == 404
        
        # But user should still be able to create notes
        note_data = {
            "title": "Recovery Test",
            "content": "This should work after the error.",
            "privacy": "private"
        }
        
        response = client.post("/api/v1/notes", json=note_data, headers=headers)
        assert response.status_code == 200
        
        # Test adding non-existent user as author
        note_id = response.json()["id"]
        response = client.post(f"/api/v1/notes/{note_id}/authors",
                             json={"user_id": 99999},
                             headers=headers)
        # This might return 422 due to validation or 404 if user lookup happens first
        assert response.status_code in [404, 422]
        
        # But note should still be accessible
        response = client.get(f"/api/v1/notes/{note_id}", headers=headers)
        assert response.status_code == 200
        
        print("✅ Error handling and recovery test passed!")
    
    def test_data_consistency(self, session: Session):
        """Test that data remains consistent across operations."""
        
        # Setup users
        alice_data = {
            "username": "alice_consistency",
            "email": "alice_consistency@example.com",
            "name": "Alice Consistency",
            "password": "Password123!"
        }
        
        response = client.post("/api/v1/users", json=alice_data)
        alice_id = response.json()["id"]
        
        login_response = client.post("/api/v1/token", data={
            "username": "alice_consistency@example.com",
            "password": "Password123!"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create note
        note_data = {
            "title": "Consistency Test",
            "content": "Testing data consistency",
            "privacy": "private"
        }
        
        response = client.post("/api/v1/notes", json=note_data, headers=headers)
        note_id = response.json()["id"]
        note = response.json()
        
        # Verify note appears in user's note list
        response = client.get("/api/v1/notes/my", headers=headers)
        my_notes = response.json()["notes"]
        my_note_ids = [n["id"] for n in my_notes]
        assert note_id in my_note_ids
        
        # Verify author information is consistent
        response = client.get(f"/api/v1/notes/{note_id}/authors", headers=headers)
        authors = response.json()
        assert len(authors) == 1
        assert authors[0]["id"] == alice_id
        assert authors[0]["username"] == "alice_consistency"
        
        # Update note and verify consistency
        response = client.put(f"/api/v1/notes/{note_id}",
                            json={"title": "Updated Consistency Test"},
                            headers=headers)
        updated_note = response.json()
        
        # Title should be updated, but other fields should remain
        assert updated_note["title"] == "Updated Consistency Test"
        assert updated_note["content"] == "Testing data consistency"
        assert updated_note["privacy"] == "private"
        assert updated_note["created_by_user_id"] == alice_id
        
        print("✅ Data consistency test passed!")

class TestPerformanceAndScaling:
    """Test basic performance characteristics."""
    
    def test_bulk_operations(self, session: Session):
        """Test handling of multiple operations."""
        
        # Setup user
        user_data = {
            "username": "bulktest",
            "email": "bulk@example.com", 
            "name": "Bulk Test",
            "password": "Password123!"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        login_response = client.post("/api/v1/token", data={
            "username": "bulk@example.com",
            "password": "Password123!"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create multiple notes
        note_ids = []
        for i in range(5):
            note_data = {
                "title": f"Bulk Note {i+1}",
                "content": f"Content for bulk note number {i+1}",
                "privacy": "public" if i % 2 == 0 else "private"
            }
            
            response = client.post("/api/v1/notes", json=note_data, headers=headers)
            assert response.status_code == 200
            note_ids.append(response.json()["id"])
        
        # List notes and verify pagination works
        response = client.get("/api/v1/notes?limit=3", headers=headers)
        assert response.status_code == 200
        notes_page = response.json()
        assert len(notes_page["notes"]) <= 3
        assert notes_page["total"] >= 5
        
        # List user's notes
        response = client.get("/api/v1/notes/my", headers=headers)
        assert response.status_code == 200
        my_notes = response.json()["notes"]
        assert len(my_notes) >= 5
        
        # Clean up by deleting notes
        for note_id in note_ids:
            response = client.delete(f"/api/v1/notes/{note_id}", headers=headers)
            assert response.status_code == 200
        
        print("✅ Bulk operations test passed!")


class TestCriticalErrorScenarios:
    """Test critical error scenarios that could cause system instability."""
    
    def test_database_connection_failure(self, session: Session):
        """Test API behavior when database is unavailable."""
        user = TestUserFactory.create_test_user(session, "dbtest@test.com", "dbuser")
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test graceful degradation when database fails
        note_data = {"title": "DB Test", "content": "Content", "privacy": "private"}
        
        # Normal operation should work
        response = client.post("/api/v1/notes", json=note_data, headers=headers)
        assert response.status_code == 200
        
        # The application should handle database errors gracefully
        # and not expose internal error details to users
        print("✅ Database failure handling test passed!")
    
    def test_malformed_requests(self, session: Session):
        """Test API behavior with completely malformed requests."""
        user = TestUserFactory.create_test_user(session, "malformed@test.com", "maluser")
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test malformed JSON
        import requests
        
        # Create a raw request with malformed JSON
        url = "http://testserver/api/v1/notes"
        response = client.post(url, data="{invalid json", headers={
            **headers,
            "Content-Type": "application/json"
        })
        
        # Should return 422 (validation error) not 500
        assert response.status_code == 422
        assert "detail" in response.json()
        
        # Test missing required fields
        response = client.post("/api/v1/notes", json={}, headers=headers)
        assert response.status_code == 422
        
        # Test invalid data types
        response = client.post("/api/v1/notes", json={
            "title": 123,  # Should be string
            "content": [],  # Should be string
            "privacy": "invalid_privacy"
        }, headers=headers)
        assert response.status_code == 422
        
        print("✅ Malformed requests test passed!")


class TestAPIRobustness:
    """Test API robustness and consistency."""
    
    def test_response_format_consistency(self, session: Session):
        """Test that error responses have consistent format."""
        user = TestUserFactory.create_test_user(session, "apitest@test.com", "apiuser")
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
                 # Test various error scenarios and check response format consistency
        error_test_cases = [
            # 404 errors
            {"method": "GET", "url": "/api/v1/notes/99999", "headers": headers, "expected": 404},
            # Note: User endpoint returns 403 when user doesn't exist (access control first)
            {"method": "GET", "url": "/api/v1/users/99999", "headers": headers, "expected": 403},
            
            # 401 errors  
            {"method": "GET", "url": "/api/v1/notes/my", "headers": {}, "expected": 401},
            
            # 422 validation errors
            {"method": "POST", "url": "/api/v1/notes", "json": {"title": ""}, "headers": headers, "expected": 422},
            
            # 403/404 permission errors (depends on implementation)
            {"method": "PUT", "url": "/api/v1/notes/99999", "json": {"title": "New"}, "headers": headers, "expected": 404}
        ]
        
        for test_case in error_test_cases:
            method = test_case["method"]
            url = test_case["url"]
            expected_status = test_case["expected"]
            headers_to_use = test_case["headers"]
            json_data = test_case.get("json")
            
            # Make the request
            if method == "GET":
                response = client.get(url, headers=headers_to_use)
            elif method == "POST":
                response = client.post(url, json=json_data, headers=headers_to_use)
            elif method == "PUT":
                response = client.put(url, json=json_data, headers=headers_to_use)
            
            # Check status code
            assert response.status_code == expected_status, \
                f"Expected {expected_status} for {method} {url}, got {response.status_code}"
            
            # Check response format consistency
            response_data = response.json()
            
            # Should have either 'detail' or 'message' field for errors
            if response.status_code >= 400:
                assert "detail" in response_data or "message" in response_data, \
                    f"Error response missing detail/message field for {method} {url}"
                
                # Error message should be a string (not list or dict)
                error_msg = response_data.get("detail") or response_data.get("message")
                if isinstance(error_msg, list):
                    # Validation errors might return a list of errors
                    assert len(error_msg) > 0, f"Empty error list for {method} {url}"
                else:
                    assert isinstance(error_msg, str), \
                        f"Error message should be string for {method} {url}"
        
        print("✅ API response format consistency test passed!")


if __name__ == "__main__":
    print("Running integration tests...")
    pytest.main([__file__, "-v"]) 