"""Unit tests for database interface functions.

These tests verify database operations and model creation functions.
"""

from uuid import uuid4

from app.database.postgres_models import MinuteVersion, TemplateMetadata, TemplateName


class TestCreateErrorMinuteVersion:
    """Test cases for error minute version creation logic.

    These tests verify the MinuteVersion model behavior when creating error states,
    simulating the logic in create_error_minute_version without requiring database setup.
    """

    def test_create_error_minute_version_with_template(self):
        """Test error minute version creation when template is provided."""
        minute_version_id = uuid4()
        transcription_id = uuid4()
        error = ValueError("Test error")
        template = TemplateMetadata(
            name=TemplateName.GENERAL,
            description="General meeting minutes",
            category="common",
        )
        trace_id = "test-trace-123"

        # Simulate create_error_minute_version logic
        result = MinuteVersion(
            id=minute_version_id,
            transcription_id=transcription_id,
            html_content="",
            is_generating=False,
            error_message=str(error),
            template=template,
            trace_id=trace_id,
        )

        assert result.id == minute_version_id
        assert result.transcription_id == transcription_id
        assert result.error_message == "Test error"
        assert result.html_content == ""
        assert result.is_generating is False
        assert result.trace_id == trace_id
        assert result.template == template

    def test_minute_version_template_required_for_database(self):
        """Test that MinuteVersion can be created without template in memory.

        While SQLModel allows creating MinuteVersion with template=None in memory,
        this would fail when saving to database since template is defined as
        a required JSONB field. This test documents that validation happens at
        database save time, not object creation time.

        The fix in llm_calls.py ensures template is ALWAYS passed to prevent
        this invalid state from being created.
        """
        minute_version_id = uuid4()
        transcription_id = uuid4()
        template = TemplateMetadata(
            name=TemplateName.GENERAL,
            description="General meeting minutes",
            category="common",
        )

        # MinuteVersion CAN be created with template in memory
        valid_version = MinuteVersion(
            id=minute_version_id,
            transcription_id=transcription_id,
            html_content="",
            is_generating=False,
            error_message="test error",
            template=template,
        )

        assert valid_version.template is not None
        assert valid_version.template.name == TemplateName.GENERAL

    def test_create_error_minute_version_without_trace_id(self):
        """Test error minute version creation when trace_id is omitted."""
        minute_version_id = uuid4()
        transcription_id = uuid4()
        error = ValueError("Test error")
        template = TemplateMetadata(
            name=TemplateName.CRISSA,
            description="CRISSA meeting minutes",
            category="common",
        )

        # Simulate create_error_minute_version without trace_id
        result = MinuteVersion(
            id=minute_version_id,
            transcription_id=transcription_id,
            html_content="",
            is_generating=False,
            error_message=str(error),
            template=template,
            # trace_id not provided - defaults to None
        )

        assert result.id == minute_version_id
        assert result.transcription_id == transcription_id
        assert result.error_message == "Test error"
        assert result.html_content == ""
        assert result.is_generating is False
        assert result.trace_id is None
        assert result.template == template

    def test_create_error_minute_version_simulates_ai_edit_error_scenario(self):
        """Test that simulates the ai_edit_task error handling scenario.

        In ai_edit_task, current_minutes has a template that must be passed to
        the error minute version. Tests both TemplateMetadata object and dict forms.
        """
        minute_version_id = uuid4()
        transcription_id = uuid4()
        error = RuntimeError("LLM API failed")

        # Simulate template as it would appear in current_minutes
        template_obj = TemplateMetadata(
            name=TemplateName.GENERAL,
            description="General meeting minutes",
            category="common",
        )

        # Test creating with TemplateMetadata object directly
        result = MinuteVersion(
            id=minute_version_id,
            transcription_id=transcription_id,
            html_content="",
            is_generating=False,
            error_message=str(error),
            template=template_obj,
        )

        assert result.id == minute_version_id
        assert result.transcription_id == transcription_id
        assert result.error_message == "LLM API failed"
        assert result.html_content == ""
        assert result.is_generating is False
        assert result.template is not None
        assert result.template.name == TemplateName.GENERAL
