import pytest
import json
import httpx
from app.models.user import User, UserRole


class TestUserRoutes:
    """Test user API routes."""

    async def test_create_user(self, async_client: httpx.AsyncClient):
        """Test user creation endpoint."""
        response = await async_client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "name": "New User",
                "password": "Password123!",
                "age": 25,
                "bio": "Test bio"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert data["age"] == 25
        assert data["bio"] == "Test bio"
        assert data["is_active"] is True
        assert data["is_email_verified"] is False
        assert "hashed_password" not in data
        assert "id" in data

    async def test_create_user_duplicate_email(self, async_client: httpx.AsyncClient, test_user: User):
        """Test creating user with duplicate email fails."""
        response = await async_client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": test_user.email,  # duplicate email
                "name": "New User",
                "password": "Password123!"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_create_user_invalid_password(self, async_client: httpx.AsyncClient):
        """Test creating user with invalid password fails."""
        response = await async_client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "name": "New User",
                "password": "weak"  # invalid password
            }
        )
        
        assert response.status_code == 422

    async def test_get_users_requires_auth(self, async_client: httpx.AsyncClient):
        """Test that getting users requires authentication."""
        response = await async_client.get("/api/v1/users")
        assert response.status_code == 401

    async def test_get_users_with_auth(self, async_client: httpx.AsyncClient, test_user: User, test_user_token: str):
        """Test getting users list with authentication."""
        response = await async_client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(user["id"] == test_user.id for user in data)

    async def test_get_user_by_id(self, async_client: httpx.AsyncClient, test_user: User, test_user_token: str):
        """Test getting specific user by ID."""
        response = await async_client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    async def test_update_own_profile(self, async_client: httpx.AsyncClient, test_user: User, test_user_token: str):
        """Test user updating their own profile."""
        response = await async_client.put(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "name": "Updated Name",
                "bio": "Updated bio",
                "age": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
        assert data["age"] == 30

    async def test_update_other_user_forbidden(self, async_client: httpx.AsyncClient, test_user: User, test_admin_user: User, test_user_token: str):
        """Test regular user cannot update other user's profile."""
        response = await async_client.put(
            f"/api/v1/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"name": "Hacked Name"}
        )
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    async def test_delete_user_requires_admin(self, async_client: httpx.AsyncClient, test_user: User, test_user_token: str):
        """Test regular user cannot delete users."""
        response = await async_client.delete(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    async def test_admin_can_delete_user(self, async_client: httpx.AsyncClient, test_user: User, test_admin_token: str):
        """Test admin can delete users."""
        response = await async_client.delete(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        assert "User deleted successfully" in response.json()["detail"]

    async def test_admin_can_update_user_role(self, async_client: httpx.AsyncClient, test_user: User, test_admin_token: str):
        """Test admin can update user roles."""
        from app.models.user import UserRole
        
        response = await async_client.post(
            f"/api/v1/users/{test_user.id}/role?role={UserRole.ADMIN.value}",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == UserRole.ADMIN.value

    async def test_regular_user_cannot_update_role(self, async_client: httpx.AsyncClient, test_admin_user: User, test_user_token: str):
        """Test regular user cannot update roles."""
        from app.models.user import UserRole
        
        response = await async_client.post(
            f"/api/v1/users/{test_admin_user.id}/role?role={UserRole.USER.value}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    async def test_verify_email_public(self, async_client: httpx.AsyncClient, session):
        """Test email verification endpoint is public."""
        # Create a user with verification token
        from app.models.user import User
        from app.utils.auth import get_password_hash
        import secrets
        
        verification_token = secrets.token_urlsafe()
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
        
        response = await async_client.post(f"/api/v1/users/verify-email/{verification_token}")
        
        assert response.status_code == 200
        assert "Email verified successfully" in response.json()["detail"]

    async def test_verify_email_invalid_token(self, async_client: httpx.AsyncClient):
        """Test email verification with invalid token."""
        response = await async_client.post("/api/v1/users/verify-email/invalid-token")
        
        assert response.status_code == 400
        assert "Invalid verification token" in response.json()["detail"]

    async def test_unauthorized_access(self, async_client: httpx.AsyncClient):
        """Test accessing protected endpoints without token."""
        protected_endpoints = [
            ("GET", "/api/v1/users"),
            ("GET", "/api/v1/users/1"),
            ("PUT", "/api/v1/users/1"),
            ("DELETE", "/api/v1/users/1"),
            ("POST", "/api/v1/users/1/role"),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            elif method == "PUT":
                response = await async_client.put(endpoint, json={})
            elif method == "DELETE":
                response = await async_client.delete(endpoint)
            elif method == "POST":
                response = await async_client.post(endpoint)
            
            assert response.status_code == 401

    async def test_invalid_token(self, async_client: httpx.AsyncClient):
        """Test accessing protected endpoints with invalid token."""
        response = await async_client.get(
            "/api/v1/users",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401 