from models.word import Word

from video_engine.video_search_strategy import (
    VideoSearchStrategy
)

from video_engine.video_candidate_collector import (
    VideoCandidateCollector
)

from config import VIDEO_SEARCH_COUNT


class VideoSearchService:

    def __init__(
        self,
        search_strategy=None,
        candidate_collector=None
    ):

        self.search_strategy = (
            search_strategy
            or VideoSearchStrategy()
        )

        self.candidate_collector = (
            candidate_collector
            or VideoCandidateCollector()
        )

    def search(
        self,
        word: Word,
        per_source: int = VIDEO_SEARCH_COUNT
    ) -> dict:

        queries = (
            self.search_strategy.build_queries(
                word
            )
        )

        attempts = []

        for attempt_number, query in enumerate(
            queries,
            start=1
        ):

            print(
                f"\nVideo search attempt "
                f"{attempt_number}/{len(queries)}"
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

            attempts.append({
                "attempt": attempt_number,
                "query": query,
                "candidate_count": len(
                    candidates
                )
            })

            if candidates:

                print(
                    f"Found {len(candidates)} "
                    f"short video candidate(s)."
                )

                return {
                    "status":
                        "candidates_found",

                    "query":
                        query,

                    "attempt":
                        attempt_number,

                    "candidates":
                        candidates,

                    "attempts":
                        attempts
                }

            print(
                "No suitable short videos "
                "for this query."
            )

        return {
            "status":
                "no_candidates",

            "query":
                None,

            "attempt":
                None,

            "candidates":
                [],

            "attempts":
                attempts
        }