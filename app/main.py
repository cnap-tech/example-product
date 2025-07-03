from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.database import init_db
from app.routers.user import router as user_router
from app.routers.auth import router as auth_router
from app.routers.friends import router as friends_router
from app.routers.notes import router as notes_router
from app.middleware.auth import AuthenticationMiddleware
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database only if not in testing mode
    if not os.getenv("TESTING"):
        await init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Add authentication middleware
app.add_middleware(AuthenticationMiddleware)

# Include routers
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(user_router, prefix="/api/v1", tags=["users"])
app.include_router(friends_router, prefix="/api/v1", tags=["friends"])
app.include_router(notes_router, prefix="/api/v1", tags=["notes"]) 