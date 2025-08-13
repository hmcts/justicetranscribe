# ruff: noqa
import asyncio
from datetime import datetime
import json
import os

import requests
from requests.auth import HTTPBasicAuth

from backend.app.llm.llm_client import LLMModel
from backend.app.minutes.llm_calls import llm_completion


async def llm_diff_summary(input_text, output_text):
    """Use LLM to generate a summary of the differences between two texts."""
    prompt = [
        {
            "role": "system",
            "content": "You are a helpful assistant that identifies and summarizes differences between two versions of text.",
        },
        {
            "role": "user",
            "content": f"I have two versions of a text. Please identify and summarize the key differences between them in a concise, bullet-point format. Focus only on meaningful changes (ignore minor formatting or spacing differences or newline differences).\n\nORIGINAL TEXT:\n{input_text}\n\nMODIFIED TEXT:\n{output_text}",
        },
    ]

    completion = await llm_completion(
        temperature=0.3,
        messages=prompt,
        model=LLMModel.VERTEX_GEMINI_25_FLASH,
    )

    return completion.choices[0].message.content


async def main():
    print("Starting process...")

    response = requests.get(
        "https://cloud.langfuse.com/api/public/observations",
        params={
            "name": "user-edit",
            # "traceId": "b8981fa9-0e01-466d-8899-d14964c81ff3",
        },  # filter by event name
        auth=HTTPBasicAuth(
            os.environ["LANGFUSE_PUBLIC_KEY"],
            os.environ["LANGFUSE_SECRET_KEY"],
        ),
    )
    data = response.json()

    print(f"Processing {len(data['data'])} observations...")

    # Process each observation and add LLM summary
    for i, obs in enumerate(data["data"]):
        input_text = obs["input"]
        output_text = obs["output"]

        print(f"Processing observation {i+1}/{len(data['data'])}...")

        summary = await llm_diff_summary(input_text, output_text)

        # Add the LLM summary to the observation
        obs["llm_diff_summary"] = summary

        print(f"Completed observation {i+1}")

    # Save enhanced data to JSON file
    with open("evaluation/llm/.outputs/user-edit-raw-data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nFinished processing {len(data['data'])} observations.")
    print(
        "Enhanced data with LLM summaries saved to evaluation/llm/.outputs/user-edit-raw-data.json"
    )


if __name__ == "__main__":
    asyncio.run(main())
