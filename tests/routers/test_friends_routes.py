"""
Test cases for friendship router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from tests.conftest import TestUserFactory, AssertionHelpers


client = TestClient(app)


class TestSendFriendRequest:
    """Test sending friend requests via API"""
    
    def test_send_friend_request_success(self, authenticated_users, session: Session):
        """Test successfully sending a friend request"""
        user1_token, user2_token, user1, user2 = authenticated_users
        
        response = client.post(
            "/api/v1/friend-requests",
            json={"addressee_id": user2.id},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["requester_id"] == user1.id
        assert data["addressee_id"] == user2.id
        assert data["status"] == "pending"
        
    def test_send_friend_request_to_self(self, authenticated_users, session: Session):
        """Test that users cannot send friend requests to themselves"""
        user1_token, _, user1, _ = authenticated_users
        
        response = client.post(
            "/api/v1/friend-requests",
            json={"addressee_id": user1.id},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 400
        AssertionHelpers.assert_error_response(response, "Cannot send friend request to yourself")
        
    def test_send_friend_request_nonexistent_user(self, authenticated_users, session: Session):
        """Test sending friend request to non-existent user"""
        user1_token, _, user1, _ = authenticated_users
        
        response = client.post(
            "/api/v1/friend-requests",
            json={"addressee_id": 99999},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 404
        AssertionHelpers.assert_error_response(response, "Addressee user not found")
        
    def test_send_friend_request_unauthenticated(self, test_users_batch, session: Session):
        """Test that unauthenticated users cannot send friend requests"""
        user1, user2 = test_users_batch[:2]
        
        response = client.post(
            "/api/v1/friend-requests",
            json={"addressee_id": user2.id}
        )
        
        assert response.status_code == 401


class TestRespondToFriendRequest:
    """Test responding to friend requests via API"""
    
    def test_accept_friend_request(self, friendship_scenarios, session: Session):
        """Test accepting a friend request"""
        scenario = friendship_scenarios["pending_request"]
        user1_token = scenario["user1_token"]
        user2_token = scenario["user2_token"]
        friendship_id = scenario["friendship_id"]
        
        response = client.post(
            f"/api/v1/friend-requests/{friendship_id}/respond",
            json={"friendship_id": friendship_id, "action": "accept"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        
    def test_reject_friend_request(self, friendship_scenarios, session: Session):
        """Test rejecting a friend request"""
        scenario = friendship_scenarios["pending_request"]
        user2_token = scenario["user2_token"]
        friendship_id = scenario["friendship_id"]
        
        response = client.post(
            f"/api/v1/friend-requests/{friendship_id}/respond",
            json={"friendship_id": friendship_id, "action": "reject"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        
    def test_block_friend_request(self, friendship_scenarios, session: Session):
        """Test blocking a friend request"""
        scenario = friendship_scenarios["pending_request"]
        user2_token = scenario["user2_token"]
        friendship_id = scenario["friendship_id"]
        
        response = client.post(
            f"/api/v1/friend-requests/{friendship_id}/respond",
            json={"friendship_id": friendship_id, "action": "block"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"
        
    def test_respond_nonexistent_friendship(self, authenticated_users, session: Session):
        """Test responding to non-existent friendship"""
        _, user2_token, _, _ = authenticated_users
        
        response = client.post(
            "/api/v1/friend-requests/99999/respond",
            json={"friendship_id": 99999, "action": "accept"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 404
        AssertionHelpers.assert_error_response(response, "Friendship not found")
        
    def test_respond_not_addressee(self, friendship_scenarios, session: Session):
        """Test that only addressee can respond to friend request"""
        scenario = friendship_scenarios["pending_request"]
        user1_token = scenario["user1_token"]  # Wrong user
        friendship_id = scenario["friendship_id"]
        
        response = client.post(
            f"/api/v1/friend-requests/{friendship_id}/respond",
            json={"friendship_id": friendship_id, "action": "accept"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 403
        AssertionHelpers.assert_error_response(response, "You can only respond to friend requests sent to you")


class TestGetFriendsList:
    """Test getting friends list via API"""
    
    def test_get_friends_list_success(self, friendship_scenarios, session: Session):
        """Test getting friends list with accepted friendships"""
        scenario = friendship_scenarios["accepted_friendship"]
        user1_token = scenario["user1_token"]
        user2 = scenario["user2"]
        
        response = client.get(
            "/api/v1/friends",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["friends"]) == 1
        assert data["friends"][0]["id"] == user2.id
        
    def test_get_friends_list_empty(self, authenticated_users, session: Session):
        """Test getting empty friends list"""
        user1_token, _, _, _ = authenticated_users
        
        response = client.get(
            "/api/v1/friends",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["friends"]) == 0
        
    def test_get_friends_list_pagination(self, authenticated_users, session: Session):
        """Test friends list pagination"""
        user1_token, _, user1, _ = authenticated_users
        
        # Create multiple friends
        friends = []
        for i in range(3):
            friend = TestUserFactory.create_test_user(session, f"friend{i}@test.com", f"friend{i}")
            friends.append(friend)
            
        # Accept friendship requests (simplified for test)
        # In real scenario, would send and accept requests
        
        response = client.get(
            "/api/v1/friends?page=1&per_page=2",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 2  # Should match the query parameter


class TestGetPendingRequests:
    """Test getting pending friend requests via API"""
    
    def test_get_pending_requests(self, friendship_scenarios, session: Session):
        """Test getting pending friend requests"""
        scenario = friendship_scenarios["pending_request"]
        user2_token = scenario["user2_token"]
        user1 = scenario["user1"]
        
        response = client.get(
            "/api/v1/friend-requests/pending",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["requester_id"] == user1.id
        assert data[0]["status"] == "pending"
        
    def test_get_pending_requests_empty(self, authenticated_users, session: Session):
        """Test getting empty pending requests list"""
        user1_token, _, _, _ = authenticated_users
        
        response = client.get(
            "/api/v1/friend-requests/pending",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestGetSentRequests:
    """Test getting sent friend requests via API"""
    
    def test_get_sent_requests(self, friendship_scenarios, session: Session):
        """Test getting sent friend requests"""
        scenario = friendship_scenarios["pending_request"]
        user1_token = scenario["user1_token"]
        user2 = scenario["user2"]
        
        response = client.get(
            "/api/v1/friend-requests/sent",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["addressee_id"] == user2.id
        assert data[0]["status"] == "pending"


class TestRemoveFriend:
    """Test removing friends via API"""
    
    def test_remove_friend_success(self, friendship_scenarios, session: Session):
        """Test successfully removing a friend"""
        scenario = friendship_scenarios["accepted_friendship"]
        user1_token = scenario["user1_token"]
        user2 = scenario["user2"]
        
        response = client.delete(
            f"/api/v1/friends/{user2.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "removed successfully" in data["detail"]
        
    def test_remove_friend_not_found(self, authenticated_users, session: Session):
        """Test removing non-existent friend"""
        user1_token, _, _, _ = authenticated_users
        
        response = client.delete(
            "/api/v1/friends/99999",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 404
        AssertionHelpers.assert_error_response(response, "Friendship not found")


class TestGetFriendshipStatus:
    """Test getting friendship status via API"""
    
    def test_get_friendship_status_friends(self, friendship_scenarios, session: Session):
        """Test getting status when users are friends"""
        scenario = friendship_scenarios["accepted_friendship"]
        user1_token = scenario["user1_token"]
        user2 = scenario["user2"]
        
        response = client.get(
            f"/api/v1/friendship-status/{user2.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["friendship_status"] == "accepted"
        assert data["are_friends"] == True
        assert data["user_id"] == user2.id
        
    def test_get_friendship_status_no_friendship(self, authenticated_users, session: Session):
        """Test getting status when no friendship exists"""
        user1_token, _, _, user2 = authenticated_users
        
        response = client.get(
            f"/api/v1/friendship-status/{user2.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["friendship_status"] is None
        assert data["are_friends"] == False
        assert data["user_id"] == user2.id


class TestCancelFriendRequest:
    """Test canceling friend requests via API"""
    
    def test_cancel_friend_request_success(self, friendship_scenarios, session: Session):
        """Test successfully canceling a friend request"""
        scenario = friendship_scenarios["pending_request"]
        user1_token = scenario["user1_token"]
        user2 = scenario["user2"]
        
        response = client.delete(
            f"/api/v1/friend-requests/cancel/{user2.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cancelled successfully" in data["detail"]
        
    def test_cancel_friend_request_not_found(self, authenticated_users, session: Session):
        """Test canceling non-existent friend request"""
        user1_token, _, _, _ = authenticated_users
        
        response = client.delete(
            "/api/v1/friend-requests/cancel/99999",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 404
        AssertionHelpers.assert_error_response(response, "No pending friend request found")


class TestFriendsWorkflow:
    """Test complete friendship workflow scenarios"""
    
    def test_complete_friendship_workflow(self, authenticated_users, session: Session):
        """Test complete friendship workflow from request to removal"""
        user1_token, user2_token, user1, user2 = authenticated_users
        
        # Step 1: Send friend request
        response = client.post(
            "/api/v1/friend-requests",
            json={"addressee_id": user2.id},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        friendship_id = response.json()["id"]
        
        # Step 2: Accept friend request
        response = client.post(
            f"/api/v1/friend-requests/{friendship_id}/respond",
            json={"friendship_id": friendship_id, "action": "accept"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 200
        
        # Step 3: Check friendship status
        response = client.get(
            f"/api/v1/friendship-status/{user2.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        assert response.json()["friendship_status"] == "accepted"
        
        # Step 4: Check friends list
        response = client.get(
            "/api/v1/friends",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()["friends"]) == 1
        
        # Step 5: Remove friend
        response = client.delete(
            f"/api/v1/friends/{user2.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        
        # Step 6: Verify friendship removed
        response = client.get(
            "/api/v1/friends",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()["friends"]) == 0
        
    def test_duplicate_friend_request_prevention(self, authenticated_users, session: Session):
        """Test that duplicate friend requests are prevented"""
        user1_token, _, user1, user2 = authenticated_users
        
        # Send first friend request
        response = client.post(
            "/api/v1/friend-requests",
            json={"addressee_id": user2.id},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        
        # Try to send duplicate request
        response = client.post(
            "/api/v1/friend-requests",
            json={"addressee_id": user2.id},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 400
        AssertionHelpers.assert_error_response(response, "Friend request already pending") 