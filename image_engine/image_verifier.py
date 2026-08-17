import json
import mimetypes
from pathlib import Path

from google.genai import (
    types,
    errors
)

from ai.gemini_client import client

from config import (
    GEMINI_IMAGE_VERIFIER_MODEL,
    GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL,
    IMAGE_MIN_SCORE
)


class ImageVerifier:

    def verify(
        self,
        word,
        image_paths
    ):

        image_paths = [
            Path(path)
            for path in image_paths
            if Path(path).exists()
        ]

        if not image_paths:

            raise ValueError(
                f"No candidate images found for {word.word}"
            )

        prompt = self._build_prompt(
            word,
            image_paths
        )

        contents = [
            prompt
        ]

        # Add:
        #
        # IMAGE FILE: pexels_001.jpg
        # [actual image]
        #
        # IMAGE FILE: pixabay_001.jpg
        # [actual image]

        for image_path in image_paths:

            mime_type = (
                mimetypes.guess_type(
                    image_path
                )[0]
                or "image/jpeg"
            )

            contents.append(
                f"IMAGE FILE: {image_path.name}"
            )

            contents.append(
                types.Part.from_bytes(
                    data=image_path.read_bytes(),
                    mime_type=mime_type
                )
            )

        print(
            f"Verifying {len(image_paths)} images "
            f"for: {word.word}"
        )

        # print(
        #     f"Gemini image model: "
        #     f"{GEMINI_IMAGE_VERIFIER_MODEL}"
        # )

        # response = client.models.generate_content(
        #     model=GEMINI_IMAGE_VERIFIER_MODEL,
        #     contents=contents
        # )

        print(
            f"Gemini image model: "
            f"{GEMINI_IMAGE_VERIFIER_MODEL}"
        )

        model_used = (
            GEMINI_IMAGE_VERIFIER_MODEL
        )

        try:

            response = (
                client.models.generate_content(
                    model=GEMINI_IMAGE_VERIFIER_MODEL,
                    contents=contents
                )
            )

        except errors.ServerError as error:

            if error.code != 503:
                raise

            print(
                f"{GEMINI_IMAGE_VERIFIER_MODEL} "
                "is temporarily unavailable."
            )

            print(
                "Trying fallback image model: "
                f"{GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL}"
            )

            model_used = (
                GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
            )

            try:

                response = (
                    client.models.generate_content(
                        model=(
                            GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
                        ),
                        contents=contents
                    )
                )

            except errors.ServerError as fallback_error:

                if fallback_error.code != 503:
                    raise

                print(
                    "Both Gemini image models are "
                    "temporarily unavailable."
                )

                return {
                    "verification_status":
                        "unavailable",

                    "selected_image":
                        None,

                    "selected_score":
                        0,

                    "model_used":
                        None,

                    "candidates":
                        [],

                    "error":
                        "Gemini image verification "
                        "temporarily unavailable."
                }

        text = self._clean_json(
            response.text
        )

        result = json.loads(
            text
        )

        validated_result = (
            self._validate_result(
                result,
                image_paths
            )
        )

        validated_result[
            "verification_status"
        ] = "completed"

        validated_result[
            "model_used"
        ] = model_used

        return validated_result

    # -------------------------------------------------
    # PROMPT
    # -------------------------------------------------

    def _build_prompt(
        self,
        word,
        image_paths
    ):

        filenames = "\n".join(
            f"- {path.name}"
            for path in image_paths
        )

        return f"""
You are selecting the best image for an English vocabulary
educational video.

TARGET WORD:
{word.word}

MEANING:
{word.meaning}

EXAMPLE SENTENCE:
{word.present_sentence}

IMAGE SEARCH QUERY:
{word.search_query}

CANDIDATE FILES:

{filenames}

Each candidate image will be provided after this instruction.
The exact filename appears immediately before its image.

Evaluate EVERY candidate independently.

The main goal is educational clarity.

The best image should help an English learner understand the
meaning of "{word.word}" immediately.

Score each image from 0 to 100.

Consider:

1. SEMANTIC MATCH
   Does the image actually represent the intended meaning?

2. EDUCATIONAL CLARITY
   Could a learner understand the word from this image?

3. VISUAL CLARITY
   Is the important action, person, or object clearly visible?

4. AMBIGUITY
   Penalize images that could easily represent a different word.

5. DISTRACTIONS
   Penalize:
   - excessive text
   - logos
   - watermarks
   - clutter
   - tiny subjects
   - irrelevant background elements

6. SUITABILITY
   The image should be suitable for a general English-learning
   YouTube video.

IMPORTANT:

Judge the intended meaning using the MEANING and EXAMPLE SENTENCE.

Do not select an image merely because it contains objects from
the search query.

For action verbs, prefer an image where the ACTION itself is
clearly visible.

For nouns, prefer an image where the target object is easy
to identify.

For abstract words, prefer a scene that clearly communicates
the concept.

Do not favor Pexels or Pixabay.
Judge all sources equally.

If no candidate is genuinely useful for teaching the word,
do not force a selection.

An image should normally score at least {IMAGE_MIN_SCORE}
to be automatically selected.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "selected_image": null,
    "selected_score": 0,
    "candidates": [
        {{
            "image": "filename.jpg",
            "score": 0,
            "suitable": false,
            "reason": ""
        }}
    ]
}}

Rules:

- Include every provided candidate exactly once.
- "image" must use the exact supplied filename.
- Scores must be integers from 0 to 100.
- Select the highest-quality educational image.
- If the best score is below {IMAGE_MIN_SCORE},
  set "selected_image" to null.
- If selected_image is null, selected_score must contain
  the highest candidate score.
"""

    # -------------------------------------------------
    # VALIDATE GEMINI RESULT
    # -------------------------------------------------

    def _validate_result(
        self,
        result,
        image_paths
    ):

        valid_names = {
            path.name
            for path in image_paths
        }

        candidates = []

        for candidate in result.get(
            "candidates",
            []
        ):

            image_name = candidate.get(
                "image"
            )

            # Gemini invented a filename
            if image_name not in valid_names:
                continue

            try:
                score = int(
                    candidate.get(
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

            candidates.append({
                "image": image_name,
                "score": score,
                "suitable": bool(
                    candidate.get(
                        "suitable",
                        False
                    )
                ),
                "reason": candidate.get(
                    "reason",
                    ""
                )
            })

        if not candidates:

            raise ValueError(
                "Gemini did not return "
                "valid image candidates."
            )

        candidates.sort(
            key=lambda item:
                item["score"],
            reverse=True
        )

        best = candidates[0]

        selected_image = None

        if (
            best["score"] >= IMAGE_MIN_SCORE
            and best["suitable"]
        ):
            selected_image = best["image"]

        return {
            "selected_image":
                selected_image,

            "selected_score":
                best["score"],

            "candidates":
                candidates
        }

    # -------------------------------------------------
    # CLEAN JSON
    # -------------------------------------------------

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