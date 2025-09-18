# ruff: noqa: TRY300, B904, TRY003
import json
from collections.abc import Callable
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Any

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from litellm import acompletion
from pydantic import BaseModel

from utils.settings import get_settings


class LLMModel(str, Enum):
    AZURE_GPT_4O = "azure/gpt-4o-2024-08-06"
    AZURE_GROK_3 = "azure/grok-3"
    VERTEX_GEMINI_25_PRO = "vertex_ai/gemini-2.5-pro"
    VERTEX_GEMINI_20_FLASH = "vertex_ai/gemini-2.0-flash"
    VERTEX_GEMINI_25_FLASH = "vertex_ai/gemini-2.5-flash"


ALL_LLM_MODELS = [
    LLMModel.AZURE_GPT_4O,
    LLMModel.AZURE_GROK_3,
    LLMModel.VERTEX_GEMINI_25_PRO,
    LLMModel.VERTEX_GEMINI_20_FLASH,
    LLMModel.VERTEX_GEMINI_25_FLASH,
]
# Create langfuse client with settings
_settings = get_settings()
langfuse_client = Langfuse(
    public_key=_settings.LANGFUSE_PUBLIC_KEY,
    secret_key=_settings.LANGFUSE_SECRET_KEY,
    host=_settings.LANGFUSE_HOST,
    environment=_settings.ENVIRONMENT,
)

langfuse_context.configure(environment=_settings.ENVIRONMENT)


class LangfuseAuthManager:
    """Manages Langfuse authentication state and lazy initialization."""

    def __init__(self):
        self._authenticated = False

    def ensure_authenticated(self):
        """
        Ensure Langfuse client is authenticated.

        This is called lazily on first use rather than at import time
        to avoid authentication failures during test collection.
        """
        if not self._authenticated:
            auth_result = langfuse_client.auth_check()
            if not auth_result:
                raise RuntimeError(
                    f"Langfuse authentication failed for host: {get_settings().LANGFUSE_HOST}. "
                    f"Please verify your LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are correct."
                )
            self._authenticated = True


# Create singleton instance
_auth_manager = LangfuseAuthManager()


def _ensure_langfuse_authenticated():
    """Convenience function to ensure Langfuse authentication."""
    _auth_manager.ensure_authenticated()


def _load_vertex_credentials() -> str:
    """
    Load the Google Cloud credentials by:
    1. First attempting to read from config/justice-transcribe-d4aeca0459de.json
    2. Falling back to environment variable if file doesn't exist
    Returns the credentials as a JSON string.
    """
    import pathlib

    # First try to load from file
    credentials_path = pathlib.Path("config/justice-transcribe-d4aeca0459de.json")
    if credentials_path.exists():
        try:
            with Path(credentials_path).open("r") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read credentials file at {credentials_path}. Error: {e!s}")

    # Fall back to environment variable
    try:
        vertex_credentials = get_settings().GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT
        return vertex_credentials
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Google Cloud credentials from environment variable. Error: {e!s}")


# Create a pre-configured version of acompletion with Azure Grok defaults
def _get_azure_grok_acompletion():
    settings = get_settings()
    return partial(
        acompletion,
        api_base=settings.AZURE_GROK_ENDPOINT,
        api_version="2024-05-01-preview",
        api_key=settings.AZURE_GROK_API_KEY,
        num_retries=25,
    )

azure_grok_acompletion = _get_azure_grok_acompletion()


# Create a pre-configured version of acompletion with Azure defaults
def _get_azure_acompletion():
    settings = get_settings()
    return partial(
        acompletion,
        api_base=settings.AZURE_OPENAI_ENDPOINT,
        api_version="2025-03-01-preview",
        api_key=settings.AZURE_OPENAI_API_KEY,
        num_retries=25,
    )

azure_acompletion = _get_azure_acompletion()

# Create a pre-configured version of completion with Vertex AI defaults
gemini_completion = partial(
    acompletion,
    vertex_credentials=_load_vertex_credentials(),
    max_retries=25,
    fallbacks=[LLMModel.VERTEX_GEMINI_25_FLASH, LLMModel.VERTEX_GEMINI_20_FLASH],
    safety_settings=[
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ],
)


def _is_content_filtering_error(error: Exception) -> bool:
    """
    Detect if an error is specifically a CSAM content filtering error from Gemini.
    """
    error_str = str(error).lower()

    # CSAM-specific content filtering error patterns from Gemini/Vertex AI
    csam_filtering_indicators = [
        "harm_category_sexually_explicit",
        "sexually_explicit",
        "child safety",
        "child exploitation",
        "sexual content involving minors",
        "underage",
        "minor safety",
        "csam",
        "child sexual abuse",
        "child abuse material",
    ]

    return any(indicator in error_str for indicator in csam_filtering_indicators)


async def _gemini_completion_with_multi_fallback(*, model: str, messages: list, **kwargs):
    """
    Gemini completion with automatic multi-level fallbacks:
    1. Try Gemini first
    2. On CSAM content filtering errors, fallback to Azure Grok
    3. If Grok also fails, fallback to Azure OpenAI GPT-4o
    This handles cases where Gemini blocks legitimate legal/judicial content mentioning CSAM.
    """
    try:
        # Try Gemini first
        result = await gemini_completion(model=model, messages=messages, **kwargs)
        # Update observation to track successful Gemini usage
        langfuse_context.update_current_observation(
            metadata={
                "actual_model_used": model,
                "fallback_triggered": False,
                "fallback_reason": None,
            }
        )
        if not result.choices or result.choices[0].message.content is None or result.choices[0].message.content == "":
            print("GEMINI RETURNED NO CONTENT")  # noqa: T201
            raise Exception("Gemini returned no content")  # noqa: EM101, TRY002
        return result
    except Exception as e:
        if _is_content_filtering_error(e) or "Gemini returned no content" in str(e):
            try:
                # Fall back to Azure Grok
                print("FALLING BACK TO GROK")  # noqa: T201
                result = await azure_grok_acompletion(model=LLMModel.AZURE_GROK_3, messages=messages, **kwargs)
                # Update observation to track Grok fallback usage
                langfuse_context.update_current_observation(
                    metadata={
                        "requested_model": model,
                        "actual_model_used": LLMModel.AZURE_GROK_3,
                        "fallback_triggered": True,
                        "fallback_reason": "gemini_content_filtering",
                        "original_error": str(e),
                    }
                )
                return result
            except Exception as grok_error:
                # If Grok also fails, fall back to Azure OpenAI GPT-4o as final fallback
                result = await azure_acompletion(model=LLMModel.AZURE_GPT_4O, messages=messages, **kwargs)
                # Update observation to track final fallback usage
                langfuse_context.update_current_observation(
                    metadata={
                        "requested_model": model,
                        "actual_model_used": LLMModel.AZURE_GPT_4O,
                        "fallback_triggered": True,
                        "fallback_reason": "gemini_content_filtering_and_grok_failure",
                        "original_error": str(e),
                        "grok_error": str(grok_error),
                    }
                )
                return result
        # If it's not a CSAM content filtering error, raise the original error
        raise


def with_structured_output(completion_func: Callable) -> Callable:
    """
    Wraps a completion function to handle structured output using Pydantic models.
    Works with any completion function that returns a standard completion response.
    Retries up to 5 times if JSON validation fails by requesting a new completion.
    """

    async def wrapped(messages: list, response_format: type[BaseModel] | None = None, **kwargs: Any):
        max_attempts = 5
        attempt = 0

        while attempt < max_attempts:
            try:
                response = await completion_func(messages=messages, response_format=response_format, **kwargs)
                content = response.choices[0].message.content

                if response_format:
                    return response_format.model_validate_json(content)
                return content
            except (json.JSONDecodeError, ValueError):
                attempt += 1
                if attempt == max_attempts:
                    raise  # Re-raise the last exception if we've exhausted all attempts
                continue

        return None  # Add explicit return at the end of the while loop

    return wrapped


structured_azure_completion = with_structured_output(azure_acompletion)
structured_gemini_completion = with_structured_output(_gemini_completion_with_multi_fallback)
structured_azure_grok_completion = with_structured_output(azure_grok_acompletion)


def get_backend_for_model(model: str) -> str:
    if model == LLMModel.AZURE_GROK_3:
        return "azure_grok"
    elif model.startswith("azure"):
        return "azure"
    elif model.startswith("vertex_ai"):
        return "vertex"
    else:
        raise ValueError(f"Unknown model prefix for model: {model}")


@observe(name="llm_completion", as_type="generation")
async def llm_completion(*, model: str, messages: list, **kwargs):
    # Ensure Langfuse is authenticated before any LLM operations
    _ensure_langfuse_authenticated()

    backend = get_backend_for_model(model)

    if backend == "azure":
        result = await azure_acompletion(model=model, messages=messages, **kwargs)
    elif backend == "azure_grok":
        result = await azure_grok_acompletion(model=model, messages=messages, **kwargs)
    elif backend == "vertex":
        result = await _gemini_completion_with_multi_fallback(model=model, messages=messages, **kwargs)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    return result


def structured_output_llm_completion_builder_func(response_format):
    async def wrapped(*, model: str, messages: list, **kwargs):
        # Ensure Langfuse is authenticated before any LLM operations
        _ensure_langfuse_authenticated()

        backend = get_backend_for_model(model)
        if backend == "azure":
            return await structured_azure_completion(
                messages=messages,
                response_format=response_format,
                model=model,
                **kwargs,
            )
        elif backend == "azure_grok":
            return await structured_azure_grok_completion(
                messages=messages,
                response_format=response_format,
                model=model,
                **kwargs,
            )
        elif backend == "vertex":
            return await structured_gemini_completion(
                messages=messages,
                response_format=response_format,
                model=model,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    return wrapped
