import pytest
import os
from typing import AsyncGenerator, Generator
import httpx
from sqlmodel import SQLModel, Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash, create_access_token
from sqlalchemy import text

# Set test environment variables for PostgreSQL
os.environ["DATABASE_URL"] = "postgresql://postgres:your_secure_password_here@localhost:5433/notesnest_test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["TESTING"] = "true"

# Import after setting environment variables
from db.database import get_session, get_sync_engine, get_async_session, get_async_engine

def override_get_session():
    """Override session for tests."""
    with Session(get_sync_engine()) as session:
        yield session

# Override the dependency
app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Set up database tables once for all tests."""
    # Import models to ensure they're registered
    from app.models.user import User
    from app.models.friendship import Friendship
    from app.models.note import Note, NoteAuthor
    
    engine = get_sync_engine()
    SQLModel.metadata.create_all(engine)
    yield
    
    # Clean teardown after all tests
    try:
        SQLModel.metadata.drop_all(engine)
    except Exception:
        # If cascade drop fails, use raw SQL
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS note_author CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS note CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS friendship CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS \"user\" CASCADE"))
            conn.commit()

@pytest.fixture
def session():
    """Create a clean database session for each test."""
    engine = get_sync_engine()
    
    # Clear data without dropping tables
    with Session(engine) as session:
        # Delete in proper order to respect foreign keys, using correct table names
        session.execute(text("DELETE FROM noteauthor"))
        session.execute(text("DELETE FROM note"))
        session.execute(text("DELETE FROM friendship"))
        session.execute(text('DELETE FROM "user"'))
        session.commit()
        
        yield session

@pytest.fixture
async def async_session():
    """Create a clean async database session for each test."""
    async with AsyncSession(get_async_engine()) as session:
        yield session

@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

@pytest.fixture
def test_user(session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.USER,
        is_active=True,
        is_email_verified=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def test_admin_user(session: Session):
    """Create a test admin user."""
    admin = User(
        username="adminuser",
        email="admin@example.com",
        name="Admin User",
        hashed_password=get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_email_verified=True
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin

@pytest.fixture
def test_user_token(test_user: User):
    """Create access token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture
def test_admin_token(test_admin_user: User):
    """Create access token for test admin user."""
    return create_access_token(data={"sub": str(test_admin_user.id)})

class TestUserFactory:
    """Factory for creating test users in tests."""
    
    @staticmethod
    def create_test_user(session: Session, email: str, username: str, name: str = None, role: UserRole = UserRole.USER):
        """Create a test user with the given parameters."""
        if name is None:
            name = username.title()
            
        user = User(
            username=username,
            email=email,
            name=name,
            hashed_password=get_password_hash("TestPassword123!"),
            role=role,
            is_active=True,
            is_email_verified=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

# Module-level function for easier importing
def create_test_user(session: Session, email: str, username: str, name: str = None, role: UserRole = UserRole.USER):
    """Create a test user with the given parameters."""
    return TestUserFactory.create_test_user(session, email, username, name, role)

class AssertionHelpers:
    """Helper methods for test assertions."""
    
    @staticmethod
    def assert_error_response(response, expected_message: str):
        """Assert that response contains expected error message."""
        data = response.json()
        if "detail" in data:
            assert expected_message in data["detail"]
        elif "message" in data:
            assert expected_message in data["message"]
        else:
            # If no detail or message, check if the expected message is anywhere in the response
            response_text = str(data)
            assert expected_message in response_text

@pytest.fixture
def test_users_batch(session: Session):
    """Create a batch of test users for testing."""
    users = []
    for i in range(5):
        user = TestUserFactory.create_test_user(
            session, 
            f"batchuser{i}@test.com", 
            f"batchuser{i}",
            f"Batch User {i}"
        )
        users.append(user)
    return users

@pytest.fixture
def authenticated_users(session: Session):
    """Create two authenticated users with tokens."""
    user1 = TestUserFactory.create_test_user(session, "user1@test.com", "user1", "User One")
    user2 = TestUserFactory.create_test_user(session, "user2@test.com", "user2", "User Two")
    
    user1_token = create_access_token(data={"sub": str(user1.id)})
    user2_token = create_access_token(data={"sub": str(user2.id)})
    
    return user1_token, user2_token, user1, user2

@pytest.fixture
def friendship_scenarios(session: Session):
    """Create various friendship scenarios for testing."""
    from app.services.friendship_service import FriendshipService
    
    # Create users for scenarios
    user1 = TestUserFactory.create_test_user(session, "scenario1@test.com", "scenario1", "Scenario User 1")
    user2 = TestUserFactory.create_test_user(session, "scenario2@test.com", "scenario2", "Scenario User 2")
    user3 = TestUserFactory.create_test_user(session, "scenario3@test.com", "scenario3", "Scenario User 3")
    user4 = TestUserFactory.create_test_user(session, "scenario4@test.com", "scenario4", "Scenario User 4")
    
    # Create tokens
    user1_token = create_access_token(data={"sub": str(user1.id)})
    user2_token = create_access_token(data={"sub": str(user2.id)})
    user3_token = create_access_token(data={"sub": str(user3.id)})
    user4_token = create_access_token(data={"sub": str(user4.id)})
    
    # Scenario 1: Pending friend request
    friendship_pending = FriendshipService.send_friend_request(user1.id, user2.id, session)
    
    # Scenario 2: Accepted friendship
    friendship_accepted = FriendshipService.send_friend_request(user3.id, user4.id, session)
    FriendshipService.respond_to_friend_request(friendship_accepted.id, "accept", user4.id, session)
    
    return {
        "pending_request": {
            "user1": user1,
            "user2": user2,
            "user1_token": user1_token,
            "user2_token": user2_token,
            "friendship_id": friendship_pending.id
        },
        "accepted_friendship": {
            "user1": user3,
            "user2": user4,
            "user1_token": user3_token,
            "user2_token": user4_token,
            "friendship_id": friendship_accepted.id
        }
    }


 