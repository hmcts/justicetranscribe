import asyncio

from backend.app.llm.llm_client import LLMModel
from backend.app.minutes.scripts.evals.eval_class import EvalConfig
from backend.app.minutes.scripts.evals.generation_only_evaluator import (
    GenerationOnlyEvaluator,
)
from backend.app.minutes.templates.general_style import generate_general_style_summary


async def main():
    # Configuration
    config = EvalConfig(
        dataset_name="Synthetic-transcripts-v1",
        experiment_name="generation-only-experiment",
        judge_model=LLMModel.VERTEX_GEMINI_25_FLASH,  # This won't be used but is required by EvalConfig
        concurrency_limit=1,
    )

    # Create evaluator
    evaluator = GenerationOnlyEvaluator(
        config=config,
        prompt_names=["general-style-template-prompt"],
        generate_output_func=generate_general_style_summary,
    )

    # Run evaluation
    await evaluator.run_evaluation()


if __name__ == "__main__":
    asyncio.run(main())
