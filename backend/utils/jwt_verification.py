import json
import time
from typing import Dict, Optional, Any
import httpx
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException
from utils.settings import settings_instance
import logging

logger = logging.getLogger(__name__)

class JWTVerificationService:
    def __init__(self):
        self.tenant_id = settings_instance.AZURE_AD_TENANT_ID
        self.client_id = settings_instance.AZURE_AD_CLIENT_ID
        self.jwks_client = None
        self.enabled = settings_instance.ENABLE_JWT_VERIFICATION  # Now defaults to True
        self.strict_mode = settings_instance.JWT_VERIFICATION_STRICT  # Now defaults to True
        
        if self.enabled and self.tenant_id:
            # Azure AD v2.0 JWKS endpoint
            jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            # Fixed: Remove cache_jwks parameter and use correct parameter names
            self.jwks_client = PyJWKClient(
                jwks_url,
                cache_keys=True,  # Changed from cache_jwks to cache_keys
                max_cached_keys=16
            )
            logger.info(f"🔐 JWT verification service initialized - Strict mode: {self.strict_mode}")

    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
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
            
            logger.info(f"✅ JWT verification successful for user: {decoded_token.get('email', 'unknown')}")
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT token has expired")
            return None
            
        except jwt.InvalidAudienceError:
            logger.warning("JWT token audience mismatch")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT token audience invalid")
            return None
            
        except jwt.InvalidIssuerError:
            logger.warning("JWT token issuer invalid")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT token issuer invalid")
            return None
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT token verification failed: {e}")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail=f"JWT token invalid: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error during JWT verification: {e}")
            if self.strict_mode:
                raise HTTPException(status_code=401, detail="JWT verification failed")
            return None

    def extract_user_info_from_jwt(self, decoded_token: Dict[str, Any]) -> Dict[str, str]:
        """Extract user information from verified JWT token"""
        return {
            "email": decoded_token.get("email") or decoded_token.get("preferred_username", ""),
            "name": decoded_token.get("name", ""),
            "azure_user_id": decoded_token.get("oid", ""),  # Object ID from Azure AD
            "upn": decoded_token.get("upn", ""),
        }

# Singleton instance
jwt_verification_service = JWTVerificationService()