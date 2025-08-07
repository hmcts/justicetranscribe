# ruff: noqa

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from backend.app.llm.llm_client import LLMModel
from backend.app.minutes.scripts.evals.eval_class import EvalConfig, Evaluator


class DialogueEntry(BaseModel):
    speaker: str
    text: str


class GenerationOnlyEvaluator(Evaluator[list[DialogueEntry], str, None]):
    def __init__(
        self,
        config: EvalConfig,
        prompt_names: list[str],
        generate_output_func: Callable,
    ):
        super().__init__(config, prompt_names)
        self.generate_output_func = generate_output_func

    async def generate_output(
        self,
        dialogue_entries: list[DialogueEntry],
        model: LLMModel,
        prompt_name: str,
        prompt_version: str,
    ) -> str:
        return await self.generate_output_func(
            dialogue_entries=dialogue_entries,
            user_email="eval@system",
            model_name=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
        )

    async def evaluate_output(
        self,
        dialogue_entries: list[DialogueEntry],
        output: str,
        model: LLMModel,
        prompt_name: str,
        prompt_version: str,
    ) -> None:
        # No evaluation needed, return None
        return None

    def score_judgement(self, judgement: None, trace_id: str) -> None:
        # No scoring needed
        pass

    def prepare_input(self, item: Any) -> list[DialogueEntry]:
        """Convert the dataset item into a list of DialogueEntry objects"""
        return [DialogueEntry(**entry) for entry in item.input]
