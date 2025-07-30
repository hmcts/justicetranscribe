import shutil
import subprocess
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import aioboto3
import ffmpeg
import httpx

from app.logger import logger
from shared_utils.database.postgres_models import DialogueEntry
from shared_utils.settings import settings_instance

async_s3_session = aioboto3.Session()


@asynccontextmanager
async def get_s3_client():
    s3_config = {}
    if settings_instance.USE_LOCALSTACK:
        s3_config = {
            "endpoint_url": "http://localhost:4566",
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
        }

    async with async_s3_session.client("s3", **s3_config) as s3:
        yield s3


def is_rate_limit_error(exception):
    """Check if the exception is due to rate limiting (HTTP 429)"""
    return (
        isinstance(exception, httpx.HTTPStatusError) and exception.response.status_code == 429  # noqa: PLR2004
    )


def get_file_s3_key(user_email: str, file_name: str) -> str:
    """
    Generate a consistent S3 file key for user uploads.

    Args:
        user_email (str): The email of the user uploading the file
        extension (str): The file extension

    Returns:
        str: The generated file key in the format 'user-uploads/{email}/{uuid}.{extension}'
    """
    return f"user-uploads/{user_email}/{file_name}"


def convert_to_mp3(  # noqa: C901, PLR0912
    input_file_path: Path, output_file=None, bitrate="192k", vbr=None
) -> Path:
    """
    Convert any audio or video file to MP3 format using FFmpeg.

    Args:
    input_file (str): Path to the input audio or video file.
    output_file (str, optional): Path to the output MP3 file. If not provided,
                                 it will be generated based on the input file name.
    bitrate (str, optional): The bitrate for the output MP3 file. Default is '192k'.
    vbr (int, optional): VBR quality setting (0-9). If provided, overrides bitrate.
                         0 is highest quality, 9 is lowest. None means CBR is used.

    Returns:
    str: Path to the output MP3 file.

    Raises:
    FileNotFoundError: If the input file doesn't exist.
    RuntimeError: If FFmpeg encounters an error during conversion.
    ValueError: If invalid bitrate or VBR quality is provided.
    """

    temp_output = None

    if not Path(input_file_path).is_file():
        msg = f"Input file not found: {input_file_path}"
        # logger.error(msg)
        raise FileNotFoundError(msg)

    # Always generate an output filename if not provided
    if output_file is None:
        # input_path = Path(input_file_path)
        output_file = str(input_file_path.with_name(f"{input_file_path.stem}_converted.mp3"))

    # Validate bitrate format
    if not bitrate.endswith(("k", "K")) or not bitrate[:-1].isdigit():
        msg = f"Invalid bitrate format: {bitrate}. Use format like '192k'."
        # logger.error(msg)
        raise ValueError(msg)

    # Validate VBR quality
    if vbr is not None and not (0 <= vbr <= 9):  # noqa: PLR2004
        msg = f"Invalid VBR quality: {vbr}. Must be between 0 and 9."
        # logger.error(msg)
        raise ValueError(msg)

    try:
        # logger.info("Probing input file for audio streams")
        probe = ffmpeg.probe(input_file_path)
        audio_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "audio"]

        if not audio_streams:
            msg = f"No audio stream found in the input file: {input_file_path}"
            # logger.error(msg)
            raise RuntimeError(msg)

        # Create a temporary file if the input is an MP3
        if str(input_file_path).lower().endswith(".mp3"):
            temp_output = tempfile.NamedTemporaryFile(  # noqa: SIM115
                suffix=".mp3", delete=False
            ).name
            final_output = output_file
        else:
            temp_output = output_file
            final_output = output_file
            # logger.info("Input is not MP3. No temporary file needed.")

        # Open the input file
        input_stream = ffmpeg.input(input_file_path)

        # Set up the output stream with the desired parameters
        output_args = {
            "acodec": "libmp3lame",  # Use LAME MP3 encoder
            "loglevel": "warning",  # Show warnings and errors
        }

        if vbr is not None:
            output_args["qscale:a"] = vbr  # Use VBR encoding
        else:
            output_args["audio_bitrate"] = bitrate  # Use CBR encoding

        output_stream = ffmpeg.output(input_stream, temp_output, **output_args)

        # Run the FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True)
        # logger.info("FFmpeg command completed successfully")

        # If we used a temporary file, replace the original
        if temp_output and temp_output != final_output:
            shutil.move(temp_output, final_output)

    except Exception:
        # logger.exception("Unexpected error occurred")
        # log error message:
        # logger.exception(e)

        # Clean up the temporary file if it was created
        if temp_output and Path(temp_output).exists():
            # logger.info("Removing temporary file: %s", temp_output)
            Path(temp_output).unlink()
        raise
    else:
        return output_file


def convert_input_dialogue_entries_to_dialogue_entries(
    entries: list,
) -> list[DialogueEntry]:
    return [
        DialogueEntry(
            speaker=str(entry["speaker"]),
            text=entry["text"],
            start_time=float(entry["offsetMilliseconds"]) / 1000,
            end_time=(float(entry["offsetMilliseconds"]) + float(entry["durationMilliseconds"])) / 1000,
        )
        for entry in entries
    ]


def get_audio_duration(file_path: Path) -> float:
    """
    Get the duration of an audio file in seconds using ffprobe.

    Args:
        file_path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        ValueError: If the file cannot be processed or is invalid
    """
    try:
        logger.info("Getting audio duration using ffprobe")
        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"ffprobe command failed with return code {result.returncode}")
            logger.error(f"ffprobe stderr: {result.stderr}")
            raise ValueError(  # noqa: TRY003
                "Failed to get duration using ffprobe"  # noqa: EM101
            )

        duration = float(result.stdout)
        logger.info(f"Successfully got duration using ffprobe: {duration} seconds")
        return duration  # noqa: TRY300

    except Exception as e:
        logger.error(f"Failed to get audio duration: {e!s}", exc_info=True)
        raise


async def cleanup_files(temp_path: Path | None) -> None:
    """Helper function to clean up temporary files and S3 objects."""
    try:
        # Clean up local files
        if temp_path and temp_path.exists():
            temp_path.unlink()
    except Exception as e:
        logger.error(f"Error cleaning up files: {e!s}", exc_info=True)


def get_url_for_transcription(transcription_id: UUID) -> str:
    # https://justice-transcribe.ai.cabinetoffice.gov.uk/?id=027fecb0-6d4f-4ecb-b742-161adb5bad22
    app_url = settings_instance.APP_URL
    if not app_url.startswith("https://"):
        app_url = f"https://{app_url.removeprefix('http://')}"
    return f"{app_url}/?id={transcription_id}"
