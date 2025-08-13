# ruff: noqa

import asyncio
import json
import os
import re
from pathlib import Path
import logging
from datetime import datetime

from fastapi import HTTPException

from backend.app.minutes.llm_calls import generate_meeting_title
from shared_utils.database.postgres_models import DialogueEntry

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from langfuse.decorators import langfuse_context

langfuse_context.configure(
    enabled=False,
)


async def process_evaluation(index, eval, semaphore, user_email="evaluation@example.com"):
    try:
        # Check if the evaluation has the expected structure
        if "input" not in eval or "args" not in eval["input"]:
            logger.error(f"Evaluation at index {index} is missing expected keys. Structure: {eval.keys()}")
            if "input" in eval:
                logger.error(f"Input keys: {eval['input'].keys()}")
            return eval

        # Extract the dialogue entries and user email from args
        args = eval["input"]["args"]
        if len(args) < 2:
            logger.error(f"Evaluation at index {index} doesn't have enough args. Found {len(args)} args")
            return eval

        dialogue_entries_raw = args[0]
        user_email_from_args = args[1]

        # Convert raw dialogue entries to DialogueEntry objects
        dialogue_entries = [
            DialogueEntry(
                speaker=entry["speaker"], text=entry["text"], start_time=entry["start_time"], end_time=entry["end_time"]
            )
            for entry in dialogue_entries_raw
        ]

        # Use a semaphore to limit concurrent executions
        async with semaphore:
            # Call the generate_meeting_title function
            title_output = await generate_meeting_title(
                transcript=dialogue_entries,
                user_email=user_email_from_args,
            )

        eval["new_output_to_compare"] = title_output
        logger.info(f"Successfully processed evaluation {index}")

    except HTTPException as e:
        logger.error(f"HTTP error processing evaluation at index {index}: status={e.status_code}, detail={e.detail}")
        eval["error"] = f"HTTP {e.status_code}: {e.detail}"
    except ValueError as e:
        logger.error(f"Value error processing evaluation at index {index}: {str(e)}")
        eval["error"] = f"ValueError: {str(e)}"
    except TimeoutError as e:
        logger.error(f"Timeout error processing evaluation at index {index}: {str(e)}")
        eval["error"] = f"Timeout: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error processing evaluation at index {index}: {type(e).__name__}: {str(e)}")
        logger.error(f"Evaluation observation_id: {eval.get('observation_id', 'unknown')}")
        # Only log the full structure if it's a truly unexpected error
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        eval["error"] = f"{type(e).__name__}: {str(e)}"

    return eval


async def process_evaluations(input_file_path, max_concurrent=10, start_index=0, limit=None, test_description=""):
    # Load the JSON file
    with open(input_file_path, "r") as f:
        evaluations = json.load(f)

    logger.info(f"Loaded {len(evaluations)} evaluations from {input_file_path}")

    # Apply start index and limit
    if start_index > 0:
        evaluations = evaluations[start_index:]
        logger.info(f"Starting from index {start_index}, {len(evaluations)} evaluations remaining")

    if limit is not None:
        evaluations = evaluations[:limit]
        end_index = start_index + len(evaluations) - 1
        logger.info(f"Processing evaluations {start_index} to {end_index} ({len(evaluations)} total)")
    else:
        end_index = start_index + len(evaluations) - 1
        logger.info(f"Processing evaluations {start_index} to {end_index} ({len(evaluations)} total)")

    # Create a semaphore to limit concurrent executions
    semaphore = asyncio.Semaphore(max_concurrent)

    # Process evaluations in parallel - adjust index to reflect original position
    tasks = [process_evaluation(start_index + idx, eval, semaphore) for idx, eval in enumerate(evaluations)]
    processed_evals = await asyncio.gather(*tasks, return_exceptions=False)

    # Create organized output path with timestamp and hyperparameters
    input_path = Path(input_file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Extract base filename without extension
    base_name = input_path.stem

    # Create hyperparameter string
    limit_str = f"_limit{limit}" if limit is not None else "_full"
    start_str = f"_start{start_index}" if start_index > 0 else ""
    hyperparam_str = f"concurrent{max_concurrent}{start_str}{limit_str}"

    # Sanitize test description for filename
    sanitized_description = re.sub(r"[^\w\-_]", "_", test_description.strip()) if test_description else ""
    description_str = f"_{sanitized_description}" if sanitized_description else ""

    # Create output filename with timestamp, hyperparameters, and description
    output_filename = f"{timestamp}_{hyperparam_str}{description_str}.json"

    # Create outputs subfolder
    output_dir = input_path.parent / "titles_generated_outputs"
    output_dir.mkdir(exist_ok=True)

    output_file_path = output_dir / output_filename

    with open(output_file_path, "w") as f:
        json.dump(processed_evals, f, indent=2)

    return output_file_path


async def main():
    # Prompt user for test description
    test_description = input("Enter a short description of what you're testing: ").strip()
    if test_description:
        logger.info(f"Test description: {test_description}")

    # Find the most recent evaluation file
    # Allow using a specific file path or fall back to finding the most recent file
    specific_file_path = "evaluation/llm/titles/.outputs/meeting_title_observations_20250601_211442.json"  # Set this to your specific path when needed

    if specific_file_path:
        latest_file = Path(specific_file_path)
        logger.info(f"Using specified file: {latest_file}")
    else:
        eval_dir = Path("evaluation/llm/titles/.outputs")
        # Look for files matching the pattern
        files = list(eval_dir.glob("meeting_title_observations_*.json"))
        if not files:
            logger.error("No evaluation files found")
            return

        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        logger.info(f"Processing file: {latest_file}")

    # Examine file structure (for debugging)
    with open(latest_file, "r") as f:
        data = json.load(f)
        logger.info(f"File contains {len(data)} items")
        if len(data) > 0:
            logger.info(f"First item keys: {data[0].keys()}")
            if "input" in data[0]:
                logger.info(f"First item input keys: {data[0]['input'].keys()}")
            if "input" in data[0] and "args" in data[0]["input"]:
                logger.info(f"First item args length: {len(data[0]['input']['args'])}")

    # Number of concurrent executions
    max_concurrent = 500

    # Limit number of evaluations to process (None = process all)
    limit = 1000  # Set to None to process all, or a number to limit for testing
    start_index = 0

    # Process the evaluations
    output_file = await process_evaluations(latest_file, max_concurrent, start_index, limit, test_description)
    logger.info(f"Updated evaluations saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
