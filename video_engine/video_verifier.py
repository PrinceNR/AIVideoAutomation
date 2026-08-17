import json
import mimetypes
from pathlib import Path

from google.genai import types

from ai.gemini_verification_client import (
    GeminiVerificationClient
)

from video_engine.video_candidate import (
    VideoCandidate
)

from config import (
    GEMINI_VIDEO_VERIFIER_MODEL,
    GEMINI_VIDEO_VERIFIER_FALLBACK_MODEL,
    VIDEO_MIN_SCORE
)


class VideoVerifier:

    def __init__(
        self,
        verification_client=None
    ):

        self.verification_client = (
            verification_client
            or GeminiVerificationClient()
        )

    def verify(
        self,
        word,
        candidate: VideoCandidate,
        frame_paths
    ) -> dict:

        frames = [
            Path(path)
            for path in frame_paths
            if Path(path).exists()
        ]

        if not frames:

            raise ValueError(
                "No video frames found "
                "for verification."
            )

        prompt = self._build_prompt(
            word,
            candidate,
            frames
        )

        contents = [
            prompt
        ]

        for index, frame_path in enumerate(
            frames,
            start=1
        ):

            mime_type = (
                mimetypes.guess_type(
                    frame_path
                )[0]
                or "image/jpeg"
            )

            contents.append(
                f"FRAME {index}: "
                f"{frame_path.name}"
            )

            contents.append(
                types.Part.from_bytes(
                    data=frame_path.read_bytes(),
                    mime_type=mime_type
                )
            )

        print(
            f"Verifying video for: "
            f"{word.word}"
        )

        response = (
            self.verification_client.generate(
                contents=contents,

                primary_model=(
                    GEMINI_VIDEO_VERIFIER_MODEL
                ),

                fallback_model=(
                    GEMINI_VIDEO_VERIFIER_FALLBACK_MODEL
                ),

                task_name="video verifier"
            )
        )

        if (
            response["status"]
            == "unavailable"
        ):

            return {
                "verification_status":
                    "unavailable",

                "score": 0,

                "suitable": False,

                "motion_visible": False,

                "meaning_match": False,

                "loop_suitable": False,

                "model_used": None,

                "reason":
                    "Gemini video verification "
                    "temporarily unavailable."
            }

        text = self._clean_json(
            response["text"]
        )

        result = json.loads(
            text
        )

        validated = (
            self._validate_result(
                result
            )
        )

        validated[
            "verification_status"
        ] = "completed"

        validated[
            "model_used"
        ] = response[
            "model_used"
        ]

        validated[
            "source"
        ] = candidate.source

        validated[
            "source_id"
        ] = candidate.source_id

        return validated

    def _build_prompt(
        self,
        word,
        candidate,
        frame_paths
    ):

        return f"""
    You are verifying a short motion clip for an English
    vocabulary educational video.

    TARGET WORD:
    {word.word}

    MEANING:
    {word.meaning}

    EXAMPLE SENTENCE:
    {word.present_sentence}

    VIDEO DURATION:
    {candidate.duration} seconds

    VIDEO SOURCE:
    {candidate.source}

    You will receive {len(frame_paths)} frames extracted
    from the video in chronological order.

    FRAME 1 is earlier in the video.
    Each following frame occurs later.

    Evaluate whether the SEQUENCE of frames communicates
    the intended meaning of the vocabulary word.

    The goal is educational clarity.

    Consider:

    1. MEANING MATCH
    Does the clip represent the intended meaning?

    2. MOTION
    Is the relevant movement or action visible across
    the chronological frames?

    3. EDUCATIONAL CLARITY
    Could an English learner understand the word from
    this motion clip?

    4. AMBIGUITY
    Penalize clips that could easily represent another
    action or meaning.

    5. VISUAL QUALITY
    The main person/object/action should be clearly
    visible.

    6. LOOP SUITABILITY
    This clip may be repeated like a GIF.
    Prefer a simple continuous scene without major cuts,
    unrelated scene changes, logos, or distracting text.

    IMPORTANT:

    Do not approve the video merely because the frames
    contain a related person or object.

    For a movement word, the chronological sequence must
    provide visual evidence of the movement.

    Example:

    For "nod", simply showing a person's face is not enough.
    The sequence should support visible up-and-down head
    movement.

    Score from 0 to 100.

    A clip should normally score at least
    {VIDEO_MIN_SCORE} to be automatically accepted.

    Return ONLY valid JSON.

    Use exactly this structure:

    {{
        "score": 0,
        "suitable": false,
        "motion_visible": false,
        "meaning_match": false,
        "loop_suitable": false,
        "reason": ""
    }}
    """

    def _validate_result(
        self,
        result
    ):

        try:

            score = int(
                result.get(
                    "score",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            score = 0

        score = max(
            0,
            min(
                score,
                100
            )
        )

        motion_visible = bool(
            result.get(
                "motion_visible",
                False
            )
        )

        meaning_match = bool(
            result.get(
                "meaning_match",
                False
            )
        )

        loop_suitable = bool(
            result.get(
                "loop_suitable",
                False
            )
        )

        model_suitable = bool(
            result.get(
                "suitable",
                False
            )
        )

        suitable = (
            model_suitable
            and meaning_match
            and motion_visible
            and score >= VIDEO_MIN_SCORE
        )

        return {
            "score":
                score,

            "suitable":
                suitable,

            "motion_visible":
                motion_visible,

            "meaning_match":
                meaning_match,

            "loop_suitable":
                loop_suitable,

            "reason":
                result.get(
                    "reason",
                    ""
                )
        }

    def _clean_json(
        self,
        text
    ):

        text = text.strip()

        if text.startswith(
            "```json"
        ):
            text = text[7:]

        elif text.startswith(
            "```"
        ):
            text = text[3:]

        if text.endswith(
            "```"
        ):
            text = text[:-3]

        return text.strip()