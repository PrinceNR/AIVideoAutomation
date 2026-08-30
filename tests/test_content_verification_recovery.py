import copy
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from models.lesson_mapper import LessonMapper
from pipeline.vocabulary_pipeline import VocabularyPipeline
from verification.content_verifier import ContentVerifier


def make_lesson():
    return LessonMapper.from_dict({
        "title": "",
        "topic": "intermediate words starting with S",
        "suggestions": "above medium words",
        "words": [{
            "word": "superficial",
            "meaning": "existing only at the surface and not deep",
            "pronunciation": "/ˌsuː.pəˈfɪʃ.əl/",
            "part_of_speech": "adjective",
            "difficulty": "Intermediate",
            "translations": {
                "malayalam": "ზედაპირული",
                "tamil": "மேலோட்டமான",
                "hindi": "ऊपरी",
            },
            "present_sentence": (
                "His knowledge of the subject is only superficial."
            ),
            "past_sentence": (
                "The wound on her arm was merely superficial."
            ),
            "future_sentence": (
                "They will make only superficial repairs there today."
            ),
            "base_form": "",
            "present_form": "",
            "past_form": "",
            "synonyms": ["shallow", "surface", "cursory"],
            "antonyms": ["deep", "profound"],
            "image_keywords": [
                "surface scratch",
                "shallow water",
                "outer layer",
            ],
            "search_query": "surface scratch on glass",
        }],
    })


def error_report():
    return {
        "summary": {
            "total_words": 1,
            "passed": 0,
            "warnings": 0,
            "errors": 1,
        },
        "results": [{
            "word": "superficial",
            "status": "error",
            "issues": [{
                "level": "error",
                "field": "translations.malayalam",
                "message": (
                    "malayalam translation does not contain "
                    "expected script characters."
                ),
            }],
        }],
    }


def warning_report():
    return {
        "summary": {
            "total_words": 1,
            "passed": 0,
            "warnings": 1,
            "errors": 0,
        },
        "results": [{
            "word": "superficial",
            "status": "warning",
            "issues": [{
                "level": "warning",
                "field": "past_sentence",
                "message": (
                    "Sentence contains 6 words. "
                    "Expected 7 to 15 words."
                ),
            }],
        }],
    }


def passed_report():
    return {
        "summary": {
            "total_words": 1,
            "passed": 1,
            "warnings": 0,
            "errors": 0,
        },
        "results": [{
            "word": "superficial",
            "status": "passed",
            "issues": [],
        }],
    }


class FakeFileManager:

    def __init__(self, lesson, folder=None):
        self.lesson = lesson
        self.folder = Path(folder) if folder else None
        self.saved = []

    def load_lesson(self, _path):
        return self.lesson

    def save_json(self, data, path):
        self.saved.append((data, Path(path)))

        if (
            isinstance(data, dict)
            and "topic" in data
            and "words" in data
        ):
            self.lesson = LessonMapper.from_dict(data)

    def create_lesson_folder(self, _topic):
        return self.folder


class SequenceRuleVerifier:

    def __init__(self, reports):
        self.reports = list(reports)
        self.calls = 0

    def verify(self, _lesson):
        self.calls += 1
        return copy.deepcopy(self.reports.pop(0))


class FakeSemanticVerifier:

    def __init__(self, corrected_lesson):
        self.corrected_lesson = corrected_lesson
        self.calls = []

    def verify(self, lesson_dict, **kwargs):
        self.calls.append((lesson_dict, kwargs))
        return {
            "summary": {
                "total_words": 1,
                "passed": 1,
                "warnings": 0,
                "errors": 0,
            },
            "results": [],
            "corrected_lesson": copy.deepcopy(
                self.corrected_lesson
            ),
        }


class ContentVerificationRecoveryTests(unittest.TestCase):

    def _run_verifier(self, reports, corrected_lesson):
        lesson = make_lesson()

        with tempfile.TemporaryDirectory() as temp_folder:
            lesson_path = Path(temp_folder) / "lesson.json"
            lesson_path.touch()
            verifier = ContentVerifier.__new__(ContentVerifier)
            verifier.file_manager = FakeFileManager(lesson)
            verifier.rule_verifier = SequenceRuleVerifier(reports)
            verifier.semantic_verifier = FakeSemanticVerifier(
                corrected_lesson
            )
            output = io.StringIO()

            with redirect_stdout(output):
                result = verifier.verify(lesson_path)

        return verifier, result, output.getvalue()

    def test_rule_error_prints_word_field_value_rule_and_reason(self):
        corrected = LessonMapper.to_dict(make_lesson())
        corrected["words"][0]["translations"]["malayalam"] = (
            "ഉപരിപ്ലവമായ"
        )
        _verifier, result, output = self._run_verifier(
            [error_report(), passed_report()],
            corrected,
        )

        self.assertTrue(result["passed"])
        self.assertIn("word: superficial", output)
        self.assertIn("field: translations.malayalam", output)
        self.assertIn("rule: translation_native_script", output)
        self.assertIn("value: ზედაპირული", output)
        self.assertIn("reason: malayalam translation", output)
        self.assertNotIn("Please review:\nNone", output)

    def test_non_ascii_offending_value_is_console_safe(self):
        lesson_dict = LessonMapper.to_dict(make_lesson())
        output_bytes = io.BytesIO()
        console = io.TextIOWrapper(
            output_bytes,
            encoding="cp1252",
            write_through=True,
        )

        with redirect_stdout(console):
            ContentVerifier._print_rule_issues(
                error_report(),
                lesson_dict,
            )

        output = output_bytes.getvalue().decode("cp1252")
        self.assertIn("word: superficial", output)
        self.assertIn("value: \\u10", output)
        self.assertIn("reason: malayalam translation", output)

    def test_fixable_error_uses_existing_correction_and_reverification(self):
        corrected = LessonMapper.to_dict(make_lesson())
        corrected["words"][0]["translations"]["malayalam"] = (
            "ഉപരിപ്ലവമായ"
        )
        verifier, result, _output = self._run_verifier(
            [error_report(), passed_report()],
            corrected,
        )

        self.assertEqual(len(verifier.semantic_verifier.calls), 1)
        self.assertEqual(verifier.rule_verifier.calls, 2)
        supplied_report = (
            verifier.semantic_verifier.calls[0][1]["rule_report"]
        )
        self.assertEqual(supplied_report["summary"]["errors"], 1)
        self.assertTrue(result["passed"])
        self.assertEqual(result["corrected_rule_errors"], 0)

    def test_warnings_alone_do_not_fail_content(self):
        lesson_dict = LessonMapper.to_dict(make_lesson())
        _verifier, result, _output = self._run_verifier(
            [warning_report(), warning_report()],
            lesson_dict,
        )

        self.assertTrue(result["passed"])
        self.assertTrue(result["has_warnings"])

    def test_unresolved_error_remains_controlled_not_ready(self):
        lesson_dict = LessonMapper.to_dict(make_lesson())
        _verifier, result, output = self._run_verifier(
            [error_report(), error_report()],
            lesson_dict,
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["corrected_rule_errors"], 1)
        self.assertIn(
            "Unresolved content verification issues",
            output,
        )

    def test_corrected_zero_error_checkpoint_proceeds_normally(self):
        lesson = make_lesson()
        lesson.content_verification = {
            "passed": False,
            "rule_errors": 1,
        }
        corrected = LessonMapper.to_dict(lesson)
        corrected["words"][0]["translations"]["malayalam"] = (
            "ഉപരിപ്ലവമായ"
        )

        with tempfile.TemporaryDirectory() as temp_folder:
            folder = Path(temp_folder)
            lesson_path = folder / "lesson.json"
            lesson_path.touch()
            pipeline = VocabularyPipeline.__new__(VocabularyPipeline)
            pipeline.file_manager = FakeFileManager(lesson, folder)
            pipeline.content_verifier = SimpleNamespace(
                verify=lambda _path: {
                    "passed": True,
                    "has_warnings": True,
                    "rule_errors": 1,
                    "semantic_errors": 1,
                    "corrected_rule_errors": 0,
                    "corrected_lesson": corrected,
                    "rule_report": Path("rule.json"),
                    "semantic_report": Path("semantic.json"),
                    "corrected_rule_report": Path(
                        "corrected.json"
                    ),
                }
            )
            media_plan = SimpleNamespace(calls=0)
            video_plan = SimpleNamespace(calls=0)
            media_selection = SimpleNamespace(calls=0)
            audio = SimpleNamespace(calls=0)

            def plan_media(planned_lesson):
                media_plan.calls += 1
                planned_lesson.words[0].preferred_media = "photo"

            def select_media(**kwargs):
                media_selection.calls += 1
                kwargs["word"].media_status = "media_missing"

            media_plan.plan_lesson = plan_media
            video_plan.plan_lesson = lambda _lesson: setattr(
                video_plan, "calls", video_plan.calls + 1
            )
            media_selection.process_word = select_media
            audio.generate_word_audio = lambda *_args: setattr(
                audio, "calls", audio.calls + 1
            )
            pipeline.media_planning_service = media_plan
            pipeline.video_query_planning_service = video_plan
            pipeline.media_selection_service = media_selection
            pipeline.audio_generator = audio
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
                result_path = pipeline.run(
                    topic=lesson.topic,
                    count=1,
                    suggestions=lesson.suggestions,
                )

        generate.assert_not_called()
        self.assertEqual(result_path, lesson_path)
        self.assertEqual(media_plan.calls, 1)
        self.assertEqual(video_plan.calls, 1)
        self.assertEqual(media_selection.calls, 1)
        self.assertEqual(audio.calls, 1)

    def test_failed_checkpoint_does_not_start_media_or_audio(self):
        lesson = make_lesson()
        lesson.content_verification = {
            "passed": False,
            "rule_errors": 1,
        }

        with tempfile.TemporaryDirectory() as temp_folder:
            folder = Path(temp_folder)
            lesson_path = folder / "lesson.json"
            lesson_path.touch()
            pipeline = VocabularyPipeline.__new__(VocabularyPipeline)
            pipeline.file_manager = FakeFileManager(lesson, folder)
            pipeline.content_verifier = SimpleNamespace(
                verify=lambda _path: {
                    "passed": False,
                    "has_warnings": False,
                    "rule_errors": 1,
                    "semantic_errors": 0,
                    "corrected_rule_errors": 1,
                    "corrected_lesson": None,
                    "rule_report": Path("rule.json"),
                    "semantic_report": None,
                    "corrected_rule_report": Path(
                        "corrected.json"
                    ),
                }
            )
            media_plan = SimpleNamespace(calls=0)
            video_plan = SimpleNamespace(calls=0)
            media_selection = SimpleNamespace(calls=0)
            audio = SimpleNamespace(calls=0)
            media_plan.plan_lesson = lambda _lesson: setattr(
                media_plan, "calls", media_plan.calls + 1
            )
            video_plan.plan_lesson = lambda _lesson: setattr(
                video_plan, "calls", video_plan.calls + 1
            )
            media_selection.process_word = lambda **_kwargs: setattr(
                media_selection,
                "calls",
                media_selection.calls + 1,
            )
            audio.generate_word_audio = lambda *_args: setattr(
                audio, "calls", audio.calls + 1
            )
            pipeline.media_planning_service = media_plan
            pipeline.video_query_planning_service = video_plan
            pipeline.media_selection_service = media_selection
            pipeline.audio_generator = audio
            pipeline.stage1_readiness_assessor = SimpleNamespace(
                assess=lambda *_args: {
                    "content": "incomplete",
                    "media": "incomplete",
                    "audio": "incomplete",
                    "overall": "completed_with_issues",
                    "ready_for_presentation": False,
                    "problem_words": [],
                },
                print_report=lambda _result: None,
            )
            output = io.StringIO()

            with patch(
                "pipeline.vocabulary_pipeline.generate_vocabulary"
            ) as generate, redirect_stdout(output):
                result_path = pipeline.run(
                    topic=lesson.topic,
                    count=1,
                    suggestions=lesson.suggestions,
                )

        generate.assert_not_called()
        self.assertEqual(result_path, lesson_path)
        self.assertEqual(media_plan.calls, 0)
        self.assertEqual(video_plan.calls, 0)
        self.assertEqual(media_selection.calls, 0)
        self.assertEqual(audio.calls, 0)
        self.assertIn(
            "Resuming content verification from checkpoint",
            output.getvalue(),
        )
        self.assertNotIn("Please review:\nNone", output.getvalue())


if __name__ == "__main__":
    unittest.main()
