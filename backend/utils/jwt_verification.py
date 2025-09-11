import logging
from typing import Any

import jwt
from fastapi import HTTPException
from jwt import PyJWKClient

from utils.settings import get_settings

logger = logging.getLogger(__name__)

class JWTVerificationService:
    def __init__(self):
        settings = get_settings()
        self.tenant_id = settings.AZURE_AD_TENANT_ID
        self.client_id = settings.AZURE_AD_CLIENT_ID
        self.jwks_client = None
        self.enabled = settings.JWT_ENABLE_VERIFICATION  # Now defaults to True
        self.strict_mode = settings.JWT_VERIFICATION_STRICT  # Now defaults to True

        if self.enabled and self.tenant_id:
            # Azure AD v2.0 JWKS endpoint
            jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            # Fixed: Remove cache_jwks parameter and use correct parameter names
            self.jwks_client = PyJWKClient(
                jwks_url,
                cache_keys=True,  # Changed from cache_jwks to cache_keys
                max_cached_keys=16
            )
            logger.info("🔐 JWT verification service initialized - Strict mode: %s", self.strict_mode)

    async def verify_jwt_token(self, token: str) -> dict[str, Any] | None:  # noqa: C901, PLR0911, PLR0912
        """
        Verify JWT token signature and claims
        Returns decoded token payload if valid, None if verification disabled
        Raises HTTPException if verification enabled but token invalid
        """
        if not self.enabled:
            logger.info("JWT verification disabled")
            return None

        if not token:
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT token required for verification")
            return None

        try:
            # Get signing key from Azure AD
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Verify token signature and claims
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,  # Must match our application ID
                issuer=f"https://login.microsoftonline.com/{self.tenant_id}/v2.0",
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                }
            )

        except jwt.ExpiredSignatureError as e:
            logger.warning("JWT token has expired")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT token has expired") from e
            return None

        except jwt.InvalidAudienceError as e:
            logger.warning("JWT token audience mismatch")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT token audience invalid") from e
            return None

        except jwt.InvalidIssuerError as e:
            logger.warning("JWT token issuer invalid")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT token issuer invalid") from e
            return None

        except jwt.InvalidTokenError as e:
            logger.warning("JWT token verification failed: %s", e)
            if self.strict_mode:
                raise HTTPException(status_code=401, detail=f"JWT token invalid: {e!s}") from e
            return None

        except Exception as e:
            logger.exception("Unexpected error during JWT verification")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT verification failed") from e
            return None
        else:
            logger.info("✅ JWT verification successful for user: %s", decoded_token.get("email", "unknown"))
            return decoded_token

    def extract_user_info_from_jwt(self, decoded_token: dict[str, Any]) -> dict[str, str]:
        """Extract user information from verified JWT token"""
        return {
            "email": decoded_token.get("email") or decoded_token.get("preferred_username", ""),
            "name": decoded_token.get("name", ""),
            "azure_user_id": decoded_token.get("oid", ""),  # Object ID from Azure AD
            "upn": decoded_token.get("upn", ""),
        }

# Singleton instance
jwt_verification_service = JWTVerificationService()
