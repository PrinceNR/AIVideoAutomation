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
                "present_sentence":
                    word.present_sentence,
                "past_sentence":
                    word.past_sentence,
                "future_sentence":
                    word.future_sentence,
                "existing_preferred_media":
                    word.preferred_media,
                "existing_media_reason":
                    word.media_reason,
                "existing_requires_motion":
                    word.requires_motion
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
media type and create exactly 3 stock-image search
queries for the intended teaching sense.

Work in this order for every word:

1. Read the meaning, part of speech, and all example
   sentences to identify the exact intended sense.
2. Derive one concrete VISUAL TEACHING CONCEPT that
   could make that sense understandable to a learner.
3. Choose the preferred media type and whether motion
   is required.
4. Using that concept and media decision, create three
   short stock-image queries. These image queries are
   also needed when video later falls back to an image.

If existing media planning fields are supplied, use
them as context but correct them when the intended
sense requires a better choice.

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
- For abstract words, convert the meaning into a
  concrete action, interaction, or situation before
  writing queries.
- Prefer a visible cause, action, or consequence over
  a vague emotional association.
- Do not merely turn synonyms into search queries.
- Each image query must contain 2 to 6 words.
- Use literal, common stock-photo search language.
- Keep queries broad enough to exist on Pexels or
  Pixabay; do not copy a full example sentence.
- Make all scenes YouTube-safe and educational.
- Return exactly 3 distinct image queries per word.
- Preserve every input index.
- Return exactly one result per input word.
- Return valid JSON only.
- Do not include Markdown.

Examples:

Word: reliable
Meaning: can be trusted to work well or behave
consistently

Visual concept:
an employee repeatedly completing work correctly
and on time

Good image queries:
- employee completing task on time
- worker meeting project deadline
- professional checking finished work

Avoid synonym-only associations such as:
- dependable person smiling
- trustworthy employee
- steady worker

Word: reputation
Meaning: the opinion people have formed about a
person or organization over time

Visual concept:
customers reading and discussing a business's
accumulated public reviews

Good image queries:
- customer reading business reviews
- people discussing company reviews
- business owner checking ratings

Avoid generic success symbols such as awards,
handshakes, or certificates when they do not show
how reputation is formed.

Word: rescue
Meaning: save someone from danger

Good image queries:
- lifeguard rescuing swimmer
- firefighter carrying person safety
- water rescue action

Vocabulary:

{vocabulary_json}

Return:

{{
    "plans": [
        {{
            "index": 0,
            "preferred_type": "photo",
            "requires_motion": false,
            "reason": "Short reason",
            "visual_concept": "Concrete visible teaching scene",
            "image_search_queries": [
                "query one",
                "query two",
                "query three"
            ]
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

            visual_concept = " ".join(
                str(
                    item.get(
                        "visual_concept",
                        ""
                    )
                ).strip().split()
            )

            if not visual_concept:
                raise ValueError(
                    "Each media plan must include "
                    "a visual teaching concept."
                )

            image_search_queries = (
                self._normalize_queries(
                    item.get(
                        "image_search_queries",
                        []
                    )
                )
            )

            if len(image_search_queries) != 3:
                raise ValueError(
                    "Each media plan must include "
                    "exactly 3 image search queries."
                )

            if any(
                not 2 <= len(query.split()) <= 6
                for query in image_search_queries
            ):
                raise ValueError(
                    "Image search queries must contain "
                    "2 to 6 words."
                )

            plans.append(
                MediaPlan(
                    preferred_type=media_type,
                    reason=item.get(
                        "reason",
                        ""
                    ),
                    requires_motion=(
                        requires_motion
                    ),
                    visual_concept=(
                        visual_concept
                    ),
                    image_search_queries=(
                        image_search_queries
                    )
                )
            )

        return plans

    @staticmethod
    def _normalize_queries(queries):

        normalized = []
        seen = set()

        for query in queries:
            if not isinstance(query, str):
                continue

            clean_query = " ".join(
                query.strip().split()
            )

            if not clean_query:
                continue

            key = clean_query.lower()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(clean_query)

        return normalized
