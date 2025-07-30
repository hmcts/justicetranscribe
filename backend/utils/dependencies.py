import json
import base64
import os
from typing import Annotated, Optional
from fastapi import Header, HTTPException, Depends
from sqlmodel import Session, select

from app.database.postgres_database import get_session
from app.database.postgres_models import User


def is_local_development() -> bool:
    """Check if we're running in local development mode"""
    return os.getenv("ENVIRONMENT", "local").lower() in ["local"]


def get_mock_user_data() -> dict:
    """Return mock user data for local development"""
    return {
        "user_id": "local-dev-user-123", 
        "name": "Local Developer",
        "email": "developer@localhost.com"
    }


async def get_current_user(
    session: Session = Depends(get_session),
    x_ms_client_principal: Annotated[Optional[str], Header()] = None
) -> User:
    """
    Get or create the current user from Azure Easy Auth headers in production,
    or return mock user for local development.
    """
    
    # Local development mode
    if is_local_development():
        print("🔧 Local development mode: Using mock authentication")
        user_data = get_mock_user_data()
        email = user_data["email"]
        azure_user_id = user_data["user_id"]
        name = user_data["name"]
    else:
        # Production mode - MUST have Easy Auth headers
        if not x_ms_client_principal:
            raise HTTPException(
                status_code=401, 
                detail="Authentication required. Please ensure Easy Auth is properly configured."
            )

        try:
            # Parse Azure Easy Auth headers
            decoded_info = base64.b64decode(x_ms_client_principal).decode("utf-8")
            user_info = json.loads(decoded_info)

            # Extract user details
            azure_user_id = user_info.get("userId", "")
            name = user_info.get("userDetails", "")

            # Get email from claims
            email = ""
            claims = user_info.get("claims", [])
            for claim in claims:
                if claim.get("typ") in ["email", "preferred_username", "upn"]:
                    email = claim.get("val", "")
                    break

            if not email:
                raise HTTPException(
                    status_code=401, 
                    detail="Authentication failed: email claim missing from Azure AD token"
                )

            # Use email as user_id if userId is empty
            if not azure_user_id:
                azure_user_id = email

            print(f"✅ Authenticated user - ID: {azure_user_id}, Name: {name}, Email: {email}")

        except (json.JSONDecodeError, base64.binascii.Error) as e:
            raise HTTPException(status_code=401, detail=f"Invalid authentication information: {str(e)}")

    # Get or create user in database
    statement = select(User).where(User.azure_user_id == azure_user_id)
    user = session.exec(statement).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            azure_user_id=azure_user_id
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"✅ Created new user: {email}")
    else:
        print(f"✅ Found existing user: {email}")
    
    return user
