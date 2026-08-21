import json
import tempfile
import unittest
from pathlib import Path

from media_engine.adaptive_media_recovery_planner import (
    AdaptiveMediaRecoveryPlanner
)
from media_engine.media_recovery_plan import (
    MediaRecoveryPlan
)
from media_engine.media_selection_service import (
    MediaSelectionService
)
from media_engine.media_type import MediaType
from models.lesson import Lesson
from models.lesson_mapper import LessonMapper
from models.word import Word


def make_word():
    return Word(
        word="hesitate",
        meaning="to pause before doing something",
        pronunciation="/hesitate/",
        part_of_speech="verb",
        difficulty="Intermediate",
        translations={},
        present_sentence="She hesitates before opening the door.",
        past_sentence="He hesitated before answering.",
        future_sentence="They will hesitate before deciding.",
        base_form="hesitate",
        present_form="hesitates",
        past_form="hesitated",
        synonyms=[],
        antonyms=[],
        image_keywords=[
            "hand hesitating over desk",
            "person stopping before action"
        ],
        search_query="person pausing before door",
        preferred_media="photo",
        media_reason="A pause may be visible in a still image.",
        requires_motion=False
    )


class ResultImageDownloader:

    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.calls = 0

    def download_word_images(self, word, lesson_folder):
        self.calls += 1
        status = self.statuses.pop(0)

        if status == "selected":
            image_path = Path(lesson_folder) / "recovered.jpg"
            image_path.write_bytes(b"image")
            word.default_image = str(image_path)
            word.media_type = "photo"
        else:
            word.default_image = None
            word.media_type = None

        return {"status": status}


class ResultVideoSelectionService:

    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.calls = 0
        self.query_sets = []

    def select(self, word, output_folder):
        self.calls += 1
        self.query_sets.append(
            list(word.video_search_queries)
        )
        status = self.statuses.pop(0)

        if status == "selected":
            return {
                "status": "selected",
                "selected_video": str(
                    Path(output_folder) / "recovered.mp4"
                ),
                "preview_image": str(
                    Path(output_folder) / "preview.jpg"
                ),
                "selected_score": 90,
                "attempts": []
            }

        return {
            "status": status,
            "selected_video": None,
            "selected_score": 0,
            "attempts": []
        }


class RecordingRecoveryPlanner:

    def __init__(self, media_type=MediaType.VIDEO):
        self.calls = 0
        self.attempted_queries = []
        self.media_type = media_type

    def plan(self, word, attempted_queries):
        self.calls += 1
        self.attempted_queries.append(
            list(attempted_queries)
        )

        return MediaRecoveryPlan(
            media_type=self.media_type,
            reason="Motion shows a visible pause before action.",
            search_queries=[
                "person pauses then decides",
                "woman stops before entering",
                "man pauses before answering"
            ]
        )


class AdaptiveMediaRecoveryTests(unittest.TestCase):

    def test_normal_success_never_invokes_recovery(self):
        image = ResultImageDownloader(["selected"])
        video = ResultVideoSelectionService([])
        planner = RecordingRecoveryPlanner()
        service = MediaSelectionService(
            video_selection_service=video,
            image_downloader=image,
            recovery_planner=planner
        )

        with tempfile.TemporaryDirectory() as folder:
            result = service.process_word(
                make_word(),
                Path(folder)
            )

        self.assertEqual(result["media_status"], "selected")
        self.assertEqual(planner.calls, 0)
        self.assertEqual(video.calls, 0)

    def test_failed_static_selection_recovers_through_video(self):
        image = ResultImageDownloader(["no_suitable_image"])
        video = ResultVideoSelectionService(["selected"])
        planner = RecordingRecoveryPlanner()
        service = MediaSelectionService(
            video_selection_service=video,
            image_downloader=image,
            recovery_planner=planner
        )
        word = make_word()

        with tempfile.TemporaryDirectory() as folder:
            result = service.process_word(
                word,
                Path(folder)
            )

        self.assertEqual(
            word.media_status,
            "fallback_selected"
        )
        self.assertEqual(
            result["media_status"],
            "fallback_selected"
        )
        self.assertEqual(word.media_type, "video")
        self.assertEqual(planner.calls, 1)
        self.assertEqual(video.calls, 1)
        self.assertEqual(
            video.query_sets[0],
            [
                "person pauses then decides",
                "woman stops before entering",
                "man pauses before answering"
            ]
        )

    def test_recovery_receives_and_rejects_attempted_queries(self):
        image = ResultImageDownloader(["no_suitable_image"])
        video = ResultVideoSelectionService(["no_suitable_video"])
        planner = RecordingRecoveryPlanner()
        service = MediaSelectionService(
            video_selection_service=video,
            image_downloader=image,
            recovery_planner=planner
        )
        word = make_word()

        with tempfile.TemporaryDirectory() as folder:
            service.process_word(word, Path(folder))

        self.assertEqual(
            planner.attempted_queries[0],
            [
                "person pausing before door",
                "hand hesitating over desk",
                "person stopping before action"
            ]
        )

        repeated_plan = {
            "media_type": "video",
            "reason": "test",
            "search_queries": [
                "person pausing before door",
                "woman stops then decides",
                "man pauses before answering"
            ]
        }

        with self.assertRaises(ValueError):
            AdaptiveMediaRecoveryPlanner()._parse(
                json.dumps(repeated_plan),
                planner.attempted_queries[0]
            )

    def test_recovery_is_attempted_at_most_once(self):
        image = ResultImageDownloader([
            "no_suitable_image",
            "no_suitable_image"
        ])
        video = ResultVideoSelectionService([
            "no_suitable_video"
        ])
        planner = RecordingRecoveryPlanner()
        service = MediaSelectionService(
            video_selection_service=video,
            image_downloader=image,
            recovery_planner=planner
        )
        word = make_word()

        with tempfile.TemporaryDirectory() as folder:
            service.process_word(word, Path(folder))
            service.process_word(word, Path(folder))

        self.assertEqual(planner.calls, 1)
        self.assertEqual(video.calls, 1)
        self.assertEqual(image.calls, 2)

        restored = LessonMapper.from_dict(
            LessonMapper.to_dict(
                Lesson(
                    title="Recovery",
                    topic="recovery",
                    words=[word]
                )
            )
        )
        self.assertTrue(
            restored.words[0]
            .media_recovery["attempted"]
        )

    def test_failed_recovery_remains_media_missing(self):
        service = MediaSelectionService(
            video_selection_service=(
                ResultVideoSelectionService([
                    "no_suitable_video"
                ])
            ),
            image_downloader=(
                ResultImageDownloader([
                    "no_suitable_image"
                ])
            ),
            recovery_planner=RecordingRecoveryPlanner()
        )
        word = make_word()

        with tempfile.TemporaryDirectory() as folder:
            result = service.process_word(
                word,
                Path(folder)
            )

        self.assertEqual(word.media_status, "media_missing")
        self.assertEqual(result["media_status"], "media_missing")

    def test_recovery_verification_unavailable_remains_distinct(self):
        service = MediaSelectionService(
            video_selection_service=(
                ResultVideoSelectionService([
                    "verification_unavailable"
                ])
            ),
            image_downloader=(
                ResultImageDownloader([
                    "no_suitable_image"
                ])
            ),
            recovery_planner=RecordingRecoveryPlanner()
        )
        word = make_word()

        with tempfile.TemporaryDirectory() as folder:
            result = service.process_word(
                word,
                Path(folder)
            )

        self.assertEqual(
            word.media_status,
            "verification_unavailable"
        )
        self.assertEqual(
            result["media_status"],
            "verification_unavailable"
        )

    def test_recovery_prompt_uses_semantics_and_prior_queries(self):
        word = make_word()
        attempted_queries = [
            word.search_query,
            *word.image_keywords
        ]

        prompt = (
            AdaptiveMediaRecoveryPlanner
            ._build_prompt(
                word,
                attempted_queries
            )
        )

        self.assertIn(word.word, prompt)
        self.assertIn(word.meaning, prompt)
        self.assertIn(word.part_of_speech, prompt)
        self.assertIn(word.present_sentence, prompt)
        self.assertIn(word.past_sentence, prompt)
        self.assertIn(word.future_sentence, prompt)
        self.assertIn(word.preferred_media, prompt)
        self.assertIn(word.media_reason, prompt)

        for query in attempted_queries:
            self.assertIn(query, prompt)


if __name__ == "__main__":
    unittest.main()
