import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ai import gemini_verification_client
from ai.gemini_verification_client import (
    GeminiVerificationClient
)
from media_engine.media_selection_service import (
    MediaSelectionService
)
from models.word import Word
from video_engine.video_selection_service import (
    VideoSelectionService
)


def make_word(word_text="resign"):
    return Word(
        word=word_text,
        meaning="test meaning",
        pronunciation="",
        part_of_speech="verb",
        difficulty="medium",
        translations={},
        present_sentence="Test sentence.",
        past_sentence="",
        future_sentence="",
        base_form=word_text,
        present_form=word_text,
        past_form=word_text,
        synonyms=[],
        antonyms=[],
        image_keywords=[],
        search_query=word_text,
        preferred_media="video"
    )


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


class SearchStrategy:

    def build_queries(self, word):
        return ["test query"]


class CandidateCollector:

    def collect(self, query, per_source):
        return [
            SimpleNamespace(source_id="1"),
            SimpleNamespace(source_id="2")
        ]


class CandidateDownloader:

    def download(
        self,
        candidates,
        output_folder,
        max_downloads
    ):
        return [
            SimpleNamespace(
                source="pexels",
                source_id=candidate.source_id,
                video_url=(
                    "https://example.test/"
                    f"{candidate.source_id}.mp4"
                ),
                local_path=(
                    f"candidate_{candidate.source_id}.mp4"
                ),
                duration=4.0,
                width=1280,
                height=720
            )
            for candidate in candidates[:max_downloads]
        ]


class FrameExtractor:

    def extract(self, video_path, output_folder):
        return [Path("frame.jpg")]


class ResultVerifier:

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    def verify(self, word, candidate, frame_paths):
        self.calls += 1

        if self.error is not None:
            raise self.error

        return dict(self.result)


class ResultVideoService:

    def __init__(self, status=None, error=None):
        self.status = status
        self.error = error

    def select(self, word, output_folder):
        if self.error is not None:
            raise self.error

        return {
            "status": self.status,
            "selected_video": None,
            "selected_score": 0,
            "attempts": []
        }


class ResultImageDownloader:

    def __init__(self, status):
        self.status = status

    def download_word_images(self, word, lesson_folder):
        if self.status == "selected":
            image_path = Path(lesson_folder) / "fallback.jpg"
            image_path.write_bytes(b"image")
            word.default_image = str(image_path)
            word.media_type = "photo"
        else:
            word.default_image = None
            word.media_type = None

        return {"status": self.status}


class VideoVerificationStatusTests(unittest.TestCase):

    @staticmethod
    def _selection_service(verifier):
        return VideoSelectionService(
            search_strategy=SearchStrategy(),
            candidate_collector=CandidateCollector(),
            candidate_downloader=CandidateDownloader(),
            frame_extractor=FrameExtractor(),
            video_verifier=verifier
        )

    @staticmethod
    def _daily_quota_error():
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

    def test_verified_unsuitable_is_normal_failure(self):
        verifier = ResultVerifier({
            "verification_status": "completed",
            "score": 70,
            "suitable": False
        })
        service = self._selection_service(verifier)
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as folder:
            with redirect_stdout(output):
                result = service.select(
                    make_word("rescue"),
                    Path(folder)
                )

        self.assertEqual(result["status"], "no_suitable_video")
        self.assertIn(
            "passed video verification",
            output.getvalue()
        )

    def test_quota_unavailable_is_not_semantic_rejection(self):
        verifier = ResultVerifier({
            "verification_status": "unavailable",
            "unavailable_reason": "quota_exhausted",
            "score": 0,
            "suitable": False
        })
        service = self._selection_service(verifier)
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as folder:
            with redirect_stdout(output):
                result = service.select(
                    make_word("respond"),
                    Path(folder)
                )

        self.assertEqual(
            result["status"],
            "verification_unavailable"
        )
        self.assertEqual(
            result["verification_unavailable_reason"],
            "quota_exhausted"
        )
        self.assertEqual(verifier.calls, 1)
        self.assertIn(
            "Video verification unavailable for this query.",
            output.getvalue()
        )
        self.assertNotIn(
            "passed video verification",
            output.getvalue()
        )

    def test_video_gemini_client_classifies_daily_quota(self):
        models = FakeModels([
            self._daily_quota_error(),
            self._daily_quota_error()
        ])
        fake_client = SimpleNamespace(models=models)

        with (
            patch.object(
                gemini_verification_client,
                "client",
                fake_client
            ),
            patch.object(
                gemini_verification_client.errors,
                "ClientError",
                FakeClientError
            ),
            patch.object(
                gemini_verification_client.time,
                "sleep"
            ) as sleep
        ):
            result = GeminiVerificationClient().generate(
                contents=["test"],
                primary_model="primary",
                fallback_model="fallback",
                task_name="video verifier"
            )

        self.assertEqual(models.calls, ["primary", "fallback"])
        sleep.assert_not_called()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(
            result["unavailable_reason"],
            "quota_exhausted"
        )

    def test_video_client_uses_fallback_and_remembers_daily_quota(self):
        fallback_response = SimpleNamespace(
            text='{"score": 70}'
        )
        models = FakeModels([
            self._daily_quota_error(),
            fallback_response,
            fallback_response
        ])
        fake_client = SimpleNamespace(models=models)

        with (
            patch.object(
                gemini_verification_client,
                "client",
                fake_client
            ),
            patch.object(
                gemini_verification_client.errors,
                "ClientError",
                FakeClientError
            )
        ):
            verification_client = GeminiVerificationClient()
            first_result = verification_client.generate(
                contents=["first video"],
                primary_model="primary",
                fallback_model="fallback",
                task_name="video verifier"
            )
            second_result = verification_client.generate(
                contents=["second video"],
                primary_model="primary",
                fallback_model="fallback",
                task_name="video verifier"
            )

        self.assertEqual(
            models.calls,
            ["primary", "fallback", "fallback"]
        )
        self.assertEqual(first_result["status"], "completed")
        self.assertEqual(second_result["status"], "completed")
        self.assertEqual(
            first_result["model_used"],
            "fallback"
        )
        self.assertEqual(
            second_result["model_used"],
            "fallback"
        )

    def test_video_unavailable_with_image_success_is_fallback_selected(self):
        service = MediaSelectionService(
            video_selection_service=ResultVideoService(
                "verification_unavailable"
            ),
            image_downloader=ResultImageDownloader(
                "selected"
            )
        )
        word = make_word("reveal")

        with tempfile.TemporaryDirectory() as folder:
            result = service.process_word(
                word,
                Path(folder)
            )

        self.assertEqual(word.media_status, "fallback_selected")
        self.assertEqual(result["media_status"], "fallback_selected")

    def test_normal_video_and_image_failures_are_media_missing(self):
        service = MediaSelectionService(
            video_selection_service=ResultVideoService(
                "no_suitable_video"
            ),
            image_downloader=ResultImageDownloader(
                "no_suitable_image"
            )
        )
        word = make_word("resign")

        with tempfile.TemporaryDirectory() as folder:
            result = service.process_word(
                word,
                Path(folder)
            )

        self.assertEqual(word.media_status, "media_missing")
        self.assertEqual(result["media_status"], "media_missing")

    def test_genuine_exception_becomes_error(self):
        service = MediaSelectionService(
            video_selection_service=ResultVideoService(
                error=RuntimeError("unexpected processing failure")
            ),
            image_downloader=ResultImageDownloader(
                "no_suitable_image"
            )
        )
        word = make_word("resign")

        with tempfile.TemporaryDirectory() as folder:
            result = service.process_word(
                word,
                Path(folder)
            )

        self.assertEqual(word.media_status, "error")
        self.assertEqual(result["media_status"], "error")


if __name__ == "__main__":
    unittest.main()
