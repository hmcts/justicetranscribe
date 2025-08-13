# ruff: noqa

import asyncio
import json
import os
import re
from pathlib import Path
import logging
from datetime import datetime

from backend.app.minutes.templates.crissa import (
    generate_full_crissa,
)
from shared_utils.database.postgres_models import DialogueEntry

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from langfuse.decorators import langfuse_context

langfuse_context.configure(
    enabled=False,
)


async def process_evaluation(
    index, eval, semaphore, user_email="evaluation@example.com"
):
    try:
        # Check if the evaluation has the expected structure
        if "input" not in eval or "dialogue_entries" not in eval["input"]:
            logger.error(
                f"Evaluation at index {index} is missing expected keys. Structure: {eval.keys()}"
            )
            if "input" in eval:
                logger.error(f"Input keys: {eval['input'].keys()}")
            return eval

        # Extract the transcript
        transcript = eval["input"]["dialogue_entries"]

        # Use a semaphore to limit concurrent executions
        async with semaphore:
            # Call the one-shot function directly with the transcript string
            # one_shot_output = await generate_full_crissa_one_shot_with_refinement(
            #     transcript_string=transcript,
            #     user_email=user_email,
            #     today_date=eval["date"],
            # )
            full_crissa_output = await generate_full_crissa(
                dialogue_entries=transcript,
                user_email=user_email,
                today_date=eval["date"],
                prompt_version=33,
            )

        eval["new_output_to_compare"] = full_crissa_output
        logger.info(f"Successfully processed evaluation {index}")
    except Exception as e:
        logger.error(f"Error processing evaluation at index {index}: {str(e)}")
        logger.error(f"Evaluation structure: {eval}")

    return eval


async def process_evaluations(
    input_file_path, max_concurrent=10, start_index=0, limit=None, test_description=""
):
    # Load the JSON file
    with open(input_file_path, "r") as f:
        evaluations = json.load(f)

    logger.info(f"Loaded {len(evaluations)} evaluations from {input_file_path}")

    # Apply start index and limit
    if start_index > 0:
        evaluations = evaluations[start_index:]
        logger.info(
            f"Starting from index {start_index}, {len(evaluations)} evaluations remaining"
        )

    if limit is not None:
        evaluations = evaluations[:limit]
        end_index = start_index + len(evaluations) - 1
        logger.info(
            f"Processing evaluations {start_index} to {end_index} ({len(evaluations)} total)"
        )
    else:
        end_index = start_index + len(evaluations) - 1
        logger.info(
            f"Processing evaluations {start_index} to {end_index} ({len(evaluations)} total)"
        )

    # Create a semaphore to limit concurrent executions
    semaphore = asyncio.Semaphore(max_concurrent)

    # Process evaluations in parallel - adjust index to reflect original position
    tasks = [
        process_evaluation(start_index + idx, eval, semaphore)
        for idx, eval in enumerate(evaluations)
    ]
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
    sanitized_description = (
        re.sub(r"[^\w\-_]", "_", test_description.strip()) if test_description else ""
    )
    description_str = f"_{sanitized_description}" if sanitized_description else ""

    # Create output filename with timestamp, hyperparameters, and description
    output_filename = f"{timestamp}_{hyperparam_str}{description_str}.json"

    # Create outputs subfolder
    output_dir = input_path.parent / "crissa_generated_outputs"
    output_dir.mkdir(exist_ok=True)

    output_file_path = output_dir / output_filename

    with open(output_file_path, "w") as f:
        json.dump(processed_evals, f, indent=2)

    return output_file_path


async def main():
    # Prompt user for test description
    test_description = input(
        "Enter a short description of what you're testing: "
    ).strip()
    if test_description:
        logger.info(f"Test description: {test_description}")

    # Find the most recent evaluation file
    # Allow using a specific file path or fall back to finding the most recent file
    specific_file_path = "evaluation/llm/.outputs/generate_full_crissa_observations_with_diff_summary.json"  # Set this to your specific path when needed

    if specific_file_path:
        latest_file = Path(specific_file_path)
        logger.info(f"Using specified file: {latest_file}")
    else:
        eval_dir = Path("evaluation/llm/.outputs")
        # Look for files matching the pattern
        files = list(eval_dir.glob("generate_full_crissa_observations_*.json"))
        if not files:
            logger.error("No evaluation files found")
            return

    # Get the most recent file
    # latest_file = max(files, key=os.path.getctime)
    # logger.info(f"Processing file: {latest_file}")

    # Examine file structure (for debugging)
    with open(latest_file, "r") as f:
        data = json.load(f)
        logger.info(f"File contains {len(data)} items")
        if len(data) > 0:
            logger.info(f"First item keys: {data[0].keys()}")
            if "input" in data[0]:
                logger.info(f"First item input keys: {data[0]['input'].keys()}")

    # Number of concurrent executions
    max_concurrent = 10

    # Limit number of evaluations to process (None = process all)
    limit = 50  # Set to None to process all, or a number to limit for testing
    start_index = 200
    # Process the evaluations
    output_file = await process_evaluations(
        latest_file, max_concurrent, start_index, limit, test_description
    )
    logger.info(f"Updated evaluations saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
