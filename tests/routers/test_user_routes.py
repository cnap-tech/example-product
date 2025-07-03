import pytest
import json
import httpx
from app.models.user import User, UserRole
from app.utils.auth import create_access_token
from tests.conftest import TestUserFactory


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
        assert "Access denied" in response.json()["detail"]

    async def test_delete_user_requires_admin(self, async_client: httpx.AsyncClient, test_user: User, test_admin_token: str):
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
        """Test that regular users cannot update user roles."""
        from app.models.user import UserRole
        
        response = await async_client.post(
            f"/api/v1/users/{test_admin_user.id}/role?role={UserRole.USER.value}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]

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


class TestSecurityInputValidation:
    """Test security-related input validation scenarios."""
    
    async def test_sql_injection_attempts(self, async_client: httpx.AsyncClient, session):
        """Test SQL injection payloads in user input fields."""
        # Create a user for authentication
        user = TestUserFactory.create_test_user(session, "sqltest@test.com", "sqluser")
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # SQL injection payloads to test
        sql_payloads = [
            "'; DROP TABLE users; --",
            "admin'--",
            "' OR 1=1 --",
            "'; UPDATE users SET role='admin' WHERE id=1; --",
            "' UNION SELECT password FROM users --",
            "') OR '1'='1",
            "'; INSERT INTO users (username) VALUES ('hacker'); --",
            "<script>alert('xss')</script>",  # Also test XSS
            "{{7*7}}",  # Template injection
            "$(whoami)"  # Command injection
        ]
        
        for payload in sql_payloads:
            # Test user creation with malicious username
            response = await async_client.post(
                "/api/v1/users",
                json={
                    "username": payload,
                    "email": f"test{hash(payload)}@test.com",
                    "name": "Test User",
                    "password": "TestPassword123!"
                }
            )
            
            # Should either succeed (payload properly escaped) or fail with validation error
            # But never crash with 500 or execute the payload
            if response.status_code == 200:
                # If user was created, verify the data was properly escaped
                user_id = response.json()["id"]
                
                # Login as the created user to access their profile
                login_token = create_access_token(data={"sub": str(user_id)})
                auth_headers = {"Authorization": f"Bearer {login_token}"}
                user_response = await async_client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
                user_data_returned = user_response.json()
                
                # Username should contain the payload as literal text, not executed
                assert payload in user_data_returned["username"]
                
                # Clean up - delete the test user
                await async_client.delete(f"/api/v1/users/{user_id}", headers=headers)
                
            elif response.status_code in [422, 400]:
                # Validation error - acceptable if there are input restrictions
                assert True
            else:
                # Should not return 500 or other error codes indicating execution or crash
                assert False, f"Unexpected status code {response.status_code} for payload: {payload}"
            
            # Test user update with malicious bio
            response = await async_client.put(
                f"/api/v1/users/{user.id}",
                headers=headers,
                json={"bio": payload}
            )
            
            # Should either succeed (escaped) or fail with validation error
            if response.status_code == 200:
                # Verify bio was properly escaped
                user_response = await async_client.get(f"/api/v1/users/{user.id}", headers=headers)
                user_data = user_response.json()
                assert payload in user_data["bio"]
            elif response.status_code in [422, 400]:
                # Validation error - acceptable
                assert True
            else:
                assert False, f"Unexpected status code {response.status_code} for bio payload: {payload}"

 