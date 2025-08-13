# ruff: noqa: T201

import asyncio

from langfuse import Langfuse  # Adjust import if needed

from backend.app.minutes.scripts.transcript_generator import generate_transcript

MODEL = "vertex_ai/gemini-2.5-flash-preview-04-17"
METHOD = "converted"
DATASET_NAME = "Synthetic-transcripts-v1"
NUM_TRANSCRIPTS = 10

# Initialize your langfuse client (adjust as needed)
langfuse = Langfuse()  # Add any required arguments/configuration


async def generate_one_transcript():
    print("Generating transcript...")
    transcript = await generate_transcript(MODEL, METHOD)
    print(f"Transcript generated length: {len(transcript)}")
    if transcript:
        return [entry.model_dump() for entry in transcript]
    else:
        print("Failed to generate transcript, skipping.")
        return None


async def main():
    print(f"Generating {NUM_TRANSCRIPTS} transcripts in parallel...")
    # Launch all transcript generation tasks concurrently
    tasks = [generate_one_transcript() for _ in range(NUM_TRANSCRIPTS)]
    results = await asyncio.gather(*tasks)

    # Filter out any failed generations (None)
    local_items = [item for item in results if item is not None]

    for item in local_items:
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME, input=item, expected_output=None
        )
    print(
        f"Uploaded {len(local_items)} transcripts to Langfuse dataset '{DATASET_NAME}'."
    )


if __name__ == "__main__":
    asyncio.run(main())
