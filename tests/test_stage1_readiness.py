import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from models.lesson import Lesson
from models.lesson_mapper import LessonMapper
from models.word import Word
from pipeline.stage1_readiness_assessor import (
    Stage1ReadinessAssessor
)


def make_word(word_text):
    return Word(
        word=word_text,
        meaning="test meaning",
        pronunciation="",
        part_of_speech="noun",
        difficulty="medium",
        translations={},
        present_sentence="Present sentence.",
        past_sentence="Past sentence.",
        future_sentence="Future sentence.",
        base_form=word_text,
        present_form=word_text,
        past_form=word_text,
        synonyms=[],
        antonyms=[],
        image_keywords=[],
        search_query=word_text,
        preferred_media="photo"
    )


def make_complete_lesson(lesson_folder, word_text="reliable"):
    word = make_word(word_text)

    image_path = Path(lesson_folder) / f"{word_text}.jpg"
    image_path.write_bytes(b"image")
    word.media_status = "selected"
    word.media_type = "photo"
    word.default_image = str(image_path)

    audio_folder = Path(lesson_folder) / "audio" / word_text
    audio_folder.mkdir(parents=True)

    for audio_name in (
        Stage1ReadinessAssessor.REQUIRED_AUDIO_NAMES
    ):
        (
            audio_folder
            / f"{audio_name}.mp3"
        ).write_bytes(b"audio")

    word.audio_folder = str(audio_folder)
    word.default_audio = str(
        audio_folder / "pronunciation.mp3"
    )

    lesson = Lesson(
        title="Readiness test",
        topic="readiness",
        words=[word],
        content_verification={
            "passed": True,
            "has_warnings": False
        }
    )

    return lesson, word


class Stage1ReadinessTests(unittest.TestCase):

    def setUp(self):
        self.assessor = Stage1ReadinessAssessor()

    def test_fully_complete_lesson_is_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson, _ = make_complete_lesson(folder)
            readiness = self.assessor.assess(
                lesson,
                Path(folder)
            )
            lesson.stage1_readiness = readiness

            restored = LessonMapper.from_dict(
                LessonMapper.to_dict(lesson)
            )

        self.assertEqual(readiness["content"], "ready")
        self.assertEqual(readiness["media"], "ready")
        self.assertEqual(readiness["audio"], "ready")
        self.assertTrue(
            readiness["ready_for_presentation"]
        )
        self.assertEqual(
            restored.content_verification,
            lesson.content_verification
        )
        self.assertEqual(
            restored.stage1_readiness,
            readiness
        )

    def test_media_missing_is_not_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson, word = make_complete_lesson(folder)
            word.media_status = "media_missing"

            readiness = self.assessor.assess(
                lesson,
                Path(folder)
            )

            output = io.StringIO()

            with redirect_stdout(output):
                self.assessor.print_report(
                    readiness
                )

        self.assertFalse(
            readiness["ready_for_presentation"]
        )
        self.assertEqual(readiness["media"], "incomplete")
        self.assertEqual(
            readiness["problem_words"][0]["issue"],
            "media_missing"
        )
        self.assertIn("STAGE 1 READINESS", output.getvalue())
        self.assertIn("Media: INCOMPLETE", output.getvalue())
        self.assertIn(
            "COMPLETED WITH ISSUES",
            output.getvalue()
        )
        self.assertIn(
            "NOT READY FOR PRESENTATION",
            output.getvalue()
        )

    def test_verification_unavailable_is_not_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson, word = make_complete_lesson(folder)
            word.media_status = "verification_unavailable"

            readiness = self.assessor.assess(
                lesson,
                Path(folder)
            )

        self.assertFalse(
            readiness["ready_for_presentation"]
        )
        self.assertEqual(
            readiness["problem_words"][0]["issue"],
            "verification_unavailable"
        )

    def test_missing_required_audio_is_not_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson, word = make_complete_lesson(folder)
            missing_path = (
                Path(word.audio_folder)
                / "past_sentence.mp3"
            )
            missing_path.unlink()

            readiness = self.assessor.assess(
                lesson,
                Path(folder)
            )

        self.assertFalse(
            readiness["ready_for_presentation"]
        )
        self.assertEqual(readiness["audio"], "incomplete")
        self.assertIn(
            "past_sentence",
            readiness["problem_words"][0]["issue"]
        )

    def test_media_error_is_not_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson, word = make_complete_lesson(folder)
            word.media_status = "error"

            readiness = self.assessor.assess(
                lesson,
                Path(folder)
            )

        self.assertFalse(
            readiness["ready_for_presentation"]
        )
        self.assertEqual(
            readiness["problem_words"][0]["issue"],
            "error"
        )

    def test_selected_status_with_missing_file_is_not_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson, word = make_complete_lesson(folder)
            Path(word.default_image).unlink()

            readiness = self.assessor.assess(
                lesson,
                Path(folder)
            )

        self.assertFalse(
            readiness["ready_for_presentation"]
        )
        self.assertEqual(
            readiness["problem_words"][0]["issue"],
            "invalid_selected_media"
        )


if __name__ == "__main__":
    unittest.main()
