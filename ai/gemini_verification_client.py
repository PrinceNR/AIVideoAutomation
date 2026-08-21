import re
import time

from google.genai import errors

from ai.gemini_client import client


class GeminiVerificationClient:

    def __init__(self):

        self._daily_exhausted_models = set()

    def generate(
        self,
        contents,
        primary_model: str,
        fallback_model: str,
        task_name: str = "verification",
        service_unavailable_retry_delay=None
    ) -> dict:

        models = [
            primary_model,
            fallback_model
        ]

        failures = []
        retry_used = False

        for index, model in enumerate(models):

            if model in self._daily_exhausted_models:
                print(
                    f"{model} daily/project quota was "
                    "already exhausted; skipping this model."
                )
                failures.append(
                    "daily_quota_exhausted"
                )
                continue

            if index == 0:
                print(
                    f"Gemini {task_name} model: "
                    f"{model}"
                )
            else:
                print(
                    f"Trying fallback model: {model}"
                )

            response, failure = self._call_model(
                model,
                contents
            )

            if response is not None:
                return {
                    "status": "completed",
                    "text": response.text,
                    "model_used": model
                }

            self._remember_daily_quota(
                model,
                failure
            )
            self._print_model_failure(
                model,
                failure
            )

            if (
                (
                    failure["kind"]
                    == "temporary_rate_limit"
                    and failure["retry_delay"]
                    is not None
                )
                or (
                    failure["kind"]
                    == "service_unavailable"
                    and service_unavailable_retry_delay
                    is not None
                )
            ) and not retry_used:
                retry_used = True
                retry_delay = (
                    failure["retry_delay"]
                    if failure["retry_delay"] is not None
                    else service_unavailable_retry_delay
                )

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
                    return {
                        "status": "completed",
                        "text": response.text,
                        "model_used": model
                    }

                self._remember_daily_quota(
                    model,
                    failure
                )
                self._print_model_failure(
                    model,
                    failure,
                    after_retry=True
                )

            failures.append(
                failure["kind"]
            )

        print(
            f"Both Gemini {task_name} models "
            "are unavailable."
        )

        return {
            "status": "unavailable",
            "unavailable_reason": (
                self._unavailable_reason(
                    failures
                )
            ),
            "text": None,
            "model_used": None
        }

    def _call_model(
        self,
        model,
        contents
    ):

        try:
            response = (
                client.models.generate_content(
                    model=model,
                    contents=contents
                )
            )
            return response, None

        except errors.ServerError as error:
            if str(error.code) != "503":
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

    def _rate_limit_failure(self, error):

        normalized = re.sub(
            r"[^a-z0-9]+",
            "",
            self._error_text(error).lower()
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

    def _remember_daily_quota(
        self,
        model,
        failure
    ):

        if failure["kind"] == "daily_quota_exhausted":
            self._daily_exhausted_models.add(
                model
            )

    @staticmethod
    def _print_model_failure(
        model,
        failure,
        after_retry=False
    ):

        if failure["kind"] == "daily_quota_exhausted":
            print(
                f"{model} daily/project quota is "
                "exhausted; not retrying this model."
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
        else:
            print(
                f"{model} is temporarily unavailable."
            )

    @staticmethod
    def _unavailable_reason(failures):

        if "daily_quota_exhausted" in failures:
            return "quota_exhausted"

        if "temporary_rate_limit" in failures:
            return "rate_limited"

        return "service_unavailable"
