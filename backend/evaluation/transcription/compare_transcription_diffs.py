# ruff: noqa
import asyncio
import difflib
import json
from pathlib import (
    Path,
)  # Keep for type hinting if necessary, though not directly used now
from typing import Any

# import aiofiles # No longer directly used in this script
# import httpx # No longer directly used in this script
# from deepgram import DeepgramClient, PrerecordedOptions # No longer directly used
from uwotm8 import convert_american_to_british_spelling

from backend.app.audio.transcription import (
    perform_transcription_steps_with_deepgram,
    perform_transcription_steps_with_azure_and_aws,
    # get_s3_client, # No longer directly needed by this script's functions
)

# from backend.app.audio.utils import cleanup_files # No longer directly needed
from backend.app.logger import logger
from backend.app.minutes.types import DialogueEntry
from shared_utils.settings import settings_instance

# Import the speaker processing function
from backend.app.audio.speakers import process_speakers_and_dialogue_entries


def print_dialogue_entries(service_name: str, entries: list[DialogueEntry]) -> str:
    """Prints dialogue entries and returns the full concatenated text."""
    print(f"\n--- {service_name} Transcription ---")
    full_text_parts = []
    if not entries:
        print("No dialogue entries found.")
        return ""

    for entry in entries:
        print(
            f"  Speaker {entry.speaker} ({entry.start_time:.2f}s - {entry.end_time:.2f}s): {entry.text}"
        )
        full_text_parts.append(entry.text)
    concatenated_text = " ".join(full_text_parts)
    print(f"\nFull text ({service_name}):\n{concatenated_text}")
    return concatenated_text


async def compare_transcriptions(s3_file_key: str):
    """
    Fetches transcriptions, processes speaker labels, prints them,
    saves to JSON in a specific folder with descriptive names, and shows a diff.
    """
    logger.info(f"Starting transcription comparison for S3 key: {s3_file_key}")

    # Define a placeholder user email for speaker processing
    user_email_for_processing = "eval_user@example.com"
    logger.info(f"Using user email for speaker processing: {user_email_for_processing}")

    # --- Define output directory and create it if it doesn't exist ---
    output_dir = Path(
        "evaluation/transcription/transcription_comparisons/individual_transcriptions"
    )
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured output directory exists: {output_dir.resolve()}")
    except Exception as e:
        logger.error(f"Could not create output directory {output_dir}: {e}")
        # Decide if we should exit or try to save in current dir as fallback
        # For now, let's try to continue and save where it can if possible (OS might prevent)
        # Or, more robustly:
        # return

    # --- Sanitize s3_file_key for use in filename ---
    sanitized_s3_key_for_filename = s3_file_key.replace("/", "_").replace("\\", "_")

    deepgram_entries_raw: list[DialogueEntry] = []
    azure_aws_entries_raw: list[DialogueEntry] = []

    try:
        logger.info(f"Requesting Deepgram transcription for: {s3_file_key}")
        deepgram_entries_raw = await perform_transcription_steps_with_deepgram(
            s3_file_key
        )
        logger.info(
            f"Retrieved {len(deepgram_entries_raw)} entries from Deepgram pathway."
        )
    except Exception as e:
        logger.error(f"Failed to get Deepgram transcription: {e}")

    try:
        logger.info(f"Requesting Azure/AWS transcription for: {s3_file_key}")
        azure_aws_entries_raw = await perform_transcription_steps_with_azure_and_aws(
            s3_file_key
        )
        logger.info(
            f"Retrieved {len(azure_aws_entries_raw)} entries from Azure/AWS pathway."
        )
    except Exception as e:
        logger.error(f"Failed to get Azure/AWS transcription: {e}")

    # Convert to British English first
    deepgram_entries_british = [
        DialogueEntry(
            speaker=entry.speaker,
            text=convert_american_to_british_spelling(entry.text),
            start_time=entry.start_time,
            end_time=entry.end_time,
        )
        for entry in deepgram_entries_raw
    ]
    azure_aws_entries_british = [
        DialogueEntry(
            speaker=entry.speaker,
            text=convert_american_to_british_spelling(entry.text),
            start_time=entry.start_time,
            end_time=entry.end_time,
        )
        for entry in azure_aws_entries_raw
    ]

    # --- Process speaker labels ---
    processed_deepgram_entries: list[DialogueEntry] = []
    if deepgram_entries_british:
        try:
            logger.info("Processing speaker labels for Deepgram transcription...")
            processed_deepgram_entries = await process_speakers_and_dialogue_entries(
                deepgram_entries_british, user_email_for_processing
            )
            logger.info("Deepgram speaker processing complete.")
        except Exception as e:
            logger.error(f"Error processing speakers for Deepgram output: {e}")
            processed_deepgram_entries = (
                deepgram_entries_british  # Fallback to pre-processed
            )
    else:
        logger.info("Skipping speaker processing for empty Deepgram transcription.")

    processed_azure_aws_entries: list[DialogueEntry] = []
    if azure_aws_entries_british:
        try:
            logger.info("Processing speaker labels for Azure/AWS transcription...")
            processed_azure_aws_entries = await process_speakers_and_dialogue_entries(
                azure_aws_entries_british, user_email_for_processing
            )
            logger.info("Azure/AWS speaker processing complete.")
        except Exception as e:
            logger.error(f"Error processing speakers for Azure/AWS output: {e}")
            processed_azure_aws_entries = (
                azure_aws_entries_british  # Fallback to pre-processed
            )
    else:
        logger.info("Skipping speaker processing for empty Azure/AWS transcription.")
    # --- End of speaker processing ---

    # --- Save processed output to JSON files with new naming and directory ---
    if processed_deepgram_entries:
        deepgram_filename = f"{sanitized_s3_key_for_filename}_deepgram_processed.json"
        deepgram_filepath = output_dir / deepgram_filename
        deepgram_serializable = [
            entry.model_dump() if hasattr(entry, "model_dump") else entry.__dict__
            for entry in processed_deepgram_entries
        ]
        try:
            with open(deepgram_filepath, "w", encoding="utf-8") as f_deepgram_json:
                json.dump(deepgram_serializable, f_deepgram_json, indent=4)
            logger.info(
                f"Processed Deepgram transcription saved to {deepgram_filepath}"
            )
        except Exception as e:
            logger.error(f"Failed to save Deepgram JSON to {deepgram_filepath}: {e}")

    if processed_azure_aws_entries:
        azure_aws_filename = f"{sanitized_s3_key_for_filename}_azure_aws_processed.json"
        azure_aws_filepath = output_dir / azure_aws_filename
        azure_aws_serializable = [
            entry.model_dump() if hasattr(entry, "model_dump") else entry.__dict__
            for entry in processed_azure_aws_entries
        ]
        try:
            with open(azure_aws_filepath, "w", encoding="utf-8") as f_azure_json:
                json.dump(azure_aws_serializable, f_azure_json, indent=4)
            logger.info(
                f"Processed Azure/AWS transcription saved to {azure_aws_filepath}"
            )
        except Exception as e:
            logger.error(f"Failed to save Azure/AWS JSON to {azure_aws_filepath}: {e}")
    # --- End of JSON saving ---

    # Use processed entries for printing and diffing
    deepgram_text = print_dialogue_entries(
        "Deepgram (Processed Speakers)", processed_deepgram_entries
    )
    azure_text = print_dialogue_entries(
        "Azure/AWS Fallback (Processed Speakers)", processed_azure_aws_entries
    )

    if not deepgram_text and not azure_text:
        logger.warning("Both transcriptions are empty. Nothing to compare.")
        return

    if not deepgram_text:
        logger.warning("Deepgram transcription is empty. Cannot compare.")
        # Still print Azure/AWS if it exists
        if azure_text:
            print("\nAzure/AWS transcription was present but Deepgram was empty.")
        return
    if not azure_text:
        logger.warning("Azure/AWS transcription is empty. Cannot compare.")
        # Still print Deepgram if it exists
        if deepgram_text:
            print("\nDeepgram transcription was present but Azure/AWS was empty.")
        return

    print("\n--- Diff (Deepgram vs Azure/AWS) ---")
    # Use splitlines() for difflib
    diff = difflib.unified_diff(
        deepgram_text.splitlines(keepends=True),
        azure_text.splitlines(keepends=True),
        fromfile="deepgram_transcription.txt",
        tofile="azure_aws_transcription.txt",
        lineterm="",
    )

    diff_lines = list(diff)  # Consume the generator to check if it's empty
    if not diff_lines:
        print("No differences found between the transcriptions.")
    else:
        for line in diff_lines:
            print(line, end="")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare Deepgram and Azure/AWS transcriptions for an S3 audio file using core app functions."
    )
    parser.add_argument(
        "s3_file_key",
        type=str,
        help="The S3 object key for the audio file (e.g., 'uploads/myaudio.wav')",
    )
    args = parser.parse_args()

    if not settings_instance.DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY not set in settings.")
        exit(1)
    if (
        not settings_instance.AZURE_SPEECH_KEY
    ):  # Azure key is still needed for the attempt
        logger.error("AZURE_SPEECH_KEY not set in settings.")
        exit(1)
    # AWS keys for transcribe and S3 will be picked up by boto3 from environment/config
    # if settings_instance.AWS_ACCESS_KEY_ID is not set, etc.
    # but DATA_S3_BUCKET is crucial.
    if not settings_instance.DATA_S3_BUCKET:
        logger.error("DATA_S3_BUCKET not set in settings.")
        exit(1)

    asyncio.run(compare_transcriptions(args.s3_file_key))
