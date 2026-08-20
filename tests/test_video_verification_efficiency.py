import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from video_engine.video_candidate import VideoCandidate
from video_engine.video_candidate_filter import VideoCandidateFilter
from video_engine.video_selection_service import VideoSelectionService


def make_candidate(
    source,
    source_id,
    video_url=None,
    duration=4.0,
    width=1280,
    height=720
):
    return VideoCandidate(
        source=source,
        source_id=source_id,
        video_url=(
            video_url
            or f"https://example.test/{source_id}.mp4"
        ),
        duration=duration,
        width=width,
        height=height
    )


class SearchStrategy:

    def __init__(self, queries):
        self.queries = queries

    def build_queries(self, word):
        return self.queries


class CandidateCollector:

    def __init__(self, candidates_by_query):
        self.candidates_by_query = candidates_by_query

    def collect(self, query, per_source):
        return list(
            self.candidates_by_query.get(
                query,
                []
            )
        )


class CandidateDownloader:

    def download(
        self,
        candidates,
        output_folder,
        max_downloads
    ):
        downloaded = list(
            candidates[:max_downloads]
        )

        for candidate in downloaded:
            candidate.local_path = str(
                Path(output_folder)
                / f"{candidate.source_id}.mp4"
            )

        return downloaded


class FrameExtractor:

    def extract(self, video_path, output_folder):
        return [Path("frame.jpg")]


class VideoVerifier:

    def __init__(self, suitable_ids=None):
        self.suitable_ids = set(
            suitable_ids
            or []
        )
        self.calls = []

    def verify(self, word, candidate, frame_paths):
        self.calls.append(candidate)
        suitable = (
            candidate.source_id
            in self.suitable_ids
        )

        return {
            "verification_status": "completed",
            "score": 90 if suitable else 50,
            "suitable": suitable,
            "motion_visible": suitable,
            "meaning_match": suitable,
            "loop_suitable": suitable,
            "reason": "test"
        }


class VideoVerificationEfficiencyTests(unittest.TestCase):

    def make_service(
        self,
        candidates_by_query,
        verifier,
        max_verifications=4
    ):
        return VideoSelectionService(
            search_strategy=SearchStrategy(
                list(candidates_by_query)
            ),
            candidate_collector=CandidateCollector(
                candidates_by_query
            ),
            candidate_downloader=CandidateDownloader(),
            frame_extractor=FrameExtractor(),
            video_verifier=verifier,
            max_verifications_per_word=(
                max_verifications
            )
        )

    def test_duplicates_are_skipped_and_word_limit_is_bounded(self):
        first = make_candidate("pexels", "1")
        candidates_by_query = {
            "query one": [
                first,
                make_candidate("pexels", "2"),
                make_candidate("pixabay", "3")
            ],
            "query two": [
                make_candidate("pexels", "1"),
                make_candidate("pixabay", "4"),
                make_candidate("pexels", "5")
            ],
            "query three": [
                make_candidate("pixabay", "6")
            ]
        }
        verifier = VideoVerifier()
        service = self.make_service(
            candidates_by_query,
            verifier
        )

        with tempfile.TemporaryDirectory() as folder:
            result = service.select(
                SimpleNamespace(word="propose"),
                Path(folder)
            )

        self.assertEqual(
            [
                candidate.source_id
                for candidate in verifier.calls
            ],
            ["1", "2", "3", "4"]
        )
        self.assertEqual(
            result["status"],
            "no_suitable_video"
        )

    def test_same_url_from_another_provider_is_not_reverified(self):
        shared_url = "https://cdn.example.test/shared.mp4"
        candidates_by_query = {
            "query one": [
                make_candidate(
                    "pexels",
                    "10",
                    shared_url
                )
            ],
            "query two": [
                make_candidate(
                    "pixabay",
                    "99",
                    shared_url
                )
            ]
        }
        verifier = VideoVerifier()
        service = self.make_service(
            candidates_by_query,
            verifier
        )

        with tempfile.TemporaryDirectory() as folder:
            service.select(
                SimpleNamespace(word="propose"),
                Path(folder)
            )

        self.assertEqual(len(verifier.calls), 1)

    def test_local_filter_rejects_invalid_technical_candidates(self):
        candidates = [
            make_candidate("pexels", "valid"),
            make_candidate(
                "pexels",
                "short",
                duration=1.0
            ),
            make_candidate(
                "pexels",
                "long",
                duration=8.0
            ),
            make_candidate(
                "pixabay",
                "small",
                width=640,
                height=360
            ),
            make_candidate(
                "pixabay",
                "portrait",
                width=1280,
                height=1920
            )
        ]

        filtered = VideoCandidateFilter().filter(
            candidates
        )

        self.assertEqual(
            [candidate.source_id for candidate in filtered],
            ["valid"]
        )

    def test_first_approved_video_stops_verification(self):
        candidates_by_query = {
            "query one": [
                make_candidate("pexels", "approved"),
                make_candidate("pexels", "unused")
            ],
            "query two": [
                make_candidate("pixabay", "also-unused")
            ]
        }
        verifier = VideoVerifier(
            suitable_ids={"approved"}
        )
        service = self.make_service(
            candidates_by_query,
            verifier
        )

        with tempfile.TemporaryDirectory() as folder:
            result = service.select(
                SimpleNamespace(word="propose"),
                Path(folder)
            )

        self.assertEqual(
            [
                candidate.source_id
                for candidate in verifier.calls
            ],
            ["approved"]
        )
        self.assertEqual(result["status"], "selected")


if __name__ == "__main__":
    unittest.main()
