"""
Test cases for FriendshipService business logic.
"""

import pytest
from sqlmodel import Session
from app.services.friendship_service import FriendshipService
from app.models.friendship import Friendship, FriendshipStatus
from app.utils.exceptions import (
    FriendshipValidationError, FriendshipNotFoundError, UserNotFoundError, PermissionError
)
from tests.conftest import TestUserFactory


class TestSendFriendRequest:
    """Test sending friend requests"""
    
    def test_send_friend_request_success(self, session: Session):
        """Test successfully sending a friend request"""
        # Create test users
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Send friend request
        friendship = FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        assert friendship.requester_id == user1.id
        assert friendship.addressee_id == user2.id
        assert friendship.status == FriendshipStatus.PENDING
        assert friendship.id is not None
        
    def test_send_friend_request_to_self(self, session: Session):
        """Test that users cannot send friend requests to themselves"""
        user = TestUserFactory.create_test_user(session, "user@test.com", "user")
        
        with pytest.raises(FriendshipValidationError, match="Cannot send friend request to yourself"):
            FriendshipService.send_friend_request(
                requester_id=user.id,
                addressee_id=user.id,
                session=session
            )
            
    def test_send_friend_request_requester_not_found(self, session: Session):
        """Test sending friend request with non-existent requester"""
        user = TestUserFactory.create_test_user(session, "user@test.com", "user")
        
        with pytest.raises(UserNotFoundError, match="Requester user not found"):
            FriendshipService.send_friend_request(
                requester_id=99999,  # Non-existent user
                addressee_id=user.id,
                session=session
            )
            
    def test_send_friend_request_addressee_not_found(self, session: Session):
        """Test sending friend request to non-existent user"""
        user = TestUserFactory.create_test_user(session, "user@test.com", "user")
        
        with pytest.raises(UserNotFoundError, match="Addressee user not found"):
            FriendshipService.send_friend_request(
                requester_id=user.id,
                addressee_id=99999,  # Non-existent user
                session=session
            )
            
    def test_send_friend_request_already_exists(self, session: Session):
        """Test that duplicate friend requests are prevented"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Send first request
        FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        # Try to send duplicate request
        with pytest.raises(FriendshipValidationError, match="Friend request already pending"):
            FriendshipService.send_friend_request(
                requester_id=user1.id,
                addressee_id=user2.id,
                session=session
            )


class TestRespondToFriendRequest:
    """Test responding to friend requests"""
    
    def test_accept_friend_request(self, session: Session):
        """Test accepting a friend request"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Send friend request
        friendship = FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        # Accept the request
        updated_friendship = FriendshipService.respond_to_friend_request(
            friendship_id=friendship.id,
            action="accept",
            current_user_id=user2.id,
            session=session
        )
        
        assert updated_friendship.status == FriendshipStatus.ACCEPTED
        
    def test_reject_friend_request(self, session: Session):
        """Test rejecting a friend request"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Send friend request
        friendship = FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        # Reject the request
        updated_friendship = FriendshipService.respond_to_friend_request(
            friendship_id=friendship.id,
            action="reject",
            current_user_id=user2.id,
            session=session
        )
        
        assert updated_friendship.status == FriendshipStatus.REJECTED
        
    def test_block_friend_request(self, session: Session):
        """Test blocking a friend request"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Send friend request
        friendship = FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        # Block the request
        updated_friendship = FriendshipService.respond_to_friend_request(
            friendship_id=friendship.id,
            action="block",
            current_user_id=user2.id,
            session=session
        )
        
        assert updated_friendship.status == FriendshipStatus.BLOCKED
        
    def test_respond_friendship_not_found(self, session: Session):
        """Test responding to non-existent friendship"""
        user = TestUserFactory.create_test_user(session, "user@test.com", "user")
        
        with pytest.raises(FriendshipNotFoundError, match="Friendship not found"):
            FriendshipService.respond_to_friend_request(
                friendship_id=99999,
                action="accept",
                current_user_id=user.id,
                session=session
            )
            
    def test_respond_not_addressee(self, session: Session):
        """Test that only the addressee can respond to a friend request"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        user3 = TestUserFactory.create_test_user(session, "user3@test.com", "user3")
        
        # Send friend request
        friendship = FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        # Try to respond as different user
        with pytest.raises(PermissionError, match="You can only respond to friend requests sent to you"):
            FriendshipService.respond_to_friend_request(
                friendship_id=friendship.id,
                action="accept",
                current_user_id=user3.id,
                session=session
            )
            
    def test_respond_invalid_action(self, session: Session):
        """Test responding with invalid action"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Send friend request
        friendship = FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        # Try invalid action
        with pytest.raises(FriendshipValidationError, match="Invalid action"):
            FriendshipService.respond_to_friend_request(
                friendship_id=friendship.id,
                action="invalid_action",
                current_user_id=user2.id,
                session=session
            )


class TestRemoveFriend:
    """Test removing friends"""
    
    def test_remove_friend_success(self, session: Session):
        """Test successfully removing a friend"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Create friendship
        friendship = FriendshipService.send_friend_request(
            requester_id=user1.id,
            addressee_id=user2.id,
            session=session
        )
        
        # Accept friendship
        FriendshipService.respond_to_friend_request(
            friendship_id=friendship.id,
            action="accept",
            current_user_id=user2.id,
            session=session
        )
        
        # Remove friendship
        FriendshipService.remove_friend(
            user_id=user1.id,
            friend_id=user2.id,
            session=session
        )
        
        # Verify friendship is removed
        friends = FriendshipService.get_friends_list(user_id=user1.id, page=1, per_page=10, session=session)
        assert len(friends.friends) == 0
        
    def test_remove_friend_not_found(self, session: Session):
        """Test removing non-existent friendship"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        with pytest.raises(FriendshipNotFoundError, match="Friendship not found"):
            FriendshipService.remove_friend(
                user_id=user1.id,
                friend_id=user2.id,
                session=session
            )


class TestGetFriendsList:
    """Test getting friends list"""
    
    def test_get_friends_list_success(self, session: Session):
        """Test getting a list of friends"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        user3 = TestUserFactory.create_test_user(session, "user3@test.com", "user3")
        
        # Create and accept friendships
        friendship1 = FriendshipService.send_friend_request(user1.id, user2.id, session)
        FriendshipService.respond_to_friend_request(friendship1.id, "accept", user2.id, session)
        
        friendship2 = FriendshipService.send_friend_request(user3.id, user1.id, session)
        FriendshipService.respond_to_friend_request(friendship2.id, "accept", user1.id, session)
        
        # Get friends list
        friends_list = FriendshipService.get_friends_list(user_id=user1.id, page=1, per_page=10, session=session)
        
        assert len(friends_list.friends) == 2
        assert friends_list.total == 2
        friend_ids = [friend.id for friend in friends_list.friends]
        assert user2.id in friend_ids
        assert user3.id in friend_ids


class TestGetPendingRequests:
    """Test getting pending friend requests"""
    
    def test_get_pending_requests(self, session: Session):
        """Test getting pending friend requests"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        user3 = TestUserFactory.create_test_user(session, "user3@test.com", "user3")
        
        # Send requests to user1
        FriendshipService.send_friend_request(user2.id, user1.id, session)
        FriendshipService.send_friend_request(user3.id, user1.id, session)
        
        # Get pending requests for user1
        requests = FriendshipService.get_pending_requests(user1.id, session)
        
        assert len(requests) == 2
        requester_ids = [req.requester_id for req in requests]
        assert user2.id in requester_ids
        assert user3.id in requester_ids


class TestGetSentRequests:
    """Test getting sent friend requests"""
    
    def test_get_sent_requests(self, session: Session):
        """Test getting sent friend requests"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        user3 = TestUserFactory.create_test_user(session, "user3@test.com", "user3")
        
        # Send requests from user1
        FriendshipService.send_friend_request(user1.id, user2.id, session)
        FriendshipService.send_friend_request(user1.id, user3.id, session)
        
        # Get sent requests for user1
        requests = FriendshipService.get_sent_requests(user1.id, session)
        
        assert len(requests) == 2
        addressee_ids = [req.addressee_id for req in requests]
        assert user2.id in addressee_ids
        assert user3.id in addressee_ids


class TestGetFriendshipStatus:
    """Test getting friendship status between users"""
    
    def test_get_friendship_status_friends(self, session: Session):
        """Test getting status when users are friends"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Create and accept friendship
        friendship = FriendshipService.send_friend_request(user1.id, user2.id, session)
        FriendshipService.respond_to_friend_request(friendship.id, "accept", user2.id, session)
        
        # Check status
        status = FriendshipService.get_friendship_status(user1.id, user2.id, session)
        assert status == FriendshipStatus.ACCEPTED
        
    def test_get_friendship_status_no_friendship(self, session: Session):
        """Test getting status when no friendship exists"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Check status with no friendship
        status = FriendshipService.get_friendship_status(user1.id, user2.id, session)
        assert status is None


class TestCancelFriendRequest:
    """Test canceling friend requests"""
    
    def test_cancel_friend_request_success(self, session: Session):
        """Test successfully canceling a friend request"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        # Send friend request
        friendship = FriendshipService.send_friend_request(user1.id, user2.id, session)
        
        # Cancel the request
        FriendshipService.cancel_friend_request(user1.id, user2.id, session)
        
        # Verify request is canceled
        sent_requests = FriendshipService.get_sent_requests(user1.id, session)
        assert len(sent_requests) == 0
        
    def test_cancel_friend_request_not_found(self, session: Session):
        """Test canceling non-existent friend request"""
        user = TestUserFactory.create_test_user(session, "user@test.com", "user")
        
        with pytest.raises(FriendshipNotFoundError, match="No pending friend request found"):
            FriendshipService.cancel_friend_request(99999, user.id, session) 