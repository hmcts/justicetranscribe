import asyncio

from backend.app.llm.llm_client import LLMModel
from backend.app.minutes.scripts.evals.eval_class import (
    EvalConfig,
)
from backend.app.minutes.scripts.evals.hallucination_evaluator import (
    HallucinationEvaluator,
)
from backend.app.minutes.templates.general_style import generate_general_style_summary

JUDGE_PROMPT = """An LLM was asked to generate case notes given the transcript of a meeting. The LLM was given the following system prompt:

{system_prompt}

You are tasked with determining whether the LLM has hallucinated the case notes given the transcript and the instructions it was given.

Sometimes, if the transcript is very short, the LLM is prone to hallucinating case notes that aren't related to the transcript. Commonly, the giveaway is that the transcript is short and the output is much longer than the transcript.

Bear in mind that the summary may include today's date, which is {today} and it is not hallucination to include it.

Input:
Transcript: {transcript}
Output: {output}

Think step by step."""


async def main():
    # Configuration
    config = EvalConfig(
        dataset_name="short-transcript-hallucination-check-v2",
        experiment_name="general-style-hallucination-eval",
        judge_model=LLMModel.VERTEX_GEMINI_25_FLASH,
        concurrency_limit=1,
    )

    # Create evaluator
    evaluator = HallucinationEvaluator(
        config=config,
        prompt_names=["general-style-template-prompt"],
        judge_prompt_template=JUDGE_PROMPT,
        generate_output_func=generate_general_style_summary,
    )

    # Run evaluation
    await evaluator.run_evaluation()


if __name__ == "__main__":
    asyncio.run(main())
