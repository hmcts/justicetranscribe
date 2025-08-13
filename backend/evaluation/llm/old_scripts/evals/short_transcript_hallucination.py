# ruff: noqa: T201
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from langfuse import Langfuse
from pydantic import BaseModel

from backend.app.llm.llm_client import (
    ALL_LLM_MODELS,
    LLMModel,
    structured_output_llm_completion_builder_func,
)
from backend.app.minutes.templates.general_style import generate_general_style_summary

# Langfuse client
langfuse = Langfuse()
DATASET_NAME = "short-transcript-hallucination-check-v2"
EXPERIMENT_NAME = "general-style-hallucination-eval"
JUDGE_MODEL = LLMModel.VERTEX_GEMINI_25_FLASH

CONCURRENCY_LIMIT = 1  # Adjust this number based on your rate limit

semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)


class DialogueEntry(BaseModel):
    speaker: str
    text: str


# Pydantic model for hallucination check
class HallucinationCheck(BaseModel):
    hallucinated: bool
    reasoning: str | None = None


JUDGE_PROMPT = """An LLM was asked to generate case notes given the transcript of a meeting. The LLM was given the following system prompt:
{system_prompt}
You are tasked with determining whether the LLM has hallucinated the case notes given the transcript and the instructions it was given.
Sometimes, if the transcript is very short, the LLM is prone to hallucinating case notes that aren't related to the transcript. Commonly, the giveaway is that the transcript is short and the output is much longer than the transcript.
Bear in mind that the summary may include today's date, which is {today} and it is not hallucination to include it.
Input:
Transcript: {transcript}
Output: {output}
Think step by step."""

judge_completion = structured_output_llm_completion_builder_func(HallucinationCheck)


async def evaluate_item(item, model, prompt_version, timestamp):
    async with semaphore:
        dialogue_entries = [DialogueEntry(**entry) for entry in item.input]
        user_email = "eval@system"

        run_name = f"{model}-prompt-v{prompt_version}-{timestamp}"
        with item.observe(run_name=run_name) as trace_id:
            # Get the prompt content first
            prompt = langfuse.get_prompt(
                "general-style-template-prompt", version=prompt_version, type="chat"
            )

            # Compile the prompt to get the messages
            compiled_chat_prompt = prompt.compile(
                meeting_transcript=dialogue_entries,  # We just need this to get the system prompt
                date=datetime.now(tz=ZoneInfo("Europe/London")).strftime("%d %B %Y"),
            )

            # Extract the system prompt from the compiled messages
            system_prompt = next(
                (
                    msg["content"]
                    for msg in compiled_chat_prompt
                    if msg["role"] == "system"
                ),
                "System prompt not found",
            )

            # Run the general style summary function with the current model and prompt version
            output = await generate_general_style_summary(
                dialogue_entries=dialogue_entries,
                user_email=user_email,
                model_name=model,
                prompt_version=prompt_version,
            )

            # Prepare judge prompt
            transcript_str = "\n".join(
                f"{e['speaker']}: {e['text']}" for e in item.input
            )
            judge_prompt = JUDGE_PROMPT.format(
                system_prompt=system_prompt,
                transcript=transcript_str,
                output=output,
                today=datetime.now(ZoneInfo("Europe/London")).strftime("%Y-%m-%d"),
            )
            judge_messages = [
                {
                    "role": "system",
                    "content": "You are a hallucination detection expert.",
                },
                {"role": "user", "content": judge_prompt},
            ]

            # Run hallucination check
            judge_result = await judge_completion(
                model=JUDGE_MODEL,
                messages=judge_messages,
            )

            langfuse.score(
                trace_id=trace_id,
                name="hallucination",
                value=judge_result.hallucinated,
                comment=f"Model: {model} | Prompt Version: {prompt_version} | Reason: {judge_result.reasoning}",
            )

            print(
                f"Model: {model} | Prompt Version: {prompt_version} | "
                f"Summary hallucinated: {judge_result.hallucinated} | "
                f"Reason: {judge_result.reasoning}"
            )


async def main():
    dataset = langfuse.get_dataset(DATASET_NAME)
    timestamp = datetime.now(ZoneInfo("Europe/London")).strftime("%Y-%m-%d_%H-%M-%S")

    # Get available prompt versions
    lf_client = Langfuse()
    lf_api_wrapper = lf_client.client
    prompts_response = lf_api_wrapper.prompts.list(
        name="general-style-template-prompt",
    )

    # Extract prompt versions from the response
    prompt_versions = []
    if prompts_response.data:
        prompt_versions = prompts_response.data[0].versions

    # Run all evaluations in parallel for all model-prompt combinations
    tasks = [
        evaluate_item(item, model, prompt_version, timestamp)
        for item in dataset.items
        for model in ALL_LLM_MODELS
        for prompt_version in prompt_versions
    ]
    await asyncio.gather(*tasks)

    # Flush events to Langfuse
    from langfuse.decorators import langfuse_context

    langfuse_context.flush()
    langfuse.flush()


if __name__ == "__main__":
    asyncio.run(main())
