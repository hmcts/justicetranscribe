# ruff: noqa
import argparse
import asyncio
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from langfuse import Langfuse
from pydantic import BaseModel

from backend.app.llm.llm_client import (
    LLMModel,
)
from backend.app.minutes.templates.crissa import generate_full_crissa
from backend.app.minutes.templates.general_style import generate_general_style_summary
from backend.utils.markdown import html_to_markdown

# Langfuse client
langfuse = Langfuse()
DATASET_NAME = "short-transcript-hallucination-check-v2"
CONCURRENCY_LIMIT = 8  # Adjust this number based on your rate limit

semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)


class DialogueEntry(BaseModel):
    speaker: str
    text: str


async def evaluate_item_general(item, model, prompt_version, timestamp):
    async with semaphore:
        dialogue_entries = [DialogueEntry(**entry) for entry in item.input]
        user_email = "eval@system"
        prompt_version_str = (
            f"{prompt_version}" if prompt_version is not None else "production"
        )
        run_name = f"general-{model}-prompt-v{prompt_version_str}-{timestamp}"
        with item.observe(run_name=run_name) as trace_id:
            output = await generate_general_style_summary(
                dialogue_entries=dialogue_entries,
                user_email=user_email,
                model_name=model,
                prompt_version=prompt_version,
            )
            markdown_output = remove_citations(html_to_markdown(output))
            length_in_characters = len(markdown_output)
            langfuse.score(
                trace_id=trace_id,
                name="generated_summary",
                value=length_in_characters,
                comment=f"Model: {model} | Prompt Version: {prompt_version_str} | Output: {output}",
            )
            print(f"[GENERAL] Model: {model} | Prompt Version: {prompt_version_str}")


def remove_citations(text):
    # This regex matches one or more occurrences of [number] (e.g., [4], [6][10])
    return re.sub(r"(\[\d+\])+", "", text)


async def evaluate_item_crissa(item, model, prompt_version, timestamp):
    async with semaphore:
        dialogue_entries = [DialogueEntry(**entry) for entry in item.input]
        user_email = "eval@system"
        prompt_version_str = (
            f"{prompt_version}" if prompt_version is not None else "production"
        )
        run_name = f"crissa-{model}-prompt-v{prompt_version_str}-{timestamp}"
        with item.observe(run_name=run_name) as trace_id:
            output = await generate_full_crissa(
                dialogue_entries=dialogue_entries,
                user_email=user_email,
                model_name=model,
                prompt_version=prompt_version,
            )

            markdown_output = remove_citations(html_to_markdown(output))
            length_in_characters = len(markdown_output)
            langfuse.score(
                trace_id=trace_id,
                name="generated_crissa",
                value=length_in_characters,
                comment=f"Model: {model} | Prompt Version: {prompt_version_str} | Output: {output}",
            )


async def main():
    parser = argparse.ArgumentParser(
        description="Sense check generation for templates."
    )
    parser.add_argument(
        "--template",
        choices=["general", "crissa", "both"],
        default="crissa",
        help="Which template(s) to run: general, crissa, or both.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="short-transcript-hallucination-check-v2",
        help="Name of the dataset to use.",
    )
    args = parser.parse_args()

    dataset = langfuse.get_dataset(args.dataset)
    timestamp = datetime.now(ZoneInfo("Europe/London")).strftime("%Y-%m-%d_%H-%M-%S")

    tasks = []
    for item in dataset.items:
        for model in [LLMModel.VERTEX_GEMINI_25_PRO]:
            if args.template in ("general", "both"):
                tasks.append(evaluate_item_general(item, model, None, timestamp))
            if args.template in ("crissa", "both"):
                tasks.append(evaluate_item_crissa(item, model, None, timestamp))

    await asyncio.gather(*tasks)

    from langfuse.decorators import langfuse_context

    langfuse_context.flush()
    langfuse.flush()


if __name__ == "__main__":
    asyncio.run(main())
