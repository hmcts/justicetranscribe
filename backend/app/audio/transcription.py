import asyncio
import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

import aiofiles
import httpx
from fastapi import HTTPException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from uwotm8 import convert_american_to_british_spelling

from app.audio.utils import (
    cleanup_files,
    convert_input_dialogue_entries_to_dialogue_entries,
    get_blob_service_client,
)
from app.logger import logger
from app.database.postgres_models import DialogueEntry
from utils.settings import settings_instance

TOO_MANY_REQUESTS = 429


async def transcribe_audio(user_upload_s3_file_key: str) -> list[DialogueEntry]:
    result = await perform_transcription_steps_with_azure_and_aws(user_upload_s3_file_key)

    # Convert to British English spelling regardless of which service was used
    for entry in result:
        entry.text = convert_american_to_british_spelling(entry.text)

    return result


# deepgram = DeepgramClient(
#     config=DeepgramClientOptions(
#         url=settings_instance.DEEPGRAM_API_URL,
#         api_key=settings_instance.DEEPGRAM_API_KEY,
#     )
# )


# async def perform_transcription_steps_with_deepgram(
#     user_upload_s3_file_key: str,
# ) -> list[DialogueEntry]:
#     async with get_s3_client() as s3:
#         # Generate presigned GET URL
#         presigned_url = await s3.generate_presigned_url(
#             "get_object",
#             Params={
#                 "Bucket": settings_instance.DATA_S3_BUCKET,
#                 "Key": user_upload_s3_file_key,
#             },
#             ExpiresIn=600,
#         )
#         print("presigned_url", presigned_url)

#     options = PrerecordedOptions(smart_format=True, model="nova-3", diarize=True)

#     response = deepgram.listen.rest.v("1").transcribe_url(
#         {"url": presigned_url}, options, timeout=httpx.Timeout(300.0, connect=10.0)
#     )

#     dialogue_entries = []

#     transcript = response.results.channels[0].alternatives[0]

#     for word in transcript.words:
#         entry = DialogueEntry(
#             speaker=f"Speaker {word.speaker if hasattr(word, 'speaker') else 'Unknown'}",
#             text=word.word,
#             start_time=word.start,
#             end_time=word.end,
#         )
#         dialogue_entries.append(entry)

#     return dialogue_entries


async def perform_transcription_steps_with_azure_and_aws(
    user_upload_blob_path: str,
) -> list[DialogueEntry]:
    temp_file_path = None

    try:
        file_extension = Path(user_upload_blob_path).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            logger.info(f"Downloading file from Azure Blob Storage: {user_upload_blob_path} to {temp_file.name}")

            # Use async Azure Blob client
            async with get_blob_service_client() as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=settings_instance.AZURE_STORAGE_CONTAINER_NAME,
                    blob=user_upload_blob_path
                )
                
                # Download the blob content
                download_stream = await blob_client.download_blob()
                content = await download_stream.readall()
                temp_file.write(content)

            temp_file_path = Path(temp_file.name)

        result = await transcribe_audio_with_azure(temp_file_path)

    except Exception:
        await cleanup_files(temp_file_path)
        raise
    else:
        await cleanup_files(temp_file_path)
        return result


# async def actually_transcribe_audio_azure_or_aws(
#     audio_file_path: Path,
# ) -> list[DialogueEntry]:
#     try:
#         return await transcribe_audio_with_azure(audio_file_path)
#     except Exception as e:
#         sentry_sdk.capture_exception(e)
#         logger.warning(f"Azure transcription failed, falling back to AWS: {e}")
#         return await transcribe_audio_with_aws_transcribe(audio_file_path)


# AWS Transcribe functionality has been removed - using Azure Speech Services only


# async def transcribe_audio_with_aws_transcribe(
#     audio_file_path: Path,
# ) -> list[DialogueEntry]:
#     file_name = uuid.uuid4()
#     file_extension = audio_file_path.suffix.lower()
#
#     s3_key = f"aws-transcribe/{file_name}{file_extension}"
#     async with aiofiles.open(audio_file_path, "rb") as audio_file:
#         file_content = await audio_file.read()
#         s3.put_object(Bucket=settings_instance.DATA_S3_BUCKET, Key=s3_key, Body=file_content)
#
#     s3_uri = f"s3://{settings_instance.DATA_S3_BUCKET}/{s3_key}"
#     job_name = f"minute-transcription-job-{file_name}"
#
#     # Start transcription job
#     transcribe.start_transcription_job(
#         TranscriptionJobName=job_name,
#         Media={"MediaFileUri": s3_uri},
#         OutputBucketName=settings_instance.DATA_S3_BUCKET,
#         OutputKey=f"transcribe-output/{file_name}/",
#         LanguageCode="en-GB",
#         Settings={"ShowSpeakerLabels": True, "MaxSpeakerLabels": 30},
#     )
#
#     # Poll for completion
#     while True:
#         status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
#         job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
#
#         if job_status == "COMPLETED":
#             try:
#                 transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
#                 transcript_key = transcript_uri.split(f"{settings_instance.DATA_S3_BUCKET}/")[1]
#
#                 # Get the transcript JSON from S3
#                 response = s3.get_object(Bucket=settings_instance.DATA_S3_BUCKET, Key=transcript_key)
#                 transcript_content = json.loads(response["Body"].read().decode("utf-8"))
#
#                 # Extract and group audio segments
#                 audio_segments = transcript_content.get("results", {}).get("audio_segments", [])
#                 grouped_segments = convert_to_dialogue_entries(audio_segments)
#
#                 try:
#                     s3.delete_object(Bucket=settings_instance.DATA_S3_BUCKET, Key=transcript_key)
#                     s3.delete_object(Bucket=settings_instance.DATA_S3_BUCKET, Key=s3_key)
#                 except Exception as cleanup_error:
#                     logger.warning(f"Failed to delete transcript or audio file: {cleanup_error}")
#
#                 return grouped_segments  # noqa: TRY300
#
#             except Exception as e:
#                 logger.error(f"Error processing completed transcription: {e}")
#                 raise
#
#         elif job_status == "FAILED":
#             failure_reason = status["TranscriptionJob"].get("FailureReason", "Unknown error")
#             raise ValueError(  # noqa: TRY003
#                 f"Transcription job failed: {failure_reason}"
#             )
#
#         await asyncio.sleep(4)


def convert_to_dialogue_entries(transcript_data: list[dict]) -> list[DialogueEntry]:
    """
    Convert transcript data into a list of DialogueEntry objects.

    Args:
        transcript_data: List of transcript segments with speaker, text, and timing info

    Returns:
        List of DialogueEntry objects
    """
    dialogue_entries = []

    for segment in transcript_data:
        entry = DialogueEntry(
            speaker=segment["speaker_label"],
            text=segment["transcript"],
            start_time=float(segment["start_time"]),
            end_time=float(segment["end_time"]),
        )
        dialogue_entries.append(entry)

    return dialogue_entries


@retry(
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
)
async def transcribe_audio_with_azure(audio_file_path: Path):
    """
    Async version of transcribe audio using Azure Speech-to-Text API
    """
    url = "https://production-justice-ai.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
    if not settings_instance.AZURE_SPEECH_KEY:
        raise HTTPException(status_code=500, detail="AZURE_SPEECH_KEY not set")
    headers = {"Ocp-Apim-Subscription-Key": settings_instance.AZURE_SPEECH_KEY}
    async with aiofiles.open(audio_file_path, "rb") as audio_file:
        audio_content = await audio_file.read()
        files: Any = {
            "audio": ("audio.webm", audio_content),
            "definition": (
                None,
                '{"locales":["en-GB"],"diarization":{"enabled":true},"profanityFilterMode":"None"}',
            ),
        }

        timeout_settings = httpx.Timeout(
            timeout=900.0,
            connect=900.0,
            read=900.0,
            write=900.0,
        )

        async with httpx.AsyncClient(timeout=timeout_settings) as client:
            response = await client.post(url, headers=headers, files=files)
            if response.status_code == TOO_MANY_REQUESTS:
                response.raise_for_status()

            full_response = response.json()

            # Check for error response first
            if "code" in full_response:
                error_message = full_response.get("message", "Unknown error occurred")
                logger.error(f"Azure API error: {error_message}")
                raise HTTPException(status_code=422, detail=error_message)

            # If no error, proceed with phrases extraction
            phrases = full_response.get("phrases")
            if not phrases:
                raise HTTPException(
                    status_code=500,
                    detail="No transcription phrases found in response",
                )

            return convert_input_dialogue_entries_to_dialogue_entries(phrases)

