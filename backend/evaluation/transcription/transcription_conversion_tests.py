# ruff: noqa

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.audio.speakers import group_dialogue_entries_by_speaker
from backend.app.audio.transcription import (
    actually_transcribe_audio_azure_or_aws,
    # perform_transcription_steps_with_deepgram,
    # perform_transcription_steps_with_deepgram_mp3_conversion,
)
from backend.app.audio.utils import convert_to_mp3, get_s3_client
from backend.app.minutes.types import DialogueEntry


def save_transcript(entries: list[DialogueEntry], output_path: Path) -> None:
    """Save transcript entries to a JSON file."""
    # Convert entries to a list of dicts for JSON serialization
    entries_dict = [
        {
            "speaker": entry.speaker,
            "text": entry.text,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
        }
        for entry in entries
    ]

    with open(output_path, "w") as f:
        json.dump(entries_dict, f, indent=2)


async def list_s3_files(bucket: str, prefix: str) -> list[str]:
    """List all files in the given S3 bucket prefix."""
    async with get_s3_client() as s3:
        paginator = s3.get_paginator("list_objects_v2")
        files = []
        async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    files.append(obj["Key"])
    return files


# @retry(
#     stop=stop_after_attempt(3),
#     wait=wait_exponential(multiplier=1, min=4, max=10),
#     reraise=True,
# )
# async def download_and_transcribe_deepgram(s3_key: str) -> list[DialogueEntry]:
#     """Download a file from S3 and transcribe it using Deepgram with retry logic."""
#     try:
#         return await perform_transcription_steps_with_deepgram(s3_key)
#     except Exception as e:
#         print(f"Deepgram transcription attempt failed for {s3_key}: {e!s}")
#         raise


# @retry(
#     stop=stop_after_attempt(3),
#     wait=wait_exponential(multiplier=1, min=4, max=10),
#     reraise=True,
# )
# async def download_and_transcribe_deepgram_with_mp3(s3_key: str) -> list[DialogueEntry]:
#     """Download a file from S3 and transcribe it using Deepgram with MP3 conversion."""
#     try:
#         return await perform_transcription_steps_with_deepgram_mp3_conversion(s3_key)
#     except Exception as e:
#         print(
#             f"Deepgram with MP3 conversion transcription attempt failed for {s3_key}: {e!s}"
#         )
#         raise


async def download_and_transcribe(
    s3_key: str,
    use_conversion: bool = True,
    use_deepgram: bool = False,
    use_deepgram_mp3: bool = False,
) -> list[DialogueEntry]:
    """Download a file from S3 and transcribe it using the specified method."""
    temp_file_path = None
    converted_file_path = None

    try:
        # if use_deepgram_mp3:
        #     entries = await download_and_transcribe_deepgram_with_mp3(s3_key)
        # elif use_deepgram:
        #     entries = await download_and_transcribe_deepgram(s3_key)
        # else:
        file_extension = Path(s3_key).suffix.lower()
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            async with get_s3_client() as s3:
                await s3.download_fileobj(
                    "i-dot-ai-prod-justice-transcribe-data", s3_key, temp_file
                )
            temp_file_path = Path(temp_file.name)

        if use_conversion:
            converted_file_path = convert_to_mp3(temp_file_path)
            entries = await actually_transcribe_audio_azure_or_aws(converted_file_path)
        else:
            entries = await actually_transcribe_audio_azure_or_aws(temp_file_path)

        # Group entries by speaker before returning
        return group_dialogue_entries_by_speaker(entries)

    finally:
        pass
        # Clean up temporary files
        # if temp_file_path and temp_file_path.exists():
        #     temp_file_path.unlink()
        # if converted_file_path and converted_file_path.exists():
        #     converted_file_path.unlink()


async def process_single_file(s3_key: str, output_base_dir: Path) -> dict[str, Any]:
    """Process a single file and return the results."""
    try:
        print(f"\nTesting file: {s3_key}")

        # Create output directory for this file
        file_name = Path(s3_key).stem
        file_output_dir = output_base_dir / file_name
        file_output_dir.mkdir(parents=True, exist_ok=True)

        # First try Azure/AWS transcriptions
        without_conversion_task = download_and_transcribe(
            s3_key, use_conversion=False, use_deepgram=False, use_deepgram_mp3=False
        )
        with_conversion_task = download_and_transcribe(
            s3_key, use_conversion=True, use_deepgram=False, use_deepgram_mp3=False
        )

        without_conversion, with_conversion = await asyncio.gather(
            without_conversion_task, with_conversion_task
        )

        # Save transcripts
        save_transcript(without_conversion, file_output_dir / "without_conversion.json")
        save_transcript(with_conversion, file_output_dir / "with_conversion.json")

        print(f"Without conversion: {len(without_conversion)} entries")
        print(f"With conversion: {len(with_conversion)} entries")

        # Then try both Deepgram versions
        # try:
        #     deepgram_tasks = [
        #         download_and_transcribe(
        #             s3_key,
        #             use_conversion=False,
        #             use_deepgram=True,
        #             use_deepgram_mp3=False,
        #         ),
        #         download_and_transcribe(
        #             s3_key,
        #             use_conversion=False,
        #             use_deepgram=False,
        #             use_deepgram_mp3=True,
        #         ),
        #     ]
        #     deepgram, deepgram_mp3 = await asyncio.gather(*deepgram_tasks)
        #
        #     save_transcript(deepgram, file_output_dir / "deepgram.json")
        #     save_transcript(deepgram_mp3, file_output_dir / "deepgram_mp3.json")
        #
        #     print(f"Deepgram: {len(deepgram)} entries")
        #     print(f"Deepgram with MP3: {len(deepgram_mp3)} entries")
        # except Exception as e:
        #     print(f"Deepgram transcription failed for {s3_key}: {e!s}")
        #     deepgram = []
        #     deepgram_mp3 = []

        # Set empty values for deepgram results
        deepgram = []
        deepgram_mp3 = []

        # Get unique speakers for each method
        def get_unique_speakers(entries):
            return len(set(entry.speaker for entry in entries))

        speaker_counts = {
            "without_conversion": get_unique_speakers(without_conversion),
            "with_conversion": get_unique_speakers(with_conversion),
            # "deepgram": get_unique_speakers(deepgram) if deepgram else None,
            # "deepgram_mp3": get_unique_speakers(deepgram_mp3) if deepgram_mp3 else None,
        }

        # Compare results
        entry_counts = {
            "without_conversion": len(without_conversion),
            "with_conversion": len(with_conversion),
            # "deepgram": len(deepgram) if deepgram else None,
            # "deepgram_mp3": len(deepgram_mp3) if deepgram_mp3 else None,
        }

        # Check if there are any differences in either entries or speakers
        if (
            len(set(v for v in entry_counts.values() if v is not None)) > 1
            or len(set(v for v in speaker_counts.values() if v is not None)) > 1
        ):
            return {
                "file": s3_key,
                "without_conversion_count": entry_counts["without_conversion"],
                "with_conversion_count": entry_counts["with_conversion"],
                # "deepgram_count": entry_counts["deepgram"],
                # "deepgram_mp3_count": entry_counts["deepgram_mp3"],
                "speaker_counts": speaker_counts,
                "differences": {
                    "with_vs_without": entry_counts["with_conversion"]
                    - entry_counts["without_conversion"],
                    # "deepgram_vs_without": (
                    #     entry_counts["deepgram"] - entry_counts["without_conversion"]
                    #     if entry_counts["deepgram"] is not None
                    #     else None
                    # ),
                    # "deepgram_vs_with": (
                    #     entry_counts["deepgram"] - entry_counts["with_conversion"]
                    #     if entry_counts["deepgram"] is not None
                    #     else None
                    # ),
                    # "deepgram_mp3_vs_without": (
                    #     entry_counts["deepgram_mp3"]
                    #     - entry_counts["without_conversion"]
                    #     if entry_counts["deepgram_mp3"] is not None
                    #     else None
                    # ),
                    # "deepgram_mp3_vs_with": (
                    #     entry_counts["deepgram_mp3"] - entry_counts["with_conversion"]
                    #     if entry_counts["deepgram_mp3"] is not None
                    #     else None
                    # ),
                    # "deepgram_mp3_vs_deepgram": (
                    #     entry_counts["deepgram_mp3"] - entry_counts["deepgram"]
                    #     if entry_counts["deepgram_mp3"] is not None
                    #     and entry_counts["deepgram"] is not None
                    #     else None
                    # ),
                    "speaker_differences": {
                        "with_vs_without": speaker_counts["with_conversion"]
                        - speaker_counts["without_conversion"],
                        # "deepgram_vs_without": (
                        #     speaker_counts["deepgram"]
                        #     - speaker_counts["without_conversion"]
                        #     if speaker_counts["deepgram"] is not None
                        #     else None
                        # ),
                        # "deepgram_vs_with": (
                        #     speaker_counts["deepgram"]
                        #     - speaker_counts["with_conversion"]
                        #     if speaker_counts["deepgram"] is not None
                        #     else None
                        # ),
                        # "deepgram_mp3_vs_without": (
                        #     speaker_counts["deepgram_mp3"]
                        #     - speaker_counts["without_conversion"]
                        #     if speaker_counts["deepgram_mp3"] is not None
                        #     else None
                        # ),
                        # "deepgram_mp3_vs_with": (
                        #     speaker_counts["deepgram_mp3"]
                        #     - speaker_counts["with_conversion"]
                        #     if speaker_counts["deepgram_mp3"] is not None
                        #     else None
                        # ),
                        # "deepgram_mp3_vs_deepgram": (
                        #     speaker_counts["deepgram_mp3"] - speaker_counts["deepgram"]
                        #     if speaker_counts["deepgram_mp3"] is not None
                        #     and speaker_counts["deepgram"] is not None
                        #     else None
                        # ),
                    },
                },
            }
        return None

    except Exception as e:
        print(f"Error processing {s3_key}: {e!s}")
        return None


@pytest.mark.asyncio
async def test_transcription_with_and_without_conversion():
    """Test transcription results with and without convert_to_mp3."""
    # Replace these with your actual values
    BUCKET = "i-dot-ai-prod-justice-transcribe-data"
    PREFIX = "user-uploads/liz.bowen@justice.gov.uk/"

    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base_dir = (
        Path(__file__).parent
        / f"transcription_comparisons/transcription_comparison_{timestamp}"
    )
    output_base_dir.mkdir(parents=True, exist_ok=True)

    # Get list of files to test
    files = await list_s3_files(BUCKET, PREFIX)
    print(f"Found {len(files)} files to test")

    # Process files in parallel with a semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(
        10
    )  # Reduced to 3 since we're now doing 3 transcriptions per file

    async def process_with_semaphore(s3_key: str):
        async with semaphore:
            return await process_single_file(s3_key, output_base_dir)

    # Create tasks for all files
    tasks = [process_with_semaphore(s3_key) for s3_key in files]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)

    # Filter out None results and print summary
    results = [r for r in results if r is not None]

    # Save summary to a JSON file
    summary = {
        "timestamp": timestamp,
        "files_processed": len(files),
        "files_with_differences": len(results),
        "results": results,
    }

    with open(output_base_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    if results:
        print("\nSummary of files with differences:")
        for result in results:
            print(f"\nFile: {result['file']}")
            print(f"  Without conversion: {result['without_conversion_count']} entries")
            print(f"  With conversion: {result['with_conversion_count']} entries")
            # print(f"  Deepgram: {result['deepgram_count']}")
            # print(f"  Deepgram with MP3: {result['deepgram_mp3_count']}")
            print("\n  Speaker counts:")
            print(
                f"    Without conversion: {result['speaker_counts']['without_conversion']} speakers"
            )
            print(
                f"    With conversion: {result['speaker_counts']['with_conversion']} speakers"
            )
            # print(f"    Deepgram: {result['speaker_counts']['deepgram']}")
            # print(f"    Deepgram with MP3: {result['speaker_counts']['deepgram_mp3']}")
    else:
        print("\nNo differences found in any files")

    print(f"\nResults have been saved to: {output_base_dir}")


if __name__ == "__main__":
    asyncio.run(test_transcription_with_and_without_conversion())
