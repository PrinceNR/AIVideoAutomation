import json

from google.genai import errors

from ai.gemini_client import client

from media_engine.media_plan import (
    MediaPlan
)

from media_engine.media_type import (
    MediaType
)

from media_engine.prompts import (
    MEDIA_PLANNER_PROMPT
)

from config import (
    GEMINI_CONTENT_MODEL,
    GEMINI_FALLBACK_MODEL
)


class MediaPlanner:

    def plan(
        self,
        word
    ) -> MediaPlan:

        prompt = (
            MEDIA_PLANNER_PROMPT.format(
                word=word.word,
                meaning=word.meaning,
                part_of_speech=(
                    word.part_of_speech
                ),
                sentence=(
                    word.present_sentence
                )
            )
        )

        response = (
            self._generate(
                prompt
            )
        )

        return self._parse(
            response.text
        )

    def _generate(
        self,
        prompt: str
    ):

        try:

            print(
                f"Media planner model: "
                f"{GEMINI_CONTENT_MODEL}"
            )

            return (
                client.models.generate_content(
                    model=(
                        GEMINI_CONTENT_MODEL
                    ),
                    contents=prompt
                )
            )

        except errors.ServerError as error:

            if error.code != 503:
                raise

            print(
                f"{GEMINI_CONTENT_MODEL} "
                f"is temporarily unavailable."
            )

            print(
                f"Trying fallback model: "
                f"{GEMINI_FALLBACK_MODEL}"
            )

            return (
                client.models.generate_content(
                    model=(
                        GEMINI_FALLBACK_MODEL
                    ),
                    contents=prompt
                )
            )

    def _parse(
        self,
        text: str
    ) -> MediaPlan:

        data = json.loads(
            text.strip()
        )

        media_type = MediaType(
            data["preferred_type"]
        )

        requires_motion = bool(
            data.get(
                "requires_motion",
                False
            )
        )

        # Keep the result logically consistent
        if media_type != MediaType.VIDEO:
            requires_motion = False

        return MediaPlan(
            preferred_type=media_type,
            reason=data.get(
                "reason",
                ""
            ),
            requires_motion=(
                requires_motion
            )
        )