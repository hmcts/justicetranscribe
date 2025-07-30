import logging
from typing import Annotated

import jwt
from fastapi import Header, HTTPException
from sqlmodel import Session, select

from shared_utils.auth import parse_auth_token
from shared_utils.database.postgres_database import engine
from shared_utils.database.postgres_models import User
from shared_utils.settings import settings_instance

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_session():
    with Session(engine) as session:
        yield session


async def get_current_user(
    x_amzn_oidc_accesstoken: Annotated[str | None, Header()] = None,
) -> User | None:
    """
    Called on every endpoint to decode JWT passed in every request.
    Gets or creates the user based on the email in the JWT
    Args:
        x_amzn_oidc_accesstoken: The incoming JWT from the auth provider, passed via the frontend app
    Returns:
        User: The user matching the username in the token
    """
    authorization: str | None = x_amzn_oidc_accesstoken

    if settings_instance.ENVIRONMENT in ["local", "integration-test"]:
        # A JWT for local testing, an example JWT from cognito, for user test@test.com
        jwt_dict = {
            "sub": "90429234-4031-7077-b9ba-60d1af121245",
            "aud": "account",
            "email_verified": "true",
            "preferred_username": "test@test.co.uk",
            "email": "test@test.co.uk",
            "username": "test@test.co.uk",
            "exp": 1727262399,
            "iss": "https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_example",
            "realm_access": {"roles": ["justice-transcribe"]},
        }
        jwt_headers = {
            "typ": "JWT",
            "kid": "1234947a-59d3-467c-880c-f005c6941ffg",
            "alg": "HS256",
            "iss": "https://auth.dev.i.ai.gov.uk/realms/i_ai",
            "exp": 1727262399,
        }
        authorization = jwt.encode(
            jwt_dict, "secret", algorithm="HS256", headers=jwt_headers
        )

    if not authorization:
        logger.info("No authorization header provided")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        email, _ = parse_auth_token(authorization)

        with Session(engine) as session:
            # Try to find existing user
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()

            if not user:
                # Create new user if doesn't exist
                user = User(email=email)
                session.add(user)
                session.commit()
                session.refresh(user)

            return user

    except Exception:
        logger.exception("Failed to decode token")
        raise HTTPException(  # noqa: B904
            status_code=401,
            detail="Failed to decode token",
            headers={"WWW-Authenticate": "Bearer"},
        )
