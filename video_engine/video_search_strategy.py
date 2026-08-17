from models.word import Word


class VideoSearchStrategy:

    def __init__(
        self,
        max_queries: int = 3
    ):
        self.max_queries = max_queries

    def build_queries(
        self,
        word: Word
    ) -> list[str]:

        candidates = []

        # -----------------------------------------
        # 1. Dedicated motion queries
        # -----------------------------------------

        if word.video_search_queries:

            candidates.extend(
                word.video_search_queries
            )

        # -----------------------------------------
        # 2. Existing visual search query fallback
        # -----------------------------------------

        if word.search_query:

            candidates.append(
                word.search_query
            )

        # -----------------------------------------
        # 3. Existing visual keywords fallback
        # -----------------------------------------

        if word.image_keywords:

            candidates.extend(
                word.image_keywords
            )

        # -----------------------------------------
        # 4. Final generic fallback
        # -----------------------------------------

        if word.word:

            candidates.append(
                word.word
            )

        queries = self._normalize(
            candidates
        )

        return queries[
            :self.max_queries
        ]

    def _normalize(
        self,
        queries
    ) -> list[str]:

        normalized = []
        seen = set()

        for query in queries:

            if not isinstance(
                query,
                str
            ):
                continue

            clean_query = " ".join(
                query.strip().split()
            )

            if not clean_query:
                continue

            key = clean_query.lower()

            if key in seen:
                continue

            seen.add(key)

            normalized.append(
                clean_query
            )

        return normalized