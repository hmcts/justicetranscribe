# ruff: noqa
import os
import json
import time
from datetime import datetime
from typing import List, Any

from langfuse import Langfuse
from langfuse.api.core.api_error import ApiError
from shared_utils.settings import settings_instance

BATCH_SIZE = 50  # Reduced batch size to be gentler on API
REQUEST_DELAY = 0.5  # Delay between requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests
MAX_OBSERVATIONS = None  # Set to None for unlimited, or specify a number to limit (e.g., 100)

langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),  # Use env var or fallback
    environment=settings_instance.ENVIRONMENT,
)


def fetch_with_retry(fetch_func, *args, **kwargs):
    """Fetch data with exponential backoff retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(REQUEST_DELAY)  # Rate limiting delay
            return fetch_func(*args, **kwargs)
        except ApiError as e:
            if e.status_code == 429:  # Rate limit error
                wait_time = (2**attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                print(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}). Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                if attempt == MAX_RETRIES - 1:
                    print(f"Max retries reached. Skipping this request.")
                    return None
            else:
                print(f"API error: {e}")
                return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    return None


now = datetime.now()

# Initialize variables for paging
all_observations = []
current_page = 1
fetched_count = 0

# Fetch all observations with paging
while True:
    print(f"Fetching page {current_page}...")

    observations_batch = fetch_with_retry(
        langfuse.fetch_observations,
        page=current_page,
        limit=BATCH_SIZE,
        name="generate_full_crissa",
    )

    if observations_batch is None or not observations_batch.data:
        print(f"No more observations found. Total fetched: {fetched_count}")
        break

    # Filter for prod environment
    filtered_observations = [obs for obs in observations_batch.data if obs.environment == "prod"]

    # Check if adding these observations would exceed our limit
    if MAX_OBSERVATIONS is not None:
        remaining_slots = MAX_OBSERVATIONS - fetched_count
        if remaining_slots <= 0:
            print(f"Reached maximum limit of {MAX_OBSERVATIONS} observations")
            break
        # Truncate the batch if it would exceed the limit
        if len(filtered_observations) > remaining_slots:
            filtered_observations = filtered_observations[:remaining_slots]
            print(f"Truncating batch to stay within limit of {MAX_OBSERVATIONS}")

    # Add to our collection
    all_observations.extend(filtered_observations)
    fetched_count += len(filtered_observations)
    current_page += 1

    print(f"Fetched {len(filtered_observations)} observations on page {current_page-1}. Total so far: {fetched_count}")

    # Check if we've reached our limit
    if MAX_OBSERVATIONS is not None and fetched_count >= MAX_OBSERVATIONS:
        print(f"Reached maximum limit of {MAX_OBSERVATIONS} observations")
        break

    # If we got fewer than BATCH_SIZE, we've reached the end
    if len(observations_batch.data) < BATCH_SIZE:
        break

print(f"Total observations fetched: {len(all_observations)}")

# Create JSON file to store observations
json_filename = f"evaluation/llm/crissa/.outputs/raw_langfuse_data/generate_full_crissa_observations_{now.strftime('%Y%m%d_%H%M%S')}.json"

# Format observations for JSON
formatted_observations = []
for i, obs in enumerate(all_observations):
    print(f"Processing observation {i+1}/{len(all_observations)} - {obs.trace_id}")

    # Fetch trace with retry logic
    trace = fetch_with_retry(langfuse.fetch_trace, obs.trace_id)

    if trace is None:
        print(f"Failed to fetch trace {obs.trace_id}, skipping...")
        continue

    print(f"TRACE scores: {trace.data.scores}")

    # Convert datetime to string to make it JSON serializable
    observation_date = (
        obs.start_time.isoformat() if hasattr(obs, "start_time") and obs.start_time else datetime.now().isoformat()
    )

    # Extract scores information
    scores = []
    if trace.data.scores:
        for score in trace.data.scores:
            score_data = {
                "name": score.name,
                "value": score.value,
                "comment": score.comment,
            }
            # Handle categorical scores that might have string_value
            if hasattr(score, "string_value"):
                score_data["string_value"] = score.string_value
            scores.append(score_data)

    # Add observation to our list
    formatted_observations.append(
        {
            "trace_id": obs.trace_id,
            "observation_id": obs.id,
            "date": observation_date,
            "input": obs.input,
            "output": obs.output,
            "scores": scores,
        }
    )

# Write all observations to JSON file
with open(json_filename, "w", encoding="utf-8") as jsonfile:
    # Use a custom default function to handle non-serializable objects
    def json_serializer(obj):
        if isinstance(obj, (datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    json.dump(
        formatted_observations,
        jsonfile,
        ensure_ascii=False,
        default=json_serializer,
        indent=2,
    )

print(f"Observations saved to {json_filename}")
print(f"Total number of observations saved: {len(formatted_observations)}")
