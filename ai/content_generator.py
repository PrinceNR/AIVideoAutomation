from google.genai import errors, types

from ai.gemini_client import client
from ai.prompts import VOCABULARY_PROMPT
from config import (
    CONTENT_GENERATION_VERBOSE_LOGGING,
    GEMINI_CONTENT_MODEL,
    GEMINI_FALLBACK_MODEL,
)
from models.lesson_mapper import LessonMapper
from utils.AIResponseCleaner import (
    AIResponseCleaner,
    AIResponseParseError,
)


class LessonGenerationError(RuntimeError):
    """Raised when bounded lesson generation cannot return valid data."""


class LessonStructureError(ValueError):
    """Raised when parsed JSON is not a complete vocabulary lesson."""


REQUIRED_WORD_FIELDS = {
    "word",
    "meaning",
    "pronunciation",
    "part_of_speech",
    "difficulty",
    "translations",
    "present_sentence",
    "past_sentence",
    "future_sentence",
    "base_form",
    "present_form",
    "past_form",
    "synonyms",
    "antonyms",
    "image_keywords",
    "search_query",
}

STRING_WORD_FIELDS = {
    "word",
    "meaning",
    "pronunciation",
    "part_of_speech",
    "difficulty",
    "present_sentence",
    "past_sentence",
    "future_sentence",
    "base_form",
    "present_form",
    "past_form",
    "search_query",
}

LIST_WORD_FIELDS = {
    "synonyms",
    "antonyms",
    "image_keywords",
}

TRANSLATION_FIELDS = {
    "malayalam",
    "tamil",
    "hindi",
}


def build_vocabulary_prompt(
    topic,
    count,
    suggestions="",
):

    return VOCABULARY_PROMPT.format(
        topic=topic,
        count=count,
        suggestions=suggestions,
    )


def generate_vocabulary(
    topic,
    count,
    suggestions="",
):

    prompt = build_vocabulary_prompt(
        topic=topic,
        count=count,
        suggestions=suggestions,
    )
    model = GEMINI_CONTENT_MODEL
    last_error = None

    print(f"Gemini model: {model}")

    for attempt in range(2):
        attempt_prompt = (
            prompt
            if attempt == 0
            else _recovery_prompt(prompt)
        )
        response, model = _request_content(
            model=model,
            prompt=attempt_prompt,
            count=count,
        )

        try:
            truncated = _response_was_truncated(response)
            data = AIResponseCleaner.parse_json_object(
                _response_text(
                    response,
                    truncated=truncated,
                ),
                truncated=truncated,
            )
            _validate_lesson_structure(data, count)
        except (
            AIResponseParseError,
            LessonStructureError,
        ) as error:
            last_error = error
            _log_generation_diagnostic(error)

            if attempt == 0:
                category = getattr(
                    error,
                    "category",
                    "incomplete",
                )
                print(
                    f"Gemini returned {category} lesson JSON; "
                    "retrying once..."
                )
                continue

            break

        lesson = LessonMapper.from_dict(data)
        print("Lesson generated successfully.")
        return lesson

    raise LessonGenerationError(
        "Gemini lesson JSON remained invalid or incomplete "
        "after one recovery attempt."
    ) from last_error


def _request_content(model, prompt, count):

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=_lesson_response_schema(count),
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        return response, model
    except errors.ServerError as error:
        if (
            error.code != 503
            or model != GEMINI_CONTENT_MODEL
        ):
            raise

        print(
            f"{GEMINI_CONTENT_MODEL} "
            "is temporarily unavailable."
        )
        print(
            f"Trying fallback model: "
            f"{GEMINI_FALLBACK_MODEL}"
        )
        response = client.models.generate_content(
            model=GEMINI_FALLBACK_MODEL,
            contents=prompt,
            config=config,
        )
        return response, GEMINI_FALLBACK_MODEL


def _recovery_prompt(prompt):

    return (
        f"{prompt}\n\n"
        "RECOVERY REQUIREMENT:\n"
        "The previous response was invalid or incomplete. "
        "Return one complete JSON object only. Do not use "
        "markdown, commentary, ellipses, or omitted values."
    )


def _validate_lesson_structure(data, requested_count):

    if not isinstance(data, dict):
        raise LessonStructureError(
            "Lesson must be a top-level object."
        )

    if not isinstance(data.get("topic"), str):
        raise LessonStructureError(
            "Lesson topic is missing or invalid."
        )

    words = data.get("words")

    if not isinstance(words, list):
        raise LessonStructureError(
            "Lesson words must be a list."
        )

    if len(words) != requested_count:
        raise LessonStructureError(
            "Lesson is incomplete: expected "
            f"{requested_count} words, received {len(words)}."
        )

    for index, word in enumerate(words, start=1):
        if not isinstance(word, dict):
            raise LessonStructureError(
                f"Word {index} must be an object."
            )

        missing = REQUIRED_WORD_FIELDS.difference(word)

        if missing:
            raise LessonStructureError(
                f"Word {index} is missing required fields: "
                f"{', '.join(sorted(missing))}."
            )

        invalid_strings = [
            field
            for field in STRING_WORD_FIELDS
            if not isinstance(word.get(field), str)
        ]

        if invalid_strings:
            raise LessonStructureError(
                f"Word {index} has invalid string fields: "
                f"{', '.join(sorted(invalid_strings))}."
            )

        invalid_lists = [
            field
            for field in LIST_WORD_FIELDS
            if not isinstance(word.get(field), list)
        ]

        if invalid_lists:
            raise LessonStructureError(
                f"Word {index} has invalid list fields: "
                f"{', '.join(sorted(invalid_lists))}."
            )

        translations = word.get("translations")

        if (
            not isinstance(translations, dict)
            or not TRANSLATION_FIELDS.issubset(translations)
            or any(
                not isinstance(translations.get(field), str)
                for field in TRANSLATION_FIELDS
            )
        ):
            raise LessonStructureError(
                f"Word {index} has incomplete translations."
            )


def _response_was_truncated(response):

    finish_reason = getattr(response, "finish_reason", None)

    if finish_reason is None:
        try:
            finish_reason = response.candidates[0].finish_reason
        except (AttributeError, IndexError, TypeError):
            finish_reason = None

    reason_name = getattr(
        finish_reason,
        "name",
        str(finish_reason or ""),
    )
    return str(reason_name).upper() in {
        "MAX_TOKENS",
        "LENGTH",
    }


def _response_text(response, *, truncated):

    try:
        return response.text
    except (AttributeError, ValueError) as error:
        raise AIResponseParseError(
            "AI response did not contain readable text.",
            category=(
                "incomplete" if truncated else "invalid"
            ),
        ) from error


def _log_generation_diagnostic(error):

    if not CONTENT_GENERATION_VERBOSE_LOGGING:
        return

    print(
        "Lesson generation diagnostic: "
        f"{type(error).__name__}: {error}"
    )
    snippet = getattr(
        error,
        "diagnostic_snippet",
        "",
    )

    if snippet:
        print(f"Response near parse failure: {snippet}")


def _lesson_response_schema(count):

    string_schema = {"type": "string"}
    string_list_schema = {
        "type": "array",
        "items": string_schema,
    }
    word_properties = {
        field: string_schema
        for field in STRING_WORD_FIELDS
    }
    word_properties.update({
        field: string_list_schema
        for field in LIST_WORD_FIELDS
    })
    word_properties["translations"] = {
        "type": "object",
        "properties": {
            field: string_schema
            for field in TRANSLATION_FIELDS
        },
        "required": sorted(TRANSLATION_FIELDS),
    }

    return {
        "type": "object",
        "properties": {
            "topic": string_schema,
            "words": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "properties": word_properties,
                    "required": sorted(REQUIRED_WORD_FIELDS),
                },
            },
        },
        "required": ["topic", "words"],
    }
