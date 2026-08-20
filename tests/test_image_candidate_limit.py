import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config import (
    GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL,
    GEMINI_IMAGE_VERIFIER_MODEL,
    IMAGE_VERIFICATION_MAX_CANDIDATES
)
from image_engine import image_verifier
from image_engine.image_candidate_type import (
    ImageCandidateType
)
from image_engine.image_selection_service import (
    ImageSelectionService
)
from image_engine.image_verifier import ImageVerifier


class SearchStrategy:

    def __init__(self, queries):
        self.queries = queries

    def build_queries(self, word):
        return list(self.queries)


class CandidateCollector:

    def __init__(self, candidates_by_query):
        self.candidates_by_query = candidates_by_query

    def collect(
        self,
        query,
        image_folder,
        attempt,
        per_source,
        candidate_type
    ):
        return list(
            self.candidates_by_query[query]
        )


class RecordingVerifier:

    def __init__(self):
        self.calls = []

    def verify(self, word, image_paths):
        paths = list(image_paths)
        self.calls.append(paths)

        return {
            "verification_status": "completed",
            "selected_image": None,
            "selected_score": 50,
            "model_used": "test-model",
            "candidates": [{
                "image": Path(path).name,
                "score": 50,
                "suitable": False,
                "reason": "test"
            } for path in paths]
        }


def make_word():
    return SimpleNamespace(
        word="pristine",
        meaning="perfectly clean",
        present_sentence="The room looks pristine.",
        search_query="clean white room"
    )


def candidate_name(attempt, provider, index):
    return Path(
        f"attempt_{attempt:02d}_photo_"
        f"{provider}_{index:03d}.jpg"
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


class ImageCandidateLimitTests(unittest.TestCase):

    def _selection_service(
        self,
        candidates_by_query,
        maximum=IMAGE_VERIFICATION_MAX_CANDIDATES
    ):
        verifier = RecordingVerifier()
        service = ImageSelectionService(
            search_strategy=SearchStrategy(
                list(candidates_by_query)
            ),
            candidate_collector=CandidateCollector(
                candidates_by_query
            ),
            image_verifier=verifier,
            max_verification_candidates=maximum
        )
        return service, verifier

    def test_fewer_than_maximum_remain_unchanged(self):
        candidates = {
            "query one": [
                candidate_name(1, "pexels", 1),
                candidate_name(1, "pixabay", 1)
            ],
            "query two": [
                candidate_name(2, "pexels", 1),
                candidate_name(2, "pixabay", 1)
            ]
        }
        expected = (
            candidates["query one"]
            + candidates["query two"]
        )
        service, verifier = self._selection_service(
            candidates
        )

        service.select(
            make_word(),
            Path("unused"),
            candidate_type=ImageCandidateType.PHOTO
        )

        self.assertEqual(len(verifier.calls), 1)
        self.assertEqual(verifier.calls[0], expected)

    def test_large_batch_is_limited_with_query_provider_diversity(self):
        candidates = {}

        for attempt in range(1, 4):
            query = f"query {attempt}"
            candidates[query] = [
                candidate_name(attempt, "pexels", index)
                for index in range(1, 4)
            ] + [
                candidate_name(attempt, "pixabay", index)
                for index in range(1, 4)
            ]

        service, verifier = self._selection_service(
            candidates
        )
        output = io.StringIO()

        with redirect_stdout(output):
            service.select(
                make_word(),
                Path("unused"),
                candidate_type=ImageCandidateType.PHOTO
            )

        self.assertEqual(len(verifier.calls), 1)
        selected = verifier.calls[0]
        self.assertEqual(len(selected), 8)

        filenames = [path.name for path in selected]
        self.assertEqual(
            {
                attempt
                for attempt in (1, 2, 3)
                if any(
                    f"attempt_{attempt:02d}_" in name
                    for name in filenames
                )
            },
            {1, 2, 3}
        )
        self.assertTrue(
            any("_pexels_" in name for name in filenames)
        )
        self.assertTrue(
            any("_pixabay_" in name for name in filenames)
        )
        self.assertIn(
            "Collected 18 image candidates.",
            output.getvalue()
        )
        self.assertIn(
            "Selected 8 candidates for Gemini verification.",
            output.getvalue()
        )

    def test_transport_disconnect_retries_once_and_recovers(self):
        success = SimpleNamespace(
            text=json.dumps({
                "selected_image": "candidate.jpg",
                "selected_score": 85,
                "candidates": [{
                    "image": "candidate.jpg",
                    "score": 85,
                    "suitable": True,
                    "reason": "clear"
                }]
            })
        )
        models = FakeModels([
            RuntimeError(
                "Server disconnected without sending a response."
            ),
            success
        ])
        fake_client = SimpleNamespace(models=models)

        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder) / "candidate.jpg"
            image_path.write_bytes(b"image")

            with (
                patch.object(
                    image_verifier,
                    "client",
                    fake_client
                ),
                patch.object(
                    image_verifier.time,
                    "sleep"
                ) as sleep
            ):
                result = ImageVerifier().verify(
                    make_word(),
                    [image_path]
                )

        self.assertEqual(
            models.calls,
            [
                GEMINI_IMAGE_VERIFIER_MODEL,
                GEMINI_IMAGE_VERIFIER_MODEL
            ]
        )
        sleep.assert_called_once_with(1.0)
        self.assertEqual(result["verification_status"], "completed")
        self.assertEqual(result["selected_score"], 85)

    def test_repeated_transport_disconnect_is_bounded(self):
        disconnect = RuntimeError(
            "Server disconnected without sending a response."
        )
        models = FakeModels([
            disconnect,
            disconnect,
            disconnect
        ])
        fake_client = SimpleNamespace(models=models)

        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder) / "candidate.jpg"
            image_path.write_bytes(b"image")

            with (
                patch.object(
                    image_verifier,
                    "client",
                    fake_client
                ),
                patch.object(
                    image_verifier.time,
                    "sleep"
                ) as sleep
            ):
                result = ImageVerifier().verify(
                    make_word(),
                    [image_path]
                )

        self.assertEqual(
            models.calls,
            [
                GEMINI_IMAGE_VERIFIER_MODEL,
                GEMINI_IMAGE_VERIFIER_MODEL,
                GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
            ]
        )
        sleep.assert_called_once_with(1.0)
        self.assertEqual(result["verification_status"], "unavailable")
        self.assertEqual(
            result["unavailable_reason"],
            "transport_error"
        )


if __name__ == "__main__":
    unittest.main()
