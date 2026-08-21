import json

from ai.gemini_verification_client import (
    GeminiVerificationClient
)
from ai.metadata_prompts import YOUTUBE_METADATA_PROMPT
from config import (
    YOUTUBE_METADATA_MODEL,
    YOUTUBE_METADATA_FALLBACK_MODEL
)


class MetadataTemporarilyUnavailableError(RuntimeError):
    pass


def generate_youtube_metadata(
    topic,
    lesson
):

    # -----------------------------------------
    # Prepare vocabulary information
    # -----------------------------------------

    word_lines = []

    for word in lesson.words:

        word_lines.append(
            f"- {word.word}: {word.meaning}"
        )

    words_text = "\n".join(
        word_lines
    )

    # -----------------------------------------
    # Build prompt
    # -----------------------------------------

    prompt = YOUTUBE_METADATA_PROMPT.format(
        topic=topic,
        words=words_text
    )

    # -----------------------------------------
    # Gemini
    # -----------------------------------------

    result = GeminiVerificationClient().generate(
        contents=prompt,
        primary_model=YOUTUBE_METADATA_MODEL,
        fallback_model=YOUTUBE_METADATA_FALLBACK_MODEL,
        task_name="YouTube metadata",
        service_unavailable_retry_delay=1.0
    )

    if result["status"] != "completed":
        raise MetadataTemporarilyUnavailableError(
            "YouTube metadata generation is temporarily "
            "unavailable because all configured Gemini models "
            "are unavailable. Please rerun Stage 5 later."
        )

    print(
        "YouTube metadata generated with model: "
        f"{result['model_used']}"
    )

    text = result["text"].strip()

    # -----------------------------------------
    # Remove possible Markdown JSON fences
    # -----------------------------------------

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # -----------------------------------------
    # Convert JSON
    # -----------------------------------------

    metadata = json.loads(text)

    return metadata
