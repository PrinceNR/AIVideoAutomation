from video_engine.pexels_video_client import (
    PexelsVideoClient
)

from video_engine.pixabay_video_client import (
    PixabayVideoClient
)

from video_engine.video_candidate_filter import (
    VideoCandidateFilter
)

from config import VIDEO_SEARCH_COUNT


class VideoCandidateCollector:

    def __init__(
        self,
        pexels_client=None,
        pixabay_client=None,
        candidate_filter=None
    ):

        self.pexels_client = (
            pexels_client
            or PexelsVideoClient()
        )

        self.pixabay_client = (
            pixabay_client
            or PixabayVideoClient()
        )

        self.candidate_filter = (
            candidate_filter
            or VideoCandidateFilter()
        )

    def collect(
        self,
        query: str,
        per_source: int = VIDEO_SEARCH_COUNT
    ):

        candidates = []

        candidates.extend(
            self._search_source(
                source_name="pexels",
                client=self.pexels_client,
                query=query,
                per_source=per_source
            )
        )

        candidates.extend(
            self._search_source(
                source_name="pixabay",
                client=self.pixabay_client,
                query=query,
                per_source=per_source
            )
        )

        candidates = (
            self._remove_duplicates(
                candidates
            )
        )

        return self.candidate_filter.filter(
            candidates
        )

    def _search_source(
        self,
        source_name,
        client,
        query,
        per_source
    ):

        try:

            print(
                f"Searching {source_name.title()} "
                f"videos: {query}"
            )

            candidates = client.search(
                query=query,
                per_page=per_source
            )

            print(
                f"{source_name.title()} returned "
                f"{len(candidates)} candidates."
            )

            return candidates

        except Exception as error:

            print(
                f"{source_name.title()} video "
                f"search failed: {error}"
            )

            return []

    def _remove_duplicates(
        self,
        candidates
    ):

        unique = []
        seen = set()

        for candidate in candidates:

            key = (
                candidate.source,
                candidate.source_id
                or candidate.video_url
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(candidate)

        return unique