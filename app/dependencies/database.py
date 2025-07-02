"""Database dependencies for FastAPI routes."""

from sqlmodel import Session
from fastapi import Depends
from db.database import get_session_for_services


def get_db() -> Session:
    """
    Standard database session dependency.
    Provides a clean interface for all route handlers.
    """
    return Depends(get_session_for_services)


# Alias for backward compatibility
DBSession = Depends(get_session_for_services) 