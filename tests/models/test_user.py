import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from sqlmodel import select, Session
from app.models.user import User, UserCreate, UserRead, UserUpdate, UserRole
from app.utils.auth import get_password_hash, verify_password


class TestUserModel:
    """Test User model functionality."""

    def test_user_create_validation(self):
        """Test user creation validation."""
        # Valid user creation
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            name="Test User",
            password="TestPassword123!"
        )
        assert user_data.username == "testuser"
        assert user_data.email == "test@example.com"
        assert user_data.name == "Test User"
        assert user_data.password == "TestPassword123!"

    def test_password_validation(self):
        """Test password validation rules."""
        # Test weak password
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            UserCreate(
                username="test",
                email="test@example.com",
                name="Test",
                password="weak"
            )
        
        # Test password without uppercase
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            UserCreate(
                username="test",
                email="test@example.com",
                name="Test",
                password="lowercase123!"
            )
        
        # Test password without numbers
        with pytest.raises(ValueError, match="Password must contain at least one number"):
            UserCreate(
                username="test",
                email="test@example.com",
                name="Test",
                password="NoNumbers!"
            )

    async def test_user_crud_operations(self, session: Session):
        """Test basic CRUD operations on User model."""
        # Create
        user = User(
            username="testuser",
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("TestPassword123!")
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_email_verified is False
        assert user.role == UserRole.USER
        
        # Read
        retrieved_user = session.get(User, user.id)
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        
        # Update
        retrieved_user.name = "Updated Name"
        session.commit()
        session.refresh(retrieved_user)
        assert retrieved_user.name == "Updated Name"
        
        # Delete
        session.delete(retrieved_user)
        session.commit()
        deleted_user = session.get(User, user.id)
        assert deleted_user is None

    def test_user_defaults(self):
        """Test that user model has correct default values."""
        user = User(
            username="testuser",
            email="test@example.com",
            name="Test User",
            hashed_password="hashed_password"
        )
        
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_email_verified is False
        assert user.email_verification_token is None
        assert user.social_links == {"facebook": None, "twitter": None, "linkedin": None, "instagram": None, "github": None}
        assert user.address == {"street": None, "city": None, "state": None, "country": "", "postal_code": None}
        assert user.deleted_at is None

    async def test_user_unique_constraints(self, session: Session):
        """Test that email and username are unique."""
        # Create first user
        user1 = User(
            username="testuser",
            email="test@example.com",
            name="Test User 1",
            hashed_password=get_password_hash("password123")
        )
        session.add(user1)
        session.commit()
        
        # Try to create user with same email
        user2 = User(
            username="testuser2",
            email="test@example.com",  # Same email
            name="Test User 2",
            hashed_password=get_password_hash("password123")
        )
        session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()
        
        session.rollback()
        
        # Try to create user with same username
        user3 = User(
            username="testuser",  # Same username
            email="test2@example.com",
            name="Test User 3",
            hashed_password=get_password_hash("password123")
        )
        session.add(user3)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()

    def test_password_hashing(self):
        """Test password hashing functionality."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Hashed password should be different from original
        assert hashed != password
        
        # Should be able to verify password
        assert verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert verify_password("WrongPassword", hashed) is False

    def test_user_read_model(self):
        """Test UserRead model excludes sensitive fields."""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            name="Test User",
            hashed_password="hashed_password_here",
            role=UserRole.USER,
            is_active=True,
            is_email_verified=True
        )
        
        # Convert to UserRead
        user_read = UserRead.model_validate(user)
        
        # Should include public fields
        assert user_read.id == 1
        assert user_read.username == "testuser"
        assert user_read.email == "test@example.com"
        assert user_read.name == "Test User"
        assert user_read.role == UserRole.USER
        assert user_read.is_active is True
        assert user_read.is_email_verified is True
        
        # Should not include hashed_password in the model_dump
        user_dict = user_read.model_dump()
        assert "hashed_password" not in user_dict

    async def test_json_field_updates(self, session: Session):
        """Test that JSON fields can be updated properly."""
        user = User(
            username="testuser",
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("password123"),
            social_links={"twitter": "https://twitter.com/test", "github": "https://github.com/test", "facebook": None, "linkedin": None, "instagram": None}
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Update social_links
        user.social_links = {"twitter": "https://twitter.com/updated", "github": "https://github.com/updated", "linkedin": "https://linkedin.com/in/test", "facebook": None, "instagram": None}
        session.commit()
        session.refresh(user)
        
        assert user.social_links["twitter"] == "https://twitter.com/updated"
        assert user.social_links["github"] == "https://github.com/updated"
        assert user.social_links["linkedin"] == "https://linkedin.com/in/test"
        
        # Verify it persists after re-querying
        retrieved_user = session.get(User, user.id)
        assert retrieved_user.social_links["twitter"] == "https://twitter.com/updated"
        assert retrieved_user.social_links["linkedin"] == "https://linkedin.com/in/test" 
