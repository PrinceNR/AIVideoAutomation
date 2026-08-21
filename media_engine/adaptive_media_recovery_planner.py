import json

from google.genai import errors

from ai.gemini_client import client
from config import (
    GEMINI_CONTENT_MODEL,
    GEMINI_FALLBACK_MODEL
)
from media_engine.media_recovery_plan import (
    MediaRecoveryPlan
)
from media_engine.media_type import (
    MediaType
)


class AdaptiveMediaRecoveryPlanner:

    def plan(
        self,
        word,
        attempted_queries
    ):

        attempted_queries = self._normalize_queries(
            attempted_queries
        )

        prompt = self._build_prompt(
            word,
            attempted_queries
        )

        response = self._generate(
            prompt
        )

        return self._parse(
            response.text,
            attempted_queries
        )

    @staticmethod
    def _build_prompt(
        word,
        attempted_queries
    ):

        context = {
            "word": word.word,
            "meaning": word.meaning,
            "part_of_speech": word.part_of_speech,
            "present_sentence": word.present_sentence,
            "past_sentence": word.past_sentence,
            "future_sentence": word.future_sentence,
            "preferred_media": word.preferred_media,
            "media_reason": word.media_reason,
            "requires_motion": word.requires_motion,
            "attempted_queries": attempted_queries
        }

        context_json = json.dumps(
            context,
            ensure_ascii=False,
            indent=2
        )

        return f"""
You are making ONE bounded recovery plan for media
selection in an English vocabulary teaching video.

Normal media selection already tried every planned
photo/illustration or video fallback and found no
verified media scoring at least the required threshold.

Choose the single representation most likely to teach
the exact intended sense now:

- video for motion, timing, hesitation, gesture,
  transition, or change over time;
- photo for a concrete real-world action or scene;
- illustration for a static concept that is difficult
  to photograph literally.

Then generate exactly 3 NEW stock-search queries for
only that representation.

Rules:

- Use the meaning and all examples to preserve the
  intended teaching sense.
- Consider the previous media choice, reason, and
  requires_motion value, but change type when another
  representation is clearly more teachable.
- Never repeat or trivially rephrase an attempted query.
- Each query must contain 2 to 6 words.
- Use literal, stock-search-friendly visible actions or
  scenes rather than abstract synonyms.
- Do not copy a full example sentence.
- Keep every query YouTube-safe and educational.
- This is the only recovery plan; do not propose a
  sequence of additional fallbacks.
- Return valid JSON only, without Markdown.

For "hesitate", a useful recovery may choose video and
search for visible pause-and-decide motion, rather than
another still image of a person near a door.

Context:

{context_json}

Return exactly:

{{
    "media_type": "video",
    "reason": "Short recovery reason",
    "search_queries": [
        "new query one",
        "new query two",
        "new query three"
    ]
}}
"""

    @staticmethod
    def _generate(prompt):

        try:
            print(
                "Adaptive media recovery model: "
                f"{GEMINI_CONTENT_MODEL}"
            )

            return client.models.generate_content(
                model=GEMINI_CONTENT_MODEL,
                contents=prompt
            )

        except errors.ServerError as error:
            if str(error.code) != "503":
                raise

            print(
                f"{GEMINI_CONTENT_MODEL} is "
                "temporarily unavailable."
            )
            print(
                "Trying fallback model: "
                f"{GEMINI_FALLBACK_MODEL}"
            )

            return client.models.generate_content(
                model=GEMINI_FALLBACK_MODEL,
                contents=prompt
            )

    def _parse(
        self,
        text,
        attempted_queries
    ):

        data = json.loads(
            self._clean_json(text)
        )

        media_type = MediaType(
            data["media_type"]
        )

        search_queries = self._normalize_queries(
            data.get(
                "search_queries",
                []
            )
        )

        if len(search_queries) != 3:
            raise ValueError(
                "Adaptive media recovery must return "
                "exactly 3 search queries."
            )

        if any(
            not 2 <= len(query.split()) <= 6
            for query in search_queries
        ):
            raise ValueError(
                "Adaptive recovery queries must "
                "contain 2 to 6 words."
            )

        attempted_keys = {
            query.lower()
            for query in self._normalize_queries(
                attempted_queries
            )
        }

        repeated_queries = [
            query
            for query in search_queries
            if query.lower() in attempted_keys
        ]

        if repeated_queries:
            raise ValueError(
                "Adaptive media recovery repeated "
                "an attempted query."
            )

        return MediaRecoveryPlan(
            media_type=media_type,
            reason=str(
                data.get("reason", "")
            ).strip(),
            search_queries=search_queries
        )

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

    @staticmethod
    def _clean_json(text):

        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()
