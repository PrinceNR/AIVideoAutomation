import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ai import gemini_verification_client
from ai.youtube_metadata_generator import (
    MetadataTemporarilyUnavailableError,
    generate_youtube_metadata
)
from pipeline.youtube_metadata_pipeline import (
    YouTubeMetadataPipeline
)


class FakeServerError(Exception):
    def __init__(self):
        super().__init__(
            "503 UNAVAILABLE: This model is currently "
            "experiencing high demand. Please try again later."
        )
        self.code = 503


class FakeModels:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def generate_content(self, model, contents):
        self.calls.append(model)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def metadata_response(title="Useful Vocabulary"):
    return SimpleNamespace(text=json.dumps({
        "title": title,
        "description": "Learn useful words.",
        "tags": ["English", "vocabulary"],
        "hashtags": ["#English", "#Vocabulary"]
    }))


def lesson():
    word = SimpleNamespace(word="curious", meaning="eager to know")
    return SimpleNamespace(words=[word])


class YouTubeMetadataAvailabilityTests(unittest.TestCase):
    def generate_with(self, results):
        models = FakeModels(results)
        fake_client = SimpleNamespace(models=models)
        patches = (
            patch.object(
                gemini_verification_client,
                "client",
                fake_client
            ),
            patch.object(
                gemini_verification_client.errors,
                "ServerError",
                FakeServerError
            ),
            patch.object(
                gemini_verification_client.time,
                "sleep"
            )
        )
        return models, patches

    def test_normal_first_call_success(self):
        models, patches = self.generate_with([metadata_response()])
        with patches[0], patches[1], patches[2] as sleep:
            result = generate_youtube_metadata("test", lesson())

        self.assertEqual(result["title"], "Useful Vocabulary")
        self.assertEqual(len(models.calls), 1)
        sleep.assert_not_called()

    def test_transient_503_then_success(self):
        models, patches = self.generate_with([
            FakeServerError(),
            metadata_response()
        ])
        with patches[0], patches[1], patches[2] as sleep:
            result = generate_youtube_metadata("test", lesson())

        self.assertEqual(result["title"], "Useful Vocabulary")
        self.assertEqual(models.calls[0], models.calls[1])
        sleep.assert_called_once_with(1.0)

    def test_primary_503_then_fallback_success(self):
        models, patches = self.generate_with([
            FakeServerError(),
            FakeServerError(),
            metadata_response("Fallback title")
        ])
        with patches[0], patches[1], patches[2]:
            result = generate_youtube_metadata("test", lesson())

        self.assertEqual(result["title"], "Fallback title")
        self.assertNotEqual(models.calls[0], models.calls[2])

    def test_all_models_unavailable_preserves_existing_file(self):
        models, patches = self.generate_with([
            FakeServerError(),
            FakeServerError(),
            FakeServerError()
        ])

        with tempfile.TemporaryDirectory() as folder:
            lesson_path = Path(folder) / "lesson.json"
            metadata_path = Path(folder) / "youtube" / "metadata.json"
            metadata_path.parent.mkdir()
            original = '{"title": "Existing valid metadata"}'
            metadata_path.write_text(original, encoding="utf-8")

            pipeline = YouTubeMetadataPipeline()
            pipeline.file_manager.load_lesson = lambda path: lesson()

            with patches[0], patches[1], patches[2]:
                with self.assertRaisesRegex(
                    MetadataTemporarilyUnavailableError,
                    "temporarily unavailable"
                ):
                    pipeline.run(lesson_path)

            self.assertEqual(
                metadata_path.read_text(encoding="utf-8"),
                original
            )
            self.assertEqual(len(models.calls), 3)


if __name__ == "__main__":
    unittest.main()
