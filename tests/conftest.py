import pytest
import os
from typing import AsyncGenerator, Generator
import httpx
from sqlmodel import SQLModel, Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash, create_access_token

# Set test environment variables for PostgreSQL
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/notesnest_test"
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
    SQLModel.metadata.create_all(get_sync_engine())
    yield
    # Teardown after all tests
    SQLModel.metadata.drop_all(get_sync_engine())

@pytest.fixture
def session():
    """Create a clean database session for each test."""
    # Drop and recreate tables for each test to ensure clean state
    SQLModel.metadata.drop_all(get_sync_engine())
    SQLModel.metadata.create_all(get_sync_engine())
    
    with Session(get_sync_engine()) as session:
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


 