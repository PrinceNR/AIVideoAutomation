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
    VIDEO_VERIFY_COUNT,
    VIDEO_VERIFICATION_MAX_CANDIDATES
)


class VideoSelectionService:

    def __init__(
        self,
        search_strategy=None,
        candidate_collector=None,
        candidate_downloader=None,
        frame_extractor=None,
        video_verifier=None,
        max_verifications_per_word=(
            VIDEO_VERIFICATION_MAX_CANDIDATES
        )
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

        self.max_verifications_per_word = (
            max_verifications_per_word
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
        verification_unavailable = False
        verification_completed = False
        processing_failed = False
        verification_count = 0
        verified_candidate_keys = set()

        for attempt_number, query in enumerate(
            queries,
            start=1
        ):

            if (
                verification_count
                >= self.max_verifications_per_word
            ):

                print(
                    "Gemini video verification limit "
                    f"reached ({self.max_verifications_per_word} "
                    "per word)."
                )

                break

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

            candidates, duplicate_count = (
                self._exclude_verified_candidates(
                    candidates,
                    verified_candidate_keys
                )
            )

            if duplicate_count:

                print(
                    f"Skipped {duplicate_count} video "
                    "candidate(s) already verified "
                    "for this word."
                )

            if not candidates:

                attempts.append({
                    "attempt": attempt_number,
                    "query": query,
                    "status": "no_new_candidates",
                    "candidates": []
                })

                continue

            remaining_verifications = (
                self.max_verifications_per_word
                - verification_count
            )

            attempt_folder = (
                output_folder
                / f"attempt_{attempt_number:02d}"
            )

            downloaded = (
                self.candidate_downloader.download(
                    candidates=candidates,
                    output_folder=attempt_folder,
                    max_downloads=(
                        min(
                            VIDEO_VERIFY_COUNT,
                            remaining_verifications
                        )
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

                    verified_candidate_keys.update(
                        self._candidate_identity_keys(
                            candidate
                        )
                    )

                    verification_count += 1

                    verification = (
                        self.video_verifier.verify(
                            word=word,
                            candidate=candidate,
                            frame_paths=frames
                        )
                    )

                except Exception as error:

                    processing_failed = True

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

                verification_status = (
                    verification.get(
                        "verification_status",
                        "completed"
                    )
                )

                if verification_status == "unavailable":
                    verification_unavailable = True

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
                        ),

                    "verification_status":
                        verification_status
                }

                candidate_results.append(
                    candidate_result
                )

                if verification_status == "unavailable":
                    continue

                verification_completed = True

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

                    preview_image = None

                    if frames:
                        preview_index = (
                            1 if len(frames) > 1 else 0
                        )

                        preview_image = str(
                            frames[preview_index]
                        )

                    return {
                        "status":
                            "selected",

                        "selected_video":
                            candidate.local_path,

                        "preview_image":
                            preview_image,

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

        if verification_unavailable:
            status = "verification_unavailable"
        elif processing_failed and not verification_completed:
            status = "error"
        else:
            status = "no_suitable_video"

        return {
            "status": status,

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

    def _exclude_verified_candidates(
        self,
        candidates,
        verified_candidate_keys
    ):

        unique_candidates = []
        current_query_keys = set()
        duplicate_count = 0

        for candidate in candidates:

            candidate_keys = (
                self._candidate_identity_keys(
                    candidate
                )
            )

            if candidate_keys and (
                candidate_keys
                & (
                    verified_candidate_keys
                    | current_query_keys
                )
            ):

                duplicate_count += 1
                continue

            unique_candidates.append(
                candidate
            )

            current_query_keys.update(
                candidate_keys
            )

        return (
            unique_candidates,
            duplicate_count
        )

    def _candidate_identity_keys(
        self,
        candidate
    ):

        keys = set()

        source = str(
            getattr(
                candidate,
                "source",
                ""
            )
            or ""
        ).strip().lower()

        source_id = str(
            getattr(
                candidate,
                "source_id",
                ""
            )
            or ""
        ).strip()

        if source_id:
            keys.add((
                "source_id",
                source,
                source_id
            ))

        video_url = str(
            getattr(
                candidate,
                "video_url",
                ""
            )
            or ""
        ).strip()

        if video_url:
            keys.add((
                "video_url",
                video_url
            ))

        return keys
