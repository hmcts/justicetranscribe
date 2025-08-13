# ruff: noqa
from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from backend.app.llm.llm_client import (
    LLMModel,
    structured_output_llm_completion_builder_func,
)
from backend.app.minutes.scripts.evals.eval_class import EvalConfig, Evaluator


class DialogueEntry(BaseModel):
    speaker: str
    text: str


class HallucinationCheck(BaseModel):
    hallucinated: bool
    reasoning: str | None = None


class HallucinationEvaluator(Evaluator[list[DialogueEntry], str, HallucinationCheck]):
    def __init__(
        self,
        config: EvalConfig,
        prompt_names: list[str],
        judge_prompt_template: str,
        generate_output_func: Callable,
    ):
        super().__init__(config, prompt_names)
        self.judge_prompt_template = judge_prompt_template
        self.generate_output_func = generate_output_func
        self.judge_completion = structured_output_llm_completion_builder_func(
            HallucinationCheck
        )

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
    ) -> HallucinationCheck:
        prompt = self.langfuse.get_prompt(
            prompt_name, version=prompt_version, type="chat"
        )

        compiled_chat_prompt = prompt.compile(
            meeting_transcript=dialogue_entries,
            date=datetime.now(tz=ZoneInfo("Europe/London")).strftime("%d %B %Y"),
        )

        system_prompt = next(
            (msg["content"] for msg in compiled_chat_prompt if msg["role"] == "system"),
            "System prompt not found",
        )

        transcript_str = "\n".join(f"{e.speaker}: {e.text}" for e in dialogue_entries)

        judge_prompt = self.judge_prompt_template.format(
            system_prompt=system_prompt,
            transcript=transcript_str,
            output=output,
            today=datetime.now(ZoneInfo("Europe/London")).strftime("%Y-%m-%d"),
        )

        judge_messages = [
            {"role": "system", "content": "You are a hallucination detection expert."},
            {"role": "user", "content": judge_prompt},
        ]

        return await self.judge_completion(
            model=self.config.judge_model,
            messages=judge_messages,
            max_retries=100,
        )

    def score_judgement(self, judgement: HallucinationCheck, trace_id: str) -> None:
        self.langfuse.score(
            trace_id=trace_id,
            name="hallucination",
            value=judgement.hallucinated,
            comment=f"Reason: {judgement.reasoning}",
        )

    def prepare_input(self, item: Any) -> list[DialogueEntry]:
        """Convert the dataset item into a list of DialogueEntry objects"""
        return [DialogueEntry(**entry) for entry in item.input]
