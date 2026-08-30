import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import ai.content_generator as content_generator
from ai.content_generator import (
    LessonGenerationError,
    generate_vocabulary,
)
from models.lesson_mapper import LessonMapper
from pipeline.vocabulary_pipeline import VocabularyPipeline
from utils.AIResponseCleaner import (
    AIResponseCleaner,
    AIResponseParseError,
)


def lesson_data(topic="intermediate words starting with U"):

    return {
        "title": "",
        "topic": topic,
        "words": [{
            "word": "unwavering",
            "meaning": "remaining steady and determined",
            "pronunciation": "/ʌnˈweɪ.vər.ɪŋ/",
            "part_of_speech": "adjective",
            "difficulty": "Intermediate",
            "translations": {
                "malayalam": "അചഞ്ചലമായ",
                "tamil": "உறுதியான",
                "hindi": "अटल",
            },
            "present_sentence": (
                "She shows unwavering support for her friends."
            ),
            "past_sentence": (
                "He remained unwavering during the difficult meeting."
            ),
            "future_sentence": (
                "They will stay unwavering in their decision."
            ),
            "base_form": "",
            "present_form": "",
            "past_form": "",
            "synonyms": ["steady", "resolute", "constant"],
            "antonyms": ["uncertain", "wavering"],
            "image_keywords": [
                "determined person",
                "steady support",
                "firm decision",
            ],
            "search_query": "determined person standing firm",
        }],
    }


class SequenceModels:

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class SequenceClient:

    def __init__(self, responses):
        self.models = SequenceModels(responses)


def response(text, finish_reason="STOP"):

    return SimpleNamespace(
        text=text,
        finish_reason=SimpleNamespace(name=finish_reason),
    )


class PipelineFileManager:

    def __init__(self, folder, lesson=None):
        self.folder = Path(folder)
        self.lesson = lesson
        self.saved = []

    def create_lesson_folder(self, _topic):
        return self.folder

    def load_lesson(self, _path):
        return self.lesson

    def save_json(self, data, path):
        self.saved.append((data, Path(path)))


class ContentGenerationJSONRecoveryTests(unittest.TestCase):

    def _generate_with(self, *responses):
        fake_client = SequenceClient(responses)

        with patch.object(
            content_generator,
            "client",
            fake_client,
        ), redirect_stdout(io.StringIO()):
            lesson = generate_vocabulary(
                "intermediate words starting with U",
                1,
            )

        return lesson, fake_client.models.calls

    def test_valid_json_parses_in_one_structured_request(self):
        lesson, calls = self._generate_with(
            response(json.dumps(lesson_data()))
        )

        self.assertEqual(lesson.words[0].word, "unwavering")
        self.assertEqual(len(calls), 1)
        request_config = calls[0]["config"]
        self.assertEqual(
            request_config.response_mime_type,
            "application/json",
        )
        self.assertEqual(
            request_config.response_json_schema[
                "properties"
            ]["words"]["minItems"],
            1,
        )

    def test_fenced_json_response_parses(self):
        raw = "```json\n" + json.dumps(lesson_data()) + "\n```"
        parsed = AIResponseCleaner.parse_json_object(raw)

        self.assertEqual(parsed["words"][0]["word"], "unwavering")

    def test_surrounding_prose_extracts_complete_object(self):
        raw = (
            "Here is the requested lesson:\n"
            + json.dumps(lesson_data())
            + "\nGeneration complete."
        )
        parsed = AIResponseCleaner.parse_json_object(raw)

        self.assertEqual(parsed["topic"], lesson_data()["topic"])

    def test_parse_diagnostic_is_bounded_around_failure(self):
        raw = (
            "intro "
            + ("x" * 300)
            + '{"topic": "U", "words": [BROKEN]}'
            + ("y" * 300)
        )

        with self.assertRaises(AIResponseParseError) as caught:
            AIResponseCleaner.parse_json_object(raw)

        snippet = caught.exception.diagnostic_snippet
        self.assertIn("BROKEN", snippet)
        self.assertLessEqual(
            len(snippet),
            AIResponseCleaner.DIAGNOSTIC_RADIUS * 2,
        )

    def test_malformed_json_retries_once_and_accepts_valid_retry(self):
        fake_client = SequenceClient([
            response('{"topic": "U", "words": ['),
            response(json.dumps(lesson_data())),
        ])
        output = io.StringIO()

        with patch.object(
            content_generator,
            "client",
            fake_client,
        ), redirect_stdout(output):
            lesson = generate_vocabulary("U", 1)

        self.assertEqual(lesson.words[0].word, "unwavering")
        self.assertEqual(len(fake_client.models.calls), 2)
        self.assertIn("retrying once", output.getvalue())
        self.assertIn(
            "RECOVERY REQUIREMENT",
            fake_client.models.calls[1]["contents"],
        )

    def test_truncated_json_is_not_guessed_and_retry_is_bounded(self):
        fake_client = SequenceClient([
            response(
                '{"topic": "U", "words": [{"word": ',
                "MAX_TOKENS",
            ),
            response(
                '{"topic": "U", "words": [{"word": ',
                "MAX_TOKENS",
            ),
        ])

        with patch.object(
            content_generator,
            "client",
            fake_client,
        ), redirect_stdout(io.StringIO()):
            with self.assertRaises(LessonGenerationError):
                generate_vocabulary("U", 1)

        self.assertEqual(len(fake_client.models.calls), 2)

    def test_structurally_incomplete_json_is_not_silently_filled(self):
        incomplete = json.dumps({"topic": "U", "words": []})
        fake_client = SequenceClient([
            response(incomplete),
            response(incomplete),
        ])

        with patch.object(
            content_generator,
            "client",
            fake_client,
        ), redirect_stdout(io.StringIO()):
            with self.assertRaises(LessonGenerationError):
                generate_vocabulary("U", 1)

        self.assertEqual(len(fake_client.models.calls), 2)

    def test_failed_generation_is_controlled_and_starts_no_later_stage(self):
        with tempfile.TemporaryDirectory() as temp_folder:
            pipeline = VocabularyPipeline.__new__(VocabularyPipeline)
            pipeline.file_manager = PipelineFileManager(temp_folder)
            pipeline.content_verifier = SimpleNamespace(
                verify=lambda *_args: self.fail(
                    "content verification must not start"
                )
            )
            pipeline.media_selection_service = SimpleNamespace(
                process_word=lambda **_kwargs: self.fail(
                    "media must not start"
                )
            )
            pipeline.audio_generator = SimpleNamespace(
                generate_word_audio=lambda *_args: self.fail(
                    "audio must not start"
                )
            )
            output = io.StringIO()

            with patch(
                "pipeline.vocabulary_pipeline.generate_vocabulary",
                side_effect=LessonGenerationError("invalid JSON"),
            ), redirect_stdout(output):
                result = pipeline.run("U", 1, "")

            self.assertEqual(
                result,
                Path(temp_folder) / "lesson.json",
            )
            self.assertEqual(pipeline.file_manager.saved, [])

        terminal_output = output.getvalue()
        self.assertIn("Content: INCOMPLETE", terminal_output)
        self.assertIn("Media: INCOMPLETE", terminal_output)
        self.assertIn("Audio: INCOMPLETE", terminal_output)
        self.assertIn("NOT READY FOR PRESENTATION", terminal_output)
        self.assertNotIn("Traceback", terminal_output)

    def test_failed_generation_never_overwrites_existing_lesson(self):
        existing_lesson = LessonMapper.from_dict(lesson_data())

        with tempfile.TemporaryDirectory() as temp_folder:
            lesson_path = Path(temp_folder) / "lesson.json"
            original = json.dumps(lesson_data(), ensure_ascii=False)
            lesson_path.write_text(original, encoding="utf-8")
            pipeline = VocabularyPipeline.__new__(VocabularyPipeline)
            pipeline.file_manager = PipelineFileManager(
                temp_folder,
                existing_lesson,
            )

            with patch(
                "pipeline.vocabulary_pipeline.generate_vocabulary",
                side_effect=LessonGenerationError("invalid JSON"),
            ), redirect_stdout(io.StringIO()):
                pipeline.run("U", 1, "")

            self.assertEqual(
                lesson_path.read_text(encoding="utf-8"),
                original,
            )
            self.assertEqual(pipeline.file_manager.saved, [])

    def test_valid_existing_lesson_keeps_media_resume_behavior(self):
        existing_lesson = LessonMapper.from_dict(lesson_data())
        existing_lesson.words[0].preferred_media = "photo"
        media_calls = []
        audio_calls = []

        with tempfile.TemporaryDirectory() as temp_folder:
            lesson_path = Path(temp_folder) / "lesson.json"
            lesson_path.touch()
            pipeline = VocabularyPipeline.__new__(VocabularyPipeline)
            pipeline.file_manager = PipelineFileManager(
                temp_folder,
                existing_lesson,
            )

            def select_media(**kwargs):
                media_calls.append(kwargs["word"].word)
                kwargs["word"].media_status = "media_missing"

            pipeline.media_selection_service = SimpleNamespace(
                process_word=select_media
            )
            pipeline.audio_generator = SimpleNamespace(
                generate_word_audio=lambda word, _folder: (
                    audio_calls.append(word.word)
                )
            )
            pipeline.stage1_readiness_assessor = SimpleNamespace(
                assess=lambda *_args: {
                    "content": "ready",
                    "media": "incomplete",
                    "audio": "incomplete",
                    "overall": "completed_with_issues",
                    "ready_for_presentation": False,
                    "problem_words": [],
                },
                print_report=lambda _result: None,
            )

            with patch(
                "pipeline.vocabulary_pipeline.generate_vocabulary"
            ) as generate, redirect_stdout(io.StringIO()):
                result = pipeline.run("U", 1, "")

            generate.assert_not_called()
            self.assertEqual(result, lesson_path)

        self.assertEqual(media_calls, ["unwavering"])
        self.assertEqual(audio_calls, ["unwavering"])


if __name__ == "__main__":
    unittest.main()
