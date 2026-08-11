import json

from ai.gemini_client import client
from ai.metadata_prompts import YOUTUBE_METADATA_PROMPT


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

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )

    text = response.text.strip()

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