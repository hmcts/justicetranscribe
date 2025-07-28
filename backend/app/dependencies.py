import json
import base64
import os
from typing import Annotated, Optional
from pydantic import BaseModel
from fastapi import Header, HTTPException, Depends
from sqlmodel import Session
from .database import get_session
from .services import UserService
from .auth_models import AuthUser


def is_local_development() -> bool:
    print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'local')}")
    """Check if we're running in local development mode"""
    return os.getenv("ENVIRONMENT", "local").lower() in ["local"] 


def get_mock_user() -> AuthUser:
    """Return a mock user for local development"""
    return AuthUser(
        user_id="local-dev-user-123",
        name="Local Developer",
        email="developer@localhost.com",
        roles=["developer", "admin"]
    )


async def get_current_user(
    x_ms_client_principal: Annotated[Optional[str], Header()] = None
) -> AuthUser:
    """
    Extract user information from Azure App Service Easy Auth headers in production,
    or return mock user data for local development.
    """
    
    # Local development mode - return mock user
    if is_local_development():
        print("🔧 Local development mode: Using mock authentication")
        return get_mock_user()
    
    # Production mode - MUST have Easy Auth headers
    if not x_ms_client_principal:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Please ensure Easy Auth is properly configured."
        )
    
    try:
        # The header is base64 encoded JSON
        decoded_info = base64.b64decode(x_ms_client_principal).decode('utf-8')
        user_info = json.loads(decoded_info)
        
        # Extract user details from the Easy Auth payload
        user_id = user_info.get('userId', '')
        name = user_info.get('userDetails', '')
        
        # Get email from claims - this MUST exist in corporate environments
        email = ''
        claims = user_info.get('claims', [])
        for claim in claims:
            if claim.get('typ') in ['email', 'preferred_username', 'upn']:
                email = claim.get('val', '')
                break
        
        # Email is required - fail fast if missing
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed: email claim missing from Azure AD token"
            )
        
        # Use email as user_id if userId is empty (which it is in your case)
        if not user_id:
            user_id = email
        
        print(f"✅ Authenticated user - ID: {user_id}, Name: {name}, Email: {email}")
        
        return AuthUser(
            user_id=user_id,
            name=name or email.split('@')[0],  # Simple fallback: part before @
            email=email,
            roles=[]  # Extract roles if needed later
        )
        
    except (json.JSONDecodeError, base64.binascii.Error) as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication information: {str(e)}"
        )

def get_current_db_user(
    session: Session = Depends(get_session),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get or create the current user in the database"""
    from .models import User as DBUser  # Import here to avoid circular imports
    
    # In local development, we might want to create a test user
    if is_local_development():
        # Try to get or create a local test user
        return UserService.get_or_create_user(session, current_user)
    
    # In production, get or create user based on Azure AD info
    return UserService.get_or_create_user(session, current_user)