import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from media_engine.media_selection_service import (
    MediaSelectionService
)
from models.lesson import Lesson
from models.lesson_mapper import LessonMapper
from models.word import Word
from pipeline.vocabulary_pipeline import VocabularyPipeline
from utils.file_manager import FileManager


class CountingImageDownloader:

    def __init__(self):
        self.words = []

    def download_word_images(self, word, lesson_folder):
        self.words.append(word.word)

        image_path = (
            Path(lesson_folder)
            / "images"
            / word.word
            / "selected.jpg"
        )
        image_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )
        image_path.write_bytes(b"image")

        word.default_image = str(image_path)
        word.media_type = "photo"


class FailingVideoSelectionService:

    def select(self, word, output_folder):
        raise AssertionError(
            "Video selection should not run in this test."
        )


class RecordingAudioGenerator:

    def __init__(self):
        self.words = []

    def generate_word_audio(self, word, lesson_folder):
        self.words.append(word.word)


def make_word(word_text):
    return Word(
        word=word_text,
        meaning="test meaning",
        pronunciation="",
        part_of_speech="noun",
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
        preferred_media="photo"
    )


class MediaSelectionResumeTests(unittest.TestCase):

    def test_pipeline_resumes_and_only_skips_valid_media(self):
        with tempfile.TemporaryDirectory() as folder:
            output_folder = Path(folder)
            lesson_folder = output_folder / "resume_topic"
            lesson_folder.mkdir()

            valid_word = make_word("complete")
            valid_image = lesson_folder / "complete.jpg"
            valid_image.write_bytes(b"image")
            valid_word.default_image = str(valid_image)
            valid_word.media_type = "photo"

            missing_file_word = make_word("missing_file")
            missing_file_word.default_image = str(
                lesson_folder / "does_not_exist.jpg"
            )
            missing_file_word.media_type = "photo"

            incomplete_word = make_word("incomplete")
            incomplete_word.default_image = str(valid_image)
            incomplete_word.media_type = "media_missing"

            lesson = Lesson(
                title="Resume test",
                topic="resume topic",
                words=[
                    valid_word,
                    missing_file_word,
                    incomplete_word
                ]
            )

            file_manager = FileManager()
            file_manager.output_folder = output_folder
            lesson_path = lesson_folder / "lesson.json"
            file_manager.save_json(
                LessonMapper.to_dict(lesson),
                lesson_path
            )

            image_downloader = CountingImageDownloader()
            media_service = MediaSelectionService(
                video_selection_service=(
                    FailingVideoSelectionService()
                ),
                image_downloader=image_downloader
            )
            audio_generator = RecordingAudioGenerator()

            pipeline = VocabularyPipeline.__new__(
                VocabularyPipeline
            )
            pipeline.file_manager = file_manager
            pipeline.media_selection_service = media_service
            pipeline.audio_generator = audio_generator

            with patch(
                "pipeline.vocabulary_pipeline.generate_vocabulary"
            ) as generate_vocabulary:
                result_path = pipeline.run(
                    topic="resume topic",
                    count=3,
                    suggestions=""
                )

            generate_vocabulary.assert_not_called()
            self.assertEqual(result_path, lesson_path)
            self.assertEqual(
                image_downloader.words,
                ["missing_file", "incomplete"]
            )

            saved_lesson = file_manager.load_lesson(
                lesson_path
            )
            self.assertEqual(
                saved_lesson.words[0].default_image,
                str(valid_image)
            )
            self.assertTrue(
                Path(
                    saved_lesson.words[1].default_image
                ).is_file()
            )
            self.assertTrue(
                Path(
                    saved_lesson.words[2].default_image
                ).is_file()
            )

    def test_video_resume_requires_video_and_preview_files(self):
        class CountingVideoSelectionService:
            def __init__(self):
                self.calls = 0

            def select(self, word, output_folder):
                self.calls += 1
                return {
                    "status": "selected",
                    "selected_video": str(
                        Path(output_folder) / "new.mp4"
                    ),
                    "preview_image": str(
                        Path(output_folder) / "new.jpg"
                    ),
                    "selected_score": 90
                }

        with tempfile.TemporaryDirectory() as folder:
            lesson_folder = Path(folder)
            video_path = lesson_folder / "selected.mp4"
            preview_path = lesson_folder / "preview.jpg"
            video_path.write_bytes(b"video")
            preview_path.write_bytes(b"preview")

            word = make_word("motion")
            word.preferred_media = "video"
            word.media_type = "video"
            word.default_video = str(video_path)
            word.default_image = str(preview_path)

            video_service = CountingVideoSelectionService()
            image_downloader = CountingImageDownloader()
            service = MediaSelectionService(
                video_selection_service=video_service,
                image_downloader=image_downloader
            )

            result = service.process_word(
                word,
                lesson_folder
            )

            self.assertEqual(
                result["status"],
                "already_selected"
            )
            self.assertEqual(video_service.calls, 0)
            self.assertEqual(image_downloader.words, [])

            preview_path.unlink()
            service.process_word(word, lesson_folder)

            self.assertEqual(video_service.calls, 1)


if __name__ == "__main__":
    unittest.main()
