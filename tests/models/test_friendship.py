"""
Test cases for Friendship models and related Pydantic schemas.
"""

import pytest
from datetime import datetime
from app.models.friendship import (
    Friendship, FriendshipStatus, FriendRequestCreate, 
    FriendRequestResponse, FriendshipRead, FriendRead, FriendsList
)
from app.models.user import User, UserCreate
from sqlmodel import Session
from tests.conftest import TestUserFactory


class TestFriendshipModel:
    """Test the core Friendship SQLModel"""
    
    def test_friendship_creation(self, session: Session):
        """Test creating a friendship with valid data"""
        # Create test users
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        friendship = Friendship(
            requester_id=user1.id,
            addressee_id=user2.id,
            status=FriendshipStatus.PENDING
        )
        
        session.add(friendship)
        session.commit()
        session.refresh(friendship)
        
        assert friendship.id is not None
        assert friendship.requester_id == user1.id
        assert friendship.addressee_id == user2.id
        assert friendship.status == FriendshipStatus.PENDING
        assert friendship.created_at is not None
        assert friendship.updated_at is not None
        
    def test_friendship_default_status(self, session: Session):
        """Test that friendship defaults to PENDING status"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        friendship = Friendship(
            requester_id=user1.id,
            addressee_id=user2.id
        )
        
        assert friendship.status == FriendshipStatus.PENDING
        
    def test_friendship_validation_positive_ids(self):
        """Test that friendship validates positive user IDs"""
        # This should work
        friendship = Friendship(
            requester_id=1,
            addressee_id=2,
            status=FriendshipStatus.PENDING
        )
        assert friendship.requester_id == 1
        assert friendship.addressee_id == 2
        
    def test_friendship_str_representation(self, session: Session):
        """Test string representation of friendship"""
        user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1")
        user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2")
        
        friendship = Friendship(
            requester_id=user1.id,
            addressee_id=user2.id,
            status=FriendshipStatus.ACCEPTED
        )
        
        str_repr = str(friendship)
        assert str(user1.id) in str_repr
        assert str(user2.id) in str_repr
        assert "ACCEPTED" in str_repr


class TestFriendRequestCreate:
    """Test FriendRequestCreate Pydantic model"""
    
    def test_valid_friend_request_create(self):
        """Test creating a valid friend request"""
        request_data = FriendRequestCreate(addressee_id=123)
        
        assert request_data.addressee_id == 123
        
    def test_friend_request_create_validation(self):
        """Test validation for friend request creation"""
        # Test with valid ID
        request_data = FriendRequestCreate(addressee_id=1)
        assert request_data.addressee_id == 1
        
        # Test serialization
        data_dict = request_data.model_dump()
        assert data_dict["addressee_id"] == 1


class TestFriendRequestResponse:
    """Test FriendRequestResponse Pydantic model"""
    
    def test_valid_friend_request_response(self):
        """Test creating a valid friend request response"""
        response_data = FriendRequestResponse(
            friendship_id=123,
            action="accept"
        )
        
        assert response_data.friendship_id == 123
        assert response_data.action == "accept"
        
    def test_friend_request_response_action_validation(self):
        """Test that action field accepts valid values"""
        # Test all valid actions
        valid_actions = ["accept", "reject", "block"]
        
        for action in valid_actions:
            response_data = FriendRequestResponse(
                friendship_id=1,
                action=action
            )
            assert response_data.action == action
            
    def test_friend_request_response_case_insensitive(self):
        """Test that action validation is case insensitive"""
        response_data = FriendRequestResponse(
            friendship_id=1,
            action="ACCEPT"  # uppercase
        )
        # Should be converted to lowercase
        assert response_data.action == "accept"


class TestFriendshipRead:
    """Test FriendshipRead Pydantic model"""
    
    def test_friendship_read_creation(self):
        """Test creating FriendshipRead model"""
        friendship_data = FriendshipRead(
            id=1,
            requester_id=100,
            addressee_id=200,
            status="accepted",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert friendship_data.id == 1
        assert friendship_data.requester_id == 100
        assert friendship_data.addressee_id == 200
        assert friendship_data.status == "accepted"
        assert friendship_data.created_at is not None
        assert friendship_data.updated_at is not None


class TestFriendRead:
    """Test FriendRead Pydantic model"""
    
    def test_friend_read_creation(self):
        """Test creating FriendRead model"""
        friend_data = FriendRead(
            id=1,
            username="testuser",
            name="Test User",
            email="test@example.com",
            is_active=True,
            friendship_status=FriendshipStatus.ACCEPTED,
            friendship_since=datetime.now()
        )
        
        assert friend_data.id == 1
        assert friend_data.username == "testuser"
        assert friend_data.name == "Test User"
        assert friend_data.email == "test@example.com"
        assert friend_data.is_active == True
        assert friend_data.friendship_status == FriendshipStatus.ACCEPTED
        assert friend_data.friendship_since is not None


class TestFriendsList:
    """Test FriendsList Pydantic model"""
    
    def test_friends_list_creation(self):
        """Test creating FriendsList with friends"""
        friends = [
            FriendRead(
                id=1,
                username="friend1",
                name="Friend One",
                email="friend1@test.com",
                is_active=True,
                friendship_status=FriendshipStatus.ACCEPTED,
                friendship_since=datetime.now()
            ),
            FriendRead(
                id=2,
                username="friend2", 
                name="Friend Two",
                email="friend2@test.com",
                is_active=True,
                friendship_status=FriendshipStatus.ACCEPTED,
                friendship_since=datetime.now()
            )
        ]
        
        friends_list = FriendsList(
            friends=friends,
            total=2,
            page=1,
            per_page=10,
            has_next=False,
            has_prev=False
        )
        
        assert len(friends_list.friends) == 2
        assert friends_list.total == 2
        assert friends_list.page == 1
        assert friends_list.per_page == 10
        
    def test_friends_list_empty(self):
        """Test creating empty FriendsList"""
        friends_list = FriendsList(
            friends=[],
            total=0,
            page=1,
            per_page=10,
            has_next=False,
            has_prev=False
        )
        
        assert len(friends_list.friends) == 0
        assert friends_list.total == 0
        assert friends_list.page == 1
        assert friends_list.per_page == 10 