# NotesNest

A modern, secure FastAPI application for user management with JWT authentication, built with clean architecture principles and comprehensive async support.

## 🚀 Features

- **User Management**: Complete CRUD operations for user accounts
- **JWT Authentication**: Secure login with access and refresh tokens
- **Role-Based Access Control**: User and Admin roles with appropriate permissions
- **Email Verification**: Account verification workflow
- **Password Security**: Strong password requirements and hashing
- **Soft Deletion**: Safe user removal with recovery options
- **RESTful API**: Clean, well-documented endpoints
- **Async Architecture**: Full async support with proper database connection management
- **Comprehensive Testing**: 43 async test cases covering all functionality
- **Clean Architecture**: Service layer separation for maintainable code
- **Security Middleware**: JWT-based authentication middleware with proper route protection

## 🏗️ Architecture

### System Architecture Diagram

```mermaid
graph TD
    subgraph "HTTP Layer"
        A["FastAPI App<br/>(Async Route Handlers)"] --> B["Auth Router<br/>app/routers/auth.py"]
        A --> C["User Router<br/>app/routers/user.py"]
        A --> D["Auth Middleware<br/>app/middleware/auth.py"]
    end

    subgraph "Service Layer"
        E["AuthService<br/>app/services/auth_service.py<br/>(Sync & Async Methods)"]
        F["UserService<br/>app/services/user_service.py<br/>(Sync & Async Methods)"]
    end

    subgraph "Database Layer"
        G["User Model<br/>app/models/user.py"]
        H["Database Manager<br/>db/database.py<br/>(Sync & Async Engines)"]
        I["Database Utils<br/>db/utils.py<br/>(Async Helper Methods)"]
    end

    subgraph "Exception Handling"
        J["Custom Exceptions<br/>AuthenticationError<br/>UserValidationError<br/>UserNotFoundError<br/>PermissionError"]
        K["Exception Utils<br/>app/utils/exceptions.py"]
    end

    B --> E
    C --> F
    D --> I

    E --> G
    F --> G

    G --> H
    H --> I

    E --> J
    F --> J

    B -.-> K
    C -.-> K

    style A fill:#e1f5fe
    style E fill:#f3e5f5
    style F fill:#f3e5f5
    style G fill:#e8f5e8
    style H fill:#e8f5e8
    style I fill:#e8f5e8
    style J fill:#fff3e0
    style K fill:#fff3e0
```

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
│   ├── middleware/               # Custom middleware
│   │   ├── __init__.py
│   │   └── auth.py              # JWT authentication middleware
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   └── user.py              # User model and Pydantic schemas
│   ├── routers/                  # API route handlers (async)
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints
│   │   └── user.py              # User management endpoints
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── README.md            # Service layer documentation
│   │   ├── auth_service.py      # Authentication business logic
│   │   └── user_service.py      # User management business logic
│   └── utils/                    # Utility functions
│       ├── auth.py              # Authentication utilities (JWT, hashing)
│       └── exceptions.py        # Exception handling utilities
├── db/                           # Database configuration
│   ├── database.py              # Sync/Async database setup and session management
│   ├── utils.py                 # Database utility functions (async)
│   └── README.md               # Database architecture documentation
├── migrations/                   # Alembic database migrations
│   ├── env.py                   # Migration environment configuration
│   ├── script.py.mako          # Migration script template
│   └── versions/               # Migration versions
│       └── 001_initial.py      # Initial database schema
├── tests/                        # Async test suite (pytest-asyncio)
│   ├── __init__.py
│   ├── conftest.py              # Test configuration with async fixtures
│   ├── models/                  # Model tests
│   │   ├── __init__.py
│   │   └── test_user.py        # User model tests (async)
│   └── routers/                 # Router tests
│       ├── __init__.py
│       ├── test_auth_routes.py  # Authentication route tests (async)
│       └── test_user_routes.py  # User management route tests (async)
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
- **Authentication**: JWT tokens with middleware-based protection
- **Password Hashing**: bcrypt with secure salt generation
- **Async Testing**: pytest-asyncio with httpx.AsyncClient
- **HTTP Client**: httpx for async test requests
- **Database Sessions**: Hybrid sync/async session management
- **Database Migrations**: Alembic for schema versioning
- **Containerization**: Docker & Docker Compose
- **Code Quality**: Type hints, clean architecture, comprehensive error handling

## 📊 API Endpoints

### Authentication (Public Routes)

- `POST /api/v1/token` - User login
- `POST /api/v1/token/refresh` - Refresh access token

### User Management

- `POST /api/v1/users` - Create user account (public)
- `GET /api/v1/users` - List users (authenticated)
- `GET /api/v1/users/{user_id}` - Get user profile (own profile or admin)
- `PUT /api/v1/users/{user_id}` - Update user profile (own profile or admin)
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)
- `POST /api/v1/users/verify-email/{token}` - Verify email (public)
- `POST /api/v1/users/{user_id}/role` - Update user role (admin only)

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

### Async Test Suite

The application includes a comprehensive async test suite with 43 test cases:

```bash
# Run all tests with async support
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app

# Run specific test categories
pytest tests/models/          # Model tests (8 tests)
pytest tests/routers/         # Route tests (35 tests)

# Run specific test files
pytest tests/routers/test_auth_routes.py    # Authentication tests (18 tests)
pytest tests/routers/test_user_routes.py    # User management tests (17 tests)
```

### Test Categories

**✅ User Model Tests (8 tests):**

- User creation validation
- Password validation and hashing
- CRUD operations with async database
- Default values and constraints
- JSON field updates (social_links, address)

**✅ Authentication Route Tests (18 tests):**

- Login functionality (success/failure scenarios)
- Token refresh operations (public route)
- Authentication middleware behavior
- Protected vs public route access
- Token validation and expiration handling
- Inactive/deleted user token invalidation

**✅ User Management Route Tests (17 tests):**

- User creation and validation
- User retrieval and listing (with authentication)
- Profile updates and permissions
- Role management (admin-only operations)
- Email verification (public route)
- Authorization and access control
- Service-layer error handling

### Test Infrastructure

- **Async Framework**: pytest-asyncio for async test execution
- **HTTP Client**: httpx.AsyncClient for async API testing
- **Database**: Separate test database with proper isolation
- **Fixtures**: Async test fixtures for users, tokens, and database sessions
- **Coverage**: Comprehensive coverage of all API endpoints and business logic

## 🔒 Security Features

- **JWT Authentication**: Secure access and refresh token implementation
- **Middleware Protection**: Route-level authentication with pattern matching
- **Password Security**: bcrypt hashing with secure salt generation
- **Role-Based Access Control**: User and Admin permission levels with service-layer enforcement
- **Input Validation**: Comprehensive data validation with Pydantic
- **SQL Injection Protection**: SQLModel/SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Configurable cross-origin request handling
- **Environment Security**: Secure credential management with .env files
- **Session Management**: Proper database session lifecycle management

## 🏛️ Architecture Principles

### Async-First Design

- **Route Handlers**: All endpoints use async/await for non-blocking execution
- **Database Sessions**: Hybrid sync/async session management for optimal performance
- **Testing**: Complete async test coverage with proper async fixtures
- **Middleware**: Async-compatible authentication middleware

### Clean Architecture

- **Service Layer**: Business logic separated from HTTP concerns
- **Repository Pattern**: Database operations abstracted through services
- **Dependency Injection**: Loose coupling with FastAPI's dependency system
- **Single Responsibility**: Each module has a clear, focused purpose

### Error Handling

- **Custom Exceptions**: Domain-specific error types (AuthenticationError, UserValidationError, etc.)
- **Consistent Responses**: Standardized error format across all endpoints
- **HTTP Status Codes**: Proper status code usage (200, 400, 401, 403, 404, 422)
- **Validation**: Multi-layer input validation (Pydantic + service layer)

### Database Design

- **PostgreSQL**: Robust relational database with async driver support
- **Connection Management**: Efficient connection pooling with singleton engine pattern
- **Migrations**: Version-controlled schema changes with Alembic
- **Session Patterns**: Proper async/sync session handling for different use cases

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
3. Make your changes following the async patterns
4. Run the full test suite (`pytest -v`)
5. Ensure all 43 tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] Email service integration with async SMTP
- [ ] Password reset functionality
- [ ] User profile pictures with async file handling
- [ ] API rate limiting middleware
- [ ] Audit logging with async database writes
- [ ] Social media authentication (OAuth2)
- [ ] Advanced user search and filtering
- [ ] Real-time notifications with WebSockets
- [ ] Background task processing with Celery
- [ ] Caching layer with Redis

## 📞 Support

For questions or support, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, modern Python async practices, and comprehensive testing.
