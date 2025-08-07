# ruff: noqa
import json
from pathlib import Path
from pydantic import BaseModel

from backend.app.llm.llm_client import (
    gemini_completion,
    structured_gemini_completion,
)


class DialogueEntry(BaseModel):
    speaker: str
    text: str


class MeetingTranscript(BaseModel):
    entries: list[DialogueEntry]


async def generate_structured_meeting(model: str) -> list[DialogueEntry]:
    """Method 1: Direct structured generation"""
    system_context = {
        "role": "system",
        "content": """You are an expert in UK probation services with extensive experience in supervision meetings. 
Generate a detailed, realistic probation supervision meeting transcript that demonstrates:
- Proper professional boundaries
- Evidence-based supervision techniques
- Risk assessment and management
- Rehabilitation-focused dialogue
- Appropriate documentation style used in UK probation services
- Adequate length. Please don't generate a transcript that is too short.

IMPORTANT: Format your response as a JSON object with an "entries" field containing an array of dialogue entries, where each entry has a "speaker" and "text" field.""",
    }

    meeting_parameters = {
        "role": "user",
        "content": """Generate a detailed probation supervision meeting transcript between a Probation Officer and an offender in the UK.

Required meeting elements:
1. Standard opening procedures and identity verification
2. Discussion of compliance with probation conditions
3. Assessment of current risk factors and protective factors
4. Progress on rehabilitation goals
5. Discussion of employment/housing/substance use if relevant
6. Action planning for next steps
7. Setting next appointment

Additional context:
- Meeting duration: 45 minutes
- Type of offense: Choose a realistic offense category
- Stage: 3 months into probation order
- Include realistic challenges and progress indicators
- Use authentic UK probation terminology and procedures

Format the response as a JSON object with an "entries" array containing dialogue objects with "speaker" and "text" fields.""",
    }

    try:
        transcript = await structured_gemini_completion(
            messages=[system_context, meeting_parameters],
            model=model,
            max_tokens=8000,
            response_format=MeetingTranscript,
        )
        return transcript.entries
    except Exception as e:
        print(f"Error generating structured meeting with {model}: {e!s}")
        return None


async def generate_and_convert_meeting(model: str) -> list[DialogueEntry]:
    """Method 2: Generate raw text first, then convert to structured format"""
    generation_context = {
        "role": "system",
        "content": """You are an expert in UK probation services with extensive experience in supervision meetings. 
Generate a detailed, realistic probation supervision meeting transcript that demonstrates:
- Proper professional boundaries
- Evidence-based supervision techniques
- Risk assessment and management
- Rehabilitation-focused dialogue
- Appropriate documentation style
- Adequate length

Format the transcript as a natural dialogue with clear speaker labels (e.g., "Probation Officer:" or "Client:").""",
    }

    generation_parameters = {
        "role": "user",
        "content": """Generate a detailed probation supervision meeting transcript between a Probation Officer and an offender in the UK.

Required meeting elements:
1. Standard opening procedures and identity verification
2. Discussion of compliance with probation conditions
3. Assessment of current risk factors and protective factors
4. Progress on rehabilitation goals
5. Discussion of employment/housing/substance use if relevant
6. Action planning for next steps
7. Setting next appointment

Additional context:
- Meeting duration: 45 minutes
- Type of offense: Choose a realistic offense category
- Stage: 3 months into probation order
- Include realistic challenges and progress indicators
- Use authentic UK probation terminology and procedures""",
    }

    try:
        raw_transcript = await gemini_completion(
            messages=[generation_context, generation_parameters],
            model=model,
            max_tokens=8000,
        )

        conversion_prompt = {
            "role": "system",
            "content": """Convert the following meeting transcript into a structured format. 
Output should be a JSON object with an "entries" field containing an array of dialogue entries.
Each entry should have "speaker" and "text" fields.""",
        }

        conversion_parameters = {
            "role": "user",
            "content": f"Convert this transcript to the specified JSON format:\n\n{raw_transcript.choices[0].message.content}",
        }

        structured_result = await structured_gemini_completion(
            messages=[conversion_prompt, conversion_parameters],
            model=model,
            max_tokens=8000,
            response_format=MeetingTranscript,
        )
        return structured_result.entries

    except Exception as e:
        print(f"Error in generate_and_convert_meeting with {model}: {e!s}")
        return None


async def generate_transcript(model: str, method: str) -> list[DialogueEntry]:
    """Generate a single transcript using specified model and method"""
    if method == "structured":
        return await generate_structured_meeting(model)
    elif method == "converted":
        return await generate_and_convert_meeting(model)
    else:
        raise ValueError(f"Unknown generation method: {method}")


def save_meeting_to_file(dialogue_entries: list[DialogueEntry], filename: str):
    """Save a meeting transcript to a JSON file"""
    with Path(filename).open("w", encoding="utf-8") as f:
        json.dump(
            [entry.model_dump() for entry in dialogue_entries],
            f,
            indent=2,
            ensure_ascii=False,
        )
