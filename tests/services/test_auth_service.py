import pytest
import time
from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService, AuthenticationError
from app.models.user import User, UserRole, TokenResponse
from app.utils.auth import get_password_hash, verify_password


class TestAuthService:
    """Test AuthService functionality."""

    def test_authenticate_user_success(self, session: Session, test_user: User):
        """Test successful user authentication."""
        user = AuthService.authenticate_user(test_user.email, "testpass123", session)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.is_active is True

    def test_authenticate_user_wrong_password(self, session: Session, test_user: User):
        """Test authentication with wrong password."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthService.authenticate_user(test_user.email, "wrongpassword", session)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in exc_info.value.message

    def test_authenticate_user_nonexistent_email(self, session: Session):
        """Test authentication with non-existent email."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthService.authenticate_user("nonexistent@example.com", "password", session)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in exc_info.value.message

    def test_authenticate_user_inactive_user(self, session: Session):
        """Test authentication with inactive user."""
        # Create inactive user
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            name="Inactive User",
            hashed_password=get_password_hash("password123"),
            is_active=False
        )
        session.add(inactive_user)
        session.commit()
        
        with pytest.raises(AuthenticationError) as exc_info:
            AuthService.authenticate_user("inactive@example.com", "password123", session)
        
        assert exc_info.value.status_code == 401
        assert "User account is disabled" in exc_info.value.message

    def test_create_user_tokens(self, test_user: User):
        """Test token creation for user."""
        tokens = AuthService.create_user_tokens(test_user)
        
        assert isinstance(tokens, TokenResponse)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert len(tokens.access_token) > 20  # JWT tokens are long
        assert len(tokens.refresh_token) > 20

    def test_refresh_user_tokens_success(self, session: Session, test_user: User):
        """Test successful token refresh."""
        # Create initial tokens
        initial_tokens = AuthService.create_user_tokens(test_user)
        
        # Add small delay to ensure different timestamps
        time.sleep(1)
        
        # Refresh tokens
        new_tokens = AuthService.refresh_user_tokens(initial_tokens.refresh_token, session)
        
        assert isinstance(new_tokens, TokenResponse)
        assert new_tokens.access_token != initial_tokens.access_token
        assert new_tokens.refresh_token != initial_tokens.refresh_token
        assert new_tokens.token_type == "bearer"

    def test_refresh_user_tokens_invalid_token(self, session: Session):
        """Test refresh with invalid token."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthService.refresh_user_tokens("invalid.token.here", session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in exc_info.value.message

    def test_refresh_user_tokens_access_token(self, session: Session, test_user: User):
        """Test refresh with access token instead of refresh token."""
        # Create tokens and try to use access token for refresh
        tokens = AuthService.create_user_tokens(test_user)
        
        with pytest.raises(AuthenticationError) as exc_info:
            AuthService.refresh_user_tokens(tokens.access_token, session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in exc_info.value.message

    def test_refresh_user_tokens_inactive_user(self, session: Session):
        """Test refresh token with inactive user."""
        # Create user and tokens
        user = User(
            username="testrefresh",
            email="testrefresh@example.com",
            name="Test Refresh",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        tokens = AuthService.create_user_tokens(user)
        
        # Make user inactive
        user.is_active = False
        session.commit()
        
        with pytest.raises(AuthenticationError) as exc_info:
            AuthService.refresh_user_tokens(tokens.refresh_token, session)
        
        assert exc_info.value.status_code == 401
        assert "User is inactive or deleted" in exc_info.value.message

    def test_login_user_success(self, session: Session, test_user: User):
        """Test complete login flow."""
        tokens = AuthService.login_user(test_user.email, "testpass123", session)
        
        assert isinstance(tokens, TokenResponse)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    def test_login_user_failure(self, session: Session, test_user: User):
        """Test login with wrong credentials."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthService.login_user(test_user.email, "wrongpassword", session)
        
        assert exc_info.value.status_code == 401



    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message."""
        error = AuthenticationError("Custom error message", 403)
        
        assert error.message == "Custom error message"
        assert error.status_code == 403

    def test_authentication_error_default_values(self):
        """Test AuthenticationError with default values."""
        error = AuthenticationError("Default error")
        
        assert error.message == "Default error"
        assert error.status_code == 401 