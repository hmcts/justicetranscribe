import base64
import json
import os
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Header
from sqlmodel import Session, select

from app.database.postgres_database import get_session
from app.database.postgres_models import User
from utils.jwt_verification import jwt_verification_service

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
    x_ms_client_principal: Annotated[Optional[str], Header()] = None,
    authorization: Annotated[Optional[str], Header()] = None
) -> User:
    """
    Get or create the current user with defense-in-depth:
    1. Azure Easy Auth headers (primary)
    2. JWT signature verification (secondary)
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
            # PRIMARY: Parse Azure Easy Auth headers
            decoded_info = base64.b64decode(x_ms_client_principal).decode("utf-8")
            user_info = json.loads(decoded_info)

            # Extract user details from Easy Auth
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

            print(f"✅ Easy Auth validation passed - ID: {azure_user_id}, Email: {email}")

            # SECONDARY: JWT signature verification (defense in depth)
            jwt_token = None
            if authorization and authorization.startswith("Bearer "):
                jwt_token = authorization[7:]  # Remove "Bearer " prefix
                
            if jwt_token:
                try:
                    decoded_jwt = await jwt_verification_service.verify_jwt_token(jwt_token)
                    if decoded_jwt:
                        # Cross-validate Easy Auth claims with JWT claims
                        jwt_email = decoded_jwt.get("email") or decoded_jwt.get("preferred_username", "")
                        jwt_user_id = decoded_jwt.get("oid", "")
                        
                        # Verify that Easy Auth and JWT claims match
                        if jwt_email and jwt_email != email:
                            print(f"⚠️ Email mismatch: Easy Auth={email}, JWT={jwt_email}")
                            if jwt_verification_service.strict_mode:
                                raise HTTPException(
                                    status_code=401, 
                                    detail="Authentication claims mismatch between Easy Auth and JWT"
                                )
                        
                        if jwt_user_id and jwt_user_id != azure_user_id:
                            print(f"⚠️ User ID mismatch: Easy Auth={azure_user_id}, JWT={jwt_user_id}")
                            if jwt_verification_service.strict_mode:
                                raise HTTPException(
                                    status_code=401, 
                                    detail="User ID mismatch between Easy Auth and JWT"
                                )
                        
                        print(f"✅ JWT signature verification passed - Additional security layer confirmed")
                    else:
                        print(f"ℹ️ JWT verification skipped or failed non-strictly")
                except Exception as e:
                    print(f"⚠️ JWT verification error: {e}")
                    # In non-strict mode, JWT verification failure doesn't block the request
                    if jwt_verification_service.strict_mode:
                        raise
            else:
                if jwt_verification_service.strict_mode:
                    raise HTTPException(
                        status_code=401, 
                        detail="JWT token required for strict verification mode"
                    )
                print("ℹ️ No JWT token provided for secondary verification")

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
