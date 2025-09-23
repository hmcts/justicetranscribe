import asyncio
import uuid
from uuid import UUID

import pytz
from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import JSONResponse

from app.audio.process_audio_fully import transcribe_and_generate_llm_output
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
    StartTranscriptionJobRequest,
    TemplateResponse,
    TranscriptionMetadata,
    UpdateUserRequest,
    UploadUrlRequest,
    UploadUrlResponse,
)
from utils.dependencies import get_current_user
from utils.langfuse_models import (
    LangfuseEventRequest,
    LangfuseScoreRequest,
    LangfuseTraceRequest,
)
from utils.settings import get_settings

router = APIRouter()


# Azure Blob Storage configuration is handled through get_settings()


UK_TIMEZONE = pytz.timezone("Europe/London")


@router.get("/healthcheck")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})


@router.get("/user/onboarding-status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get user's onboarding status and check for dev override"""

    # Check if onboarding should be forced in development
    settings = get_settings()
    force_onboarding = (
        settings.FORCE_ONBOARDING_DEV and
        settings.ENVIRONMENT in ["local", "dev"]
    )

    return {
        "has_completed_onboarding": current_user.has_completed_onboarding,
        "force_onboarding_override": force_onboarding,
        "should_show_onboarding": not current_user.has_completed_onboarding or force_onboarding,
        "user_id": str(current_user.id),
        "environment": settings.ENVIRONMENT,
    }


@router.post("/user/complete-onboarding")
async def complete_onboarding(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Mark user's onboarding as complete"""

    # Don't update in dev override mode to preserve testing ability
    settings = get_settings()
    if not (settings.FORCE_ONBOARDING_DEV and settings.ENVIRONMENT in ["local", "dev"]):
        updated_user = mark_user_onboarding_complete(current_user.id)
        return {
            "success": True,
            "message": "Onboarding marked as complete",
            "has_completed_onboarding": updated_user.has_completed_onboarding
        }
    else:
        return {
            "success": True,
            "message": "Onboarding completion skipped (dev override mode active)",
            "has_completed_onboarding": current_user.has_completed_onboarding
        }
@router.post("/user/reset-onboarding")
async def reset_onboarding(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Reset user's onboarding status (dev only)"""

    # Only allow in local/dev environments
    settings = get_settings()
    if settings.ENVIRONMENT not in ["local", "dev"]:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in local/dev environments"
        )

    # Reset onboarding status
    updated_user = update_user(current_user.id, has_completed_onboarding=False)

    return {
        "success": True,
        "message": "Onboarding status reset successfully",
        "has_completed_onboarding": updated_user.has_completed_onboarding,
        "user_id": str(updated_user.id),
        "email": updated_user.email
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
            content={
                "status": "ok",
                "azure_storage": validation_result
            }
        )
    else:
        return JSONResponse(
            status_code=503,  # Service Unavailable
            content={
                "status": "error",
                "azure_storage": validation_result
            }
        )


@router.post("/get-upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> UploadUrlResponse:
    file_name_uuid = uuid.uuid4()
    file_name = f"{file_name_uuid}.{request.file_extension}"
    user_upload_blob_path = get_file_blob_path(current_user.email, file_name)

    # Generate presigned URL for Azure Blob Storage upload
    presigned_url = generate_blob_upload_url(
        container_name=get_settings().AZURE_STORAGE_CONTAINER_NAME,
        blob_name=user_upload_blob_path,
        expiry_hours=1,
    )

    return UploadUrlResponse(
        upload_url=presigned_url,
        user_upload_s3_file_key=user_upload_blob_path,  # Keep same field name for compatibility
    )


async def process_transcription(
    user_upload_blob_storage_file_key: str, user: User, transcription_id: str | None = None
) -> None:
    """Parent function that handles the TranscriptionJob state management."""
    await transcribe_and_generate_llm_output(
        user_upload_blob_storage_file_key, user, transcription_id
    )


@router.post("/start-transcription-job", response_model=None)
async def start_transcription_job(
    request: StartTranscriptionJobRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> None:
    try:
        asyncio.create_task(  # noqa: RUF006
            process_transcription(
                request.user_upload_s3_file_key, current_user, request.transcription_id
            )
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/generate-or-edit-minutes")
async def generate_or_edit_minutes(
    request: GenerateMinutesRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    new_minute_version_id = str(uuid.uuid4())

    async def process_request():
        try:
            # First verify the user has access to this transcription
            get_transcription_by_id(
                request.transcription_id,
                current_user.id,
                tz=pytz.UTC,  # We don't need timezone conversion for this check
            )

            # Fetch transcription jobs for this transcription
            transcription_jobs = get_transcription_jobs(request.transcription_id)

            if not transcription_jobs:
                raise HTTPException(
                    status_code=404,
                    detail="No transcription jobs found for this transcription",
                )

            dialogue_entries = []
            for job in transcription_jobs:
                dialogue_entries.extend(job.dialogue_entries)

            if request.action_type == "generate":
                await generate_llm_output_task(
                    dialogue_entries,
                    request.transcription_id,
                    request.template,
                    current_user.email,
                    minute_version_id=new_minute_version_id,
                )
            elif request.action_type == "edit":
                if not request.edit_instructions:
                    raise HTTPException(
                        status_code=400,
                        detail="edit_instructions are required for edit action",
                    )

                await ai_edit_task(
                    dialogue_entries,
                    request.current_minute_version_id,
                    new_minute_version_id,
                    request.edit_instructions,
                    request.transcription_id,
                    current_user.email,
                )

        except HTTPException:
            # Re-raise HTTP exceptions (like 404s) as is
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    asyncio.create_task(process_request())  # noqa: RUF006
    return JSONResponse(
        content={"minute_version_id": new_minute_version_id, "status": "initiated"}
    )


@router.get("/templates", response_model=TemplateResponse)
async def get_templates():
    """Get all template categories and their templates."""
    templates = get_all_templates()
    return TemplateResponse(templates=templates)


@router.get("/transcriptions-metadata", response_model=list[TranscriptionMetadata])
async def get_transcriptions_metadata(
    current_user: User = Depends(get_current_user),  # noqa: B008
    timezone: str = "Europe/London",  # Optional parameter with UK default
):
    """Get metadata for all transcriptions for the current user."""
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
    current_user: User = Depends(get_current_user),  # noqa: B008
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
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Save or update a transcription."""
    logger.info("saving transcription for user %s", current_user.id)

    return save_transcription(transcription_data, current_user.id)


@router.delete("/transcriptions/{transcription_id}", status_code=204)
async def delete_transcription(
    transcription_id: UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
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
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get a specific minute version by its ID for a given transcription."""
    # Verify user has access to the associated transcription
    transcription = get_transcription_by_id(
        transcription_id, current_user.id, UK_TIMEZONE
    )
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
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get all minute versions for a specific transcription."""
    # Verify user has access to this transcription
    transcription = get_transcription_by_id(
        transcription_id, current_user.id, UK_TIMEZONE
    )
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return get_minute_versions(transcription_id)


@router.post(
    "/transcriptions/{transcription_id}/minute-versions", response_model=MinuteVersion
)
async def save_minute_version_route(
    transcription_id: UUID,
    minute_data: MinuteVersion,
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Create or update a minute version for a transcription."""
    transcription = get_transcription_by_id(
        transcription_id, current_user.id, UK_TIMEZONE
    )
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    minute_data.transcription_id = transcription_id

    # Save the minute version first
    saved_minute = save_minute_version(minute_data)

    # Then handle the additional logging if needed
    old_html_content = get_minute_version_by_id(
        minute_data.id, transcription_id
    ).html_content

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
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> TranscriptionJob:
    """Create a new transcription job for a transcription."""
    # Verify user has access to this transcription
    transcription = get_transcription_by_id(
        transcription_id, current_user.id, UK_TIMEZONE
    )
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return save_transcription_job(
        job=job_data,
    )


@router.get(
    "/transcriptions/{transcription_id}/jobs", response_model=list[TranscriptionJob]
)
async def get_transcription_jobs_route(
    transcription_id: UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> list[TranscriptionJob]:
    """Get all transcription jobs for a specific transcription."""
    # Verify user has access to this transcription
    transcription = get_transcription_by_id(
        transcription_id, current_user.id, UK_TIMEZONE
    )
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return get_transcription_jobs(transcription_id)


@router.get("/user", response_model=User)
async def get_current_user_route(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get the current user's details."""
    return get_user_by_id(current_user.id)


# Add missing routes that frontend expects
@router.get("/users/me", response_model=User)
async def get_current_user_me_route(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get the current user's details (alias for /user)."""
    return get_user_by_id(current_user.id)


@router.get("/user/profile", response_model=User)
async def get_user_profile_route(
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Get the current user's profile (alias for /user)."""
    return get_user_by_id(current_user.id)




@router.post("/user", response_model=User)  # changed from .patch to .post
async def update_current_user_route(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Update the current user's details."""
    update_fields = request.model_dump(exclude_unset=True)
    return update_user(current_user.id, **update_fields)


@router.post("/langfuse/trace")
async def submit_langfuse_trace(
    request: LangfuseTraceRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
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

        logger.info(f"Langfuse trace '{request.name}' submitted for trace {request.trace_id} by user {current_user.email}")

    except Exception as e:
        logger.error(f"Failed to submit Langfuse trace: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to submit trace: {e!s}") from e
    else:
        return {"success": True, "message": "Trace submitted successfully"}


@router.post("/langfuse/score")
async def submit_langfuse_score(
    request: LangfuseScoreRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
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
        logger.error(f"Failed to submit Langfuse score: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to submit score: {e!s}") from e
    else:
        return {"success": True, "message": "Score submitted successfully"}


# Legacy endpoint for backward compatibility
@router.post("/langfuse/event")
async def submit_langfuse_event_legacy(
    request: LangfuseEventRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
):
    """Submit an event/score to Langfuse via backend proxy (legacy - use /langfuse/trace or /langfuse/score)."""
    if request.event_type == "score":
        if request.value is None:
            raise HTTPException(status_code=400, detail="Score value is required for score events")

        score_request = LangfuseScoreRequest(
            trace_id=request.trace_id,
            name=request.name,
            value=request.value,
            comment=request.comment,
        )
        return await submit_langfuse_score(score_request, current_user)

    elif request.event_type == "event":
        trace_request = LangfuseTraceRequest(
            trace_id=request.trace_id,
            name=request.name,
            metadata=request.metadata,
            input_data=request.input_data,
            output_data=request.output_data,
        )
        return await submit_langfuse_trace(trace_request, current_user)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported event type: {request.event_type}")
