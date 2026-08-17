import json

from google.genai import errors

from ai.gemini_client import client

from models.lesson_mapper import (
    LessonMapper
)

from ai.prompts import (
    VOCABULARY_PROMPT
)

from config import (
    GEMINI_CONTENT_MODEL,
    GEMINI_FALLBACK_MODEL
)


# =================================================
# BUILD VOCABULARY PROMPT
# =================================================

def build_vocabulary_prompt(
    topic,
    count,
    suggestions=""
):

    prompt = VOCABULARY_PROMPT.format(
        topic=topic,
        count=count,
        suggestions=suggestions
    )

    return prompt


# =================================================
# GENERATE VOCABULARY
# =================================================

def generate_vocabulary(
    topic,
    count,
    suggestions=""
):

    prompt = build_vocabulary_prompt(
        topic=topic,
        count=count,
        suggestions=suggestions
    )

    try:

        print(
            f"Gemini model: "
            f"{GEMINI_CONTENT_MODEL}"
        )

        response = (
            client.models.generate_content(
                model=GEMINI_CONTENT_MODEL,
                contents=prompt
            )
        )

    except errors.ServerError as error:

        if error.code != 503:
            raise

        print(
            f"{GEMINI_CONTENT_MODEL} "
            "is temporarily unavailable."
        )

        print(
            f"Trying fallback model: "
            f"{GEMINI_FALLBACK_MODEL}"
        )

        response = (
            client.models.generate_content(
                model=GEMINI_FALLBACK_MODEL,
                contents=prompt
            )
        )

    text = response.text.strip()

    data = json.loads(
        text
    )

    lesson = (
        LessonMapper.from_dict(
            data
        )
    )

    return lesson