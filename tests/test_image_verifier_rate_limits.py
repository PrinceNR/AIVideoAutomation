import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config import (
    GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL,
    GEMINI_IMAGE_VERIFIER_MODEL
)
from image_engine import image_verifier
from image_engine.image_verifier import ImageVerifier


class FakeClientError(Exception):

    def __init__(self, response_json):
        super().__init__(str(response_json))
        self.code = 429
        self.status = "RESOURCE_EXHAUSTED"
        self.response_json = response_json
        self.details = response_json["error"].get(
            "details",
            []
        )


class FakeModels:

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate_content(self, model, contents):
        self.calls.append(model)
        outcome = self.outcomes.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


class ImageVerifierRateLimitTests(unittest.TestCase):

    def setUp(self):
        self.word = SimpleNamespace(
            word="passionate",
            meaning="showing strong feeling",
            present_sentence="She is passionate about art.",
            search_query="enthusiastic artist"
        )

    def _success_response(self, image_name):
        return SimpleNamespace(
            text=json.dumps({
                "selected_image": image_name,
                "selected_score": 85,
                "candidates": [{
                    "image": image_name,
                    "score": 85,
                    "suitable": True,
                    "reason": "Clear semantic match."
                }]
            })
        )

    def _daily_quota_error(self):
        return FakeClientError({
            "error": {
                "code": 429,
                "status": "RESOURCE_EXHAUSTED",
                "details": [{
                    "@type": (
                        "type.googleapis.com/"
                        "google.rpc.QuotaFailure"
                    ),
                    "violations": [{
                        "quotaId": (
                            "GenerateRequestsPerDayPerProject"
                            "PerModel-FreeTier"
                        )
                    }]
                }]
            }
        })

    def _temporary_limit_error(self, delay="2s"):
        return FakeClientError({
            "error": {
                "code": 429,
                "status": "RESOURCE_EXHAUSTED",
                "details": [{
                    "@type": (
                        "type.googleapis.com/"
                        "google.rpc.RetryInfo"
                    ),
                    "retryDelay": delay
                }]
            }
        })

    def _verify(self, outcomes):
        models = FakeModels(outcomes)
        fake_client = SimpleNamespace(models=models)

        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder) / "candidate.jpg"
            image_path.write_bytes(b"candidate image")

            with (
                patch.object(
                    image_verifier,
                    "client",
                    fake_client
                ),
                patch.object(
                    image_verifier.errors,
                    "ClientError",
                    FakeClientError
                ),
                patch.object(
                    image_verifier.time,
                    "sleep"
                ) as sleep
            ):
                result = ImageVerifier().verify(
                    self.word,
                    [image_path]
                )

        return result, models.calls, sleep

    def test_daily_primary_quota_uses_fallback_without_sleep(self):
        result, calls, sleep = self._verify([
            self._daily_quota_error(),
            self._success_response("candidate.jpg")
        ])

        self.assertEqual(
            calls,
            [
                GEMINI_IMAGE_VERIFIER_MODEL,
                GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
            ]
        )
        sleep.assert_not_called()
        self.assertEqual(result["verification_status"], "completed")
        self.assertEqual(
            result["model_used"],
            GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
        )
        self.assertEqual(
            result["selected_image"],
            "candidate.jpg"
        )
        self.assertEqual(result["selected_score"], 85)

    def test_temporary_limit_honors_retry_info_once(self):
        result, calls, sleep = self._verify([
            self._temporary_limit_error("2s"),
            self._success_response("candidate.jpg")
        ])

        self.assertEqual(
            calls,
            [
                GEMINI_IMAGE_VERIFIER_MODEL,
                GEMINI_IMAGE_VERIFIER_MODEL
            ]
        )
        sleep.assert_called_once_with(2.0)
        self.assertEqual(result["verification_status"], "completed")
        self.assertEqual(
            result["model_used"],
            GEMINI_IMAGE_VERIFIER_MODEL
        )

    def test_both_models_exhausted_returns_unavailable(self):
        result, calls, sleep = self._verify([
            self._temporary_limit_error("1s"),
            self._temporary_limit_error("1s"),
            self._daily_quota_error()
        ])

        self.assertEqual(
            calls,
            [
                GEMINI_IMAGE_VERIFIER_MODEL,
                GEMINI_IMAGE_VERIFIER_MODEL,
                GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
            ]
        )
        sleep.assert_called_once_with(1.0)
        self.assertEqual(result["verification_status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], "quota_exhausted")
        self.assertIsNone(result["selected_image"])
        self.assertEqual(result["selected_score"], 0)
        self.assertEqual(result["candidates"], [])


if __name__ == "__main__":
    unittest.main()
