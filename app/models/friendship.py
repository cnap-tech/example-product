from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import field_validator

class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    REJECTED = "rejected"

class Friendship(SQLModel, table=True):
    """
    Friendship model to handle user-to-user relationships.
    
    This model handles bidirectional friendships with status tracking:
    - PENDING: Friend request sent, awaiting response
    - ACCEPTED: Both users are friends
    - BLOCKED: One user blocked the other
    - REJECTED: Friend request was declined
    """
    
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign keys
    requester_id: int = Field(foreign_key="user.id", description="User who sent the friend request")
    addressee_id: int = Field(foreign_key="user.id", description="User who received the friend request")
    
    # Friendship status
    status: FriendshipStatus = Field(default=FriendshipStatus.PENDING)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships (optional, for convenience)
    # Note: These would require importing User, so we'll handle them at the service level
    
    class Config:
        # Ensure we can't have duplicate friendship requests
        # This will be enforced at the database level with a unique constraint
        pass

    @field_validator("requester_id", "addressee_id")
    @classmethod
    def validate_user_ids(cls, v):
        if v <= 0:
            raise ValueError("User ID must be positive")
        return v
    
    def __str__(self):
        return f"Friendship({self.requester_id} -> {self.addressee_id}, status={self.status})"

# Pydantic models for API requests/responses

class FriendRequestCreate(SQLModel):
    """Model for creating a friend request"""
    addressee_id: int
    
    @field_validator("addressee_id")
    @classmethod
    def validate_addressee_id(cls, v):
        if v <= 0:
            raise ValueError("Addressee ID must be positive")
        return v

class FriendRequestResponse(SQLModel):
    """Model for responding to a friend request"""
    friendship_id: int
    action: str  # 'accept', 'reject', or 'block'
    
    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v.lower() not in ['accept', 'reject', 'block']:
            raise ValueError("Action must be 'accept', 'reject', or 'block'")
        return v.lower()

class FriendshipRead(SQLModel):
    """Model for reading friendship data"""
    id: int
    requester_id: int
    addressee_id: int
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime

class FriendRead(SQLModel):
    """Model for reading friend user data"""
    id: int
    username: str
    name: str
    email: str
    is_active: bool
    friendship_status: FriendshipStatus
    friendship_since: datetime

class FriendsList(SQLModel):
    """Model for listing friends with pagination"""
    friends: List[FriendRead]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool 