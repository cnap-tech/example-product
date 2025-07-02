from sqlmodel import SQLModel, Field, JSON
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import EmailStr, field_validator

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(SQLModel, table=True):
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Basic user info
    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(unique=True, index=True)
    name: str
    age: Optional[int] = None
    bio: Optional[str] = None
    
    # Authentication
    hashed_password: str
    role: UserRole = Field(default=UserRole.USER)
    
    # Account status
    is_active: bool = Field(default=True)
    is_email_verified: bool = Field(default=False)
    email_verification_token: Optional[str] = None
    
    # Optional JSON data
    social_links: Dict[str, Optional[str]] = Field(
        default={"facebook": None, "twitter": None, "linkedin": None, "instagram": None, "github": None},
        sa_type=JSON
    )
    address: Dict[str, Optional[str]] = Field(
        default={"street": None, "city": None, "state": None, "country": "", "postal_code": None},
        sa_type=JSON
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class UserCreate(SQLModel):
    username: str
    email: EmailStr
    name: str
    password: str
    age: Optional[int] = None
    bio: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserRead(SQLModel):
    id: int
    username: str
    email: EmailStr
    name: str
    age: Optional[int] = None
    bio: Optional[str] = None
    is_active: bool
    is_email_verified: bool
    role: UserRole
    social_links: Dict[str, Optional[str]] = {}
    address: Dict[str, Optional[str]] = {}
    created_at: datetime
    updated_at: datetime

class UserLogin(SQLModel):
    username: str
    password: str

class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(SQLModel):
    refresh_token: str

class UserUpdate(SQLModel):
    name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None