import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

from image_engine.image_downloader import ImageDownloader
from media_engine.media_selection_service import (
    MediaSelectionService
)
from models.lesson import Lesson
from models.lesson_mapper import LessonMapper
from models.word import Word
from pipeline.vocabulary_pipeline import VocabularyPipeline
from video_engine.video_selection_service import (
    VideoSelectionService
)


def make_word(word_text, preferred_media="photo"):
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
        preferred_media=preferred_media
    )


class ResultImageDownloader:

    def __init__(self, status):
        self.status = status

    def download_word_images(self, word, lesson_folder):
        if self.status == "error":
            raise RuntimeError("image failure")

        if self.status == "selected":
            image_path = (
                Path(lesson_folder)
                / f"{word.word}.jpg"
            )
            image_path.write_bytes(b"image")
            word.default_image = str(image_path)
            word.media_type = "photo"
        else:
            word.default_image = None
            word.media_type = None

        return {
            "status": self.status,
            "selected_score": (
                85 if self.status == "selected" else 0
            )
        }


class ResultVideoSelectionService:

    def __init__(self, status):
        self.status = status

    def select(self, word, output_folder):
        return {
            "status": self.status,
            "selected_video": None,
            "selected_score": 0,
            "attempts": []
        }


class MediaStatusReportingTests(unittest.TestCase):

    def test_word_statuses_and_checkpoint_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson_folder = Path(folder)

            selected = make_word("selected")
            selected_service = MediaSelectionService(
                video_selection_service=(
                    ResultVideoSelectionService(
                        "no_suitable_video"
                    )
                ),
                image_downloader=(
                    ResultImageDownloader("selected")
                )
            )
            selected_service.process_word(
                selected,
                lesson_folder
            )

            fallback = make_word("fallback", "video")
            fallback_service = MediaSelectionService(
                video_selection_service=(
                    ResultVideoSelectionService(
                        "no_suitable_video"
                    )
                ),
                image_downloader=(
                    ResultImageDownloader("selected")
                )
            )
            fallback_service.process_word(
                fallback,
                lesson_folder
            )

            missing = make_word("missing")
            missing.media_recovery = {
                "attempted": True,
                "status": "media_missing"
            }
            MediaSelectionService(
                video_selection_service=(
                    ResultVideoSelectionService(
                        "no_suitable_video"
                    )
                ),
                image_downloader=(
                    ResultImageDownloader(
                        "no_suitable_image"
                    )
                )
            ).process_word(missing, lesson_folder)

            unavailable = make_word("unavailable")
            MediaSelectionService(
                video_selection_service=(
                    ResultVideoSelectionService(
                        "no_suitable_video"
                    )
                ),
                image_downloader=(
                    ResultImageDownloader(
                        "verification_unavailable"
                    )
                )
            ).process_word(unavailable, lesson_folder)

            failed = make_word("failed")
            MediaSelectionService(
                video_selection_service=(
                    ResultVideoSelectionService(
                        "no_suitable_video"
                    )
                ),
                image_downloader=(
                    ResultImageDownloader("error")
                )
            ).process_word(failed, lesson_folder)

            words = [
                selected,
                fallback,
                missing,
                unavailable,
                failed
            ]

            self.assertEqual(
                [word.media_status for word in words],
                [
                    "selected",
                    "fallback_selected",
                    "media_missing",
                    "verification_unavailable",
                    "error"
                ]
            )

            lesson = Lesson(
                title="Status test",
                topic="status",
                words=words
            )
            restored = LessonMapper.from_dict(
                LessonMapper.to_dict(lesson)
            )

            self.assertEqual(
                [word.media_status for word in restored.words],
                [word.media_status for word in words]
            )

    def test_summary_counts_and_lists_problem_words(self):
        statuses = [
            "selected",
            "fallback_selected",
            "media_missing",
            "verification_unavailable",
            "error"
        ]
        words = []

        for status in statuses:
            word = make_word(status)
            word.media_status = status
            words.append(word)

        output = io.StringIO()

        with redirect_stdout(output):
            counts = VocabularyPipeline._print_media_summary(
                words
            )

        text = output.getvalue()

        self.assertEqual(
            counts,
            {status: 1 for status in statuses}
        )
        self.assertIn("MEDIA SELECTION SUMMARY", text)
        self.assertIn("Words processed: 5", text)
        self.assertIn("Missing: 1", text)
        self.assertIn(
            "media_missing -> media_missing",
            text
        )
        self.assertIn(
            "verification_unavailable -> "
            "verification_unavailable",
            text
        )

    def test_video_verification_unavailable_is_preserved(self):
        class SearchStrategy:
            def build_queries(self, word):
                return ["test query"]

        class CandidateCollector:
            def collect(self, query, per_source):
                return [SimpleNamespace(source_id="1")]

        candidate = SimpleNamespace(
            source="pexels",
            source_id="1",
            local_path="candidate.mp4",
            duration=5.0,
            width=1280,
            height=720
        )

        class CandidateDownloader:
            def download(
                self,
                candidates,
                output_folder,
                max_downloads
            ):
                return [candidate]

        class FrameExtractor:
            def extract(self, video_path, output_folder):
                return [Path("frame.jpg")]

        class VideoVerifier:
            def verify(self, word, candidate, frame_paths):
                return {
                    "verification_status": "unavailable",
                    "score": 0,
                    "suitable": False
                }

        service = VideoSelectionService(
            search_strategy=SearchStrategy(),
            candidate_collector=CandidateCollector(),
            candidate_downloader=CandidateDownloader(),
            frame_extractor=FrameExtractor(),
            video_verifier=VideoVerifier()
        )

        with tempfile.TemporaryDirectory() as folder:
            result = service.select(
                make_word("motion", "video"),
                Path(folder)
            )

        self.assertEqual(
            result["status"],
            "verification_unavailable"
        )

    def test_missing_image_does_not_print_finished_success(self):
        class MissingFallbackService:
            def select(
                self,
                word,
                image_folder,
                per_source
            ):
                return {
                    "status": "no_suitable_image",
                    "selected_score": 55
                }

        downloader = ImageDownloader.__new__(
            ImageDownloader
        )
        downloader.fallback_service = (
            MissingFallbackService()
        )
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as folder:
            with redirect_stdout(output):
                result = downloader.download_word_images(
                    make_word("missing"),
                    Path(folder)
                )

        self.assertEqual(
            result["status"],
            "no_suitable_image"
        )
        self.assertNotIn(
            "Finished image processing",
            output.getvalue()
        )


if __name__ == "__main__":
    unittest.main()
