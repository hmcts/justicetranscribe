import asyncio
import uuid
from uuid import UUID

import pytz
import sentry_sdk
from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import JSONResponse

from app.audio.utils import (
    generate_blob_upload_url,
    get_file_blob_path,
    validate_current_azure_storage_config,
)
from app.database.interface_functions import (
    delete_transcription_by_id,
    fetch_transcriptions_metadata,
    get_minute_version_by_id,
    get_minute_versions,
    get_transcription_by_id,
    get_transcription_jobs,
    get_user_by_id,
    mark_user_onboarding_complete,
    save_minute_version,
    save_transcription,
    save_transcription_job,
    update_user,
)
from app.database.postgres_models import (
    MinuteVersion,
    Transcription,
    TranscriptionJob,
    User,
)
from app.llm.llm_client import (
    langfuse_client,
)
from app.logger import logger
from app.minutes.llm_calls import ai_edit_task, generate_llm_output_task
from app.minutes.templates.templates_metadata import (
    get_all_templates,
)
from app.minutes.types import (
    GenerateMinutesRequest,
    OnboardingStatusResponse,
    TemplateResponse,
    TranscriptionMetadata,
    UpdateUserRequest,
    UploadUrlRequest,
    UploadUrlResponse,
)
from utils.allowlist import get_allowlist_manager
from utils.dependencies import get_allowlisted_user, get_current_user
from utils.langfuse_models import (
    LangfuseScoreRequest,
    LangfuseTraceRequest,
)
from utils.settings import get_settings

router = APIRouter()


# Azure Blob Storage configuration is handled through get_settings()


UK_TIMEZONE = pytz.timezone("Europe/London")


@router.get("/health")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})


@router.get("/healthcheck")
async def health_check_legacy():
    """Legacy endpoint for backwards compatibility"""
    return JSONResponse(status_code=200, content={"status": "ok"})


@router.get("/user/onboarding-status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> OnboardingStatusResponse:
    """
    Get user's onboarding status and allowlist check.

    This endpoint provides comprehensive status information for the frontend
    to determine what UI to display to the user. It checks both onboarding
    completion status and allowlist membership.

    Parameters
    ----------
    current_user : User
        The authenticated user from the dependency injection.

    Returns
    -------
    OnboardingStatusResponse
        Complete status information including onboarding and allowlist status.

    Raises
    ------
    HTTPException
        If user authentication fails or allowlist check fails.
    """
    # Check if onboarding should be forced in development
    settings = get_settings()
    force_onboarding = settings.FORCE_ONBOARDING_DEV and settings.ENVIRONMENT in [
        "local",
        "dev",
    ]

    # Check allowlist status with fail-open approach
    # Check for local development bypass first
    if (
        settings.ENVIRONMENT == "local"
        and settings.BYPASS_ALLOWLIST_DEV
        and current_user.email == "developer@localhost.com"
    ):
        logger.info(
            "🔓 ALLOWLIST BYPASS (ENV VAR) | User: %s | BYPASS_ALLOWLIST_DEV=%s",
            current_user.email,
            settings.BYPASS_ALLOWLIST_DEV,
        )
        is_allowlisted = True
    else:
        try:
            logger.debug("🔍 Checking allowlist for user: %s", current_user.email)
            allowlist_manager = get_allowlist_manager()
            is_allowlisted = allowlist_manager.is_user_allowlisted(current_user.email)

            if is_allowlisted:
                logger.info("✅ ALLOWLIST CHECK PASSED | User: %s", current_user.email)
            else:
                logger.warning("❌ ALLOWLIST CHECK FAILED | User: %s | Not in allowlist", current_user.email)
        except Exception as e:
            # FAIL OPEN: Allowlist check failed - log and allow access
            logger.exception(
                "⚠️ ALLOWLIST CHECK FAILED IN ONBOARDING STATUS - FAILING OPEN ⚠️ | User: %s",
                current_user.email,
            )
            sentry_sdk.capture_exception(
                e,
                extras={
                    "user_email": current_user.email,
                    "endpoint": "/user/onboarding-status",
                    "fail_open": True,
                    "message": "Allowlist check failed in onboarding-status - allowing access (fail-open mode)",
                },
            )
            logger.warning(
                "🔓 ALLOWLIST BYPASS (FAIL-OPEN) | User: %s | Allowing access due to system error",
                current_user.email,
            )
            is_allowlisted = True  # Fail open: allow access

    return OnboardingStatusResponse(
        has_completed_onboarding=current_user.has_completed_onboarding,
        force_onboarding_override=force_onboarding,
        should_show_onboarding=(not current_user.has_completed_onboarding) or force_onboarding,
        user_id=current_user.id,
        environment=settings.ENVIRONMENT,
        is_allowlisted=is_allowlisted,
        should_show_coming_soon=not is_allowlisted,
    )


@router.post("/user/complete-onboarding")
async def complete_onboarding(
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Mark user's onboarding as complete"""

    # Don't update in dev override mode to preserve testing ability
    settings = get_settings()
    if not (settings.FORCE_ONBOARDING_DEV and settings.ENVIRONMENT in ["local", "dev"]):
        updated_user = mark_user_onboarding_complete(current_user.id)
        return {
            "success": True,
            "message": "Onboarding marked as complete",
            "has_completed_onboarding": updated_user.has_completed_onboarding,
        }
    else:
        return {
            "success": True,
            "message": "Onboarding completion skipped (dev override mode active)",
            "has_completed_onboarding": current_user.has_completed_onboarding,
        }


@router.post("/user/reset-onboarding")
async def reset_onboarding(
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Reset user's onboarding status (dev only)"""

    # Only allow in local/dev environments
    settings = get_settings()
    if settings.ENVIRONMENT not in ["local", "dev"]:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in local/dev environments",
        )

    # Reset onboarding status
    updated_user = update_user(current_user.id, has_completed_onboarding=False)

    return {
        "success": True,
        "message": "Onboarding status reset successfully",
        "has_completed_onboarding": updated_user.has_completed_onboarding,
        "user_id": str(updated_user.id),
        "email": updated_user.email,
    }


@router.get("/healthcheck/azure-storage")
async def azure_storage_health_check():
    """
    Health check endpoint to validate Azure Storage configuration and account key.
    This helps detect if the storage account key has been cycled and needs updating.
    """
    validation_result = validate_current_azure_storage_config()

    if validation_result["valid"]:
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "azure_storage": validation_result},
        )
    else:
        return JSONResponse(
            status_code=503,  # Service Unavailable
            content={"status": "error", "azure_storage": validation_result},
        )


@router.post("/get-upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
) -> UploadUrlResponse:
    file_name_uuid = uuid.uuid4()
    file_name = f"{file_name_uuid}.{request.file_extension}"
    user_upload_blob_path = get_file_blob_path(current_user.email, file_name)

    # Generate presigned URL for Azure Blob Storage upload
    presigned_url = generate_blob_upload_url(
        container_name=get_settings().AZURE_STORAGE_CONTAINER_NAME,
        blob_name=user_upload_blob_path,
        expiry_hours=24,
    )
    # throw error for testing:
    # raise HTTPException(status_code=500, detail="Test error")

    return UploadUrlResponse(
        upload_url=presigned_url,
        user_upload_s3_file_key=user_upload_blob_path,  # Keep same field name for compatibility
    )


def _validate_transcription_for_minutes(transcription_id: UUID, user_id: UUID) -> list:
    """
    Validate that a transcription has dialogue entries for minute generation.

    Parameters
    ----------
    transcription_id : UUID
        ID of the transcription to validate
    user_id : UUID
        ID of the user requesting access

    Returns
    -------
    list
        List of dialogue entries from all transcription jobs

    Raises
    ------
    HTTPException
        If transcription not found, no jobs exist, or no dialogue entries available
    """
    # Verify user has access to this transcription
    get_transcription_by_id(
        transcription_id,
        user_id,
        tz=pytz.UTC,
    )

    # Fetch transcription jobs
    transcription_jobs = get_transcription_jobs(transcription_id)

    if not transcription_jobs:
        raise HTTPException(
            status_code=404,
            detail="No transcription jobs found. Cannot generate minutes.",
        )

    # Extract all dialogue entries
    dialogue_entries = []
    for job in transcription_jobs:
        dialogue_entries.extend(job.dialogue_entries)

    # Validate dialogue entries exist (catches "500: No transcription phrases" case)
    if not dialogue_entries:
        logger.warning(
            f"No dialogue entries found for transcription {transcription_id}. "
            f"Found {len(transcription_jobs)} job(s) but no dialogue entries."
        )
        raise HTTPException(
            status_code=424,
            detail="No dialogue entries found. Transcription may have failed or contained no speech.",
        )

    return dialogue_entries


@router.post("/generate-or-edit-minutes")
async def generate_or_edit_minutes(
    request: GenerateMinutesRequest,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """
    Initiate minute generation or editing as an async background task.

    Validates transcription has dialogue entries before starting LLM processing.
    Returns immediately with a minute_version_id that can be polled for completion.

    Parameters
    ----------
    request : GenerateMinutesRequest
        Request containing transcription_id, template, and action type
    current_user : User
        Authenticated user from dependency injection

    Returns
    -------
    JSONResponse
        Contains minute_version_id and status="initiated"

    Raises
    ------
    HTTPException
        404 if transcription or jobs not found
        424 if no dialogue entries available (transcription failed)
        400 if edit_instructions missing for edit action
    """
    user_id = current_user.id
    user_email = current_user.email

    # Validate and get dialogue entries (raises HTTPException if invalid)
    dialogue_entries = _validate_transcription_for_minutes(request.transcription_id, user_id)

    # Validate edit_instructions BEFORE creating minute_version_id
    if request.action_type == "edit" and not request.edit_instructions:
        raise HTTPException(
            status_code=400,
            detail="edit_instructions are required for edit action",
        )

    # Only create ID after ALL validation passes
    new_minute_version_id = str(uuid.uuid4())

    async def process_request():
        if request.action_type == "generate":
            await generate_llm_output_task(
                dialogue_entries,
                request.transcription_id,
                request.template,
                user_email,
                minute_version_id=new_minute_version_id,
            )
        elif request.action_type == "edit":
            await ai_edit_task(
                dialogue_entries,
                request.current_minute_version_id,
                new_minute_version_id,
                request.edit_instructions,
                request.transcription_id,
                user_email,
            )

    asyncio.create_task(process_request())  # noqa: RUF006 - fire-and-forget background task
    return JSONResponse(content={"minute_version_id": new_minute_version_id, "status": "initiated"})


@router.get("/templates", response_model=TemplateResponse)
async def get_templates(
    current_user: User = Depends(get_current_user),  # noqa: B008, ARG001
):
    """Get all template categories (auth only, used during onboarding)."""
    templates = get_all_templates()
    return TemplateResponse(templates=templates)


@router.get("/transcriptions-metadata", response_model=list[TranscriptionMetadata])
async def get_transcriptions_metadata(
    current_user: User = Depends(get_current_user),  # noqa: B008
    timezone: str = "Europe/London",  # Optional parameter with UK default
):
    """Get metadata for all transcriptions (auth only, allowlist checked in frontend)."""
    logger.info("getting transcription metadata for user %s", current_user.id)

    # Get timezone (fallback to UK if invalid)
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        tz = UK_TIMEZONE

    return fetch_transcriptions_metadata(current_user.id, tz)


@router.get("/transcriptions/{transcription_id}", response_model=Transcription)
async def get_transcription(
    transcription_id: UUID,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
    timezone: str = "Europe/London",  # Optional parameter with UK default
):
    """Get a specific transcription by ID."""
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        tz = UK_TIMEZONE

    return get_transcription_by_id(transcription_id, current_user.id, tz)


@router.post("/transcriptions", response_model=Transcription)
async def save_transcription_route(
    transcription_data: Transcription,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Save or update a transcription."""
    logger.info("saving transcription for user %s", current_user.id)

    return save_transcription(transcription_data, current_user.id)


@router.delete("/transcriptions/{transcription_id}", status_code=204)
async def delete_transcription(
    transcription_id: UUID,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Delete a specific transcription by ID."""
    delete_transcription_by_id(transcription_id, current_user.id)


@router.get(
    "/transcriptions/{transcription_id}/minute-versions/{minute_version_id}",
    response_model=MinuteVersion,
)
async def get_minute_version_by_id_route(
    transcription_id: UUID,
    minute_version_id: UUID,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Get a specific minute version by its ID for a given transcription."""
    # Verify user has access to the associated transcription
    transcription = get_transcription_by_id(transcription_id, current_user.id, UK_TIMEZONE)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Get the specific minute version, ensuring it belongs to the transcription
    minute_version = get_minute_version_by_id(minute_version_id, transcription_id)
    return minute_version


@router.get(
    "/transcriptions/{transcription_id}/minute-versions",
    response_model=list[MinuteVersion],
)
async def get_minute_versions_route(
    transcription_id: UUID,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Get all minute versions for a specific transcription."""
    # Verify user has access to this transcription
    transcription = get_transcription_by_id(transcription_id, current_user.id, UK_TIMEZONE)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return get_minute_versions(transcription_id)


@router.post("/transcriptions/{transcription_id}/minute-versions", response_model=MinuteVersion)
async def save_minute_version_route(
    transcription_id: UUID,
    minute_data: MinuteVersion,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Create or update a minute version for a transcription."""
    transcription = get_transcription_by_id(transcription_id, current_user.id, UK_TIMEZONE)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    minute_data.transcription_id = transcription_id

    # Save the minute version first
    saved_minute = save_minute_version(minute_data)

    # Then handle the additional logging if needed
    old_html_content = get_minute_version_by_id(minute_data.id, transcription_id).html_content

    # Only log the event if content has changed
    if old_html_content != minute_data.html_content:
        langfuse_client.event(
            trace_id=minute_data.trace_id,
            name="user-edit",
            input=old_html_content,
            output=minute_data.html_content,
        )

    return saved_minute


@router.post("/transcriptions/{transcription_id}/jobs", response_model=TranscriptionJob)
async def save_transcription_job_route(
    transcription_id: UUID,
    job_data: TranscriptionJob,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
) -> TranscriptionJob:
    """Create a new transcription job for a transcription."""
    # Verify user has access to this transcription
    transcription = get_transcription_by_id(transcription_id, current_user.id, UK_TIMEZONE)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return save_transcription_job(
        job=job_data,
    )


@router.get("/transcriptions/{transcription_id}/jobs", response_model=list[TranscriptionJob])
async def get_transcription_jobs_route(
    transcription_id: UUID,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
) -> list[TranscriptionJob]:
    """Get all transcription jobs for a specific transcription."""
    # Verify user has access to this transcription
    transcription = get_transcription_by_id(transcription_id, current_user.id, UK_TIMEZONE)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return get_transcription_jobs(transcription_id)


@router.get("/user", response_model=User)
async def get_current_user_route(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get the current user's details (auth only, no allowlist check)."""
    return get_user_by_id(current_user.id)


# Add missing routes that frontend expects
@router.get("/users/me", response_model=User)
async def get_current_user_me_route(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get the current user's details (auth only, no allowlist check)."""
    return get_user_by_id(current_user.id)


@router.get("/user/profile", response_model=User)
async def get_user_profile_route(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get the current user's profile (auth only, no allowlist check)."""
    return get_user_by_id(current_user.id)


@router.post("/user", response_model=User)  # changed from .patch to .post
async def update_current_user_route(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Update the current user's details (auth only, used during onboarding)."""
    update_fields = request.model_dump(exclude_unset=True)
    return update_user(current_user.id, **update_fields)


@router.post("/langfuse/trace")
async def submit_langfuse_trace(
    request: LangfuseTraceRequest,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Submit a trace to Langfuse via backend proxy for security."""
    try:
        # Submit general trace/event
        langfuse_client.event(
            trace_id=request.trace_id,
            name=request.name,
            metadata=request.metadata or {},
            input=request.input_data,
            output=request.output_data,
            user_id=current_user.email,
        )

        logger.info(
            f"Langfuse trace '{request.name}' submitted for trace {request.trace_id} by user {current_user.email}"
        )

    except Exception as e:
        _e = f"Failed to submit Langfuse trace: {e!s}"
        logger.error(_e)
        raise HTTPException(status_code=500, detail=_e) from e
    else:
        return {"success": True, "message": "Trace submitted successfully"}


@router.post("/langfuse/score")
async def submit_langfuse_score(
    request: LangfuseScoreRequest,
    current_user: User = Depends(get_allowlisted_user),  # noqa: B008
):
    """Submit a score to Langfuse via backend proxy for security."""
    try:
        # Submit score using the backend Langfuse client
        langfuse_client.score(
            trace_id=request.trace_id,
            name=request.name,
            value=request.value,
            comment=request.comment,
            user_id=current_user.email,
        )

        logger.info(f"Langfuse score submitted for trace {request.trace_id} by user {current_user.email}")

    except Exception as e:
        _e = f"Failed to submit Langfuse score: {e!s}"
        logger.error(_e)
        raise HTTPException(status_code=500, detail=_e) from e
    else:
        return {"success": True, "message": "Score submitted successfully"}
