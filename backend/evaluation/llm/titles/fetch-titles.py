# ruff: noqa

import json
import os
import time
from datetime import datetime

from langfuse import Langfuse
from langfuse.api.core.api_error import ApiError

from shared_utils.settings import get_settings

# Configuration
BATCH_SIZE = 50
REQUEST_DELAY = 0.5  # seconds between requests
MAX_RETRIES = 3

# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    environment=get_settings().ENVIRONMENT,
)


def fetch_with_retry(fetch_func, *args, **kwargs):
    """Simple retry logic for API calls"""
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(REQUEST_DELAY)
            return fetch_func(*args, **kwargs)
        except ApiError as e:
            if e.status_code == 429:  # Rate limit
                wait_time = 2**attempt
                print(f"Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                print(f"API error: {e}")
                break
        except Exception as e:
            print(f"Error: {e}")
            break
    return None


def main():
    print("Fetching generate_meeting_title observations...")

    all_observations = []
    page = 1

    # Fetch all observations with pagination
    while True:
        print(f"Fetching page {page}...")

        batch = fetch_with_retry(
            langfuse.fetch_observations, page=page, limit=BATCH_SIZE, name="generate_meeting_title"
        )

        if not batch or not batch.data:
            break

        # Filter for prod environment
        prod_observations = [obs for obs in batch.data if obs.environment == "prod"]
        all_observations.extend(prod_observations)

        print(f"Found {len(prod_observations)} prod observations on page {page}")

        # Check if we've reached the end
        if len(batch.data) < BATCH_SIZE:
            break

        page += 1

    print(f"Total observations found: {len(all_observations)}")

    # Format observations for output
    formatted_observations = []
    for i, obs in enumerate(all_observations, 1):
        print(f"Processing {i}/{len(all_observations)}: {obs.id}")

        formatted_obs = {
            "observation_id": obs.id,
            "trace_id": obs.trace_id,
            "date": obs.start_time.isoformat() if obs.start_time else datetime.now().isoformat(),
            "input": obs.input,
            "output": obs.output,
        }
        formatted_observations.append(formatted_obs)

    # Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation/llm/titles/.outputs/meeting_title_observations_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(formatted_observations, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(formatted_observations)} observations to {filename}")


if __name__ == "__main__":
    main()
