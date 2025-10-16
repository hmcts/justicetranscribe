"""Tests for authentication dependency functions."""

import base64
import json
from typing import Any

import pytest
from fastapi import HTTPException

from app.database.postgres_models import User


@pytest.fixture(scope="module", autouse=True)
def mock_settings():
    """Mock settings at module level to prevent import-time side effects."""
    from unittest.mock import MagicMock, patch

    mock_settings_obj = MagicMock()
    mock_settings_obj.DATABASE_CONNECTION_STRING = "postgresql://test:test@localhost/test"
    mock_settings_obj.ENVIRONMENT = "test"

    with (
        patch("utils.settings.get_settings", return_value=mock_settings_obj),
        patch("app.database.postgres_database.get_settings", return_value=mock_settings_obj),
    ):
        yield mock_settings_obj


@pytest.fixture
def mock_db_session(mocker):
    """Mock database session using pytest-mock."""
    mock_session = mocker.MagicMock()
    mock_result = mocker.MagicMock()
    mock_session.exec.return_value = mock_result
    mock_session.add = mocker.MagicMock()
    mock_session.commit = mocker.MagicMock()
    mock_session.refresh = mocker.MagicMock()
    return mock_session


@pytest.fixture
def mock_jwt_service(mocker):
    """Mock JWT verification service using pytest-mock."""
    mock_service = mocker.MagicMock()
    mock_service.verify_jwt_token = mocker.AsyncMock()
    mock_service.strict_mode = True
    return mock_service


@pytest.fixture
def mock_logger(mocker):
    """Mock logger to capture log calls without side effects."""
    return mocker.patch("utils.dependencies.logger")


@pytest.fixture
def mock_is_local_dev(mocker):
    """Mock is_local_development to always return False (production mode)."""
    return mocker.patch("utils.dependencies.is_local_development", return_value=False)


class TestGetCurrentUserOIDValidation:
    """Test cases for OID-based authentication validation in get_current_user."""

    def create_easy_auth_header(self, user_id: str, email: str, claims: list[dict] | None = None) -> str:
        """Helper to create Easy Auth x-ms-client-principal header.

        Parameters
        ----------
        user_id : str
            The Azure AD user ID (oid)
        email : str
            The user's email address
        claims : list[dict] | None
            Optional custom claims. If None, standard email claim is created.

        Returns
        -------
        str
            Base64-encoded Easy Auth header value
        """
        if claims is None:
            claims = [{"typ": "email", "val": email}]

        user_info = {
            "userId": user_id,
            "claims": claims
        }
        json_str = json.dumps(user_info)
        return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    def create_jwt_payload(self, oid: str, email: str, **kwargs: Any) -> dict[str, Any]:
        """Helper to create JWT token payload.

        Parameters
        ----------
        oid : str
            The Azure AD object ID
        email : str
            The user's email address
        **kwargs
            Additional claims to include

        Returns
        -------
        dict[str, Any]
            JWT payload dictionary
        """
        payload = {
            "oid": oid,
            "email": email,
            **kwargs
        }
        return payload

    @pytest.mark.asyncio
    async def test_oid_match_with_different_emails_succeeds(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that matching OIDs with different emails allows authentication."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        old_email = "user.old@example.com"
        new_email = "user.new@example.com"

        easy_auth_header = self.create_easy_auth_header(oid, new_email)
        jwt_payload = self.create_jwt_payload(oid, old_email)

        mock_user = User(id="test-id", email=new_email, azure_user_id=oid)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = True
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        result = await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        assert result == mock_user, "Should return user when OIDs match despite email difference"
        assert mock_jwt_service.verify_jwt_token.call_count == 1, "JWT verification should be called once"
        assert mock_is_local_dev.call_count >= 1, "Should check if local development mode"

    @pytest.mark.asyncio
    async def test_oid_mismatch_fails_in_strict_mode(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that mismatched OIDs block authentication in strict mode."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        easy_auth_oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        jwt_oid = "different-oid-1234-5678-9abc-def012345678"
        email = "user@example.com"

        easy_auth_header = self.create_easy_auth_header(easy_auth_oid, email)
        jwt_payload = self.create_jwt_payload(jwt_oid, email)

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = True
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                session=mock_db_session,
                x_ms_client_principal=easy_auth_header,
                authorization="Bearer test-token"
            )

        assert exc_info.value.status_code == 401, "Should return 401 status code"
        assert "oid claim mismatch" in exc_info.value.detail, f"Error message should mention oid claim mismatch, got: {exc_info.value.detail}"
        assert easy_auth_oid in exc_info.value.detail, f"Error should include Easy Auth OID, got: {exc_info.value.detail}"
        assert jwt_oid in exc_info.value.detail, f"Error should include JWT OID, got: {exc_info.value.detail}"

    @pytest.mark.asyncio
    async def test_oid_mismatch_logs_warning_in_non_strict_mode(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that mismatched OIDs log warning but allow authentication in non-strict mode."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        easy_auth_oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        jwt_oid = "different-oid-1234-5678-9abc-def012345678"
        email = "user@example.com"

        easy_auth_header = self.create_easy_auth_header(easy_auth_oid, email)
        jwt_payload = self.create_jwt_payload(jwt_oid, email)

        mock_user = User(id="test-id", email=email, azure_user_id=easy_auth_oid)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = False
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        result = await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        assert result == mock_user, "Should return user in non-strict mode despite OID mismatch"
        assert mock_logger.error.call_count == 1, "Should log error once for OID mismatch"
        error_call_args = mock_logger.error.call_args[0]
        assert "User ID mismatch" in error_call_args[0], "Error log should mention user ID mismatch"

    @pytest.mark.asyncio
    async def test_case_insensitive_oid_comparison(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that OID comparison is case-insensitive."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        oid_lower = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        oid_upper = "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
        oid_mixed = "a1B2c3D4-E5f6-7890-ABCD-ef1234567890"
        email = "user@example.com"

        easy_auth_header = self.create_easy_auth_header(oid_lower, email)
        jwt_payload = self.create_jwt_payload(oid_upper, email)

        mock_user = User(id="test-id", email=email, azure_user_id=oid_mixed)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = True
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        result = await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        assert result == mock_user, "Should match OIDs regardless of case"

    @pytest.mark.asyncio
    async def test_email_mismatch_logs_info_not_warning(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that email mismatches are logged at INFO level, not WARNING."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        old_email = "user.old@example.com"
        new_email = "user.new@example.com"

        easy_auth_header = self.create_easy_auth_header(oid, new_email)
        jwt_payload = self.create_jwt_payload(oid, old_email)

        mock_user = User(id="test-id", email=new_email, azure_user_id=oid)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = False
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        # Should log INFO for email difference
        info_calls = list(mock_logger.info.call_args_list)
        email_diff_logged = any(
            "Email differs" in str(call) or old_email in str(call)
            for call in info_calls
        )
        assert email_diff_logged, "Should log INFO message about email difference"

        # Should NOT log WARNING for email difference
        if mock_logger.warning.called:
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            assert not any("Email" in call for call in warning_calls), "Should not log WARNING for email mismatch"

    @pytest.mark.asyncio
    async def test_missing_jwt_oid_doesnt_cause_error(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that missing JWT OID doesn't cause authentication failure."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        email = "user@example.com"

        easy_auth_header = self.create_easy_auth_header(oid, email)
        jwt_payload = {"email": email}  # No oid claim

        mock_user = User(id="test-id", email=email, azure_user_id=oid)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = False
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        result = await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        assert result == mock_user, "Should succeed when JWT OID is missing (not validating OID)"

    @pytest.mark.asyncio
    async def test_missing_easy_auth_oid_doesnt_cause_error(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that missing Easy Auth OID doesn't cause authentication failure."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        email = "user@example.com"
        jwt_oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

        # Create Easy Auth header without userId
        user_info = {
            "claims": [{"typ": "email", "val": email}]
            # No userId field
        }
        json_str = json.dumps(user_info)
        easy_auth_header = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        jwt_payload = self.create_jwt_payload(jwt_oid, email)

        # User will be looked up by email since no OID
        mock_user = User(id="test-id", email=email, azure_user_id=email)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = False
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        result = await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        assert result == mock_user, "Should succeed when Easy Auth OID is missing"

    @pytest.mark.asyncio
    async def test_same_email_and_oid_no_logging(self, mocker, mock_db_session, mock_jwt_service, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that matching email and OID don't trigger unnecessary logging."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        email = "user@example.com"

        easy_auth_header = self.create_easy_auth_header(oid, email)
        jwt_payload = self.create_jwt_payload(oid, email)

        mock_user = User(id="test-id", email=email, azure_user_id=oid)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service.verify_jwt_token.return_value = jwt_payload
        mock_jwt_service.strict_mode = True
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        result = await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        assert result == mock_user, "Should return user successfully"

        # Should not log error for OID mismatch (they match)
        assert mock_logger.error.call_count == 0, "Should not log error when OIDs match"

        # Check info logs don't mention email differences
        if mock_logger.info.called:
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert not any("Email differs" in call for call in info_calls), "Should not log email difference when emails match"

    @pytest.mark.asyncio
    async def test_no_jwt_token_in_strict_mode_fails(self, mocker, mock_db_session, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that missing JWT token in strict mode blocks authentication."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        oid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        email = "user@example.com"

        easy_auth_header = self.create_easy_auth_header(oid, email)

        # Configure JWT service mock to be in strict mode
        mock_jwt_service = mocker.MagicMock()
        mock_jwt_service.strict_mode = True
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                session=mock_db_session,
                x_ms_client_principal=easy_auth_header,
                authorization=None  # No JWT token
            )

        assert exc_info.value.status_code == 401, "Should return 401 status code"
        assert "JWT token required" in exc_info.value.detail, f"Error should mention JWT token required, got: {exc_info.value.detail}"

    @pytest.mark.asyncio
    async def test_fallback_to_email_as_user_identifier(self, mocker, mock_db_session, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that system falls back to email when no user IDs are available."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange
        email = "user@example.com"

        # Create Easy Auth header without userId
        user_info = {
            "claims": [{"typ": "email", "val": email}]
            # No userId field
        }
        json_str = json.dumps(user_info)
        easy_auth_header = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        # JWT payload without oid
        jwt_payload = {"email": email}  # No oid claim

        # User will be looked up by email since no OID
        mock_user = User(id="test-id", email=email, azure_user_id=email)
        mock_db_session.exec.return_value.first.return_value = mock_user

        # Configure JWT service mock
        mock_jwt_service = mocker.MagicMock()
        mock_jwt_service.verify_jwt_token = mocker.AsyncMock(return_value=jwt_payload)
        mock_jwt_service.strict_mode = False
        mocker.patch("utils.dependencies.jwt_verification_service", mock_jwt_service)

        # Act
        result = await get_current_user(
            session=mock_db_session,
            x_ms_client_principal=easy_auth_header,
            authorization="Bearer test-token"
        )

        # Assert
        assert result == mock_user, "Should return user when falling back to email"
        # Check that fallback logging occurred
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Falling back to email" in call for call in info_calls), "Should log fallback to email as identifier"

    @pytest.mark.asyncio
    async def test_invalid_json_in_easy_auth_header_fails(self, mocker, mock_db_session, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that invalid JSON in Easy Auth header raises appropriate error."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange - Create invalid JSON in Easy Auth header
        invalid_json = "not valid json"
        easy_auth_header = base64.b64encode(invalid_json.encode("utf-8")).decode("utf-8")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                session=mock_db_session,
                x_ms_client_principal=easy_auth_header,
                authorization="Bearer test-token"
            )

        assert exc_info.value.status_code == 401, "Should return 401 status code"
        assert "Invalid authentication information" in exc_info.value.detail, f"Error should mention invalid authentication, got: {exc_info.value.detail}"

    @pytest.mark.asyncio
    async def test_invalid_base64_in_easy_auth_header_fails(self, mocker, mock_db_session, mock_logger, mock_is_local_dev):  # noqa: ARG002
        """Test that invalid base64 in Easy Auth header raises appropriate error."""
        # Lazy import to avoid side effects
        from utils.dependencies import get_current_user

        # Arrange - Invalid base64 string
        easy_auth_header = "not-valid-base64!!!"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                session=mock_db_session,
                x_ms_client_principal=easy_auth_header,
                authorization="Bearer test-token"
            )

        assert exc_info.value.status_code == 401, "Should return 401 status code"
        assert "Invalid authentication information" in exc_info.value.detail, f"Error should mention invalid authentication, got: {exc_info.value.detail}"

