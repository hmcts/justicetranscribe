import asyncio
from uuid import UUID

import sentry_sdk

from app.audio.speakers import process_speakers_and_dialogue_entries
from app.audio.transcription import transcribe_audio
from app.audio.utils import (
    get_url_for_transcription,
)
from app.database.interface_functions import (
    save_transcription,
    save_transcription_job,
)
from app.database.postgres_models import (
    Transcription,
    TranscriptionJob,
)
from app.logger import logger
from app.minutes.llm_calls import (
    generate_llm_output_task,
    generate_meeting_title,
)
from app.minutes.templates.templates_metadata import (
    crissa_template,
    general_template,
)
from utils.gov_notify import send_email


async def generate_and_save_meeting_title(
    dialogue_entries: list, transcription: Transcription, user_id: UUID, user_email: str
) -> Transcription:
    try:
        logger.info(
            f"Generating meeting title for {len(dialogue_entries)} dialogue entries"
        )
        provisional_title = await generate_meeting_title(dialogue_entries, user_email)
        existing_transcription = transcription
        existing_transcription.title = provisional_title
        return save_transcription(existing_transcription, user_id)
    except Exception as e:
        logger.error(f"Error saving transcription: {e}")
        sentry_sdk.capture_exception(e)
        return transcription


async def transcribe_and_generate_llm_output(
    user_upload_blob_storage_file_key: str,
    user_id: UUID,
    user_email: str,
    transcription_id: str | None = None,
):
    # Start a Sentry transaction for the whole function
    with sentry_sdk.start_transaction(
        op="task", name="Transcribe and Generate LLM Output"
    ) as transaction:  # noqa: F841
        transcription_data = Transcription(id=transcription_id)
        transcription = save_transcription(transcription_data, user_id)

        try:
            dialogue_entries = await transcribe_audio(user_upload_blob_storage_file_key)
            updated_dialogue_entries = await process_speakers_and_dialogue_entries(
                dialogue_entries, user_email
            )
            save_transcription_job(
                TranscriptionJob(
                    transcription_id=transcription.id,
                    dialogue_entries=updated_dialogue_entries,
                    s3_audio_url=user_upload_blob_storage_file_key,
                )
            )

        except Exception as e:
            save_transcription_job(
                TranscriptionJob(
                    transcription_id=transcription.id,
                    dialogue_entries=[],
                    s3_audio_url=user_upload_blob_storage_file_key,
                    error_message=str(e),
                )
            )
            sentry_sdk.capture_exception(e)
            raise

        # Start all three tasks in parallel
        general_task = generate_llm_output_task(
            updated_dialogue_entries, transcription.id, general_template, user_email
        )
        title_task = generate_and_save_meeting_title(
            updated_dialogue_entries, transcription, user_id, user_email
        )
        crissa_task = generate_llm_output_task(
            updated_dialogue_entries, transcription.id, crissa_template, user_email
        )

        try:
            # Wait for all three tasks including CRISSA before sending email
            await asyncio.gather(general_task, title_task, crissa_task)
        except Exception as e:
            logger.error(f"Error in parallel tasks: {e}")
            sentry_sdk.capture_exception(e)

        try:
            send_email(
                user_email,
                get_url_for_transcription(transcription.id),
                transcription.title or "",
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            sentry_sdk.capture_exception(e)
