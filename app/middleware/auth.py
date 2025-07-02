from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.models.user import User, UserRole
from app.utils.auth import verify_token
from db.utils import DatabaseUtils
from typing import Optional, Set, Tuple
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)


class AuthScheme(str, Enum):
    """Authentication scheme constants."""
    BEARER = "bearer"


class TokenType(str, Enum):
    """JWT token type constants."""
    ACCESS = "access"
    REFRESH = "refresh"


class HTTPMethod(str, Enum):
    """HTTP method constants."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


def get_current_user(request: Request) -> Optional[User]:
    """
    Extract current user from request.
    Returns None if not authenticated or user not found.
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        return None
    
    try:
        return DatabaseUtils.get_user_by_id_sync(user_id)
    except Exception as e:
        logger.error(f"Database error fetching user {user_id}: {e}")
        return None


def get_admin_user(request: Request) -> User:
    """
    Get current user and ensure they are an admin.
    Raises HTTPException if not authenticated or not admin.
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling JWT authentication.
    
    Routes can be configured as:
    - PUBLIC: No authentication required
    - PROTECTED: Authentication required
    - ADMIN_ONLY: Admin authentication required
    """
    
    # Define public routes that don't require authentication
    PUBLIC_ROUTES: Set[Tuple[str, str]] = {
        ("/api/v1/users", HTTPMethod.POST),              # User registration
        ("/api/v1/token", HTTPMethod.POST),              # Login
        ("/api/v1/token/refresh", HTTPMethod.POST),      # Token refresh
        ("/api/v1/users/verify-email/{token}", HTTPMethod.POST),  # Email verification
        ("/docs", HTTPMethod.GET),                       # API docs
        ("/redoc", HTTPMethod.GET),                      # ReDoc docs
        ("/openapi.json", HTTPMethod.GET),               # OpenAPI schema
        ("/", HTTPMethod.GET),                           # Root endpoint
        ("/health", HTTPMethod.GET),                     # Health check
    }
    
    # Routes that require admin access - let service layer handle authorization
    ADMIN_ROUTES: Set[Tuple[str, str]] = {
        # Remove these to let service layer handle authorization
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and apply authentication logic."""
        path = request.url.path
        method = request.method.upper()
        
        # Check if route is public
        if self._is_public_route(path, method):
            return await call_next(request)
        
        # Extract and verify token
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token"}
            )
        
        try:
            # Verify token and extract user info
            payload = verify_token(token, TokenType.ACCESS)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user and verify status
            user = DatabaseUtils.get_user_by_id_sync(user_id)
            if not user or not user.is_active:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User account inactive or not found"}
                )
            
            # Check admin access if required
            if self._requires_admin(path, method) and user.role != UserRole.ADMIN:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Admin access required"}
                )
            
            # Store user info in request state
            request.state.user_id = user.id
            request.state.user = user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        return await call_next(request)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract bearer token from Authorization header."""
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != AuthScheme.BEARER.value:
            return None
        
        return token
    
    def _is_public_route(self, path: str, method: str) -> bool:
        """Check if a route is public (no authentication required)."""
        # Direct match
        if (path, method) in self.PUBLIC_ROUTES:
            return True
        
        # Pattern matching for dynamic routes
        for route_pattern, route_method in self.PUBLIC_ROUTES:
            if route_method == method and self._matches_pattern(path, route_pattern):
                return True
        
        return False
    
    def _requires_admin(self, path: str, method: str) -> bool:
        """Check if a route requires admin access."""
        # Direct match
        if (path, method) in self.ADMIN_ROUTES:
            return True
        
        # Pattern matching for dynamic routes
        for route_pattern, route_method in self.ADMIN_ROUTES:
            if route_method == method and self._matches_pattern(path, route_pattern):
                return True
        
        return False
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching for routes with path parameters."""
        import re
        
        # Replace {param} placeholders with regex pattern for path parameters
        # e.g., "/users/{user_id}" becomes "/users/[^/]+"
        regex_pattern = re.sub(r'\{[^}]+\}', '[^/]+', pattern)
        
        # Escape any remaining special regex characters
        regex_pattern = re.escape(regex_pattern).replace(r'\[', '[').replace(r'\]', ']').replace(r'\+', '+').replace(r'\^', '^')
        
        # Add anchors for exact matching
        regex_pattern = f"^{regex_pattern}$"
        
        return bool(re.match(regex_pattern, path)) 