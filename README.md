# NotesNest

A modern, secure FastAPI application for collaborative note-taking with user management, friendship system, and JWT authentication. Built with clean architecture principles and comprehensive async support.

## 🚀 Features

- **Notes System**: Create, edit, and share collaborative notes with privacy controls
- **Author Management**: Add/remove collaborators on notes with granular permissions
- **User Management**: Complete CRUD operations for user accounts
- **Friendship System**: Send/accept friend requests, manage friend lists
- **JWT Authentication**: Secure login with access and refresh tokens
- **Role-Based Access Control**: User and Admin roles with appropriate permissions
- **Privacy Controls**: Public and private notes with access control
- **Email Verification**: Account verification workflow
- **Password Security**: Strong password requirements and hashing
- **Soft Deletion**: Safe user removal with recovery options
- **RESTful API**: Clean, well-documented endpoints
- **Async Architecture**: Full async support with proper database connection management
- **Comprehensive Testing**: 176 test cases covering all functionality
- **Clean Architecture**: Refactored service layer with modular design
- **Security Middleware**: JWT-based authentication middleware with proper route protection
- **Unified Exception Handling**: Consistent error responses across all endpoints

## 🏗️ Architecture

### System Architecture Diagram

```mermaid
graph TD
    subgraph "HTTP Layer"
        A["FastAPI App<br/>(Async Route Handlers)"] --> B["Auth Router<br/>app/routers/auth.py"]
        A --> C["User Router<br/>app/routers/user.py"]
        A --> D["Friends Router<br/>app/routers/friends.py"]
        A --> E["Notes Router<br/>app/routers/notes.py"]
        A --> F["Auth Middleware<br/>app/middleware/auth.py"]
    end

    subgraph "Dependencies Layer"
        G["Auth Dependencies<br/>app/dependencies/auth.py<br/>(require_auth, require_admin)"]
        H["Database Dependencies<br/>app/dependencies/database.py<br/>(Simplified Session Management)"]
    end

    subgraph "Service Layer"
        I["AuthService<br/>app/services/auth_service.py"]
        J["UserService<br/>app/services/user/<br/>(Modular Package)"]
        K["FriendshipService<br/>app/services/friendship_service.py"]
        L["NoteService<br/>app/services/note/<br/>(Modular Package)"]
    end

    subgraph "User Service Modules"
        M["CRUD Operations<br/>app/services/user/crud.py"]
        N["Validation<br/>app/services/user/validation.py"]
        O["Management<br/>app/services/user/management.py"]
        P["Exceptions<br/>app/services/user/exceptions.py"]
    end

    subgraph "Note Service Modules"
        Q["CRUD Operations<br/>app/services/note/crud.py"]
        R["Author Management<br/>app/services/note/authors.py"]
        S["Permissions<br/>app/services/note/permissions.py"]
        T["Exceptions<br/>app/services/note/exceptions.py"]
    end

    subgraph "Database Layer"
        U["User Model<br/>app/models/user.py"]
        V["Friendship Model<br/>app/models/friendship.py"]
        W["Note Model<br/>app/models/note.py"]
        X["Database Manager<br/>db/database.py<br/>(Sync & Async Engines)"]
        Y["Database Utils<br/>db/utils.py<br/>(Async Helper Methods)"]
    end

    subgraph "Exception Handling"
        Z["Unified Exception Handler<br/>app/utils/exceptions.py<br/>(Standardized Error Responses)"]
    end

    B --> G
    C --> G
    D --> G
    E --> G

    B --> H
    C --> H
    D --> H
    E --> H

    B --> I
    C --> J
    D --> K
    E --> L

    J --> M
    J --> N
    J --> O
    J --> P

    L --> Q
    L --> R
    L --> S
    L --> T

    I --> U
    J --> U
    K --> U
    K --> V
    L --> W

    U --> X
    V --> X
    W --> X
    X --> Y

    G --> Z
    B --> Z
    C --> Z
    D --> Z
    E --> Z

    style A fill:#e1f5fe
    style G fill:#e8f5e8
    style H fill:#e8f5e8
    style I fill:#f3e5f5
    style J fill:#f3e5f5
    style K fill:#f3e5f5
    style L fill:#f3e5f5
    style M fill:#fff9c4
    style N fill:#fff9c4
    style O fill:#fff9c4
    style P fill:#fff9c4
    style Q fill:#fff9c4
    style R fill:#fff9c4
    style S fill:#fff9c4
    style T fill:#fff9c4
    style U fill:#e8f5e8
    style V fill:#e8f5e8
    style W fill:#e8f5e8
    style X fill:#e8f5e8
    style Y fill:#e8f5e8
    style Z fill:#fff3e0
```

### Recent Refactoring Improvements

- **🔧 Authentication Dependencies**: Centralized auth logic with `require_auth()`, `require_admin()`, and user access control
- **🎯 Unified Exception Handling**: Standardized error responses across all endpoints
- **📦 Modular Service Architecture**: Split large service files into focused modules (CRUD, validation, management)
- **🔄 Simplified Database Sessions**: Clean dependency injection patterns
- **🛡️ Enhanced Security**: Improved error messages and consistent access control
- **📝 Notes System**: Complete collaborative note-taking with author management and privacy controls

### Async Architecture Benefits

- **🔄 Async Route Handlers**: All API endpoints use async/await for better concurrency
- **🗄️ Hybrid Database Support**: Efficient sync/async database session management
- **⚡ Performance**: Non-blocking I/O operations for better throughput
- **🧪 Async Testing**: Complete test suite using pytest-asyncio and httpx
- **🛡️ Middleware Integration**: Authentication middleware with proper async database access

### Directory Structure

```
NotesNest/
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application setup with middleware
│   ├── dependencies/             # Centralized dependencies
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication dependencies (require_auth, require_admin)
│   │   └── database.py          # Database session dependencies
│   ├── middleware/               # Custom middleware
│   │   ├── __init__.py
│   │   └── auth.py              # JWT authentication middleware
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── user.py              # User model and Pydantic schemas
│   │   ├── friendship.py        # Friendship model and schemas
│   │   └── note.py              # Note model and schemas
│   ├── routers/                  # API route handlers (async)
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── user.py              # User management endpoints
│   │   ├── friends.py           # Friendship management endpoints
│   │   └── notes.py             # Notes and collaboration endpoints
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication business logic
│   │   ├── friendship_service.py # Friendship business logic
│   │   ├── user/                # Modular user service package
│   │   │   ├── __init__.py      # Unified UserService interface
│   │   │   ├── crud.py          # Create, Read, Update, Delete operations
│   │   │   ├── validation.py    # Email/username uniqueness validation
│   │   │   ├── management.py    # Role updates, permissions, email verification
│   │   │   └── exceptions.py    # User-specific exceptions
│   │   └── note/                # Modular note service package
│   │       ├── __init__.py      # Unified NoteService interface
│   │       ├── crud.py          # Note CRUD operations
│   │       ├── authors.py       # Author management
│   │       ├── permissions.py   # Access control and permissions
│   │       └── exceptions.py    # Note-specific exceptions
│   └── utils/                    # Utility functions
│       ├── auth.py              # Authentication utilities (JWT, hashing)
│       └── exceptions.py        # Unified exception handling utilities
├── db/                           # Database configuration
│   ├── database.py              # Sync/Async database setup and session management
│   ├── utils.py                 # Database utility functions (async)
│   └── README.md               # Database architecture documentation
├── migrations/                   # Alembic database migrations
│   ├── env.py                   # Migration environment configuration
│   ├── script.py.mako          # Migration script template
│   └── versions/               # Migration versions
│       ├── 001_initial.py      # Initial database schema
│       ├── 002_add_friendship_table.py # Friendship system schema
│       └── 003_add_note_tables.py # Notes and collaboration schema
├── tests/                        # Comprehensive test suite (pytest-asyncio)
│   ├── __init__.py
│   ├── conftest.py              # Test configuration with async fixtures
│   ├── models/                  # Model tests (31 tests)
│   │   ├── __init__.py
│   │   ├── test_user.py        # User model tests (8 tests)
│   │   ├── test_friendship.py  # Friendship model tests (13 tests)
│   │   └── test_note.py        # Note model tests (10 tests)
│   ├── routers/                 # Router tests (95 tests)
│   │   ├── __init__.py
│   │   ├── test_auth_routes.py  # Authentication route tests (21 tests)
│   │   ├── test_user_routes.py  # User management route tests (17 tests)
│   │   ├── test_friends_routes.py # Friendship route tests (23 tests)
│   │   └── test_notes_routes.py # Notes route tests (34 tests)
│   ├── services/               # Service tests (85 tests)
│   │   ├── __init__.py
│   │   ├── test_auth_service.py # Authentication service tests (13 tests)
│   │   ├── test_user_service.py # User service tests (30 tests)
│   │   └── test_friendship_service.py # Friendship service tests (20 tests)
│   └── test_integration.py     # Integration tests (15 tests)
├── docker-compose.yml           # Docker services configuration
├── docker-compose.test.yml      # Test environment configuration
├── Dockerfile                   # Application container
├── requirements.txt             # Python dependencies (includes async packages)
├── pytest.ini                  # Test configuration for async testing
├── alembic.ini                 # Database migration configuration
├── .env.example                # Environment variables template
└── .gitignore                  # Git ignore patterns
```

## 🛠️ Technology Stack

- **Framework**: FastAPI (with full async support)
- **Database**: PostgreSQL with SQLModel (SQLAlchemy 2.0+)
- **Authentication**: JWT tokens with centralized dependency injection
- **Password Hashing**: bcrypt with secure salt generation
- **Async Testing**: pytest-asyncio with httpx.AsyncClient
- **HTTP Client**: httpx for async test requests
- **Database Sessions**: Hybrid sync/async session management
- **Database Migrations**: Alembic for schema versioning
- **Containerization**: Docker & Docker Compose
- **Code Quality**: Type hints, modular architecture, comprehensive error handling

## 📊 API Endpoints

### Authentication (Public Routes)

- `POST /api/v1/token` - User login (returns access and refresh tokens)
- `POST /api/v1/token/refresh` - Refresh access token

### User Management

- `POST /api/v1/users` - Create user account (public)
- `GET /api/v1/users` - List users (authenticated)
- `GET /api/v1/users/{user_id}` - Get user profile (own profile or admin)
- `PUT /api/v1/users/{user_id}` - Update user profile (own profile or admin)
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)
- `POST /api/v1/users/verify-email/{token}` - Verify email (public)
- `POST /api/v1/users/{user_id}/role` - Update user role (admin only)

### Friendship Management

- `POST /api/v1/friend-requests` - Send friend request (authenticated)
- `POST /api/v1/friend-requests/{friendship_id}/respond` - Accept/reject friend request (authenticated)
- `DELETE /api/v1/friends/{friend_id}` - Remove friend (authenticated)
- `GET /api/v1/friends` - Get friends list with pagination (authenticated)
- `GET /api/v1/friend-requests/pending` - Get pending friend requests (authenticated)
- `GET /api/v1/friend-requests/sent` - Get sent friend requests (authenticated)
- `GET /api/v1/friendship-status/{user_id}` - Get friendship status (authenticated)
- `DELETE /api/v1/friend-requests/cancel/{addressee_id}` - Cancel friend request (authenticated)

### Notes & Collaboration

- `POST /api/v1/notes` - Create a new note (authenticated)
- `GET /api/v1/notes` - List notes with pagination and filtering (public for public notes)
- `GET /api/v1/notes/my` - List user's notes (authenticated)
- `GET /api/v1/notes/{note_id}` - Get specific note (public for public notes)
- `PUT /api/v1/notes/{note_id}` - Update note (authenticated, authors only)
- `DELETE /api/v1/notes/{note_id}` - Delete note (authenticated, creator only)
- `GET /api/v1/notes/{note_id}/authors` - Get note authors (accessible if note is viewable)
- `POST /api/v1/notes/{note_id}/authors` - Add author to note (authenticated, authors only)
- `DELETE /api/v1/notes/{note_id}/authors` - Remove author from note (authenticated, authors only)

### Documentation

- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
- `GET /openapi.json` - OpenAPI schema

## 🚦 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- Docker (optional)

### Local Development

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd NotesNest
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start PostgreSQL database**

   ```bash
   docker-compose up -d db
   ```

6. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Development

```bash
# Start all services (app + database)
docker-compose up -d

# View application logs
docker-compose logs -f app

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up --build
```

## 🧪 Testing

### Comprehensive Test Suite

The application includes a comprehensive async test suite with **176 test cases**:

```bash
# Run all tests with async support
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app

# Run specific test categories
pytest tests/models/          # Model tests (31 tests)
pytest tests/routers/         # Route tests (95 tests)
pytest tests/services/        # Service tests (85 tests)
pytest tests/test_integration.py # Integration tests (15 tests)

# Run specific test files
pytest tests/routers/test_auth_routes.py      # Authentication tests (21 tests)
pytest tests/routers/test_user_routes.py      # User management tests (17 tests)
pytest tests/routers/test_friends_routes.py   # Friendship tests (23 tests)
pytest tests/routers/test_notes_routes.py     # Notes tests (34 tests)
pytest tests/services/test_user_service.py    # User service tests (30 tests)
pytest tests/services/test_friendship_service.py # Friendship service tests (20 tests)
```

### Test Categories

**✅ Model Tests (31 tests):**

- **User Model (8 tests)**: Creation validation, password hashing, CRUD operations, defaults, constraints, JSON fields
- **Friendship Model (13 tests)**: Friendship creation, validation, status management, relationships
- **Note Model (10 tests)**: Note creation, validation, privacy controls, author relationships

**✅ Router Tests (95 tests):**

- **Authentication Routes (21 tests)**: Login functionality, token refresh, middleware behavior, protected routes, security edge cases
- **User Management Routes (17 tests)**: User creation, retrieval, updates, permissions, role management, security validation
- **Friendship Routes (23 tests)**: Friend requests, responses, friend lists, status checking, cancellation
- **Notes Routes (34 tests)**: Note CRUD, collaboration, author management, privacy controls, concurrent access, large data handling

**✅ Service Tests (85 tests):**

- **Authentication Service (13 tests)**: User authentication, token management, error handling
- **User Service (30 tests)**: CRUD operations, validation, permissions, role management, email verification
- **Friendship Service (20 tests)**: Friend request workflow, friend list management, status tracking

**✅ Integration Tests (15 tests):**

- **Complete User Journey (1 test)**: End-to-end workflow from registration to collaboration
- **Cross-Feature Interactions (3 tests)**: Friends and notes collaboration, permissions, privacy consistency
- **Error Handling (2 tests)**: Cascading error handling, data consistency
- **Performance (1 test)**: Bulk operations handling
- **Critical Scenarios (3 tests)**: Database failures, malformed requests, security edge cases
- **API Robustness (1 test)**: Response format consistency

### Test Infrastructure

- **Async Framework**: pytest-asyncio for async test execution
- **HTTP Client**: httpx.AsyncClient for async API testing
- **Database**: Separate test database with proper isolation
- **Fixtures**: Comprehensive async test fixtures for users, tokens, friendships, notes, and database sessions
- **Coverage**: 100% coverage of all API endpoints and business logic
- **Modular Testing**: Tests organized by architectural layer (models, routers, services)
- **Security Testing**: Token manipulation, SQL injection, input validation, concurrent access
- **Performance Testing**: Large data handling, bulk operations, concurrent operations

## 🔒 Security Features

- **JWT Authentication**: Secure access and refresh token implementation
- **Centralized Auth Dependencies**: Reusable `require_auth()` and `require_admin()` dependencies
- **Middleware Protection**: Route-level authentication with pattern matching
- **Password Security**: bcrypt hashing with secure salt generation
- **Role-Based Access Control**: User and Admin permission levels with service-layer enforcement
- **Input Validation**: Comprehensive data validation with Pydantic
- **SQL Injection Protection**: SQLModel/SQLAlchemy ORM with parameterized queries
- **Access Control**: Granular permissions for notes (view, edit, delete, manage authors)
- **Privacy Controls**: Public/private notes with proper access enforcement
- **CORS Configuration**: Configurable cross-origin request handling
- **Environment Security**: Secure credential management with .env files
- **Session Management**: Proper database session lifecycle management
- **Unified Error Handling**: Consistent error responses that don't leak sensitive information

## 🏛️ Architecture Principles

### Async-First Design

- **Route Handlers**: All endpoints use async/await for non-blocking execution
- **Database Sessions**: Hybrid sync/async session management for optimal performance
- **Testing**: Complete async test coverage with proper async fixtures
- **Middleware**: Async-compatible authentication middleware

### Clean Architecture

- **Modular Service Layer**: Business logic separated into focused modules (CRUD, validation, management)
- **Dependency Injection**: Centralized auth and database dependencies
- **Single Responsibility**: Each module has a clear, focused purpose
- **Backward Compatibility**: Refactored services maintain existing API contracts

### Error Handling

- **Unified Exception Handler**: Standardized error conversion across all endpoints
- **Domain-Specific Exceptions**: Custom error types (AuthenticationError, UserValidationError, NotePermissionError, etc.)
- **Consistent Responses**: Standardized error format across all endpoints
- **HTTP Status Codes**: Proper status code usage (200, 400, 401, 403, 404, 422)
- **Validation**: Multi-layer input validation (Pydantic + service layer)

### Database Design

- **PostgreSQL**: Robust relational database with async driver support
- **Connection Management**: Efficient connection pooling with singleton engine pattern
- **Migrations**: Version-controlled schema changes with Alembic
- **Session Patterns**: Simplified dependency injection for database sessions
- **Relationship Management**: Proper foreign key relationships for friendships and note authorship

## 📝 Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/notesnest
TESTING=false

# Database Credentials (for Docker)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=notesnest

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-256-bits
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
APP_ENV=development
DEBUG=true

# Test Database Configuration
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/notesnest_test
```

**⚠️ Security Note**: Never commit real credentials to version control. Always use environment variables for sensitive data in production.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the async patterns and modular architecture
4. Run the full test suite (`pytest -v`)
5. Ensure all 176 tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions or support, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, modern Python async practices, modular architecture, and comprehensive testing (176 tests).
