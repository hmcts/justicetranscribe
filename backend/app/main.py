import os
from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .dependencies import get_current_user, is_local_development
from .internal import admin
from .routers import items, users
from .auth_models import AuthUser

# Only import CORS middleware if we're in local development
if is_local_development():
    from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 FastAPI application starting up...")
    print(f"🔧 Environment: {'Local Development' if is_local_development() else 'Production'}")
  
    
    print("📚 API Documentation available at: /docs")
    
    yield
    
    # Shutdown
    print("🛑 FastAPI application shutting down...")


# Create FastAPI app
app = FastAPI(
    title="justicetranscribe API",
    description="FastAPI backend with Azure AD authentication and PostgreSQL database",
    lifespan=lifespan
)

# Configure CORS only for local development
# In production, Azure App Service handles CORS automatically
if is_local_development():
    print("🔧 Configuring CORS for local development")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",  # In case you run on different ports
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add routers
app.include_router(users.router)
app.include_router(items.router)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_user)],
    responses={418: {"description": "I'm a teapot"}},
)


@app.get("/health")
async def health_check():
    """Health check endpoint - no auth required"""
    return {"status": "healthy", "environment": "local" if is_local_development() else "production"}


@app.get("/")
async def root(current_user: AuthUser = Depends(get_current_user)):
    return {
        "message": "Hello Bigger Applications!", 
        "authenticated_user": {
            "name": current_user.name,
            "email": current_user.email,
            "user_id": current_user.user_id
        }
    }


@app.get("/user/profile")
async def get_user_profile(current_user: AuthUser = Depends(get_current_user)):
    """Example endpoint that returns current user information"""
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "roles": current_user.roles
    }


