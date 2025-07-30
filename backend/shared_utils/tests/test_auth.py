import os
from datetime import datetime

import jwt
import pytest
import pytz
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from shared_utils.auth import is_authorised_user, parse_auth_token


def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    pem_public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_key, pem_public_key

valid_private_key, valid_public_key = generate_rsa_keys()

expected_role = "test-role1"

def jwt_payload(expiry_time = None):
    now = round(datetime.now(pytz.utc).timestamp())
    now_plus_one_hour = str(now + 3600)

    if not expiry_time:
        expiry_time = now_plus_one_hour

    payload = {"exp": str(expiry_time), "iat": str(now - 10), "auth_time": str(now - 10), "jti": "879ff44f-5c24-4a3c-a4d1-b967733821e4", "iss": "https://test-data.ai.cabinetoffice.gov.uk/realms/i_ai", "aud": "account", "sub": "5668bedb-4b98-4952-b645-bc8019b94c3b", "typ": "Bearer", "azp": "test-app", "sid": "7cf70320-beb6-4591-98ad-f4c87a16da43", "acr": "0", "realm_access": { "roles": [ "test-role1" ] }, "scope": "openid profile email", "email_verified": "true", "preferred_username": "test@example.com", "email": "test@example.com" }
    return payload

def encode_jwt(jwt_payload, private_key):
    return jwt.encode(jwt_payload, private_key, algorithm="RS256")

def test_parse_auth_token_returns_email_and_roles_tuple():
    os.environ["DISABLE_AUTH_SIGNATURE_VERIFICATION"] = "True"
    os.environ["REPO"] = expected_role
    test_jwt = encode_jwt(jwt_payload(), valid_private_key)

    email, roles = parse_auth_token(test_jwt)
    assert email == "test@example.com"
    assert os.environ.get("REPO") in roles

def test_parse_auth_token_with_signature_validation_validates_successfully():
    if os.environ.get("DISABLE_AUTH_SIGNATURE_VERIFICATION"):
        del os.environ["DISABLE_AUTH_SIGNATURE_VERIFICATION"]
    os.environ["REPO"] = expected_role

    pem_public_key_str = valid_public_key.decode("utf-8")
    stripped_key = pem_public_key_str.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").strip()

    os.environ["AUTH_PROVIDER_PUBLIC_KEY"] = stripped_key

    test_jwt = encode_jwt(jwt_payload(), valid_private_key)

    email, roles = parse_auth_token(test_jwt)
    assert email == "test@example.com"
    assert os.environ.get("REPO") in roles

def test_parse_auth_token_with_invalid_signature_throws_during_validation():
    if os.environ.get("DISABLE_AUTH_SIGNATURE_VERIFICATION"):
        del os.environ["DISABLE_AUTH_SIGNATURE_VERIFICATION"]
    os.environ["REPO"] = expected_role

    alternate_private_key, _ = generate_rsa_keys()

    pem_public_key_str = valid_public_key.decode("utf-8")
    stripped_key = pem_public_key_str.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").strip()

    os.environ["AUTH_PROVIDER_PUBLIC_KEY"] = stripped_key

    test_jwt = encode_jwt(jwt_payload(), alternate_private_key) # Mis-sign the request

    with pytest.raises(jwt.InvalidTokenError, match="Invalid authentication token: Signature verification failed"):
       parse_auth_token(test_jwt)

def test_parse_auth_token_throws_expired_exception_if_expired_token():
    if os.environ.get("DISABLE_AUTH_SIGNATURE_VERIFICATION"):
        del os.environ["DISABLE_AUTH_SIGNATURE_VERIFICATION"]
    os.environ["REPO"] = expected_role

    expired = round(datetime.now(pytz.utc).timestamp()) - 3600

    test_jwt = encode_jwt(jwt_payload(expired), valid_private_key)

    with pytest.raises(jwt.ExpiredSignatureError):
       parse_auth_token(test_jwt)

def test_is_authorised_user_returns_true_if_roles_valid():
    os.environ["DISABLE_AUTH_SIGNATURE_VERIFICATION"] = "True"
    os.environ["REPO"] = expected_role
    test_jwt = encode_jwt(jwt_payload(), valid_private_key)

    assert is_authorised_user(test_jwt)

def test_is_authorised_user_returns_false_if_roles_invalid():
    os.environ["DISABLE_AUTH_SIGNATURE_VERIFICATION"] = "True"
    os.environ["REPO"] = "unexpected-role"
    test_jwt = encode_jwt(jwt_payload(), valid_private_key)

    assert not is_authorised_user(test_jwt)
