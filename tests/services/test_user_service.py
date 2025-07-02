import pytest
from sqlmodel import Session
from app.services.user_service import (
    UserService, UserValidationError, UserNotFoundError, PermissionError
)
from app.models.user import User, UserCreate, UserRole, UserUpdate
from app.utils.auth import get_password_hash, verify_password
from datetime import datetime


class TestUserService:
    """Test UserService functionality."""

    def test_validate_unique_email_success(self, session: Session):
        """Test email validation when email is unique."""
        # Should not raise exception for unique email
        UserService.validate_unique_email("unique@example.com", None, session)

    def test_validate_unique_email_duplicate(self, session: Session, test_user: User):
        """Test email validation with duplicate email."""
        with pytest.raises(UserValidationError) as exc_info:
            UserService.validate_unique_email(test_user.email, None, session)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.message

    def test_validate_unique_email_exclude_self(self, session: Session, test_user: User):
        """Test email validation excluding current user."""
        # Should not raise exception when excluding the user with that email
        UserService.validate_unique_email(test_user.email, test_user.id, session)

    def test_validate_unique_username_success(self, session: Session):
        """Test username validation when username is unique."""
        # Should not raise exception for unique username
        UserService.validate_unique_username("uniqueuser", None, session)

    def test_validate_unique_username_duplicate(self, session: Session, test_user: User):
        """Test username validation with duplicate username."""
        with pytest.raises(UserValidationError) as exc_info:
            UserService.validate_unique_username(test_user.username, None, session)
        
        assert exc_info.value.status_code == 400
        assert "Username already taken" in exc_info.value.message

    def test_validate_unique_username_exclude_self(self, session: Session, test_user: User):
        """Test username validation excluding current user."""
        # Should not raise exception when excluding the user with that username
        UserService.validate_unique_username(test_user.username, test_user.id, session)

    def test_create_user_success(self, session: Session):
        """Test successful user creation."""
        user_create = UserCreate(
            username="newuser",
            email="newuser@example.com",
            name="New User",
            password="Password123!",
            age=25,
            bio="Test bio"
        )
        
        user = UserService.create_user(user_create, session)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
        assert user.age == 25
        assert user.bio == "Test bio"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_email_verified is False
        assert verify_password("Password123!", user.hashed_password)

    def test_create_user_duplicate_email(self, session: Session, test_user: User):
        """Test user creation with duplicate email."""
        user_create = UserCreate(
            username="newuser",
            email=test_user.email,  # duplicate email
            name="New User",
            password="Password123!"
        )
        
        with pytest.raises(UserValidationError) as exc_info:
            UserService.create_user(user_create, session)
        
        assert "Email already registered" in exc_info.value.message

    def test_create_user_duplicate_username(self, session: Session, test_user: User):
        """Test user creation with duplicate username."""
        user_create = UserCreate(
            username=test_user.username,  # duplicate username
            email="newuser@example.com",
            name="New User",
            password="Password123!"
        )
        
        with pytest.raises(UserValidationError) as exc_info:
            UserService.create_user(user_create, session)
        
        assert "Username already taken" in exc_info.value.message

    def test_get_user_by_id_success(self, session: Session, test_user: User):
        """Test successful user retrieval by ID."""
        user = UserService.get_user_by_id(test_user.id, session)
        
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.username == test_user.username

    def test_get_user_by_id_not_found(self, session: Session):
        """Test user retrieval with non-existent ID."""
        with pytest.raises(UserNotFoundError) as exc_info:
            UserService.get_user_by_id(99999, session)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.message

    def test_get_user_by_id_include_deleted(self, session: Session):
        """Test retrieving deleted user when including deleted users."""
        # Create and soft delete a user
        user = User(
            username="deleteduser",
            email="deleted@example.com",
            name="Deleted User",
            hashed_password=get_password_hash("password123"),
            deleted_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Should not find without include_deleted
        with pytest.raises(UserNotFoundError):
            UserService.get_user_by_id(user.id, session, include_deleted=False)
        
        # Should find with include_deleted
        found_user = UserService.get_user_by_id(user.id, session, include_deleted=True)
        assert found_user.id == user.id

    def test_list_users(self, session: Session, test_user: User):
        """Test user listing with pagination."""
        users = UserService.list_users(0, 10, session)
        
        assert isinstance(users, list)
        assert len(users) >= 1
        assert any(user.id == test_user.id for user in users)

    def test_list_users_pagination(self, session: Session):
        """Test user listing pagination."""
        # Create multiple users
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                name=f"User {i}",
                hashed_password=get_password_hash("password123")
            )
            session.add(user)
        session.commit()
        
        # Test pagination
        first_page = UserService.list_users(0, 2, session)
        second_page = UserService.list_users(2, 2, session)
        
        assert len(first_page) == 2
        assert len(second_page) >= 1
        assert first_page[0].id != second_page[0].id

    def test_check_user_access_permission_own_profile(self, test_user: User):
        """Test access permission for own profile."""
        # Should not raise exception
        UserService.check_user_access_permission(test_user.id, test_user)

    def test_check_user_access_permission_admin_access(self, test_user: User, test_admin_user: User):
        """Test admin can access any profile."""
        # Admin should be able to access any user's profile
        UserService.check_user_access_permission(test_user.id, test_admin_user)

    def test_check_user_access_permission_denied(self, test_user: User):
        """Test access permission denied for other user's profile."""
        other_user = User(
            id=999,
            username="otheruser",
            email="other@example.com",
            name="Other User",
            hashed_password="hashed",
            role=UserRole.USER
        )
        
        with pytest.raises(PermissionError) as exc_info:
            UserService.check_user_access_permission(test_user.id, other_user)
        
        assert exc_info.value.status_code == 403
        assert "Not enough permissions" in exc_info.value.message

    def test_check_user_access_permission_require_admin(self, test_user: User):
        """Test admin requirement."""
        with pytest.raises(PermissionError) as exc_info:
            UserService.check_user_access_permission(test_user.id, test_user, require_admin=True)
        
        assert exc_info.value.status_code == 403

    def test_update_user_success(self, session: Session, test_user: User):
        """Test successful user update."""
        update_data = {
            "name": "Updated Name",
            "bio": "Updated bio",
            "age": 30
        }
        
        updated_user = UserService.update_user(test_user.id, update_data, test_user, session)
        
        assert updated_user.name == "Updated Name"
        assert updated_user.bio == "Updated bio"
        assert updated_user.age == 30
        assert updated_user.updated_at is not None

    def test_update_user_permission_denied(self, session: Session, test_user: User):
        """Test user update with insufficient permissions."""
        other_user = User(
            id=999,
            username="otheruser",
            email="other@example.com",
            name="Other User",
            hashed_password="hashed",
            role=UserRole.USER
        )
        
        update_data = {"name": "Hacked Name"}
        
        with pytest.raises(PermissionError):
            UserService.update_user(test_user.id, update_data, other_user, session)

    def test_update_user_duplicate_email(self, session: Session, test_user: User, test_admin_user: User):
        """Test user update with duplicate email."""
        update_data = {"email": test_admin_user.email}
        
        with pytest.raises(UserValidationError) as exc_info:
            UserService.update_user(test_user.id, update_data, test_user, session)
        
        assert "Email already registered" in exc_info.value.message

    def test_delete_user_soft_delete(self, session: Session, test_admin_user: User):
        """Test soft user deletion."""
        # Create user to delete
        user_to_delete = User(
            username="todelete",
            email="todelete@example.com",
            name="To Delete",
            hashed_password=get_password_hash("password123")
        )
        session.add(user_to_delete)
        session.commit()
        session.refresh(user_to_delete)
        
        UserService.delete_user(user_to_delete.id, test_admin_user, session, permanent=False)
        
        # Refresh to get updated state
        session.refresh(user_to_delete)
        
        assert user_to_delete.deleted_at is not None
        assert user_to_delete.is_active is False

    def test_delete_user_permanent_delete(self, session: Session, test_admin_user: User):
        """Test permanent user deletion."""
        # Create user to delete
        user_to_delete = User(
            username="topermadelete",
            email="topermadelete@example.com",
            name="To Permanently Delete",
            hashed_password=get_password_hash("password123")
        )
        session.add(user_to_delete)
        session.commit()
        user_id = user_to_delete.id
        
        UserService.delete_user(user_id, test_admin_user, session, permanent=True)
        
        # User should no longer exist
        with pytest.raises(UserNotFoundError):
            UserService.get_user_by_id(user_id, session, include_deleted=True)

    def test_delete_user_permission_denied(self, session: Session, test_user: User):
        """Test user deletion with insufficient permissions."""
        with pytest.raises(PermissionError):
            UserService.delete_user(test_user.id, test_user, session)

    def test_update_user_role_success(self, session: Session, test_user: User, test_admin_user: User):
        """Test successful user role update."""
        updated_user = UserService.update_user_role(test_user.id, UserRole.ADMIN, test_admin_user, session)
        
        assert updated_user.role == UserRole.ADMIN
        assert updated_user.updated_at is not None

    def test_update_user_role_permission_denied(self, session: Session, test_user: User, test_admin_user: User):
        """Test role update with insufficient permissions."""
        with pytest.raises(PermissionError):
            UserService.update_user_role(test_admin_user.id, UserRole.USER, test_user, session)

    def test_verify_email_success(self, session: Session):
        """Test successful email verification."""
        # Create user with verification token
        verification_token = "test-verification-token"
        user = User(
            username="unverified",
            email="unverified@example.com",
            name="Unverified User",
            hashed_password=get_password_hash("password123"),
            is_email_verified=False,
            email_verification_token=verification_token
        )
        session.add(user)
        session.commit()
        
        UserService.verify_email(verification_token, session)
        
        session.refresh(user)
        assert user.is_email_verified is True
        assert user.email_verification_token is None

    def test_verify_email_invalid_token(self, session: Session):
        """Test email verification with invalid token."""
        with pytest.raises(UserValidationError) as exc_info:
            UserService.verify_email("invalid-token", session)
        
        assert "Invalid verification token" in exc_info.value.message

    def test_user_validation_error_custom(self):
        """Test UserValidationError with custom values."""
        error = UserValidationError("Custom validation error", 422)
        
        assert error.message == "Custom validation error"
        assert error.status_code == 422

    def test_user_not_found_error_default(self):
        """Test UserNotFoundError with default values."""
        error = UserNotFoundError()
        
        assert error.message == "User not found"
        assert error.status_code == 404

    def test_permission_error_default(self):
        """Test PermissionError with default values."""
        error = PermissionError()
        
        assert error.message == "Not enough permissions"
        assert error.status_code == 403 