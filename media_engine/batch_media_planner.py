import json

from google.genai import errors

from ai.gemini_client import client

from media_engine.media_plan import (
    MediaPlan
)

from media_engine.media_type import (
    MediaType
)

from config import (
    GEMINI_CONTENT_MODEL,
    GEMINI_FALLBACK_MODEL
)


class BatchMediaPlanner:

    def plan(
        self,
        words
    ) -> list[MediaPlan]:

        if not words:
            return []

        prompt = self._build_prompt(
            words
        )

        response = self._generate(
            prompt
        )

        return self._parse(
            response.text,
            expected_count=len(words)
        )

    def _build_prompt(
        self,
        words
    ) -> str:

        vocabulary = []

        for index, word in enumerate(
            words
        ):

            vocabulary.append({
                "index": index,
                "word": word.word,
                "meaning": word.meaning,
                "part_of_speech":
                    word.part_of_speech,
                "sentence":
                    word.present_sentence
            })

        vocabulary_json = json.dumps(
            vocabulary,
            ensure_ascii=False,
            indent=2
        )

        return f"""
You are planning educational visual media for
English vocabulary learning videos.

For each vocabulary word, choose the single BEST
media type.

Available media types:

photo:
Use when one real-world still photograph clearly
communicates the intended meaning.

illustration:
Use when the meaning is abstract, emotional,
conceptual, symbolic, or difficult to communicate
clearly with a normal photograph.

video:
Use when visible movement, gesture, change over time,
physical action, or sequence materially improves
understanding.

Rules:

- Do not choose video merely because a word is a verb.
- Prefer photo when one clear photograph is enough.
- Prefer illustration when a still visual is useful
  but a photograph would likely be ambiguous.
- Choose video when motion is important to the meaning.
- Judge the intended meaning, not other meanings of
  the same word.
- Preserve every input index.
- Return exactly one result per input word.
- Return valid JSON only.
- Do not include Markdown.

Vocabulary:

{vocabulary_json}

Return:

{{
    "plans": [
        {{
            "index": 0,
            "preferred_type": "photo",
            "requires_motion": false,
            "reason": "Short reason"
        }}
    ]
}}
"""

    def _generate(
        self,
        prompt: str
    ):

        try:

            print(
                f"Batch media planner model: "
                f"{GEMINI_CONTENT_MODEL}"
            )

            return client.models.generate_content(
                model=GEMINI_CONTENT_MODEL,
                contents=prompt
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

            return client.models.generate_content(
                model=GEMINI_FALLBACK_MODEL,
                contents=prompt
            )

    def _parse(
        self,
        text: str,
        expected_count: int
    ) -> list[MediaPlan]:

        data = json.loads(
            text.strip()
        )

        raw_plans = data.get(
            "plans",
            []
        )

        if len(raw_plans) != expected_count:

            raise ValueError(
                "Media planner returned an "
                "unexpected number of plans."
            )

        raw_plans.sort(
            key=lambda item: item["index"]
        )

        plans = []

        for expected_index, item in enumerate(
            raw_plans
        ):

            if (
                item.get("index")
                != expected_index
            ):

                raise ValueError(
                    "Media planner returned "
                    "invalid plan indexes."
                )

            media_type = MediaType(
                item["preferred_type"]
            )

            requires_motion = bool(
                item.get(
                    "requires_motion",
                    False
                )
            )

            if media_type != MediaType.VIDEO:
                requires_motion = False

            plans.append(
                MediaPlan(
                    preferred_type=media_type,
                    reason=item.get(
                        "reason",
                        ""
                    ),
                    requires_motion=(
                        requires_motion
                    )
                )
            )

        return plans