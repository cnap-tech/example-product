# Database Architecture

This directory contains the database configuration and utilities for the NotesNest application.

## Files

### `database.py`

Core database configuration with both async and sync capabilities:

- **DatabaseConfig**: Centralized configuration management
- **Lazy Engine Initialization**: Engines are created only when needed, respecting environment variables
- **Dual Engine Support**: Both async and sync engines for different use cases
- **Environment-Aware**: Automatically switches to test database when `TESTING=true`

### `utils.py`

Database utility functions for common operations:

- **DatabaseUtils**: Class with common user lookup operations
- **Sync and Async Methods**: Parallel implementations for different contexts
- **Error Handling**: Proper exception handling for database operations

## Architecture Decisions

### 1. Dual Engine Approach

We maintain both async and sync engines because:

- **FastAPI Routes**: Use async sessions for better performance
- **Middleware**: Uses sync sessions to avoid async complexity in middleware
- **Tests**: Use sync sessions for simpler test management

### 2. Lazy Initialization

Engines are created lazily to:

- **Respect Environment Variables**: Test environment can set variables before engine creation
- **Avoid Import-Time Errors**: Database connection errors don't occur during module import
- **Support Multiple Environments**: Same code works in development, production, and testing

### 3. Centralized Configuration

The `DatabaseConfig` class provides:

- **Single Source of Truth**: All database URL logic in one place
- **Environment Detection**: Automatic test database selection
- **Driver Management**: Handles async/sync driver differences automatically

## Usage Examples

### Basic Session Usage

```python
# Async usage (for FastAPI routes)
from db.database import get_session

async def my_route(session: Session = Depends(get_session)):
    # Use session for database operations
    pass

# Sync usage (for utilities/middleware)
from db.database import get_sync_session

def my_function():
    for session in get_sync_session():
        # Use session for database operations
        break
```

### Using Database Utils

```python
from db.utils import DatabaseUtils

# Sync operations (for middleware)
user = DatabaseUtils.get_user_by_id_sync(user_id)

# Async operations (for routes)
user = await DatabaseUtils.get_user_by_id_async(user_id)
```

### Testing

Tests automatically use the test database when `TESTING=true` environment variable is set:

```python
# In conftest.py
os.environ["TESTING"] = "true"

# This will automatically use the test database
from db.database import get_sync_engine
```

## Environment Variables

- `DATABASE_URL`: Production database URL (default: postgres://postgres:postgres@db:5432/notesnest)
- `TESTING`: When set to "true", uses test database at localhost:5433

## Database URLs

The system automatically handles driver differences:

- **Async**: `postgresql+asyncpg://...`
- **Sync**: `postgresql://...`
- **Test**: Always uses `localhost:5433` with appropriate driver

## Migration Notes

If you're migrating from the old database setup:

1. **Import Changes**:

   - Old: `from db.database import get_session, engine`
   - New: `from db.database import get_session, get_sync_engine`

2. **Engine Access**:

   - Old: Direct `engine` variable
   - New: `get_sync_engine()` or `get_async_engine()` functions

3. **Utilities**:
   - Old: Manual session management everywhere
   - New: Use `DatabaseUtils` for common operations
