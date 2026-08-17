from pathlib import Path

from models.word import Word

from video_engine.video_search_strategy import (
    VideoSearchStrategy
)

from video_engine.video_candidate_collector import (
    VideoCandidateCollector
)

from video_engine.video_candidate_downloader import (
    VideoCandidateDownloader
)

from video_engine.video_frame_extractor import (
    VideoFrameExtractor
)

from video_engine.video_verifier import (
    VideoVerifier
)

from config import (
    VIDEO_SEARCH_COUNT,
    VIDEO_VERIFY_COUNT
)


class VideoSelectionService:

    def __init__(
        self,
        search_strategy=None,
        candidate_collector=None,
        candidate_downloader=None,
        frame_extractor=None,
        video_verifier=None
    ):

        self.search_strategy = (
            search_strategy
            or VideoSearchStrategy()
        )

        self.candidate_collector = (
            candidate_collector
            or VideoCandidateCollector()
        )

        self.candidate_downloader = (
            candidate_downloader
            or VideoCandidateDownloader()
        )

        self.frame_extractor = (
            frame_extractor
            or VideoFrameExtractor()
        )

        self.video_verifier = (
            video_verifier
            or VideoVerifier()
        )

    def select(
        self,
        word: Word,
        output_folder: Path,
        per_source: int = VIDEO_SEARCH_COUNT
    ) -> dict:

        output_folder = Path(
            output_folder
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        queries = (
            self.search_strategy.build_queries(
                word
            )
        )

        attempts = []

        best_score = 0
        best_candidate = None

        for attempt_number, query in enumerate(
            queries,
            start=1
        ):

            print(
                f"\nVideo selection attempt "
                f"{attempt_number}/"
                f"{len(queries)}"
            )

            print(
                f"Query: {query}"
            )

            candidates = (
                self.candidate_collector.collect(
                    query=query,
                    per_source=per_source
                )
            )

            if not candidates:

                attempts.append({
                    "attempt": attempt_number,
                    "query": query,
                    "status": "no_candidates",
                    "candidates": []
                })

                print(
                    "No short video candidates."
                )

                continue

            attempt_folder = (
                output_folder
                / f"attempt_{attempt_number:02d}"
            )

            downloaded = (
                self.candidate_downloader.download(
                    candidates=candidates,
                    output_folder=attempt_folder,
                    max_downloads=(
                        VIDEO_VERIFY_COUNT
                    )
                )
            )

            candidate_results = []

            for candidate_index, candidate in enumerate(
                downloaded,
                start=1
            ):

                print(
                    f"\nVerifying video candidate "
                    f"{candidate_index}/"
                    f"{len(downloaded)}"
                )

                frames_folder = (
                    attempt_folder
                    / (
                        f"candidate_"
                        f"{candidate_index:02d}_frames"
                    )
                )

                try:

                    frames = (
                        self.frame_extractor.extract(
                            video_path=Path(
                                candidate.local_path
                            ),
                            output_folder=(
                                frames_folder
                            )
                        )
                    )

                    verification = (
                        self.video_verifier.verify(
                            word=word,
                            candidate=candidate,
                            frame_paths=frames
                        )
                    )

                except Exception as error:

                    candidate_results.append({
                        "source":
                            candidate.source,

                        "source_id":
                            candidate.source_id,

                        "local_path":
                            candidate.local_path,

                        "status":
                            "processing_failed",

                        "score":
                            0,

                        "error":
                            str(error)
                    })

                    continue

                score = (
                    verification.get(
                        "score",
                        0
                    )
                )

                candidate_result = {
                    "source":
                        candidate.source,

                    "source_id":
                        candidate.source_id,

                    "duration":
                        candidate.duration,

                    "width":
                        candidate.width,

                    "height":
                        candidate.height,

                    "local_path":
                        candidate.local_path,

                    "score":
                        score,

                    "suitable":
                        verification.get(
                            "suitable",
                            False
                        ),

                    "motion_visible":
                        verification.get(
                            "motion_visible",
                            False
                        ),

                    "meaning_match":
                        verification.get(
                            "meaning_match",
                            False
                        ),

                    "loop_suitable":
                        verification.get(
                            "loop_suitable",
                            False
                        ),

                    "reason":
                        verification.get(
                            "reason",
                            ""
                        ),

                    "model_used":
                        verification.get(
                            "model_used"
                        )
                }

                candidate_results.append(
                    candidate_result
                )

                if score > best_score:

                    best_score = score
                    best_candidate = (
                        candidate_result
                    )

                if verification.get(
                    "suitable",
                    False
                ):

                    print(
                        "Suitable video found."
                    )

                    attempts.append({
                        "attempt":
                            attempt_number,

                        "query":
                            query,

                        "status":
                            "selected",

                        "candidates":
                            candidate_results
                    })

                    return {
                        "status":
                            "selected",

                        "selected_video":
                            candidate.local_path,

                        "selected_score":
                            score,

                        "selected_query":
                            query,

                        "source":
                            candidate.source,

                        "source_id":
                            candidate.source_id,

                        "duration":
                            candidate.duration,

                        "loop_suitable":
                            verification.get(
                                "loop_suitable",
                                False
                            ),

                        "attempts":
                            attempts
                    }

            attempts.append({
                "attempt":
                    attempt_number,

                "query":
                    query,

                "status":
                    "rejected",

                "candidates":
                    candidate_results
            })

            print(
                "No candidate from this query "
                "passed video verification."
            )

        return {
            "status":
                "no_suitable_video",

            "selected_video":
                None,

            "selected_score":
                best_score,

            "best_candidate":
                best_candidate,

            "selected_query":
                None,

            "attempts":
                attempts
        }