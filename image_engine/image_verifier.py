import json
import mimetypes
import re
import time
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

        response, model_used, failures = (
            self._generate_with_fallback(
                contents
            )
        )

        if response is None:
            return self._unavailable_result(
                failures
            )

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
    # GEMINI AVAILABILITY / QUOTA HANDLING
    # -------------------------------------------------

    def _generate_with_fallback(
        self,
        contents
    ):

        models = [
            GEMINI_IMAGE_VERIFIER_MODEL,
            GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
        ]

        failures = []
        retry_used = False

        for index, model in enumerate(models):

            if index == 1:
                print(
                    "Trying fallback image model: "
                    f"{model}"
                )

            response, failure = self._call_model(
                model,
                contents
            )

            if response is not None:
                return response, model, failures

            self._print_model_failure(
                model,
                failure
            )

            if (
                failure["kind"] in (
                    "temporary_rate_limit",
                    "transient_transport"
                )
                and failure["retry_delay"]
                is not None
                and not retry_used
            ):
                retry_used = True
                retry_delay = failure[
                    "retry_delay"
                ]

                if (
                    failure["kind"]
                    == "transient_transport"
                ):
                    print(
                        "Retrying Gemini image "
                        "verification once after a "
                        "transient transport failure."
                    )
                else:
                    print(
                        "Retrying once after Gemini's "
                        f"{retry_delay:g}s retry delay."
                    )

                time.sleep(retry_delay)

                response, failure = self._call_model(
                    model,
                    contents
                )

                if response is not None:
                    return response, model, failures

                self._print_model_failure(
                    model,
                    failure,
                    after_retry=True
                )

            failures.append(failure["kind"])

        return None, None, failures

    def _call_model(
        self,
        model,
        contents
    ):

        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            return response, None

        except errors.ServerError as error:
            if self._is_transient_transport_error(
                error
            ):
                return None, {
                    "kind": "transient_transport",
                    "retry_delay": 1.0
                }

            if error.code != 503:
                raise

            return None, {
                "kind": "service_unavailable",
                "retry_delay": None
            }

        except errors.ClientError as error:
            if not self._is_rate_limit_error(error):
                raise

            return None, self._rate_limit_failure(
                error
            )

        except Exception as error:
            if not self._is_transient_transport_error(
                error
            ):
                raise

            return None, {
                "kind": "transient_transport",
                "retry_delay": 1.0
            }

    def _rate_limit_failure(self, error):

        error_text = self._error_text(error)

        normalized = re.sub(
            r"[^a-z0-9]+",
            "",
            error_text.lower()
        )

        daily_quota = (
            "perday" in normalized
            or "dailyquota" in normalized
            or "dailylimit" in normalized
        )

        return {
            "kind": (
                "daily_quota_exhausted"
                if daily_quota
                else "temporary_rate_limit"
            ),
            "retry_delay": (
                None
                if daily_quota
                else self._retry_delay_seconds(error)
            )
        }

    def _is_rate_limit_error(self, error):

        if str(getattr(error, "code", "")) == "429":
            return True

        return (
            "RESOURCE_EXHAUSTED"
            in self._error_text(error).upper()
        )

    def _is_transient_transport_error(self, error):

        text = self._error_text(error).lower()

        markers = (
            "server disconnected without sending "
            "a response",
            "remoteprotocolerror",
            "connection reset",
            "connection aborted",
            "connection closed",
            "network error",
            "read timeout",
            "timed out",
            "transport error"
        )

        return any(
            marker in text
            for marker in markers
        )

    def _error_text(self, error):

        values = [
            str(error),
            getattr(error, "status", None),
            getattr(error, "message", None),
            getattr(error, "details", None),
            getattr(error, "response_json", None)
        ]

        return " ".join(
            str(value)
            for value in values
            if value is not None
        )

    def _retry_delay_seconds(self, error):

        for attribute in (
            "details",
            "response_json"
        ):
            delay = self._find_retry_delay(
                getattr(error, attribute, None)
            )
            if delay is not None:
                return delay

        match = re.search(
            r"retryDelay['\"]?\s*[:=]\s*['\"]?"
            r"(\d+(?:\.\d+)?)s",
            self._error_text(error),
            flags=re.IGNORECASE
        )

        if match:
            return float(match.group(1))

        return None

    def _find_retry_delay(self, value):

        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = re.sub(
                    r"[^a-z]",
                    "",
                    str(key).lower()
                )
                if normalized_key == "retrydelay":
                    return self._parse_duration(item)

                delay = self._find_retry_delay(item)
                if delay is not None:
                    return delay

        elif isinstance(value, (list, tuple)):
            for item in value:
                delay = self._find_retry_delay(item)
                if delay is not None:
                    return delay

        return None

    def _parse_duration(self, value):

        if isinstance(value, (int, float)):
            return max(0.0, float(value))

        if isinstance(value, dict):
            seconds = float(value.get("seconds", 0))
            nanos = float(value.get("nanos", 0))
            return max(
                0.0,
                seconds + nanos / 1_000_000_000
            )

        match = re.fullmatch(
            r"\s*(\d+(?:\.\d+)?)s?\s*",
            str(value)
        )

        if match:
            return float(match.group(1))

        return None

    def _print_model_failure(
        self,
        model,
        failure,
        after_retry=False
    ):

        if failure["kind"] == "daily_quota_exhausted":
            print(
                f"{model} daily/project quota "
                "is exhausted; not retrying this model."
            )
        elif failure["kind"] == "temporary_rate_limit":
            suffix = (
                " after its single retry"
                if after_retry
                else ""
            )
            print(
                f"{model} is temporarily "
                f"rate-limited{suffix}."
            )
        elif failure["kind"] == "transient_transport":
            suffix = (
                " after its single retry"
                if after_retry
                else ""
            )
            print(
                "Gemini image verification had a "
                f"transient transport failure{suffix}."
            )
        else:
            print(
                f"{model} is temporarily unavailable."
            )

    def _unavailable_result(self, failures):

        if "daily_quota_exhausted" in failures:
            reason = "quota_exhausted"
        elif "temporary_rate_limit" in failures:
            reason = "rate_limited"
        elif "transient_transport" in failures:
            reason = "transport_error"
        else:
            reason = "service_unavailable"

        print(
            "Both Gemini image verification "
            "models are unavailable."
        )

        return {
            "verification_status": "unavailable",
            "unavailable_reason": reason,
            "selected_image": None,
            "selected_score": 0,
            "model_used": None,
            "candidates": [],
            "error": (
                "Gemini image verification "
                "temporarily unavailable."
            )
        }

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
