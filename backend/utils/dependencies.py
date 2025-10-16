import base64
import json
import logging
import os
from typing import Annotated

import sentry_sdk
from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from app.database.postgres_database import get_session
from app.database.postgres_models import User
from utils.allowlist import get_allowlist_cache
from utils.email_utils import emails_match
from utils.jwt_verification import jwt_verification_service
from utils.settings import get_settings

logger = logging.getLogger(__name__)


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

async def get_current_user(  # noqa: C901, PLR0912, PLR0915
    session: Session = Depends(get_session),  # noqa: B008
    x_ms_client_principal: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None
) -> User:
    """
    Get or create the current user with defense-in-depth:
    1. Azure Easy Auth headers (primary)
    2. JWT signature verification (secondary)
    """

    # Local development mode
    if is_local_development():
        logger.info("Local development mode: Using mock authentication")
        user_data = get_mock_user_data()
        email = user_data["email"]
        azure_user_id = user_data["user_id"]
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

            # SECONDARY: JWT signature verification (defense in depth)
            jwt_token = None
            jwt_user_id = None
            if authorization and authorization.startswith("Bearer "):
                jwt_token = authorization[7:]  # Remove "Bearer " prefix

            if jwt_token:
                try:
                    decoded_jwt = await jwt_verification_service.verify_jwt_token(jwt_token)
                    if decoded_jwt:
                        # Cross-validate Easy Auth claims with JWT claims
                        jwt_email = decoded_jwt.get("email") or decoded_jwt.get("preferred_username", "")
                        jwt_user_id = decoded_jwt.get("oid", "")

                        # Verify that Easy Auth and JWT user identities match via oid (case-insensitive)
                        if jwt_user_id and azure_user_id and jwt_user_id.lower() != azure_user_id.lower():
                            logger.error(
                                "User ID mismatch - potential spoofing attempt: Easy Auth oid=%s, JWT oid=%s",
                                azure_user_id,
                                jwt_user_id
                            )
                            if jwt_verification_service.strict_mode:
                                raise HTTPException(
                                    status_code=401,
                                    detail="Authentication claims mismatch between Easy Auth and JWT"
                                )

                        # Log email differences for observability (expected when emails change)
                        if jwt_email and not emails_match(email, jwt_email):
                            logger.info(
                                "Email differs between Easy Auth and JWT (user identity verified): Easy Auth=%s, JWT=%s",
                                email,
                                jwt_email
                            )

                        logger.info("JWT signature verification passed - Additional security layer confirmed")
                    else:
                        logger.info("JWT verification skipped or failed non-strictly")
                except Exception as e:
                    logger.warning("JWT verification error: %s", e)
                    # In non-strict mode, JWT verification failure doesn't block the request
                    if jwt_verification_service.strict_mode:
                        raise
            else:
                if jwt_verification_service.strict_mode:
                    raise HTTPException(
                        status_code=401,
                        detail="JWT token required for strict verification mode"
                    )
                logger.info("No JWT token provided for secondary verification")

            # Use JWT user ID as the primary identifier if available (more reliable)
            # Fall back to Easy Auth userId, then email as last resort
            if jwt_user_id:
                azure_user_id = jwt_user_id
                logger.info("Using JWT object ID as primary user identifier: %s", azure_user_id)
            elif azure_user_id:
                logger.info("Using Easy Auth userId: %s", azure_user_id)
            else:
                azure_user_id = email
                logger.info("Falling back to email as user identifier: %s", azure_user_id)

            logger.info("Authentication validated - ID: %s, Email: %s", azure_user_id, email)

        except (json.JSONDecodeError, base64.binascii.Error) as e:
            raise HTTPException(status_code=401, detail=f"Invalid authentication information: {e!s}") from e

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
        logger.info("Created new user: %s", email)
    else:
        logger.info("Found existing user: %s", email)

    return user


async def get_allowlisted_user(
    current_user: User = Depends(get_current_user)  # noqa: B008
) -> User:
    """
    Get the current user AND verify they are on the allowlist.

    This dependency should be used on all protected endpoints that require
    allowlist verification (which is most endpoints after onboarding).

    Parameters
    ----------
    current_user : User
        The authenticated user from get_current_user dependency.

    Returns
    -------
    User
        The authenticated and allowlisted user.

    Raises
    ------
    HTTPException
        403 if user is not on the allowlist.
    """
    settings = get_settings()

    # Check for local development bypass
    if (settings.ENVIRONMENT == "local" and
        settings.BYPASS_ALLOWLIST_DEV and
        current_user.email == "developer@localhost.com"):
        logger.info("Allowlist bypassed for local dev user: %s", current_user.email)
        return current_user

    # Check allowlist with fail-open approach
    try:
        allowlist_config = settings.get_allowlist_config()
        allowlist_cache = get_allowlist_cache(settings.ALLOWLIST_CACHE_TTL_SECONDS)
        is_allowlisted = await allowlist_cache.is_user_allowlisted(
            current_user.email,
            settings.AZURE_STORAGE_CONNECTION_STRING,
            allowlist_config["container"],
            allowlist_config["blob_name"]
        )

        if not is_allowlisted:
            logger.warning("Access denied: User %s is not on the allowlist", current_user.email)
            raise HTTPException(
                status_code=403,
                detail="Access denied. Your account is not authorized to use this service. Please contact your administrator."
            )

        logger.info("Allowlist verified for user: %s", current_user.email)
        return current_user  # noqa: TRY300

    except HTTPException:
        # Re-raise HTTPException (user not allowlisted) - don't fail open for this
        raise
    except Exception as e:
        # FAIL OPEN: Allowlist check failed (service unavailable, parse error, etc.)
        # Log extensively and allow access
        logger.exception(
            "⚠️ ALLOWLIST CHECK FAILED - FAILING OPEN ⚠️ | User: %s",
            current_user.email
        )
        sentry_sdk.capture_exception(
            e,
            extras={
                "user_email": current_user.email,
                "fail_open": True,
                "message": "Allowlist check failed - allowing access (fail-open mode)"
            }
        )
        logger.warning("Allowing access for user %s due to allowlist service failure (fail-open)", current_user.email)
        return current_user
