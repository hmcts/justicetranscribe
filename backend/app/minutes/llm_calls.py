# flake8: noqa: E501

from uuid import UUID, uuid4

import sentry_sdk
from fastapi import HTTPException
from langfuse.decorators import langfuse_context, observe
from uwotm8 import convert_american_to_british_spelling

from app.database.interface_functions import (
    create_error_minute_version,
    get_minute_version_by_id,
    save_minute_version,
)
from app.database.postgres_models import (
    DialogueEntry,
    MinuteVersion,
    TemplateMetadata,
    TemplateName,
)
from app.llm.llm_client import (
    LLMModel,
    langfuse_client,
    llm_completion,
    structured_output_llm_completion_builder_func,
)
from app.minutes.templates.crissa import generate_full_crissa
from app.minutes.templates.general_style import generate_general_style_summary
from app.minutes.templates.utils import format_transcript_string_for_prompt
from app.minutes.types import (
    MeetingTitleOutput,
    SpeakerPredictionOutput,
)
from utils.markdown import html_to_markdown, markdown_to_html


@observe(name="edit_minutes_with_ai", as_type="generation")
async def edit_minutes_with_ai(
    current_minute_version: MinuteVersion,
    edit_instructions: str,
    transcript: list[DialogueEntry],
    user_email: str,
    **kwargs,  # noqa: ARG001
) -> str:
    current_markdown_minutes = html_to_markdown(current_minute_version.html_content)
    langfuse_context.update_current_trace(
        user_id=user_email,
    )
    prompt = langfuse_client.get_prompt("ai-edit-prompt", type="chat")
    langfuse_context.update_current_observation(
        prompt=prompt,
    )

    transcript_string = format_transcript_string_for_prompt(transcript, include_index=False)
    compiled_chat_prompt = prompt.compile(
        meeting_transcript=transcript_string,
        meeting_summary=current_markdown_minutes,
        user_instructions=edit_instructions,
    )

    initial_completion = await llm_completion(
        temperature=0.1,
        messages=compiled_chat_prompt,
        model=LLMModel.VERTEX_GEMINI_25_FLASH,
    )
    british_minutes = convert_american_to_british_spelling(initial_completion.choices[0].message.content)
    html_minutes = markdown_to_html(british_minutes)

    return html_minutes


@observe(name="generate_meeting_title", as_type="generation")
async def generate_meeting_title(
    transcript: list[DialogueEntry],
    user_email: str,
) -> str:
    langfuse_context.update_current_trace(
        user_id=user_email,
    )
    prompt = langfuse_client.get_prompt("generate-meeting-title-prompt", type="chat")
    langfuse_context.update_current_observation(
        prompt=prompt,
    )
    transcript_string = format_transcript_string_for_prompt(transcript, include_index=False)
    compiled_chat_prompt = prompt.compile(meeting_transcript=transcript_string)

    meeting_title_completion_func = structured_output_llm_completion_builder_func(MeetingTitleOutput)
    completion = await meeting_title_completion_func(
        messages=compiled_chat_prompt,
        temperature=0.1,
        model=LLMModel.VERTEX_GEMINI_25_FLASH,
    )

    if not completion or not completion.title:
        raise HTTPException(status_code=500, detail="No title generated")

    return completion.title.strip()


@observe(name="generate_speaker_predictions", as_type="generation")
async def generate_speaker_predictions(dialogue_entries: list, user_email: str) -> dict:
    langfuse_context.update_current_trace(
        user_id=user_email,
    )
    prompt = langfuse_client.get_prompt("predict-speaker-names", type="chat")
    langfuse_context.update_current_observation(
        prompt=prompt,
    )
    # Prepare the conversation context
    conversation_context = "\n".join([f"{entry.speaker}: {entry.text}" for entry in dialogue_entries])

    compiled_chat_prompt = prompt.compile(meeting_transcript=conversation_context)
    speaker_prediction_completion_func = structured_output_llm_completion_builder_func(SpeakerPredictionOutput)
    completion = await speaker_prediction_completion_func(
        messages=compiled_chat_prompt,
        temperature=0.1,
        model=LLMModel.VERTEX_GEMINI_25_FLASH,
    )

    predictions = completion

    if not predictions:
        raise HTTPException(status_code=500, detail="No predictions found")

    return {pred.original_speaker: pred.predicted_name for pred in predictions.predictions}


@observe(name="generate_summary_task", as_type="generation")
async def generate_llm_output_task(
    dialogue_entries: list[DialogueEntry],
    transcription_id: UUID,
    template: TemplateMetadata,
    user_email: str,
    minute_version_id: UUID | None = None,
) -> str:
    # Start a Sentry transaction for the whole function
    with sentry_sdk.start_transaction(op="task", name="Generate LLM Output Task") as transaction:  # noqa: F841
        # Ensure we have a consistent ID through the whole process
        if minute_version_id is None:
            minute_version_id = uuid4()  # Generate a UUID if none provided

        # save initial version with is_generating=True
        initial_minute_version = MinuteVersion(
            id=minute_version_id,
            transcription_id=transcription_id,
            html_content="",
            template=template,
            trace_id=langfuse_context.get_current_trace_id(),
            is_generating=True,
        )
        save_minute_version(initial_minute_version)

        try:
            # Generate content based on template
            if template.name == TemplateName.GENERAL:
                llm_output = await generate_general_style_summary(dialogue_entries, user_email)
            elif template.name == TemplateName.CRISSA:
                llm_output = await generate_full_crissa(dialogue_entries, user_email)
            else:
                msg = "Invalid template parameter"
                raise ValueError(msg)

            # Update the existing minute_version instead of creating a new one
            initial_minute_version.html_content = llm_output
            initial_minute_version.is_generating = False
            save_minute_version(initial_minute_version)

            return llm_output  # noqa: TRY300

        except Exception as e:
            # Save error state
            error_minute_version = create_error_minute_version(
                minute_version_id,
                transcription_id,
                e,
                template=template,
                trace_id=langfuse_context.get_current_trace_id(),
            )
            save_minute_version(error_minute_version)
            raise


async def ai_edit_task(
    dialogue_entries: list[DialogueEntry],
    current_minute_version_id: UUID,
    new_minute_version_id: UUID,
    edit_instructions: str,
    transcription_id: UUID,
    user_email: str,
) -> str:
    with sentry_sdk.start_transaction(op="task", name="AI Edit Task") as transaction:  # noqa: F841
        # if length of dialogue entries is 0, return empty string
        if len(dialogue_entries) == 0:
            raise HTTPException(status_code=400, detail="No dialogue entries found")

        current_minutes = get_minute_version_by_id(current_minute_version_id, transcription_id)

        new_minute_version = MinuteVersion(
            id=new_minute_version_id,
            transcription_id=transcription_id,
            html_content="",
            template=current_minutes.template,
            trace_id=current_minutes.trace_id,
            is_generating=True,
        )
        save_minute_version(new_minute_version)
        try:
            llm_output = await edit_minutes_with_ai(
                current_minutes,
                edit_instructions,
                dialogue_entries,
                user_email,
                langfuse_parent_trace_id=current_minutes.trace_id,
            )

            new_minute_version.html_content = llm_output
            new_minute_version.is_generating = False
            save_minute_version(new_minute_version)

            return llm_output  # noqa: TRY300

        except Exception as e:
            # Pass template from current_minutes to create valid error state
            error_minute_version = create_error_minute_version(
                new_minute_version_id,
                transcription_id,
                e,
                template=current_minutes.template
                if isinstance(current_minutes.template, dict)
                else current_minutes.template.model_dump(),
            )
            save_minute_version(error_minute_version)
            raise
