# ruff: noqa
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar
from zoneinfo import ZoneInfo

from langfuse import Langfuse
from pydantic import BaseModel

from backend.app.llm.llm_client import (
    ALL_LLM_MODELS,
    LLMModel,
)

# Type variables for generic types
InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")
JudgementType = TypeVar("JudgementType")


class DialogueEntry(BaseModel):
    speaker: str
    text: str


@dataclass
class EvalConfig:
    """Configuration for evaluation run"""

    dataset_name: str
    experiment_name: str
    judge_model: LLMModel
    concurrency_limit: int = 1

    def __post_init__(self):
        self.semaphore = asyncio.Semaphore(self.concurrency_limit)


class EvaluationResult(BaseModel):
    """Generic evaluation result"""

    score: float
    metadata: dict[str, Any]
    reasoning: str | None = None


class Evaluator(ABC, Generic[InputType, OutputType, JudgementType]):
    """Abstract base class for evaluators"""

    def __init__(self, config: EvalConfig, prompt_names: list[str]):
        self.config = config
        self.langfuse = Langfuse()
        self.prompt_names: list[str] = prompt_names

    @abstractmethod
    async def generate_output(
        self,
        input_data: InputType,
        model: LLMModel,
        prompt_name: str,
        prompt_version: str,
    ) -> OutputType:
        """Generate output for given input using specified model and prompt"""

    @abstractmethod
    async def evaluate_output(
        self,
        input_data: InputType,
        output: OutputType,
        model: LLMModel,
        prompt_name: str,
        prompt_version: str,
    ) -> JudgementType:
        """Evaluate the output against input"""

    @abstractmethod
    def score_judgement(self, judgement: JudgementType, trace_id: str) -> None:
        """Score the judgement in Langfuse"""

    @abstractmethod
    def prepare_input(self, item: Any) -> InputType:
        """Transform the raw dataset item into the expected input type"""

    async def evaluate_item(
        self,
        item: Any,
        model: LLMModel,
        prompt_name: str,
        prompt_version: str,
        run_name: str,
    ) -> None:
        """Evaluate a single item"""
        async with self.config.semaphore:
            print(f"Evaluating item {item}")

            with item.observe(run_name=run_name) as trace_id:
                input_data = self.prepare_input(item)
                output = await self.generate_output(
                    input_data, model, prompt_name, prompt_version
                )
                judgement = await self.evaluate_output(
                    input_data, output, model, prompt_name, prompt_version
                )
                self.score_judgement(judgement, trace_id)

    async def run_evaluation(self) -> None:
        """Run evaluation on entire dataset"""
        dataset = self.langfuse.get_dataset(self.config.dataset_name)
        timestamp = datetime.now(ZoneInfo("Europe/London")).strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        tasks = []
        for model in ALL_LLM_MODELS:
            for prompt_name in self.prompt_names:
                prompt_versions = self.get_prompt_versions(prompt_name)
                for prompt_version in prompt_versions:
                    run_name = f"{model}-{prompt_name}-v{prompt_version}-{timestamp}"
                    model_prompt_tasks = [
                        self.evaluate_item(
                            item,
                            model,
                            prompt_name,
                            prompt_version,
                            run_name,
                        )
                        for item in dataset.items
                    ]
                tasks.extend(model_prompt_tasks)

        await asyncio.gather(*tasks)

        self.flush_results()

    def get_prompt_versions(self, prompt_name: str) -> list[str]:
        """Get available prompt versions"""
        prompts_response = self.langfuse.client.prompts.list(
            name=prompt_name,
        )
        if prompts_response.data:
            return prompts_response.data[0].versions
        return []

    def flush_results(self) -> None:
        """Flush results to Langfuse"""
        from langfuse.decorators import langfuse_context

        langfuse_context.flush()
        self.langfuse.flush()
